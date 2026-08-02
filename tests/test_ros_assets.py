import importlib.util
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class RosAssetsTest(unittest.TestCase):
    def test_gazebo_and_package_xml_are_well_formed(self):
        files = [
            ROOT / "ros2/openpatrol_simulation/package.xml",
            ROOT / "ros2/openpatrol_adapter/package.xml",
            ROOT / "ros2/openpatrol_simulation/models/openpatrol/model.config",
            ROOT / "ros2/openpatrol_simulation/models/openpatrol/model.sdf",
            ROOT / "ros2/openpatrol_simulation/worlds/warehouse.sdf",
            ROOT / "ros2/openpatrol_simulation/urdf/openpatrol_mock.urdf.xacro",
        ]
        for path in files:
            with self.subTest(path=path):
                ET.parse(path)

    def test_gazebo_contract_matches_rover_one_rev_a(self):
        model = (ROOT / "ros2/openpatrol_simulation/models/openpatrol/model.sdf").read_text()
        bridge = (ROOT / "ros2/openpatrol_simulation/config/bridge.yaml").read_text()
        for value in ("/cmd_vel_safe", "/odom", "/scan", "/imu", "/camera/image_raw"):
            self.assertIn(value, model + bridge)
        for value in (
            "<max_linear_velocity>0.45</max_linear_velocity>",
            "<wheel_separation>0.34</wheel_separation>",
            "<wheel_radius>0.05</wheel_radius>",
            "left_front_joint",
            "left_rear_joint",
            "right_front_joint",
            "right_rear_joint",
        ):
            self.assertIn(value, model)
        world = (ROOT / "ros2/openpatrol_simulation/worlds/warehouse.sdf").read_text()
        self.assertIn("<uri>../models/openpatrol</uri>", world)

    def test_ros_command_limits_reject_non_finite_values(self):
        path = ROOT / "ros2/openpatrol_adapter/openpatrol_adapter/limits.py"
        spec = importlib.util.spec_from_file_location("limits", path)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)
        self.assertEqual((.5, -1), module.clamp_command(5, -3, .5, 1))
        with self.assertRaises(ValueError):
            module.clamp_command(float("nan"), 0, .5, 1)

    def test_headless_ci_exercises_motion_sensors_and_watchdog(self):
        workflow = (ROOT / ".github/workflows/ros-gazebo.yml").read_text()
        probe = (ROOT / "scripts/ros_gazebo_smoke.py").read_text()
        for value in ("gazebo_headless.launch.py", "safety_adapter", "ros_gazebo_smoke.py", "upload-artifact"):
            self.assertIn(value, workflow)
        for value in ("/odom", "/scan", "/cmd_vel_safe", "moved>=.05", "safe_zero_after_drive"):
            self.assertIn(value, probe)

    def test_navigation_assets_expose_slam_nav2_and_docking_boundary(self):
        package = (ROOT / "ros2/openpatrol_simulation/package.xml").read_text()
        launch = (ROOT / "ros2/openpatrol_simulation/launch/navigation.launch.py").read_text()
        params = (ROOT / "ros2/openpatrol_simulation/config/nav2_params.yaml").read_text()
        for value in ("nav2_bringup", "slam_toolbox", "opennav_docking"):
            self.assertIn(value, package + launch)
        for value in ("scan_topic: /scan", "base_frame: base_link", "max_velocity: [0.5, 0.0, 1.0]"):
            self.assertIn(value, params)
        workflow = (ROOT / ".github/workflows/ros-gazebo.yml").read_text()
        smoke = (ROOT / "scripts/ros_navigation_smoke.py").read_text()
        for value in ("navigation.launch.py", "ros_navigation_smoke.py", "/navigate_to_pose", "/follow_waypoints", "/map"):
            self.assertIn(value, workflow + smoke)

    def test_ground_controller_bridge_closes_the_physical_boundary(self):
        setup = (ROOT / "ros2/openpatrol_adapter/setup.py").read_text()
        bridge = (ROOT / "ros2/openpatrol_adapter/openpatrol_adapter/serial_motor_bridge.py").read_text()
        launch_path = ROOT / "ros2/openpatrol_adapter/launch/physical_rover.launch.py"
        firmware = (ROOT / "hardware/common/firmware/safety_controller/safety_controller.ino").read_text()
        protocol = (ROOT / "hardware/common/serial-protocol.md").read_text()
        self.assertTrue(launch_path.is_file())
        self.assertIn("serial_motor_bridge", setup + launch_path.read_text())
        for value in ("/cmd_vel_safe", "/odom", "/battery_state", "/hardware/estop", "encode_command", "parse_status"):
            self.assertIn(value, bridge)
        for value in ("COMMAND_TIMEOUT_MS=200", "crc16", "safetyLoopOk", "DRIVER_ENABLE", "MAST_EXTENDED", "DRIVE_MOVING_OUTPUT"):
            self.assertIn(value, firmware)
        for value in ("CRC16-CCITT", "normally-closed", "$C,sequence", "$S,sequence", "bit 5"):
            self.assertIn(value, protocol)

    def test_airscout_adapter_keeps_flight_critical_authority_in_autopilot(self):
        setup = (ROOT / "ros2/openpatrol_adapter/setup.py").read_text()
        adapter = (ROOT / "ros2/openpatrol_adapter/openpatrol_adapter/mavlink_velocity_adapter.py").read_text()
        guard = (ROOT / "ros2/openpatrol_adapter/openpatrol_adapter/mavros_state_guard.py").read_text()
        launch = (ROOT / "ros2/openpatrol_adapter/launch/physical_airscout.launch.py").read_text()
        config = (ROOT / "ros2/openpatrol_adapter/config/airscout.yaml").read_text()
        for value in (
            "mavlink_velocity_adapter",
            "mavros_state_guard",
            "/air/cmd_vel_safe",
            "/air/operator_enable",
            "/air/velocity_authorized",
            "/air/flight_state",
            "/air/adapter_state",
            "/mavros/setpoint_velocity/cmd_vel",
        ):
            self.assertIn(value, setup + adapter + guard + launch)
        for forbidden in ("/mavros/actuator_control", "CommandLong", "arming/cmd", "set_mode"):
            self.assertNotIn(forbidden, adapter + guard)
        for value in ("command_stale_ms: 500", "operator_enable_timeout_ms: 500", "state_timeout_ms: 2000", "health_topic: /air/adapter_state", "max_horizontal_mps: 1.5", "max_vertical_mps: 1.0"):
            self.assertIn(value, config)
        self.assertIn("autopilot_command_loss_authoritative", adapter)
        self.assertIn("state_fresh", guard)

    def test_sentinel_mast_has_independent_limits_and_bridge(self):
        setup = (ROOT / "ros2/openpatrol_adapter/setup.py").read_text()
        bridge = (ROOT / "ros2/openpatrol_adapter/openpatrol_adapter/sentinel_mast_bridge.py").read_text()
        launch = (ROOT / "ros2/openpatrol_adapter/launch/physical_sentinel.launch.py").read_text()
        firmware = (ROOT / "hardware/sentinel-rev-a/firmware/mast_controller/mast_controller.ino").read_text()
        mast_protocol = (ROOT / "hardware/sentinel-rev-a/mast-protocol.md").read_text()
        for value in ("sentinel_mast_bridge", "/sentinel/mast/target_mm", "/sentinel/mast/state"):
            self.assertIn(value, setup + bridge + launch)
        for value in ("UPPER_LIMIT", "LOWER_LIMIT", "TILT_OK", "DRIVE_MOVING", "COMMAND_TIMEOUT_MS=500", "HEIGHT_ADC"):
            self.assertIn(value, firmware)
        for value in ("$M,sequence", "$T,sequence", "CRC16-CCITT", "self-locking"):
            self.assertIn(value, mast_protocol)

    def test_family_packs_are_complete_and_visuals_are_engineering_aligned(self):
        readme = (ROOT / "README.md").read_text()
        platforms = (ROOT / "docs/hardware-platforms.md").read_text()
        design = (ROOT / "docs/family-design-language.md").read_text()
        required = (
            "hardware/common/cad/family_style.scad",
            "hardware/rover-one-rev-a/cad/rover_one.scad",
            "hardware/rover-one-rev-a/cad/rover_one_family.scad",
            "hardware/triscout-rev-a/cad/triscout.scad",
            "hardware/triscout-rev-a/cad/triscout_family.scad",
            "hardware/airscout-rev-a/cad/airscout.scad",
            "hardware/airscout-rev-a/BOM.csv",
            "hardware/airscout-rev-a/wiring.md",
            "hardware/sentinel-rev-a/cad/sentinel.scad",
            "hardware/sentinel-rev-a/BOM.csv",
            "hardware/sentinel-rev-a/wiring.md",
            "hardware/sentinel-rev-a/mast-protocol.md",
            "openpatrol/profiles/rover-one-rev-a.json",
            "openpatrol/profiles/triscout-rev-a.json",
            "openpatrol/profiles/airscout-rev-a.json",
            "openpatrol/profiles/sentinel-rev-a.json",
            "docs/assets/openpatrol-hardware-family-concept.svg",
            "docs/assets/sentinel-mast-envelope.svg",
        )
        for relative in required:
            self.assertTrue((ROOT / relative).is_file(), relative)
        for value in ("openpatrol-plain-future-v1", "Source-of-truth hierarchy", "warm off-white", "matte charcoal"):
            self.assertIn(value, design)
        for value in ("ready-to-test prototype", "physically unvalidated", "AirScout", "Sentinel"):
            self.assertIn(value, readme + platforms)

    def test_cad_export_workflow_covers_all_four_platforms(self):
        script = (ROOT / "scripts/export-hardware.sh").read_text()
        workflow = (ROOT / ".github/workflows/hardware-cad.yml").read_text()
        for platform in ("rover-one-rev-a", "triscout-rev-a", "airscout-rev-a", "sentinel-rev-a"):
            self.assertIn(platform, script + workflow)
        for part in ("prop_guard_segment", "shell_top", "mast_bushing", "mask_frame", "head_shell"):
            self.assertIn(part, script)
        self.assertIn("xvfb-run -a ./scripts/export-hardware.sh all", workflow)


if __name__ == "__main__":
    unittest.main()
