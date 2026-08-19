# SSI Agent

> The lightweight Linux monitoring daemon for the SSI ecosystem.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)

> **Tip:** if you're setting up the whole SSI ecosystem (agent, backend, clients) rather than just this repo, use the [workspace setup script](https://github.com/RemiZlatinis/ssi) in the metarepository instead — it clones and bootstraps all components for you.

## 📖 Overview

The **SSI Agent** is the "worker" of the **Service Status Indicator (SSI)** ecosystem. It is a lightweight daemon designed for Linux systems that leverages `systemd` to schedule and execute service checks.

It runs your custom BASH scripts, captures their output, and streams real-time status updates to the SSI Backend via WebSocket. Designed for transparency and minimal overhead, it ensures you always know the health of your services.

## ✨ Key Features

- **Systemd-Native**: Leverages systemd timers for reliable, scheduled execution.
- **Real-Time Reporting**: Maintains a persistent WebSocket connection to the backend for instant updates.
- **Zero-Config Scripts**: Adds existing BASH scripts as monitored services with a single command.
- **Low Overhead**: Minimal resource footprint, ideal for any Linux server.

## 🚀 Getting Started

### Prerequisites

- **Operating System**: Linux (systemd-based distributions like Ubuntu, Arch, Debian, CentOS, RHEL).
- **Python**: Version 3.12 or higher.
- **Poetry**: For dependency management (`poetry install`).
- **Dependencies**: `acl` (for permission management).
- **Podman**: For the containerized development environment ([optional, see AGENTS.md](./AGENTS.md#step-3-set-up-containerized-development)).

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
ssi auth register
# Follow the on-screen instructions to enter the code in your mobile app
```

> **Configuration**: the agent connects to a backend endpoint — see the [Configuration guide](./docs/06-configuration.md) to point your agent at a self-hosted backend.

**2. Add a Service**
Turn any BASH script into a monitored service:

```bash
ssi service add /path/to/my-script.bash
```

> **Note**: Your script must follow specific output conventions (standardized CSV logs) to be parsed correctly. See the [Service Script Documentation](./docs/service-scripts/00-index.md).

**3. Check Status**
See what your agent is doing:

```bash
ssi service status
# OR for detailed logs
ssi service status --details
```

**4. Remove a Service**

```bash
ssi service remove my-service-id
```

## 🛠️ Development Setup

### Quick Start

To set up your development environment (with validation), use this prompt with your AI agent:

```
I'm working on the ssi-agent project. Please help me set up and validate my development environment.
Follow the detailed instructions in AGENTS.md under the "Development Workflow" section to:
1. Install pre-commit hooks
2. Configure VS Code with Ruff formatter
3. Verify the setup is working correctly

Please check each step and report any issues.
```

**Or manually follow** the comprehensive [Development Setup Guide](./AGENTS.md#-development-workflow) in [AGENTS.md](./AGENTS.md).

### Container-Based Development

The recommended way to develop is using the automated development environment script:

```bash
poetry run dev
```

This builds/starts a development container with systemd enabled (Podman), runs the installer inside, and drops you into an interactive shell. For more details, see [AGENTS.md](./AGENTS.md#step-3-set-up-containerized-development).

### Tests

```bash
poetry run test
```

Starts a fresh test container, installs the agent, and runs the E2E test suite.

## 📚 Documentation

For detailed documentation, please refer to the `docs/` directory in this repository:

- [**Index**](./docs/00-index.md) - Where to start.
- [**Overview**](./docs/01-overview.md) - Deep dive into architecture and philosophy.
- [**Installation Guide**](./docs/02-installation.md) - Manual installation and troubleshooting.
- [**Quick Start**](./docs/03-quick-start.md) - Get an agent up and running quickly.
- [**Architecture**](./docs/04-architecture.md) - How the agent is built and why.
- [**CLI Reference**](./docs/05-cli-reference.md) - Full list of commands and options.
- [**Configuration**](./docs/06-configuration.md) - Advanced agent configuration.
- [**Troubleshooting**](./docs/90-troubleshooting.md) - Common issues and fixes.
- [**FAQ**](./docs/91-faq.md) - Frequently asked questions.
- [**Changelog**](./docs/99-changelog.md) - Release history.
- [**Service Scripts**](./docs/service-scripts/00-index.md) - How service scripts work.

> For high-level architecture and the full ecosystem overview, visit the [SSI Metarepository](https://github.com/RemiZlatinis/ssi).

## 🤝 Contributing

We welcome contributions! Please read the [Contributing Guidelines](https://github.com/RemiZlatinis/ssi/blob/main/CONTRIBUTING.md) in the SSI Metarepository.

**Before submitting a PR, ensure:**

1. Pre-commit hooks are installed and passing locally
2. Your feature branch is based on `main`
3. Commit messages follow conventional commit format
4. All checks pass: `pre-commit run --all-files`

## ⚖️ License

This project is licensed under the MIT License - see the [LICENSE](./LICENSE) file for details.