# Shared fabrication and controller rules

All four Rev-A platforms use `openpatrol-plain-future-v1`, defined in `cad/family_style.scad` and `docs/family-design-language.md`. The ground platforms share payload grids, compute conventions, sensor treatments, safety loops and ROS topic contracts where practical. AirScout shares appearance and evidence interfaces, but keeps flight-critical control inside its qualified autopilot.

Critical rules:

- M4 structural fasteners and M3 electronics are the default; use slotted holes only to absorb documented supplier variation.
- Keep ground-platform batteries low and inside the wheel polygon.
- Keep AirScout's centre of gravity at the thrust centre and verify every substituted motor/prop/ESC combination.
- No Dupont wires in drive, mast, flight-power or safety harnesses.
- A normally-closed ground safety chain removes drive power independently of Linux and firmware.
- The reference ground controller adds CRC-checked commands and a 200 ms watchdog, secondary to the hardwired relay loop.
- Sentinel's mast uses a separate controller, hard limits, position feedback, tilt interlock and a self-locking/braked column.
- AirScout's autopilot owns arming, attitude, motor mixing, geofence and failsafes; OpenPatrol never commands raw motors.
- Export CAD with `./scripts/openpatrol export-hardware all` and inspect every output before fabrication.
