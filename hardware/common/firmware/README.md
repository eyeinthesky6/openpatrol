# Reference safety-controller firmware

The `safety_controller/` sketch targets the official Arduino RP2040 core and is compiled in GitHub Actions for a Raspberry Pi Pico. The implementation is in the adjacent `safety_controller.ino` so the complete control and safety logic remains visible without generated code.

It implements:

- CRC-checked USB serial commands from the ROS bridge
- 200 ms command watchdog
- differential left/right velocity control using encoder feedback
- secondary driver enable and PWM/direction outputs
- cumulative encoder, battery and safety-state reporting

Compile locally with:

```bash
arduino-cli core update-index
arduino-cli core install arduino:mbed_rp2040
arduino-cli compile --fqbn arduino:mbed_rp2040:pico hardware/common/firmware/safety_controller
```

Before upload, set the board-specific pin map, encoder counts per wheel revolution, battery-divider calibration, motor polarity and conservative PID/feed-forward constants. The sketch cannot certify a motor or battery and is not the sole safety device.

The normally-closed E-stop/bumper/charger loop must directly de-energize the drive relay. The firmware reads an isolated feedback contact and refuses drive when it is open.
