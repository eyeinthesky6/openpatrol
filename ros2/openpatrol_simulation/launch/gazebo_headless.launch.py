from launch import LaunchDescription
from launch.actions import AppendEnvironmentVariable,IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
from pathlib import Path

def generate_launch_description():
    share=Path(get_package_share_directory("openpatrol_simulation")); gz=Path(get_package_share_directory("ros_gz_sim"))
    return LaunchDescription([
        AppendEnvironmentVariable("GZ_SIM_RESOURCE_PATH",str(share/"models")),
        IncludeLaunchDescription(PythonLaunchDescriptionSource(str(gz/"launch/gz_sim.launch.py")),launch_arguments={"gz_args":f"-s -r {share/'worlds/warehouse.sdf'}"}.items()),
        Node(package="ros_gz_bridge",executable="parameter_bridge",parameters=[{"config_file":str(share/"config/bridge.yaml")}],output="screen"),
    ])
