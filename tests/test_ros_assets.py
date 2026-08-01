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
    def test_ros_command_limits_reject_non_finite_values(self):
        path=ROOT/"ros2/openpatrol_adapter/openpatrol_adapter/limits.py"; spec=importlib.util.spec_from_file_location("limits",path); module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        self.assertEqual((.5,-1),module.clamp_command(5,-3,.5,1))
        with self.assertRaises(ValueError): module.clamp_command(float("nan"),0,.5,1)

if __name__=="__main__": unittest.main()
