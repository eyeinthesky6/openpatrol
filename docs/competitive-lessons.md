# Lessons from adjacent open-source projects

This is a design input, not a criticism scoreboard. Mature projects reveal where real deployments hurt.

## Frigate

Reported support patterns include storage exhaustion from misunderstood retention, long-running events caused by stationary/lighting conditions, segment-cache overload that breaks event playback, UTC/local-time confusion and CPU cost that persists because decoding supports previews and scrubbing. OpenPatrol responds with visible storage status, bounded evidence retention, explicit camera degraded/offline states, source and age on every incident, and separate health diagnostics rather than a silent spinner.

Sources: Frigate issues [#2502](https://github.com/blakeblackshear/frigate/issues/2502), [#3070](https://github.com/blakeblackshear/frigate/issues/3070), [#6636](https://github.com/blakeblackshear/frigate/issues/6636), [#3991](https://github.com/blakeblackshear/frigate/issues/3991) and [#6793](https://github.com/blakeblackshear/frigate/issues/6793).

## Nav2 and ROS 2

Simulation success does not guarantee real motion: users report stuttering or spinning after integration, heartbeat/network failures, late obstacle response, intermittent planning failures and slow remote subscribers affecting robot traffic. OpenPatrol therefore keeps navigation on robot compute, makes localization and watchdog status first-class, stops on faults, uses a 0.5 m/s limit, confirms dangerous commands and separates the browser from the safety controller.

Sources: Nav2 issues [#5480](https://github.com/ros-navigation/navigation2/issues/5480), [#5557](https://github.com/ros-navigation/navigation2/issues/5557), [#4299](https://github.com/ros-navigation/navigation2/issues/4299), [#4655](https://github.com/ros-navigation/navigation2/issues/4655) and ROS 2 issue [#1434](https://github.com/ros2/ros2/issues/1434).

## Open-RMF and Home Assistant

RMF-Web issues show demand for fleet filtering, task-form validation, pagination and predictable LAN setup. Home Assistant discussions show the risk of making critical controls too easy to expose to the wrong user. OpenPatrol keeps a single-robot default, presents dedicated operational views, validates settings server-side, documents LAN deployment, separates operator and detector credentials and makes return/E-stop confirmation explicit.

Sources: [RMF-Web open issues](https://github.com/open-rmf/rmf-web/issues), RMF-Web [#1028](https://github.com/open-rmf/rmf-web/issues/1028) and Home Assistant frontend [#28480](https://github.com/home-assistant/frontend/issues/28480).
