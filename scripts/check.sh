#!/bin/sh
set -eu
python3 -m compileall -q openpatrol tests
python3 -m unittest discover -s tests -v
for schema in schemas/*.json;do python3 -m json.tool "$schema" >/dev/null;done
python3 -m compileall -q ros2/openpatrol_adapter/openpatrol_adapter ros2/openpatrol_simulation/launch
python3 -m py_compile scripts/ros_gazebo_smoke.py
python3 -m openpatrol.hardware_harness >/dev/null
if command -v node >/dev/null 2>&1;then node --check static/app.js;fi
bash -n scripts/openpatrol scripts/export-hardware.sh
