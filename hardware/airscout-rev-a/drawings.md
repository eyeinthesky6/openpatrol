# AirScout Rev-A critical drawing schedule

All dimensions are millimetres unless noted. The OpenSCAD source is parametric; generated DXF/STL files must be checked against this schedule before release to a vendor.

## Datums

- **A:** lower centre plate top face
- **B:** longitudinal centreline through front/rear motor centres
- **C:** lateral centreline through left/right motor centres
- **D:** motor thrust plane

## Locked dimensions

| Feature | Nominal | Prototype tolerance |
|---|---:|---:|
| motor-to-motor diagonal | 380 | ±1.0 |
| mismatch between diagonals | 0 | ≤2.0 |
| motor plane coplanarity | 0 | ≤0.8 |
| lower centre plate | 170 × 150 × 2 | ±0.3 cut; ±0.1 thickness |
| upper centre plate | 155 × 135 × 2 | ±0.3 cut |
| carbon arm section | 20 × 20 × 1.5 | supplier tolerance; record actual |
| carbon arm cut length | 235 | ±0.5 |
| propeller diameter | 9 in / 228.6 | supplier controlled |
| minimum adjacent prop-tip gap | 35 | no negative tolerance below 30 |
| battery tray usable envelope | 145 × 58 | verify chosen pack and straps |
| flight-controller hole pattern | 30.5 × 30.5 | ±0.2 |
| target CG offset from thrust centre | 0 | ≤5 each axis |

## Assembly controls

- Use a flat fixture through all four motor mounts while tightening arm clamps.
- Measure both diagonals after final torque and after the first restrained thrust test.
- Motor fasteners require thread locker compatible with the motor manufacturer; do not allow screws to contact windings.
- Keep the camera, companion computer and radio inside the central mass envelope.
- Guards must clear rotating propellers by at least 12 mm under hand-applied deflection.
- The shell is non-structural and may be printed or thermoformed, but it must not obstruct flight-controller airflow, GNSS view or battery removal.

## Release checks

The exported assembly preview must show four motors, the camera chin, centre shell, antenna/GNSS location, landing legs and the same off-white/charcoal family treatment used in the README visual. Cosmetic surfaces may change internally, but the propeller envelope and sensor locations may not.
