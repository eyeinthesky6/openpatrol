# Setup guide

## 1. Run the local simulation

Install Python 3.11 or newer, clone the repository and run:

```bash
python3 -m openpatrol.server
```

Open `http://127.0.0.1:8765`. The default loopback deployment needs no credentials. Mission Control clearly labels its camera as synthetic and its rear camera as offline.

## 2. Run a secured LAN pilot

Generate three different long random secrets for operator mutations, detector ingestion and receipt signing. Provide them through a root-readable environment file rather than shell history:

```text
OPENPATROL_HOST=0.0.0.0
OPENPATROL_OPERATOR_TOKEN=<operator secret>
OPENPATROL_INGEST_TOKEN=<detector secret>
OPENPATROL_SIGNING_KEY=<device signing secret>
OPENPATROL_DATA=/var/lib/openpatrol
```

Place OpenPatrol behind a TLS reverse proxy on a trusted VLAN or VPN. Do not expose port 8765, ROS 2, MQTT, Frigate or go2rtc directly to the internet. Enter the operator token in Settings; it stays in browser session storage and is not written into frontend files.

## 3. Validate before connecting motors

Run `./scripts/check.sh` and the eight-hour software exercise from `docs/simulation-exercise.md`. Then follow `docs/safety-validation.md` with wheels lifted, an exclusion zone and a physical E-stop. Software success does not waive physical validation.

## 4. Attach Frigate

Install `pip install 'openpatrol[mqtt]'`, copy the examples under `deploy/frigate`, replace the RTSP placeholder, pin container versions and configure the detector secret. Confirm that Diagnostics shows the expected adapter state and that received events contain the intended camera, timestamp and media reference.

## 5. Attach ROS 2

Copy `ros2/openpatrol_adapter` into a ROS 2 Jazzy workspace and build with `colcon build --packages-select openpatrol_adapter`. Validate `/hardware/estop`, `/battery_state`, `/cmd_vel_safe` and the 250 ms motor-controller watchdog before allowing floor motion.

## 6. Operate

Use Overview for live state and safety commands, Incidents for evidence review, Diagnostics for degraded components and Settings for retention/speed policy. Return to dock and emergency stop require confirmation. Review operational alerts at shift start and handover.
