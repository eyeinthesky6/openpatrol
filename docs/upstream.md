# Upstream component policy

OpenPatrol integrates rather than clones upstream projects.

| Capability | Preferred upstream | Integration |
|---|---|---|
| DIY robot base | Linorobot2 | ROS 2 dependency and adapter |
| Reference robot compatibility | TurtleBot3 | Test target only |
| Navigation and docking | Nav2 | ROS 2 packages |
| Mapping/localization | SLAM Toolbox | ROS 2 package, LGPL obligations preserved |
| Local video/evidence | Frigate + go2rtc | Separate authenticated services |
| Multi-robot coordination | Open-RMF | Deferred adapter |
| Docked drone | PX4 | Deferred MAVLink/ROS 2 adapter |
| Ultra-low-cost edition | OpenBot | Separate reference build |

No third-party source has been copied into this repository.
