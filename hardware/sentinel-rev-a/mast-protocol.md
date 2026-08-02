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
- bit 7: mast position sensor invalid or outside calibrated electrical range

The hard upper/lower limits and tilt input interrupt actuator enable locally. The Pi cannot override them. An invalid position sensor stops the actuator and removes the active-low `RETRACTED_OK` confirmation. The drive controller therefore treats controller power loss, broken interlock wiring, or invalid height sensing as **mast extended/unknown** and applies the 180 mm/s wheel cap.

The reference column is mechanically self-locking or actively braked, so loss of controller power cannot allow the head to free-fall. This protocol is supervisory and cannot bypass the local hard limits, tilt interlock, or the independent retracted-confirm switch.
