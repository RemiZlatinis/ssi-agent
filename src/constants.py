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

# Logging
PUBLIC_DSN = (
    "https://24d5031370854ccc980809a73e14b98b@servicestatusindicator.bugsink.com/1"
)
