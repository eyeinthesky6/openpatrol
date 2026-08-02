# Rover One Rev A wiring

## Power tree

`Battery + → 25 A main fuse → keyed isolator → split bus`.

- Drive branch: 20 A fuse → normally-open 30 A drive relay → MDD10A motor supply → left motor pair/right motor pair.
- Compute branch: 7.5 A fuse → 5.1 V 6 A protected DC-DC → Raspberry Pi, powered USB hub if required and lidar.
- Control branch: 2 A fuse → safety controller, relay coil, bumper loop and beacon.

Battery negative returns to one star point. Bond an aluminium chassis to protective ground only when the selected charger/site architecture requires it; do not improvise mains grounding.

## Normally-closed stop loop

Keyed enable → E-stop NC contact → front bumper NC → rear bumper NC → left/right side NC → safety-controller watchdog relay NC → charger interlock NC → drive-relay coil. Opening any element removes motor power. A second E-stop contact enters the controller as `/hardware/estop` feedback.

## Controller I/O

- Inputs: four encoder pairs, E-stop feedback, four bumper states, charger present, battery voltage/current and motor-driver fault.
- Outputs: left/right PWM and direction, driver enable, relay coil supervision and drive-enabled beacon.
- USB/UART to Pi: measured wheel ticks, battery state and safety status. The controller rejects commands older than 250 ms.

Use ferrules or locking connectors, strain relief and labelled wire. Keep encoder/camera wiring away from motor leads; twist motor pairs and add suppression at the motor terminals if required by testing.
