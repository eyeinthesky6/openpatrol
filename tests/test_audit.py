import json
import tempfile
import unittest
from pathlib import Path

from openpatrol.audit import AuditLog


class AuditTest(unittest.TestCase):
    def test_chain_verifies_and_detects_tampering(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/"audit.jsonl"; log=AuditLog(path)
            log.append("robot.command",details={"command":"pause"}); log.append("robot.command",details={"command":"resume"})
            self.assertTrue(log.verify()["valid"])
            entries=log.list(); entries[0]["details"]["command"]="estop"
            path.write_text("\n".join(json.dumps(item) for item in entries)+"\n",encoding="utf-8")
            self.assertFalse(log.verify()["valid"])


if __name__ == "__main__": unittest.main()
