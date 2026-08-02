"""Optional Frigate MQTT adapter.

Frigate remains the recorder/restreamer/object tracker. OpenPatrol consumes its
versioned events and converts object, zone and custom-model labels into the
provider-neutral security-event contract.
"""
from __future__ import annotations
import argparse
import json
import os
import time
import urllib.request
from typing import Any

CUSTOM_LABELS = {
    "fall", "fallen_person", "person_down", "fight", "violence", "aggressive_motion",
    "drowning", "drowning_distress", "pool_distress", "smoke", "fire", "panic",
}


def normalize_frigate_event(message: dict[str, Any], base_url: str = "") -> dict[str, Any] | None:
    after = message.get("after") or {}
    if message.get("type") not in {"new", "update", "end"} or not after.get("id") or not after.get("label"):
        return None
    score = float(after.get("top_score") or after.get("score") or 0)
    label = str(after["label"]).lower().replace("-", "_")
    camera = str(after.get("camera", "unknown"))
    zones = [str(zone) for zone in (after.get("entered_zones") or after.get("current_zones") or [])]
    zone = zones[-1] if zones else camera
    restricted = {zone.strip() for zone in os.getenv("OPENPATROL_RESTRICTED_ZONES", "").split(",") if zone.strip()}
    duration = max(0.0, float(after.get("end_time") or time.time()) - float(after.get("start_time") or time.time()))
    loiter_seconds = max(1, int(os.getenv("OPENPATROL_LOITER_SECONDS", "300")))
    rule, event_type, severity = "object_detected", label, "medium"
    title = f"{label.replace('_', ' ').title()} at {camera}"
    if label == "person" and restricted.intersection(zones):
        rule, event_type, severity = "restricted_zone_entry", "restricted_zone_entry", "high"
        title = f"Person entered restricted zone at {camera}"
    elif label == "person" and duration >= loiter_seconds:
        rule, event_type, severity = "loitering", "loitering", "high"
        title = f"Person remained at {camera} for {int(duration)} seconds"
    elif label in CUSTOM_LABELS:
        aliases = {"fallen_person":"fall", "person_down":"fall", "violence":"aggressive_motion", "drowning":"drowning_distress", "pool_distress":"drowning_distress"}
        event_type = aliases.get(label, label)
        rule = f"frigate_{event_type}"
        severity = "critical" if event_type in {"drowning_distress", "fire"} else "high"
    elif label == "person" and score >= .8:
        severity = "high"
    clip = f"{base_url.rstrip('/')}/api/events/{after['id']}/clip.mp4" if base_url else None
    detection = {
        "id": f"frigate-{after['id']}", "event_type": event_type, "title": title,
        "severity": severity, "confidence": max(0.0, min(score, 1.0)),
        "source": f"frigate/{camera}", "provider": "frigate", "rule": rule,
        "device_id": camera, "zone": zone,
        "attributes": {"label": label, "zones": zones, "duration_seconds": round(duration, 2)},
    }
    if clip:
        detection["media_reference"] = clip
    return detection


def post_detection(api_url: str, token: str, detection: dict[str, Any]) -> dict[str, Any]:
    request = urllib.request.Request(
        api_url.rstrip("/") + "/api/v1/security-events",
        data=json.dumps(detection).encode(),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        if response.status not in {200, 201}:
            raise RuntimeError(f"OpenPatrol returned {response.status}")
        return json.load(response)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mqtt-host", default=os.getenv("FRIGATE_MQTT_HOST", "127.0.0.1"))
    parser.add_argument("--mqtt-port", type=int, default=int(os.getenv("FRIGATE_MQTT_PORT", "1883")))
    args = parser.parse_args()
    try:
        import paho.mqtt.client as mqtt
    except ImportError as exc:
        raise SystemExit("Install the mqtt extra: pip install 'openpatrol[mqtt]'") from exc
    api = os.getenv("OPENPATROL_URL", "http://127.0.0.1:8765")
    token = os.environ["OPENPATROL_INGEST_TOKEN"]
    frigate = os.getenv("FRIGATE_URL", "")

    def on_message(client, userdata, message):
        try:
            event = normalize_frigate_event(json.loads(message.payload), frigate)
            if event:
                post_detection(api, token, event)
        except Exception as exc:
            print(f"Frigate event rejected: {exc}", flush=True)

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_message = on_message
    client.connect(args.mqtt_host, args.mqtt_port)
    client.subscribe("frigate/events")
    client.loop_forever()


if __name__ == "__main__":
    main()
