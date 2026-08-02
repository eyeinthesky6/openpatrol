# OpenPatrol command centre

OpenPatrol is an **open integration layer**, not a replacement mandate. Existing IP cameras, NVR/VMS products, access control, alarm panels, Home Assistant devices and dry-contact sensors can continue to operate independently while OpenPatrol provides one incident queue, evidence trail and operator/device alert path.

## Data path

```text
RTSP/ONVIF cameras ─┐
Frigate/model events ├─> security observations ─> conservative fusion ─> evidence receipt
Alarm/access events ┤                                             └─> operator alert
Sensor Hub inputs ──┘                                                  └─> device commands
                                                                    speaker/strobe/siren
```

### Inputs

- **Video:** RTSP cameras are restreamed/recorded through Frigate/go2rtc. Frigate object/zone events and any provider's model events enter `POST /api/v1/security-events`.
- **NVR/VMS and AI products:** use `openpatrol-vision-adapter` or post the versioned JSON event directly.
- **Alarm, access control and automation:** use `openpatrol-security-bridge` over NDJSON or MQTT. The normalizer accepts common flat, Home Assistant and ONVIF/Hikvision-style event fields.
- **Wired sensors:** the Security Sensor Hub Rev A brings eight supervised dry-contact/relay loops into the same contract.

### Outputs

Devices register capabilities such as `speaker`, `talkback`, `strobe` and `siren`. The command centre creates a bounded command queue. The endpoint agent can execute only allow-listed actions; event data can never inject a shell command.

- Browser audio and desktop notifications for high/critical candidates
- Zone strobe for high/critical incidents
- Zone siren for critical incidents when enabled by policy
- Operator text announcements or recorded talkback
- Automatic neutral warnings for high-confidence intrusion, water distress, fire/smoke and panic events
- Falls and fights remain operator-first to avoid harmful or accusatory automated speech

## Installation

Lightweight local demo:

```bash
pipx install git+https://github.com/eyeinthesky6/openpatrol.git
openpatrol
```

Repository checkout:

```bash
./scripts/openpatrol up        # command-centre demo
./scripts/openpatrol vision    # + Frigate/go2rtc camera stack
./scripts/openpatrol security  # + MQTT security bridge
./scripts/openpatrol full      # camera + MQTT stack
```

The script creates local ingest, device and signing secrets. Set an operator token before LAN use and place the UI behind a VPN or authenticated TLS gateway.

## API summary

- `GET /api/v1/command-centre`
- `POST /api/v1/security-events`
- `POST /api/v1/devices/register`
- `POST /api/v1/devices/{id}/heartbeat`
- `GET /api/v1/devices/{id}/commands`
- `POST /api/v1/devices/{id}/commands/{command}/ack`
- `POST /api/v1/announce`
- `POST /api/v1/talkback`

See `schemas/security-event-v1.schema.json`, `schemas/device-registry-v1.schema.json` and `schemas/alert-v1.schema.json`.

## Network boundary

Do not expose OpenPatrol, Frigate/go2rtc, MQTT, ROS 2 or MAVLink directly to the internet. Use separate ingest/device/operator credentials, restricted network segments and an authenticated gateway. Camera credentials remain in Frigate/device configuration and are not returned by the command-centre API.
