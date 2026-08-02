# Sensor Hub serial protocol v1

USB serial: 115200 8N1, newline-delimited JSON.

Hub to gateway:

```json
{"v":1,"seq":42,"type":"zone","zone":3,"state":"alarm","raw":612,"at_ms":123456}
{"v":1,"seq":43,"type":"tamper","state":"open","at_ms":123500}
{"v":1,"seq":44,"type":"heartbeat","outputs":{"strobe":false,"siren":false},"at_ms":124000}
```

Gateway to hub:

```json
{"v":1,"id":"cmd-123","action":"strobe","seconds":20}
{"v":1,"id":"cmd-124","action":"siren","seconds":10}
{"v":1,"id":"cmd-125","action":"stop_output"}
```

The hub rejects unknown actions and enforces a 60-second maximum output duration. A physical service-isolate input overrides both outputs. The gateway maps zone states to authenticated `POST /api/v1/security-events` calls and acknowledges command-centre output commands only after the hub reports the requested state.
