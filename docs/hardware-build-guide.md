# Rev-A hardware build and validation guide

## Choose a baseline

- Rover One: payload and stable sensing.
- TriScout: cheapest smooth-floor build.
- AirScout: supervised aerial views only.
- Sentinel: elevated view/telepresence; mast adds failure modes.
- Security Sensor Hub: integrate existing fixed sensors and local audio/visual warnings.

Build one exact baseline before substitutions.

## Export and quote

```bash
openpatrol setup --with openscad
./scripts/openpatrol export-hardware all
```

Inspect every generated DXF/STL and critical dimension before ordering. Record the exact commit and substitutions.

## Mobile-platform acceptance

Ground: direction/encoder polarity, watchdog stop, hardwired E-stop/bumper chain, current/thermal tests, braking distances, sensor blind spots, endurance and docking.

Sentinel mast: hard limits, position calibration, command-loss stop, self-locking hold, tilt/docking interlocks, sway/tip margin, reduced-speed braking and 500 extension cycles.

AirScout: motor order/direction, thrust/current/temperature, reviewed PX4/ArduPilot parameters, kill/geofence/battery/command-loss failsafes, tethered hover and at least 25 supervised flights.

## Sensor-hub acceptance

1. Verify fused 12 V and 5 V branches and service isolation.
2. Calibrate normal/alarm/open/short bands for every installed EOL loop.
3. Prove connected certified panels remain operational when OpenPatrol is powered off.
4. Exercise every input 100 times and verify zone/event mapping.
5. Verify strobe/siren duration caps and physical output-isolate override.
6. Verify speaker intelligibility and maximum sound level for the site.
7. Test network loss, gateway restart, duplicate events and command acknowledgements.
8. Run a 72-hour supervised soak test without false electrical tamper/alarm events.

A missing or failed measurement blocks field deployment.
