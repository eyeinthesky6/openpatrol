import unittest
from openpatrol.security_bridge import normalize_security_event
class SecurityBridgeTest(unittest.TestCase):
 def test_generic_door(self):
  e=normalize_security_event({"event_type":"door","device_id":"d1","zone":"gate","state":"open"},"alarm")
  self.assertEqual("door_open",e["event_type"]);self.assertEqual("gate",e["zone"])
 def test_home_assistant(self):
  e=normalize_security_event({"entity_id":"binary_sensor.front","state":"on","attributes":{"device_class":"door"},"area":"front"},"home-assistant")
  self.assertEqual("door_open",e["event_type"])
 def test_onvif_style(self):
  e=normalize_security_event({"eventType":"LineCrossing","sourceId":"cam-2","region":"yard"},"onvif")
  self.assertEqual("restricted_zone_entry",e["event_type"])
 def test_inactive_rejected(self):
  with self.assertRaises(ValueError):normalize_security_event({"event_type":"motion","state":"off"})
 def test_bad_confidence_rejected(self):
  with self.assertRaises(ValueError):normalize_security_event({"event_type":"motion","confidence":2})
if __name__=="__main__":unittest.main()
