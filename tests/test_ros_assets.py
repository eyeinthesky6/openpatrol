import importlib.util,tempfile,unittest,xml.etree.ElementTree as ET
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

class RosAssetsTest(unittest.TestCase):
    def test_gazebo_and_package_xml_are_well_formed(self):
        files=[ROOT/"ros2/openpatrol_simulation/package.xml",ROOT/"ros2/openpatrol_simulation/models/openpatrol/model.config",ROOT/"ros2/openpatrol_simulation/models/openpatrol/model.sdf",ROOT/"ros2/openpatrol_simulation/worlds/warehouse.sdf",ROOT/"ros2/openpatrol_simulation/urdf/openpatrol_mock.urdf.xacro"]
        for path in files:
            with self.subTest(path=path): ET.parse(path)
    def test_gazebo_contract_uses_safe_command_and_required_sensors(self):
        model=(ROOT/"ros2/openpatrol_simulation/models/openpatrol/model.sdf").read_text()
        bridge=(ROOT/"ros2/openpatrol_simulation/config/bridge.yaml").read_text()
        for value in ("/cmd_vel_safe","/odom","/scan","/imu","/camera/image_raw"):
            self.assertIn(value,model+bridge)
        self.assertIn("<max_linear_velocity>0.5</max_linear_velocity>",model)
        self.assertIn("<wheel_separation>0.32</wheel_separation>",model)
        world=(ROOT/"ros2/openpatrol_simulation/worlds/warehouse.sdf").read_text()
        self.assertIn("<uri>../models/openpatrol</uri>",world)
    def test_ros_command_limits_reject_non_finite_values(self):
        path=ROOT/"ros2/openpatrol_adapter/openpatrol_adapter/limits.py"; spec=importlib.util.spec_from_file_location("limits",path); module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        self.assertEqual((.5,-1),module.clamp_command(5,-3,.5,1))
        with self.assertRaises(ValueError): module.clamp_command(float("nan"),0,.5,1)
    def test_headless_ci_exercises_motion_sensors_and_watchdog(self):
        workflow=(ROOT/".github/workflows/ros-gazebo.yml").read_text(); probe=(ROOT/"scripts/ros_gazebo_smoke.py").read_text()
        for value in ("gazebo_headless.launch.py","safety_adapter","ros_gazebo_smoke.py","upload-artifact"):
            self.assertIn(value,workflow)
        for value in ("/odom","/scan","/cmd_vel_safe","moved>=.05","safe_zero_after_drive"):
            self.assertIn(value,probe)
    def test_navigation_assets_expose_slam_nav2_and_docking_boundary(self):
        package=(ROOT/"ros2/openpatrol_simulation/package.xml").read_text(); launch=(ROOT/"ros2/openpatrol_simulation/launch/navigation.launch.py").read_text(); params=(ROOT/"ros2/openpatrol_simulation/config/nav2_params.yaml").read_text()
        for value in ("nav2_bringup","slam_toolbox","opennav_docking"): self.assertIn(value,package+launch)
        for value in ("scan_topic: /scan","base_frame: base_link","max_velocity: [0.5, 0.0, 1.0]"): self.assertIn(value,params)
        workflow=(ROOT/".github/workflows/ros-gazebo.yml").read_text(); smoke=(ROOT/"scripts/ros_navigation_smoke.py").read_text()
        for value in ("navigation.launch.py","ros_navigation_smoke.py","/navigate_to_pose","/follow_waypoints","/map"): self.assertIn(value,workflow+smoke)
        odom_tf=(ROOT/"ros2/openpatrol_adapter/openpatrol_adapter/odom_tf.py").read_text()
        for value in ("TransformBroadcaster","/odom","base_link","math.isfinite"): self.assertIn(value,odom_tf)
        virtual_lidar=(ROOT/"ros2/openpatrol_adapter/openpatrol_adapter/virtual_lidar.py").read_text()
        for value in ("wall_range","LaserScan","/scan","360"): self.assertIn(value,virtual_lidar)
        self.assertIn("virtual_lidar",(ROOT/"ros2/openpatrol_simulation/launch/gazebo_headless.launch.py").read_text())

if __name__=="__main__": unittest.main()
