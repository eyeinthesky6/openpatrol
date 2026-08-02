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
- Mast `EXTENDED` output is wired into the Sentinel drive controller's speed-cap input.
- Drive `MOVING` output is wired into the mast controller; extension is inhibited above creep speed.

## Head harness

Use a flexible energy chain with separate twisted power and data paths. Provide 20 percent spare loop at full extension, strain relief at both ends and a service connector below the head. The optional projector connector remains capped when not fitted.
