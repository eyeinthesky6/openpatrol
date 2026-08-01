# Product-note traceability

This matrix prevents roadmap claims from being mistaken for shipped capability.

| Product-note requirement | Status | Evidence / exit gate |
|---|---|---|
| End-to-end patrol → event → receipt → review | Implemented | Simulator, UI and automated integration tests |
| Hardware-neutral product boundary | Implemented | Core has no ROS dependency; integration contract documented |
| Tamper-evident event receipt | Implemented | Immutable capture hash, chained reviews and tamper tests |
| Operator and detector audit | Implemented | Hash-chained JSONL audit and verification endpoint |
| Local-only default and bounded retention | Implemented | Loopback bind, no cloud dependency, configurable age/count limits |
| Command authorization and receipt origin | Implemented / deployment keying required | Separate operator/detector tokens and optional HMAC receipt signatures |
| Health, battery and incident telemetry | Implemented | State API, health endpoint and Prometheus metrics |
| Mobility adapter specification | Software complete / hardware unverified | Installable ROS 2 adapter, velocity limits and watchdog; physical conformance remains Phase 1 |
| Frigate integration | Software complete / deployment unverified | MQTT adapter, authenticated detection endpoint and example profile |
| Live video and evidence clips | Integration supplied / hardware unverified | Frigate clip references and optional media digest; camera and signed-media test remain physical deployment work |
| Physical stop chain | Not claimed | Requires motor controller, normally-closed E-stop and crash/lost-link testing |
| SLAM/Nav2 autonomous patrol | Not claimed | Requires ROS 2 reference chassis or simulator package |
| Docking and charging | Simulated only | Product state exists; physical gate is ≥95% successful docks over 100 patrol hours |
| Original CAD, wiring and BOM | Parametric reference supplied | OpenSCAD base/payload source, BOM and stop-chain spec; fabrication dimensions require selected supplier parts |
| Privacy masking and encryption at rest | Not claimed | Required before real-person or sensitive-site recording |
| Reproducibility by an external builder | Package complete / independent result pending | One-command checks and deterministic source archive; external builder must record result |

## Next build order

1. Package the current simulation release and get one independent reproduction.
2. Select the 2WD/caster controller and write the ROS 2 adapter conformance tests before CAD styling.
3. Build the teleoperated mule with a physical power-cut E-stop and motor watchdog.
4. Add Frigate clips, signed media manifests and privacy retention tests.
5. Add Nav2, localization-uncertainty stop and waypoint-specific dwell/detection rules.
6. Add dock hardware only after 25 collision-free autonomous patrol hours.
