"""Start SLAM and Nav2 against the OpenPatrol ROS sensor/mobility contract."""
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare
from launch_ros.actions import Node


def generate_launch_description():
    use_sim_time = LaunchConfiguration("use_sim_time")
    params = PathJoinSubstitution([FindPackageShare("openpatrol_simulation"), "config", "nav2_params.yaml"])
    slam = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(PathJoinSubstitution([FindPackageShare("slam_toolbox"), "launch", "online_async_launch.py"])),
        launch_arguments={"use_sim_time": use_sim_time, "slam_params_file": params}.items(),
    )
    nav = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(PathJoinSubstitution([FindPackageShare("nav2_bringup"), "launch", "navigation_launch.py"])),
        launch_arguments={"use_sim_time": use_sim_time, "params_file": params, "autostart": "true"}.items(),
    )
    odom_tf=Node(package="openpatrol_adapter",executable="odom_tf",parameters=[{"use_sim_time":use_sim_time}],output="screen")
    return LaunchDescription([DeclareLaunchArgument("use_sim_time", default_value="true"), odom_tf, slam, nav])
