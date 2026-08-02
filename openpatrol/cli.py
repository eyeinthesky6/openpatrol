"""Friendly, dependency-light command line for OpenPatrol."""
from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
from importlib import resources
from pathlib import Path
from typing import Any

from .hardware_profile import builtin_profiles, load_profile, validate_profile


def _command_exists(command: str) -> bool:
    return shutil.which(command) is not None


def _ros_package_exists(package: str) -> bool:
    if not _command_exists("ros2"):
        return False
    try:
        return subprocess.run(
            ["ros2", "pkg", "prefix", package],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=5,
            check=False,
        ).returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def _doctor_report() -> dict[str, Any]:
    data_root = Path(os.getenv("OPENPATROL_DATA", Path.cwd() / "runtime"))
    try:
        free_gb = round(
            shutil.disk_usage(data_root.parent if data_root.parent.exists() else Path.cwd()).free / 1e9,
            1,
        )
    except OSError:
        free_gb = None
    docker = _command_exists("docker")
    compose = False
    if docker:
        try:
            compose = subprocess.run(
                ["docker", "compose", "version"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=5,
                check=False,
            ).returncode == 0
        except (OSError, subprocess.TimeoutExpired):
            compose = False
    ros_ready = _command_exists("ros2")
    return {
        "core": {
            "ready": sys.version_info >= (3, 11),
            "python": platform.python_version(),
            "platform": platform.platform(),
            "free_disk_gb": free_gb,
            "bundled_dashboard": resources.files("static").joinpath("index.html").is_file(),
            "bundled_scenario": resources.files("scenarios").joinpath("warehouse.json").is_file(),
        },
        "optional": {
            "vision": {
                "ready": docker and compose,
                "requires": "Docker Compose v2, RTSP camera and roughly 4 GB free disk",
            },
            "ros_gazebo": {
                "ready": ros_ready and (_command_exists("gz") or _command_exists("ign")),
                "requires": "Ubuntu 24.04, ROS 2 Jazzy, Gazebo Harmonic and roughly 15 GB free disk",
            },
            "mavros_air": {
                "ready": ros_ready and _ros_package_exists("mavros"),
                "requires": "ROS 2 Jazzy, MAVROS and a separately configured ArduPilot/PX4 flight controller",
            },
            "openscad": {
                "ready": _command_exists("openscad"),
                "requires": "OpenSCAD 2021.01 or newer to export the hardware source",
            },
        },
    }


def _print_doctor(report: dict[str, Any]) -> None:
    core = report["core"]
    print(f"Core: {'READY' if core['ready'] else 'BLOCKED'} · Python {core['python']}")
    print(f"Dashboard assets: {'yes' if core['bundled_dashboard'] else 'missing'}")
    print(f"Default scenario: {'yes' if core['bundled_scenario'] else 'missing'}")
    for name, item in report["optional"].items():
        print(f"{name}: {'READY' if item['ready'] else 'optional/not installed'}")
        if not item["ready"]:
            print(f"  {item['requires']}")


def _setup(args: argparse.Namespace) -> int:
    report = _doctor_report()
    _print_doctor(report)
    selected = set(args.with_component or [])
    if not args.non_interactive and sys.stdin.isatty():
        print("\nThe core demo is already lightweight. Heavy components are optional.")
        for component, prompt in (
            ("vision", "Prepare camera detection/recording with Docker + Frigate?"),
            ("ros-gazebo", "Prepare ROS 2 Jazzy + Gazebo simulation?"),
            ("mavros-air", "Prepare the AirScout MAVROS/MAVLink boundary?"),
            ("openscad", "Prepare hardware CAD export with OpenSCAD?"),
        ):
            answer = input(f"{prompt} [y/N] ").strip().lower()
            if answer in {"y", "yes"}:
                selected.add(component)
    if not selected:
        print("\nNothing heavy selected. Run `openpatrol` to start the bundled demo.")
        return 0

    aliases = {"ros-gazebo": "ros_gazebo", "mavros-air": "mavros_air"}
    print("\nSelected optional components:")
    for component in sorted(selected):
        key = aliases.get(component, component)
        if key not in report["optional"]:
            print(f"- {component}: unknown option")
            continue
        item = report["optional"][key]
        state = "already available" if item["ready"] else item["requires"]
        print(f"- {component}: {state}")
    print(
        "\nOpenPatrol will not silently install system-level robotics packages. "
        "From a repository checkout, use `./scripts/openpatrol vision` for Frigate "
        "and follow docs/setup-guide.md plus ros2/openpatrol_adapter/README.md for robotics stacks."
    )
    return 0


def _hardware(args: argparse.Namespace) -> int:
    if args.hardware_command == "list":
        for name in sorted(builtin_profiles()):
            print(name)
        return 0
    names = list(args.profile or [])
    if not names or names == ["all"]:
        names = sorted(builtin_profiles())
    reports = [validate_profile(load_profile(name)) for name in names]
    if args.json:
        print(json.dumps(reports if len(reports) > 1 else reports[0], indent=2))
    else:
        for report in reports:
            print(f"{report['profile_id']}: {'PASS' if report['valid'] else 'FAIL'}")
            print(f"  mobility_kind: {report['mobility_kind']}")
            for key, value in report["calculations"].items():
                print(f"  {key}: {value}")
            for warning in report["warnings"]:
                print(f"  warning: {warning}")
            for error in report["errors"]:
                print(f"  error: {error}")
    return 0 if all(report["valid"] for report in reports) else 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="openpatrol",
        description="Run the lightweight OpenPatrol demo and inspect optional robotics components.",
    )
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("demo", help="start the bundled local simulation")
    sub.add_parser("run", help="alias for demo")
    doctor = sub.add_parser("doctor", help="check core and optional prerequisites")
    doctor.add_argument("--json", action="store_true")
    setup = sub.add_parser("setup", help="interactive optional-component advisor")
    setup.add_argument(
        "--with",
        dest="with_component",
        action="append",
        choices=["vision", "ros-gazebo", "mavros-air", "openscad"],
    )
    setup.add_argument("--non-interactive", action="store_true")
    hardware = sub.add_parser("hardware", help="validate software/hardware reference profiles")
    hardware_sub = hardware.add_subparsers(dest="hardware_command", required=True)
    hardware_sub.add_parser("list", help="list bundled engineering profiles")
    check = hardware_sub.add_parser("check", help="validate one or all profiles")
    check.add_argument("profile", nargs="*")
    check.add_argument("--json", action="store_true")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    if args.command in {None, "demo", "run"}:
        from .server import main as server_main

        server_main()
        return
    if args.command == "doctor":
        report = _doctor_report()
        if args.json:
            print(json.dumps(report, indent=2))
        else:
            _print_doctor(report)
        raise SystemExit(0 if report["core"]["ready"] else 2)
    if args.command == "setup":
        raise SystemExit(_setup(args))
    if args.command == "hardware":
        raise SystemExit(_hardware(args))
    parser.error("unknown command")


if __name__ == "__main__":
    main()
