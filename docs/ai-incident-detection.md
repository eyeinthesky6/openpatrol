# AI incident detection and validation

OpenPatrol produces **incident candidates**, not legal, medical or emergency-service conclusions. Accuracy is a property of the complete site: camera position, lighting, occlusion, model, thresholds, event fusion and operating procedure.

## Supported candidate classes

| Candidate | Typical evidence |
|---|---|
| Fall | fall/person-down model; stronger when followed by immobility |
| Intrusion / break-in | door/forced-entry/glass event plus person or motion in the same zone |
| Drowning / water distress | validated pool-distress model or existing pool-alarm relay |
| Fight / violent movement | two or more of aggressive motion, multiple persons and shout/audio event |
| Sudden movement | calibrated frame-change or model event |
| Fire / smoke | validated camera model and preferably an independent alarm-panel relay |
| Panic / tamper | deterministic button, enclosure or panel event |
| Restricted-zone entry / loitering | person tracking plus configured zone/time rule |

## Confidence policy

OpenPatrol retains weak observations for operator context but creates an incident only when a rule threshold is crossed. Independent sources receive a small fusion boost. Thresholds are intentionally conservative and every candidate remains reviewable.

Direct high-consequence labels such as fall, fight and drowning still require a calibrated model score. The bundled motion helper detects frame change only; it does **not** pretend that pixel motion alone can diagnose a fight or drowning.

## Site acceptance protocol

For every camera and incident class:

1. Freeze the camera position, resolution, FPS, lighting and zone map.
2. Collect representative staged positives and ordinary negatives with consent.
3. Separate calibration data from acceptance data.
4. Measure precision, recall, false alarms per camera-hour and alert latency.
5. Choose thresholds from the operational cost of misses versus false alarms.
6. Test darkness, glare, rain, occlusion, crowding and network interruption.
7. Verify evidence clips and device alerts reach the correct operator/zone.
8. Record model/version/configuration and repeat after any material change.

A practical prototype target is not one universal percentage. Each declared class should have a published acceptance table and confusion matrix for its site. Life-safety and public deployment require professional review and applicable regulation/certification.

## Explicit exclusions

- no face recognition in the reference build
- no covert monitoring
- no weapons, pursuit or autonomous physical intervention
- no replacement of certified fire, pool, medical or access-control systems
- no guarantee of identifying “any incident” from video alone
