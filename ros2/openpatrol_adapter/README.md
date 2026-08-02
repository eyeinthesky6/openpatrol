# ROS 2 adapter

Build inside ROS 2 Jazzy with:

```bash
colcon build --packages-select openpatrol_adapter
source install/setup.bash
```

## Simulation or generic mobility boundary

`safety_adapter` consumes `/cmd_vel` and `/hardware/estop`, clamps commands, applies a Linux-side freshness watchdog and publishes `/cmd_vel_safe`. The motor controller must independently implement the timeout; this node is not the final safety controller.

## Rev-A physical hardware

Flash `hardware/common/firmware/safety_controller.ino`, calibrate the pin map and encoder counts, then connect the controller over USB and run:

```bash
ros2 launch openpatrol_adapter physical_rover.launch.py serial_port:=/dev/ttyACM0
```

The launch starts the command safety adapter, CRC-checked serial motor bridge and odometry TF bridge. Rover One defaults are included. For TriScout use:

```bash
ros2 launch openpatrol_adapter physical_rover.launch.py \
  serial_port:=/dev/ttyACM0 wheel_track_m:=0.30 max_wheel_speed_mps:=0.42
```

Inputs: `/cmd_vel`. Physical-controller outputs: `/odom`, `/battery_state`, `/hardware/estop`, `/openpatrol/controller_health`. Drive commands cross `/cmd_vel_safe` only. See `hardware/common/serial-protocol.md`.
