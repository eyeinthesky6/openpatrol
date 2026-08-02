# Security Sensor Hub Rev A bring-up

The hub is the inexpensive bridge for sites whose useful signals already exist as relay contacts rather than APIs.

1. Build the enclosure/electronics from `hardware/security-sensor-hub-rev-a/`.
2. Connect only isolated dry contacts or listed interface relays.
3. Calibrate each supervised-loop voltage band in firmware.
4. Flash the RP2040 firmware and verify serial heartbeat/events.
5. Install the optional bridge extra:

```bash
pipx install 'openpatrol[sensor] @ git+https://github.com/eyeinthesky6/openpatrol.git'
OPENPATROL_INGEST_TOKEN=... OPENPATROL_DEVICE_ID=sensor-hub-1 \
  openpatrol-sensor-hub --port /dev/ttyACM0
```

6. Register the gateway as a `sensor_hub` device with `sensors`, `speaker`, `strobe` and/or `siren` capabilities.
7. Test normal, alarm, open-wire and short states for every loop.
8. Test the physical output-isolate switch before enabling operator or automatic output policy.

The hub is a prototype integration endpoint, not a certified alarm or life-safety panel.
