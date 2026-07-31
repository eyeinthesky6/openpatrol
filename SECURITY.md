# Security policy

Report vulnerabilities privately to the repository owner rather than opening a public exploit issue. Do not include live camera feeds, credentials or personal data in reports.

The simulation binds to loopback by default. A real deployment must use a trusted LAN or VPN, unique ingest credentials, firewall rules and encrypted storage. Never expose ROS 2, Frigate, go2rtc, the evidence directory or this development server directly to the public internet.

This repository is pre-1.0 experimental software. Security fixes target the latest `main`; no long-term support release exists yet.
