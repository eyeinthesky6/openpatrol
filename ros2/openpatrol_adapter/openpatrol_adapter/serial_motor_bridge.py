"""ROS 2 bridge to the OpenPatrol reference safety/motor controller.

The microcontroller and normally-closed stop loop remain authoritative. This node
cannot energize a physically open drive relay and sends disabled frames on exit.
"""
from __future__ import annotations

import json
import math
import time
from typing import Any

import rclpy
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from rclpy.node import Node
from sensor_msgs.msg import BatteryState
from std_msgs.msg import Bool, String

from .protocol import ProtocolError, differential_increment, encode_command, parse_status, tick_delta, twist_to_wheels

try:
    import serial
except ImportError:  # pragma: no cover - resolved by ROS dependency on hardware hosts
    serial = None


class SerialMotorBridge(Node):
    def __init__(self) -> None:
        super().__init__("openpatrol_serial_motor_bridge")
        self.declare_parameter("serial_port", "/dev/ttyACM0")
        self.declare_parameter("baud", 115200)
        self.declare_parameter("wheel_radius_m", 0.05)
        self.declare_parameter("wheel_track_m", 0.34)
        self.declare_parameter("encoder_counts_per_rev", 1320)
        self.declare_parameter("max_wheel_speed_mps", 0.45)
        self.declare_parameter("command_stale_ms", 150)
        self.declare_parameter("battery_full_mv", 14400)
        self.declare_parameter("battery_empty_mv", 11200)
        self.declare_parameter("odom_frame", "odom")
        self.declare_parameter("base_frame", "base_link")

        self.port_name = str(self.get_parameter("serial_port").value)
        self.baud = int(self.get_parameter("baud").value)
        self.radius = float(self.get_parameter("wheel_radius_m").value)
        self.track = float(self.get_parameter("wheel_track_m").value)
        self.counts_per_rev = int(self.get_parameter("encoder_counts_per_rev").value)
        self.max_wheel_speed = float(self.get_parameter("max_wheel_speed_mps").value)
        self.command_stale = int(self.get_parameter("command_stale_ms").value) / 1000
        self.battery_full_mv = int(self.get_parameter("battery_full_mv").value)
        self.battery_empty_mv = int(self.get_parameter("battery_empty_mv").value)
        self.odom_frame = str(self.get_parameter("odom_frame").value)
        self.base_frame = str(self.get_parameter("base_frame").value)
        if self.radius <= 0 or self.track <= 0 or self.counts_per_rev <= 0 or self.max_wheel_speed <= 0:
            raise ValueError("physical drive parameters must be positive")
        if not 0.02 <= self.command_stale <= 0.2:
            raise ValueError("command_stale_ms must be between 20 and 200")

        self.odom_pub = self.create_publisher(Odometry, "/odom", 20)
        self.battery_pub = self.create_publisher(BatteryState, "/battery_state", 10)
        self.estop_pub = self.create_publisher(Bool, "/hardware/estop", 10)
        self.health_pub = self.create_publisher(String, "/openpatrol/controller_health", 10)
        self.create_subscription(Twist, "/cmd_vel_safe", self.on_command, 20)

        self.serial_handle: Any = None
        self.rx = bytearray()
        self.seq = 0
        self.latest_twist = Twist()
        self.latest_command_at = 0.0
        self.last_status_at = 0.0
        self.previous_ticks: tuple[int, int] | None = None
        self.x = self.y = self.theta = 0.0
        self.last_odom_at: float | None = None
        self.rejected_frames = 0
        self.create_timer(0.02, self.step)

    def on_command(self, message: Twist) -> None:
        values = (message.linear.x, message.angular.z)
        if not all(math.isfinite(value) for value in values):
            self.get_logger().error("Rejected non-finite velocity command")
            return
        self.latest_twist = message
        self.latest_command_at = time.monotonic()

    def connect(self) -> None:
        if self.serial_handle is not None or serial is None:
            return
        try:
            self.serial_handle = serial.Serial(self.port_name, self.baud, timeout=0, write_timeout=0.05)
            self.serial_handle.reset_input_buffer()
            self.get_logger().info(f"Connected safety controller on {self.port_name} at {self.baud}")
        except Exception as exc:
            self.serial_handle = None
            self.publish_health("offline", str(exc))

    def disconnect(self, reason: str) -> None:
        handle, self.serial_handle = self.serial_handle, None
        if handle is not None:
            try:
                handle.close()
            except Exception:
                pass
        self.publish_health("offline", reason)

    def step(self) -> None:
        self.connect()
        handle = self.serial_handle
        if handle is None:
            return
        now = time.monotonic()
        enabled = now - self.latest_command_at <= self.command_stale
        try:
            left, right = twist_to_wheels(
                self.latest_twist.linear.x if enabled else 0.0,
                self.latest_twist.angular.z if enabled else 0.0,
                self.track,
                self.max_wheel_speed,
            )
            self.seq = (self.seq + 1) & 0xFFFFFFFF
            handle.write(encode_command(self.seq, left, right, enabled))
            waiting = min(int(getattr(handle, "in_waiting", 0)), 4096)
            if waiting:
                self.rx.extend(handle.read(waiting))
            if len(self.rx) > 8192:
                self.rx.clear()
                self.rejected_frames += 1
            while b"\n" in self.rx:
                line, _, remainder = self.rx.partition(b"\n")
                self.rx = bytearray(remainder)
                self.consume(line + b"\n", now)
        except Exception as exc:
            self.disconnect(str(exc))

    def consume(self, line: bytes, now: float) -> None:
        try:
            status = parse_status(line)
        except ProtocolError as exc:
            self.rejected_frames += 1
            self.publish_health("degraded", str(exc))
            return
        self.last_status_at = now
        estop = Bool()
        estop.data = status.estop_open or status.stop_loop_open or status.driver_fault or status.charger_connected
        self.estop_pub.publish(estop)

        battery = BatteryState()
        battery.header.stamp = self.get_clock().now().to_msg()
        battery.voltage = status.battery_mv / 1000
        span = max(1, self.battery_full_mv - self.battery_empty_mv)
        battery.percentage = max(0.0, min(1.0, (status.battery_mv - self.battery_empty_mv) / span))
        battery.present = status.battery_mv > 0
        self.battery_pub.publish(battery)

        if self.previous_ticks is not None:
            left_delta = tick_delta(status.left_ticks, self.previous_ticks[0])
            right_delta = tick_delta(status.right_ticks, self.previous_ticks[1])
            distance, rotation = differential_increment(left_delta, right_delta, self.radius, self.track, self.counts_per_rev)
            mid = self.theta + rotation / 2
            self.x += distance * math.cos(mid)
            self.y += distance * math.sin(mid)
            self.theta = math.atan2(math.sin(self.theta + rotation), math.cos(self.theta + rotation))
            dt = max(1e-3, now - (self.last_odom_at or now))
            self.publish_odom(distance / dt, rotation / dt)
        self.previous_ticks = (status.left_ticks, status.right_ticks)
        self.last_odom_at = now
        state = "safe_stop" if estop.data or status.command_timed_out else "ready"
        self.publish_health(state, "controller status received", status.flags)

    def publish_odom(self, linear_mps: float, angular_rps: float) -> None:
        message = Odometry()
        message.header.stamp = self.get_clock().now().to_msg()
        message.header.frame_id = self.odom_frame
        message.child_frame_id = self.base_frame
        message.pose.pose.position.x = self.x
        message.pose.pose.position.y = self.y
        message.pose.pose.orientation.z = math.sin(self.theta / 2)
        message.pose.pose.orientation.w = math.cos(self.theta / 2)
        message.twist.twist.linear.x = linear_mps
        message.twist.twist.angular.z = angular_rps
        self.odom_pub.publish(message)

    def publish_health(self, state: str, detail: str, flags: int | None = None) -> None:
        message = String()
        message.data = json.dumps(
            {
                "state": state,
                "detail": detail,
                "port": self.port_name,
                "last_status_age_ms": round((time.monotonic() - self.last_status_at) * 1000)
                if self.last_status_at
                else None,
                "rejected_frames": self.rejected_frames,
                "flags": flags,
            },
            separators=(",", ":"),
        )
        self.health_pub.publish(message)

    def shutdown(self) -> None:
        handle = self.serial_handle
        if handle is not None:
            for _ in range(3):
                try:
                    self.seq = (self.seq + 1) & 0xFFFFFFFF
                    handle.write(encode_command(self.seq, 0.0, 0.0, False))
                except Exception:
                    break
                time.sleep(0.02)
        self.disconnect("shutdown")


def main() -> None:
    rclpy.init()
    node = SerialMotorBridge()
    try:
        rclpy.spin(node)
    finally:
        node.shutdown()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
