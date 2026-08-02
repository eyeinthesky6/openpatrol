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
GROUND_REQUIRED_TOPICS = {
    "command": "/cmd_vel_safe",
    "odometry": "/odom",
    "scan": "/scan",
    "battery": "/battery_state",
    "estop": "/hardware/estop",
}
AIR_REQUIRED_TOPICS = {
    "command": "/air/cmd_vel_safe",
    "odometry": "/air/odom",
    "battery": "/battery_state",
    "flight_state": "/air/flight_state",
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


def _mobility_kind(profile: dict[str, Any]) -> str:
    # v1 profiles shipped before the family expansion did not include mobility.kind.
    return str(profile.get("mobility", {}).get("kind", "ground_wheeled"))


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
        allows_bool = expected is bool or (isinstance(expected, tuple) and bool in expected)
        if not isinstance(current, expected) or (isinstance(current, bool) and not allows_bool):
            errors.append(f"{path} has the wrong type")
            return None
        return current

    def require_bool(path: str) -> bool | None:
        value = require(path, bool)
        return value if isinstance(value, bool) else None

    if profile.get("profile_version") != PROFILE_VERSION:
        errors.append(f"profile_version must be {PROFILE_VERSION}")

    kind = _mobility_kind(profile)
    if kind not in {"ground_wheeled", "aerial_multirotor"}:
        errors.append("mobility.kind must be ground_wheeled or aerial_multirotor")

    profile_id = require("id", str)
    status = require("status", str)
    length_mm = require("chassis.length_mm", (int, float))
    width_mm = require("chassis.width_mm", (int, float))
    height_mm = require("chassis.height_mm", (int, float))
    battery_v = require("power.battery_nominal_v", (int, float))
    battery_ah = require("power.battery_ah", (int, float))
    average_w = require("power.average_load_w", (int, float))
    estimated_bom_inr = require("cost.estimated_bom_inr", (int, float))
    target_envelope_inr = profile.get("cost", {}).get("target_envelope_inr", 40000)
    max_total_kg = require("mass.max_total_kg", (int, float))
    max_payload_kg = require("mass.max_payload_kg", (int, float))

    positive_values = {
        "chassis.length_mm": length_mm,
        "chassis.width_mm": width_mm,
        "chassis.height_mm": height_mm,
        "power.battery_nominal_v": battery_v,
        "power.battery_ah": battery_ah,
        "power.average_load_w": average_w,
        "cost.estimated_bom_inr": estimated_bom_inr,
        "mass.max_total_kg": max_total_kg,
    }
    for key, value in positive_values.items():
        if isinstance(value, (int, float)) and value <= 0:
            errors.append(f"{key} must be positive")
    if not isinstance(target_envelope_inr, (int, float)) or isinstance(target_envelope_inr, bool):
        errors.append("cost.target_envelope_inr has the wrong type")
    elif target_envelope_inr <= 0:
        errors.append("cost.target_envelope_inr must be positive")
    elif isinstance(estimated_bom_inr, (int, float)) and estimated_bom_inr > target_envelope_inr:
        errors.append("cost.estimated_bom_inr exceeds cost.target_envelope_inr")

    if isinstance(max_payload_kg, (int, float)) and isinstance(max_total_kg, (int, float)):
        if max_payload_kg < 0:
            errors.append("mass.max_payload_kg cannot be negative")
        elif max_payload_kg >= max_total_kg:
            errors.append("mass.max_payload_kg must be below mass.max_total_kg")

    footprint = profile.get("chassis", {}).get("footprint_mm")
    if not isinstance(footprint, list) or len(footprint) < 3:
        errors.append("chassis.footprint_mm must contain at least three [x,y] points")
    elif isinstance(length_mm, (int, float)) and isinstance(width_mm, (int, float)):
        for point in footprint:
            if (
                not isinstance(point, list)
                or len(point) != 2
                or not all(isinstance(value, (int, float)) and not isinstance(value, bool) for value in point)
            ):
                errors.append("every chassis.footprint_mm point must be numeric [x,y]")
                break
            if abs(point[0]) > length_mm / 2 + 1 or abs(point[1]) > width_mm / 2 + 1:
                errors.append("chassis footprint extends beyond declared chassis dimensions")
                break

    usable_energy_wh = None
    if all(isinstance(value, (int, float)) and value > 0 for value in (battery_v, battery_ah, average_w)):
        usable_fraction = float(profile.get("power", {}).get("usable_fraction", 0.8))
        if not 0.5 <= usable_fraction <= 0.95:
            errors.append("power.usable_fraction must be between 0.5 and 0.95")
            usable_fraction = 0.8
        usable_energy_wh = float(battery_v) * float(battery_ah) * usable_fraction

    calculations: dict[str, float | None] = {
        "usable_energy_wh": round(usable_energy_wh, 1) if usable_energy_wh is not None else None,
    }

    if kind == "ground_wheeled":
        _validate_ground(
            profile,
            require,
            require_bool,
            errors,
            warnings,
            calculations,
            usable_energy_wh,
        )
    elif kind == "aerial_multirotor":
        _validate_air(
            profile,
            require,
            require_bool,
            errors,
            warnings,
            calculations,
            usable_energy_wh,
        )

    if status != "engineering-release-unvalidated":
        warnings.append("Only engineering-release-unvalidated is accepted before a physical build report")

    family = profile.get("visual", {}).get("family")
    if family != "openpatrol-plain-future-v1":
        warnings.append("visual.family should use the shared OpenPatrol industrial-design language")

    return {
        "valid": not errors,
        "profile_id": profile_id,
        "mobility_kind": kind,
        "source": profile.get("_source"),
        "errors": errors,
        "warnings": warnings,
        "calculations": calculations,
    }


def _validate_ground(
    profile: dict[str, Any],
    require: Any,
    require_bool: Any,
    errors: list[str],
    warnings: list[str],
    calculations: dict[str, float | None],
    usable_energy_wh: float | None,
) -> None:
    wheel_count = require("drive.wheel_count", int)
    wheel_diameter_mm = require("drive.wheel_diameter_mm", (int, float))
    motor_rpm = require("drive.motor_rpm", (int, float))
    max_speed_mps = require("drive.max_speed_mps", (int, float))
    declared_runtime_h = require("power.target_runtime_h", (int, float))
    timeout_ms = require("safety.command_timeout_ms", int)
    deceleration = require("safety.design_deceleration_mps2", (int, float))
    margin_m = require("safety.static_margin_m", (int, float))

    if wheel_count not in {2, 3, 4, 6}:
        errors.append("drive.wheel_count must be 2, 3, 4 or 6")
    for key, value in {
        "drive.wheel_diameter_mm": wheel_diameter_mm,
        "drive.motor_rpm": motor_rpm,
        "drive.max_speed_mps": max_speed_mps,
        "power.target_runtime_h": declared_runtime_h,
        "safety.design_deceleration_mps2": deceleration,
    }.items():
        if isinstance(value, (int, float)) and value <= 0:
            errors.append(f"{key} must be positive")

    theoretical_speed = None
    if all(isinstance(value, (int, float)) and value > 0 for value in (wheel_diameter_mm, motor_rpm)):
        theoretical_speed = math.pi * (float(wheel_diameter_mm) / 1000) * float(motor_rpm) / 60
        if isinstance(max_speed_mps, (int, float)) and max_speed_mps > theoretical_speed * 0.95:
            errors.append("drive.max_speed_mps exceeds 95% of no-load wheel-speed estimate; leave control margin")
        if isinstance(max_speed_mps, (int, float)) and max_speed_mps > 0.5:
            errors.append("reference indoor ground platforms are capped at 0.5 m/s")
    calculations["theoretical_no_load_speed_mps"] = round(theoretical_speed, 3) if theoretical_speed else None

    estimated_runtime_h = None
    if usable_energy_wh is not None:
        estimated_runtime_h = usable_energy_wh / float(profile["power"]["average_load_w"])
        if isinstance(declared_runtime_h, (int, float)) and declared_runtime_h > estimated_runtime_h:
            errors.append("power.target_runtime_h exceeds the usable-energy estimate")
    calculations["estimated_runtime_h"] = round(estimated_runtime_h, 2) if estimated_runtime_h else None

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
    calculations["design_stop_distance_m"] = round(stop_distance_m, 3) if stop_distance_m else None

    if isinstance(timeout_ms, int) and not 50 <= timeout_ms <= 250:
        errors.append("safety.command_timeout_ms must be between 50 and 250")
    if profile.get("safety", {}).get("estop_architecture") != "normally_closed_hardwired_drive_cut":
        errors.append("safety.estop_architecture must independently cut drive power")
    if int(profile.get("safety", {}).get("bumper_switch_count", 0)) < 3:
        errors.append("at least three normally-closed bumper switches are required")
    if require_bool("safety.independent_motor_watchdog") is False:
        errors.append("safety.independent_motor_watchdog must be true")
    if require_bool("safety.charging_drive_interlock") is False:
        errors.append("safety.charging_drive_interlock must be true")

    topics = profile.get("ros", {}).get("topics", {})
    _validate_topics(topics, GROUND_REQUIRED_TOPICS, errors)

    mast = profile.get("mast")
    if mast is not None:
        _validate_mast(profile, require, require_bool, errors, calculations)

    if profile.get("power", {}).get("battery_chemistry") != "LiFePO4":
        warnings.append("LiFePO4 is the preferred baseline chemistry for ground platforms")


def _validate_mast(
    profile: dict[str, Any],
    require: Any,
    require_bool: Any,
    errors: list[str],
    calculations: dict[str, float | None],
) -> None:
    retracted = require("mast.retracted_sensor_height_mm", (int, float))
    extended = require("mast.extended_sensor_height_mm", (int, float))
    travel = require("mast.travel_mm", (int, float))
    max_head_mass = require("mast.max_head_mass_kg", (int, float))
    head_mass = require("mast.head_mass_kg", (int, float))
    extended_speed = require("mast.max_drive_speed_extended_mps", (int, float))
    mast_timeout = require("mast.command_timeout_ms", int)
    tilt_interlock_degrees = require("mast.tilt_interlock_degrees", (int, float))
    for key, value in {
        "mast.retracted_sensor_height_mm": retracted,
        "mast.extended_sensor_height_mm": extended,
        "mast.travel_mm": travel,
        "mast.max_head_mass_kg": max_head_mass,
        "mast.head_mass_kg": head_mass,
        "mast.max_drive_speed_extended_mps": extended_speed,
        "mast.tilt_interlock_degrees": tilt_interlock_degrees,
    }.items():
        if isinstance(value, (int, float)) and value <= 0:
            errors.append(f"{key} must be positive")
    if all(isinstance(value, (int, float)) for value in (retracted, extended, travel)):
        if extended <= retracted:
            errors.append("mast.extended_sensor_height_mm must exceed retracted height")
        if abs((extended - retracted) - travel) > 25:
            errors.append("mast.travel_mm must match the declared height change within 25 mm")
    if all(isinstance(value, (int, float)) for value in (head_mass, max_head_mass)) and head_mass > max_head_mass:
        errors.append("mast.head_mass_kg exceeds mast.max_head_mass_kg")
    if isinstance(extended_speed, (int, float)):
        drive_speed = profile.get("drive", {}).get("max_speed_mps")
        if isinstance(drive_speed, (int, float)) and extended_speed >= drive_speed:
            errors.append("mast.max_drive_speed_extended_mps must be below normal drive speed")
        if extended_speed > 0.2:
            errors.append("mast extended drive speed is capped at 0.2 m/s")
    if isinstance(mast_timeout, int) and not 100 <= mast_timeout <= 1000:
        errors.append("mast.command_timeout_ms must be between 100 and 1000")
    for path in (
        "mast.upper_limit_switch",
        "mast.lower_limit_switch",
        "mast.self_locking_or_braked",
        "mast.tilt_interlock",
        "mast.docking_requires_retracted",
    ):
        if require_bool(path) is False:
            errors.append(f"{path} must be true")
    calculations["mast_height_change_mm"] = (
        round(float(extended) - float(retracted), 1)
        if isinstance(retracted, (int, float)) and isinstance(extended, (int, float))
        else None
    )
    chassis = profile.get("chassis", {})
    cg_height_mm = profile.get("mass", {}).get("cg_height_max_mm")
    static_tip_angle_deg = None
    if all(
        isinstance(value, (int, float)) and value > 0
        for value in (chassis.get("length_mm"), chassis.get("width_mm"), cg_height_mm)
    ):
        half_span_mm = min(float(chassis["length_mm"]), float(chassis["width_mm"])) / 2
        static_tip_angle_deg = math.degrees(math.atan(half_span_mm / float(cg_height_mm)))
        if isinstance(tilt_interlock_degrees, (int, float)):
            if not 2 <= tilt_interlock_degrees <= 12:
                errors.append("mast.tilt_interlock_degrees must be between 2 and 12")
            elif tilt_interlock_degrees >= static_tip_angle_deg * 0.5:
                errors.append("mast tilt interlock must trip below half the ideal static tip angle")
    calculations["ideal_static_tip_angle_deg"] = (
        round(static_tip_angle_deg, 1) if static_tip_angle_deg is not None else None
    )


def _validate_air(
    profile: dict[str, Any],
    require: Any,
    require_bool: Any,
    errors: list[str],
    warnings: list[str],
    calculations: dict[str, float | None],
    usable_energy_wh: float | None,
) -> None:
    motor_count = require("airframe.motor_count", int)
    prop_diameter_in = require("airframe.prop_diameter_in", (int, float))
    max_takeoff_mass_kg = require("airframe.max_takeoff_mass_kg", (int, float))
    hover_throttle = require("performance.target_hover_throttle", (int, float))
    max_horizontal = require("performance.max_horizontal_speed_mps", (int, float))
    max_vertical = require("performance.max_vertical_speed_mps", (int, float))
    target_flight_min = require("performance.target_flight_time_min", (int, float))
    timeout_ms = require("safety.command_timeout_ms", int)

    if motor_count not in {4, 6, 8}:
        errors.append("airframe.motor_count must be 4, 6 or 8")
    for key, value in {
        "airframe.prop_diameter_in": prop_diameter_in,
        "airframe.max_takeoff_mass_kg": max_takeoff_mass_kg,
        "performance.max_horizontal_speed_mps": max_horizontal,
        "performance.max_vertical_speed_mps": max_vertical,
        "performance.target_flight_time_min": target_flight_min,
    }.items():
        if isinstance(value, (int, float)) and value <= 0:
            errors.append(f"{key} must be positive")
    if isinstance(hover_throttle, (int, float)) and not 0.3 <= hover_throttle <= 0.65:
        errors.append("performance.target_hover_throttle must be between 0.30 and 0.65")
    if isinstance(max_takeoff_mass_kg, (int, float)):
        max_total = profile.get("mass", {}).get("max_total_kg")
        if isinstance(max_total, (int, float)) and abs(max_takeoff_mass_kg - max_total) > 0.05:
            errors.append("airframe.max_takeoff_mass_kg must match mass.max_total_kg within 0.05 kg")
    if isinstance(timeout_ms, int) and not 200 <= timeout_ms <= 1000:
        errors.append("aerial safety.command_timeout_ms must be between 200 and 1000")

    for path in (
        "safety.flight_controller_failsafe",
        "safety.geofence_enabled",
        "safety.battery_failsafe",
        "safety.arming_interlock",
        "safety.propeller_guards_required_indoor",
    ):
        if require_bool(path) is False:
            errors.append(f"{path} must be true")
    if profile.get("safety", {}).get("command_loss_action") not in {"hover_then_land", "land"}:
        errors.append("safety.command_loss_action must be hover_then_land or land")

    topics = profile.get("ros", {}).get("topics", {})
    _validate_topics(topics, AIR_REQUIRED_TOPICS, errors)

    estimated_flight_min = None
    if usable_energy_wh is not None:
        estimated_flight_min = usable_energy_wh / float(profile["power"]["average_load_w"]) * 60
        if isinstance(target_flight_min, (int, float)) and target_flight_min > estimated_flight_min:
            errors.append("performance.target_flight_time_min exceeds the usable-energy estimate")
    calculations["estimated_flight_time_min"] = round(estimated_flight_min, 1) if estimated_flight_min else None
    calculations["disk_area_m2"] = (
        round(motor_count * math.pi * (float(prop_diameter_in) * 0.0254 / 2) ** 2, 3)
        if isinstance(motor_count, int) and isinstance(prop_diameter_in, (int, float))
        else None
    )

    if profile.get("power", {}).get("battery_chemistry") not in {"LiPo", "Li-ion"}:
        warnings.append("AirScout baseline expects a high-discharge LiPo or qualified Li-ion pack")


def _validate_topics(topics: Any, expected_topics: dict[str, str], errors: list[str]) -> None:
    if not isinstance(topics, dict):
        errors.append("ros.topics must be an object")
        return
    for name, expected in expected_topics.items():
        if topics.get(name) != expected:
            errors.append(f"ros.topics.{name} must be {expected}")
