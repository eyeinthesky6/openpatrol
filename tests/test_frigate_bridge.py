import unittest
from openpatrol.frigate_bridge import normalize_frigate_event
class FrigateBridgeTest(unittest.TestCase):
    def test_normalizes_event(self):
        event=normalize_frigate_event({"type":"new","after":{"id":"abc","label":"person","camera":"gate","top_score":.91}},"http://frigate:5000")
        self.assertEqual("frigate-abc",event["id"]); self.assertEqual("high",event["severity"]); self.assertTrue(event["media_reference"].endswith("clip.mp4"))
    def test_ignores_incomplete_message(self): self.assertIsNone(normalize_frigate_event({"type":"new","after":{}}))
if __name__=="__main__": unittest.main()
