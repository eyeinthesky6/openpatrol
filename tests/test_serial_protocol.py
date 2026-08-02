import importlib.util
import math
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PATH=ROOT/"ros2/openpatrol_adapter/openpatrol_adapter/protocol.py"
SPEC=importlib.util.spec_from_file_location("openpatrol_serial_protocol",PATH)
PROTOCOL=importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name]=PROTOCOL
assert SPEC.loader is not None
SPEC.loader.exec_module(PROTOCOL)


class SerialProtocolTest(unittest.TestCase):
    def test_command_crc_and_status_round_trip(self):
        command=PROTOCOL.encode_command(42,.25,-.125,True)
        self.assertTrue(command.startswith(b"$C,42,250,-125,1*"))
        payload=b"S,42,100,-50,12800,5"
        crc=PROTOCOL.crc16_ccitt(payload)
        status=PROTOCOL.parse_status(b"$"+payload+f"*{crc:04X}\n".encode())
        self.assertEqual((42,100,-50,12800,5),(status.seq,status.left_ticks,status.right_ticks,status.battery_mv,status.flags))
        self.assertTrue(status.estop_open)
        self.assertTrue(status.command_timed_out)

    def test_bad_crc_is_rejected(self):
        with self.assertRaises(PROTOCOL.ProtocolError):
            PROTOCOL.parse_status("$S,1,0,0,12800,0*0000\n")

    def test_twist_scaling_preserves_curvature(self):
        left,right=PROTOCOL.twist_to_wheels(.4,1.0,.34,.45)
        self.assertLessEqual(max(abs(left),abs(right)),.45)
        self.assertAlmostEqual((right-left)/.34,1.0*(.45/.57),places=6)

    def test_encoder_wrap_and_odometry_increment(self):
        self.assertEqual(3,PROTOCOL.tick_delta(-2147483647,2147483646))
        distance,rotation=PROTOCOL.differential_increment(1320,1320,.05,.34,1320)
        self.assertAlmostEqual(math.pi*.1,distance,places=6)
        self.assertAlmostEqual(0,rotation,places=6)


if __name__=="__main__": unittest.main()
