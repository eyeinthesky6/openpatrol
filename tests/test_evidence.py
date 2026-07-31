import json
import tempfile
import unittest
from pathlib import Path

from openpatrol.evidence import EvidenceStore, canonical_bytes


class EvidenceTest(unittest.TestCase):
    def test_receipt_is_persisted_and_reviewable(self):
        with tempfile.TemporaryDirectory() as directory:
            store = EvidenceStore(Path(directory))
            receipt = store.create(
                robot_id="r1", site_id="s1", lap=0,
                waypoint={"id":"gate","x":2,"y":3},
                event={"id":"person","event_type":"person","title":"Person","severity":"high","confidence":.9},
            )
            self.assertEqual(64, len(receipt["integrity"]["digest"]))
            reviewed = store.update_review(receipt["event_id"], "confirmed", "verified")
            self.assertEqual("confirmed", reviewed["review"]["disposition"])
            self.assertEqual(1, len(store.list()))

    def test_canonical_representation_is_order_independent(self):
        self.assertEqual(canonical_bytes({"a":1,"b":2}), canonical_bytes({"b":2,"a":1}))


if __name__ == "__main__": unittest.main()
