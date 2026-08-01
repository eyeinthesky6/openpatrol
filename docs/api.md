# HTTP API

All mutation bodies use `application/json`. Errors have the shape `{"error":{"code":"...","message":"..."}}` and bodies are limited to 64 KiB.

When `OPENPATROL_OPERATOR_TOKEN` is configured, command and review mutations require `Authorization: Bearer …`. Detector ingestion always requires its separate `OPENPATROL_INGEST_TOKEN`.

- `GET /api/v1/health` — liveness and runtime mode
- `GET /api/v1/state` — robot, map and incident snapshot
- `POST /api/v1/commands` — `{"action":"pause|resume|return|estop|reset-estop"}`
- `GET /api/v1/incidents` — evidence receipts
- `GET /api/v1/incidents/{event_id}/verify` — capture and audit-chain verification
- `POST /api/v1/incidents/{event_id}/review` — disposition `confirmed`, `dismissed` or `escalated`, optional note and actor
- `POST /api/v1/detections` — authenticated normalized external detection; requires `Authorization: Bearer $OPENPATROL_INGEST_TOKEN`
- `GET /metrics` — Prometheus text exposition
- `GET /api/v1/audit/verify` — verify the operational audit hash chain

`/api/state`, `/api/health`, `/api/patrol` and the legacy review route remain compatible during the v1 transition.
