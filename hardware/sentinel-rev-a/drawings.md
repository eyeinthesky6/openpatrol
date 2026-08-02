# Sentinel Rev-A critical drawing schedule

All dimensions are millimetres unless noted. The mast is an elevated mass and must be treated as a stability mechanism, not decorative bodywork.

## Datums

- **A:** lower chassis deck top face
- **B:** vehicle longitudinal centreline
- **C:** vehicle lateral centreline
- **D:** mast-column centreline
- **E:** floor plane at nominal tyre radius

## Locked dimensions

| Feature | Nominal | Prototype tolerance |
|---|---:|---:|
| overall base envelope | 460 × 400 | ±3 cosmetic; no wheel interference |
| structural lower deck | 430 × 320 × 3 | ±0.4 cut |
| wheelbase | 280 | ±1.0 |
| wheel track | 360 | ±1.0 |
| wheel diameter | 125 | record loaded radius |
| mast centre from B/C | 0 / 0 | ±1.0 |
| retracted sensor-head height from E | 980 | ±10 after calibration |
| extended sensor-head height from E | 1500 | ±10 after calibration |
| mast travel | 520 | ±5 |
| masked-head exterior | 190 × 110 × 85 | ±1 printed/formed |
| maximum installed head mass | 2.5 kg | hard limit |
| target installed head mass | 1.8 kg | record actual |
| maximum total mass | 24 kg | hard limit |
| maximum total-CG height | 430 | verify by tilt test |

## Mast interfaces

- Four M8 mast-base fasteners on the `mast_base` drawing; use locking nuts or qualified thread locker.
- A separate linear position sensor must cover the full 980–1500 mm calibrated head-height range. Electrical values outside the calibrated range are a fault, not a height estimate.
- The lower and upper limits are independent normally-closed inputs to the mast controller.
- Add an independent normally-closed **retracted-confirm switch** at the bottom datum. It is series-wired with the mast controller's isolated `RETRACTED_OK` output to the drive controller.
- The column must be self-locking or actively braked at rated head mass.
- The flexible cable chain must retain at least 20% service slack at full extension and must not enter the lidar field of view.
- The fixed lidar remains below the moving head so base navigation survives a mast controller fault.

## Stability controls

Using the declared 430 mm maximum CG height and 200 mm half-width, the ideal static side-tip angle is about 25 degrees before tyre/body compliance. The hardware tilt interlock is therefore set no higher than 8 degrees pending measured tests. This is an engineering margin, not a certification claim.

No autonomous docking or normal-speed travel is permitted unless the mast is positively confirmed retracted. The drive controller independently applies the 0.18 m/s wheel cap when the confirmation loop is open. Open wire, controller power loss, invalid height sensor, or mast movement all fail to the capped state.

## Exterior and service

The masked sensor head, off-white torso, charcoal mast/base and vertical blue status light are controlled family features. A rear recessed guarded service stop is allowed; an exposed public-facing stop button is not the baseline because it invites casual disabling. A supervised wireless safety pendant still opens the hardwired drive chain during testing.
