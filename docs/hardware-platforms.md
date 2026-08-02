# Hardware platform matrix

OpenPatrol is software-first and mobility-agnostic. Two platforms now have complete Rev-A engineering packs; the others remain proposals.

| Name | Form | Current status | Decision |
|---|---|---|---|
| **OpenPatrol Rover One** | Four-wheel skid-steer rover | Complete Rev-A engineering pack; software profile passes; physical validation pending | Primary product reference |
| **OpenPatrol TriScout** | Two drive wheels plus rear caster | Complete Rev-A engineering pack; software profile passes; physical validation pending | Lowest-cost builder reference |
| **OpenPatrol AirScout** | Guarded quadcopter | Integration proposal only | Defer until a ground pilot proves demand |
| **OpenPatrol Sentinel** | Wheeled torso/service robot | Concept only | Defer until telepresence/manipulation is required |
| **OpenPatrol Humanoid Lab** | Walking humanoid | Upstream research track | Not a patrol product |

## Shared Rev-A architecture

Both buildable platforms use a 12.8 V LiFePO4 power bus, common 12 V 100 RPM encoder gearmotors, 100 mm rubber wheels, Raspberry Pi 5 4 GB, RP2040/ESP32-S3 safety I/O, LD06/LD19-class 2D lidar, a protected dual-channel H-bridge, a hardwired normally-closed stop loop and removable ABS covers. Structural plates are laser-cut 3 mm 5052 aluminium; low-cost indoor prototypes may use 6 mm HDPE or birch plywood with the same files.

Use `openpatrol hardware check all` to validate kinematics, power budget, stop envelope, cost cap and ROS topic compatibility. Use `./scripts/openpatrol export-hardware all` to export DXF/STL/preview artifacts.

## Design truth

“Build-ready” here means the design is sufficiently specified for a competent fabricator and assembler to build Rev A without inventing the architecture. It does not mean that an unbuilt design has proven braking, thermal safety, runtime, sensor coverage or dock reliability. Those claims require a fabricated unit and recorded acceptance data.

## Deferred platforms

AirScout should use PX4 or ArduPilot for stabilization and failsafes behind a MAVLink/ROS 2 adapter. Sentinel should remain wheeled; walking legs add cost, fall risk and energy use without improving routine patrol. Neither is included in the current production reference scope.
