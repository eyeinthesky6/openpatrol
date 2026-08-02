import unittest
from openpatrol.sensor_hub_bridge import normalize_hub_message
class SensorHubBridgeTest(unittest.TestCase):
 def test_alarm_zone(self):
  e=normalize_hub_message({"v":1,"seq":2,"type":"zone","zone":5,"state":"alarm","raw":200},device_id="hub")
  self.assertEqual("smoke",e["event_type"]);self.assertEqual("critical",e["severity"])
 def test_normal_ignored(self):
  self.assertIsNone(normalize_hub_message({"v":1,"seq":2,"type":"zone","zone":1,"state":"normal"},device_id="hub"))
 def test_open_wire_is_tamper(self):
  self.assertEqual("tamper",normalize_hub_message({"v":1,"seq":3,"type":"zone","zone":1,"state":"open"},device_id="hub")["event_type"])
if __name__=="__main__":unittest.main()
