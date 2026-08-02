"""Serial bridge for the OpenPatrol Security Sensor Hub Rev A."""
from __future__ import annotations
import argparse
import json
import os
import time
from typing import Any
from .security_bridge import post_event

ZONE_TYPES = {
    1: "door_open", 2: "motion", 3: "glass_break", 4: "panic",
    5: "smoke", 6: "drowning_distress", 7: "tamper", 8: "water_leak",
}


def normalize_hub_message(message: dict[str, Any], *, device_id: str, zone_names: dict[int, str] | None = None) -> dict[str, Any] | None:
    if message.get("v") != 1:
        raise ValueError("unsupported sensor-hub protocol")
    if message.get("type") != "zone":
        return None
    zone_number = int(message["zone"])
    state = str(message.get("state") or "unknown")
    if state == "normal":
        return None
    event_type = "tamper" if state in {"open", "short"} else ZONE_TYPES.get(zone_number, "alarm_input")
    zone = (zone_names or {}).get(zone_number, f"sensor-zone-{zone_number}")
    severity = "critical" if event_type in {"smoke", "panic", "drowning_distress"} else "high" if event_type in {"glass_break", "tamper"} else "medium"
    return {
        "id": f"{device_id}-{message.get('seq', time.time_ns())}",
        "event_type": event_type,
        "title": f"{event_type.replace('_',' ').title()} at {zone}",
        "severity": severity, "confidence": 1.0,
        "source": f"sensor-hub/{device_id}", "provider": "openpatrol-sensor-hub-v1",
        "device_id": device_id, "zone": zone,
        "attributes": {"zone_number": zone_number, "loop_state": state, "raw": message.get("raw")},
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", default=os.getenv("OPENPATROL_SENSOR_PORT", "/dev/ttyACM0"))
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument("--device-id", default=os.getenv("OPENPATROL_DEVICE_ID", "sensor-hub-1"))
    parser.add_argument("--url", default=os.getenv("OPENPATROL_URL", "http://127.0.0.1:8765"))
    args = parser.parse_args()
    try:
        import serial
    except ImportError as exc:
        raise SystemExit("Install the sensor extra: pip install 'openpatrol[sensor]'") from exc
    token = os.environ["OPENPATROL_INGEST_TOKEN"]
    with serial.Serial(args.port, args.baud, timeout=2) as stream:
        while True:
            line = stream.readline()
            if not line:
                continue
            try:
                event = normalize_hub_message(json.loads(line), device_id=args.device_id)
                if event:
                    post_event(args.url, token, event)
            except Exception as exc:
                print(f"Sensor hub message rejected: {exc}", flush=True)


if __name__ == "__main__":
    main()
