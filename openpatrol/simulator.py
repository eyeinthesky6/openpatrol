from __future__ import annotations

import math
import json
import threading
import uuid
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .evidence import EvidenceStore
from .scenario import Scenario


class PatrolSimulator:
    LOW_BATTERY = 18.0

    def __init__(self, scenario: Scenario, evidence: EvidenceStore, robot_id: str = "openpatrol-one", state_path: Path | None = None):
        self.scenario, self.evidence, self.robot_id = scenario, evidence, robot_id
        first = scenario.waypoints[0]
        self.x, self.y = first.x, first.y
        self.target_index, self.current_waypoint, self.dwell_remaining = 1, first.id, first.dwell_ticks
        self.lap, self.battery, self.distance, self.tick_count = 0, 100.0, 0.0, 0
        # Default server tick is 0.4 s, so 0.2 m/tick models the 0.5 m/s indoor limit.
        self.status, self.speed, self.fault = "patrolling", 0.2, None
        self._emitted: dict[str, int] = {}
        self._lock = threading.RLock()
        self.state_path = state_path
        self._restore()

    def tick(self) -> None:
        with self._lock:
            if self.status == "docked":
                self.battery = min(100.0, self.battery + 0.02)
                self._persist()
                return
            if self.status not in {"patrolling", "returning"}:
                return
            self.tick_count += 1
            if self.battery <= self.LOW_BATTERY and self.status == "patrolling":
                self.status, self.target_index = "returning", 0
            if self.dwell_remaining > 0 and self.status == "patrolling":
                self.dwell_remaining -= 1
                self._detect_at(self.current_waypoint)
                return
            target = self.scenario.waypoints[self.target_index]
            dx, dy = target.x - self.x, target.y - self.y
            remaining = math.hypot(dx, dy)
            moved = 0.0
            if remaining <= self.speed:
                self.distance += remaining
                moved = remaining
                self.x, self.y, self.current_waypoint = target.x, target.y, target.id
                if self.status == "returning" and self.target_index == 0:
                    self.status, self.dwell_remaining = "docked", 0
                else:
                    self.dwell_remaining = target.dwell_ticks
                    self.target_index = (self.target_index + 1) % len(self.scenario.waypoints)
                    if self.target_index == 0:
                        self.lap += 1
                    self._detect_at(target.id)
            else:
                self.x += dx / remaining * self.speed
                self.y += dy / remaining * self.speed
                self.distance += self.speed
                moved = self.speed
                self.current_waypoint = None
            self.battery = max(5.0, self.battery - moved * 0.018)
            if self.tick_count % 10 == 0: self._persist()

    def command(self, action: str) -> None:
        with self._lock:
            if action == "estop":
                self.status, self.fault = "estopped", "operator emergency stop"
            elif action == "reset-estop" and self.status == "estopped":
                self.status, self.fault = "paused", None
            elif action == "pause" and self.status == "patrolling":
                self.status = "paused"
            elif action == "resume" and self.status in {"paused", "docked"}:
                if self.status == "docked" and self.battery <= self.LOW_BATTERY + 5:
                    raise ValueError("battery reserve is too low to leave the dock")
                self.status, self.fault = "patrolling", None
            elif action == "return" and self.status not in {"estopped", "fault"}:
                self.status, self.target_index, self.dwell_remaining = "returning", 0, 0
            elif action in {"inject-localization-fault", "inject-drive-fault"}:
                self.status, self.fault = "fault", action.removeprefix("inject-").replace("-", " ")
            elif action == "clear-fault" and self.status == "fault":
                self.status, self.fault = "paused", None
            else:
                raise ValueError(f"command {action!r} is not allowed while {self.status}")
            self._persist()

    def set_status(self, status: str) -> None:
        self.command("resume" if status == "patrolling" else "pause")

    def ingest_detection(self, event: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            waypoint = min(self.scenario.waypoints, key=lambda item: math.hypot(item.x - self.x, item.y - self.y))
            media = None
            if event.get("media_reference"):
                media = {"kind": "external_reference", "reference": str(event["media_reference"])[:1000], "sha256": event.get("media_sha256")}
            return self.evidence.create(robot_id=self.robot_id, site_id=self.scenario.site_id, lap=self.lap, waypoint=asdict(waypoint), event=event, source=str(event.get("source", "external")), media=media)

    def _detect_at(self, waypoint_id: str | None) -> None:
        if waypoint_id is None:
            return
        waypoint = next(item for item in self.scenario.waypoints if item.id == waypoint_id)
        for event in self.scenario.events:
            last_lap = self._emitted.get(event.id, -event.cooldown_laps)
            if event.waypoint_id == waypoint_id and self.lap - last_lap >= event.cooldown_laps:
                self.evidence.create(robot_id=self.robot_id, site_id=self.scenario.site_id, lap=self.lap, waypoint=asdict(waypoint), event=asdict(event))
                self._emitted[event.id] = self.lap

    def state(self) -> dict[str, Any]:
        with self._lock:
            target = self.scenario.waypoints[self.target_index]
            return {
                "api_version": "v1", "mode": "simulation",
                "robot": {"id": self.robot_id, "x": round(self.x, 2), "y": round(self.y, 2), "status": self.status, "battery": round(self.battery, 1), "lap": self.lap, "target": target.id, "distance": round(self.distance, 1), "fault": self.fault, "estop": self.status == "estopped"},
                "site": {"id": self.scenario.site_id, "name": self.scenario.name, "width": self.scenario.width, "height": self.scenario.height, "waypoints": [asdict(item) for item in self.scenario.waypoints]},
                "incidents": self.evidence.list(),
            }

    def _persist(self) -> None:
        if not self.state_path: return
        payload={"schema_version":1,"x":self.x,"y":self.y,"target_index":self.target_index,"current_waypoint":self.current_waypoint,"dwell_remaining":self.dwell_remaining,"lap":self.lap,"battery":self.battery,"distance":self.distance,"tick_count":self.tick_count,"status":self.status}
        self.state_path.parent.mkdir(parents=True,exist_ok=True); temp=self.state_path.with_suffix(f".{uuid.uuid4().hex}.tmp"); temp.write_text(json.dumps(payload),encoding="utf-8"); temp.replace(self.state_path)

    def _restore(self) -> None:
        if not self.state_path or not self.state_path.exists(): return
        try:
            payload=json.loads(self.state_path.read_text(encoding="utf-8"))
            if payload.get("schema_version")!=1: return
            self.x=float(payload["x"]); self.y=float(payload["y"]); self.target_index=int(payload["target_index"])%len(self.scenario.waypoints); self.current_waypoint=payload.get("current_waypoint"); self.dwell_remaining=max(0,int(payload["dwell_remaining"])); self.lap=max(0,int(payload["lap"])); self.battery=max(5.0,min(100.0,float(payload["battery"]))); self.distance=max(0.0,float(payload["distance"])); self.tick_count=max(0,int(payload["tick_count"])); previous=payload.get("status")
            self.status="docked" if previous=="docked" else "paused"; self.fault=None if previous=="docked" else "restart requires operator resume"
        except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError):
            self.status,self.fault="fault","runtime state could not be restored"
