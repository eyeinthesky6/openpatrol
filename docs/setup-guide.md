# Setup guide

## 1. One-command simulation

Install Docker with Compose v2, clone the repository and run:

```bash
./scripts/openpatrol up
```

The command creates private detector/signing secrets in `.env`, builds the non-root container and starts the simulator. Open `http://127.0.0.1:8765`. Use `./scripts/openpatrol check`, `logs` and `down` for verification, logs and shutdown. Developers may instead run `python3 -m openpatrol.server` with Python 3.11+.

## 2. Camera, recording and object detection

Edit `CAMERA_RTSP_URL` in `.env`, then run `./scripts/openpatrol vision`. This starts pinned Frigate, Mosquitto, the authenticated event bridge and OpenPatrol. Frigate tracks common person, vehicle and animal classes. Confirm the stream, events, snapshots and camera health before relying on alerts. Camera credentials and RTSP discovery cannot be guessed safely.

Do not expose OpenPatrol, ROS 2, MQTT, Frigate or go2rtc directly to the internet. For a LAN pilot, set a separate `OPENPATROL_OPERATOR_TOKEN` in `.env` and place HTTP access behind an authenticated TLS gateway or VPN.

## 3. Connect another vision model

Any model may emit one JSON object per line:

```json
{"id":"frame-42-person-1","label":"person","confidence":0.91,"provider":"yolo-local","location":"front","media_reference":"https://controlled-media/event.jpg"}
```

Pipe it into `openpatrol-vision-adapter`. The adapter normalizes and authenticates events. Provider output remains immutable; an operator can attach “Known courier” in the incident dialog. Labels are separately audited annotations, not facial-recognition claims.

## 4. Mapping and autonomous navigation

Copy `ros2/` into a ROS 2 Jazzy workspace and build both packages with `colcon`. Start with `mock_hardware.launch.py`, then `gazebo.launch.py`. Start `navigation.launch.py` alongside the robot to enable SLAM Toolbox and Nav2. It consumes the same `/scan`, `/odom` and TF contract used by Gazebo and physical hardware. Drive under supervision to create the first map, save it, then define patrol waypoints. Chassis footprint, acceleration, braking and sensor noise require calibration.

## 5. Physical docking

`opennav_docking` provides navigation-level dock and undock actions. Each dock needs a platform plug-in for final alignment, charging feedback and retry behaviour. Contacts, fusing, thermal monitoring and electrical interlocks are hardware—not YAML. The simulator exercises low-battery return, docking and gradual charging before hardware arrives.

## 6. Safety validation

Run `./scripts/openpatrol check`, the virtual hardware suite, the hosted Gazebo smoke test and the operational exercise. Before floor motion, validate `/hardware/estop`, `/battery_state`, `/cmd_vel_safe`, the motor-controller watchdog, a hardwired power interruption and `docs/safety-validation.md` with wheels lifted and an exclusion zone.

## 7. Operations

Use Overview for state and safety commands, Incidents for evidence review and labels, Diagnostics for provider/camera/navigation degradation, and Settings for retention and speed policy. An unchecked physical validation item is not a passed test.
