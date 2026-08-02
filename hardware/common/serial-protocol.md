# Safety-controller serial protocol

The Pi and reference RP2040/ESP32 controller communicate over USB serial at 115200 baud. This is a convenience and observability link—not the physical safety chain. E-stop, bumper loop, charger interlock and drive relay remain a hardwired, normally-closed chain.

## Frames

ASCII frames end in newline and carry CRC16-CCITT over the payload between `$` and `*`.

```text
$C,sequence,left_mm_s,right_mm_s,enable*CCCC
$S,sequence,left_ticks,right_ticks,battery_mv,flags*CCCC
```

Commands are sent every 20 ms. The controller disables PWM and drops its secondary enable output when no valid, enabled command arrives within 200 ms. The hardwired stop loop must de-energize the drive relay independently.

Status flags:

- bit 0: E-stop input open
- bit 1: NC bumper/stop loop open
- bit 2: command watchdog timed out
- bit 3: motor-driver fault
- bit 4: charger connected

Encoder counts are signed wrapping 32-bit cumulative counts, averaged per side on Rover One. `encoder_counts_per_rev` means counts per **wheel** revolution after gearbox and quadrature decoding; measure it on the assembled unit.

## ROS bridge

Build the ROS 2 workspace and run:

```bash
ros2 launch openpatrol_adapter physical_rover.launch.py serial_port:=/dev/ttyACM0
```

Rover One defaults are 0.05 m radius, 0.34 m track and 0.45 m/s. For TriScout override `wheel_track_m:=0.30 max_wheel_speed_mps:=0.42`. Replace the placeholder encoder count after a measured wheel-revolution calibration.

The firmware is compiled on every pull request through `.github/workflows/firmware.yml`; this catches source/toolchain breakage but does not replace pin-by-pin bench validation on the selected controller board.
