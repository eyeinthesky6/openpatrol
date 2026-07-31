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
from .scenario import load_scenario
from .simulator import PatrolSimulator

ROOT = Path(__file__).resolve().parent.parent
STATIC = ROOT / "static"
DATA = Path(os.getenv("OPENPATROL_DATA", ROOT / "runtime"))
SCENARIO = Path(os.getenv("OPENPATROL_SCENARIO", ROOT / "scenarios" / "warehouse.json"))


class AppHandler(SimpleHTTPRequestHandler):
    simulator: PatrolSimulator

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(STATIC), **kwargs)

    def do_GET(self):
        if self.path == "/api/state":
            self._json(self.simulator.state())
            return
        if self.path == "/api/health":
            self._json({"status": "ok", "mode": "simulation", "local_only": True})
            return
        super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/patrol":
            body = self._body()
            self.simulator.set_status(body.get("status", "paused"))
            self._json(self.simulator.state())
            return
        if parsed.path.startswith("/api/incidents/") and parsed.path.endswith("/review"):
            event_id = parsed.path.split("/")[3]
            body = self._body()
            disposition = body.get("disposition")
            if disposition not in {"confirmed", "dismissed", "escalated"}:
                self._json({"error": "invalid disposition"}, HTTPStatus.BAD_REQUEST)
                return
            try:
                receipt = self.simulator.evidence.update_review(event_id, disposition, body.get("note", ""))
            except FileNotFoundError:
                self._json({"error": "incident not found"}, HTTPStatus.NOT_FOUND)
                return
            self._json(receipt)
            return
        self._json({"error": "not found"}, HTTPStatus.NOT_FOUND)

    def log_message(self, fmt, *args):
        if self.path.startswith("/api/") and args and str(args[1]) == "200":
            return
        super().log_message(fmt, *args)

    def _body(self):
        length = int(self.headers.get("Content-Length", "0"))
        return json.loads(self.rfile.read(length) or b"{}")

    def _json(self, payload, status=HTTPStatus.OK):
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers(); self.wfile.write(data)


def main():
    scenario = load_scenario(SCENARIO)
    simulator = PatrolSimulator(scenario, EvidenceStore(DATA / "evidence"))
    AppHandler.simulator = simulator
    tick_seconds = float(os.getenv("OPENPATROL_TICK_SECONDS", "0.4"))

    def run_simulation():
        while True:
            simulator.tick(); time.sleep(tick_seconds)

    threading.Thread(target=run_simulation, daemon=True, name="patrol-simulator").start()
    address = (os.getenv("OPENPATROL_HOST", "127.0.0.1"), int(os.getenv("OPENPATROL_PORT", "8765")))
    print(f"OpenPatrol running at http://{address[0]}:{address[1]}")
    ThreadingHTTPServer(address, AppHandler).serve_forever()


if __name__ == "__main__":
    main()
