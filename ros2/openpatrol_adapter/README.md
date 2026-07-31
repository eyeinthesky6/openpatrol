# ROS 2 adapter

Build inside ROS 2 Jazzy with `colcon build --packages-select openpatrol_adapter`. Inputs: `/cmd_vel`, `/hardware/estop`, `/battery_state`. Outputs: `/cmd_vel_safe`, `/openpatrol/mobility_health`. The motor controller must independently implement the timeout; this Linux node is not the final safety controller.
