# Production-like digital-twin exercise

Run an accelerated eight-hour shift:

```bash
python3 -m openpatrol.exercise --ticks 72000 --tick-seconds 0.4 --output runtime/exercise-report.json
```

The exercise starts from isolated state, patrols at the 0.5 m/s indoor limit, creates scenario incidents, injects Frigate-style person detections, triggers E-stops and localization faults, checks that position freezes, clears faults, returns for low-battery charging, resumes the shift, simulates a process restart, reviews every incident and verifies all evidence signatures and audit links.

A passing report requires safe-state immobility, safe restart, valid signed receipts, valid audit chain, bounded battery, route progress, external detector coverage and a distance compatible with speed × time. The report is evidence about deterministic software behavior—not proof that motors, LiDAR, cameras, Wi-Fi or a physical dock work.

For interactive fault testing, start Mission Control and send authenticated simulation commands `inject-localization-fault`, `inject-drive-fault`, and `clear-fault` to `/api/v1/commands`. Never expose these simulation-only controls through a physical mobility adapter.
