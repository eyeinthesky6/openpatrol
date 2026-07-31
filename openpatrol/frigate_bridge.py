"""Optional Frigate MQTT adapter. Install with: pip install 'openpatrol[mqtt]'."""
from __future__ import annotations
import argparse, json, os, urllib.request
from typing import Any

def normalize_frigate_event(message: dict[str, Any], base_url: str = "") -> dict[str, Any] | None:
    after = message.get("after") or {}
    if message.get("type") not in {"new", "update", "end"} or not after.get("id") or not after.get("label"): return None
    score=float(after.get("top_score") or after.get("score") or 0); label=str(after["label"]); camera=str(after.get("camera","unknown"))
    clip=f"{base_url.rstrip('/')}/api/events/{after['id']}/clip.mp4" if base_url else None
    return {"id":f"frigate-{after['id']}","event_type":label,"title":f"{label.replace('_',' ').title()} at {camera}","severity":"high" if label=="person" and score>=.8 else "medium","confidence":max(0.0,min(score,1.0)),"source":f"frigate/{camera}","media_reference":clip}

def post_detection(api_url: str, token: str, detection: dict[str, Any]) -> None:
    request=urllib.request.Request(api_url.rstrip("/")+"/api/v1/detections",data=json.dumps(detection).encode(),headers={"Content-Type":"application/json","Authorization":f"Bearer {token}"},method="POST")
    with urllib.request.urlopen(request,timeout=10) as response:
        if response.status!=201: raise RuntimeError(f"OpenPatrol returned {response.status}")

def main() -> None:
    parser=argparse.ArgumentParser(); parser.add_argument("--mqtt-host",default=os.getenv("FRIGATE_MQTT_HOST","127.0.0.1")); parser.add_argument("--mqtt-port",type=int,default=int(os.getenv("FRIGATE_MQTT_PORT","1883"))); args=parser.parse_args()
    try: import paho.mqtt.client as mqtt
    except ImportError as exc: raise SystemExit("Install the mqtt extra: pip install 'openpatrol[mqtt]'") from exc
    api,token,frigate=os.getenv("OPENPATROL_URL","http://127.0.0.1:8765"),os.environ["OPENPATROL_INGEST_TOKEN"],os.getenv("FRIGATE_URL","")
    def on_message(client,userdata,message):
        try:
            detection=normalize_frigate_event(json.loads(message.payload),frigate)
            if detection: post_detection(api,token,detection)
        except Exception as exc: print(f"Frigate event rejected: {exc}",flush=True)
    client=mqtt.Client(mqtt.CallbackAPIVersion.VERSION2); client.on_message=on_message; client.connect(args.mqtt_host,args.mqtt_port); client.subscribe("frigate/events"); client.loop_forever()
if __name__=="__main__": main()
