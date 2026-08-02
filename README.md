# OpenPatrol

OpenPatrol is a mobility-agnostic, local-first patrol and evidence reference system. It ships a working software simulation—not a mock screen—that closes the loop from route execution and detection through tamper-evident evidence, human review, audit history, safety-state controls and observability.

![AI-generated concept render of proposed OpenPatrol hardware family](docs/assets/openpatrol-hardware-family-concept.png)

> **Concept render, not built hardware.** Rover One and TriScout now have complete Rev-A engineering packs, but remain physically unvalidated until fabricated units pass the published safety protocol. AirScout and Sentinel remain proposals.

## Install the lightweight core

The core uses Python 3.11+ and no third-party runtime packages. The simplest isolated install is:

```bash
pipx install git+https://github.com/eyeinthesky6/openpatrol.git
openpatrol
```

Open `http://127.0.0.1:8765`. The wheel includes the dashboard and default warehouse scenario. Run `openpatrol doctor` to inspect optional capabilities and `openpatrol setup` for an interactive explanation before installing heavy components.

From a repository checkout, Docker users can run:

```bash
./scripts/openpatrol up
```

The script creates local secrets, builds the non-root image, waits for the health endpoint and only then prints the dashboard URL.

## Optional components

OpenPatrol does **not** silently install multi-gigabyte robotics packages.

- `openpatrol setup --with vision` explains the Docker/Frigate camera path.
- `openpatrol setup --with ros-gazebo` checks for ROS 2 Jazzy and Gazebo Harmonic.
- `openpatrol setup --with openscad` checks hardware-export capability.
- From a checkout, set `CAMERA_RTSP_URL` in `.env` and run `./scripts/openpatrol vision`.

The Docker image installs the MQTT bridge correctly, and CI boots the exact advertised Compose command plus a clean installed wheel.

## What works

- configurable waypoint patrol with pause, resume, return-to-dock and E-stop simulation states
- synthetic detections and authenticated external detection ingestion
- atomic evidence receipts with immutable capture and append-only review history
- responsive local operator UI, incident filters and review dispositions
- versioned JSON API, health endpoint, Prometheus-compatible metrics and security headers
- provider-neutral vision adapter and pinned optional Frigate/Mosquitto profile
- ROS 2 Jazzy safety adapter, SLAM Toolbox/Nav2 configuration and Gazebo Harmonic warehouse twin
- deterministic virtual hardware, watchdog, odometry, LiDAR and navigation smoke tests
- production-like accelerated eight-hour software exercise
- two cost-controlled hardware engineering packs with CAD, BOM, wiring and compatibility profiles

Run verification with:

```bash
./scripts/check.sh
openpatrol hardware check all
```

Create a reproducible source archive with `./scripts/release.sh`. Build wheels and source distributions with `python -m build`; the `package` GitHub Action also preserves them as artifacts.

## Hardware reference builds

| Platform | Architecture | Target payload | Engineering BOM |
|---|---|---:|---:|
| Rover One Rev A | four-wheel skid steer | 5 kg | about ₹36,900 |
| TriScout Rev A | two-wheel differential + caster | 3 kg | about ₹32,500 |

Both use 12.8 V LiFePO4, common 100 RPM encoder gearmotors, 100 mm rubber wheels, a shared Pi/lidar payload and a normally-closed hardwired drive cut. Export fabrication files with `./scripts/openpatrol export-hardware all`. See `docs/hardware-build-guide.md` and `hardware/`.

![AI-generated concept of Rover One and AirScout inspecting a warehouse](docs/assets/openpatrol-warehouse-concept.png)

The image is an AI-generated operating concept, not a field-test photograph. The checked-in Gazebo model validates the ground-rover software path. A PX4/ArduPilot drone adapter is not implemented.

## Configuration

| Variable | Default | Purpose |
|---|---|---|
| `OPENPATROL_HOST` | `127.0.0.1` | Bind address; container sets `0.0.0.0` |
| `OPENPATROL_PORT` | `8765` | HTTP port |
| `OPENPATROL_DATA` | `./runtime` | Persistent local evidence directory |
| `OPENPATROL_SCENARIO` | bundled warehouse | Simulation scenario |
| `OPENPATROL_TICK_SECONDS` | `0.4` | Simulation tick interval |
| `OPENPATROL_INGEST_TOKEN` | unset | Bearer token enabling detection ingestion |
| `OPENPATROL_OPERATOR_TOKEN` | unset | Bearer token protecting commands and review |
| `OPENPATROL_SIGNING_KEY` | unset | HMAC-SHA256 receipt-origin key |
| `OPENPATROL_RETENTION_DAYS` | `30` | Maximum evidence age |
| `OPENPATROL_MAX_RECORDS` | `5000` | Hard receipt cap |

For LAN use, set both tokens and put HTTP behind an authenticated TLS gateway or VPN. Do not expose OpenPatrol, ROS 2, MQTT, Frigate or go2rtc directly to the internet.

## Safety and project boundaries

The UI E-stop is a product-state demonstration. A physical robot requires a hardwired power interruption, controller-level watchdog, charging interlock and measured stopping envelope independent of Linux, Wi-Fi and the browser. OpenPatrol excludes weapons, pursuit, deliberate contact, face recognition and covert monitoring.

Software is Apache-2.0. Original hardware source is intended for CERN-OHL-P-2.0 distribution. Documentation and concept media must retain their stated licences and provenance.
