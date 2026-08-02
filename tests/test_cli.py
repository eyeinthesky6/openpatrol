import json
import subprocess
import sys
import unittest


class CliTest(unittest.TestCase):
    def run_cli(self, *args):
        return subprocess.run(
            [sys.executable, "-m", "openpatrol.cli", *args],
            check=False,
            capture_output=True,
            text=True,
        )

    def test_doctor_json(self):
        result = self.run_cli("doctor", "--json")
        self.assertEqual(0, result.returncode, result.stderr)
        report = json.loads(result.stdout)
        self.assertTrue(report["core"]["ready"])
        self.assertTrue(report["core"]["bundled_dashboard"])

    def test_hardware_profiles(self):
        result = self.run_cli("hardware", "check", "all", "--json")
        self.assertEqual(0, result.returncode, result.stderr)
        reports = json.loads(result.stdout)
        self.assertTrue(all(item["valid"] for item in reports))


if __name__ == "__main__":
    unittest.main()
