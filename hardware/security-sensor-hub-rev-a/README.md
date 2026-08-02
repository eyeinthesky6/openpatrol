# OpenPatrol Security Sensor Hub Rev A

A low-cost fixed endpoint for bringing existing alarm contacts and local audio/visual outputs into OpenPatrol without replacing the site's cameras, NVR, access control or certified life-safety systems.

## Rev-A scope

- 8 supervised 12 V dry-contact / relay-input zones through an MCP3008 ADC
- detects normal, alarm, open-wire and short/tamper bands after site calibration
- RP2040 controller with independent local input scanning
- Ethernet or Wi-Fi Linux gateway (Raspberry Pi Zero 2 W / equivalent) running `openpatrol-sensor-hub`
- 2 isolated low-side/relay outputs for strobe and siren
- 15 W class-D speaker output for operator talkback and automatic warnings
- enclosure tamper input, status LED and local mute/service key input
- 12 V input with fused branches and a 5 V buck converter

Typical connected inputs include door contacts, PIR relays, glass-break relays, panic buttons, existing fire-panel relay outputs, pool/water alarm relays and enclosure tamper loops. **Certified fire, pool, medical and access-control systems remain independently functional; OpenPatrol consumes their dry-contact or API events and does not replace them.**

## Engineering status

The source is ready for quotation and a supervised Rev-A build. It is not certified, physically validated or suitable as the sole life-safety controller. See `drawings.md`, `wiring.md`, `protocol.md`, the firmware and the parametric CAD.

Export enclosure parts:

```bash
openscad -o sensor_hub_bottom.stl -D 'part="bottom"' cad/sensor_hub.scad
openscad -o sensor_hub_lid.stl -D 'part="lid"' cad/sensor_hub.scad
openscad -o din_plate.dxf -D 'part="din_plate"' -D 'flat=true' cad/sensor_hub.scad
```
