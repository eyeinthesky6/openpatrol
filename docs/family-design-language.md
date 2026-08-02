# OpenPatrol family design language

`openpatrol-plain-future-v1` is the shared industrial-design contract for Rover One, TriScout, AirScout and Sentinel. It turns the marketing direction into reviewable geometry and fabrication rules instead of treating appearance as a separate illustration exercise.

## Character

- plain, calm and slightly futuristic rather than aggressive or theatrical
- broad soft radii, simple serviceable panels and visible but tidy seams
- warm off-white upper shells over matte-charcoal structural or drive sections
- black rubber wheels or charcoal flight arms
- one restrained blue system-status light, white forward lights and small amber side markers
- compact black sensor windows; no fake vents, decorative armour or jagged surfaces
- antennas only where a real radio requires one; their locations remain within the declared envelope

The visual modules live in `hardware/common/cad/family_style.scad`. The Rover One and TriScout family-preview files use those modules, while their original flat-sheet fabrication source remains the dimensional authority. AirScout and Sentinel use the same modules directly in their engineering CAD.

## Exterior construction

The Rev-A appearance is designed around low-volume manufacturing:

1. laser-cut aluminium, HDPE or carbon structural parts
2. PETG/ASA printed corner blocks, bezels and local brackets
3. 2 mm ABS sheet or printed two-piece shells for non-structural covers
4. replaceable smoked polycarbonate sensor masks
5. commodity LED modules behind printed or machined diffusers

No surface requires injection moulding. A competent fabricator may thermoform or heat-bend the ABS shell, but must not alter wheel clearance, propeller clearance, sensor fields of view, service access or cooling openings.

## Family identifiers

| Element | Ground platforms | AirScout | Sentinel-specific |
|---|---|---|---|
| upper colour | warm off-white | warm off-white centre shell | warm off-white torso and head housing |
| lower colour | matte charcoal | charcoal arms/tray | charcoal base and mast |
| sensor treatment | black recessed camera bar, lidar puck | black camera chin | black masked visor on telescoping mast |
| system status | blue short light or lidar ring | blue system light plus red/green navigation | blue vertical torso light |
| safety/marker lighting | white forward, amber side | flight-controller navigation convention | white forward, amber side |

## Source-of-truth hierarchy

1. The platform JSON profile defines the operating envelope, mass, power, safety and software interfaces.
2. The platform CAD defines fabrication dimensions and part geometry.
3. The BOM and wiring document define the baseline components and connections.
4. Generated assembly previews and README images communicate the intended exterior.
5. A physical build report is required before any performance or safety claim becomes validated.

Marketing renders are not allowed to add actuators, sensors, wheels, propellers or mast travel that do not exist in the corresponding profile and CAD. Internal component substitutions are allowed when the envelope, centre of gravity, cooling, electrical ratings and software contract remain inside the baseline.

## Service and safety details

- Service fasteners should be captive where practical and accessible without removing the drivetrain.
- The public-facing exterior must not expose a casual pushbutton that silently defeats the robot. Ground platforms retain a guarded/recessed service stop and a separate supervised wireless safety pendant for testing.
- Safety stops remain independent of Linux and the browser.
- Sentinel must retract its mast before docking and before transport.
- AirScout propeller guards are mandatory for indoor prototype tests.

The family is an engineering-source-aligned **ready-to-test prototype design**, not a certified commercial robot line.
