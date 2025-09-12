"""Constants for the Service Status Indicator Agent."""

from pathlib import Path

PREFIX = "ssi_"  # Prefix for systemd services
SERVICES_DIR = Path("/usr/local/lib/systemd/system/")
SCRIPTS_DIR = Path("/usr/local/lib/service-status-indicator/")
LOG_DIR = Path("/var/log/service-status-indicator")
