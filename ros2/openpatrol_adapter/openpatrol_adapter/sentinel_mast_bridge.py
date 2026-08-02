"""ROS 2 bridge for the Sentinel telescoping mast controller."""
from __future__ import annotations

import json
import time
from typing import Any

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
from std_msgs.msg import Bool, Int32, String

from .mast_protocol import MIN_HEIGHT_MM, encode_mast_command, parse_mast_status
from .protocol import ProtocolError

try:
    import serial
except ImportError:  # pragma: no cover
    serial = None


class SentinelMastBridge(Node):
    def __init__(self) -> None:
        super().__init__("openpatrol_sentinel_mast_bridge")
        self.declare_parameter("serial_port", "/dev/ttyACM1")
        self.declare_parameter("baud", 115200)
        self.declare_parameter("command_stale_ms", 400)
        self.declare_parameter("min_height_mm", 980)
        self.declare_parameter("max_height_mm", 1500)
        self.port_name = str(self.get_parameter("serial_port").value)
        self.baud = int(self.get_parameter("baud").value)
        self.stale_s = int(self.get_parameter("command_stale_ms").value) / 1000
        self.min_height = int(self.get_parameter("min_height_mm").value)
        self.max_height = int(self.get_parameter("max_height_mm").value)
        if self.min_height < MIN_HEIGHT_MM or self.max_height > 1500 or self.min_height >= self.max_height:
            raise ValueError("mast height parameters exceed the Rev-A physical envelope")
        if not 0.1 <= self.stale_s <= 0.5:
            raise ValueError("command_stale_ms must be between 100 and 500")

        self.state_pub = self.create_publisher(String, "/sentinel/mast/state", 10)
        self.joint_pub = self.create_publisher(JointState, "/sentinel/mast/joint_state", 10)
        self.extended_pub = self.create_publisher(Bool, "/sentinel/mast/extended", 10)
        self.create_subscription(Int32, "/sentinel/mast/target_mm", self.on_target, 10)
        self.create_subscription(Bool, "/hardware/estop", self.on_estop, 10)

        self.serial_handle: Any = None
        self.rx = bytearray()
        self.seq = 0
        self.target_mm = self.min_height
        self.target_at = 0.0
        self.estop = True
        self.rejected_frames = 0
        self.create_timer(0.02, self.step)

    def on_target(self, message: Int32) -> None:
        self.target_mm = max(self.min_height, min(self.max_height, int(message.data)))
        self.target_at = time.monotonic()

    def on_estop(self, message: Bool) -> None:
        self.estop = bool(message.data)

    def connect(self) -> None:
        if self.serial_handle is not None or serial is None:
            return
        try:
            self.serial_handle = serial.Serial(self.port_name, self.baud, timeout=0, write_timeout=0.05)
            self.serial_handle.reset_input_buffer()
        except Exception as exc:
            self.serial_handle = None
            self.publish_state("offline", str(exc))

    def disconnect(self, reason: str) -> None:
        handle, self.serial_handle = self.serial_handle, None
        if handle is not None:
            try:
                handle.close()
            except Exception:
                pass
        self.publish_extended(True)
        self.publish_state("offline", reason)

    def step(self) -> None:
        self.connect()
        handle = self.serial_handle
        if handle is None:
            self.publish_extended(True)
            return
        enabled = not self.estop and time.monotonic() - self.target_at <= self.stale_s
        try:
            self.seq = (self.seq + 1) & 0xFFFFFFFF
            handle.write(encode_mast_command(self.seq, self.target_mm, enabled))
            waiting = min(int(getattr(handle, "in_waiting", 0)), 4096)
            if waiting:
                self.rx.extend(handle.read(waiting))
            if len(self.rx) > 8192:
                self.rx.clear()
                self.rejected_frames += 1
            while b"\n" in self.rx:
                line, _, remainder = self.rx.partition(b"\n")
                self.rx = bytearray(remainder)
                self.consume(line + b"\n")
        except Exception as exc:
            self.disconnect(str(exc))

    def consume(self, line: bytes) -> None:
        try:
            status = parse_mast_status(line)
        except ProtocolError as exc:
            self.rejected_frames += 1
            self.publish_extended(True)
            self.publish_state("degraded", str(exc))
            return
        joint = JointState()
        joint.header.stamp = self.get_clock().now().to_msg()
        joint.name = ["sentinel_mast_joint"]
        joint.position = [(status.height_mm - self.min_height) / 1000]
        self.joint_pub.publish(joint)
        self.publish_extended(status.extended_or_unknown)
        blocked = (
            status.tilt_interlock
            or status.actuator_fault
            or status.drive_moving
            or status.position_sensor_fault
        )
        self.publish_state(
            "blocked" if blocked else "ready",
            "mast status received",
            status.height_mm,
            status.flags,
        )

    def publish_extended(self, extended_or_unknown: bool) -> None:
        message = Bool()
        message.data = bool(extended_or_unknown)
        self.extended_pub.publish(message)

    def publish_state(self, state: str, detail: str, height_mm: int | None = None, flags: int | None = None) -> None:
        message = String()
        message.data = json.dumps(
            {
                "state": state,
                "detail": detail,
                "height_mm": height_mm,
                "target_mm": self.target_mm,
                "flags": flags,
                "extended_or_unknown": True if flags is None else bool(flags & 0xC0),
                "position_sensor_fault": False if flags is None else bool(flags & 0x80),
                "port": self.port_name,
                "rejected_frames": self.rejected_frames,
            },
            separators=(",", ":"),
        )
        self.state_pub.publish(message)

    def shutdown(self) -> None:
        handle = self.serial_handle
        if handle is not None:
            for _ in range(3):
                try:
                    self.seq = (self.seq + 1) & 0xFFFFFFFF
                    handle.write(encode_mast_command(self.seq, self.target_mm, False))
                except Exception:
                    break
                time.sleep(0.02)
        self.disconnect("shutdown")


def main() -> None:
    rclpy.init()
    node = SentinelMastBridge()
    try:
        rclpy.spin(node)
    finally:
        node.shutdown()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
