"""Publish odom -> base_link TF for controllers that emit only Odometry."""
import math
import rclpy
from geometry_msgs.msg import TransformStamped
from nav_msgs.msg import Odometry
from rclpy.node import Node
from tf2_ros import TransformBroadcaster


class OdomTransform(Node):
    def __init__(self):
        super().__init__("openpatrol_odom_tf")
        self.broadcaster=TransformBroadcaster(self)
        self.sent=False
        self.create_subscription(Odometry,"/odom",self.on_odom,20)
    def on_odom(self,msg):
        pose=msg.pose.pose
        values=(pose.position.x,pose.position.y,pose.position.z,pose.orientation.x,pose.orientation.y,pose.orientation.z,pose.orientation.w)
        if not all(math.isfinite(value) for value in values):
            self.get_logger().error("Rejected non-finite odometry transform"); return
        transform=TransformStamped(); transform.header=msg.header
        transform.header.frame_id=msg.header.frame_id or "odom"; transform.child_frame_id=msg.child_frame_id or "base_link"
        transform.transform.translation.x=pose.position.x; transform.transform.translation.y=pose.position.y; transform.transform.translation.z=pose.position.z
        transform.transform.rotation=pose.orientation; self.broadcaster.sendTransform(transform)
        if not self.sent: self.get_logger().info(f"Publishing {transform.header.frame_id} -> {transform.child_frame_id}"); self.sent=True


def main():
    rclpy.init(); node=OdomTransform()
    try: rclpy.spin(node)
    finally: node.destroy_node(); rclpy.shutdown()
