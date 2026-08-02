"""CRC-protected serial protocol for the Sentinel telescoping mast."""
from __future__ import annotations

from dataclasses import dataclass

from .protocol import ProtocolError, _frame, _payload

MIN_HEIGHT_MM = 980
MAX_HEIGHT_MM = 1500


def encode_mast_command(seq: int, target_mm: int, enabled: bool = True) -> bytes:
    if not 0 <= seq <= 0xFFFFFFFF:
        raise ProtocolError("sequence must fit uint32")
    if not MIN_HEIGHT_MM <= target_mm <= MAX_HEIGHT_MM:
        raise ProtocolError(f"mast target must be between {MIN_HEIGHT_MM} and {MAX_HEIGHT_MM} mm")
    return _frame(f"M,{seq},{target_mm},{1 if enabled else 0}")


@dataclass(frozen=True)
class MastStatus:
    seq: int
    height_mm: int
    flags: int

    @property
    def lower_limit(self) -> bool:
        return bool(self.flags & 0x01)

    @property
    def upper_limit(self) -> bool:
        return bool(self.flags & 0x02)

    @property
    def command_timed_out(self) -> bool:
        return bool(self.flags & 0x04)

    @property
    def tilt_interlock(self) -> bool:
        return bool(self.flags & 0x08)

    @property
    def actuator_fault(self) -> bool:
        return bool(self.flags & 0x10)

    @property
    def drive_moving(self) -> bool:
        return bool(self.flags & 0x20)

    @property
    def extended(self) -> bool:
        return bool(self.flags & 0x40)


def parse_mast_status(line: bytes | str) -> MastStatus:
    fields = _payload(line).split(",")
    if len(fields) != 4 or fields[0] != "T":
        raise ProtocolError("expected T mast-status frame with three fields")
    try:
        seq, height_mm, flags = (int(value) for value in fields[1:])
    except ValueError as exc:
        raise ProtocolError("mast status fields must be integers") from exc
    if not 0 <= seq <= 0xFFFFFFFF:
        raise ProtocolError("mast status sequence is outside uint32")
    if not MIN_HEIGHT_MM - 30 <= height_mm <= MAX_HEIGHT_MM + 30:
        raise ProtocolError("mast height is outside the physical envelope")
    if not 0 <= flags <= 0xFFFF:
        raise ProtocolError("mast flags are outside uint16")
    return MastStatus(seq, height_mm, flags)
