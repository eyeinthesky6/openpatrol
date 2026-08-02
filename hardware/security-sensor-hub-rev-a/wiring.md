# Wiring and power boundary

## Power

1. 12 V DC enters through a 3 A fuse and service disconnect.
2. One fused branch feeds the speaker amplifier, strobe and siren outputs.
3. A 5 V/3 A buck feeds the Linux gateway and RP2040; the RP2040 3.3 V rail feeds the MCP3008.
4. Keep speaker/siren return currents separate from ADC ground until the power-entry star point.

## Supervised zones

Each field loop uses a site-selected end-of-line resistor; the Rev-A baseline is 4.7 kΩ at the far end with a protected 10 kΩ pull-up and 1 kΩ series input. The MCP3008 measures eight channels. Firmware thresholds must be calibrated from real measured voltages for:

- normal/secure
- alarm/contact active
- open wire
- short/tamper

Do not connect mains, powered fire circuits or proprietary panel buses directly. Use a listed isolated relay/module supplied by that system.

## Outputs

- OUT1: visual strobe
- OUT2: siren
- speaker amplifier: line/audio output from Linux gateway

Local service isolation must prevent software from energising siren/strobe during maintenance. The enclosure tamper loop is always reported even when outputs are isolated.
