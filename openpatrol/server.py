from __future__ import annotations

import json
import os
import threading
import time
from http import HTTPStatus
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse

from .evidence import EvidenceStore
from .audit import AuditLog
from .scenario import load_scenario
from .simulator import PatrolSimulator

ROOT = Path(__file__).resolve().parent.parent
STATIC = ROOT / "static"
MAX_BODY = 64 * 1024


class AppHandler(SimpleHTTPRequestHandler):
    simulator: PatrolSimulator
    ingest_token = ""
    operator_token = ""
    audit: AuditLog
    started_at = time.monotonic()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(STATIC), **kwargs)

    def end_headers(self):
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy", "default-src 'self'; style-src 'self'; script-src 'self'; img-src 'self' data:; connect-src 'self'")
        self.send_header("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        super().end_headers()

    def do_GET(self):
        path = urlparse(self.path).path
        if path in {"/api/state", "/api/v1/state"}:
            return self._json(self.simulator.state())
        if path in {"/api/health", "/api/v1/health"}:
            return self._json({"status": "ok", "mode": "simulation", "local_only": True, "uptime_seconds": round(time.monotonic() - self.started_at, 1)})
        if path == "/api/v1/incidents":
            return self._json({"incidents": self.simulator.evidence.list()})
        if path == "/api/v1/audit/verify":
            return self._json(self.audit.verify())
        if path.startswith("/api/v1/incidents/") and path.endswith("/verify"):
            event_id = path.split("/")[4]
            try: return self._json(self.simulator.evidence.verify(event_id))
            except (FileNotFoundError, json.JSONDecodeError): return self._error(HTTPStatus.NOT_FOUND, "incident_not_found", "Incident not found")
        if path == "/metrics":
            state = self.simulator.state()
            body = (f"openpatrol_battery_percent {state['robot']['battery']}\nopenpatrol_laps_total {state['robot']['lap']}\nopenpatrol_incidents_total {len(state['incidents'])}\n").encode()
            self.send_response(HTTPStatus.OK); self.send_header("Content-Type", "text/plain; version=0.0.4"); self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body); return
        if path.startswith("/api/"):
            return self._error(HTTPStatus.NOT_FOUND, "not_found", "API route not found")
        return super().do_GET()

    def do_POST(self):
        path = urlparse(self.path).path
        try:
            body = self._body()
            if path in {"/api/patrol", "/api/v1/commands"}:
                if not self._operator_authorized(): return self._error(HTTPStatus.UNAUTHORIZED, "unauthorized", "Operator token is required")
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
                if not self._operator_authorized(): return self._error(HTTPStatus.UNAUTHORIZED, "unauthorized", "Operator token is required")
                event_id = path.split("/")[-2]
                receipt = self.simulator.evidence.update_review(event_id, str(body.get("disposition", "")), str(body.get("note", "")), str(body.get("actor", "local-operator")))
                self.audit.append("incident.review", actor=str(body.get("actor", "local-operator")), details={"event_id": event_id, "disposition": body.get("disposition")})
                return self._json(receipt)
            if path == "/api/v1/detections":
                if not self.ingest_token or self.headers.get("Authorization") != f"Bearer {self.ingest_token}":
                    return self._error(HTTPStatus.UNAUTHORIZED, "unauthorized", "A configured ingest token is required")
                event = self._validate_detection(body)
                receipt = self.simulator.ingest_detection(event)
                self.audit.append("detection.ingest", actor="detector-adapter", details={"event_id": receipt["event_id"], "source": event.get("source", "external")})
                return self._json(receipt, HTTPStatus.CREATED)
            return self._error(HTTPStatus.NOT_FOUND, "not_found", "API route not found")
        except json.JSONDecodeError:
            return self._error(HTTPStatus.BAD_REQUEST, "invalid_json", "Request body must be valid JSON")
        except (ValueError, TypeError) as exc:
            return self._error(HTTPStatus.BAD_REQUEST, "invalid_request", str(exc))
        except FileNotFoundError:
            return self._error(HTTPStatus.NOT_FOUND, "incident_not_found", "Incident not found")

    @staticmethod
    def _validate_detection(body):
        required = {"id", "event_type", "title", "severity", "confidence"}
        missing = required - body.keys()
        if missing: raise ValueError(f"missing fields: {', '.join(sorted(missing))}")
        if body["severity"] not in {"low", "medium", "high", "critical"}: raise ValueError("invalid severity")
        confidence = float(body["confidence"])
        if not 0 <= confidence <= 1: raise ValueError("confidence must be between 0 and 1")
        media_hash = body.get("media_sha256")
        if media_hash is not None and (len(str(media_hash)) != 64 or any(char not in "0123456789abcdefABCDEF" for char in str(media_hash))): raise ValueError("media_sha256 must be a 64-character hexadecimal digest")
        return {**body, "confidence": confidence}

    def _body(self):
        if self.headers.get("Content-Type", "").split(";")[0] != "application/json":
            raise ValueError("Content-Type must be application/json")
        length = int(self.headers.get("Content-Length", "0"))
        if length > MAX_BODY: raise ValueError("request body is too large")
        return json.loads(self.rfile.read(length) or b"{}")

    def _operator_authorized(self):
        return not self.operator_token or self.headers.get("Authorization") == f"Bearer {self.operator_token}"

    def _error(self, status, code, message):
        return self._json({"error": {"code": code, "message": message}}, status)

    def _json(self, payload, status=HTTPStatus.OK):
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status); self.send_header("Content-Type", "application/json; charset=utf-8"); self.send_header("Content-Length", str(len(data))); self.send_header("Cache-Control", "no-store"); self.end_headers(); self.wfile.write(data)

    def log_message(self, fmt, *args):
        if self.path.startswith("/api/") and args and str(args[1]).startswith("2"): return
        super().log_message(fmt, *args)


def create_server(host="127.0.0.1", port=8765, *, data=None, scenario=None, ingest_token=""):
    scenario_path = Path(scenario or os.getenv("OPENPATROL_SCENARIO", ROOT / "scenarios" / "warehouse.json"))
    data_path = Path(data or os.getenv("OPENPATROL_DATA", ROOT / "runtime"))
    evidence = EvidenceStore(data_path / "evidence", retention_days=int(os.getenv("OPENPATROL_RETENTION_DAYS", "30")), max_records=int(os.getenv("OPENPATROL_MAX_RECORDS", "5000")), signing_key=os.getenv("OPENPATROL_SIGNING_KEY", ""))
    simulator = PatrolSimulator(load_scenario(scenario_path), evidence, state_path=data_path / "runtime-state.json")
    handler = type("ConfiguredAppHandler", (AppHandler,), {"simulator": simulator, "audit": AuditLog(data_path / "audit.jsonl"), "ingest_token": ingest_token or os.getenv("OPENPATROL_INGEST_TOKEN", ""), "operator_token": os.getenv("OPENPATROL_OPERATOR_TOKEN", ""), "started_at": time.monotonic()})
    return ThreadingHTTPServer((host, port), handler), simulator


def main():
    host, port = os.getenv("OPENPATROL_HOST", "127.0.0.1"), int(os.getenv("OPENPATROL_PORT", "8765"))
    server, simulator = create_server(host, port)
    tick_seconds = max(0.02, float(os.getenv("OPENPATROL_TICK_SECONDS", "0.4")))
    stop = threading.Event()
    def run_simulation():
        while not stop.wait(tick_seconds): simulator.tick()
    threading.Thread(target=run_simulation, daemon=True, name="patrol-simulator").start()
    print(f"OpenPatrol running at http://{host}:{server.server_address[1]}")
    try: server.serve_forever()
    except KeyboardInterrupt: pass
    finally: stop.set(); server.server_close()


if __name__ == "__main__": main()
