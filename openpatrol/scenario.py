from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Waypoint:
    id: str
    x: float
    y: float
    dwell_ticks: int = 2


@dataclass(frozen=True)
class SyntheticEvent:
    id: str
    waypoint_id: str
    event_type: str
    title: str
    severity: str
    confidence: float
    cooldown_laps: int = 2


@dataclass(frozen=True)
class Scenario:
    site_id: str
    name: str
    width: int
    height: int
    waypoints: tuple[Waypoint, ...]
    events: tuple[SyntheticEvent, ...]


def load_scenario(path: Path) -> Scenario:
    raw = json.loads(path.read_text(encoding="utf-8"))
    waypoints = tuple(Waypoint(**item) for item in raw["waypoints"])
    ids = {item.id for item in waypoints}
    if len(ids) != len(waypoints) or len(waypoints) < 2:
        raise ValueError("scenario needs at least two uniquely named waypoints")
    events = tuple(SyntheticEvent(**item) for item in raw.get("events", []))
    if any(event.waypoint_id not in ids for event in events):
        raise ValueError("every event must reference an existing waypoint")
    return Scenario(
        site_id=raw["site_id"],
        name=raw["name"],
        width=int(raw["map"]["width"]),
        height=int(raw["map"]["height"]),
        waypoints=waypoints,
        events=events,
    )
