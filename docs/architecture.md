# Architecture boundaries

OpenPatrol keeps product logic separate from mobility, navigation and video providers.

## Mobility adapter

A physical adapter must provide:

- pose and velocity feedback;
- `drive`, `stop` and hardware E-stop state;
- battery percentage, voltage, temperature and charging state;
- bumper/obstacle/fault status;
- watchdog behaviour that stops the platform when commands disappear;
- declared maximum speed, payload and braking distance.

The first ROS 2 adapter will map these concepts to standard `geometry_msgs/Twist`, odometry, battery and diagnostics topics. Linorobot2/Nav2 are upstream dependencies, not vendored forks.

## Perception adapter

The simulation emits synthetic detections. A physical deployment may accept events from Frigate over MQTT or a ROS 2 perception node. Every adapter produces a normalized detection with type, confidence, source and optional media reference.

## Evidence core

Evidence receipts remain valid without a cloud service. The current SHA-256 receipt demonstrates integrity plumbing; a production system should add device signing keys, secure time, immutable media storage and key rotation.

## Safety boundary

Linux and the web UI are not safety controllers. Drive power interruption, emergency stop and the motor watchdog belong below the application computer.
