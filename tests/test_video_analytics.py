import unittest
from openpatrol.video_analytics import normalize_model_event,motion_score
class VideoAnalyticsTest(unittest.TestCase):
 def test_normalizes_supported_label(self):
  e=normalize_model_event({"id":"1","label":"fallen-person","confidence":.84,"camera":"cam1","zone":"lobby","provider":"pose"})
  self.assertEqual("fall",e["event_type"]);self.assertEqual("high",e["severity"])
 def test_drowning_is_critical(self):
  self.assertEqual("critical",normalize_model_event({"label":"drowning","confidence":.9})["severity"])
 def test_invalid_score(self):
  with self.assertRaises(ValueError):normalize_model_event({"label":"fall","confidence":float('nan')})
 def test_motion_score_without_numpy_shape_is_safe(self): self.assertEqual(0,motion_score(None,None))
if __name__=="__main__":unittest.main()
