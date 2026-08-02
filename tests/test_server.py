import json, os, tempfile, threading, unittest, urllib.error, urllib.request
from pathlib import Path
from openpatrol.server import ROOT, create_server

class ServerTest(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.previous={k:os.environ.get(k) for k in ("OPENPATROL_OPERATOR_TOKEN","OPENPATROL_DEVICE_TOKEN")}
  os.environ["OPENPATROL_OPERATOR_TOKEN"]="operator-secret";os.environ["OPENPATROL_DEVICE_TOKEN"]="device-secret"
  self.server,self.sim=create_server("127.0.0.1",0,data=Path(self.temp.name),scenario=ROOT/"scenarios"/"warehouse.json",ingest_token="ingest-secret")
  self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start();self.base=f"http://127.0.0.1:{self.server.server_address[1]}"
 def tearDown(self):
  self.server.shutdown();self.server.server_close();self.thread.join();self.temp.cleanup()
  for k,v in self.previous.items(): os.environ.pop(k,None) if v is None else os.environ.__setitem__(k,v)
 def request(self,path,body=None,token=None):
  headers={};data=None
  if body is not None:data=json.dumps(body).encode();headers["Content-Type"]="application/json"
  if token:headers["Authorization"]=f"Bearer {token}"
  request=urllib.request.Request(self.base+path,data=data,headers=headers,method="POST" if body is not None else "GET")
  with urllib.request.urlopen(request,timeout=3) as response:return response.status,json.load(response),response.headers
 def operator(self,path,body=None):return self.request(path,body,"operator-secret")
 def ingest(self,path,body):return self.request(path,body,"ingest-secret")
 def device(self,path,body=None):return self.request(path,body,"device-secret")
 def test_health_and_command_centre_auth(self):
  status,payload,headers=self.request("/api/v1/health");self.assertEqual(200,status);self.assertEqual("ready",payload["command_centre"]);self.assertEqual("nosniff",headers["X-Content-Type-Options"])
  with self.assertRaises(urllib.error.HTTPError) as caught:self.request("/api/v1/command-centre")
  self.assertEqual(401,caught.exception.code);self.assertIn("devices",self.operator("/api/v1/command-centre")[1])
 def test_legacy_detection_and_receipt(self):
  event={"id":"cam-1","event_type":"person","title":"Person","severity":"high","confidence":.91,"source":"test-camera"}
  status,receipt,_=self.ingest("/api/v1/detections",event);self.assertEqual(201,status);self.assertTrue(self.request(f"/api/v1/incidents/{receipt['event_id']}/verify")[1]["valid"])
 def test_register_poll_announce_and_ack(self):
  device={"id":"lobby-hub","name":"Lobby Hub","kind":"sensor_hub","zone":"lobby","capabilities":["sensors","speaker","strobe","siren"]}
  self.assertEqual(201,self.device("/api/v1/devices/register",device)[0])
  command=self.operator("/api/v1/announce",{"device_ids":["lobby-hub"],"text":"Please leave the restricted area"})[1]["commands"][0]
  pending=self.device("/api/v1/devices/lobby-hub/commands")[1]["commands"];self.assertEqual(command["id"],pending[0]["id"])
  ack=self.device(f"/api/v1/devices/lobby-hub/commands/{command['id']}/ack",{"result":{"ok":True}})[1];self.assertEqual("acknowledged",ack["status"])
 def test_security_fusion_and_device_outputs(self):
  device={"id":"pool-hub","name":"Pool Hub","kind":"sensor_hub","zone":"pool","capabilities":["sensors","speaker","strobe","siren"]}
  self.device("/api/v1/devices/register",device)
  result=self.ingest("/api/v1/security-events",{"id":"pool-1","event_type":"drowning_distress","title":"Pool distress","severity":"critical","confidence":.92,"source":"vision/pool","provider":"pool-model","device_id":"pool-camera","zone":"pool"})[1]
  self.assertEqual("incident",result["status"]);self.assertIn("Lifeguard",result["alert"]["automatic_message"])
  actions={item["action"] for item in self.device("/api/v1/devices/pool-hub/commands")[1]["commands"]};self.assertTrue({"speak","strobe","siren"}.issubset(actions))
 def test_weak_observation_does_not_raise_incident(self):
  result=self.ingest("/api/v1/security-events",{"id":"weak","event_type":"fall","severity":"high","confidence":.4,"source":"vision/cam","provider":"model","device_id":"cam","zone":"lobby"})[1]
  self.assertEqual("observed",result["status"]);self.assertIsNone(result["incident"])
 def test_security_event_retry_is_idempotent(self):
  event={"id":"panic-1","event_type":"panic","severity":"critical","confidence":1,"source":"panel","provider":"panel","device_id":"panel","zone":"gate"}
  first=self.ingest("/api/v1/security-events",event)[1];second=self.ingest("/api/v1/security-events",event)[1]
  self.assertEqual("incident",first["status"]);self.assertEqual("duplicate",second["status"])
 def test_operator_mutations_reject_wrong_token(self):
  with self.assertRaises(urllib.error.HTTPError) as caught:self.request("/api/v1/commands",{"action":"pause"},"wrong")
  self.assertEqual(401,caught.exception.code)
 def test_settings_update_confidence_floor(self):
  saved=self.operator("/api/v1/settings",{"retention_days":14,"max_records":200,"max_speed_mps":.25,"site_timezone":"Asia/Kolkata","alert_confidence_floor":.8})[1]
  self.assertEqual(.8,saved["alert_confidence_floor"]);self.assertEqual(.8,self.server.RequestHandlerClass.command_centre.confidence_floor)
 def test_integrations_expose_open_security_contract(self):
  capabilities=self.request("/api/v1/integrations")[1]["capabilities"]
  self.assertIn("security_systems",capabilities);self.assertIn("device_outputs",capabilities)

if __name__=="__main__":unittest.main()
