# Hardware platform matrix

| Name | Form | Engineering status | Intended role |
|---|---|---|---|
| Rover One | Four-wheel skid-steer rover | Ready-to-test Rev A; physical validation pending | Robust primary indoor patrol |
| TriScout | Two drive wheels plus caster | Ready-to-test Rev A; physical validation pending | Lowest-cost smooth-floor patrol |
| AirScout | Guard-ready X quadcopter | Ready-to-test airframe/MAVLink source; flight validation pending | Short supervised aerial inspection |
| Sentinel | Four-wheel sentry, telescoping masked head | Ready-to-test chassis/mast/controller; physical validation pending | Elevated viewpoint and telepresence |
| Security Sensor Hub | Fixed 8-zone sensor/audio endpoint | Ready-to-test enclosure/electronics/firmware; validation pending | Integrate existing wired systems and local alerts |

The four mobile platforms use `visual.family: openpatrol-plain-future-v1`: warm off-white shells, charcoal structures, soft radii, dark sensor windows and restrained status lighting.

Ground platforms share bounded `/cmd_vel_safe`, odometry, watchdog and independent hardwired drive cut. Sentinel adds a separately controlled mast and a reduced speed envelope when raised. AirScout keeps stabilization, arming, geofence and failsafes inside ArduPilot/PX4.

The fixed hub is not a mobility profile. It consumes isolated relay/dry-contact signals and exposes only allow-listed speaker/strobe/siren commands. Certified systems remain independently functional.

Run:

```bash
openpatrol hardware check all
./scripts/openpatrol export-hardware all
```
