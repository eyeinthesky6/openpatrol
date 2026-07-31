import tempfile
import unittest
from pathlib import Path

from openpatrol.evidence import EvidenceStore
from openpatrol.scenario import Scenario, SyntheticEvent, Waypoint
from openpatrol.simulator import PatrolSimulator


class SimulatorTest(unittest.TestCase):
    def test_patrol_emits_event_and_completes_lap(self):
        scenario=Scenario("s","test",20,20,(Waypoint("a",0,0,0),Waypoint("b",2,0,1)),(SyntheticEvent("e","b","person","Detected","high",.9,2),))
        with tempfile.TemporaryDirectory() as directory:
            sim=PatrolSimulator(scenario,EvidenceStore(Path(directory)))
            for _ in range(8): sim.tick()
            state=sim.state()
            self.assertGreaterEqual(state["robot"]["lap"],1)
            self.assertEqual(1,len(state["incidents"]))

    def test_pause_freezes_position(self):
        scenario=Scenario("s","test",20,20,(Waypoint("a",0,0,0),Waypoint("b",10,0,1)),())
        with tempfile.TemporaryDirectory() as directory:
            sim=PatrolSimulator(scenario,EvidenceStore(Path(directory)))
            sim.set_status("paused"); before=sim.state()["robot"]; sim.tick(); after=sim.state()["robot"]
            self.assertEqual((before["x"],before["y"]),(after["x"],after["y"]))

    def test_estop_requires_reset_before_resume(self):
        scenario=Scenario("s","test",20,20,(Waypoint("a",0,0,0),Waypoint("b",10,0,1)),())
        with tempfile.TemporaryDirectory() as directory:
            sim=PatrolSimulator(scenario,EvidenceStore(Path(directory)))
            sim.command("estop"); self.assertEqual("estopped",sim.state()["robot"]["status"])
            with self.assertRaises(ValueError): sim.command("resume")
            sim.command("reset-estop"); sim.command("resume")
            self.assertEqual("patrolling",sim.state()["robot"]["status"])

    def test_return_to_dock(self):
        scenario=Scenario("s","test",20,20,(Waypoint("dock",0,0,0),Waypoint("b",10,0,1)),())
        with tempfile.TemporaryDirectory() as directory:
            sim=PatrolSimulator(scenario,EvidenceStore(Path(directory)))
            sim.tick(); sim.command("return")
            for _ in range(10): sim.tick()
            self.assertEqual("docked",sim.state()["robot"]["status"])

    def test_dock_charges_gradually_and_enforces_reserve(self):
        scenario=Scenario("s","test",20,20,(Waypoint("dock",0,0,0),Waypoint("b",2,0,0)),())
        with tempfile.TemporaryDirectory() as directory:
            sim=PatrolSimulator(scenario,EvidenceStore(Path(directory))); sim.status="docked"; sim.battery=10
            sim.tick(); self.assertEqual(10.5,sim.battery)
            with self.assertRaises(ValueError): sim.command("resume")
            for _ in range(30): sim.tick()
            sim.command("resume"); self.assertEqual("patrolling",sim.status)


if __name__ == "__main__": unittest.main()
