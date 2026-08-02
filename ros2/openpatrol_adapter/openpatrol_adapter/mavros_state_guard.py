"""Read-only MAVROS state guard for AirScout velocity authorization.

This node never arms the vehicle and never changes flight mode. It only authorizes
OpenPatrol velocity setpoints after the operator/autopilot have already established
a connected, armed GUIDED/OFFBOARD state and while an operator heartbeat remains fresh.
"""
from __future__ import annotations

import json
import time

import rclpy
from mavros_msgs.msg import State
from rclpy.node import Node
from std_msgs.msg import Bool, String


class MavrosStateGuard(Node):
    def __init__(self) -> None:
        super().__init__("openpatrol_airscout_state_guard")
        self.declare_parameter("state_topic", "/mavros/state")
        self.declare_parameter("allowed_modes", ["GUIDED", "OFFBOARD"])
        self.declare_parameter("operator_enable_timeout_ms", 500)
        self.allowed_modes = {str(value).upper() for value in self.get_parameter("allowed_modes").value}
        self.operator_timeout_s = int(self.get_parameter("operator_enable_timeout_ms").value) / 1000
        if not self.allowed_modes:
            raise ValueError("allowed_modes cannot be empty")
        if not 0.2 <= self.operator_timeout_s <= 2.0:
            raise ValueError("operator_enable_timeout_ms must be between 200 and 2000")

        self.authorization_pub = self.create_publisher(Bool, "/air/velocity_authorized", 10)
        self.state_pub = self.create_publisher(String, "/air/flight_state", 10)
        self.create_subscription(State, str(self.get_parameter("state_topic").value), self.on_state, 10)
        self.create_subscription(Bool, "/air/operator_enable", self.on_operator_enable, 10)
        self.create_subscription(Bool, "/hardware/estop", self.on_estop, 10)

        self.connected = False
        self.armed = False
        self.mode = ""
        self.estop = False
        self.operator_enabled = False
        self.operator_enable_at = 0.0
        self.create_timer(0.05, self.step)

    def on_state(self, message: State) -> None:
        self.connected = bool(message.connected)
        self.armed = bool(message.armed)
        self.mode = str(message.mode).upper()

    def on_operator_enable(self, message: Bool) -> None:
        self.operator_enabled = bool(message.data)
        self.operator_enable_at = time.monotonic()

    def on_estop(self, message: Bool) -> None:
        self.estop = bool(message.data)

    def step(self) -> None:
        age = time.monotonic() - self.operator_enable_at
        fresh_operator_enable = self.operator_enabled and age <= self.operator_timeout_s
        authorized = (
            self.connected
            and self.armed
            and self.mode in self.allowed_modes
            and fresh_operator_enable
            and not self.estop
        )
        message = Bool()
        message.data = authorized
        self.authorization_pub.publish(message)

        state = String()
        state.data = json.dumps(
            {
                "connected": self.connected,
                "armed": self.armed,
                "mode": self.mode,
                "allowed_mode": self.mode in self.allowed_modes,
                "operator_enable_fresh": fresh_operator_enable,
                "estop": self.estop,
                "velocity_authorized": authorized,
                "arming_or_mode_control": False,
            },
            separators=(",", ":"),
        )
        self.state_pub.publish(state)


def main() -> None:
    rclpy.init()
    node = MavrosStateGuard()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
