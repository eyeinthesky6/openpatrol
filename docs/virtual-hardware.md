# Virtual hardware test harness

OpenPatrol has three simulation levels. They share the safe velocity, odometry, battery, E-stop and sensor boundaries used by a physical chassis.

## Level 1: deterministic CI hardware

Run without ROS or third-party packages:

```bash
python3 -m openpatrol.hardware_harness --output runtime/hardware-report.json
```

This exercises command clamps, a 250 ms watchdog, latched E-stop, motor stall, wheel slip, encoder and LiDAR dropout, recovery and a watt-hour battery model. It is deterministic and runs in normal CI. It deliberately models only the hardware contract, not contact physics or localization quality.

## Level 2: ROS 2 mock hardware

On Ubuntu 24.04 with ROS 2 Jazzy, copy both packages under `ros2/` into a colcon workspace, install dependencies with `rosdep`, build and launch:

```bash
colcon build --packages-select openpatrol_adapter openpatrol_simulation
source install/setup.bash
ros2 launch openpatrol_simulation mock_hardware.launch.py
```

The mock uses `mock_components/GenericSystem` and the real controller configuration. It validates URDF, controller manager, joint interfaces, velocity limits and launch wiring without physics.

## Level 3: Gazebo Harmonic

Install the Jazzy `ros_gz`, Nav2 and controller packages, build the same workspace, then run:

```bash
ros2 launch openpatrol_simulation gazebo.launch.py
ros2 run openpatrol_adapter safety_adapter
```

Publish `false` to `/hardware/estop`, then command `/cmd_vel`. The safety adapter is the only path to `/cmd_vel_safe`; Gazebo consumes that safe topic and publishes `/odom`, `/imu` and `/camera/image_raw`. A deterministic 2-D ray-cast node publishes `/scan` from the bounded warehouse geometry. This avoids GPU-renderer differences on hosted runners while exercising the exact `LaserScan` contract used by a physical lidar. The warehouse world contains shelving and a small differential-drive model with sensor noise, friction and mass.

Useful acceptance checks:

```bash
ros2 topic hz /scan
ros2 topic hz /odom
ros2 topic echo /openpatrol/mobility_health
ros2 topic pub --once /hardware/estop std_msgs/msg/Bool '{data: false}'
ros2 topic pub -r 10 /cmd_vel geometry_msgs/msg/Twist '{linear: {x: 0.2}}'
```

Stop publishing and confirm `/cmd_vel_safe` becomes zero within 250 ms. Repeat with E-stop, paused simulation, obstructed aisles and intentionally disabled bridges. Never tune physical stopping distance from simulation alone.

## Pass boundary

A virtual pass proves software wiring and expected fault responses. It does not prove tyre grip, braking distance, motor torque, centre-of-gravity stability, real sensor blind spots, wireless coverage, battery range or charger alignment. Those remain physical acceptance tests.

## GitHub Actions

`.github/workflows/ros-gazebo.yml` runs Level 3 headlessly on Ubuntu 24.04. It installs ROS 2 Jazzy and Gazebo Harmonic using their maintained setup actions, resolves package dependencies, builds both packages and starts the real Gazebo world plus safety adapter. The black-box probe requires at least three LiDAR scans, at least 5 cm of odometry movement and a zero safe-velocity output after command traffic stops. Logs are retained as a workflow artifact for 14 days even when the job fails.

This heavyweight job has a 20-minute limit and is separate from the fast Python test job. The workflow can also be started manually using `workflow_dispatch`.
