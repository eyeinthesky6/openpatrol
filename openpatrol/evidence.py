from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def canonical_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


class EvidenceStore:
    def __init__(self, directory: Path):
        self.directory = directory
        self.directory.mkdir(parents=True, exist_ok=True)

    def create(self, *, robot_id: str, site_id: str, lap: int, waypoint: dict[str, Any], event: dict[str, Any]) -> dict[str, Any]:
        now = datetime.now(timezone.utc)
        event_id = f"evt-{now.strftime('%Y%m%dT%H%M%S')}-{event['id']}-l{lap}"
        core = {
            "schema_version": "openpatrol.evidence/v1",
            "event_id": event_id,
            "robot_id": robot_id,
            "site_id": site_id,
            "captured_at": now.isoformat(),
            "lap": lap,
            "pose": {"x": waypoint["x"], "y": waypoint["y"], "waypoint_id": waypoint["id"]},
            "detection": {
                "type": event["event_type"],
                "title": event["title"],
                "severity": event["severity"],
                "confidence": event["confidence"],
                "source": "synthetic-scenario",
            },
            "media": {"kind": "simulation_snapshot", "reference": f"snapshot://{event_id}"},
            "software": {"openpatrol": "0.1.0", "detector": "synthetic-v1"},
            "review": {"status": "pending", "disposition": None, "note": None, "reviewed_at": None},
        }
        digest = hashlib.sha256(canonical_bytes(core)).hexdigest()
        receipt = {**core, "integrity": {"algorithm": "sha256", "digest": digest}}
        self._write(receipt)
        return receipt

    def update_review(self, event_id: str, disposition: str, note: str = "") -> dict[str, Any]:
        path = self.directory / f"{event_id}.json"
        receipt = json.loads(path.read_text(encoding="utf-8"))
        receipt["review"] = {
            "status": "reviewed",
            "disposition": disposition,
            "note": note.strip()[:500],
            "reviewed_at": datetime.now(timezone.utc).isoformat(),
        }
        self._write(receipt)
        return receipt

    def list(self) -> list[dict[str, Any]]:
        receipts = [json.loads(path.read_text(encoding="utf-8")) for path in self.directory.glob("evt-*.json")]
        return sorted(receipts, key=lambda item: item["captured_at"], reverse=True)

    def _write(self, receipt: dict[str, Any]) -> None:
        path = self.directory / f"{receipt['event_id']}.json"
        temp = path.with_suffix(".tmp")
        temp.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        temp.replace(path)
