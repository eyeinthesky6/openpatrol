from __future__ import annotations

import math
import threading
from dataclasses import asdict
from typing import Any

from .evidence import EvidenceStore
from .scenario import Scenario


class PatrolSimulator:
    def __init__(self, scenario: Scenario, evidence: EvidenceStore, robot_id: str = "openpatrol-one"):
        self.scenario = scenario
        self.evidence = evidence
        self.robot_id = robot_id
        first = scenario.waypoints[0]
        self.x, self.y = first.x, first.y
        self.target_index = 1
        self.current_waypoint = first.id
        self.dwell_remaining = first.dwell_ticks
        self.lap = 0
        self.battery = 100.0
        self.distance = 0.0
        self.status = "patrolling"
        self.speed = 1.8
        self.tick_count = 0
        self._emitted: dict[str, int] = {}
        self._lock = threading.RLock()

    def tick(self) -> None:
        with self._lock:
            if self.status != "patrolling":
                return
            self.tick_count += 1
            if self.dwell_remaining > 0:
                self.dwell_remaining -= 1
                self._detect_at(self.current_waypoint)
                return
            target = self.scenario.waypoints[self.target_index]
            dx, dy = target.x - self.x, target.y - self.y
            remaining = math.hypot(dx, dy)
            if remaining <= self.speed:
                self.distance += remaining
                self.x, self.y = target.x, target.y
                self.current_waypoint = target.id
                self.dwell_remaining = target.dwell_ticks
                self.target_index += 1
                if self.target_index >= len(self.scenario.waypoints):
                    self.target_index = 0
                    self.lap += 1
                self._detect_at(target.id)
            else:
                self.x += dx / remaining * self.speed
                self.y += dy / remaining * self.speed
                self.distance += self.speed
                self.current_waypoint = None
            self.battery = max(5.0, 100.0 - self.distance * 0.018)

    def _detect_at(self, waypoint_id: str | None) -> None:
        if waypoint_id is None:
            return
        waypoint = next(item for item in self.scenario.waypoints if item.id == waypoint_id)
        for event in self.scenario.events:
            last_lap = self._emitted.get(event.id, -event.cooldown_laps)
            if event.waypoint_id == waypoint_id and self.lap - last_lap >= event.cooldown_laps:
                self.evidence.create(
                    robot_id=self.robot_id,
                    site_id=self.scenario.site_id,
                    lap=self.lap,
                    waypoint=asdict(waypoint),
                    event=asdict(event),
                )
                self._emitted[event.id] = self.lap

    def set_status(self, status: str) -> None:
        if status not in {"patrolling", "paused"}:
            raise ValueError("invalid patrol status")
        with self._lock:
            self.status = status

    def state(self) -> dict[str, Any]:
        with self._lock:
            target = self.scenario.waypoints[self.target_index]
            return {
                "robot": {
                    "id": self.robot_id,
                    "x": round(self.x, 2), "y": round(self.y, 2),
                    "status": self.status,
                    "battery": round(self.battery, 1),
                    "lap": self.lap,
                    "target": target.id,
                    "distance": round(self.distance, 1),
                },
                "site": {
                    "id": self.scenario.site_id,
                    "name": self.scenario.name,
                    "width": self.scenario.width,
                    "height": self.scenario.height,
                    "waypoints": [asdict(item) for item in self.scenario.waypoints],
                },
                "incidents": self.evidence.list(),
            }
