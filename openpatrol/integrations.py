"""Stable provider-neutral integration registry for OpenPatrol."""
from __future__ import annotations
import os


def registry(mode: str = "simulation") -> dict:
    frigate = os.getenv("FRIGATE_URL", "").strip()
    camera_ui = os.getenv("OPENPATROL_CAMERA_UI_URL", "").strip()
    return {
        "contract_version": "openpatrol.integrations/v2",
        "capabilities": {
            "mobility": {
                "provider": "gazebo" if mode == "simulation" else "ros2",
                "status": "ready",
                "contract": ["/cmd_vel_safe", "/odom", "/scan"],
            },
            "navigation": {
                "provider": "nav2", "status": "available",
                "contract": ["NavigateToPose", "FollowWaypoints", "map", "tf"],
            },
            "mapping": {
                "provider": "slam_toolbox", "status": "available",
                "contract": ["/scan", "/map"],
            },
            "docking": {
                "provider": "opennav_docking",
                "status": "simulated" if mode == "simulation" else "adapter_required",
                "contract": ["dock", "undock", "charging"],
            },
            "video": {
                "provider": "frigate/go2rtc" if frigate else "provider-neutral",
                "status": "configured" if frigate else "adapter_ready",
                "operator_url": camera_ui or None,
                "ingest": ["RTSP", "ONVIF discovery", "Frigate MQTT", "generic model NDJSON"],
                "contract": ["POST /api/v1/security-events", "GET /api/v1/cameras"],
            },
            "security_systems": {
                "provider": "open-adapters", "status": "ready",
                "ingest": ["HTTP JSON", "NDJSON", "MQTT", "Home Assistant", "alarm relay", "access control"],
                "contract": ["POST /api/v1/security-events"],
            },
            "incident_fusion": {
                "provider": "openpatrol-fusion-v1", "status": "ready-to-calibrate",
                "supported_candidates": [
                    "fall", "intrusion", "break_in", "drowning_distress", "fight",
                    "sudden_motion", "fire", "smoke", "panic", "tamper", "restricted_zone_entry",
                ],
                "contract": ["GET /api/v1/observations", "GET /api/v1/alerts"],
            },
            "device_outputs": {
                "provider": "openpatrol-device-agent", "status": "ready",
                "actions": ["notify", "speak", "play_audio", "strobe", "siren", "stop_output"],
                "contract": [
                    "POST /api/v1/devices/register", "GET /api/v1/devices/{id}/commands",
                    "POST /api/v1/announce", "POST /api/v1/talkback",
                ],
            },
            "identity": {
                "provider": "operator_labels", "status": "ready",
                "contract": ["POST /api/v1/incidents/{id}/subjects"],
            },
        },
    }
