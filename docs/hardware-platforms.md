# Hardware platform proposals

OpenPatrol is software-first and mobility-agnostic. The designs below are proposals at different maturity levels. A concept render is not CAD, and parametric CAD is not a validated machine. Only a fabricated revision with measured safety results may be called build-ready.

## Product family

| Name | Form | Status | Why it exists |
|---|---|---|---|
| **OpenPatrol Rover One** | Four-wheel differential/skid-steer rover | Parametric prototype deck | Recommended reference: stable, efficient, readily sourced and able to carry a camera, lidar and compute payload |
| **OpenPatrol TriScout** | Two driven wheels plus rear caster | Parametric concept deck | Lower-cost indoor experiment; less payload capacity and worse threshold handling than Rover One |
| **OpenPatrol AirScout** | Guarded quadcopter | Integration proposal only | Brief elevated inspections and inaccessible shelves; not intended for continuous indoor patrol |
| **OpenPatrol Sentinel** | Wheeled service robot with torso/head | Concept only | Human-facing telepresence and optional manipulation without the cost and fall risk of walking legs |
| **OpenPatrol Humanoid Lab** | Walking articulated humanoid | Upstream research track | Research and demonstrations only; not recommended as the patrol product |

The left-most small platform in the family render represents TriScout; the larger center platform is Rover One. Sentinel is a **wheeled service robot/mobile manipulator**, not a humanoid. A humanoid normally has an articulated humanlike body and locomotion; an android additionally tries to resemble a person.

## Original editable designs

- `hardware/reference-rover4/cad/base.scad`: provisional 420 × 320 mm 4WD deck with four motor regions, service openings and a 20 mm payload grid.
- `hardware/reference-triscout/cad/base.scad`: provisional delta deck for two drive wheels and one caster.
- `hardware/reference-one/cad/base.scad`: the original 2WD/caster mule.
- `hardware/payload-standard/payload_plate.scad`: common sensor/compute payload plate.

Generate local previews with OpenSCAD, for example:

```bash
openscad -o rover-one.stl hardware/reference-rover4/cad/base.scad
openscad -o triscout.stl hardware/reference-triscout/cad/base.scad
```

The motor cut-outs are envelopes, not supplier-controlled hole patterns. Before fabrication, select actual motors, validate ground clearance, center of gravity, braking, thermal load, structure, ingress protection and the independent stop chain.

## Open-source foundations to integrate, not silently copy

| Project | Useful material | Proposed OpenPatrol use | Licence/action |
|---|---|---|---|
| [TurtleBot3](https://github.com/ROBOTIS-GIT/turtlebot3) | Open mobile-base hardware, ROS packages and many mechanical variants | Reference compatibility target and proven ROS conventions | Check per-directory hardware/software licences; preserve notices |
| [Linorobot2](https://github.com/linorobot/linorobot2) | ROS 2 support for 2WD, 4WD and mecanum DIY robots | Physical-base adapter recipe | Apache-2.0 repository; pin the Jazzy branch and preserve notices |
| [OpenBot](https://github.com/ob-f/OpenBot) | Low-cost four-wheel vehicle using a smartphone | Ultra-low-cost camera rover profile | MIT repository; preserve attribution and review any separately sourced components |
| [Robotont](https://github.com/robotont) | Open omnidirectional robot hardware and ROS support | Future holonomic indoor variant | Import only after file-level licence review |
| [PX4](https://github.com/PX4/PX4-Autopilot) and [Pixhawk hardware](https://github.com/pixhawk/Hardware) | Flight stack and open flight-controller reference designs | AirScout MAVLink/ROS 2 adapter; do not invent a flight controller | Pixhawk reference hardware is generally CC BY-SA; derived files must retain terms |
| [ArduPilot](https://github.com/ArduPilot/ardupilot) | Mature autopilot stack and simulation | Alternative AirScout backend | GPL-3.0; external integration boundary |
| [Poppy Humanoid](https://github.com/poppy-project/poppy-humanoid) | 3D-printable articulated research humanoid | Humanoid Lab reference only | Confirm current file licences and actuator availability before import |
| [OpenCat](https://github.com/PetoiCamp/OpenCat-Quadruped-Robot) | Affordable open quadruped framework | Optional stair/uneven-ground research profile | External project; licence review required before copying assets |

No third-party CAD is vendored today. That is deliberate: “open source” does not mean all files can be merged under OpenPatrol's licences. Each selected upstream should be pinned in a manifest, attributed, kept updateable, and isolated when copyleft/share-alike terms require it.

## Drone boundary

AirScout should be a separately certified/validated vehicle. OpenPatrol should send high-level inspect/return requests through a MAVLink adapter while PX4 or ArduPilot owns stabilization, geofencing, failsafes and return-to-land. Indoor operation needs propeller guards, optical-flow or visual-inertial positioning, altitude sensing and a supervised launch area. The current repository does not yet implement or simulate this adapter.

## Humanoid decision

A walking humanoid is visually compelling but is the wrong default surveillance carrier: it spends energy balancing, falls, costs far more, and adds many actuators without improving camera coverage. Sentinel—the wheeled torso—is the credible proposal. Poppy/Open-source humanoids should remain optional research integrations until a specific manipulation or stair-climbing requirement justifies them.

## Media truth

The README images are AI-generated concept renders. They illustrate intended form factors and operating scenarios; they are not photographs of built OpenPatrol hardware. A real demonstration video should be recorded only after a prototype or its Gazebo model performs the shown mission. An AI concept video may be added, but must remain visibly labelled **concept animation**.
