"""Constants for the Service Status Indicator Agent."""

from pathlib import Path

APP_NAME = "ssi-agent"
SSI_AGENT_UNIT_PREFIX = "ssi-"  # Prefix for systemd services

# Directories
SYSTEM_SERVICES_DIR = Path("/etc/systemd/system")
INSTALLED_SERVICE_SCRIPTS_DIR = Path(f"/opt/{APP_NAME}/.installed-service-scripts")
LOG_DIR = Path(f"/var/log/{APP_NAME}")
CONFIG_DIR = Path(f"/etc/{APP_NAME}")

# Config file
CONFIG_FILE = CONFIG_DIR / "config.json"  # Match install.sh format
WEBSOCKET_PING_INTERVAL = 30
WEBSOCKET_PING_TIMEOUT = 70
WEBSOCKET_CLOSE_TIMEOUT = 5

# Logging
PUBLIC_DSN = (
    "https://24d5031370854ccc980809a73e14b98b@servicestatusindicator.bugsink.com/1"
)
