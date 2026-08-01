"""Provider-neutral NDJSON adapter for any local or hosted vision model."""
from __future__ import annotations
import argparse, json, os, sys
from .frigate_bridge import post_detection


def normalize_provider_detection(item: dict) -> dict:
    required = {"id", "label", "confidence"}
    missing = required - item.keys()
    if missing:
        raise ValueError(f"missing fields: {', '.join(sorted(missing))}")
    label = str(item["label"]).strip()
    if not label or len(label) > 80: raise ValueError("label must contain 1 to 80 characters")
    confidence = float(item["confidence"])
    if not 0 <= confidence <= 1: raise ValueError("confidence must be between 0 and 1")
    provider = str(item.get("provider", "generic-vision"))[:120]
    location = str(item.get("location", "camera"))[:120]
    result={"id": str(item["id"])[:120], "event_type": label, "title": str(item.get("title") or f"{label.replace('_', ' ').title()} at {location}")[:200], "severity": str(item.get("severity", "medium")), "confidence": confidence, "source": f"vision/{provider}/{location}"[:200], "provider": provider}
    if item.get("media_reference"): result["media_reference"]=item["media_reference"]
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Read one vision detection JSON object per line and send it to OpenPatrol")
    parser.add_argument("--url", default=os.getenv("OPENPATROL_URL", "http://127.0.0.1:8765")); args = parser.parse_args()
    token = os.environ["OPENPATROL_INGEST_TOKEN"]
    for number, line in enumerate(sys.stdin, 1):
        if not line.strip(): continue
        try:
            detection = normalize_provider_detection(json.loads(line)); post_detection(args.url, token, detection)
            print(json.dumps({"line": number, "status": "accepted", "id": detection["id"]}), flush=True)
        except Exception as exc:
            print(json.dumps({"line": number, "status": "rejected", "error": str(exc)}), file=sys.stderr, flush=True)
