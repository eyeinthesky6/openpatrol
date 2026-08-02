# Sentinel Rev A

Sentinel Rev A is the tall member of the OpenPatrol family: a cost-aware four-wheel patrol base, simple ABS torso and a **masked sensor head on a motorised telescoping mast**. The head reaches 1.50 m at full extension and retracts to a 0.98 m sensor height for movement, docking and transport.

This pack is ready for fabrication and supervised prototype testing. It is not a field-certified public-space robot.

## Locked envelope

- 460 x 400 mm footprint; 125 mm rubber wheels
- 0.38 m/s normal speed; hard software/controller cap of 0.18 m/s while the mast is extended
- 12.8 V 20 Ah LiFePO4 power system
- 24 V self-locking lifting column, 520 mm travel, upper and lower hard limits
- masked 190 x 110 x 85 mm head with dual camera behind smoked polycarbonate
- fixed 2D lidar on the torso roof so navigation does not depend on the moving mast
- optional pico projector reserved behind the visor, but excluded from the baseline BOM

## Why the mast is separate

The drive and mast use separate controllers and separate fused power branches. A mast fault must not remove the drive safety controller, and a Linux/ROS crash must stop both actuators through their local watchdogs. The mast controller exposes an `extended` interlock to the drive controller, which applies the reduced wheel-speed cap independently of the Pi.

## Fabrication

1. Export parts with `./scripts/openpatrol export-hardware sentinel-rev-a`.
2. Build and test the rolling base before fitting the torso or mast.
3. Square the torso extrusion frame within 1 mm and mount the lifting column directly to the aluminium mast plate—not to plastic covers.
4. Fit the energy chain and cycle the mast by hand/low current before installing the head.
5. Keep the finished head below 2.5 kg and record the measured mass and cable pull at every 100 mm of travel.

## Safety and anti-tamper compromise

The prototype has no prominent front mushroom button. A guarded rear service stop remains reachable by trained test staff, while the operator uses a dedicated wireless safety pendant. The rear stop, bumper loop, tilt switch, charger interlock and drive relay are hardwired; hiding safety behind software would be theatre, not engineering.

## Prototype acceptance

- drive base passes the Rover-style wheels-up, stop-loop, thermal and braking tests
- mast hard limits stop travel without ROS or the Pi
- mast holds position with power removed and does not back-drive
- drive speed remains <=0.18 m/s above the extension threshold
- tilt input stops mast and drive; extended static and dynamic tip tests are recorded
- 500 full mast cycles plus 25 autonomous patrol hours without cable snag, uncontrolled motion or contact
- docking is permitted only with the mast confirmed retracted
