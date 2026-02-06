# Agent Documentation

Welcome to the Service Status Indicator (SSI) Agent documentation.

## Table of Contents

### Getting Started

- [Overview](01-overview.md) — What is the SSI Agent?
- [Installation](02-installation.md) — How to install the agent
- [Quick Start](03-quick-start.md) — Get up and running in minutes

### Core Concepts

- [Architecture](04-architecture.md) — How the agent works
- [CLI Reference](05-cli-reference.md) — Command-line interface
- [Configuration](06-configuration.md) — Configuration options

### Service Scripts

- [Introduction](service-scripts/00-index.md) — What are service scripts?
- [Block Structure](service-scripts/01-structure.md) — Anatomy of a service script
- [Manifest Reference](service-scripts/02-manifest-reference.md) — Manifest fields
- [Status Codes](service-scripts/03-status-codes.md) — Output format and status codes
- [Library](service-scripts/04-library.md) — Production-ready scripts
- [Best Practices](service-scripts/05-best-practices.md) — Tips and recommendations

### Reference

- [Troubleshooting](90-troubleshooting.md) — Common issues and solutions
- [FAQ](91-faq.md) — Frequently asked questions
- [Changelog](99-changelog.md) — Version history

---

## Quick Links

| Task           | Command                         |
| -------------- | ------------------------------- |
| Register agent | `ssi auth register`             |
| Add a service  | `ssi service add <script.bash>` |
| List services  | `ssi service list`              |
| Check status   | `ssi service status`            |

---

## Related Projects

| Project                                                                | Description                      |
| ---------------------------------------------------------------------- | -------------------------------- |
| [ssi-backend](https://github.com/RemiZlatinis/ssi-backend)             | Backend API and WebSocket server |
| [ssi-client-mobile](https://github.com/RemiZlatinis/ssi-client-mobile) | Mobile client application        |
| [ssi-site](https://github.com/RemiZlatinis/ssi-site)                   | Project website                  |
