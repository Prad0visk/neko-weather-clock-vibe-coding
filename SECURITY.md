# Security policy

## Safe use

This repository contains a display theme and a local image/package builder. The builder does not connect to the clock, discover devices, scan the LAN, accept inbound connections, or flash firmware. The theme requests weather data from the public Open-Meteo endpoint using the location in the selected configuration.

## Before sharing a customized build

- Keep `config.local.json`, Wi-Fi settings, serial logs, firmware dumps, and personalized screenshots out of public commits.
- Use `config.example.json` as a generic demonstration only. Set a personal location locally if desired; local configuration is ignored by Git.
- Check screenshots and theme packages for identifying information before sharing them.
- Install theme packages only on compatible hardware and keep a known-good theme available.

## Reporting a security issue

Please open a GitHub issue without including passwords, Wi-Fi credentials, private IP addresses, MAC addresses, or other personal data. For an issue that should not be public, use GitHub's private vulnerability reporting if enabled for this repository.
