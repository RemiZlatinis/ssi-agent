"""Constants for the Service Status Indicator Agent."""

from pathlib import Path

APP_NAME = "ssi-agent"
PREFIX = "ssi_"  # Prefix for systemd services

# Directories
SERVICES_DIR = Path("/etc/systemd/system")
SCRIPTS_DIR = Path(f"/opt/{APP_NAME}")
LOG_DIR = Path(f"/var/log/{APP_NAME}")
CONFIG_DIR = Path(f"/etc/{APP_NAME}")

# Config file
CONFIG_FILE = CONFIG_DIR / "config.json"  # Match install.sh format
PING_INTERVAL_SECONDS = 10

# Backend API
BACKEND_HOST = "192.168.1.20:8000"
WEBSOCKET_URI = f"ws://{BACKEND_HOST}/ws/agent/"
URI_REGISTER = f"http://{BACKEND_HOST}/api/agents/register/"
URI_UNREGISTER = f"http://{BACKEND_HOST}/api/agents/unregister/"
URI_WHOAMI = f"http://{BACKEND_HOST}/api/agents/me/"
URI_INITIATE_REGISTRATION = f"http://{BACKEND_HOST}/api/agents/register/initiate/"
URI_REGISTRATION_STATUS = f"http://{BACKEND_HOST}/api/agents/register/status/"
