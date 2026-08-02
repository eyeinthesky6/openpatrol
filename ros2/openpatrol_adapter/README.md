# ROS 2 adapter

Build inside ROS 2 Jazzy with:

```bash
colcon build --packages-select openpatrol_adapter
source install/setup.bash
```

## Shared safety boundary

`safety_adapter` consumes `/cmd_vel` and `/hardware/estop`, clamps commands, applies a Linux-side freshness watchdog and publishes `/cmd_vel_safe`. Physical controllers and flight-controller failsafes remain authoritative; ROS is never the only stop mechanism.

## Rover One and TriScout

```bash
ros2 launch openpatrol_adapter physical_rover.launch.py serial_port:=/dev/ttyACM0
```

For TriScout add `wheel_track_m:=0.30 max_wheel_speed_mps:=0.42`.

## Sentinel

Flash the common drive controller and the Sentinel mast controller, then run:

```bash
ros2 launch openpatrol_adapter physical_sentinel.launch.py \
  drive_serial_port:=/dev/ttyACM0 mast_serial_port:=/dev/ttyACM1
```

The launch starts the ground safety/drive path plus the independent mast bridge. Mast commands use `/sentinel/mast/target_mm`; state is published on `/sentinel/mast/state`, `/sentinel/mast/joint_state` and `/sentinel/mast/extended`. Hardware hard limits, tilt input and the mast-extended wheel-speed cap remain local to the controllers.

## AirScout

Run MAVROS for the selected ArduPilot/PX4 controller, configure arming/geofence/battery and command-loss failsafes in the flight controller, then run:

```bash
ros2 launch openpatrol_adapter physical_airscout.launch.py
```

`mavros_state_guard` is read-only: it authorizes velocity only when a fresh MAVROS state reports a connected, already-armed GUIDED/OFFBOARD vehicle, an optional `/hardware/estop` is not asserted and a fresh `/air/operator_enable` heartbeat is present. `mavlink_velocity_adapter` maps bounded `/air/cmd_vel_safe` intent to the MAVROS velocity-setpoint topic at 20 Hz. When authorization or command freshness is lost it publishes one immediate zero setpoint, then stops the stream so the flight controller's configured command-loss land/RTL action can engage. Guard state is published on `/air/flight_state`; adapter handoff state is separate on `/air/adapter_state`. Neither node arms, changes flight modes or publishes raw motor commands; a dedicated flight-controller/RC kill path remains mandatory. During supervised bring-up, publish the operator-enable heartbeat from a dedicated control process rather than a one-shot shell command.

For a restrained bench/SITL test only, the heartbeat can be exercised explicitly:

```bash
ros2 topic pub -r 10 /air/operator_enable std_msgs/msg/Bool "{data: true}"
ros2 topic pub -r 10 /air/cmd_vel_safe geometry_msgs/msg/Twist \
  "{linear: {x: 0.2, y: 0.0, z: 0.0}, angular: {z: 0.0}}"
```

Stopping either publisher produces one zero setpoint within 500 ms and then stops the setpoint stream, handing command-loss recovery to the configured autopilot action. Do not use shell publishers as an operational control station.
