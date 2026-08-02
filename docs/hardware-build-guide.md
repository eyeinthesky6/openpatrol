# Rev-A hardware build and validation guide

## 1. Choose the platform

Choose Rover One for payload, threshold handling and a more stable camera/lidar platform. Choose TriScout when cost, build time and indoor floor quality matter more than payload. Do not customize both at once; build one exact baseline before substituting parts.

## 2. Export and quote

```bash
openpatrol setup --with openscad
./scripts/openpatrol export-hardware all
```

Send the generated DXF files to a laser-cutting vendor with material, thickness, quantity and deburring requirements. Print the STL parts in PETG or ASA with four perimeters and at least 40% infill. Inspect exported dimensions against the README before ordering.

## 3. Bench assembly

Assemble the unpowered chassis, measure wheel track, wheel diameter, wheelbase, caster level and complete mass, then update the JSON profile only when the measurement materially differs. Wire one fused branch at a time. Test the stop loop with a continuity meter before connecting the battery or motor driver.

## 4. Software bring-up

Install the lightweight core first:

```bash
pipx install git+https://github.com/eyeinthesky6/openpatrol.git
openpatrol doctor
openpatrol hardware check all
openpatrol
```

ROS/Gazebo and Frigate are optional and intentionally not pulled into the core Python package. From a repository checkout, `openpatrol setup` explains their requirements; `./scripts/openpatrol vision` starts the camera stack after an RTSP URL is configured.

For physical hardware, map encoder ticks, battery and E-stop into the documented ROS topics. Keep the physical motor watchdog and NC stop loop independent of the Pi.

## 5. Validation gates

1. Wheels-up direction, encoder polarity and 250 ms stale-command stop.
2. E-stop and every bumper switch remove drive torque without the Pi.
3. Current, wiring and DC-DC thermal test at stalled/peak realistic load.
4. Low-speed straight-line and rotation calibration.
5. Measured braking distance at each speed and maximum payload.
6. Lidar/camera blind-spot and obstacle tests.
7. Eight-hour supervised endurance run, then 25 autonomous hours without contact.
8. Docking only after locomotion is stable; 100 attempts with at least 95% success.

Record results against the exact commit, BOM substitutions, firmware and measured mass. A failed or missing measurement blocks field deployment.
