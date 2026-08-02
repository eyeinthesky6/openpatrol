"""Local video-event normalization and lightweight motion analytics.

Motion/scene-change detection works with OpenCV when installed. High-level fall,
fight, drowning and intrusion labels are accepted from any model through the
same normalized contract; site-specific model validation remains mandatory.
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

MODEL_ALIASES = {
    "falling": "fall", "fallen_person": "fall", "person_down": "fall",
    "fight": "fight", "violence": "aggressive_motion", "aggression": "aggressive_motion",
    "drowning": "drowning_distress", "swimmer_distress": "drowning_distress",
    "intrusion": "restricted_zone_entry", "forced_entry": "forced_entry",
    "rapid_motion": "sudden_motion", "smoke": "smoke", "fire": "fire",
}


def normalize_model_event(item: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(item, dict):
        raise ValueError("model event must be an object")
    label = str(item.get("label") or item.get("event_type") or "").strip().lower().replace("-", "_").replace(" ", "_")
    event_type = MODEL_ALIASES.get(label, label)
    if not event_type:
        raise ValueError("label is required")
    confidence = float(item.get("confidence"))
    if not math.isfinite(confidence) or not 0 <= confidence <= 1:
        raise ValueError("confidence must be between 0 and 1")
    camera = str(item.get("camera") or item.get("device_id") or "camera")[:120]
    zone = str(item.get("zone") or camera)[:120]
    default_severity = "critical" if event_type in {"drowning_distress", "fire"} else "high" if event_type in {"fall", "fight", "forced_entry", "restricted_zone_entry"} else "medium"
    result = {
        "id": str(item.get("id") or f"model-{camera}-{time.time_ns()}")[:120],
        "event_type": event_type,
        "title": str(item.get("title") or f"{event_type.replace('_',' ').title()} at {zone}")[:200],
        "severity": str(item.get("severity") or default_severity), "confidence": confidence,
        "source": str(item.get("source") or f"vision/{item.get('provider','generic')}/{camera}")[:200],
        "provider": str(item.get("provider") or "generic-model")[:120],
        "device_id": camera, "zone": zone, "observed_at": item.get("observed_at"),
        "attributes": item.get("attributes") if isinstance(item.get("attributes"), dict) else {},
    }
    if item.get("media_reference"):
        result["media_reference"] = str(item["media_reference"])[:1000]
    return result


def motion_score(previous: Any, current: Any) -> float:
    """Return normalized mean absolute frame difference for numpy arrays."""
    try:
        import numpy as np
        if previous is None or current is None or previous.shape != current.shape:
            return 0.0
        return float(np.mean(np.abs(current.astype("float32") - previous.astype("float32"))) / 255.0)
    except (ImportError, AttributeError, ValueError):
        return 0.0


def post_event(url: str, token: str, event: dict[str, Any]) -> None:
    request = urllib.request.Request(url.rstrip("/") + "/api/v1/security-events", data=json.dumps(event).encode(), headers={"Content-Type":"application/json", "Authorization":f"Bearer {token}"}, method="POST")
    with urllib.request.urlopen(request, timeout=15):
        pass



def run_motion_stream(stream_url: str, *, api_url: str, token: str, camera: str, zone: str, threshold: float = .12, cooldown_seconds: float = 10.0) -> None:
    """Read an RTSP/video stream and emit calibrated sudden-motion observations.

    This is deliberately a scene-change detector, not a fall/fight/drowning
    classifier. Sites can use any validated model to emit the richer labels.
    """
    try:
        import cv2
    except ImportError as exc:
        raise SystemExit("Install the analytics extra: pip install 'openpatrol[analytics]'") from exc
    capture = cv2.VideoCapture(stream_url)
    if not capture.isOpened():
        raise SystemExit(f"Cannot open video stream: {stream_url}")
    previous = None
    last_event = 0.0
    while True:
        ok, frame = capture.read()
        if not ok:
            capture.release(); time.sleep(2); capture = cv2.VideoCapture(stream_url); previous = None; continue
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.resize(gray, (320, 180))
        gray = cv2.GaussianBlur(gray, (7, 7), 0)
        score = motion_score(previous, gray)
        previous = gray
        now = time.monotonic()
        if score >= threshold and now - last_event >= cooldown_seconds:
            confidence = min(.95, .55 + (score - threshold) * 2.5)
            event = normalize_model_event({
                "id": f"motion-{camera}-{time.time_ns()}", "label": "sudden_motion",
                "confidence": confidence, "camera": camera, "zone": zone,
                "provider": "openpatrol-opencv-motion-v1",
                "attributes": {"motion_score": round(score, 4), "threshold": threshold},
            })
            post_event(api_url, token, event); last_event = now


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze an RTSP stream for sudden motion or normalize model-event NDJSON")
    parser.add_argument("--url", default=os.getenv("OPENPATROL_URL", "http://127.0.0.1:8765"))
    parser.add_argument("--stream", default=os.getenv("OPENPATROL_ANALYTICS_STREAM"))
    parser.add_argument("--camera", default=os.getenv("OPENPATROL_CAMERA_ID", "patrol-camera"))
    parser.add_argument("--zone", default=os.getenv("OPENPATROL_CAMERA_ZONE", "patrol"))
    parser.add_argument("--motion-threshold", type=float, default=float(os.getenv("OPENPATROL_MOTION_THRESHOLD", ".12")))
    parser.add_argument("--cooldown", type=float, default=float(os.getenv("OPENPATROL_MOTION_COOLDOWN", "10")))
    args = parser.parse_args()
    token = os.environ["OPENPATROL_INGEST_TOKEN"]
    if args.stream:
        run_motion_stream(args.stream, api_url=args.url, token=token, camera=args.camera, zone=args.zone, threshold=args.motion_threshold, cooldown_seconds=args.cooldown)
        return
    for line in sys.stdin:
        if not line.strip():
            continue
        event = normalize_model_event(json.loads(line))
        post_event(args.url, token, event)
        print(json.dumps({"status": "accepted", "id": event["id"]}), flush=True)

if __name__ == "__main__":
    main()
