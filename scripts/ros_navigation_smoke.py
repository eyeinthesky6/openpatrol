"""Prove SLAM produces a map and Nav2 exposes patrol actions in Gazebo."""
import json, time
import rclpy
from nav_msgs.msg import OccupancyGrid
from nav2_msgs.action import FollowWaypoints, NavigateToPose
from geometry_msgs.msg import Twist
from lifecycle_msgs.srv import GetState
from rclpy.action import ActionClient
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from tf2_ros import Buffer, TransformListener


class Probe(Node):
    def __init__(self):
        super().__init__("openpatrol_navigation_smoke")
        self.maps=0; self.cells=0; self.scans=0; self.finite_ranges=0; self.scan_frame=""
        self.create_subscription(OccupancyGrid,"/map",self.on_map,10)
        self.create_subscription(LaserScan,"/scan",self.on_scan,10)
        self.tf_buffer=Buffer(); self.tf_listener=TransformListener(self.tf_buffer,self)
        self.drive=self.create_publisher(Twist,"/cmd_vel",10)
        self.navigate=ActionClient(self,NavigateToPose,"/navigate_to_pose")
        self.waypoints=ActionClient(self,FollowWaypoints,"/follow_waypoints")
        self.bt_state=self.create_client(GetState,"/bt_navigator/get_state")
        self.waypoint_state=self.create_client(GetState,"/waypoint_follower/get_state")
    def on_map(self,msg):
        self.maps+=1; self.cells=max(self.cells,len(msg.data))
    def on_scan(self,msg):
        self.scans+=1; self.scan_frame=msg.header.frame_id
        self.finite_ranges=max(self.finite_ranges,sum(1 for value in msg.ranges if value==value and value not in (float("inf"),float("-inf"))))


rclpy.init(); node=Probe(); started=time.monotonic(); deadline=started+75; navigate_ready=False; waypoints_ready=False
try:
    while time.monotonic()<deadline:
        command=Twist()
        if time.monotonic()-started<10: command.angular.z=.25
        node.drive.publish(command)
        rclpy.spin_once(node,timeout_sec=.2)
        navigate_ready=node.navigate.server_is_ready(); waypoints_ready=node.waypoints.server_is_ready()
        if node.maps and node.cells and navigate_ready and waypoints_ready: break
    node.drive.publish(Twist())
    def active(client):
        if not client.wait_for_service(timeout_sec=2): return False
        future=client.call_async(GetState.Request()); rclpy.spin_until_future_complete(node,future,timeout_sec=3)
        return bool(future.done() and future.result() and future.result().current_state.id==3)
    tf_ready=node.tf_buffer.can_transform("odom",node.scan_frame or "base_link",rclpy.time.Time())
    result={"maps":node.maps,"map_cells":node.cells,"scans":node.scans,"finite_ranges":node.finite_ranges,"scan_frame":node.scan_frame,"scan_tf":tf_ready,"navigate_to_pose":navigate_ready,"follow_waypoints":waypoints_ready,"bt_active":active(node.bt_state),"waypoints_active":active(node.waypoint_state)}
    if not all((result["maps"]>=1,result["map_cells"]>0,result["scans"]>0,result["finite_ranges"]>0,result["scan_tf"],result["navigate_to_pose"],result["follow_waypoints"],result["bt_active"],result["waypoints_active"])):
        raise SystemExit(f"NAVIGATION_SMOKE_FAIL {result}")
    print("NAVIGATION_SMOKE_PASS",json.dumps(result,sort_keys=True))
finally:
    node.destroy_node(); rclpy.shutdown()
