"""Validation for OpenPatrol mechanical/electrical reference profiles.

The profiles make the software-to-hardware boundary reviewable without pretending
that a CAD release has passed physical validation.
"""
from __future__ import annotations

import json
import math
from importlib import resources
from pathlib import Path
from typing import Any

PROFILE_VERSION = "openpatrol.hardware/v1"
REQUIRED_TOPICS = {
    "command": "/cmd_vel_safe",
    "odometry": "/odom",
    "scan": "/scan",
    "battery": "/battery_state",
    "estop": "/hardware/estop",
}


class HardwareProfileError(ValueError):
    pass


def builtin_profiles() -> dict[str, Path]:
    root = resources.files("openpatrol").joinpath("profiles")
    return {
        item.name.removesuffix(".json"): Path(str(item))
        for item in root.iterdir()
        if item.name.endswith(".json")
    }


def load_profile(value: str | Path) -> dict[str, Any]:
    path = Path(value)
    if not path.exists():
        builtins = builtin_profiles()
        key = str(value).removesuffix(".json")
        if key not in builtins:
            raise HardwareProfileError(
                f"Unknown profile {value!s}; choose one of: {', '.join(sorted(builtins))}"
            )
        path = builtins[key]
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise HardwareProfileError(f"Cannot read hardware profile {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise HardwareProfileError("Hardware profile must be a JSON object")
    data["_source"] = str(path)
    return data


def validate_profile(profile: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []

    def require(path: str, expected: type | tuple[type, ...]) -> Any:
        current: Any = profile
        for part in path.split("."):
            if not isinstance(current, dict) or part not in current:
                errors.append(f"missing {path}")
                return None
            current = current[part]
        if not isinstance(current, expected) or isinstance(current, bool):
            errors.append(f"{path} has the wrong type")
            return None
        return current

    if profile.get("profile_version") != PROFILE_VERSION:
        errors.append(f"profile_version must be {PROFILE_VERSION}")

    profile_id = require("id", str)
    status = require("status", str)
    length_mm = require("chassis.length_mm", (int, float))
    width_mm = require("chassis.width_mm", (int, float))
    height_mm = require("chassis.height_mm", (int, float))
    wheel_count = require("drive.wheel_count", int)
    wheel_diameter_mm = require("drive.wheel_diameter_mm", (int, float))
    motor_rpm = require("drive.motor_rpm", (int, float))
    max_speed_mps = require("drive.max_speed_mps", (int, float))
    battery_v = require("power.battery_nominal_v", (int, float))
    battery_ah = require("power.battery_ah", (int, float))
    average_w = require("power.average_load_w", (int, float))
    declared_runtime_h = require("power.target_runtime_h", (int, float))
    timeout_ms = require("safety.command_timeout_ms", int)
    deceleration = require("safety.design_deceleration_mps2", (int, float))
    margin_m = require("safety.static_margin_m", (int, float))
    estimated_bom_inr = require("cost.estimated_bom_inr", (int, float))
    max_total_kg = require("mass.max_total_kg", (int, float))
    max_payload_kg = require("mass.max_payload_kg", (int, float))

    positive_values = {
        "chassis.length_mm": length_mm,
        "chassis.width_mm": width_mm,
        "chassis.height_mm": height_mm,
        "drive.wheel_diameter_mm": wheel_diameter_mm,
        "drive.motor_rpm": motor_rpm,
        "drive.max_speed_mps": max_speed_mps,
        "power.battery_nominal_v": battery_v,
        "power.battery_ah": battery_ah,
        "power.average_load_w": average_w,
        "power.target_runtime_h": declared_runtime_h,
        "safety.design_deceleration_mps2": deceleration,
        "cost.estimated_bom_inr": estimated_bom_inr,
        "mass.max_total_kg": max_total_kg,
    }
    for key, value in positive_values.items():
        if isinstance(value, (int, float)) and value <= 0:
            errors.append(f"{key} must be positive")

    if wheel_count not in {2, 3, 4}:
        errors.append("drive.wheel_count must be 2, 3 or 4")
    if isinstance(max_payload_kg, (int, float)) and isinstance(max_total_kg, (int, float)):
        if max_payload_kg >= max_total_kg:
            errors.append("mass.max_payload_kg must be below mass.max_total_kg")

    theoretical_speed = None
    if all(isinstance(value, (int, float)) and value > 0 for value in (wheel_diameter_mm, motor_rpm)):
        theoretical_speed = math.pi * (float(wheel_diameter_mm) / 1000) * float(motor_rpm) / 60
        if isinstance(max_speed_mps, (int, float)) and max_speed_mps > theoretical_speed * 0.95:
            errors.append(
                "drive.max_speed_mps exceeds 95% of no-load wheel-speed estimate; leave control margin"
            )
        if isinstance(max_speed_mps, (int, float)) and max_speed_mps > 0.5:
            errors.append("reference indoor platforms are capped at 0.5 m/s")

    usable_energy_wh = None
    estimated_runtime_h = None
    if all(isinstance(value, (int, float)) and value > 0 for value in (battery_v, battery_ah, average_w)):
        usable_energy_wh = float(battery_v) * float(battery_ah) * 0.8
        estimated_runtime_h = usable_energy_wh / float(average_w)
        if isinstance(declared_runtime_h, (int, float)) and declared_runtime_h > estimated_runtime_h:
            errors.append("power.target_runtime_h exceeds the 80%-usable-energy estimate")

    stop_distance_m = None
    if all(isinstance(value, (int, float)) and value >= 0 for value in (max_speed_mps, deceleration, margin_m)):
        if deceleration == 0:
            errors.append("safety.design_deceleration_mps2 cannot be zero")
        elif isinstance(timeout_ms, int) and timeout_ms >= 0:
            stop_distance_m = (
                float(max_speed_mps) * timeout_ms / 1000
                + float(max_speed_mps) ** 2 / (2 * float(deceleration))
                + float(margin_m)
            )
    if isinstance(timeout_ms, int) and not 50 <= timeout_ms <= 250:
        errors.append("safety.command_timeout_ms must be between 50 and 250")
    if profile.get("safety", {}).get("estop_architecture") != "normally_closed_hardwired_drive_cut":
        errors.append("safety.estop_architecture must independently cut drive power")
    if int(profile.get("safety", {}).get("bumper_switch_count", 0)) < 3:
        errors.append("at least three normally-closed bumper switches are required")

    topics = profile.get("ros", {}).get("topics", {})
    if not isinstance(topics, dict):
        errors.append("ros.topics must be an object")
    else:
        for name, expected in REQUIRED_TOPICS.items():
            if topics.get(name) != expected:
                errors.append(f"ros.topics.{name} must be {expected}")

    footprint = profile.get("chassis", {}).get("footprint_mm")
    if not isinstance(footprint, list) or len(footprint) < 3:
        errors.append("chassis.footprint_mm must contain at least three [x,y] points")
    elif isinstance(length_mm, (int, float)) and isinstance(width_mm, (int, float)):
        for point in footprint:
            if (
                not isinstance(point, list)
                or len(point) != 2
                or not all(isinstance(value, (int, float)) for value in point)
            ):
                errors.append("every chassis.footprint_mm point must be numeric [x,y]")
                break
            if abs(point[0]) > length_mm / 2 + 1 or abs(point[1]) > width_mm / 2 + 1:
                errors.append("chassis footprint extends beyond declared chassis dimensions")
                break

    if status != "engineering-release-unvalidated":
        warnings.append("Only engineering-release-unvalidated is accepted before a physical build report")
    if isinstance(estimated_bom_inr, (int, float)) and estimated_bom_inr > 40000:
        warnings.append("BOM exceeds the target low-cost reference envelope of INR 40,000")
    if profile.get("power", {}).get("battery_chemistry") != "LiFePO4":
        warnings.append("LiFePO4 is the preferred baseline chemistry for the reference builds")

    return {
        "valid": not errors,
        "profile_id": profile_id,
        "source": profile.get("_source"),
        "errors": errors,
        "warnings": warnings,
        "calculations": {
            "theoretical_no_load_speed_mps": round(theoretical_speed, 3)
            if theoretical_speed is not None
            else None,
            "usable_energy_wh": round(usable_energy_wh, 1) if usable_energy_wh is not None else None,
            "estimated_runtime_h": round(estimated_runtime_h, 2)
            if estimated_runtime_h is not None
            else None,
            "design_stop_distance_m": round(stop_distance_m, 3)
            if stop_distance_m is not None
            else None,
        },
    }
