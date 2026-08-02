import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class SensorHubAssetsTest(unittest.TestCase):
 def test_pack_and_ci_contract(self):
  required=[
   'hardware/security-sensor-hub-rev-a/README.md','hardware/security-sensor-hub-rev-a/BOM.csv',
   'hardware/security-sensor-hub-rev-a/wiring.md','hardware/security-sensor-hub-rev-a/protocol.md',
   'hardware/security-sensor-hub-rev-a/cad/sensor_hub.scad',
   'hardware/security-sensor-hub-rev-a/firmware/sensor_hub/sensor_hub.ino',
  ]
  for name in required:self.assertTrue((ROOT/name).is_file(),name)
  export=(ROOT/'scripts/export-hardware.sh').read_text();cad=(ROOT/'.github/workflows/hardware-cad.yml').read_text();fw=(ROOT/'.github/workflows/firmware.yml').read_text()
  self.assertIn('security-sensor-hub-rev-a',export+cad);self.assertIn('sensor_hub',fw)
 def test_firmware_has_bounded_outputs_and_supervised_states(self):
  source=(ROOT/'hardware/security-sensor-hub-rev-a/firmware/sensor_hub/sensor_hub.ino').read_text()
  for value in ('MAX_OUTPUT_MS=60000','short','alarm','normal','open','ISOLATE_PIN','stop_output'):self.assertIn(value,source)
if __name__=='__main__':unittest.main()
