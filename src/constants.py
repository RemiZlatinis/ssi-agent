"""Constants for the Service Status Indicator Agent."""

from pathlib import Path

APP_NAME = "ssi-agent"
PREFIX = "ssi_"  # Prefix for systemd services

# Directories
SERVICES_DIR = Path("/etc/systemd/system")
SCRIPTS_DIR = Path("/opt/service-status-indicator")
LOG_DIR = Path("/var/log/service-status-indicator")
CONFIG_DIR = Path("/etc/service-status-indicator")

# Config file
CONFIG_FILE = CONFIG_DIR / "config.json"  # Match install.sh format

# Backend API
BACKEND_HOST = "192.168.1.20:8000"
URI_REGISTER = f"http://{BACKEND_HOST}/api/agents/register/"
URI_UNREGISTER = f"http://{BACKEND_HOST}/api/agents/unregister/"
URI_WHOAMI = f"http://{BACKEND_HOST}/api/agents/me/"
