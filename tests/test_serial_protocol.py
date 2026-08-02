import math
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ros2/openpatrol_adapter"))
from openpatrol_adapter import mast_protocol as MAST
from openpatrol_adapter import protocol as PROTOCOL


class SerialProtocolTest(unittest.TestCase):
    def test_command_crc_and_status_round_trip(self):
        command = PROTOCOL.encode_command(42, .25, -.125, True)
        self.assertTrue(command.startswith(b"$C,42,250,-125,1*"))
        payload = b"S,42,100,-50,12800,37"
        crc = PROTOCOL.crc16_ccitt(payload)
        status = PROTOCOL.parse_status(b"$" + payload + f"*{crc:04X}\n".encode())
        self.assertEqual(
            (42, 100, -50, 12800, 37),
            (status.seq, status.left_ticks, status.right_ticks, status.battery_mv, status.flags),
        )
        self.assertTrue(status.estop_open)
        self.assertTrue(status.command_timed_out)
        self.assertTrue(status.mast_extended)

    def test_bad_crc_is_rejected(self):
        with self.assertRaises(PROTOCOL.ProtocolError):
            PROTOCOL.parse_status("$S,1,0,0,12800,0*0000\n")

    def test_twist_scaling_preserves_curvature(self):
        left, right = PROTOCOL.twist_to_wheels(.4, 1.0, .34, .45)
        self.assertLessEqual(max(abs(left), abs(right)), .45)
        self.assertAlmostEqual((right - left) / .34, 1.0 * (.45 / .57), places=6)

    def test_encoder_wrap_and_odometry_increment(self):
        self.assertEqual(3, PROTOCOL.tick_delta(-2147483647, 2147483646))
        distance, rotation = PROTOCOL.differential_increment(1320, 1320, .05, .34, 1320)
        self.assertAlmostEqual(math.pi * .1, distance, places=6)
        self.assertAlmostEqual(0, rotation, places=6)

    def test_mast_command_and_status_round_trip(self):
        command = MAST.encode_mast_command(7, 1450, True)
        self.assertTrue(command.startswith(b"$M,7,1450,1*"))
        payload = b"T,7,1438,34"
        crc = PROTOCOL.crc16_ccitt(payload)
        status = MAST.parse_mast_status(b"$" + payload + f"*{crc:04X}\n".encode())
        self.assertEqual((7, 1438, 34), (status.seq, status.height_mm, status.flags))
        self.assertTrue(status.upper_limit)
        self.assertTrue(status.drive_moving)
        self.assertFalse(status.position_sensor_fault)

    def test_mast_position_sensor_fault_is_extended_or_unknown(self):
        payload = b"T,8,980,128"
        crc = PROTOCOL.crc16_ccitt(payload)
        status = MAST.parse_mast_status(b"$" + payload + f"*{crc:04X}\n".encode())
        self.assertTrue(status.position_sensor_fault)
        self.assertTrue(status.extended_or_unknown)
        self.assertFalse(status.extended)

    def test_mast_protocol_rejects_out_of_range_target(self):
        with self.assertRaises(PROTOCOL.ProtocolError):
            MAST.encode_mast_command(1, 1700, True)


if __name__ == "__main__":
    unittest.main()
