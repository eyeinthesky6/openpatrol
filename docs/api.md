# HTTP API

All mutation bodies use `application/json`. Errors have the shape `{"error":{"code":"...","message":"..."}}` and bodies are limited to 64 KiB.

- `GET /api/v1/health` — liveness and runtime mode
- `GET /api/v1/state` — robot, map and incident snapshot
- `POST /api/v1/commands` — `{"action":"pause|resume|return|estop|reset-estop"}`
- `GET /api/v1/incidents` — evidence receipts
- `GET /api/v1/incidents/{event_id}/verify` — capture and audit-chain verification
- `POST /api/v1/incidents/{event_id}/review` — disposition `confirmed`, `dismissed` or `escalated`, optional note and actor
- `POST /api/v1/detections` — authenticated normalized external detection; requires `Authorization: Bearer $OPENPATROL_INGEST_TOKEN`
- `GET /metrics` — Prometheus text exposition

`/api/state`, `/api/health`, `/api/patrol` and the legacy review route remain compatible during the v1 transition.
