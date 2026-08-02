import runpy
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = runpy.run_path(
    str(ROOT / "ros2/openpatrol_adapter/openpatrol_adapter/flight_contract.py")
)
velocity_publish_decision = CONTRACT["velocity_publish_decision"]


class FlightContractTest(unittest.TestCase):
    def test_active_command_streams(self):
        decision = velocity_publish_decision(
            authorized=True, command_age_s=0.1, stale_s=0.5, was_streaming=False
        )
        self.assertTrue(decision.publish)
        self.assertFalse(decision.zero)
        self.assertTrue(decision.streaming)
        self.assertEqual("active", decision.reason)

    def test_authorization_loss_publishes_one_zero_then_goes_silent(self):
        falling_edge = velocity_publish_decision(
            authorized=False, command_age_s=0.1, stale_s=0.5, was_streaming=True
        )
        self.assertTrue(falling_edge.publish)
        self.assertTrue(falling_edge.zero)
        self.assertFalse(falling_edge.streaming)
        self.assertEqual("not_authorized", falling_edge.reason)

        silent = velocity_publish_decision(
            authorized=False, command_age_s=0.2, stale_s=0.5, was_streaming=False
        )
        self.assertFalse(silent.publish)
        self.assertFalse(silent.streaming)

    def test_stale_command_hands_control_to_autopilot(self):
        decision = velocity_publish_decision(
            authorized=True, command_age_s=0.6, stale_s=0.5, was_streaming=True
        )
        self.assertTrue(decision.publish)
        self.assertTrue(decision.zero)
        self.assertFalse(decision.streaming)
        self.assertEqual("command_stale", decision.reason)

    def test_invalid_time_contract_is_rejected(self):
        with self.assertRaises(ValueError):
            velocity_publish_decision(
                authorized=True, command_age_s=-0.1, stale_s=0.5, was_streaming=False
            )
        with self.assertRaises(ValueError):
            velocity_publish_decision(
                authorized=True, command_age_s=0.1, stale_s=0.0, was_streaming=False
            )


if __name__ == "__main__":
    unittest.main()
