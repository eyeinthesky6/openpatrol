"""Provider-neutral NDJSON adapter for local or hosted vision models."""
from __future__ import annotations
import argparse
import json
import os
import sys
from .video_analytics import normalize_model_event, post_event


def normalize_provider_detection(item: dict) -> dict:
    # Backward-compatible aliases used by earlier adapters/tests.
    if "event_type" not in item and "label" in item:
        item = {**item, "event_type": item["label"]}
    if "camera" not in item and item.get("location"):
        item = {**item, "camera": item["location"]}
    return normalize_model_event(item)


def main() -> None:
    parser = argparse.ArgumentParser(description="Read one vision event JSON object per line and send it to OpenPatrol")
    parser.add_argument("--url", default=os.getenv("OPENPATROL_URL", "http://127.0.0.1:8765"))
    args = parser.parse_args()
    token = os.environ["OPENPATROL_INGEST_TOKEN"]
    for number, line in enumerate(sys.stdin, 1):
        if not line.strip():
            continue
        try:
            event = normalize_provider_detection(json.loads(line))
            post_event(args.url, token, event)
            print(json.dumps({"line": number, "status": "accepted", "id": event["id"]}), flush=True)
        except Exception as exc:
            print(json.dumps({"line": number, "status": "rejected", "error": str(exc)}), file=sys.stderr, flush=True)


if __name__ == "__main__":
    main()
