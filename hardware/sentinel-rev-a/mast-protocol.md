# Sentinel mast-controller protocol

USB serial is 115200 baud. Frames use the same CRC16-CCITT framing as the drive controller.

```text
$M,sequence,target_mm,enable*CCCC
$T,sequence,height_mm,flags*CCCC
```

`target_mm` is absolute sensor-head height from the floor, clamped to 980-1500 mm. Commands are refreshed at 20 Hz. The mast stops after 500 ms without a valid enabled frame.

Flags:

- bit 0: lower limit active
- bit 1: upper limit active
- bit 2: command timeout
- bit 3: tilt interlock active
- bit 4: actuator fault/over-current
- bit 5: drive-moving interlock active
- bit 6: mast above extended-speed threshold

The hard upper/lower limits and tilt input interrupt actuator enable locally. The Pi cannot override them.

The reference column is mechanically self-locking or actively braked, so loss of controller power cannot allow the head to free-fall. This protocol is supervisory and cannot bypass the local hard limits or tilt interlock.
