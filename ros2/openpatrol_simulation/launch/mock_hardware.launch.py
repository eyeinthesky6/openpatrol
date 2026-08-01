from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
from pathlib import Path
import xacro

def generate_launch_description():
    share=Path(get_package_share_directory("openpatrol_simulation"))
    robot=xacro.process_file(str(share/"urdf/openpatrol_mock.urdf.xacro")).toxml()
    controllers=str(share/"config/controllers.yaml")
    return LaunchDescription([
        Node(package="robot_state_publisher",executable="robot_state_publisher",parameters=[{"robot_description":robot,"use_sim_time":False}]),
        Node(package="controller_manager",executable="ros2_control_node",parameters=[{"robot_description":robot},controllers],output="screen"),
        Node(package="controller_manager",executable="spawner",arguments=["joint_state_broadcaster","--controller-manager","/controller_manager"]),
        Node(package="controller_manager",executable="spawner",arguments=["diff_drive_controller","--controller-manager","/controller_manager"]),
    ])
