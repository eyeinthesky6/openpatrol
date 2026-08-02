import json
import tempfile
import unittest
from pathlib import Path

from openpatrol.hardware_profile import builtin_profiles, load_profile, validate_profile


class HardwareProfileTest(unittest.TestCase):
    def test_bundled_profiles_are_valid_and_low_cost(self):
        self.assertEqual({"rover-one-rev-a", "triscout-rev-a"}, set(builtin_profiles()))
        for name in builtin_profiles():
            profile = load_profile(name)
            report = validate_profile(profile)
            self.assertTrue(report["valid"], report)
            self.assertLessEqual(profile["drive"]["max_speed_mps"], 0.5)
            self.assertLessEqual(profile["cost"]["estimated_bom_inr"], 40000)
            self.assertEqual("engineering-release-unvalidated", profile["status"])

    def test_unsafe_profile_is_rejected(self):
        profile = load_profile("rover-one-rev-a")
        profile["safety"]["command_timeout_ms"] = 500
        profile["safety"]["estop_architecture"] = "software_only"
        report = validate_profile(profile)
        self.assertFalse(report["valid"])
        self.assertTrue(any("command_timeout" in item for item in report["errors"]))
        self.assertTrue(any("estop_architecture" in item for item in report["errors"]))

    def test_external_profile_can_be_loaded(self):
        profile = load_profile("triscout-rev-a")
        profile.pop("_source", None)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "profile.json"
            path.write_text(json.dumps(profile), encoding="utf-8")
            self.assertTrue(validate_profile(load_profile(path))["valid"])


if __name__ == "__main__":
    unittest.main()
