import unittest
from openpatrol.device_agent import execute_command
class DeviceAgentTest(unittest.TestCase):
 def test_allowlist_dry_run(self):
  self.assertTrue(execute_command({"action":"speak","payload":{"text":"hello"}},dry_run=True)["ok"])
 def test_rejects_unknown_action(self):
  self.assertFalse(execute_command({"action":"shell","payload":{"command":"rm -rf /"}},dry_run=True)["ok"])
 def test_missing_audio(self):
  self.assertEqual("missing_audio",execute_command({"action":"play_audio","payload":{}},dry_run=False)["error"])
if __name__=="__main__":unittest.main()
