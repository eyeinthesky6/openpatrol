from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument("serial_port", default_value="/dev/ttyACM0"),
        DeclareLaunchArgument("wheel_radius_m", default_value="0.05"),
        DeclareLaunchArgument("wheel_track_m", default_value="0.34"),
        DeclareLaunchArgument("encoder_counts_per_rev", default_value="1320"),
        DeclareLaunchArgument("max_wheel_speed_mps", default_value="0.45"),
        Node(
            package="openpatrol_adapter",
            executable="safety_adapter",
            parameters=[{"command_timeout_ms": 250, "max_linear_mps": 0.5, "max_angular_rps": 1.0}],
            output="screen",
        ),
        Node(
            package="openpatrol_adapter",
            executable="serial_motor_bridge",
            parameters=[{
                "serial_port": LaunchConfiguration("serial_port"),
                "wheel_radius_m": ParameterValue(LaunchConfiguration("wheel_radius_m"), value_type=float),
                "wheel_track_m": ParameterValue(LaunchConfiguration("wheel_track_m"), value_type=float),
                "encoder_counts_per_rev": ParameterValue(LaunchConfiguration("encoder_counts_per_rev"), value_type=int),
                "max_wheel_speed_mps": ParameterValue(LaunchConfiguration("max_wheel_speed_mps"), value_type=float),
            }],
            output="screen",
        ),
        Node(package="openpatrol_adapter", executable="odom_tf", output="screen"),
    ])
