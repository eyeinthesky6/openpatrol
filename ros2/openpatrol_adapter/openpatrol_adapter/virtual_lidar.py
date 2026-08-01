"""Deterministic 2-D warehouse lidar for CI and software-only development."""
import math
import rclpy
from nav_msgs.msg import Odometry
from rclpy.node import Node
from sensor_msgs.msg import LaserScan


def wall_range(x, y, angle, max_range=12.0):
    """Return distance to the warehouse perimeter in odometry coordinates."""
    dx, dy = math.cos(angle), math.sin(angle)
    hits = []
    # The robot starts at world x=-3; world walls -6/+6 become odom -3/+9.
    for boundary in (-3.0, 9.0):
        if abs(dx) > 1e-9:
            distance = (boundary - x) / dx
            hit_y = y + distance * dy
            if distance > 0 and -6.0 <= hit_y <= 6.0: hits.append(distance)
    for boundary in (-6.0, 6.0):
        if abs(dy) > 1e-9:
            distance = (boundary - y) / dy
            hit_x = x + distance * dx
            if distance > 0 and -3.0 <= hit_x <= 9.0: hits.append(distance)
    return min(min(hits, default=max_range), max_range)


class VirtualLidar(Node):
    def __init__(self):
        super().__init__("openpatrol_virtual_lidar")
        self.x = self.y = self.yaw = 0.0
        self.create_subscription(Odometry, "/odom", self.on_odom, 20)
        self.publisher = self.create_publisher(LaserScan, "/scan", 10)
        self.create_timer(0.1, self.publish_scan)

    def on_odom(self, message):
        self.x, self.y = message.pose.pose.position.x, message.pose.pose.position.y
        q = message.pose.pose.orientation
        self.yaw = math.atan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y * q.y + q.z * q.z))

    def publish_scan(self):
        message = LaserScan(); message.header.stamp = self.get_clock().now().to_msg(); message.header.frame_id = "base_link"
        message.angle_min = -math.pi; message.angle_increment = 2 * math.pi / 360; message.angle_max = math.pi - message.angle_increment
        message.scan_time = 0.1; message.time_increment = message.scan_time / 360; message.range_min = 0.12; message.range_max = 12.0
        message.ranges = [wall_range(self.x, self.y, self.yaw + message.angle_min + index * message.angle_increment) for index in range(360)]
        message.intensities = [1.0] * 360; self.publisher.publish(message)


def main():
    rclpy.init(); node = VirtualLidar()
    try: rclpy.spin(node)
    finally: node.destroy_node(); rclpy.shutdown()
