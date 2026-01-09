# Installation

## Prerequisites

Before installing the SSI Agent, ensure your system meets the following requirements:

| Requirement         | How to Check                                   |
| ------------------- | ---------------------------------------------- |
| Linux with systemd  | `systemctl --version`                          |
| Python 3.12+        | `python3 --version`                            |
| python3-venv        | `python3 -c 'import venv'`                     |
| pip                 | `pip3 --version` or `python3 -m pip --version` |
| setfacl (ACL tools) | `which setfacl`                                |
| gcc (recommended)   | `which gcc`                                    |

### Installing Prerequisites (Debian/Ubuntu)

```bash
sudo apt update
sudo apt install python3 python3-venv python3-pip acl build-essential
```

### Installing Prerequisites (RHEL/CentOS/Fedora)

```bash
sudo dnf install python3 python3-pip acl gcc
```

## Installation

### Quick Install

Clone the repository and run the install script:

```bash
git clone https://github.com/RemiZlatinis/ssi-agent.git
cd ssi-agent
sudo ./install.sh
```

### What the Installer Does

1. **Checks system requirements** — Verifies Python, systemd, and dependencies
2. **Creates system user** — `ssi-agent` user for running the daemon
3. **Creates directories**:
   - `/opt/ssi-agent/` — Application files
   - `/opt/ssi-agent/venv/` — Python virtual environment
   - `/opt/ssi-agent/bin/` — Entry point scripts
   - `/opt/ssi-agent/scripts/` — Enabled service-scripts
   - `/etc/ssi-agent/` — Configuration files
   - `/var/log/ssi-agent/` — Log files
4. **Sets up Python virtual environment** — Isolated Python environment
5. **Installs systemd service** — Daemon service file
6. **Creates CLI symlink** — `ssi` command available system-wide
7. **Starts the daemon** — Agent begins running

## Post-Installation

After installation, verify the agent is running:

```bash
# Check service status
systemctl status ssi-agent

# Verify CLI is available
ssi --help
```

### Register the Agent

To connect the agent to your SSI backend:

```bash
ssi register
```

This will display a 6-digit code. Enter this code in an SSI client to complete registration.

## Directory Structure

After installation, the following directories are created:

```
/opt/ssi-agent/
├── venv/                     # Python virtual environment
├── bin/                      # Entry point scripts
└── .enabled-service-scripts/ # Enabled service scripts

/etc/ssi-agent/
└── config.json               # Agent configuration

/var/log/ssi-agent/
└── <service_id>.log          # Service log files
```

## Configuration

The default configuration file is created at `/etc/ssi-agent/config.json`:

```json
{
  "backend_url": "https://api.service-status-indicator.com/",
  "log_level": "INFO",
  "log_dir": "/var/log/ssi-agent",
  "config_dir": "/etc/ssi-agent"
}
```

To change the backend URL:

```bash
ssi set-backend https://your-backend-url.com/
```

## Uninstallation

To completely remove the SSI Agent:

```bash
cd ssi-agent
sudo ./install.sh --remove
```

Or use the `--uninstall` flag:

```bash
sudo ./install.sh --uninstall
```

The uninstaller will:

- Stop and disable the systemd service
- Remove application files
- Remove configuration (optional)
- Remove log files (prompts for confirmation)
- Remove the system user

## Upgrading

To upgrade the agent, simply re-run the installer:

```bash
cd ssi-agent
git pull
sudo ./install.sh
```

The installer preserves your existing configuration.

## Troubleshooting Installation

### "systemd is required but not found"

The SSI Agent only works on systemd-based Linux distributions. Distributions without systemd (e.g., Alpine, Devuan) are not supported.

### "Python 3.12 or higher is required"

Install a newer Python version:

```bash
# Ubuntu/Debian with deadsnakes PPA
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt install python3.12 python3.12-venv
```

### "setfacl is required but not found"

Install the ACL utilities:

```bash
# Debian/Ubuntu
sudo apt install acl

# RHEL/CentOS
sudo dnf install acl
```

### Permission Denied Errors

Ensure you're running the installer with sudo:

```bash
sudo ./install.sh
```
