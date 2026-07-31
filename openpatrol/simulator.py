from __future__ import annotations

import math
import threading
from dataclasses import asdict
from typing import Any

from .evidence import EvidenceStore
from .scenario import Scenario


class PatrolSimulator:
    LOW_BATTERY = 18.0

    def __init__(self, scenario: Scenario, evidence: EvidenceStore, robot_id: str = "openpatrol-one"):
        self.scenario, self.evidence, self.robot_id = scenario, evidence, robot_id
        first = scenario.waypoints[0]
        self.x, self.y = first.x, first.y
        self.target_index, self.current_waypoint, self.dwell_remaining = 1, first.id, first.dwell_ticks
        self.lap, self.battery, self.distance, self.tick_count = 0, 100.0, 0.0, 0
        self.status, self.speed, self.fault = "patrolling", 1.8, None
        self._emitted: dict[str, int] = {}
        self._lock = threading.RLock()

    def tick(self) -> None:
        with self._lock:
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
            if remaining <= self.speed:
                self.distance += remaining
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
                self.current_waypoint = None
            self.battery = max(5.0, 100.0 - self.distance * 0.018)

    def command(self, action: str) -> None:
        with self._lock:
            if action == "estop":
                self.status, self.fault = "estopped", "operator emergency stop"
            elif action == "reset-estop" and self.status == "estopped":
                self.status, self.fault = "paused", None
            elif action == "pause" and self.status == "patrolling":
                self.status = "paused"
            elif action == "resume" and self.status in {"paused", "docked"}:
                was_docked = self.status == "docked"
                self.status, self.fault = "patrolling", None
                if was_docked: self.battery = 100.0
            elif action == "return" and self.status not in {"estopped", "fault"}:
                self.status, self.target_index, self.dwell_remaining = "returning", 0, 0
            else:
                raise ValueError(f"command {action!r} is not allowed while {self.status}")

    def set_status(self, status: str) -> None:
        self.command("resume" if status == "patrolling" else "pause")

    def ingest_detection(self, event: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            waypoint = min(self.scenario.waypoints, key=lambda item: math.hypot(item.x - self.x, item.y - self.y))
            return self.evidence.create(robot_id=self.robot_id, site_id=self.scenario.site_id, lap=self.lap, waypoint=asdict(waypoint), event=event, source=str(event.get("source", "external")))

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
