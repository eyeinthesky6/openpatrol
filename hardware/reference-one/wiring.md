# Reference wiring and stop chain

This is an engineering specification, not a certified electrical drawing. A qualified builder must select wire gauge, fuse ratings, connectors, charger and enclosure for actual current and jurisdiction.

`Battery + → main fuse → keyed isolator → branch fuses`. The compute branch feeds the protected DC-DC converter. The drive branch passes through a contactor or controller-enable input controlled by a normally-closed series loop: E-stop contacts, bumper relay, motor-controller fault relay and service disconnect. Opening any element removes drive torque without Linux cooperation. Battery negative uses a documented star return.

The controller watchdog commands zero torque if fresh commands stop for 250 ms. Linux, ROS 2 and Wi-Fi are supervisory only. The charger connector must be keyed, reverse-polarity protected and interlocked so drive cannot energize while charging.
