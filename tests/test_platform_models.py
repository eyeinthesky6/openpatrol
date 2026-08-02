import unittest

from openpatrol.hardware_profile import load_profile, validate_profile
from openpatrol.platform_model import AirScoutModel, SentinelModel


class PlatformModelTest(unittest.TestCase):
    def test_airscout_stale_command_transitions_to_landing(self):
        profile = load_profile("airscout-rev-a")
        self.assertTrue(validate_profile(profile)["valid"])
        model = AirScoutModel(profile)
        model.arm_for_test(1.0)
        model.set_command(1.0, 0.0, 0.0, 0.0)
        model.step(0.2)
        state = model.step(0.4)
        self.assertEqual("landing", state.mode)
        self.assertLess(state.z_m, 1.0)

    def test_airscout_geofence_rejects_outward_motion(self):
        profile = load_profile("airscout-rev-a")
        model = AirScoutModel(profile)
        model.arm_for_test(1.0)
        model.state.x_m = profile["safety"]["geofence_radius_m"] - 0.1
        model.set_command(1.5, 0.0, 0.0, 0.0)
        state = model.step(0.2)
        self.assertEqual("landing", state.mode)
        self.assertLessEqual(state.x_m, profile["safety"]["geofence_radius_m"])

    def test_sentinel_mast_caps_speed_and_blocks_docking(self):
        profile = load_profile("sentinel-rev-a")
        self.assertTrue(validate_profile(profile)["valid"])
        model = SentinelModel(profile)
        decision = model.decide(0.38, 1300)
        self.assertAlmostEqual(profile["mast"]["max_drive_speed_extended_mps"], decision.commanded_linear_mps)
        self.assertFalse(decision.mast_allowed)
        self.assertFalse(decision.docking_allowed)

    def test_sentinel_tilt_stops_everything(self):
        model = SentinelModel(load_profile("sentinel-rev-a"))
        decision = model.decide(0.2, 1100, tilt_fault=True)
        self.assertEqual(0.0, decision.commanded_linear_mps)
        self.assertFalse(decision.mast_allowed)
        self.assertFalse(decision.docking_allowed)


if __name__ == "__main__":
    unittest.main()
