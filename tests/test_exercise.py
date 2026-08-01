import tempfile,unittest
from pathlib import Path
from openpatrol.exercise import run_exercise
class ExerciseTest(unittest.TestCase):
    def test_accelerated_operational_exercise_passes(self):
        with tempfile.TemporaryDirectory() as directory:
            report=run_exercise(ticks=25000,tick_seconds=.4,workdir=Path(directory))
            self.assertEqual("pass",report["result"]); self.assertGreater(report["metrics"]["laps"],0); self.assertTrue(all(report["checks"].values()))
if __name__=="__main__": unittest.main()
