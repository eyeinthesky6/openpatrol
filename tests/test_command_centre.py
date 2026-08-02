import tempfile
import unittest
from pathlib import Path
from openpatrol.command_centre import CommandCentre, DeviceRegistry, IncidentFusion


class FakeSimulator:
    def __init__(self): self.events=[]
    def ingest_detection(self,event):
        self.events.append(event);return {"event_id":f"evt-{len(self.events)}","detection":event}


class CommandCentreTest(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();root=Path(self.temp.name)
        self.devices=DeviceRegistry(root)
        self.devices.register({"id":"pool-hub","name":"Pool Hub","kind":"sensor_hub","zone":"pool","capabilities":["sensors","speaker","strobe","siren"],"metadata":{"global_alerts":False}})
        self.devices.register({"id":"control-room","name":"Control Room","kind":"speaker","zone":"control","capabilities":["speaker","strobe"],"metadata":{"global_alerts":True}})
        self.centre=CommandCentre(root,self.devices);self.sim=FakeSimulator()
    def tearDown(self): self.temp.cleanup()
    def event(self,**overrides):
        base={"id":"one","event_type":"motion","severity":"medium","confidence":.8,"source":"test","provider":"test","device_id":"cam","zone":"pool"};base.update(overrides);return base
    def test_weak_fall_remains_observation(self):
        result=self.centre.ingest(self.event(event_type="fall",confidence=.55),self.sim)
        self.assertEqual("observed",result["status"]);self.assertFalse(self.sim.events)
    def test_fall_plus_immobility_fuses(self):
        self.assertEqual("incident",self.centre.ingest(self.event(id="f",event_type="fall",confidence=.8),self.sim)["status"])
        result=self.centre.ingest(self.event(id="i",event_type="immobility",confidence=.8),self.sim)
        self.assertEqual("incident",result["status"]);self.assertEqual("fall",result["fusion"]["event_type"])
    def test_drowning_routes_neutral_warning_and_outputs(self):
        result=self.centre.ingest(self.event(event_type="drowning_distress",confidence=.91,severity="critical"),self.sim)
        self.assertEqual("incident",result["status"]);self.assertIn("Lifeguard",result["alert"]["automatic_message"])
        actions={c["action"] for c in self.devices.poll("pool-hub")}
        self.assertTrue({"speak","strobe","siren"}.issubset(actions))
        self.assertTrue(self.devices.poll("control-room"))
    def test_intrusion_fuses_door_and_person(self):
        self.assertEqual("observed",self.centre.ingest(self.event(id="d",event_type="door_open",confidence=.8),self.sim)["status"])
        result=self.centre.ingest(self.event(id="p",event_type="person",confidence=.82),self.sim)
        self.assertEqual("incident",result["status"]);self.assertEqual("intrusion",result["fusion"]["event_type"])
    def test_fight_is_operator_first(self):
        result=self.centre.ingest(self.event(event_type="fight",confidence=.9,severity="high"),self.sim)
        self.assertEqual("incident",result["status"]);self.assertIsNone(result["alert"]["automatic_message"])
    def test_duplicate_is_idempotent(self):
        event=self.event(event_type="panic",confidence=1,severity="critical")
        self.assertEqual("incident",self.centre.ingest(event,self.sim)["status"])
        self.assertEqual("duplicate",self.centre.ingest(event,self.sim)["status"]);self.assertEqual(1,len(self.sim.events))
    def test_command_queue_and_ack(self):
        cmd=self.devices.queue(["pool-hub"],"speak",{"text":"test"})[0]
        self.assertEqual(cmd["id"],self.devices.poll("pool-hub")[0]["id"])
        self.assertEqual("acknowledged",self.devices.acknowledge("pool-hub",cmd["id"],{"ok":True})["status"])
        self.assertFalse(self.devices.poll("pool-hub"))
    def test_combined_confidence_rewards_independent_devices(self):
        items=[{"event_type":"motion","confidence":.5,"device_id":"a","source":"a"},{"event_type":"person","confidence":.5,"device_id":"b","source":"b"}]
        self.assertGreater(IncidentFusion.combined_confidence(items),.75)

if __name__=="__main__":unittest.main()
