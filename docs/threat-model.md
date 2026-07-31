# Threat model

Protected assets are live streams, evidence, site maps, credentials, operator actions and the ability to move hardware. Trust boundaries exist between browser/operator, OpenPatrol API, detector/Frigate, ROS 2 computer, motor controller and stored media.

Primary threats: exposed LAN services, stolen ingest tokens, forged detections, receipt/media tampering, malicious teleoperation, command replay, unsafe stale commands, untrusted model/container updates, excessive retention and physical access to storage or debug ports.

Baseline controls: loopback bind, VPN rather than public ports, bearer authentication for detector ingestion, hash-chained receipts/audit, bounded retention, container capability removal, controller-level watchdog, normally-closed stop chain and no face recognition. Deployment controls still required: TLS/authenticating reverse proxy, encrypted host volume, OS full-disk encryption, unique device credentials, network segmentation, signed images/updates and credential rotation.

Hashing detects alteration; it does not establish who created a receipt. Production evidence requires a hardware-backed device signing key, secure time and a signed media digest. That remains a pre-pilot gate.
