# Integration contracts

## Frigate or another detector

Set a long random `OPENPATROL_INGEST_TOKEN`, then normalize a detector event into:

```json
{"id":"frigate-123","event_type":"person","title":"Person near loading door","severity":"high","confidence":0.92,"source":"frigate/front_gate"}
```

POST it to `/api/v1/detections` with `Content-Type: application/json` and `Authorization: Bearer …`. OpenPatrol intentionally does not retain raw video in this starter; an adapter may place a controlled media reference in a future signed-media extension.

The runnable optional bridge is `openpatrol.frigate_bridge`. Install `pip install 'openpatrol[mqtt]'`, configure the environment documented in `deploy/frigate/compose.example.yaml`, and subscribe it to `frigate/events`. Clip URLs are references—not evidence of media integrity—unless `media_sha256` is supplied by a trusted adapter.

## ROS 2 / Nav2 mobility

An adapter should consume `geometry_msgs/Twist` for drive commands and publish `nav_msgs/Odometry`, `sensor_msgs/BatteryState` and `diagnostic_msgs/DiagnosticArray`. Nav2 supplies route execution. The adapter must stop when command freshness exceeds its watchdog deadline and report a physical E-stop as authoritative. The application must never clear a physical E-stop.

`ros2/openpatrol_adapter` supplies a Jazzy `ament_python` reference node with velocity clamps, E-stop input, 250 ms freshness watchdog and mobility-health output. It complements—not replaces—the motor-controller watchdog.

## Hardware acceptance gate

Before enabling motors: validate a separate hardwired E-stop, command timeout at the motor controller, speed/acceleration limits, bumper or obstacle stop, thermal/current limits, charger interlock and a marked exclusion zone. Record braking distance at maximum configured payload.
