# OpenPatrol hardware

OpenPatrol contains four Rev-A prototype engineering packs aligned to the same visual and software family.

| Platform | Use | Engineering BOM | Source |
|---|---|---:|---|
| **Rover One Rev A** | Robust four-wheel indoor patrol base; 5 kg payload | ₹36,891 | `rover-one-rev-a/` |
| **TriScout Rev A** | Simpler two-wheel/caster base; 3 kg payload | ₹32,499 | `triscout-rev-a/` |
| **AirScout Rev A** | Guard-ready supervised inspection quadcopter; 0.35 kg payload | ₹44,980 | `airscout-rev-a/` |
| **Sentinel Rev A** | Four-wheel elevated-view sentry with 1.5 m telescoping masked head | ₹66,890 | `sentinel-rev-a/` |

Each pack contains parametric OpenSCAD, fabrication/export targets, BOM, wiring, assembly guidance and a machine-readable software compatibility profile. Sentinel additionally contains a mast protocol and controller firmware. Run `./scripts/openpatrol export-hardware all` to generate DXF/STL/preview artifacts.

## Shared family

`common/cad/family_style.scad` defines the exterior modules and colour/material contract used by all four platforms. Rover One and TriScout retain their proven flat-sheet structural files and add family-style exterior preview sources; AirScout and Sentinel use the family modules directly.

The ground platforms share a CRC-checked drive protocol and independent normally-closed safety loop. AirScout uses an independent ArduPilot/PX4 flight controller and a bounded MAVLink velocity adapter instead of reusing ground-drive firmware.

## What “engineering release” means

The files are dimensioned and connected well enough for quotation, fabrication, assembly and prototype bring-up. They are **not physical test certificates**. Supplier variation, mass, centre of gravity, motor current, tyre grip, thrust margin, braking, mast stability, thermal performance, sensor blind spots, RF behaviour, charger behaviour and ingress protection must be measured on fabricated units. Until results are committed, every profile remains `engineering-release-unvalidated`.

The README visuals communicate the intended exterior and are aligned to `docs/family-design-language.md`; CAD, profiles, BOMs and wiring remain the engineering source of truth.
