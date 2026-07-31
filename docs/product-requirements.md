# Product-note traceability

This matrix prevents roadmap claims from being mistaken for shipped capability.

| Product-note requirement | Status | Evidence / exit gate |
|---|---|---|
| End-to-end patrol → event → receipt → review | Implemented | Simulator, UI and automated integration tests |
| Hardware-neutral product boundary | Implemented | Core has no ROS dependency; integration contract documented |
| Tamper-evident event receipt | Implemented | Immutable capture hash, chained reviews and tamper tests |
| Operator and detector audit | Implemented | Hash-chained JSONL audit and verification endpoint |
| Local-only default and bounded retention | Implemented | Loopback bind, no cloud dependency, configurable age/count limits |
| Health, battery and incident telemetry | Implemented | State API, health endpoint and Prometheus metrics |
| Mobility adapter specification | Contract complete | ROS 2 topic, watchdog and physical E-stop contract; hardware conformance suite remains Phase 1 |
| Frigate integration | Contract complete | Authenticated normalized detection endpoint; real Frigate deployment remains Phase 2 |
| Live video and evidence clips | Not claimed | Needs camera/Frigate and signed media; simulation uses labeled synthetic snapshots |
| Physical stop chain | Not claimed | Requires motor controller, normally-closed E-stop and crash/lost-link testing |
| SLAM/Nav2 autonomous patrol | Not claimed | Requires ROS 2 reference chassis or simulator package |
| Docking and charging | Simulated only | Product state exists; physical gate is ≥95% successful docks over 100 patrol hours |
| Original CAD, wiring and BOM | Not started | Begin only after reference chassis selection and license/provenance review |
| Privacy masking and encryption at rest | Not claimed | Required before real-person or sensitive-site recording |
| Reproducibility by an external builder | Pending | Release gate: independent clean-machine simulation reproduction |

## Next build order

1. Package the current simulation release and get one independent reproduction.
2. Select the 2WD/caster controller and write the ROS 2 adapter conformance tests before CAD styling.
3. Build the teleoperated mule with a physical power-cut E-stop and motor watchdog.
4. Add Frigate clips, signed media manifests and privacy retention tests.
5. Add Nav2, localization-uncertainty stop and waypoint-specific dwell/detection rules.
6. Add dock hardware only after 25 collision-free autonomous patrol hours.
