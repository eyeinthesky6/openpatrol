from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument("max_horizontal_mps", default_value="1.5"),
        DeclareLaunchArgument("max_vertical_mps", default_value="1.0"),
        DeclareLaunchArgument("max_yaw_rps", default_value="0.8"),
        Node(
            package="openpatrol_adapter",
            executable="mavros_state_guard",
            parameters=[{
                "allowed_modes": ["GUIDED", "OFFBOARD"],
                "operator_enable_timeout_ms": 500,
            }],
            output="screen",
        ),
        Node(
            package="openpatrol_adapter",
            executable="mavlink_velocity_adapter",
            parameters=[{
                "max_horizontal_mps": ParameterValue(LaunchConfiguration("max_horizontal_mps"), value_type=float),
                "max_vertical_mps": ParameterValue(LaunchConfiguration("max_vertical_mps"), value_type=float),
                "max_yaw_rps": ParameterValue(LaunchConfiguration("max_yaw_rps"), value_type=float),
                "command_stale_ms": 500,
                "publish_rate_hz": 20.0,
            }],
            output="screen",
        ),
    ])
