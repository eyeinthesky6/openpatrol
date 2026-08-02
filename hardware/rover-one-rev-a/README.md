# Rover One Rev A engineering pack

Rover One is the primary OpenPatrol reference platform: four 100 mm rubber wheels, four low-cost 12 V gearmotors paired by side, a low battery tray, removable electronics deck and simple ABS cover. The design favours common fabrication processes over decorative complexity.

## Design envelope

- Overall: 440 × 380 × 245 mm including wheels and lidar plate.
- Target empty mass: 10.5 kg; payload: 5 kg; maximum total: 17 kg.
- Design speed: 0.45 m/s; software and controller hard cap: 0.5 m/s.
- Battery: 12.8 V 12 Ah LiFePO4; target mixed-duty runtime about 3.4 hours.
- Structural parts: two 3 mm 5052 aluminium plates. Prototype alternative: 6 mm HDPE or birch plywood.
- Cover: 2 mm ABS. It protects wiring; it is not a structural or weatherproof enclosure.

## Fabrication

1. Install OpenSCAD and run `./scripts/openpatrol export-hardware rover-one-rev-a`.
2. Laser-cut `lower_deck.dxf`, `upper_deck.dxf`, `cover_top.dxf`, two `cover_side.dxf` panels and `lidar_plate.dxf`.
3. Print four motor saddles, four corner blocks, one camera bracket and cable guides in PETG/ASA.
4. Deburr all metal, add edge protection around cable apertures and dry-assemble before wiring.
5. Keep motor and battery mass below the upper deck. Do not place the battery on the payload plate.

## Assembly order

Lower deck → motor saddles and wheels → bumper switches → battery tray and fused harness → upper-deck standoffs → motor driver and safety controller → Pi and DC-DC → lidar/camera → ABS cover → E-stop and beacon.

The CAD provides adjustable slots, not wishful exactness: normal 36–38 mm motor bodies, 45–90 mm battery widths and common driver boards fit without drilling the structural plate. Any substitution outside those ranges requires a profile revision.

## Software compatibility

The matching profile is bundled as `rover-one-rev-a`. Run:

```bash
openpatrol hardware check rover-one-rev-a
```

The ROS boundary is `/cmd_vel_safe`, `/odom`, `/scan`, `/battery_state` and `/hardware/estop`. The safety microcontroller must stop the driver when fresh commands disappear for 250 ms. The Linux adapter is supervisory and cannot be the only stop mechanism.

## Release boundary

This is a complete engineering release for quotation, cutting, printing and assembly. It is **not field-certified**. Do not call a build production-ready until the fabricated unit passes `docs/safety-validation.md`, measured braking, thermal, endurance and docking tests and the results are committed against the exact BOM revision.
