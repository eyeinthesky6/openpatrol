"""Friendly dependency-light command line for OpenPatrol."""
from __future__ import annotations
import argparse, json, os, platform, shutil, subprocess, sys
from importlib import resources
from pathlib import Path
from typing import Any
from .hardware_profile import builtin_profiles, load_profile, validate_profile


def _exists(command: str) -> bool: return shutil.which(command) is not None

def _ros_package(package: str) -> bool:
    if not _exists("ros2"): return False
    try: return subprocess.run(["ros2","pkg","prefix",package],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=5).returncode==0
    except (OSError,subprocess.TimeoutExpired): return False

def _doctor_report() -> dict[str, Any]:
    data_root=Path(os.getenv("OPENPATROL_DATA",Path.cwd()/"runtime"))
    try: free_gb=round(shutil.disk_usage(data_root.parent if data_root.parent.exists() else Path.cwd()).free/1e9,1)
    except OSError: free_gb=None
    docker=_exists("docker");compose=False
    if docker:
        try: compose=subprocess.run(["docker","compose","version"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=5).returncode==0
        except (OSError,subprocess.TimeoutExpired): pass
    ros=_exists("ros2")
    return {
      "core":{"ready":sys.version_info>=(3,11),"python":platform.python_version(),"platform":platform.platform(),"free_disk_gb":free_gb,"bundled_dashboard":resources.files("static").joinpath("index.html").is_file(),"bundled_scenario":resources.files("scenarios").joinpath("warehouse.json").is_file()},
      "optional":{
        "vision":{"ready":docker and compose,"requires":"Docker Compose v2, RTSP/ONVIF camera and roughly 4 GB free disk"},
        "security":{"ready":docker and compose,"requires":"Docker Compose v2 for MQTT bridge, or use HTTP/NDJSON adapters directly"},
        "analytics":{"ready":_exists("ffmpeg"),"requires":"A validated vision model/provider; OpenCV/NumPy are optional helpers"},
        "device_audio":{"ready":any(_exists(x) for x in ("espeak-ng","spd-say","say","ffplay","mpv","aplay")),"requires":"One local TTS/audio player on each speaker endpoint"},
        "sensor_hub":{"ready":_exists("openpatrol-sensor-hub") or _exists("python3"),"requires":"pyserial and the Rev-A sensor hub or another event adapter"},
        "ros_gazebo":{"ready":ros and (_exists("gz") or _exists("ign")),"requires":"Ubuntu 24.04, ROS 2 Jazzy, Gazebo Harmonic and roughly 15 GB free disk"},
        "mavros_air":{"ready":ros and _ros_package("mavros"),"requires":"ROS 2 Jazzy, MAVROS and separately configured ArduPilot/PX4"},
        "openscad":{"ready":_exists("openscad"),"requires":"OpenSCAD 2021.01+"},
      }}

def _print(report):
    c=report["core"];print(f"Core: {'READY' if c['ready'] else 'BLOCKED'} · Python {c['python']}");print(f"Dashboard assets: {'yes' if c['bundled_dashboard'] else 'missing'}");print(f"Default scenario: {'yes' if c['bundled_scenario'] else 'missing'}")
    for name,item in report["optional"].items():
        print(f"{name}: {'READY' if item['ready'] else 'optional/not installed'}")
        if not item["ready"]: print(f"  {item['requires']}")

def _setup(args):
    report=_doctor_report();_print(report);selected=set(args.with_component or [])
    if not args.non_interactive and sys.stdin.isatty():
        print("\nThe core command centre is lightweight. Heavy integrations are optional.")
        prompts=[("vision","Prepare camera recording/detection with Docker + Frigate?"),("security","Prepare the MQTT security-system bridge?"),("analytics","Prepare local OpenCV analytics helpers?"),("sensor-hub","Prepare the fixed sensor/audio hub bridge?"),("ros-gazebo","Prepare ROS 2 + Gazebo?"),("mavros-air","Prepare AirScout MAVROS?"),("openscad","Prepare CAD export?")]
        for component,prompt in prompts:
            if input(f"{prompt} [y/N] ").strip().lower() in {"y","yes"}:selected.add(component)
    if not selected: print("\nNothing heavy selected. Run `openpatrol` for the bundled command-centre demo.");return 0
    aliases={"ros-gazebo":"ros_gazebo","mavros-air":"mavros_air","sensor-hub":"sensor_hub","device-audio":"device_audio"}
    print("\nSelected optional components:")
    for component in sorted(selected):
        key=aliases.get(component,component);item=report["optional"].get(key)
        print(f"- {component}: {('already available' if item and item['ready'] else item['requires'] if item else 'unknown option')}")
    print("\nSystem packages are never installed silently. From a checkout use `./scripts/openpatrol vision`, `security`, or `full`, and review docs/command-centre.md.")
    return 0

def _hardware(args):
    if args.hardware_command=="list":
        print("\n".join(sorted(builtin_profiles())));return 0
    names=list(args.profile or []);names=sorted(builtin_profiles()) if not names or names==["all"] else names
    reports=[validate_profile(load_profile(name)) for name in names]
    if args.json: print(json.dumps(reports if len(reports)>1 else reports[0],indent=2))
    else:
        for r in reports:
            print(f"{r['profile_id']}: {'PASS' if r['valid'] else 'FAIL'}")
            for k,v in r["calculations"].items():print(f"  {k}: {v}")
            for w in r["warnings"]:print(f"  warning: {w}")
            for e in r["errors"]:print(f"  error: {e}")
    return 0 if all(r["valid"] for r in reports) else 2

def build_parser():
    p=argparse.ArgumentParser(prog="openpatrol",description="Run OpenPatrol command centre and inspect optional integrations.");s=p.add_subparsers(dest="command")
    s.add_parser("demo");s.add_parser("run");d=s.add_parser("doctor");d.add_argument("--json",action="store_true")
    setup=s.add_parser("setup");setup.add_argument("--with",dest="with_component",action="append",choices=["vision","security","analytics","device-audio","sensor-hub","ros-gazebo","mavros-air","openscad"]);setup.add_argument("--non-interactive",action="store_true")
    h=s.add_parser("hardware");hs=h.add_subparsers(dest="hardware_command",required=True);hs.add_parser("list");c=hs.add_parser("check");c.add_argument("profile",nargs="*");c.add_argument("--json",action="store_true")
    return p

def main():
    p=build_parser();a=p.parse_args()
    if a.command in {None,"demo","run"}:
        from .server import main as run;run();return
    if a.command=="doctor":
        r=_doctor_report();print(json.dumps(r,indent=2)) if a.json else _print(r);raise SystemExit(0 if r["core"]["ready"] else 2)
    if a.command=="setup":raise SystemExit(_setup(a))
    if a.command=="hardware":raise SystemExit(_hardware(a))
    p.error("unknown command")
if __name__=="__main__":main()
