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


if __name__ == "__main__": unittest.main()
