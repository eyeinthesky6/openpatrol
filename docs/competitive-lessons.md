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

## Additional 2026 hardening pass

The recurring operator problem is not a missing animation; it is uncertainty about whether a signal is current, actionable and safe. Nav2 users report real-hardware instability despite clean simulation, lifecycle heartbeat loss under network load, late obstacle response and unsafe failure from malformed/unbounded messages. RMF-Web users ask for task validation, filtering and scalable pagination. Human-factors research also finds that alert failures change monitoring behaviour and trust. OpenPatrol now treats detector retries as idempotent, bounds every ingest field, preserves scenario cooldowns across restarts, exposes a distance-aware return-energy requirement, charges idle compute/sensor energy during dwell, and verifies review state against a signed audit tail.

These changes follow primary reports rather than assuming any upstream package is defective: deployment configuration and hardware remain major variables. Sources: Nav2 [#5480](https://github.com/ros-navigation/navigation2/issues/5480), [#5557](https://github.com/ros-navigation/navigation2/issues/5557), [#5610](https://github.com/ros-navigation/navigation2/issues/5610), RMF-Web [#911](https://github.com/open-rmf/rmf-web/issues/911), [#997](https://github.com/open-rmf/rmf-web/issues/997), [#1081](https://github.com/open-rmf/rmf-web/issues/1081), and Ferraro & Mouloua's [operator alert study](https://doi.org/10.1177/1071181321651290).
