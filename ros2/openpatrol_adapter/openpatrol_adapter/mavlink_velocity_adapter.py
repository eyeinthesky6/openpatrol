"""Bounded AirScout velocity-intent bridge for MAVROS.

The flight controller remains authoritative for attitude, motor mixing, arming,
geofence and battery/command-loss failsafes. This node never publishes raw motor
commands or changes flight mode.
"""
from __future__ import annotations

import json
import math
import time

import rclpy
from geometry_msgs.msg import Twist, TwistStamped
from rclpy.node import Node
from std_msgs.msg import Bool, String

from .flight_contract import velocity_publish_decision


class MavlinkVelocityAdapter(Node):
    def __init__(self) -> None:
        super().__init__("openpatrol_airscout_velocity_adapter")
        self.declare_parameter("input_topic", "/air/cmd_vel_safe")
        self.declare_parameter("mavros_topic", "/mavros/setpoint_velocity/cmd_vel")
        self.declare_parameter("health_topic", "/air/adapter_state")
        self.declare_parameter("command_stale_ms", 500)
        self.declare_parameter("max_horizontal_mps", 1.5)
        self.declare_parameter("max_vertical_mps", 1.0)
        self.declare_parameter("max_yaw_rps", 0.8)
        self.declare_parameter("publish_rate_hz", 20.0)

        self.stale_s = int(self.get_parameter("command_stale_ms").value) / 1000
        self.max_horizontal = float(self.get_parameter("max_horizontal_mps").value)
        self.max_vertical = float(self.get_parameter("max_vertical_mps").value)
        self.max_yaw = float(self.get_parameter("max_yaw_rps").value)
        rate = float(self.get_parameter("publish_rate_hz").value)
        if not 0.2 <= self.stale_s <= 1.0:
            raise ValueError("command_stale_ms must be between 200 and 1000")
        if min(self.max_horizontal, self.max_vertical, self.max_yaw, rate) <= 0:
            raise ValueError("AirScout limits and publish rate must be positive")

        self.output = self.create_publisher(
            TwistStamped, str(self.get_parameter("mavros_topic").value), 20
        )
        self.health = self.create_publisher(
            String, str(self.get_parameter("health_topic").value), 10
        )
        self.create_subscription(
            Twist, str(self.get_parameter("input_topic").value), self.on_command, 20
        )
        self.create_subscription(Bool, "/air/velocity_authorized", self.on_authorization, 10)
        self.latest = Twist()
        self.latest_at = 0.0
        self.authorized = False
        self.was_streaming = False
        self.create_timer(1.0 / rate, self.step)

    def on_command(self, message: Twist) -> None:
        values = (
            message.linear.x,
            message.linear.y,
            message.linear.z,
            message.angular.z,
        )
        if not all(math.isfinite(value) for value in values):
            self.get_logger().error("Rejected non-finite AirScout command")
            return
        self.latest = message
        self.latest_at = time.monotonic()

    def on_authorization(self, message: Bool) -> None:
        self.authorized = bool(message.data)

    def step(self) -> None:
        age = math.inf if not self.latest_at else time.monotonic() - self.latest_at
        decision = velocity_publish_decision(
            authorized=self.authorized,
            command_age_s=age,
            stale_s=self.stale_s,
            was_streaming=self.was_streaming,
        )
        if decision.publish:
            x = 0.0 if decision.zero else self.latest.linear.x
            y = 0.0 if decision.zero else self.latest.linear.y
            horizontal = math.hypot(x, y)
            if horizontal > self.max_horizontal:
                scale = self.max_horizontal / horizontal
                x *= scale
                y *= scale
            z = 0.0 if decision.zero else max(
                -self.max_vertical, min(self.max_vertical, self.latest.linear.z)
            )
            yaw = 0.0 if decision.zero else max(
                -self.max_yaw, min(self.max_yaw, self.latest.angular.z)
            )
            message = TwistStamped()
            message.header.stamp = self.get_clock().now().to_msg()
            message.header.frame_id = "map"
            message.twist.linear.x = x
            message.twist.linear.y = y
            message.twist.linear.z = z
            message.twist.angular.z = yaw
            self.output.publish(message)
        self.was_streaming = decision.streaming

        state = String()
        state.data = json.dumps(
            {
                "adapter": "streaming" if decision.streaming else "failsafe_handoff",
                "reason": decision.reason,
                "command_age_ms": None if not self.latest_at else round(age * 1000),
                "setpoint_published": decision.publish,
                "zero_setpoint": decision.publish and decision.zero,
                "autopilot_command_loss_authoritative": True,
                "raw_motor_control": False,
                "arming_or_mode_control": False,
            },
            separators=(",", ":"),
        )
        self.health.publish(state)


def main() -> None:
    rclpy.init()
    node = MavlinkVelocityAdapter()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
