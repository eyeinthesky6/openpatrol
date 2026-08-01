"""Prove SLAM produces a map and Nav2 exposes patrol actions in Gazebo."""
import json, time
import rclpy
from nav_msgs.msg import OccupancyGrid
from nav2_msgs.action import FollowWaypoints, NavigateToPose
from rclpy.action import ActionClient
from rclpy.node import Node


class Probe(Node):
    def __init__(self):
        super().__init__("openpatrol_navigation_smoke")
        self.maps=0; self.cells=0
        self.create_subscription(OccupancyGrid,"/map",self.on_map,10)
        self.navigate=ActionClient(self,NavigateToPose,"/navigate_to_pose")
        self.waypoints=ActionClient(self,FollowWaypoints,"/follow_waypoints")
    def on_map(self,msg):
        self.maps+=1; self.cells=max(self.cells,len(msg.data))


rclpy.init(); node=Probe(); deadline=time.monotonic()+75; navigate_ready=False; waypoints_ready=False
try:
    while time.monotonic()<deadline:
        rclpy.spin_once(node,timeout_sec=.2)
        navigate_ready=node.navigate.server_is_ready(); waypoints_ready=node.waypoints.server_is_ready()
        if node.maps and node.cells and navigate_ready and waypoints_ready: break
    result={"maps":node.maps,"map_cells":node.cells,"navigate_to_pose":navigate_ready,"follow_waypoints":waypoints_ready}
    if not all((result["maps"]>=1,result["map_cells"]>0,result["navigate_to_pose"],result["follow_waypoints"])):
        raise SystemExit(f"NAVIGATION_SMOKE_FAIL {result}")
    print("NAVIGATION_SMOKE_PASS",json.dumps(result,sort_keys=True))
finally:
    node.destroy_node(); rclpy.shutdown()
