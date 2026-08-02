# TriScout Rev A engineering pack

TriScout is the lower-cost indoor reference: two driven 100 mm rubber wheels, one 75 mm swivel caster and the same compute/lidar payload used by Rover One. It is easier to fabricate and tune, but carries less payload and handles thresholds less gracefully.

## Design envelope

- Overall: 390 × 340 × 230 mm.
- Target empty mass: 8 kg; payload: 3 kg; maximum total: 12 kg.
- Design speed: 0.42 m/s; software hard cap: 0.5 m/s.
- Battery: 12.8 V 8 Ah LiFePO4; target mixed-duty runtime about 2.7 hours.
- Structural parts: two 3 mm 5052 aluminium plates; 6 mm HDPE/birch prototype alternative.
- Cover: removable 2 mm ABS panels.

## Fabrication and assembly

Run `./scripts/openpatrol export-hardware triscout-rev-a`, laser-cut the deck and cover files, and print four motor saddles plus corner blocks. Assemble the two motors first, then set caster height so the lower deck is level under expected payload. Battery, motor driver and main fuse remain below the upper deck; Pi, safety controller and sensor wiring remain above it.

The caster holes are slotted for common 45 × 30 mm patterns. Reject a caster with visible swivel play, a hard plastic wheel or a load rating below the complete robot mass.

## Software compatibility

```bash
openpatrol hardware check triscout-rev-a
```

The profile uses the same OpenPatrol ROS topic contract as Rover One. Set the physical wheel separation and encoder scale from measurements, not CAD alone. Verify straight-line drift, angular scale and stop latency before enabling Nav2 patrol.

## Release boundary

The files are buildable and quote-ready, but no physical unit has yet passed the safety protocol. Physical evidence—not a render, simulator or checklist with empty boxes—is required before field deployment.
