from __future__ import annotations

import hashlib
import json
import threading
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


def canonical_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _digest(payload: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_bytes(payload)).hexdigest()


class EvidenceStore:
    """Atomic, tamper-evident JSON receipts with an append-only review trail."""

    def __init__(self, directory: Path, *, retention_days: int = 30, max_records: int = 5000):
        self.directory = directory
        self.directory.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self.retention_days = max(1, retention_days)
        self.max_records = max(10, max_records)

    def create(self, *, robot_id: str, site_id: str, lap: int, waypoint: dict[str, Any], event: dict[str, Any], source: str = "synthetic-scenario", media: dict[str, Any] | None = None) -> dict[str, Any]:
        now = datetime.now(timezone.utc)
        event_id = f"evt-{now.strftime('%Y%m%dT%H%M%S')}-{event['id']}-{uuid.uuid4().hex[:8]}"
        capture = {
            "schema_version": "openpatrol.evidence/v2",
            "event_id": event_id,
            "robot_id": robot_id,
            "site_id": site_id,
            "captured_at": now.isoformat(),
            "lap": lap,
            "pose": {"x": waypoint["x"], "y": waypoint["y"], "waypoint_id": waypoint["id"]},
            "detection": {
                "type": event["event_type"], "title": event["title"],
                "severity": event["severity"], "confidence": event["confidence"], "source": source,
            },
            "media": media or {"kind": "simulation_snapshot" if source == "synthetic-scenario" else "external_reference", "reference": f"snapshot://{event_id}" if source == "synthetic-scenario" else None, "sha256": None},
            "software": {"openpatrol": "0.2.0", "detector": "synthetic-v1"},
        }
        receipt = {
            **capture,
            "integrity": {"algorithm": "sha256", "scope": "capture", "digest": _digest(capture)},
            "review": {"status": "pending", "disposition": None, "note": None, "reviewed_at": None},
            "audit": [],
        }
        with self._lock:
            self._write(receipt)
            self.prune()
        return receipt

    def update_review(self, event_id: str, disposition: str, note: str = "", actor: str = "local-operator") -> dict[str, Any]:
        if disposition not in {"confirmed", "dismissed", "escalated"}:
            raise ValueError("invalid disposition")
        with self._lock:
            receipt = self.get(event_id)
            timestamp = datetime.now(timezone.utc).isoformat()
            clean_note = str(note).strip()[:500]
            receipt["review"] = {"status": "reviewed", "disposition": disposition, "note": clean_note, "reviewed_at": timestamp}
            previous = receipt["audit"][-1]["digest"] if receipt["audit"] else receipt["integrity"]["digest"]
            action = {"sequence": len(receipt["audit"]) + 1, "action": "review", "disposition": disposition, "note": clean_note, "actor": actor[:80], "at": timestamp, "previous": previous}
            action["digest"] = _digest(action)
            receipt["audit"].append(action)
            self._write(receipt)
            return receipt

    def get(self, event_id: str) -> dict[str, Any]:
        if not event_id.startswith("evt-") or "/" in event_id or "\\" in event_id:
            raise FileNotFoundError(event_id)
        return json.loads((self.directory / f"{event_id}.json").read_text(encoding="utf-8"))

    def verify(self, receipt_or_id: dict[str, Any] | str) -> dict[str, Any]:
        receipt = self.get(receipt_or_id) if isinstance(receipt_or_id, str) else receipt_or_id
        capture = {key: value for key, value in receipt.items() if key not in {"integrity", "review", "audit"}}
        capture_valid = receipt.get("integrity", {}).get("digest") == _digest(capture)
        previous = receipt.get("integrity", {}).get("digest", "")
        audit_valid = True
        for index, action in enumerate(receipt.get("audit", []), 1):
            claimed = action.get("digest")
            unsigned = {key: value for key, value in action.items() if key != "digest"}
            if action.get("sequence") != index or action.get("previous") != previous or claimed != _digest(unsigned):
                audit_valid = False
                break
            previous = claimed
        return {"valid": capture_valid and audit_valid, "capture_valid": capture_valid, "audit_valid": audit_valid, "event_id": receipt.get("event_id")}

    def list(self) -> list[dict[str, Any]]:
        with self._lock:
            receipts = [json.loads(path.read_text(encoding="utf-8")) for path in self.directory.glob("evt-*.json")]
        return sorted(receipts, key=lambda item: item["captured_at"], reverse=True)

    def prune(self) -> int:
        """Apply bounded local retention. Reviewed and pending receipts follow the same declared policy."""
        with self._lock:
            paths = sorted(self.directory.glob("evt-*.json"), key=lambda path: path.stat().st_mtime, reverse=True)
            cutoff = datetime.now(timezone.utc) - timedelta(days=self.retention_days)
            removed = 0
            for index, path in enumerate(paths):
                try: captured = datetime.fromisoformat(json.loads(path.read_text(encoding="utf-8"))["captured_at"])
                except (KeyError, ValueError, json.JSONDecodeError): captured = datetime.min.replace(tzinfo=timezone.utc)
                if index >= self.max_records or captured < cutoff:
                    path.unlink(); removed += 1
            return removed

    def _write(self, receipt: dict[str, Any]) -> None:
        path = self.directory / f"{receipt['event_id']}.json"
        temp = path.with_suffix(f".{uuid.uuid4().hex}.tmp")
        temp.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        temp.replace(path)
