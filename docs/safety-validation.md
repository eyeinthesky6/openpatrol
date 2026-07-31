# Physical safety validation protocol

Do not run these tests around uninvolved people. Use a marked exclusion zone, a spotter and a tether/lift fixture for first motion.

## Recorded configuration

Record robot mass and payload, centre-of-gravity height, wheel/tyre, floor, battery voltage, speed and acceleration limits, controller firmware, watchdog value, sensor versions and test operator.

## Required tests

1. With wheels lifted, remove command traffic. Drive torque must disappear within the controller's measured 250 ms deadline.
2. At each configured speed and maximum payload, activate the physical E-stop ten times. Record response and stopping distance; no trial may exceed the declared envelope.
3. Open each normally-closed bumper/stop-chain element and disconnect the application computer. Neither condition may leave drive torque enabled.
4. Place representative matte, dark, reflective and glass obstacles. Validate collision monitoring at approach angles and minimum detectable height.
5. Introduce localization loss, stale odometry, low battery, overtemperature and charger-connected states. Each must enter its documented safe state.
6. Run 25 autonomous hours before docking experiments: zero contact, every intervention recorded.
7. Run at least 100 dock attempts from the declared capture region. Success must be ≥95%; charger polarity, temperature and drive interlock must remain safe.

The software clearance model is `v × latency + v²/(2a) + margin + localization error + obstacle error`. Measure actual deceleration; never substitute a motor brochure value. At the default 0.5 m/s, 1.0 m/s² measured deceleration, 250 ms latency and 0.1 m margin, base stopping distance is 0.35 m before perception/localization uncertainty.
