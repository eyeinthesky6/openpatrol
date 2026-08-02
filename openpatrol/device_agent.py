"""Endpoint agent for speakers, strobes and sirens on robots or fixed hubs."""
from __future__ import annotations
import argparse
import base64
import json
import os
import shutil
import subprocess
import tempfile
import time
import urllib.request
from typing import Any

ALLOWED_ACTIONS = {"notify", "speak", "play_audio", "strobe", "siren", "stop_output"}


def _request(url: str, token: str, *, body: dict[str, Any] | None = None) -> Any:
    data = json.dumps(body).encode() if body is not None else None
    headers = {"Authorization": f"Bearer {token}"}
    if data is not None:
        headers["Content-Type"] = "application/json"
    with urllib.request.urlopen(urllib.request.Request(url, data=data, headers=headers, method="POST" if data is not None else "GET"), timeout=15) as response:
        return json.load(response)


def choose_player() -> str | None:
    return next((item for item in ("ffplay", "mpv", "aplay") if shutil.which(item)), None)


def execute_command(command: dict[str, Any], *, dry_run: bool = False) -> dict[str, Any]:
    action = command.get("action")
    if action not in ALLOWED_ACTIONS:
        return {"ok": False, "error": "unsupported_action"}
    payload = command.get("payload") or {}
    if dry_run:
        return {"ok": True, "dry_run": True, "action": action}
    if action in {"notify", "strobe", "siren", "stop_output"}:
        # Hardware GPIO/relay integration is intentionally configured outside the
        # command payload; remote input can never inject a shell command.
        print(json.dumps({"device_output": action, "payload": payload}), flush=True)
        return {"ok": True, "action": action}
    if action == "speak":
        text = str(payload.get("text") or "")[:500]
        if not text:
            return {"ok": False, "error": "empty_text"}
        speaker = next((item for item in ("espeak-ng", "spd-say", "say") if shutil.which(item)), None)
        if not speaker:
            return {"ok": False, "error": "no_tts_player"}
        subprocess.run([speaker, text], check=False, timeout=45)
        return {"ok": True, "action": action, "player": speaker}
    audio = payload.get("audio_base64")
    if not audio:
        return {"ok": False, "error": "missing_audio"}
    player = choose_player()
    if not player:
        return {"ok": False, "error": "no_audio_player"}
    raw = base64.b64decode(audio, validate=True)
    if len(raw) > 512 * 1024:
        return {"ok": False, "error": "audio_too_large"}
    suffix = ".webm" if "webm" in str(payload.get("mime_type")) else ".wav"
    with tempfile.NamedTemporaryFile(suffix=suffix) as media:
        media.write(raw); media.flush()
        args = [player, "-nodisp", "-autoexit", "-loglevel", "quiet", media.name] if player == "ffplay" else [player, media.name]
        subprocess.run(args, check=False, timeout=60)
    return {"ok": True, "action": action, "player": player}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--device-id", default=os.environ.get("OPENPATROL_DEVICE_ID"))
    parser.add_argument("--url", default=os.environ.get("OPENPATROL_URL", "http://127.0.0.1:8765"))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if not args.device_id:
        raise SystemExit("--device-id or OPENPATROL_DEVICE_ID is required")
    token = os.environ["OPENPATROL_DEVICE_TOKEN"]
    base = args.url.rstrip("/")
    while True:
        try:
            _request(f"{base}/api/v1/devices/{args.device_id}/heartbeat", token, body={"telemetry": {"agent": "online"}})
            commands = _request(f"{base}/api/v1/devices/{args.device_id}/commands", token).get("commands", [])
            for command in commands:
                result = execute_command(command, dry_run=args.dry_run)
                _request(f"{base}/api/v1/devices/{args.device_id}/commands/{command['id']}/ack", token, body={"result": result})
        except Exception as exc:
            print(f"OpenPatrol device agent: {exc}", flush=True)
        time.sleep(2)

if __name__ == "__main__":
    main()
