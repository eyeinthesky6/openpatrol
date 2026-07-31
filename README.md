# OpenPatrol

OpenPatrol is a mobility-agnostic, local-first patrol and evidence system. This repository starts with a dependency-free simulation that proves the complete product loop:

1. a rover follows a route;
2. a configured scene produces an incident;
3. the system captures a tamper-evident evidence receipt;
4. a human reviews and disposes the incident.

The simulation is intentionally independent of ROS so product logic can be tested anywhere. ROS 2/Nav2, Frigate and physical chassis adapters attach at the boundaries described in `docs/architecture.md`.

## Run

```bash
python3 -m openpatrol.server
```

Open <http://127.0.0.1:8765>.

To run faster for a demo:

```bash
OPENPATROL_TICK_SECONDS=0.15 python3 -m openpatrol.server
```

## Test

```bash
python3 -m unittest discover -s tests -v
```

## Current scope

- waypoint patrol and route progress
- synthetic obstacle/person event generation
- local evidence receipts with SHA-256 integrity hash
- incident queue and human dispositions
- health, battery and local-only operator dashboard
- JSON scenario format and hardware-adapter contract

## Safety

This reference project is for sensing and inspection. It explicitly excludes weapons, pursuit, deliberate physical contact and biometric identification.

Software: Apache-2.0. Original hardware designs, when added, will use CERN-OHL-P-2.0. Documentation: CC BY 4.0.
