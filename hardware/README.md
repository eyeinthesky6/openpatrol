# OpenPatrol hardware

OpenPatrol contains four coordinated mobile Rev-A engineering packs and one fixed security/audio hub.

| Platform | Use | Engineering BOM | Source |
|---|---|---:|---|
| Rover One Rev A | Robust four-wheel indoor patrol base | ₹36,891 | `rover-one-rev-a/` |
| TriScout Rev A | Simpler two-wheel/caster base | ₹32,499 | `triscout-rev-a/` |
| AirScout Rev A | Guard-ready supervised inspection quadcopter | ₹44,980 | `airscout-rev-a/` |
| Sentinel Rev A | Elevated-view sentry with 1.5 m telescoping masked head | ₹66,890 | `sentinel-rev-a/` |
| Security Sensor Hub Rev A | 8 wired zones, speaker, strobe and siren endpoint | ₹8,700 | `security-sensor-hub-rev-a/` |

The mobile packs include parametric CAD, fabrication targets, BOM, wiring, assembly guidance and software compatibility profiles. Sentinel adds mast firmware/protocol. The fixed hub adds supervised-loop electronics, endpoint outputs, enclosure CAD and RP2040 firmware.

All share the same command-centre contracts: observations enter `POST /api/v1/security-events`; compatible output endpoints poll an allow-listed device-command queue.

## Engineering-release meaning

A competent builder can quote, fabricate, wire and bring up Rev A without inventing the architecture. None of these packs is physically validated or certified. Supplier variation, mass, stopping, thrust, thermal performance, mast stability, loop calibration, acoustics, ingress protection and site-specific AI performance must be measured before deployment.
