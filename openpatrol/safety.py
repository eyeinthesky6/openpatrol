from __future__ import annotations
import math
from dataclasses import dataclass

@dataclass(frozen=True)
class StopEnvelope:
    speed_mps: float
    deceleration_mps2: float
    command_latency_ms: int
    margin_m: float = .10
    def distance_m(self) -> float:
        if not all(math.isfinite(value) for value in (self.speed_mps,self.deceleration_mps2,self.command_latency_ms,self.margin_m)): raise ValueError("stop-envelope inputs must be finite")
        if self.speed_mps < 0 or self.deceleration_mps2 <= 0 or self.command_latency_ms < 0 or self.margin_m < 0: raise ValueError("invalid stop-envelope inputs")
        reaction=self.speed_mps*self.command_latency_ms/1000
        braking=self.speed_mps**2/(2*self.deceleration_mps2)
        return reaction+braking+self.margin_m
    def required_clearance_m(self, localization_error_m: float, obstacle_error_m: float) -> float:
        if not all(math.isfinite(value) for value in (localization_error_m,obstacle_error_m)): raise ValueError("errors must be finite")
        if localization_error_m < 0 or obstacle_error_m < 0: raise ValueError("errors cannot be negative")
        return self.distance_m()+localization_error_m+obstacle_error_m
