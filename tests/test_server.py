import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path

from openpatrol.server import ROOT, create_server


class ServerTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.previous_operator = __import__('os').environ.get("OPENPATROL_OPERATOR_TOKEN"); __import__('os').environ["OPENPATROL_OPERATOR_TOKEN"]="operator-secret"
        self.server, self.sim = create_server("127.0.0.1", 0, data=Path(self.temp.name), scenario=ROOT/"scenarios"/"warehouse.json", ingest_token="secret")
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True); self.thread.start()
        self.base = f"http://127.0.0.1:{self.server.server_address[1]}"

    def tearDown(self):
        self.server.shutdown(); self.server.server_close(); self.thread.join(); self.temp.cleanup()
        if self.previous_operator is None: __import__('os').environ.pop("OPENPATROL_OPERATOR_TOKEN",None)
        else: __import__('os').environ["OPENPATROL_OPERATOR_TOKEN"]=self.previous_operator

    def request(self, path, body=None, token=None):
        headers={}
        data=None
        if body is not None: data=json.dumps(body).encode(); headers["Content-Type"]="application/json"
        if token: headers["Authorization"]=f"Bearer {token}"
        elif path in {"/api/v1/commands","/api/patrol","/api/v1/settings"} or path.endswith("/review"): headers["Authorization"]="Bearer operator-secret"
        with urllib.request.urlopen(urllib.request.Request(self.base+path,data=data,headers=headers),timeout=2) as response:
            return response.status, json.load(response), response.headers

    def test_health_state_and_security_headers(self):
        status, payload, headers=self.request("/api/v1/health")
        self.assertEqual(200,status); self.assertEqual("ok",payload["status"]); self.assertEqual("nosniff",headers["X-Content-Type-Options"])
        self.assertEqual("simulation",self.request("/api/v1/state")[1]["mode"])

    def test_commands_and_detection_ingest(self):
        self.assertEqual("paused",self.request("/api/v1/commands",{"action":"pause"})[1]["robot"]["status"])
        event={"id":"cam-1","event_type":"person","title":"Person","severity":"high","confidence":.91,"source":"test-camera"}
        status, receipt, _=self.request("/api/v1/detections",event,"secret")
        self.assertEqual(201,status); self.assertEqual("test-camera",receipt["detection"]["source"])
        self.assertTrue(self.request(f"/api/v1/incidents/{receipt['event_id']}/verify")[1]["valid"])
        self.assertTrue(self.request("/api/v1/audit/verify")[1]["valid"])

    def test_ingest_requires_token(self):
        with self.assertRaises(urllib.error.HTTPError) as caught:
            self.request("/api/v1/detections",{})
        self.assertEqual(401,caught.exception.code)

    def test_invalid_legacy_status_is_rejected(self):
        with self.assertRaises(urllib.error.HTTPError) as caught: self.request("/api/patrol",{"status":"flying"})
        self.assertEqual(400,caught.exception.code)

    def test_mutation_rejects_wrong_operator_token(self):
        with self.assertRaises(urllib.error.HTTPError) as caught: self.request("/api/v1/commands",{"action":"pause"},"wrong")
        self.assertEqual(401,caught.exception.code)

    def test_diagnostics_and_persistent_settings(self):
        diagnostics=self.request("/api/v1/diagnostics")[1]
        self.assertEqual("simulation",diagnostics["mode"]); self.assertIn("storage",diagnostics); self.assertTrue(diagnostics["integrity"]["audit_valid"])
        saved=self.request("/api/v1/settings",{"retention_days":14,"max_records":200,"max_speed_mps":.25,"site_timezone":"Asia/Kolkata"})[1]
        self.assertTrue(saved["saved"]); self.assertEqual(14,self.request("/api/v1/settings")[1]["retention_days"]); self.assertAlmostEqual(.1,self.sim.speed)


if __name__ == "__main__": unittest.main()
