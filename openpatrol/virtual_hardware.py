"""Deterministic differential-drive hardware double for CI and fault testing."""
from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass
class HardwareConfig:
    max_linear_mps: float = 0.5
    max_angular_rps: float = 1.0
    command_timeout_s: float = 0.25
    battery_capacity_wh: float = 120.0
    idle_power_w: float = 8.0
    drive_power_w: float = 32.0

    def validate(self) -> None:
        values=asdict(self)
        if not all(math.isfinite(value) and value > 0 for value in values.values()):
            raise ValueError("hardware configuration values must be finite and positive")


class VirtualHardware:
    """A monotonic-time, deterministic hardware boundary; no wall clock is used."""
    FAULTS={"motor_stall","wheel_slip","encoder_dropout","lidar_dropout","camera_dropout","network_loss"}

    def __init__(self, config: HardwareConfig | None = None):
        self.config=config or HardwareConfig(); self.config.validate()
        self.x=self.y=self.yaw=0.0; self.linear=self.angular=0.0
        self.command_linear=self.command_angular=0.0; self.now=0.0; self.last_command_at=None
        self.battery_percent=100.0; self.estopped=True; self.faults:set[str]=set(); self.distance_m=0.0

    def set_estop(self, active: bool) -> None:
        self.estopped=bool(active)
        if self.estopped: self._stop()

    def inject(self, fault: str, active: bool = True) -> None:
        if fault not in self.FAULTS: raise ValueError(f"unknown virtual hardware fault: {fault}")
        self.faults.add(fault) if active else self.faults.discard(fault)
        if active and fault in {"motor_stall","network_loss"}: self._stop()

    def command(self, linear_mps: float, angular_rps: float) -> bool:
        if not all(math.isfinite(value) for value in (linear_mps,angular_rps)): raise ValueError("commands must be finite")
        if self.estopped or "network_loss" in self.faults or self.battery_percent <= 0: self._stop(); return False
        c=self.config
        self.command_linear=max(-c.max_linear_mps,min(c.max_linear_mps,linear_mps))
        self.command_angular=max(-c.max_angular_rps,min(c.max_angular_rps,angular_rps))
        self.last_command_at=self.now
        return True

    def tick(self, dt: float) -> None:
        if not math.isfinite(dt) or dt <= 0 or dt > 1: raise ValueError("tick duration must be finite and in (0, 1]")
        self.now+=dt
        stale=self.last_command_at is None or self.now-self.last_command_at > self.config.command_timeout_s
        blocked=self.estopped or stale or "network_loss" in self.faults or "motor_stall" in self.faults or self.battery_percent <= 0
        self.linear=0.0 if blocked else self.command_linear
        self.angular=0.0 if blocked else self.command_angular
        if "wheel_slip" in self.faults: self.linear*=0.35; self.angular*=0.65
        previous=(self.x,self.y)
        self.yaw=(self.yaw+self.angular*dt+math.pi)%(2*math.pi)-math.pi
        self.x+=math.cos(self.yaw)*self.linear*dt; self.y+=math.sin(self.yaw)*self.linear*dt
        self.distance_m+=math.hypot(self.x-previous[0],self.y-previous[1])
        power=self.config.idle_power_w+self.config.drive_power_w*min(1,abs(self.linear)/self.config.max_linear_mps)
        used_percent=power*dt/3600/self.config.battery_capacity_wh*100
        self.battery_percent=max(0.0,self.battery_percent-used_percent)
        if self.battery_percent == 0: self._stop()

    def telemetry(self) -> dict[str, Any]:
        stale=self.last_command_at is None or self.now-self.last_command_at > self.config.command_timeout_s
        pose=None if "encoder_dropout" in self.faults else {"x":self.x,"y":self.y,"yaw":self.yaw}
        return {"time":self.now,"pose":pose,"battery_percent":self.battery_percent,"velocity":{"linear":self.linear,"angular":self.angular},
                "estop":self.estopped,"command_stale":stale,"lidar_ok":"lidar_dropout" not in self.faults,
                "camera_ok":"camera_dropout" not in self.faults,"faults":sorted(self.faults)}

    def _stop(self) -> None:
        self.command_linear=self.command_angular=self.linear=self.angular=0.0


def run_acceptance(output: Path | None = None) -> dict[str, Any]:
    """Exercise clamps, watchdog, E-stop, dropout, stall, slip and recovery."""
    hw=VirtualHardware(); checks:dict[str,bool]={}
    hw.set_estop(False); checks["velocity_clamped"]=hw.command(4,3)
    hw.tick(.1); checks["clamp_enforced"]=hw.linear <= .5 and hw.angular <= 1
    hw.tick(.2); checks["watchdog_stops_motion"]=hw.linear == 0 and hw.telemetry()["command_stale"]
    hw.command(.4,0); hw.tick(.1); before=hw.x; hw.set_estop(True); hw.tick(.1); checks["estop_latches_motion"]=hw.x == before
    hw.set_estop(False); hw.inject("motor_stall"); hw.command(.4,0); hw.tick(.1); checks["stall_stops_motion"]=hw.linear == 0
    hw.inject("motor_stall",False); hw.inject("wheel_slip"); hw.command(.4,0); hw.tick(.1); checks["slip_reduces_motion"]=0 < hw.linear < .4
    hw.inject("wheel_slip",False); hw.inject("encoder_dropout"); checks["encoder_dropout_visible"]=hw.telemetry()["pose"] is None
    hw.inject("encoder_dropout",False); hw.inject("lidar_dropout"); checks["lidar_dropout_visible"]=not hw.telemetry()["lidar_ok"]
    checks["battery_bounded"]=0 <= hw.battery_percent <= 100
    report={"schema_version":"openpatrol.virtual-hardware/v1","result":"pass" if all(checks.values()) else "fail","checks":checks,
            "metrics":{"distance_m":round(hw.distance_m,4),"battery_percent":round(hw.battery_percent,6)},"final_telemetry":hw.telemetry()}
    if output: output.parent.mkdir(parents=True,exist_ok=True); output.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    return report

