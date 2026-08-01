import math,tempfile,unittest
from pathlib import Path
from openpatrol.virtual_hardware import HardwareConfig,VirtualHardware,run_acceptance

class VirtualHardwareTest(unittest.TestCase):
    def test_acceptance_suite(self):
        with tempfile.TemporaryDirectory() as directory:
            report=run_acceptance(Path(directory)/"report.json")
            self.assertEqual("pass",report["result"]); self.assertTrue(all(report["checks"].values()))
    def test_watchdog_and_estop_stop_motion(self):
        hw=VirtualHardware(); hw.set_estop(False); hw.command(.5,0); hw.tick(.1); self.assertGreater(hw.x,0)
        hw.tick(.2); self.assertEqual(0,hw.linear); before=hw.x; hw.set_estop(True); self.assertFalse(hw.command(.5,0)); hw.tick(.1); self.assertEqual(before,hw.x)
    def test_fault_visibility_and_recovery(self):
        hw=VirtualHardware(); hw.set_estop(False); hw.inject("encoder_dropout"); hw.inject("camera_dropout")
        self.assertIsNone(hw.telemetry()["pose"]); self.assertFalse(hw.telemetry()["camera_ok"])
        hw.inject("encoder_dropout",False); self.assertIsNotNone(hw.telemetry()["pose"])
    def test_invalid_math_is_rejected(self):
        with self.assertRaises(ValueError): HardwareConfig(max_linear_mps=math.nan).validate()
        hw=VirtualHardware(); hw.set_estop(False)
        with self.assertRaises(ValueError): hw.command(math.inf,0)
        with self.assertRaises(ValueError): hw.tick(0)
    def test_energy_scales_with_motion(self):
        idle=VirtualHardware(); moving=VirtualHardware(); idle.set_estop(False); moving.set_estop(False)
        for _ in range(100): idle.tick(.1); moving.command(.5,0); moving.tick(.1)
        self.assertLess(moving.battery_percent,idle.battery_percent)

if __name__=="__main__": unittest.main()
