import unittest
from openpatrol.vision_adapter import normalize_provider_detection


class VisionAdapterTest(unittest.TestCase):
    def test_normalizes_any_provider_into_detection_contract(self):
        result=normalize_provider_detection({"id":"42","label":"person","confidence":.91,"provider":"yolo-local","location":"front"})
        self.assertEqual("person",result["event_type"]); self.assertEqual("vision/yolo-local/front",result["source"])
    def test_rejects_bad_provider_output(self):
        with self.assertRaises(ValueError): normalize_provider_detection({"id":"42","label":"person","confidence":2})


if __name__=="__main__": unittest.main()
