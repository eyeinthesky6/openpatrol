"""OpenPatrol safety-controller serial protocol and differential-drive math.

Wire format is ASCII for field debugging, but every frame carries CRC16-CCITT.
Commands: $C,seq,left_mm_s,right_mm_s,enable*CCCC\n
Status:   $S,seq,left_ticks,right_ticks,battery_mv,flags*CCCC\n
Flags: bit0 E-stop open, bit1 bumper/stop-loop open, bit2 command timeout,
bit3 motor-driver fault, bit4 charger connected, bit5 mast extended.
"""
from __future__ import annotations

import math
from dataclasses import dataclass


class ProtocolError(ValueError):
    pass


def crc16_ccitt(data: bytes, seed: int = 0xFFFF) -> int:
    crc = seed
    for byte in data:
        crc ^= byte << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) & 0xFFFF if crc & 0x8000 else (crc << 1) & 0xFFFF
    return crc


def _frame(payload: str) -> bytes:
    encoded = payload.encode("ascii")
    return b"$" + encoded + f"*{crc16_ccitt(encoded):04X}\n".encode("ascii")


def _payload(line: bytes | str) -> str:
    raw = line.encode("ascii") if isinstance(line, str) else line
    raw = raw.strip()
    if not raw.startswith(b"$") or b"*" not in raw:
        raise ProtocolError("frame must start with '$' and contain '*' CRC separator")
    payload, claimed = raw[1:].rsplit(b"*", 1)
    if len(claimed) != 4:
        raise ProtocolError("CRC must contain four hexadecimal characters")
    try:
        expected = int(claimed, 16)
    except ValueError as exc:
        raise ProtocolError("CRC is not hexadecimal") from exc
    actual = crc16_ccitt(payload)
    if actual != expected:
        raise ProtocolError(f"CRC mismatch: expected {expected:04X}, calculated {actual:04X}")
    try:
        return payload.decode("ascii")
    except UnicodeDecodeError as exc:
        raise ProtocolError("frame must be ASCII") from exc


def encode_command(seq: int, left_mps: float, right_mps: float, enabled: bool = True) -> bytes:
    if not 0 <= seq <= 0xFFFFFFFF:
        raise ProtocolError("sequence must fit uint32")
    if not all(math.isfinite(value) for value in (left_mps, right_mps)):
        raise ProtocolError("wheel velocities must be finite")
    left_mm_s = round(left_mps * 1000)
    right_mm_s = round(right_mps * 1000)
    if not -2000 <= left_mm_s <= 2000 or not -2000 <= right_mm_s <= 2000:
        raise ProtocolError("wheel command exceeds protocol range")
    return _frame(f"C,{seq},{left_mm_s},{right_mm_s},{1 if enabled else 0}")


@dataclass(frozen=True)
class ControllerStatus:
    seq: int
    left_ticks: int
    right_ticks: int
    battery_mv: int
    flags: int

    @property
    def estop_open(self) -> bool:
        return bool(self.flags & 0x01)

    @property
    def stop_loop_open(self) -> bool:
        return bool(self.flags & 0x02)

    @property
    def command_timed_out(self) -> bool:
        return bool(self.flags & 0x04)

    @property
    def driver_fault(self) -> bool:
        return bool(self.flags & 0x08)

    @property
    def charger_connected(self) -> bool:
        return bool(self.flags & 0x10)

    @property
    def mast_extended(self) -> bool:
        return bool(self.flags & 0x20)


def parse_status(line: bytes | str) -> ControllerStatus:
    fields = _payload(line).split(",")
    if len(fields) != 6 or fields[0] != "S":
        raise ProtocolError("expected S status frame with five fields")
    try:
        seq, left_ticks, right_ticks, battery_mv, flags = (int(value) for value in fields[1:])
    except ValueError as exc:
        raise ProtocolError("status fields must be integers") from exc
    if not 0 <= seq <= 0xFFFFFFFF:
        raise ProtocolError("status sequence is outside uint32")
    if not 0 <= battery_mv <= 100000:
        raise ProtocolError("battery voltage is outside protocol range")
    if not 0 <= flags <= 0xFFFF:
        raise ProtocolError("flags are outside uint16")
    return ControllerStatus(seq, left_ticks, right_ticks, battery_mv, flags)


def twist_to_wheels(linear_mps: float, angular_rps: float, wheel_track_m: float, max_wheel_mps: float) -> tuple[float, float]:
    if not all(math.isfinite(value) for value in (linear_mps, angular_rps, wheel_track_m, max_wheel_mps)):
        raise ValueError("kinematic inputs must be finite")
    if wheel_track_m <= 0 or max_wheel_mps <= 0:
        raise ValueError("wheel track and maximum wheel speed must be positive")
    left = linear_mps - angular_rps * wheel_track_m / 2
    right = linear_mps + angular_rps * wheel_track_m / 2
    peak = max(abs(left), abs(right), max_wheel_mps)
    scale = max_wheel_mps / peak
    return left * scale, right * scale


def tick_delta(current: int, previous: int) -> int:
    """Return signed delta for a wrapping 32-bit encoder counter."""
    value = (current - previous) & 0xFFFFFFFF
    return value - 0x100000000 if value & 0x80000000 else value


def differential_increment(
    left_delta_ticks: int,
    right_delta_ticks: int,
    wheel_radius_m: float,
    wheel_track_m: float,
    counts_per_revolution: int,
) -> tuple[float, float]:
    if wheel_radius_m <= 0 or wheel_track_m <= 0 or counts_per_revolution <= 0:
        raise ValueError("drive dimensions and encoder counts must be positive")
    meters_per_tick = 2 * math.pi * wheel_radius_m / counts_per_revolution
    left_m = left_delta_ticks * meters_per_tick
    right_m = right_delta_ticks * meters_per_tick
    return (left_m + right_m) / 2, (right_m - left_m) / wheel_track_m
