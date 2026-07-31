import unittest
from openpatrol.safety import StopEnvelope
class SafetyMathTest(unittest.TestCase):
    def test_stop_distance_includes_latency_braking_and_margin(self): self.assertAlmostEqual(.35,StopEnvelope(.5,1.0,250,.1).distance_m(),places=6)
    def test_clearance_adds_sensor_uncertainty(self): self.assertAlmostEqual(.55,StopEnvelope(.5,1.0,250,.1).required_clearance_m(.1,.1),places=6)
    def test_rejects_impossible_deceleration(self):
        with self.assertRaises(ValueError): StopEnvelope(.5,0,250).distance_m()
if __name__=="__main__": unittest.main()
