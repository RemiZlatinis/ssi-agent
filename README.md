# SSI Agent

> The lightweight Linux monitoring daemon for the SSI ecosystem.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)

## 📖 Overview

The **SSI Agent** is the "worker" of the **Service Status Indicator (SSI)** ecosystem. It is a lightweight daemon designed for Linux systems that leverages `systemd` to schedule and execute service checks.

It runs your custom BASH scripts, captures their output, and streams real-time status updates to the SSI Backend via WebSocket. Designed for transparency and minimal overhead, it ensures you always know the health of your services.

## ✨ Key Features

- **Systemd-Native**: Leverages systemd timers for reliable, scheduled execution.
- **Real-Time Reporting**: Maintains a persistent WebSocket connection to the backend for instant updates.
- **Zero-Config Scripts**: Adds existing BASH scripts as monitored services with a single command.
- **Low Overhead**: Consumes minimal resources (~50MB memory), ideal for any Linux server.

## 🚀 Getting Started

### Prerequisites

- **Operating System**: Linux (systemd-based distributions like Ubuntu, Arch, Debian, CentOS, RHEL).
- **Python**: Version 3.12 or higher.
- **Dependencies**: `acl` (for permission management).

### Installation

We provide an automated installer script to set up the environment, user, and service.

```bash
# Clone the repository
git clone https://github.com/RemiZlatinis/ssi-agent.git
cd ssi-agent

# Run the installer
sudo ./install.sh
```

> **Why sudo?**
> The installer requires root privileges to create the dedicated `ssi-agent` system user, register the systemd service, and configure directory permissions (ACLs) for secure operation.

### Usage

The agent is managed via the `ssi` CLI tool.

**1. Register the Agent**
Connect your agent to the backend:

```bash
ssi register
# Follow the on-screen instructions to enter the code in your mobile app
```

**2. Add a Service**
Turn any BASH script into a monitored service:

```bash
ssi add /path/to/my-script.bash
```

> **Note**: Your script must follow specific output conventions (standardized CSV logs) to be parsed correctly. See the [Service Script Documentation](./docs/service-scripts/00-index.md).

**3. Check Status**
See what your agent is doing:

```bash
ssi status
# OR for detailed logs
ssi status --details
```

**4. Remove a Service**

```bash
ssi remove my_service_id
```

## 📚 Documentation

For detailed documentation, please refer to the `docs/` directory in this repository:

- [**Overview**](./docs/01-overview.md) - Deep dive into architecture and philosophy.
- [**Installation Guide**](./docs/02-installation.md) - Manual installation and troubleshooting.
- [**CLI Reference**](./docs/05-cli-reference.md) - Full list of commands and options.
- [**Configuration**](./docs/06-configuration.md) - Advanced agent configuration.

> For high-level architecture and the full ecosystem overview, visit the [SSI Metarepository](https://github.com/RemiZlatinis/ssi).

## 🤝 Contributing

We welcome contributions! Please see the [Contributing Guidelines](https://github.com/RemiZlatinis/ssi/blob/main/CONTRIBUTING.md) in the SSI Metarepository.

1.  Fork it.
2.  Create your feature branch (`git checkout -b feature/amazing-feature`).
3.  Commit your changes (`git commit -m 'feat: add amazing feature'`).
4.  Push to the branch (`git push origin feature/amazing-feature`).
5.  Open a Pull Request.

## ⚖️ License

This project is licensed under the MIT License - see the [LICENSE](./LICENSE) file for details.
