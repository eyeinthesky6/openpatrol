import json
import tempfile
import unittest
from pathlib import Path

from openpatrol.hardware_profile import builtin_profiles, load_profile, validate_profile


EXPECTED = {
    "airscout-rev-a",
    "rover-one-rev-a",
    "sentinel-rev-a",
    "triscout-rev-a",
}


class HardwareProfileTest(unittest.TestCase):
    def test_bundled_family_profiles_are_valid_and_within_declared_cost_envelopes(self):
        self.assertEqual(EXPECTED, set(builtin_profiles()))
        for name in sorted(builtin_profiles()):
            with self.subTest(profile=name):
                profile = load_profile(name)
                report = validate_profile(profile)
                self.assertTrue(report["valid"], report)
                self.assertLessEqual(
                    profile["cost"]["estimated_bom_inr"],
                    profile["cost"]["target_envelope_inr"],
                )
                self.assertEqual("engineering-release-unvalidated", profile["status"])
                self.assertEqual("openpatrol-plain-future-v1", profile["visual"]["family"])

    def test_ground_profiles_share_safe_drive_contract(self):
        for name in ("rover-one-rev-a", "triscout-rev-a", "sentinel-rev-a"):
            with self.subTest(profile=name):
                profile = load_profile(name)
                self.assertEqual("ground_wheeled", profile["mobility"]["kind"])
                self.assertLessEqual(profile["drive"]["max_speed_mps"], 0.5)
                self.assertEqual(
                    "normally_closed_hardwired_drive_cut",
                    profile["safety"]["estop_architecture"],
                )
                self.assertTrue(profile["safety"]["independent_motor_watchdog"])

    def test_airscout_uses_autopilot_failsafe_and_bounded_companion_contract(self):
        profile = load_profile("airscout-rev-a")
        report = validate_profile(profile)
        self.assertTrue(report["valid"], report)
        self.assertEqual("aerial_multirotor", report["mobility_kind"])
        self.assertEqual("hover_then_land", profile["safety"]["command_loss_action"])
        self.assertTrue(profile["safety"]["geofence_enabled"])
        self.assertGreater(profile["safety"]["geofence_radius_m"], 0)
        self.assertGreater(profile["safety"]["geofence_ceiling_m"], 0)
        self.assertLessEqual(
            profile["performance"]["indoor_speed_limit_mps"],
            profile["performance"]["max_horizontal_speed_mps"],
        )

    def test_sentinel_mast_contract_is_consistent(self):
        profile = load_profile("sentinel-rev-a")
        report = validate_profile(profile)
        self.assertTrue(report["valid"], report)
        mast = profile["mast"]
        self.assertAlmostEqual(
            mast["extended_sensor_height_mm"] - mast["retracted_sensor_height_mm"],
            mast["travel_mm"],
            delta=25,
        )
        self.assertLess(mast["max_drive_speed_extended_mps"], profile["drive"]["max_speed_mps"])
        self.assertTrue(mast["self_locking_or_braked"])
        self.assertTrue(mast["tilt_interlock"])
        self.assertTrue(mast["docking_requires_retracted"])
        self.assertGreater(report["calculations"]["ideal_static_tip_angle_deg"], 20)
        self.assertLess(mast["tilt_interlock_degrees"], report["calculations"]["ideal_static_tip_angle_deg"] / 2)

    def test_unsafe_ground_profile_is_rejected(self):
        profile = load_profile("rover-one-rev-a")
        profile["safety"]["command_timeout_ms"] = 500
        profile["safety"]["estop_architecture"] = "software_only"
        report = validate_profile(profile)
        self.assertFalse(report["valid"])
        self.assertTrue(any("command_timeout" in item for item in report["errors"]))
        self.assertTrue(any("estop_architecture" in item for item in report["errors"]))

    def test_unsafe_air_profile_is_rejected(self):
        profile = load_profile("airscout-rev-a")
        profile["safety"]["flight_controller_failsafe"] = False
        profile["safety"]["command_loss_action"] = "continue"
        report = validate_profile(profile)
        self.assertFalse(report["valid"])
        self.assertTrue(any("flight_controller_failsafe" in item for item in report["errors"]))
        self.assertTrue(any("command_loss_action" in item for item in report["errors"]))

    def test_unsafe_mast_profile_is_rejected(self):
        profile = load_profile("sentinel-rev-a")
        profile["mast"]["max_drive_speed_extended_mps"] = 0.3
        profile["mast"]["tilt_interlock"] = False
        report = validate_profile(profile)
        self.assertFalse(report["valid"])
        self.assertTrue(any("extended drive speed" in item for item in report["errors"]))
        self.assertTrue(any("tilt_interlock" in item for item in report["errors"]))

    def test_external_profile_can_be_loaded(self):
        profile = load_profile("triscout-rev-a")
        profile.pop("_source", None)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "profile.json"
            path.write_text(json.dumps(profile), encoding="utf-8")
            self.assertTrue(validate_profile(load_profile(path))["valid"])


if __name__ == "__main__":
    unittest.main()
