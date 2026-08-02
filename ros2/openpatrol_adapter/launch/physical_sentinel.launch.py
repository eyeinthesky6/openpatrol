from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument("drive_serial_port", default_value="/dev/ttyACM0"),
        DeclareLaunchArgument("mast_serial_port", default_value="/dev/ttyACM1"),
        DeclareLaunchArgument("encoder_counts_per_rev", default_value="1320"),
        Node(
            package="openpatrol_adapter",
            executable="safety_adapter",
            parameters=[{"command_timeout_ms": 200, "max_linear_mps": 0.38, "max_angular_rps": 0.8}],
            output="screen",
        ),
        Node(
            package="openpatrol_adapter",
            executable="serial_motor_bridge",
            parameters=[{
                "serial_port": LaunchConfiguration("drive_serial_port"),
                "wheel_radius_m": 0.0625,
                "wheel_track_m": 0.36,
                "encoder_counts_per_rev": ParameterValue(LaunchConfiguration("encoder_counts_per_rev"), value_type=int),
                "max_wheel_speed_mps": 0.38,
                "command_stale_ms": 150,
            }],
            output="screen",
        ),
        Node(
            package="openpatrol_adapter",
            executable="sentinel_mast_bridge",
            parameters=[{
                "serial_port": LaunchConfiguration("mast_serial_port"),
                "command_stale_ms": 400,
                "min_height_mm": 980,
                "max_height_mm": 1500,
            }],
            output="screen",
        ),
        Node(package="openpatrol_adapter", executable="odom_tf", output="screen"),
    ])
