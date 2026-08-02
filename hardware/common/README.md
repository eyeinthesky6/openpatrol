# Shared fabrication rules

Both Rev-A platforms use the same payload grid, compute tray, lidar mast, camera bracket, safety loop and software topic contract. Structural plates may be laser-cut from 3 mm 5052 aluminium for the field build or 6 mm HDPE/birch plywood for a low-cost prototype. Covers are non-structural 2 mm ABS sheet fixed to printed corner blocks.

Critical rules:

- M4 structural fasteners; M3 electronics; slotted holes absorb normal supplier variation.
- Keep the battery below the wheel axle and inside the wheel polygon.
- No Dupont wires in the drive or safety harness.
- The normally-closed E-stop loop removes motor-driver enable independently of Linux.
- Export CAD with `./scripts/openpatrol export-hardware all`; inspect every DXF before fabrication.
