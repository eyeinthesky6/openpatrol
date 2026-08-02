"""Dependency-free decisions for the AirScout MAVROS setpoint stream."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class VelocityPublishDecision:
    publish: bool
    zero: bool
    streaming: bool
    reason: str


def velocity_publish_decision(
    *,
    authorized: bool,
    command_age_s: float,
    stale_s: float,
    was_streaming: bool,
) -> VelocityPublishDecision:
    """Choose whether to publish an active setpoint, one stop, or nothing.

    Continuing to stream zero setpoints after authorization loss can keep PX4 in
    OFFBOARD or ArduPilot in GUIDED and prevent its command-loss action. Therefore
    the bridge emits one immediate zero when an active stream drops, then becomes
    silent so the flight controller's configured land/RTL failsafe remains authoritative.
    """
    if stale_s <= 0:
        raise ValueError("stale_s must be positive")
    if command_age_s < 0:
        raise ValueError("command_age_s cannot be negative")
    fresh = command_age_s <= stale_s
    if authorized and fresh:
        return VelocityPublishDecision(True, False, True, "active")
    reason = "not_authorized" if not authorized else "command_stale"
    if was_streaming:
        return VelocityPublishDecision(True, True, False, reason)
    return VelocityPublishDecision(False, True, False, reason)
