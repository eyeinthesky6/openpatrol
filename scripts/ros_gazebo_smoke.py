#!/usr/bin/env python3
"""Black-box ROS/Gazebo CI probe: sensors, motion and command watchdog."""
import math,time
import rclpy
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from std_msgs.msg import Bool

class Probe(Node):
    def __init__(self):
        super().__init__("openpatrol_gazebo_smoke")
        self.cmd=self.create_publisher(Twist,"/cmd_vel",10); self.estop=self.create_publisher(Bool,"/hardware/estop",10)
        self.create_subscription(Odometry,"/odom",self.on_odom,10); self.create_subscription(LaserScan,"/scan",self.on_scan,10); self.create_subscription(Twist,"/cmd_vel_safe",self.on_safe,10)
        self.started=time.monotonic(); self.drive_started=None; self.drive_stopped=None; self.first_pose=None; self.last_pose=None; self.scans=0; self.safe_zero_after_drive=False
        self.create_timer(.05,self.step)
    def on_odom(self,msg):
        pose=(msg.pose.pose.position.x,msg.pose.pose.position.y)
        self.first_pose=self.first_pose or pose; self.last_pose=pose
    def on_scan(self,msg):
        if msg.ranges: self.scans+=1
    def on_safe(self,msg):
        if self.drive_stopped and time.monotonic()-self.drive_stopped>.3 and abs(msg.linear.x)<1e-6 and abs(msg.angular.z)<1e-6: self.safe_zero_after_drive=True
    def step(self):
        release=Bool(); release.data=False; self.estop.publish(release)
        if self.drive_started is None and self.first_pose and self.scans>=3: self.drive_started=time.monotonic()
        if self.drive_started and time.monotonic()-self.drive_started < 3:
            command=Twist(); command.linear.x=.2; self.cmd.publish(command)
        elif self.drive_started and self.drive_stopped is None: self.drive_stopped=time.monotonic()
    def passed(self):
        moved=0 if not self.first_pose or not self.last_pose else math.hypot(self.last_pose[0]-self.first_pose[0],self.last_pose[1]-self.first_pose[1])
        return self.scans>=3 and moved>=.05 and self.safe_zero_after_drive,{"scans":self.scans,"moved_m":round(moved,3),"watchdog_zero":self.safe_zero_after_drive}

def main():
    rclpy.init(); probe=Probe(); deadline=time.monotonic()+45
    while rclpy.ok() and time.monotonic()<deadline:
        rclpy.spin_once(probe,timeout_sec=.1)
        passed,metrics=probe.passed()
        if passed: print(f"GAZEBO_SMOKE_PASS {metrics}",flush=True); probe.destroy_node(); rclpy.shutdown(); return
    _,metrics=probe.passed(); print(f"GAZEBO_SMOKE_FAIL {metrics}",flush=True); probe.destroy_node(); rclpy.shutdown(); raise SystemExit(1)

if __name__=="__main__": main()
