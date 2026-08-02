# AirScout Rev A

AirScout Rev A is a cost-controlled, guard-ready X-quadcopter reference for supervised warehouse inspection. It is **ready to fabricate and bench-test**, not approved for unsupervised flight or operation around the public.

## Locked envelope

- 380 mm motor-to-motor diagonal; approximately 560 mm overall with 9-inch props/guards
- target empty mass 1.35 kg; maximum take-off mass 1.85 kg
- 4S 6000 mAh LiPo; 16-minute engineering flight-time target
- four 2216-class 880-950 KV motors and 9-inch props
- independent ArduPilot/PX4 flight controller plus a small companion computer
- fixed forward camera, downward rangefinder/optical flow, GNSS only where appropriate
- removable perimeter guard segments are mandatory for indoor prototype testing

The white centre shell, charcoal arms and small navigation/status lights follow `docs/family-design-language.md`. The shell is deliberately simple: two printed/thermoformed halves around commodity carbon arms and standard motor mounts.

## Fabrication

1. Export the plates and printed parts with `./scripts/openpatrol export-hardware airscout-rev-a`.
2. Laser-cut the lower/upper centre plates and camera/battery plates from 2 mm 5052 aluminium.
3. Cut four carbon arms to 235 mm, hold all motor centres within 1 mm of the drawing and keep diagonal mismatch below 2 mm.
4. Print shell and fittings in PETG or ASA; print guard segments in tough PETG/nylon.
5. Perform a motor-by-motor direction check **without propellers**, then a restrained thrust/current test before flight.

## Software boundary

The flight controller owns attitude stabilisation, motor mixing, arming, geofence and battery/command-loss failsafes. OpenPatrol only supplies bounded 3-D velocity intent through `mavlink_velocity_adapter`; it never sends raw motor commands. The adapter stops setpoints after 500 ms and relies on the flight controller's configured hover-then-land response.

## Prototype acceptance

- frame diagonal and motor-plane measurements recorded
- motor/prop/ESC current and temperature checked on a thrust stand
- arming plug, kill channel, battery failsafe and geofence demonstrated
- tethered hover, optical-flow hold and command-loss landing demonstrated
- prop guards fitted for every indoor test
- 25 supervised flights without uncontrolled contact before autonomous route trials

Record the exact flight-controller firmware, parameter export, propeller batch, battery mass and OpenPatrol commit with every test report.
