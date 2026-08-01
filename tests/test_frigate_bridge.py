import unittest
from unittest.mock import patch
from openpatrol.frigate_bridge import normalize_frigate_event
class FrigateBridgeTest(unittest.TestCase):
    def test_normalizes_event(self):
        event=normalize_frigate_event({"type":"new","after":{"id":"abc","label":"person","camera":"gate","top_score":.91}},"http://frigate:5000")
        self.assertEqual("frigate-abc",event["id"]); self.assertEqual("high",event["severity"]); self.assertTrue(event["media_reference"].endswith("clip.mp4"))
    def test_ignores_incomplete_message(self): self.assertIsNone(normalize_frigate_event({"type":"new","after":{}}))
    def test_restricted_zone_and_loitering_rules(self):
        with patch.dict("os.environ",{"OPENPATROL_RESTRICTED_ZONES":"vault","OPENPATROL_LOITER_SECONDS":"60"}):
            restricted=normalize_frigate_event({"type":"update","after":{"id":"a","label":"person","camera":"hall","score":.7,"entered_zones":["vault"]}})
            loitering=normalize_frigate_event({"type":"end","after":{"id":"b","label":"person","camera":"lobby","score":.7,"start_time":100,"end_time":170}})
        self.assertEqual("restricted_zone_entry",restricted["rule"]); self.assertEqual("loitering",loitering["rule"])
if __name__=="__main__": unittest.main()
