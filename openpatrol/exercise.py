"""Accelerated digital-twin operational exercise for release and pilot readiness."""
from __future__ import annotations
import argparse,json,tempfile,uuid
from datetime import datetime,timezone
from pathlib import Path
from .audit import AuditLog
from .evidence import EvidenceStore
from .frigate_bridge import normalize_frigate_event
from .scenario import load_scenario
from .simulator import PatrolSimulator

ROOT=Path(__file__).resolve().parent.parent

def run_exercise(*,ticks:int=72000,tick_seconds:float=.4,workdir:Path|None=None)->dict:
    if ticks<100 or tick_seconds<=0: raise ValueError("exercise requires at least 100 positive-duration ticks")
    owned=None
    if workdir is None: owned=tempfile.TemporaryDirectory(); workdir=Path(owned.name)
    workdir.mkdir(parents=True,exist_ok=True); evidence=EvidenceStore(workdir/"evidence",retention_days=365,max_records=20000,signing_key="exercise-device-key"); audit=AuditLog(workdir/"audit.jsonl"); state_path=workdir/"runtime-state.json"; sim=PatrolSimulator(load_scenario(ROOT/"scenarios"/"warehouse.json"),evidence,state_path=state_path)
    if sim.status=="paused": sim.command("resume")
    stopped_motion_checks=[]; injected=0; dock_cycles=0
    for index in range(ticks):
        sim.tick()
        if sim.status=="docked" and sim.battery>=80:
            sim.command("resume"); audit.append("exercise.depart_dock",details={"tick":index,"battery":round(sim.battery,1)}); dock_cycles+=1
        if index and index%18000==0:
            before=(sim.x,sim.y); sim.command("estop"); audit.append("exercise.estop",details={"tick":index})
            for _ in range(20): sim.tick()
            stopped_motion_checks.append(before==(sim.x,sim.y)); sim.command("reset-estop"); sim.command("resume")
        if index and index%24000==0:
            before=(sim.x,sim.y); sim.command("inject-localization-fault"); audit.append("exercise.fault",details={"tick":index,"kind":"localization"})
            for _ in range(20): sim.tick()
            stopped_motion_checks.append(before==(sim.x,sim.y)); sim.command("clear-fault"); sim.command("resume")
        if index and index%15000==0:
            event=normalize_frigate_event({"type":"new","after":{"id":f"exercise-{index}","label":"person","camera":"patrol","top_score":.88}},"http://frigate.invalid")
            receipt=sim.ingest_detection(event); audit.append("detection.ingest",actor="exercise-frigate",details={"event_id":receipt["event_id"]}); injected+=1
    sim._persist(); before_restart=sim.state()["robot"]; restored=PatrolSimulator(sim.scenario,evidence,state_path=state_path); restart_safe=restored.status in {"paused","docked"} and abs(restored.distance-before_restart["distance"])<.11
    receipts=evidence.list()
    for receipt in receipts:
        if receipt["review"]["status"]=="pending": evidence.update_review(receipt["event_id"],"confirmed","exercise auto-review",actor="exercise-operator"); audit.append("incident.review",actor="exercise-operator",details={"event_id":receipt["event_id"]})
    verifications=[evidence.verify(item["event_id"]) for item in evidence.list()]; audit_result=audit.verify(); state=restored.state()["robot"]
    maximum_distance=sim.speed*(ticks+len(stopped_motion_checks)*20)+1
    checks={"safety_states_stop_motion":bool(stopped_motion_checks) and all(stopped_motion_checks),"restart_enters_safe_state":restart_safe,"all_receipts_valid":bool(verifications) and all(item["valid"] for item in verifications),"all_receipts_signed":bool(verifications) and all(item["signature_valid"] for item in verifications),"audit_chain_valid":audit_result["valid"],"battery_bounded":5<=state["battery"]<=100,"route_progressed":state["lap"]>0,"distance_physically_possible":0<state["distance"]<=maximum_distance,"external_detector_exercised":injected>0}
    report={"schema_version":"openpatrol.exercise/v1","generated_at":datetime.now(timezone.utc).isoformat(),"result":"pass" if all(checks.values()) else "fail","configuration":{"ticks":ticks,"tick_seconds":tick_seconds,"simulated_hours":round(ticks*tick_seconds/3600,2),"nominal_speed_mps":round(sim.speed/tick_seconds,2)},"metrics":{"laps":state["lap"],"distance_m":state["distance"],"battery_percent":state["battery"],"incidents":len(verifications),"external_detections":injected,"audit_entries":audit_result["entries"],"safety_interruptions":len(stopped_motion_checks),"completed_charge_cycles":dock_cycles},"checks":checks}
    if owned: owned.cleanup()
    return report

def main()->None:
    parser=argparse.ArgumentParser(); parser.add_argument("--ticks",type=int,default=72000); parser.add_argument("--tick-seconds",type=float,default=.4); parser.add_argument("--output",type=Path,default=Path("runtime/exercise-report.json")); args=parser.parse_args(); run_dir=args.output.parent/"exercise-runs"/uuid.uuid4().hex; report=run_exercise(ticks=args.ticks,tick_seconds=args.tick_seconds,workdir=run_dir); args.output.parent.mkdir(parents=True,exist_ok=True); args.output.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8"); print(json.dumps(report,indent=2)); raise SystemExit(0 if report["result"]=="pass" else 1)
if __name__=="__main__": main()
