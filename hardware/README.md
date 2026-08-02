# OpenPatrol hardware

OpenPatrol now contains two complete, low-cost Rev-A engineering packs:

| Platform | Use | Engineering BOM | Source |
|---|---|---:|---|
| **Rover One Rev A** | Primary four-wheel indoor patrol base; 5 kg payload | about ₹36,900 | `rover-one-rev-a/` |
| **TriScout Rev A** | Simpler two-wheel/caster base; 3 kg payload | about ₹32,500 | `triscout-rev-a/` |

Each pack contains parametric OpenSCAD, flat-sheet DXF export targets, printable brackets, BOM, wiring/stop-chain specification, assembly order and a machine-readable software compatibility profile. Run `./scripts/openpatrol export-hardware all` to generate fabrication files.

The two designs deliberately share the compute tray, lidar plate, motor family, motor driver, safety controller, camera bracket, power architecture and ROS topic contract. This lowers inventory, assembly effort and software variance.

## What “engineering release” means

The files are dimensioned for quotation, cutting, printing and assembly. They are **not a physical test certificate**. Supplier variation, actual mass, centre of gravity, motor current, tyre grip, braking, thermal performance, sensor blind spots, charger behaviour and ingress protection must be measured on the first fabricated units. Until those results are committed, the profiles remain `engineering-release-unvalidated`.

The AI-generated README images remain concept illustrations. Rover One and TriScout CAD are original OpenPatrol source intended for CERN-OHL-P-2.0 distribution; the software is Apache-2.0.
