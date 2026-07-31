from __future__ import annotations

import hashlib
import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .evidence import canonical_bytes


class AuditLog:
    """Append-only hash-chained operational audit log."""

    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()

    def append(self, action: str, *, actor: str = "local-operator", details: dict[str, Any] | None = None) -> dict[str, Any]:
        with self._lock:
            entries = self.list()
            previous = entries[-1]["digest"] if entries else "GENESIS"
            entry = {"sequence": len(entries) + 1, "at": datetime.now(timezone.utc).isoformat(), "actor": actor[:80], "action": action[:80], "details": details or {}, "previous": previous}
            entry["digest"] = hashlib.sha256(canonical_bytes(entry)).hexdigest()
            with self.path.open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(entry, ensure_ascii=False, separators=(",", ":")) + "\n")
                stream.flush()
            return entry

    def list(self) -> list[dict[str, Any]]:
        if not self.path.exists(): return []
        return [json.loads(line) for line in self.path.read_text(encoding="utf-8").splitlines() if line.strip()]

    def verify(self) -> dict[str, Any]:
        previous = "GENESIS"
        entries = self.list()
        for index, entry in enumerate(entries, 1):
            claimed = entry.get("digest")
            unsigned = {key: value for key, value in entry.items() if key != "digest"}
            expected = hashlib.sha256(canonical_bytes(unsigned)).hexdigest()
            if entry.get("sequence") != index or entry.get("previous") != previous or claimed != expected:
                return {"valid": False, "entries": len(entries), "failed_sequence": index}
            previous = claimed
        return {"valid": True, "entries": len(entries), "failed_sequence": None}
