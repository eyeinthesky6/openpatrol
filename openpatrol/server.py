from __future__ import annotations

import json
import math
import os
import threading
import time
import shutil
import uuid
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
    settings_path: Path
    settings: dict
    audit: AuditLog
    started_at = time.monotonic()
    settings_lock = threading.RLock()

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
        if path == "/api/v1/settings":
            return self._json({**self.settings,"operator_auth_enabled":bool(self.operator_token),"detector_auth_enabled":bool(self.ingest_token),"signing_enabled":bool(self.simulator.evidence.signing_key)})
        if path == "/api/v1/diagnostics":
            usage=shutil.disk_usage(self.simulator.evidence.directory); state=self.simulator.state(); audit=self.audit.verify(); receipts=[self.simulator.evidence.verify(item) for item in state["incidents"]]
            return self._json({"mode":"simulation","uptime_seconds":round(time.monotonic()-self.started_at,1),"storage":{"free_bytes":usage.free,"total_bytes":usage.total,"free_percent":round(usage.free/usage.total*100,1)},"integrity":{"audit_valid":audit["valid"],"receipt_failures":sum(not item["valid"] for item in receipts)},"navigation":{"localization":"fault" if state["robot"]["status"]=="fault" else "good","command_watchdog":"simulated","target":state["robot"]["target"]},"camera":{"front":{"status":"degraded","detail":"Synthetic preview only"},"rear":{"status":"offline","detail":"No adapter configured"}}})
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
            if path == "/api/v1/settings":
                if not self._operator_authorized(): return self._error(HTTPStatus.UNAUTHORIZED,"unauthorized","Operator token is required")
                allowed={"retention_days","max_records","max_speed_mps","site_timezone"}; unknown=set(body)-allowed
                if unknown: raise ValueError(f"unknown settings: {', '.join(sorted(unknown))}")
                with self.settings_lock:
                    updated={**type(self).settings}
                    if "retention_days" in body: updated["retention_days"]=max(1,min(3650,int(body["retention_days"])))
                    if "max_records" in body: updated["max_records"]=max(10,min(100000,int(body["max_records"])))
                    if "max_speed_mps" in body:
                        speed=float(body["max_speed_mps"])
                        if not math.isfinite(speed): raise ValueError("max_speed_mps must be finite")
                        updated["max_speed_mps"]=max(.05,min(.5,speed))
                    if "site_timezone" in body:
                        timezone_name=str(body["site_timezone"])
                        if not timezone_name or len(timezone_name)>80: raise ValueError("site_timezone must contain 1 to 80 characters")
                        updated["site_timezone"]=timezone_name
                    type(self).settings=updated; self.simulator.evidence.retention_days=updated["retention_days"]; self.simulator.evidence.max_records=updated["max_records"]; self.simulator.speed=updated["max_speed_mps"]*self.tick_seconds
                    temp=self.settings_path.with_suffix(f".{uuid.uuid4().hex}.tmp"); temp.write_text(json.dumps(updated,indent=2)+"\n",encoding="utf-8"); temp.replace(self.settings_path)
                self.audit.append("settings.update",details={"fields":sorted(body)}); return self._json({**updated,"saved":True})
            return self._error(HTTPStatus.NOT_FOUND, "not_found", "API route not found")
        except json.JSONDecodeError:
            return self._error(HTTPStatus.BAD_REQUEST, "invalid_json", "Request body must be valid JSON")
        except (ValueError, TypeError) as exc:
            return self._error(HTTPStatus.BAD_REQUEST, "invalid_request", str(exc))
        except FileNotFoundError:
            return self._error(HTTPStatus.NOT_FOUND, "incident_not_found", "Incident not found")

    @staticmethod
    def _validate_detection(body):
        if not isinstance(body, dict): raise ValueError("request body must be a JSON object")
        required = {"id", "event_type", "title", "severity", "confidence"}
        missing = required - body.keys()
        if missing: raise ValueError(f"missing fields: {', '.join(sorted(missing))}")
        if body["severity"] not in {"low", "medium", "high", "critical"}: raise ValueError("invalid severity")
        for field, limit in {"id":120,"event_type":80,"title":200,"source":200,"media_reference":1000}.items():
            if field in body:
                value=body[field]
                if not isinstance(value,str) or not value.strip() or len(value)>limit or any(ord(char)<32 for char in value):
                    raise ValueError(f"{field} must contain 1 to {limit} printable characters")
        if isinstance(body["confidence"], bool): raise ValueError("confidence must be numeric")
        confidence = float(body["confidence"])
        if not math.isfinite(confidence): raise ValueError("confidence must be finite")
        if not 0 <= confidence <= 1: raise ValueError("confidence must be between 0 and 1")
        media_hash = body.get("media_sha256")
        if media_hash is not None and (len(str(media_hash)) != 64 or any(char not in "0123456789abcdefABCDEF" for char in str(media_hash))): raise ValueError("media_sha256 must be a 64-character hexadecimal digest")
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
    settings_path=data_path/"settings.json"; defaults={"retention_days":int(os.getenv("OPENPATROL_RETENTION_DAYS","30")),"max_records":int(os.getenv("OPENPATROL_MAX_RECORDS","5000")),"max_speed_mps":float(os.getenv("OPENPATROL_MAX_SPEED_MPS","0.5")),"site_timezone":os.getenv("OPENPATROL_TIMEZONE","Asia/Kolkata")}
    try:
        settings={**defaults,**json.loads(settings_path.read_text(encoding="utf-8"))}
        settings["retention_days"]=max(1,min(3650,int(settings["retention_days"])))
        settings["max_records"]=max(10,min(100000,int(settings["max_records"])))
        speed=float(settings["max_speed_mps"])
        if not math.isfinite(speed): raise ValueError("non-finite speed")
        settings["max_speed_mps"]=max(.05,min(.5,speed))
        timezone_name=str(settings["site_timezone"])
        if not timezone_name or len(timezone_name)>80: raise ValueError("invalid timezone")
        settings["site_timezone"]=timezone_name
    except (FileNotFoundError,json.JSONDecodeError,OSError,ValueError,TypeError,KeyError): settings=defaults
    tick_seconds=max(.02,float(os.getenv("OPENPATROL_TICK_SECONDS","0.4")))
    evidence = EvidenceStore(data_path / "evidence", retention_days=int(settings["retention_days"]), max_records=int(settings["max_records"]), signing_key=os.getenv("OPENPATROL_SIGNING_KEY", ""))
    simulator = PatrolSimulator(load_scenario(scenario_path), evidence, state_path=data_path / "runtime-state.json")
    simulator.speed=float(settings["max_speed_mps"])*tick_seconds
    handler = type("ConfiguredAppHandler", (AppHandler,), {"simulator": simulator,"settings":settings,"settings_path":settings_path,"tick_seconds":tick_seconds,"audit":AuditLog(data_path/"audit.jsonl"),"ingest_token":ingest_token or os.getenv("OPENPATROL_INGEST_TOKEN",""),"operator_token":os.getenv("OPENPATROL_OPERATOR_TOKEN",""),"started_at":time.monotonic()})
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


if __name__ == "__main__": main()
