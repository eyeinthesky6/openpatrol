import json
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
            for _ in range(30): sim.tick()
            state=sim.state()
            self.assertGreaterEqual(state["robot"]["lap"],1)
            self.assertEqual(1,len(state["incidents"]))

    def test_pause_freezes_position(self):
        scenario=Scenario("s","test",20,20,(Waypoint("a",0,0,0),Waypoint("b",10,0,1)),())
        with tempfile.TemporaryDirectory() as directory:
            sim=PatrolSimulator(scenario,EvidenceStore(Path(directory)))
            sim.set_status("paused"); before=sim.state()["robot"]; sim.tick(); after=sim.state()["robot"]
            self.assertEqual((before["x"],before["y"]),(after["x"],after["y"]))
            with self.assertRaises(ValueError): sim.set_status("flying")

    def test_restart_preserves_event_cooldown(self):
        scenario=Scenario("s","test",20,20,(Waypoint("a",0,0,0),Waypoint("b",1,0,0)),(SyntheticEvent("e","b","person","Detected","high",.9,2),))
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/"state.json"; evidence=EvidenceStore(Path(directory)/"evidence"); sim=PatrolSimulator(scenario,evidence,state_path=path)
            for _ in range(8): sim.tick()
            self.assertEqual(1,len(evidence.list())); sim.command("pause")
            restored=PatrolSimulator(scenario,evidence,state_path=path); restored.command("resume")
            for _ in range(8): restored.tick()
            self.assertEqual(1,len(evidence.list()))

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
            for _ in range(70): sim.tick()
            self.assertEqual("docked",sim.state()["robot"]["status"])

    def test_dock_charges_gradually_and_enforces_reserve(self):
        scenario=Scenario("s","test",20,20,(Waypoint("dock",0,0,0),Waypoint("b",2,0,0)),())
        with tempfile.TemporaryDirectory() as directory:
            sim=PatrolSimulator(scenario,EvidenceStore(Path(directory))); sim.status="docked"; sim.battery=10
            sim.tick(); self.assertEqual(10.02,sim.battery)
            with self.assertRaises(ValueError): sim.command("resume")
            for _ in range(651): sim.tick()
            sim.command("resume"); self.assertEqual("patrolling",sim.status)

    def test_dwell_consumes_energy_and_return_budget_includes_distance(self):
        scenario=Scenario("s","test",10000,20,(Waypoint("dock",0,0,2),Waypoint("far",1000,0,0)),())
        with tempfile.TemporaryDirectory() as directory:
            sim=PatrolSimulator(scenario,EvidenceStore(Path(directory))); before=sim.battery; sim.tick()
            self.assertLess(sim.battery,before); sim.x=1000
            self.assertGreater(sim.return_energy_required(),sim.LOW_BATTERY)

    def test_restart_restores_progress_but_requires_safe_resume(self):
        scenario=Scenario("s","test",20,20,(Waypoint("dock",0,0,0),Waypoint("b",10,0,0)),())
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/"state.json"; evidence=EvidenceStore(Path(directory)/"evidence"); sim=PatrolSimulator(scenario,evidence,state_path=path)
            for _ in range(20): sim.tick()
            sim.command("pause"); before=sim.state()["robot"]; restored=PatrolSimulator(scenario,evidence,state_path=path); after=restored.state()["robot"]
            self.assertEqual("paused",after["status"]); self.assertAlmostEqual(before["distance"],after["distance"],places=1); self.assertIn("restart",after["fault"])

    def test_non_finite_runtime_state_fails_safe(self):
        scenario=Scenario("s","test",20,20,(Waypoint("dock",0,0,0),Waypoint("b",1,0,0)),())
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/"state.json"; path.write_text(json.dumps({"schema_version":2,"x":float("nan"),"y":0,"target_index":0,"dwell_remaining":0,"lap":0,"battery":50,"distance":0,"tick_count":0,"status":"patrolling"}))
            sim=PatrolSimulator(scenario,EvidenceStore(Path(directory)/"evidence"),state_path=path)
            self.assertEqual("fault",sim.status); self.assertIn("could not be restored",sim.fault)


if __name__ == "__main__": unittest.main()
