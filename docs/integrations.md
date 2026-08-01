# Integration contracts

## Frigate or another detector

Set a long random `OPENPATROL_INGEST_TOKEN`, then normalize a detector event into:

```json
{"id":"frigate-123","event_type":"person","title":"Person near loading door","severity":"high","confidence":0.92,"source":"frigate/front_gate"}
```

POST it to `/api/v1/detections` with `Content-Type: application/json` and `Authorization: Bearer …`. OpenPatrol intentionally does not retain raw video in this starter; an adapter may place a controlled media reference in a future signed-media extension.

The runnable optional bridge is `openpatrol.frigate_bridge`. The root Compose `vision` profile configures it and subscribes to `frigate/events`; `./scripts/openpatrol vision` is the supported entry point. Clip URLs are references—not evidence of media integrity—unless `media_sha256` is supplied by a trusted adapter.

For other vision systems, use `openpatrol-vision-adapter` or POST the normalized schema directly. Provider namespaces in `provider` and `source` are metadata, never executable plug-in names or paths. Detection is separate from identity: operators attach audited labels through `/api/v1/incidents/{id}/subjects` without altering captured model output.

## ROS 2 / Nav2 mobility

An adapter should consume `geometry_msgs/Twist` for drive commands and publish `nav_msgs/Odometry`, `sensor_msgs/BatteryState` and `diagnostic_msgs/DiagnosticArray`. Nav2 supplies route execution. The adapter must stop when command freshness exceeds its watchdog deadline and report a physical E-stop as authoritative. The application must never clear a physical E-stop.

`ros2/openpatrol_adapter` supplies a Jazzy `ament_python` reference node with velocity clamps, E-stop input, 250 ms freshness watchdog and mobility-health output. It complements—not replaces—the motor-controller watchdog.

`openpatrol_simulation/launch/navigation.launch.py` composes SLAM Toolbox and Nav2 against the Gazebo/physical topic contract. `opennav_docking` owns navigation-level actions; the builder supplies final alignment, charger feedback and electrical interlocks. Simulated return-to-dock validates mission logic, not physical contacts.

## Hardware acceptance gate

Before enabling motors: validate a separate hardwired E-stop, command timeout at the motor controller, speed/acceleration limits, bumper or obstacle stop, thermal/current limits, charger interlock and a marked exclusion zone. Record braking distance at maximum configured payload.
