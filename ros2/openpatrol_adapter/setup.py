from glob import glob
from setuptools import find_packages,setup

package_name="openpatrol_adapter"
setup(
    name=package_name,
    version="0.2.0",
    packages=find_packages(),
    data_files=[
        ("share/ament_index/resource_index/packages",["resource/"+package_name]),
        ("share/"+package_name,["package.xml"]),
        ("share/"+package_name+"/launch",glob("launch/*.launch.py")),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="OpenPatrol maintainers",
    maintainer_email="maintainers@openpatrol.invalid",
    description="OpenPatrol ROS 2 mobility and physical-controller adapter",
    license="Apache-2.0",
    entry_points={"console_scripts":[
        "safety_adapter = openpatrol_adapter.safety_adapter:main",
        "serial_motor_bridge = openpatrol_adapter.serial_motor_bridge:main",
        "odom_tf = openpatrol_adapter.odom_tf:main",
        "virtual_lidar = openpatrol_adapter.virtual_lidar:main",
    ]},
)
