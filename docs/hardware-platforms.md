# Hardware platform matrix

OpenPatrol is software-first and mobility-agnostic. All four named platforms now have inspectable Rev-A engineering packs aligned to one industrial-design language. None has completed physical validation.

| Name | Form | Engineering status | Intended role |
|---|---|---|---|
| **OpenPatrol Rover One** | Four-wheel skid-steer rover | Ready-to-test Rev-A source; physical validation pending | Primary robust indoor patrol reference |
| **OpenPatrol TriScout** | Two drive wheels plus caster | Ready-to-test Rev-A source; physical validation pending | Lowest-cost smooth-floor reference |
| **OpenPatrol AirScout** | Guard-ready X quadcopter | Ready-to-test Rev-A airframe, power and MAVLink boundary; flight validation pending | Short supervised aerial inspection |
| **OpenPatrol Sentinel** | Four-wheel sentry with telescoping masked head | Ready-to-test Rev-A chassis, mast and controller source; physical validation pending | Higher viewpoint, telepresence and inspection |
| **OpenPatrol Humanoid Lab** | Walking humanoid | Upstream research track only | Not a patrol product |

## Shared design contract

Every platform declares `visual.family: openpatrol-plain-future-v1`. The appearance uses warm off-white non-structural shells, matte-charcoal lower structures, restrained blue/white/amber lighting and recessed black sensor windows. See `docs/family-design-language.md` and `hardware/common/cad/family_style.scad`.

The three wheeled platforms share the OpenPatrol drive safety boundary: bounded `/cmd_vel_safe`, encoder odometry, a controller watchdog, charging interlock and a normally-closed hardwired drive cut. Sentinel adds a separately controlled self-locking mast and automatically reduces the speed envelope when extended.

AirScout deliberately does **not** reuse the ground motor controller. ArduPilot or PX4 owns attitude control, motor mixing, arming, geofence and battery/command-loss failsafes. OpenPatrol sends only bounded velocity intent over the MAVROS/MAVLink boundary.

## Cost targets

| Platform | Engineering BOM | Target envelope |
|---|---:|---:|
| Rover One | ₹36,891 | ₹40,000 |
| TriScout | ₹32,499 | ₹35,000 |
| AirScout | ₹44,980 | ₹50,000 |
| Sentinel | ₹66,890 | ₹75,000 |

The figures are prototype sourcing estimates, not retail prices. Exclusions are listed inside each machine-readable profile.

## Design truth

“Ready-to-test prototype source” means a competent builder can quote, fabricate, assemble, wire and bring up Rev A without inventing the architecture. It does not mean that an unbuilt design has proven braking, thrust, thermal safety, runtime, RF reliability, sensor coverage, mast stability, docking or regulatory compliance. Those claims require fabricated units and committed acceptance data.

Run:

```bash
openpatrol hardware check all
./scripts/openpatrol export-hardware all
```
