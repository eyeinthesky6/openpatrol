from __future__ import annotations

import json
import math
import os
import shutil
import threading
import time
import uuid
from http import HTTPStatus
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse

from .audit import AuditLog
from .command_centre import CommandCentre, DeviceRegistry
from .evidence import EvidenceStore
from .integrations import registry
from .scenario import load_scenario
from .simulator import PatrolSimulator

ROOT = Path(__file__).resolve().parent.parent
STATIC = ROOT / "static"
MAX_BODY = 768 * 1024


class AppHandler(SimpleHTTPRequestHandler):
    simulator: PatrolSimulator
    ingest_token = ""
    operator_token = ""
    device_token = ""
    settings_path: Path
    settings: dict
    audit: AuditLog
    command_centre: CommandCentre
    devices: DeviceRegistry
    started_at = time.monotonic()
    settings_lock = threading.RLock()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(STATIC), **kwargs)

    def end_headers(self):
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("X-Frame-Options", "SAMEORIGIN")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; style-src 'self'; script-src 'self'; "
            "img-src 'self' data: http: https:; media-src 'self' blob: http: https:; "
            "frame-src 'self' http://127.0.0.1:* http://localhost:*; "
            "connect-src 'self' blob: http: https: ws: wss:",
        )
        self.send_header("Permissions-Policy", "camera=(), microphone=(self), geolocation=()")
        super().end_headers()

    def do_GET(self):
        path = urlparse(self.path).path
        if path in {"/api/state", "/api/v1/state"}:
            return self._json(self.simulator.state())
        if path in {"/api/health", "/api/v1/health"}:
            return self._json({
                "status": "ok", "mode": "simulation", "local_only": True,
                "command_centre": "ready", "uptime_seconds": round(time.monotonic() - self.started_at, 1),
            })
        if path == "/api/v1/incidents":
            return self._json({"incidents": self.simulator.evidence.list()})
        if path == "/api/v1/audit/verify":
            return self._json(self.audit.verify())
        if path == "/api/v1/settings":
            return self._json({
                **self.settings,
                "operator_auth_enabled": bool(self.operator_token),
                "detector_auth_enabled": bool(self.ingest_token),
                "device_auth_enabled": bool(self.device_token),
                "signing_enabled": bool(self.simulator.evidence.signing_key),
            })
        if path == "/api/v1/diagnostics":
            usage = shutil.disk_usage(self.simulator.evidence.directory)
            state = self.simulator.state()
            audit = self.audit.verify()
            receipts = [self.simulator.evidence.verify(item) for item in state["incidents"]]
            devices = self.devices.list()
            return self._json({
                "mode": "simulation", "uptime_seconds": round(time.monotonic() - self.started_at, 1),
                "storage": {"free_bytes": usage.free, "total_bytes": usage.total, "free_percent": round(usage.free / usage.total * 100, 1)},
                "integrity": {"audit_valid": audit["valid"], "receipt_failures": sum(not item["valid"] for item in receipts)},
                "navigation": {"localization": "fault" if state["robot"]["status"] == "fault" else "good", "command_watchdog": "simulated", "target": state["robot"]["target"]},
                "camera": {"configured": len(self.devices.cameras()), "online": sum(item.get("status") == "online" for item in self.devices.cameras())},
                "devices": {"configured": len(devices), "online": sum(item.get("status") == "online" for item in devices)},
            })
        if path == "/api/v1/integrations":
            return self._json(registry("simulation"))
        if path == "/api/v1/command-centre":
            if not self._operator_authorized():
                return self._error(HTTPStatus.UNAUTHORIZED, "unauthorized", "Operator token is required")
            return self._json(self.command_centre.summary(self.simulator.state()))
        if path == "/api/v1/devices":
            if not self._operator_authorized():
                return self._error(HTTPStatus.UNAUTHORIZED, "unauthorized", "Operator token is required")
            return self._json({"devices": self.devices.list()})
        if path == "/api/v1/cameras":
            if not self._operator_authorized():
                return self._error(HTTPStatus.UNAUTHORIZED, "unauthorized", "Operator token is required")
            return self._json({"cameras": self.devices.cameras()})
        if path == "/api/v1/alerts":
            if not self._operator_authorized():
                return self._error(HTTPStatus.UNAUTHORIZED, "unauthorized", "Operator token is required")
            return self._json({"alerts": self.command_centre.alerts()})
        if path == "/api/v1/observations":
            if not self._operator_authorized():
                return self._error(HTTPStatus.UNAUTHORIZED, "unauthorized", "Operator token is required")
            observations = self.command_centre.observations(500)
            return self._json({"observations": [{key: value for key, value in item.items() if key != "observed_dt"} for item in reversed(observations)]})
        if path.startswith("/api/v1/devices/") and path.endswith("/commands"):
            if not self._device_authorized():
                return self._error(HTTPStatus.UNAUTHORIZED, "unauthorized", "Device token is required")
            device_id = path.split("/")[4]
            try:
                return self._json({"commands": self.devices.poll(device_id)})
            except FileNotFoundError:
                return self._error(HTTPStatus.NOT_FOUND, "device_not_found", "Device not found")
        if path.startswith("/api/v1/incidents/") and path.endswith("/verify"):
            event_id = path.split("/")[4]
            try:
                return self._json(self.simulator.evidence.verify(event_id))
            except (FileNotFoundError, json.JSONDecodeError):
                return self._error(HTTPStatus.NOT_FOUND, "incident_not_found", "Incident not found")
        if path == "/metrics":
            state = self.simulator.state()
            summary = self.command_centre.summary(state)
            body = (
                f"openpatrol_battery_percent {state['robot']['battery']}\n"
                f"openpatrol_laps_total {state['robot']['lap']}\n"
                f"openpatrol_incidents_total {len(state['incidents'])}\n"
                f"openpatrol_devices_total {summary['counts']['devices']}\n"
                f"openpatrol_active_alerts {summary['counts']['active_alerts']}\n"
            ).encode()
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/plain; version=0.0.4")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers(); self.wfile.write(body); return
        if path.startswith("/api/"):
            return self._error(HTTPStatus.NOT_FOUND, "not_found", "API route not found")
        return super().do_GET()

    def do_POST(self):
        path = urlparse(self.path).path
        try:
            body = self._body()
            if path in {"/api/patrol", "/api/v1/commands"}:
                if not self._operator_authorized():
                    return self._error(HTTPStatus.UNAUTHORIZED, "unauthorized", "Operator token is required")
                if body.get("action"):
                    action = body["action"]
                elif body.get("status") in {"patrolling", "paused"}:
                    action = "resume" if body["status"] == "patrolling" else "pause"
                else:
                    raise ValueError("action is required")
                self.simulator.command(str(action))
                self.audit.append("robot.command", actor=str(body.get("actor", "local-operator")), details={"command": action, "result": self.simulator.status})
                return self._json(self.simulator.state())

            if (path.startswith("/api/incidents/") or path.startswith("/api/v1/incidents/")) and path.endswith("/review"):
                if not self._operator_authorized():
                    return self._error(HTTPStatus.UNAUTHORIZED, "unauthorized", "Operator token is required")
                event_id = path.split("/")[-2]
                receipt = self.simulator.evidence.update_review(event_id, str(body.get("disposition", "")), str(body.get("note", "")), str(body.get("actor", "local-operator")))
                self.audit.append("incident.review", actor=str(body.get("actor", "local-operator")), details={"event_id": event_id, "disposition": body.get("disposition")})
                return self._json(receipt)

            if path.startswith("/api/v1/incidents/") and path.endswith("/subjects"):
                if not self._operator_authorized():
                    return self._error(HTTPStatus.UNAUTHORIZED, "unauthorized", "Operator token is required")
                event_id = path.split("/")[-2]
                receipt = self.simulator.evidence.update_subject_label(event_id, str(body.get("subject_id", "primary")), str(body.get("label", "")), str(body.get("actor", "local-operator")))
                self.audit.append("incident.subject_label", actor=str(body.get("actor", "local-operator")), details={"event_id": event_id, "subject_id": body.get("subject_id", "primary")})
                return self._json(receipt)

            if path == "/api/v1/detections":
                if not self._ingest_authorized():
                    return self._error(HTTPStatus.UNAUTHORIZED, "unauthorized", "A configured ingest token is required")
                event = self._validate_detection(body)
                receipt = self.simulator.ingest_detection(event)
                self.audit.append("detection.ingest", actor="detector-adapter", details={"event_id": receipt["event_id"], "source": event.get("source", "external")})
                return self._json(receipt, HTTPStatus.CREATED)

            if path == "/api/v1/security-events":
                if not self._ingest_authorized():
                    return self._error(HTTPStatus.UNAUTHORIZED, "unauthorized", "A configured ingest token is required")
                result = self.command_centre.ingest(body, self.simulator)
                self.audit.append("security.observation", actor=str(body.get("provider", "security-adapter")), details={"source_id": body.get("id"), "status": result["status"], "event_id": (result.get("incident") or {}).get("event_id")})
                return self._json(result, HTTPStatus.CREATED if result["status"] != "duplicate" else HTTPStatus.OK)

            if path == "/api/v1/devices/register":
                if not (self._device_authorized() or self._operator_authorized()):
                    return self._error(HTTPStatus.UNAUTHORIZED, "unauthorized", "Device or operator token is required")
                device = self.devices.register(body)
                self.audit.append("device.register", actor=device["id"], details={"kind": device["kind"], "zone": device["zone"]})
                return self._json(device, HTTPStatus.CREATED)

            if path.startswith("/api/v1/devices/") and path.endswith("/heartbeat"):
                if not self._device_authorized():
                    return self._error(HTTPStatus.UNAUTHORIZED, "unauthorized", "Device token is required")
                device_id = path.split("/")[4]
                device = self.devices.heartbeat(device_id, body.get("telemetry") if isinstance(body, dict) else None)
                return self._json(device)

            if path.startswith("/api/v1/devices/") and "/commands/" in path and path.endswith("/ack"):
                if not self._device_authorized():
                    return self._error(HTTPStatus.UNAUTHORIZED, "unauthorized", "Device token is required")
                parts = path.split("/")
                command = self.devices.acknowledge(parts[4], parts[6], body.get("result") if isinstance(body, dict) else None)
                self.audit.append("device.command_ack", actor=parts[4], details={"command_id": parts[6], "result": command.get("result")})
                return self._json(command)

            if path.startswith("/api/v1/devices/") and path.endswith("/commands"):
                if not self._operator_authorized():
                    return self._error(HTTPStatus.UNAUTHORIZED, "unauthorized", "Operator token is required")
                device_id = path.split("/")[4]
                commands = self.devices.queue([device_id], str(body.get("action")), body.get("payload") if isinstance(body.get("payload"), dict) else {}, incident_id=body.get("incident_id"), origin=str(body.get("actor", "local-operator")))
                self.audit.append("device.command", details={"device_id": device_id, "action": body.get("action"), "command_id": commands[0]["id"]})
                return self._json(commands[0], HTTPStatus.CREATED)

            if path in {"/api/v1/announce", "/api/v1/talkback"}:
                if not self._operator_authorized():
                    return self._error(HTTPStatus.UNAUTHORIZED, "unauthorized", "Operator token is required")
                target_ids = body.get("device_ids") or []
                if not isinstance(target_ids, list):
                    raise ValueError("device_ids must be an array")
                if not target_ids and body.get("zone"):
                    target_ids = [item["id"] for item in self.devices.list() if item["zone"] == str(body["zone"]) and ({"speaker", "talkback"} & set(item["capabilities"]))]
                if not target_ids:
                    raise ValueError("at least one speaker-capable target is required")
                if body.get("audio_base64"):
                    action = "play_audio"
                    payload = {"audio_base64": str(body["audio_base64"]), "mime_type": str(body.get("mime_type") or "audio/webm")[:80]}
                else:
                    action = "speak"
                    text = str(body.get("text") or "").strip()
                    if not text or len(text) > 500:
                        raise ValueError("text must contain 1 to 500 characters")
                    payload = {"text": text, "priority": str(body.get("priority") or "operator")[:40]}
                commands = self.devices.queue(target_ids, action, payload, incident_id=body.get("incident_id"), origin=str(body.get("actor", "local-operator")))
                self.audit.append("operator.talkback", details={"targets": target_ids, "action": action, "commands": [item["id"] for item in commands]})
                return self._json({"commands": commands}, HTTPStatus.CREATED)

            if path == "/api/v1/settings":
                if not self._operator_authorized():
                    return self._error(HTTPStatus.UNAUTHORIZED, "unauthorized", "Operator token is required")
                allowed = {"retention_days", "max_records", "max_speed_mps", "site_timezone", "alert_confidence_floor"}
                unknown = set(body) - allowed
                if unknown:
                    raise ValueError(f"unknown settings: {', '.join(sorted(unknown))}")
                with self.settings_lock:
                    updated = {**type(self).settings}
                    if "retention_days" in body: updated["retention_days"] = max(1, min(3650, int(body["retention_days"])))
                    if "max_records" in body: updated["max_records"] = max(10, min(100000, int(body["max_records"])))
                    if "max_speed_mps" in body:
                        speed = float(body["max_speed_mps"])
                        if not math.isfinite(speed): raise ValueError("max_speed_mps must be finite")
                        updated["max_speed_mps"] = max(.05, min(.5, speed))
                    if "site_timezone" in body:
                        timezone_name = str(body["site_timezone"])
                        if not timezone_name or len(timezone_name) > 80: raise ValueError("site_timezone must contain 1 to 80 characters")
                        updated["site_timezone"] = timezone_name
                    if "alert_confidence_floor" in body:
                        floor = float(body["alert_confidence_floor"])
                        if not math.isfinite(floor): raise ValueError("alert_confidence_floor must be finite")
                        updated["alert_confidence_floor"] = max(.5, min(.99, floor))
                        self.command_centre.confidence_floor = updated["alert_confidence_floor"]
                    type(self).settings = updated
                    self.simulator.evidence.retention_days = updated["retention_days"]
                    self.simulator.evidence.max_records = updated["max_records"]
                    self.simulator.speed = updated["max_speed_mps"] * self.tick_seconds
                    temp = self.settings_path.with_suffix(f".{uuid.uuid4().hex}.tmp")
                    temp.write_text(json.dumps(updated, indent=2) + "\n", encoding="utf-8"); temp.replace(self.settings_path)
                self.audit.append("settings.update", details={"fields": sorted(body)})
                return self._json({**updated, "saved": True})

            return self._error(HTTPStatus.NOT_FOUND, "not_found", "API route not found")
        except json.JSONDecodeError:
            return self._error(HTTPStatus.BAD_REQUEST, "invalid_json", "Request body must be valid JSON")
        except (ValueError, TypeError) as exc:
            return self._error(HTTPStatus.BAD_REQUEST, "invalid_request", str(exc))
        except FileNotFoundError:
            return self._error(HTTPStatus.NOT_FOUND, "not_found", "Requested record was not found")

    @staticmethod
    def _validate_detection(body):
        if not isinstance(body, dict): raise ValueError("request body must be a JSON object")
        required = {"id", "event_type", "title", "severity", "confidence"}
        missing = required - body.keys()
        if missing: raise ValueError(f"missing fields: {', '.join(sorted(missing))}")
        allowed = required | {"source", "provider", "rule", "media_reference", "media_sha256"}
        unknown = set(body) - allowed
        if unknown: raise ValueError(f"unknown fields: {', '.join(sorted(unknown))}")
        if body["severity"] not in {"low", "medium", "high", "critical"}: raise ValueError("invalid severity")
        for field, limit in {"id":120, "event_type":80, "title":200, "source":200, "provider":120, "rule":120, "media_reference":1000}.items():
            if field in body:
                value = body[field]
                if not isinstance(value, str) or not value.strip() or len(value) > limit or any(ord(char) < 32 for char in value):
                    raise ValueError(f"{field} must contain 1 to {limit} printable characters")
        if isinstance(body["confidence"], bool): raise ValueError("confidence must be numeric")
        confidence = float(body["confidence"])
        if not math.isfinite(confidence): raise ValueError("confidence must be finite")
        if not 0 <= confidence <= 1: raise ValueError("confidence must be between 0 and 1")
        media_hash = body.get("media_sha256")
        if media_hash is not None and (len(str(media_hash)) != 64 or any(char not in "0123456789abcdefABCDEF" for char in str(media_hash))):
            raise ValueError("media_sha256 must be a 64-character hexadecimal digest")
        return {**body, "confidence": confidence}

    def _body(self):
        if self.headers.get("Content-Type", "").split(";")[0] != "application/json":
            raise ValueError("Content-Type must be application/json")
        try: length = int(self.headers.get("Content-Length", "0"))
        except ValueError as exc: raise ValueError("Content-Length must be an integer") from exc
        if length < 0: raise ValueError("Content-Length cannot be negative")
        if length > MAX_BODY: raise ValueError("request body is too large")
        return json.loads(self.rfile.read(length) or b"{}")

    def _operator_authorized(self):
        return not self.operator_token or self.headers.get("Authorization") == f"Bearer {self.operator_token}"

    def _ingest_authorized(self):
        return bool(self.ingest_token) and self.headers.get("Authorization") == f"Bearer {self.ingest_token}"

    def _device_authorized(self):
        token = self.device_token or self.ingest_token
        return bool(token) and self.headers.get("Authorization") == f"Bearer {token}"

    def _error(self, status, code, message):
        return self._json({"error": {"code": code, "message": message}}, status)

    def _json(self, payload, status=HTTPStatus.OK):
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers(); self.wfile.write(data)

    def log_message(self, fmt, *args):
        if self.path.startswith("/api/") and args and str(args[1]).startswith("2"): return
        super().log_message(fmt, *args)


def create_server(host="127.0.0.1", port=8765, *, data=None, scenario=None, ingest_token=""):
    scenario_path = Path(scenario or os.getenv("OPENPATROL_SCENARIO", ROOT / "scenarios" / "warehouse.json"))
    data_path = Path(data or os.getenv("OPENPATROL_DATA", ROOT / "runtime"))
    settings_path = data_path / "settings.json"
    defaults = {
        "retention_days": int(os.getenv("OPENPATROL_RETENTION_DAYS", "30")),
        "max_records": int(os.getenv("OPENPATROL_MAX_RECORDS", "5000")),
        "max_speed_mps": float(os.getenv("OPENPATROL_MAX_SPEED_MPS", "0.5")),
        "site_timezone": os.getenv("OPENPATROL_TIMEZONE", "Asia/Kolkata"),
        "alert_confidence_floor": float(os.getenv("OPENPATROL_ALERT_CONFIDENCE_FLOOR", ".7")),
    }
    try:
        settings = {**defaults, **json.loads(settings_path.read_text(encoding="utf-8"))}
        settings["retention_days"] = max(1, min(3650, int(settings["retention_days"])))
        settings["max_records"] = max(10, min(100000, int(settings["max_records"])))
        speed = float(settings["max_speed_mps"])
        if not math.isfinite(speed): raise ValueError("non-finite speed")
        settings["max_speed_mps"] = max(.05, min(.5, speed))
        settings["alert_confidence_floor"] = max(.5, min(.99, float(settings["alert_confidence_floor"])))
        timezone_name = str(settings["site_timezone"])
        if not timezone_name or len(timezone_name) > 80: raise ValueError("invalid timezone")
        settings["site_timezone"] = timezone_name
    except (FileNotFoundError, json.JSONDecodeError, OSError, ValueError, TypeError, KeyError):
        settings = defaults
    tick_seconds = max(.02, float(os.getenv("OPENPATROL_TICK_SECONDS", "0.4")))
    evidence = EvidenceStore(data_path / "evidence", retention_days=int(settings["retention_days"]), max_records=int(settings["max_records"]), signing_key=os.getenv("OPENPATROL_SIGNING_KEY", ""))
    simulator = PatrolSimulator(load_scenario(scenario_path), evidence, state_path=data_path / "runtime-state.json")
    simulator.speed = float(settings["max_speed_mps"]) * tick_seconds
    devices = DeviceRegistry(data_path / "command-centre")
    if not devices.list():
        devices.register({"id": "openpatrol-one", "name": "OpenPatrol One", "kind": "robot", "zone": "mobile", "capabilities": ["mobility", "video", "speaker", "strobe", "siren", "talkback"], "status": "online"})
        camera_ui = os.getenv("OPENPATROL_CAMERA_UI_URL", "").strip()
        frigate = os.getenv("FRIGATE_URL", "").strip()
        if camera_ui or frigate:
            devices.register({"id": "patrol-camera", "name": "Patrol Camera", "kind": "camera", "zone": "patrol", "capabilities": ["video", "audio_in"], "provider": "frigate", "streams": {"operator_url": camera_ui or frigate, "snapshot_url": f"{frigate.rstrip('/')}/api/patrol_camera/latest.jpg" if frigate else ""}})
    centre = CommandCentre(data_path / "command-centre", devices, confidence_floor=float(settings["alert_confidence_floor"]))
    handler = type("ConfiguredAppHandler", (AppHandler,), {
        "simulator": simulator, "settings": settings, "settings_path": settings_path,
        "tick_seconds": tick_seconds, "audit": AuditLog(data_path / "audit.jsonl"),
        "ingest_token": ingest_token or os.getenv("OPENPATROL_INGEST_TOKEN", ""),
        "operator_token": os.getenv("OPENPATROL_OPERATOR_TOKEN", ""),
        "device_token": os.getenv("OPENPATROL_DEVICE_TOKEN", ""),
        "command_centre": centre, "devices": devices, "started_at": time.monotonic(),
    })
    return ThreadingHTTPServer((host, port), handler), simulator


def main():
    host, port = os.getenv("OPENPATROL_HOST", "127.0.0.1"), int(os.getenv("OPENPATROL_PORT", "8765"))
    server, simulator = create_server(host, port)
    tick_seconds = server.RequestHandlerClass.tick_seconds
    stop = threading.Event()
    def run_simulation():
        while not stop.wait(tick_seconds): simulator.tick()
    threading.Thread(target=run_simulation, daemon=True, name="patrol-simulator").start()
    print(f"OpenPatrol running at http://{host}:{server.server_address[1]}")
    try: server.serve_forever()
    except KeyboardInterrupt: pass
    finally: stop.set(); server.server_close()

if __name__ == "__main__":
    main()
