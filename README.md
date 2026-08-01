# OpenPatrol

OpenPatrol is a mobility-agnostic, local-first patrol and evidence reference system. It ships a working simulation—not a mock screen—that closes the product loop: route execution, detection, tamper-evident evidence, human review, audit history, safety-state controls and observability.

## Quick start

Requires Python 3.11+ and no third-party runtime packages.

```bash
python3 -m openpatrol.server
```

Open <http://127.0.0.1:8765>. For a faster demo: `OPENPATROL_TICK_SECONDS=0.15 python3 -m openpatrol.server`.

Or run the non-root container:

```bash
docker compose up --build
```

## What works

- configurable waypoint patrol with pause, resume, return-to-dock and E-stop simulation states
- synthetic scenario detections and authenticated external detection ingestion
- atomic evidence receipts whose immutable capture and append-only review chain can be independently verified
- responsive local operator UI, incident filters and review dispositions
- versioned JSON API, health endpoint, Prometheus-compatible metrics and security headers
- ROS 2 mobility contract and Frigate integration recipe at documented adapter boundaries
- installable ROS 2 Jazzy safety-adapter package and optional Frigate MQTT bridge
- parametric reference-base/payload CAD, India-oriented BOM, stop-chain wiring and physical validation protocol
- unit, state-machine, evidence-tamper and live HTTP integration tests
- deterministic virtual hardware, ROS 2 mock controllers and a Gazebo Harmonic warehouse digital twin

Run all verification with `./scripts/check.sh` or `python3 -m unittest discover -s tests -v`.

Create a reproducible source archive with `./scripts/release.sh`.

Run a production-like accelerated eight-hour shift with `python3 -m openpatrol.exercise`. It injects detector events, E-stops, localization faults, charge cycles and a restart, then writes a machine-readable acceptance report. See [`docs/simulation-exercise.md`](docs/simulation-exercise.md).

Run the dependency-free hardware acceptance suite with `python3 -m openpatrol.hardware_harness`. For ROS 2 mock hardware and Gazebo instructions, see [`docs/virtual-hardware.md`](docs/virtual-hardware.md).

GitHub Actions also builds ROS 2 Jazzy and runs the Gazebo warehouse headlessly. It proves LiDAR delivery, odometry motion through the safety adapter and watchdog stopping, then preserves the simulator logs as an artifact.

## Configuration

| Variable | Default | Purpose |
|---|---|---|
| `OPENPATROL_HOST` | `127.0.0.1` | Bind address; container sets `0.0.0.0` |
| `OPENPATROL_PORT` | `8765` | HTTP port |
| `OPENPATROL_DATA` | `./runtime` | Persistent local evidence directory |
| `OPENPATROL_SCENARIO` | `./scenarios/warehouse.json` | Simulation scenario |
| `OPENPATROL_TICK_SECONDS` | `0.4` | Simulation tick interval |
| `OPENPATROL_INGEST_TOKEN` | unset | Bearer token enabling `/api/v1/detections` |
| `OPENPATROL_OPERATOR_TOKEN` | unset | Bearer token protecting commands and incident review |
| `OPENPATROL_SIGNING_KEY` | unset | Secret used to authenticate receipt origin with HMAC-SHA256 |
| `OPENPATROL_RETENTION_DAYS` | `30` | Maximum local evidence age |
| `OPENPATROL_MAX_RECORDS` | `5000` | Hard cap on local evidence receipts |

The external ingestion body requires `id`, `event_type`, `title`, `severity` and `confidence`. See [`docs/integrations.md`](docs/integrations.md) and [`docs/api.md`](docs/api.md).

For LAN deployment, set both tokens and place the service behind an authenticated TLS gateway or VPN. The bundled browser UI is intended for loopback/local use; a production gateway should inject or broker operator authorization rather than embedding secrets in frontend code.

Repository map: `hardware/` contains editable mechanical source and BOM; `ros2/` contains the ROS 2 Jazzy adapter and simulation package; `deploy/frigate/` contains an integration profile; `schemas/` contains portable JSON contracts; `docs/product-requirements.md` tracks every product-note claim.

For day-to-day use see [`docs/operator-guide.md`](docs/operator-guide.md). Physical builders must execute [`docs/safety-validation.md`](docs/safety-validation.md) and publish measured results; an unchecked box is not a passed safety test.

New users should start with [`docs/setup-guide.md`](docs/setup-guide.md). The dashboard and operational safeguards are informed by recurring real-world failures documented in [`docs/competitive-lessons.md`](docs/competitive-lessons.md).

## Project boundaries

The included E-stop is a product-state demonstration. A physical robot requires a hardwired power interruption and motor-controller watchdog independent of Linux, Wi-Fi and this UI. OpenPatrol excludes weapons, pursuit, deliberate contact, face recognition and covert monitoring; deploy only with authorization, notices, retention rules and applicable privacy law.

Software is Apache-2.0. Original hardware designs, when added, should use CERN-OHL-P-2.0; documentation may use CC BY 4.0.
