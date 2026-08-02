"""Open adapters for alarm, VMS and home-automation events.

Input can be NDJSON on stdin or MQTT. The bridge normalizes common flat,
Home-Assistant, ONVIF/Hikvision-style and generic webhook payloads before posting
to the versioned OpenPatrol security-event endpoint.
"""
from __future__ import annotations
import argparse
import json
import math
import os
import sys
import time
import urllib.request
from typing import Any

ALIASES = {
    "binary_sensor.door": "door_open", "door": "door_open", "door_open": "door_open", "contact": "door_open",
    "glassbreak": "glass_break", "glass_break": "glass_break", "forced": "forced_entry", "forced_entry": "forced_entry",
    "pir": "motion", "motion": "motion", "tamper": "tamper", "panic": "panic",
    "smoke": "smoke", "fire": "fire", "water": "water_leak", "water_leak": "water_leak",
    "pool_distress": "drowning_distress", "drowning": "drowning_distress",
    "linecrossing": "restricted_zone_entry", "fielddetection": "restricted_zone_entry",
    "videoloss": "tamper", "shelteralarm": "tamper",
}
INACTIVE = {False, 0, "0", "off", "closed", "clear", "normal", "inactive", "false"}


def _flatten_provider_payload(item: dict[str, Any]) -> dict[str, Any]:
    """Extract common fields without binding OpenPatrol to one vendor schema."""
    event = item.get("event") if isinstance(item.get("event"), dict) else {}
    data = item.get("data") if isinstance(item.get("data"), dict) else {}
    after = item.get("after") if isinstance(item.get("after"), dict) else {}
    attributes = item.get("attributes") if isinstance(item.get("attributes"), dict) else {}
    merged = {**event, **data, **after, **item}
    if attributes:
        merged["attributes"] = attributes
    raw_type = (
        merged.get("event_type") or merged.get("type") or merged.get("eventType") or
        merged.get("event") or merged.get("label") or merged.get("name") or
        attributes.get("device_class") or ""
    )
    if isinstance(raw_type, dict):
        raw_type = raw_type.get("type") or raw_type.get("name") or ""
    merged["_raw_type"] = raw_type
    return merged


def normalize_security_event(item: dict[str, Any], provider: str = "generic") -> dict[str, Any]:
    if not isinstance(item, dict):
        raise ValueError("event must be an object")
    merged = _flatten_provider_payload(item)
    raw_type = str(merged.get("_raw_type") or "").strip().lower().replace("-", "_").replace(" ", "_")
    event_type = ALIASES.get(raw_type, raw_type)
    if not event_type:
        raise ValueError("event_type is required")
    device_id = str(merged.get("device_id") or merged.get("entity_id") or merged.get("camera") or merged.get("sourceId") or "external")[:120]
    zone = str(merged.get("zone") or merged.get("area") or merged.get("location") or merged.get("region") or "unassigned")[:120]
    state = merged.get("state", merged.get("active", True))
    if event_type in {"door_open", "motion", "smoke", "fire", "tamper", "panic"} and state in INACTIVE:
        raise ValueError("inactive event state")
    confidence = float(merged.get("confidence", merged.get("score", 1.0)))
    if not math.isfinite(confidence) or not 0 <= confidence <= 1:
        raise ValueError("confidence must be between 0 and 1")
    severity = str(merged.get("severity") or ("critical" if event_type in {"fire", "panic", "drowning_distress"} else "high" if event_type in {"tamper", "forced_entry", "glass_break", "restricted_zone_entry"} else "medium"))
    observed_at = merged.get("observed_at") or merged.get("timestamp") or merged.get("time")
    result = {
        "id": str(merged.get("id") or merged.get("event_id") or merged.get("eventId") or f"{provider}-{device_id}-{observed_at or time.time_ns()}")[:120],
        "event_type": event_type,
        "title": str(merged.get("title") or merged.get("description") or f"{event_type.replace('_',' ').title()} at {zone}")[:200],
        "severity": severity, "confidence": confidence,
        "source": str(merged.get("source") or f"security/{provider}/{device_id}")[:200],
        "provider": str(merged.get("provider") or provider)[:120], "device_id": device_id,
        "zone": zone, "observed_at": observed_at,
        "attributes": merged.get("attributes") if isinstance(merged.get("attributes"), dict) else {},
    }
    media = merged.get("media_reference") or merged.get("clip") or merged.get("snapshot")
    if media:
        result["media_reference"] = str(media)[:1000]
    return result


def post_event(url: str, token: str, event: dict[str, Any]) -> dict[str, Any]:
    request = urllib.request.Request(
        url.rstrip("/") + "/api/v1/security-events",
        data=json.dumps(event).encode(),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=15) as response:
        return json.load(response)


def _stdin_mode(args: argparse.Namespace, token: str) -> None:
    for number, line in enumerate(sys.stdin, 1):
        if not line.strip():
            continue
        try:
            event = normalize_security_event(json.loads(line), args.provider)
            result = post_event(args.url, token, event)
            print(json.dumps({"line": number, "status": result.get("status"), "id": event["id"]}), flush=True)
        except Exception as exc:
            print(json.dumps({"line": number, "status": "rejected", "error": str(exc)}), file=sys.stderr, flush=True)


def _mqtt_mode(args: argparse.Namespace, token: str) -> None:
    try:
        import paho.mqtt.client as mqtt
    except ImportError as exc:
        raise SystemExit("Install the mqtt extra: pip install 'openpatrol[mqtt]'") from exc

    def on_message(client, userdata, message):
        try:
            payload = json.loads(message.payload)
            if isinstance(payload, dict):
                payload.setdefault("source", f"mqtt/{message.topic}")
            event = normalize_security_event(payload, args.provider)
            post_event(args.url, token, event)
        except Exception as exc:
            print(f"Security MQTT event rejected on {message.topic}: {exc}", flush=True)

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.username_pw_set(args.mqtt_user, args.mqtt_password) if args.mqtt_user else None
    client.on_message = on_message
    client.connect(args.mqtt_host, args.mqtt_port)
    client.subscribe(args.mqtt_topic)
    client.loop_forever()


def main() -> None:
    parser = argparse.ArgumentParser(description="Normalize security-system events for OpenPatrol")
    parser.add_argument("--provider", default=os.getenv("OPENPATROL_SECURITY_PROVIDER", "generic"))
    parser.add_argument("--url", default=os.getenv("OPENPATROL_URL", "http://127.0.0.1:8765"))
    parser.add_argument("--mqtt-host", default=os.getenv("OPENPATROL_SECURITY_MQTT_HOST"))
    parser.add_argument("--mqtt-port", type=int, default=int(os.getenv("OPENPATROL_SECURITY_MQTT_PORT", "1883")))
    parser.add_argument("--mqtt-topic", default=os.getenv("OPENPATROL_SECURITY_MQTT_TOPIC", "security/#"))
    parser.add_argument("--mqtt-user", default=os.getenv("OPENPATROL_SECURITY_MQTT_USER"))
    parser.add_argument("--mqtt-password", default=os.getenv("OPENPATROL_SECURITY_MQTT_PASSWORD"))
    args = parser.parse_args()
    token = os.environ["OPENPATROL_INGEST_TOKEN"]
    if args.mqtt_host:
        _mqtt_mode(args, token)
    else:
        _stdin_mode(args, token)


if __name__ == "__main__":
    main()
