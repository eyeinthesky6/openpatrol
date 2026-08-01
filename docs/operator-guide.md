# Operator guide

## Start and verify

Run `python3 -m openpatrol.server`, open `http://127.0.0.1:8765`, and confirm `LOCAL / ONLINE`. The yellow marker is the simulated robot. Review health, battery and incident count before commanding motion.

Overview combines the map, synthetic/live-camera boundary, health, mission progress, safety controls, incident table and operational alerts. Incidents is the full review workbench. Diagnostics exposes navigation, storage, cameras, evidence and simulation fault injection. Settings persists retention, receipt cap, maximum speed and timezone; its operator token remains only in browser session storage.

Pause stops route progress. Return to dock selects the first scenario waypoint and enters `docked` on arrival. Dock charging is gradual; departure is refused below reserve. Emergency stop latches the simulated state until Reset E-stop, then the robot remains paused until Resume.

Open an incident to verify its receipt before confirming, dismissing or escalating it. A red integrity result means the capture or audit chain changed; preserve the file and investigate rather than re-reviewing it.

## Failure response

If the dashboard is offline, do not assume a physical robot stopped—use the physical E-stop. If localization, video or detector state is uncertain, pause patrol and investigate locally. Exporting or sharing real evidence is outside this simulation UI and requires site policy, authorization and an audit-controlled export feature.

## Shutdown

Pause, return to dock where safe, then stop the server with Ctrl+C. Evidence and operational audit data remain under `OPENPATROL_DATA`.
