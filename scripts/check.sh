#!/bin/sh
set -eu
python3 -m compileall -q openpatrol tests
python3 -m unittest discover -s tests -v
python3 -m json.tool schemas/detection-v1.schema.json >/dev/null
python3 -m json.tool schemas/evidence-v2.schema.json >/dev/null
python3 -m compileall -q ros2/openpatrol_adapter/openpatrol_adapter
python3 -m compileall -q ros2/openpatrol_simulation/launch
python3 -m openpatrol.hardware_harness >/dev/null
