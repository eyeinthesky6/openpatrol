# OpenPatrol

OpenPatrol is an open, local-first patrol and security command centre. It combines mobile robots, drones, existing cameras, NVR/VMS events, alarm/access systems and fixed sensors into one human-reviewed incident, evidence and alert workflow.

![OpenPatrol ready-to-test prototype family design](docs/assets/openpatrol-hardware-family-concept.svg)

> **Ready-to-test prototype source, not field-certified hardware.** Rover One, TriScout, AirScout, Sentinel and the fixed Security Sensor Hub have inspectable engineering sources. Physical validation and site-specific AI acceptance remain required.

## Install the lightweight core

Python 3.11+; no third-party runtime dependency for the command-centre demo:

```bash
pipx install git+https://github.com/eyeinthesky6/openpatrol.git
openpatrol
```

Open `http://127.0.0.1:8765`. The wheel includes the dashboard and default warehouse scenario. `openpatrol doctor` explains optional integrations without silently installing multi-gigabyte packages.

From a checkout:

```bash
./scripts/openpatrol up        # lightweight command centre
./scripts/openpatrol vision    # camera recording/detection via Frigate/go2rtc
./scripts/openpatrol security  # MQTT alarm/access/sensor bridge
./scripts/openpatrol full      # camera + security bridge
```

## What works

### Open command centre

- camera wall and device inventory for OpenPatrol and third-party systems
- RTSP/ONVIF-compatible camera path through pinned Frigate/go2rtc
- authenticated generic security-event API plus Frigate, MQTT, NDJSON and sensor-hub adapters
- conservative multi-sensor candidates for falls, intrusion/break-in, drowning/distress, fights, sudden movement, fire/smoke, panic, tamper, loitering and restricted-zone entry
- weak observations retained without automatically becoming alarms
- browser audio/notifications, local strobe/siren routing, text announcements and recorded operator talkback
- allow-listed endpoint agent; no remote shell execution
- tamper-evident evidence receipts, human review, subject labels and audit history

### Patrol and hardware

- waypoint patrol with pause, resume, dock return and E-stop simulation states
- ROS 2 Jazzy safety adapter, SLAM Toolbox/Nav2 configuration and Gazebo Harmonic warehouse twin
- physical serial boundary for Rover One, TriScout and Sentinel drive controllers
- independent Sentinel telescoping mast protocol, bridge and RP2040 firmware
- bounded AirScout velocity intent behind ArduPilot/PX4-owned flight control/failsafes
- four coordinated robot/drone engineering packs plus the fixed Security Sensor Hub Rev A

Run checks:

```bash
./scripts/check.sh
openpatrol hardware check all
./scripts/openpatrol export-hardware all
```

## Hardware reference builds

| Platform | Prototype role | Engineering BOM |
|---|---|---:|
| Rover One Rev A | robust four-wheel ground patrol | ₹36,891 |
| TriScout Rev A | lowest-cost smooth-floor rover | ₹32,499 |
| AirScout Rev A | supervised aerial inspection | ₹44,980 |
| Sentinel Rev A | elevated sensing/telepresence, 980–1,500 mm head | ₹66,890 |
| Security Sensor Hub Rev A | 8 wired zones plus speaker/strobe/siren | ₹8,700 |

All figures are prototype sourcing estimates excluding labour, tax, validation and connected third-party equipment.

## Open integration contracts

- cameras: RTSP/go2rtc/Frigate, or any provider that posts the security-event schema
- NVR/VMS/AI: `openpatrol-vision-adapter`
- alarm/access/Home Assistant: `openpatrol-security-bridge` over NDJSON or MQTT
- wired relays: `openpatrol-sensor-hub`
- robots/speakers/strobes/sirens: `openpatrol-device-agent`

See `docs/command-centre.md`, `docs/ai-incident-detection.md`, `docs/security-sensor-hub.md`, `docs/hardware-platforms.md` and `docs/hardware-build-guide.md`.

## Accuracy and safety boundary

OpenPatrol creates incident candidates. It does not guarantee detection of every incident, and camera AI must be calibrated and measured on each site. Fire, pool, medical, access-control and other certified systems remain independently operational. Face recognition, covert monitoring, weapons, pursuit and autonomous physical intervention are excluded.

Physical ground robots require hardwired drive cuts, controller watchdogs, measured stopping envelopes and supervised acceptance. AirScout requires autopilot-owned arming, geofence and command/battery failsafes plus applicable aviation/site review. Browser controls never replace physical safety circuits.

For LAN use, set separate operator, ingest and device tokens and put HTTP behind an authenticated TLS gateway or VPN. Do not expose OpenPatrol, MQTT, Frigate/go2rtc, ROS 2 or MAVLink directly to the internet.

Software is Apache-2.0. Original hardware source is intended for CERN-OHL-P-2.0 distribution.
