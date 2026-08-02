# TriScout Rev A wiring

The wiring is the same architecture as Rover One with smaller branch fuses.

`Battery + → 20 A main fuse → keyed isolator → split bus`.

- Drive: 15 A fuse → normally-open 30 A drive relay → MDD10A → one motor per channel.
- Compute: 7.5 A fuse → regulated 5.1 V 6 A DC-DC → Pi and sensors.
- Control: 2 A fuse → safety controller, relay coil, three NC bumper switches and beacon.

The normally-closed series loop is E-stop → front bumper → left/rear switch → right/rear switch → watchdog relay → charger interlock. Opening any element removes drive power. Encoder, battery, E-stop and safety state are published through the ROS hardware adapter; Linux cannot override an open stop loop.
