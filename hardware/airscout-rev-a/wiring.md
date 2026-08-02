# AirScout Rev A wiring and control boundary

## Power tree

`4S LiPo + -> removable XT60 arming plug -> 60 A fuse -> 4-in-1 ESC`.

A separately fused branch feeds the 5.1 V BEC, flight controller, companion computer, camera and telemetry. Grounds meet at the power-distribution star point; do not route motor current through the flight-controller ground path.

## Control ownership

- Flight controller: motor outputs, attitude loop, arming state, geofence, RC/GCS loss and battery failsafes.
- Companion computer: camera/telemetry and bounded OpenPatrol velocity-intent adapter.
- OpenPatrol: mission intent and evidence handling. It does **not** bypass the flight controller.

The dedicated RC/GCS kill channel and removable arming plug must remain effective if the companion computer crashes or is unplugged.

## Harness rules

- Twist motor phase wires and keep them away from GNSS/compass wiring.
- Put the GNSS/compass on the printed mast above high-current conductors.
- Use a low-ESR capacitor at the ESC input.
- Strain-relieve every arm harness and allow enough loop for an arm replacement.
- Fit a visible buzzer and front/rear navigation LEDs independent of the video stream.

## Bring-up order

1. Continuity and polarity check with the battery disconnected.
2. Power the flight controller from a current-limited bench supply.
3. Verify sensor orientation and failsafe inputs.
4. Verify each motor and direction without propellers.
5. Fit props only for restrained thrust and then tethered hover tests.
