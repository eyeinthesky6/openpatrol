"""Open, local-first security command-centre primitives.

The command centre ingests observations from cameras, robots, NVR/VMS systems,
access control, alarm panels and fixed sensors. It fuses evidence into incident
*candidates* and routes audited commands to compatible devices. It never treats
an AI score as a legal or medical conclusion.
"""
from __future__ import annotations

import hashlib
import json
import math
import threading
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable

SEVERITIES = {"low", "medium", "high", "critical"}
DEVICE_KINDS = {"camera", "robot", "drone", "sensor_hub", "speaker", "alarm", "nvr", "access_control"}
DEVICE_ACTIONS = {"notify", "speak", "play_audio", "strobe", "siren", "stop_output"}
CAPABILITIES = {"video", "audio_in", "speaker", "strobe", "siren", "sensors", "mobility", "talkback"}
EVENT_ALIASES = {
    "person_fallen": "fall", "fall_detected": "fall", "lying_person": "fall",
    "door_forced": "forced_entry", "forced_door": "forced_entry", "glass_break": "glass_break",
    "pool_distress": "drowning_distress", "submerged_person": "drowning_distress",
    "violent_motion": "aggressive_motion", "altercation": "fight",
    "fast_motion": "sudden_motion", "scene_change": "sudden_motion",
    "smoke_alarm": "smoke", "fire_alarm": "fire", "panic_button": "panic",
}


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def iso_now() -> str:
    return utc_now().isoformat()


def _atomic_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(f".{uuid.uuid4().hex}.tmp")
    temp.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temp.replace(path)


def _read_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, json.JSONDecodeError):
        return default


def _clean_text(value: Any, field: str, limit: int = 160, *, required: bool = True) -> str:
    text = str(value or "").strip()
    if required and not text:
        raise ValueError(f"{field} is required")
    if len(text) > limit or any(ord(char) < 32 for char in text):
        raise ValueError(f"{field} must contain at most {limit} printable characters")
    return text


def _confidence(value: Any) -> float:
    if isinstance(value, bool):
        raise ValueError("confidence must be numeric")
    number = float(value)
    if not math.isfinite(number) or not 0 <= number <= 1:
        raise ValueError("confidence must be between 0 and 1")
    return number


def _parse_time(value: Any) -> datetime:
    if not value:
        return utc_now()
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return parsed.astimezone(timezone.utc) if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except ValueError as exc:
        raise ValueError("observed_at must be ISO-8601") from exc


class DeviceRegistry:
    """Persistent device inventory and bounded command queue."""

    def __init__(self, directory: Path):
        self.directory = directory
        self.path = directory / "devices.json"
        self.commands_path = directory / "device-commands.json"
        self._lock = threading.RLock()
        self.directory.mkdir(parents=True, exist_ok=True)

    def list(self) -> list[dict[str, Any]]:
        with self._lock:
            devices = _read_json(self.path, {})
            return sorted(devices.values(), key=lambda item: (item.get("zone", ""), item["name"]))

    def get(self, device_id: str) -> dict[str, Any]:
        with self._lock:
            device = _read_json(self.path, {}).get(device_id)
            if not device:
                raise FileNotFoundError(device_id)
            return device

    def register(self, payload: dict[str, Any]) -> dict[str, Any]:
        device_id = _clean_text(payload.get("id"), "id", 120)
        name = _clean_text(payload.get("name") or device_id, "name", 160)
        kind = _clean_text(payload.get("kind"), "kind", 40)
        if kind not in DEVICE_KINDS:
            raise ValueError(f"kind must be one of: {', '.join(sorted(DEVICE_KINDS))}")
        zone = _clean_text(payload.get("zone") or "unassigned", "zone", 120)
        capabilities = sorted({_clean_text(item, "capability", 40) for item in payload.get("capabilities", [])})
        unknown = set(capabilities) - CAPABILITIES
        if unknown:
            raise ValueError(f"unknown capabilities: {', '.join(sorted(unknown))}")
        streams = payload.get("streams") or {}
        if not isinstance(streams, dict):
            raise ValueError("streams must be an object")
        safe_streams = {}
        for key in ("operator_url", "snapshot_url", "live_url"):
            if streams.get(key):
                safe_streams[key] = _clean_text(streams[key], key, 1000)
        now = iso_now()
        with self._lock:
            devices = _read_json(self.path, {})
            previous = devices.get(device_id, {})
            device = {
                "id": device_id, "name": name, "kind": kind, "zone": zone,
                "capabilities": capabilities, "streams": safe_streams,
                "status": str(payload.get("status") or previous.get("status") or "online")[:40],
                "provider": str(payload.get("provider") or previous.get("provider") or "openpatrol")[:120],
                "metadata": payload.get("metadata") if isinstance(payload.get("metadata"), dict) else previous.get("metadata", {}),
                "registered_at": previous.get("registered_at", now), "last_seen_at": now,
                "telemetry": previous.get("telemetry", {}),
            }
            devices[device_id] = device
            _atomic_json(self.path, devices)
            return device

    def heartbeat(self, device_id: str, telemetry: dict[str, Any] | None = None) -> dict[str, Any]:
        with self._lock:
            devices = _read_json(self.path, {})
            if device_id not in devices:
                raise FileNotFoundError(device_id)
            devices[device_id]["last_seen_at"] = iso_now()
            devices[device_id]["status"] = "online"
            if isinstance(telemetry, dict):
                devices[device_id]["telemetry"] = telemetry
            _atomic_json(self.path, devices)
            return devices[device_id]

    def queue(self, device_ids: Iterable[str], action: str, payload: dict[str, Any] | None = None, *, incident_id: str | None = None, origin: str = "operator") -> list[dict[str, Any]]:
        if action not in DEVICE_ACTIONS:
            raise ValueError(f"unsupported device action {action!r}")
        payload = payload or {}
        now = iso_now()
        with self._lock:
            devices = _read_json(self.path, {})
            commands = _read_json(self.commands_path, [])
            created = []
            for device_id in dict.fromkeys(str(item) for item in device_ids):
                if device_id not in devices:
                    raise FileNotFoundError(device_id)
                command = {
                    "id": f"cmd-{uuid.uuid4().hex}", "device_id": device_id,
                    "action": action, "payload": payload, "incident_id": incident_id,
                    "origin": origin[:80], "created_at": now, "status": "pending",
                    "acknowledged_at": None, "result": None,
                }
                commands.append(command)
                created.append(dict(command))
            _atomic_json(self.commands_path, commands[-10000:])
            return created

    def poll(self, device_id: str, limit: int = 20) -> list[dict[str, Any]]:
        self.get(device_id)
        with self._lock:
            commands = _read_json(self.commands_path, [])
            return [dict(item) for item in commands if item["device_id"] == device_id and item["status"] == "pending"][:max(1, min(limit, 100))]

    def acknowledge(self, device_id: str, command_id: str, result: dict[str, Any] | None = None) -> dict[str, Any]:
        with self._lock:
            commands = _read_json(self.commands_path, [])
            for command in commands:
                if command["id"] == command_id and command["device_id"] == device_id:
                    command["status"] = "acknowledged"
                    command["acknowledged_at"] = iso_now()
                    command["result"] = result or {"ok": True}
                    response = dict(command)
                    _atomic_json(self.commands_path, commands)
                    return response
            raise FileNotFoundError(command_id)

    def cameras(self) -> list[dict[str, Any]]:
        return [item for item in self.list() if item["kind"] == "camera" or "video" in item["capabilities"]]


class IncidentFusion:
    """Conservative multi-sensor incident candidate fusion."""

    WINDOW_SECONDS = 45

    def normalize_type(self, event_type: Any) -> str:
        value = _clean_text(event_type, "event_type", 80).lower().replace("-", "_").replace(" ", "_")
        return EVENT_ALIASES.get(value, value)

    @staticmethod
    def combined_confidence(items: list[dict[str, Any]], weights: dict[str, float] | None = None) -> float:
        residual = 1.0
        weights = weights or {}
        for item in items:
            weight = max(0.1, min(float(weights.get(item["event_type"], 1.0)), 1.0))
            residual *= 1 - min(item["confidence"] * weight, 0.99)
        score = 1 - residual
        independent = len({item.get("device_id") or item["source"] for item in items})
        if independent >= 2:
            score = min(0.99, score + min(0.12, (independent - 1) * 0.05))
        return round(score, 3)

    def fuse(self, observation: dict[str, Any], recent: list[dict[str, Any]]) -> dict[str, Any] | None:
        zone = observation["zone"]
        cutoff = observation["observed_dt"] - timedelta(seconds=self.WINDOW_SECONDS)
        context = [item for item in recent if item["zone"] == zone and item["observed_dt"] >= cutoff]
        if observation not in context:
            context.append(observation)
        by_type: dict[str, list[dict[str, Any]]] = {}
        for item in context:
            by_type.setdefault(item["event_type"], []).append(item)

        direct = observation["event_type"]
        selected: list[dict[str, Any]] = []
        incident_type = direct
        severity = observation["severity"]
        threshold = 0.72
        title = observation.get("title") or direct.replace("_", " ").title()

        if direct in {"panic", "tamper", "fire", "smoke", "drowning_distress", "fight", "fall", "forced_entry"}:
            selected = [observation]
            threshold = {"panic": .5, "tamper": .55, "fire": .55, "smoke": .6, "forced_entry": .6}.get(direct, .72)
        elif direct == "door_open" and (by_type.get("person") or by_type.get("motion")):
            incident_type, severity, title = "intrusion", "high", f"Possible intrusion in {zone}"
            selected = [observation] + (by_type.get("person") or by_type["motion"])[-1:]
            threshold = .68
        elif direct in {"person", "motion"} and by_type.get("door_open"):
            incident_type, severity, title = "intrusion", "high", f"Possible intrusion in {zone}"
            selected = [observation, by_type["door_open"][-1]]
            threshold = .68
        elif direct in {"person", "motion"} and (by_type.get("forced_entry") or by_type.get("glass_break")):
            incident_type, severity, title = "break_in", "critical", f"Possible break-in in {zone}"
            selected = [observation] + (by_type.get("forced_entry") or by_type["glass_break"])[-1:]
            threshold = .7
        elif direct == "immobility" and by_type.get("fall"):
            incident_type, severity, title = "fall", "high", f"Possible fall with immobility in {zone}"
            selected = [observation, by_type["fall"][-1]]
            threshold = .62
        elif direct in {"aggressive_motion", "multiple_persons", "shout"} and len({kind for kind in ("aggressive_motion", "multiple_persons", "shout") if by_type.get(kind)}) >= 2:
            incident_type, severity, title = "fight", "high", f"Possible fight or violent movement in {zone}"
            selected = [by_type[kind][-1] for kind in ("aggressive_motion", "multiple_persons", "shout") if by_type.get(kind)]
            threshold = .72
        elif direct in {"pool_distress", "drowning_distress", "submerged", "pool_immobility"} and len({kind for kind in ("drowning_distress", "submerged", "pool_immobility") if by_type.get(kind)}) >= 1:
            incident_type, severity, title = "drowning_distress", "critical", f"Possible water distress in {zone}"
            selected = [observation]
            threshold = .7
        elif direct == "sudden_motion":
            incident_type, severity, title = "sudden_motion", "medium", f"Sudden movement in {zone}"
            selected, threshold = [observation], .78
        elif direct == "restricted_zone_entry":
            incident_type, severity, title = direct, "high", f"Restricted-zone entry in {zone}"
            selected, threshold = [observation], .7
        else:
            return None

        score = self.combined_confidence(selected)
        if score < threshold:
            return None
        source_ids = sorted(item["id"] for item in selected)
        fingerprint = hashlib.sha256((incident_type + "|" + zone + "|" + "|".join(source_ids)).encode()).hexdigest()[:20]
        return {
            "id": f"fused-{fingerprint}", "event_type": incident_type, "title": title,
            "severity": severity if severity in SEVERITIES else "medium", "confidence": score,
            "source": f"command-centre/{zone}", "provider": "openpatrol-fusion-v1",
            "rule": f"fusion_{incident_type}", "zone": zone,
            "observations": [{key: item[key] for key in ("id", "event_type", "confidence", "source", "device_id", "observed_at")} for item in selected],
            "threshold": threshold,
        }


class CommandCentre:
    """Observation ingestion, incident creation and alert routing."""

    def __init__(self, directory: Path, devices: DeviceRegistry | None = None, *, confidence_floor: float = 0.7):
        self.directory = directory
        self.directory.mkdir(parents=True, exist_ok=True)
        self.devices = devices or DeviceRegistry(directory)
        self.observations_path = directory / "observations.jsonl"
        self.alerts_path = directory / "alerts.json"
        self._lock = threading.RLock()
        self.fusion = IncidentFusion()
        self.confidence_floor = max(.5, min(.99, float(confidence_floor)))
        self._seen = {(item.get("source"), item.get("id")) for item in self.observations()}

    def observations(self, limit: int = 500) -> list[dict[str, Any]]:
        if not self.observations_path.exists():
            return []
        rows = []
        for line in self.observations_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                item = json.loads(line)
                item["observed_dt"] = _parse_time(item["observed_at"])
                rows.append(item)
            except (json.JSONDecodeError, ValueError, KeyError):
                continue
        return rows[-max(1, min(limit, 5000)):]

    def alerts(self) -> list[dict[str, Any]]:
        with self._lock:
            return list(reversed(_read_json(self.alerts_path, [])))

    def ingest(self, payload: dict[str, Any], simulator: Any) -> dict[str, Any]:
        observation = self._validate_observation(payload)
        key = (observation["source"], observation["id"])
        with self._lock:
            if key in self._seen:
                return {"status": "duplicate", "observation": {key: value for key, value in observation.items() if key != "observed_dt"}, "incident": None, "alert": None}
            serializable = {key: value for key, value in observation.items() if key != "observed_dt"}
            with self.observations_path.open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(serializable, ensure_ascii=False, separators=(",", ":")) + "\n")
            self._seen.add(key)
            recent = self.observations(300)
            candidate = self.fusion.fuse(observation, recent)
            if not candidate or candidate["confidence"] < self.confidence_floor:
                return {"status": "observed", "observation": serializable, "incident": None, "alert": None}
            media = observation.get("media_reference")
            event = {key: candidate[key] for key in ("id", "event_type", "title", "severity", "confidence", "source", "provider", "rule")}
            if media:
                event["media_reference"] = media
            receipt = simulator.ingest_detection(event)
            alert = self._dispatch(candidate, receipt["event_id"])
            return {"status": "incident", "observation": serializable, "incident": receipt, "alert": alert, "fusion": candidate}

    def _validate_observation(self, payload: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(payload, dict):
            raise ValueError("security event must be an object")
        event_type = self.fusion.normalize_type(payload.get("event_type") or payload.get("type"))
        observed_dt = _parse_time(payload.get("observed_at"))
        attributes = payload.get("attributes") or {}
        if not isinstance(attributes, dict):
            raise ValueError("attributes must be an object")
        severity = str(payload.get("severity") or "medium")
        if severity not in SEVERITIES:
            raise ValueError("invalid severity")
        return {
            "id": _clean_text(payload.get("id") or f"obs-{uuid.uuid4().hex}", "id", 120),
            "event_type": event_type,
            "title": _clean_text(payload.get("title") or event_type.replace("_", " ").title(), "title", 200),
            "severity": severity,
            "confidence": _confidence(payload.get("confidence", 1.0)),
            "source": _clean_text(payload.get("source") or "external-security", "source", 200),
            "provider": _clean_text(payload.get("provider") or "generic", "provider", 120),
            "device_id": _clean_text(payload.get("device_id") or "external", "device_id", 120),
            "zone": _clean_text(payload.get("zone") or "unassigned", "zone", 120),
            "observed_at": observed_dt.isoformat(), "observed_dt": observed_dt,
            "attributes": attributes,
            "media_reference": _clean_text(payload.get("media_reference"), "media_reference", 1000, required=False) or None,
        }

    def _dispatch(self, candidate: dict[str, Any], incident_id: str) -> dict[str, Any]:
        message = self._automatic_message(candidate)
        devices = self.devices.list()
        zone_devices = []
        for item in devices:
            metadata = item.get("metadata") or {}
            subscriptions = metadata.get("subscribed_zones") if isinstance(metadata.get("subscribed_zones"), list) else []
            if item["zone"] == candidate["zone"] or metadata.get("global_alerts") is True or candidate["zone"] in subscriptions:
                zone_devices.append(item)
        target_ids = [item["id"] for item in zone_devices]
        commands: list[dict[str, Any]] = []
        for device in zone_devices:
            caps = set(device["capabilities"])
            if "strobe" in caps and candidate["severity"] in {"high", "critical"}:
                commands += self.devices.queue([device["id"]], "strobe", {"pattern": "critical" if candidate["severity"] == "critical" else "warning", "seconds": 20}, incident_id=incident_id, origin="incident-policy")
            if "siren" in caps and candidate["severity"] == "critical":
                commands += self.devices.queue([device["id"]], "siren", {"pattern": "pulse", "seconds": 10}, incident_id=incident_id, origin="incident-policy")
            if message and ("speaker" in caps or "talkback" in caps):
                commands += self.devices.queue([device["id"]], "speak", {"text": message, "priority": candidate["severity"]}, incident_id=incident_id, origin="incident-policy")
        alert = {
            "id": f"alert-{uuid.uuid4().hex}", "incident_id": incident_id,
            "type": candidate["event_type"], "title": candidate["title"],
            "severity": candidate["severity"], "confidence": candidate["confidence"],
            "zone": candidate["zone"], "created_at": iso_now(), "status": "active",
            "browser_audio": candidate["severity"] in {"high", "critical"},
            "target_devices": target_ids, "commands": [item["id"] for item in commands],
            "automatic_message": message,
        }
        alerts = list(reversed(self.alerts()))
        alerts.append(alert)
        _atomic_json(self.alerts_path, alerts[-5000:])
        return alert

    @staticmethod
    def _automatic_message(candidate: dict[str, Any]) -> str | None:
        kind, confidence = candidate["event_type"], candidate["confidence"]
        if kind in {"intrusion", "break_in", "restricted_zone_entry", "forced_entry"} and confidence >= .78:
            return "Warning. This area is monitored. Please leave the restricted area and await security staff."
        if kind == "drowning_distress" and confidence >= .78:
            return "Emergency at the pool area. Lifeguard or trained assistance is required immediately."
        if kind in {"fire", "smoke"} and confidence >= .75:
            return "Possible fire or smoke emergency. Follow the site evacuation plan and emergency instructions."
        if kind == "panic":
            return "Security assistance has been requested."
        # Falls and fights deliberately stay operator-first to avoid harmful or accusatory speech.
        return None

    def summary(self, simulator_state: dict[str, Any]) -> dict[str, Any]:
        observations = self.observations(200)
        alerts = self.alerts()
        devices = self.devices.list()
        return {
            "contract_version": "openpatrol.command-centre/v1",
            "generated_at": iso_now(), "patrol": simulator_state,
            "devices": devices, "cameras": self.devices.cameras(),
            "observations": [{key: value for key, value in item.items() if key != "observed_dt"} for item in reversed(observations[-50:])],
            "alerts": alerts[:100],
            "counts": {
                "devices": len(devices), "cameras": len(self.devices.cameras()),
                "online": sum(item.get("status") == "online" for item in devices),
                "active_alerts": sum(item.get("status") == "active" for item in alerts),
                "pending_incidents": sum(item.get("review", {}).get("status") == "pending" for item in simulator_state.get("incidents", [])),
            },
        }
