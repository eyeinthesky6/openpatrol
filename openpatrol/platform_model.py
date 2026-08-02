"""Dependency-free acceptance models for platform-specific safety contracts.

These are deterministic contract tests, not high-fidelity physics. They prove that
profiles, software limits and failure-state transitions agree before hardware exists.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any


@dataclass
class AirState:
    x_m: float = 0.0
    y_m: float = 0.0
    z_m: float = 0.0
    yaw_rad: float = 0.0
    mode: str = "landed"


class AirScoutModel:
    def __init__(self, profile: dict[str, Any]) -> None:
        self.profile = profile
        performance = profile["performance"]
        safety = profile["safety"]
        self.max_horizontal = float(performance["indoor_speed_limit_mps"])
        self.max_vertical = min(1.0, float(performance["max_vertical_speed_mps"]))
        self.timeout_s = float(safety["command_timeout_ms"]) / 1000
        self.geofence_radius = float(safety.get("geofence_radius_m", 25.0))
        self.geofence_ceiling = float(safety.get("geofence_ceiling_m", 8.0))
        self.state = AirState()
        self.command = (0.0, 0.0, 0.0, 0.0)
        self.command_age_s = math.inf

    def arm_for_test(self, initial_height_m: float = 0.5) -> None:
        if initial_height_m <= 0 or initial_height_m > self.geofence_ceiling:
            raise ValueError("initial height must be inside the geofence")
        self.state.z_m = initial_height_m
        self.state.mode = "hold"

    def set_command(self, vx: float, vy: float, vz: float, yaw_rate: float) -> None:
        if not all(math.isfinite(v) for v in (vx, vy, vz, yaw_rate)):
            raise ValueError("flight command must be finite")
        horizontal = math.hypot(vx, vy)
        if horizontal > self.max_horizontal:
            scale = self.max_horizontal / horizontal
            vx *= scale
            vy *= scale
        self.command = (
            vx,
            vy,
            max(-self.max_vertical, min(self.max_vertical, vz)),
            max(-0.8, min(0.8, yaw_rate)),
        )
        self.command_age_s = 0.0
        if self.state.mode != "landed":
            self.state.mode = "velocity"

    def step(self, dt_s: float) -> AirState:
        if dt_s <= 0 or not math.isfinite(dt_s):
            raise ValueError("step time must be positive and finite")
        self.command_age_s += dt_s
        stale = self.command_age_s > self.timeout_s
        if self.state.mode == "landed":
            return self.state
        if stale:
            self.state.mode = "landing"
            vx = vy = yaw = 0.0
            vz = -0.4
        else:
            vx, vy, vz, yaw = self.command
        proposed_x = self.state.x_m + vx * dt_s
        proposed_y = self.state.y_m + vy * dt_s
        proposed_z = max(0.0, self.state.z_m + vz * dt_s)
        outside = math.hypot(proposed_x, proposed_y) > self.geofence_radius or proposed_z > self.geofence_ceiling
        if outside:
            self.state.mode = "landing"
            proposed_x, proposed_y = self.state.x_m, self.state.y_m
            proposed_z = max(0.0, self.state.z_m - 0.4 * dt_s)
            yaw = 0.0
        self.state.x_m, self.state.y_m, self.state.z_m = proposed_x, proposed_y, proposed_z
        self.state.yaw_rad = math.atan2(
            math.sin(self.state.yaw_rad + yaw * dt_s),
            math.cos(self.state.yaw_rad + yaw * dt_s),
        )
        if self.state.z_m == 0.0:
            self.state.mode = "landed"
        return self.state


@dataclass(frozen=True)
class SentinelDecision:
    commanded_linear_mps: float
    mast_allowed: bool
    docking_allowed: bool
    reason: str


class SentinelModel:
    def __init__(self, profile: dict[str, Any]) -> None:
        self.profile = profile
        self.normal_speed = float(profile["drive"]["max_speed_mps"])
        self.extended_speed = float(profile["mast"]["max_drive_speed_extended_mps"])
        self.retracted_height = int(profile["mast"]["retracted_sensor_height_mm"])
        self.extended_threshold = self.retracted_height + 140

    def decide(
        self,
        requested_linear_mps: float,
        mast_height_mm: int,
        *,
        tilt_fault: bool = False,
        charging: bool = False,
    ) -> SentinelDecision:
        if not math.isfinite(requested_linear_mps):
            raise ValueError("drive command must be finite")
        if tilt_fault:
            return SentinelDecision(0.0, False, False, "tilt_interlock")
        if charging:
            return SentinelDecision(0.0, False, mast_height_mm <= self.retracted_height + 10, "charger_interlock")
        extended = mast_height_mm >= self.extended_threshold
        limit = self.extended_speed if extended else self.normal_speed
        drive = max(-limit, min(limit, requested_linear_mps))
        moving = abs(drive) > 0.05
        mast_allowed = not moving
        docking_allowed = mast_height_mm <= self.retracted_height + 10 and not moving
        return SentinelDecision(drive, mast_allowed, docking_allowed, "mast_extended" if extended else "ready")
