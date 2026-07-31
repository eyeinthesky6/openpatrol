"""Reference boundary; the motor controller must enforce the final watchdog."""
import json,time
import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node
from sensor_msgs.msg import BatteryState
from std_msgs.msg import Bool,String
class SafetyAdapter(Node):
    def __init__(self):
        super().__init__("openpatrol_safety_adapter"); self.declare_parameter("command_timeout_ms",250); self.declare_parameter("max_linear_mps",.5); self.declare_parameter("max_angular_rps",1.0)
        self.output=self.create_publisher(Twist,"/cmd_vel_safe",10); self.health=self.create_publisher(String,"/openpatrol/mobility_health",10); self.create_subscription(Twist,"/cmd_vel",self.on_command,10); self.create_subscription(Bool,"/hardware/estop",self.on_estop,10); self.create_subscription(BatteryState,"/battery_state",self.on_battery,10)
        self.estopped=True; self.battery=None; self.last_command=0.0; self.create_timer(.05,self.watchdog)
    def on_estop(self,msg): self.estopped=bool(msg.data); self.stop()
    def on_battery(self,msg): self.battery=float(msg.percentage*100) if msg.percentage>=0 else None
    def on_command(self,msg):
        self.last_command=time.monotonic()
        if self.estopped: return self.stop()
        safe=Twist(); safe.linear.x=max(-float(self.get_parameter("max_linear_mps").value),min(float(self.get_parameter("max_linear_mps").value),msg.linear.x)); safe.angular.z=max(-float(self.get_parameter("max_angular_rps").value),min(float(self.get_parameter("max_angular_rps").value),msg.angular.z)); self.output.publish(safe)
    def stop(self): self.output.publish(Twist())
    def watchdog(self):
        timed_out=(time.monotonic()-self.last_command)*1000>int(self.get_parameter("command_timeout_ms").value)
        if timed_out: self.stop()
        status=String(); status.data=json.dumps({"estop":self.estopped,"command_timed_out":timed_out,"battery_percent":self.battery}); self.health.publish(status)
def main():
    rclpy.init(); node=SafetyAdapter()
    try: rclpy.spin(node)
    finally: node.stop(); node.destroy_node(); rclpy.shutdown()
