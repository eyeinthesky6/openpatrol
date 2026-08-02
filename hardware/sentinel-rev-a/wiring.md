# Sentinel Rev A wiring and interlocks

## Power tree

`Battery + -> 40 A main fuse -> keyed isolator -> split bus`.

- Drive: 25 A fuse -> normally-open drive relay -> motor driver -> four motors.
- Compute: 10 A fuse -> 5.1 V 6 A DC-DC -> Pi, lidar, camera, audio and USB controllers.
- Mast: 10 A fuse -> isolated 24 V converter -> mast H-bridge/lifting column.
- Charge: interlocked connector; charger presence opens the drive and mast enable chain.

## Normally-closed safety chain

Rear guarded service stop, front/rear bumper switches, charger interlock and drive-controller watchdog must de-energise the drive relay independently of the Pi. The mast has its own upper/lower hard limits and tilt input. A wireless safety pendant opens the same relay chain; it is not a software command.

## Controller links

- Drive controller: USB serial, `$C`/`$S` frames from the common OpenPatrol protocol.
- Mast controller: separate USB serial, `$M`/`$T` frames from `mast-protocol.md`.
- Drive `MOVING` output is wired into the mast controller; mast motion is inhibited whenever the drive is above creep threshold.
- The drive controller's `MAST_RETRACTED_OK` input is pulled high locally. It reaches ground only through **both** an independent normally-closed retracted-confirm switch and an isolated open-collector output from the healthy mast controller. Any open wire, controller power loss, invalid position sensor, raised mast, or failed switch therefore reads extended/unknown and applies the 180 mm/s wheel cap.
- Rover One and TriScout, which have no mast, use a labelled supervised ground jumper at `MAST_RETRACTED_OK`; leaving that jumper open deliberately applies the conservative creep cap.

## Head harness

Use a flexible energy chain with separate twisted power and data paths. Provide 20 percent spare loop at full extension, strain relief at both ends and a service connector below the head. The optional projector connector remains capped when not fitted.
