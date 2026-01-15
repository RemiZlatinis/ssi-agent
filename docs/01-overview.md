# Overview

## What is the SSI Agent?

The **Service Status Indicator (SSI) Agent** is a lightweight monitoring daemon designed for Linux systems. It runs service check scripts on a schedule and reports their status to the SSI backend in real-time.

## Key Features

- **Systemd-Native**: Leverages systemd timers for reliable, scheduled execution
- **Real-Time Reporting**: WebSocket connection to backend for instant status updates
- **Self-Contained Scripts**: Each service script is independent and transparent
- **Low Overhead**: Minimal resource usage (~50MB memory, burst-only CPU)
- **CLI Management**: Simple command-line interface for all operations

## How It Works

```
┌─────────────────────────────────────────────────────────┐
│                     Linux System                        │
│ ┌─────────────┐    ┌─────────────┐    ┌───────────────┐ │
│ │ Service &   │    │  SSI Agent  │    │  SSI Backend  │ │
│ │ Timer Units ├────►             ◄────►               │ │
│ │  (systemd)  │    │   Daemon    │    │  (WebSocket)  │ │
│ └──────┬──────┘    └──────┬──────┘    └───────────────┘ │
│        │                  │                             │
│        │                  │                             │
│ ┌──────▼──────┐    ┌──────▼──────┐                      │
│ │   Service   │    │     Log     │                      │
│ │   Scripts   │    │    Files    │                      │
│ └─────────────┘    └─────────────┘                      │
└─────────────────────────────────────────────────────────┘
```

1. **Service scripts** are BASH scripts that perform monitoring checks
2. **Systemd timers** trigger scripts according to their schedule
3. **Script output** is written to log files in a standardized format
4. **The daemon** watches log files and sends updates via WebSocket
5. **The backend** receives updates and notifies connected clients

## What the Agent Is NOT

- ❌ A cross-platform tool (Linux only)
- ❌ An interactive application
- ❌ A self-updating system
- ❌ A standalone monitoring solution (requires ssi-backend)

## System Requirements

| Requirement      | Specification                 |
| ---------------- | ----------------------------- |
| Operating System | Linux (systemd-based)         |
| Python           | 3.12 or higher                |
| Init System      | systemd (required)            |
| Network          | Outbound WebSocket connection |

## Related Components

| Component           | Relationship                          |
| ------------------- | ------------------------------------- |
| `ssi-backend`       | Receives status reports via WebSocket |
| `ssi-client-mobile` | Displays status to end users          |

## Philosophy

> **Transparency and Independence**

Every service script is:

- **Self-contained**: No external dependencies beyond standard tools
- **Transparent**: What you see is exactly what runs
- **Deterministic**: Same input always produces same output

The agent follows the principle of "boring, predictable code" — clarity over cleverness, explicit over implicit.
