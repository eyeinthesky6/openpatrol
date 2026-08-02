# Rev-A hardware build and validation guide

## 1. Choose one exact baseline

- Choose **Rover One** for payload, threshold handling and the most stable lidar/camera platform.
- Choose **TriScout** for the cheapest and fastest smooth-floor ground build.
- Choose **AirScout** only for supervised aerial inspection where a ground view is insufficient.
- Choose **Sentinel** for an elevated viewpoint or telepresence; its telescoping mast adds cost and failure modes.

Build one baseline without substitutions first. Do not debug a new architecture and a new supplier stack at the same time—robots already contain enough opportunities for character development.

## 2. Export and quote

```bash
openpatrol setup --with openscad
./scripts/openpatrol export-hardware all
```

Send generated DXF files with material, thickness, quantity, bend/finish notes and deburring requirements. Print PETG/ASA parts with four perimeters and at least 40% infill unless the platform README specifies a tougher material. Inspect every generated dimension and assembly preview before ordering.

## 3. Build the structure before powering it

- Measure the actual wheel track, wheel diameter, wheelbase, airframe diagonal, mast heights and complete mass.
- Record deviations against the exact commit and supplier parts.
- Keep batteries low and inside the ground contact polygon; keep AirScout's centre of gravity within 5 mm of the thrust centre.
- Verify wheel, propeller, mast and sensor clearances through the complete motion envelope.
- Finish and label wiring before enclosing it.

## 4. Software bring-up

Install the lightweight core first:

```bash
pipx install git+https://github.com/eyeinthesky6/openpatrol.git
openpatrol doctor
openpatrol hardware check all
openpatrol
```

ROS/Gazebo, MAVROS and OpenSCAD remain optional. Platform launch examples are documented in `ros2/openpatrol_adapter/README.md`.

## 5. Ground-platform acceptance

1. Wheels-up direction, encoder polarity and stale-command stop.
2. E-stop and every bumper switch remove drive torque without the Pi.
3. Current, wiring and DC-DC thermal tests at realistic peak load.
4. Low-speed straight-line and rotation calibration.
5. Measured braking distance at each speed and maximum mass.
6. Lidar/camera blind-spot and obstacle tests.
7. Eight-hour supervised endurance run, then 25 autonomous hours without contact.
8. Docking only after locomotion is stable; 100 attempts with at least 95% success.

## 6. Sentinel mast acceptance

1. Confirm upper and lower hard limits with the drive disabled.
2. Calibrate the independent linear position sensor.
3. Demonstrate a 500 ms command-loss stop and self-locking hold at maximum head mass.
4. Prove the tilt interlock, drive-moving interlock and docking-retracted interlock.
5. Measure mast sway and tip margin with the head at 1.5 m and the platform stationary.
6. Demonstrate the 0.18 m/s extended speed cap and braking distance.
7. Run at least 500 full extension/retraction cycles while inspecting the cable chain and fasteners.

## 7. AirScout acceptance

1. Check frame diagonal, motor plane, motor order and motor direction with propellers removed.
2. Validate motor/prop/ESC current and temperature on a restraint or thrust stand.
3. Import a reviewed ArduPilot/PX4 parameter set; prove arming, kill channel, geofence, battery failsafe and command-loss landing.
4. Perform a tethered hover, then optical-flow position hold and low-speed velocity-setpoint tests.
5. Fit propeller guards for every indoor test.
6. Complete 25 supervised flights without uncontrolled contact before autonomous route trials.
7. Review applicable local aviation, privacy and site rules before any external operation.

A failed or missing measurement blocks field deployment. Store the exact profile, BOM substitutions, firmware versions, parameters, mass and results with the test report.
