# Reference controllers

- `safety_controller/safety_controller.ino` drives two differential sides, checks the normally-closed safety inputs, enforces a 200 ms command watchdog and applies the Sentinel mast-extended speed cap when that optional input is active.
- `../../sentinel-rev-a/firmware/mast_controller/mast_controller.ino` controls the self-locking lifting column with hard limits, tilt/drive interlocks and its own 500 ms watchdog.

These sketches are pin-level reference implementations. Builders must verify board voltage levels, encoder edge rate, motor-driver interface, isolated input polarity, relay/contact ratings, ADC scaling and actuator current before connection to a battery.
