"""Stable capability registry: providers can change without changing OpenPatrol APIs."""
from __future__ import annotations
import os


def registry(mode: str = "simulation") -> dict:
    camera_url = os.getenv("FRIGATE_URL", "").strip()
    camera_ui_url = os.getenv("OPENPATROL_CAMERA_UI_URL", "").strip()
    return {
        "contract_version": "openpatrol.integrations/v1",
        "capabilities": {
            "mobility": {"provider": "gazebo" if mode == "simulation" else "ros2", "status": "ready", "contract": ["/cmd_vel_safe", "/odom", "/scan"]},
            "navigation": {"provider": "nav2", "status": "available", "contract": ["NavigateToPose", "FollowWaypoints", "map", "tf"]},
            "mapping": {"provider": "slam_toolbox", "status": "available", "contract": ["/scan", "/map"]},
            "docking": {"provider": "opennav_docking", "status": "simulated" if mode == "simulation" else "adapter_required", "contract": ["dock", "undock", "charging"]},
            "vision": {"provider": "frigate" if camera_url else "generic", "status": "configured" if camera_url else "adapter_ready", "operator_url": camera_ui_url or None, "contract": ["POST /api/v1/detections"]},
            "identity": {"provider": "operator_labels", "status": "ready", "contract": ["POST /api/v1/incidents/{id}/subjects"]},
        },
    }
