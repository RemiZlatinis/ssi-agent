"""
SSI Agent - Service Loader Module

This module is responsible for discovering, parsing, and validating service
definitions from the local file system. It maintains "Source of Truth" for
each service script by looking the directory of installed scripts and the
corresponding systemd units.
"""

import logging
import re
from pathlib import Path

from . import system
from .constants import INSTALLED_SERVICE_SCRIPTS_DIR, SSI_AGENT_UNIT_PREFIX
from .models import Service
from .validators import validate_schedule

logger = logging.getLogger(__name__)


def load_from_file(script_path: Path) -> Service:
    """
    Parses a .bash script to extract metadata and returns a Service model.
    Checks the system to see if the service is currently enabled.
    """
    if not script_path.exists():
        raise FileNotFoundError(f"Service script {script_path} does not exist.")

    if script_path.suffix != ".bash":
        raise ValueError(f"Service script {script_path.name} must be a .bash file.")

    try:
        content = script_path.read_text(encoding="utf-8")

        # Regex patterns for metadata
        name_match = re.search(r"# name:\s*(.+)", content)
        desc_match = re.search(r"# description:\s*(.+)", content)
        ver_match = re.search(r"# version:\s*(.+)", content)
        sched_match = re.search(r"# schedule:\s*(.+)", content)
        timeout_match = re.search(r"# timeout:\s*(\d+)", content)

        if not name_match:
            raise ValueError(
                f"Service script {script_path.name} is missing '# name:' metadata."
            )
        if not desc_match:
            raise ValueError(
                f"Service script {script_path.name} is missing '# description:' "
                "metadata."
            )
        if not ver_match:
            raise ValueError(
                f"Service script {script_path.name} is missing '# version:' metadata."
            )
        if not sched_match:
            raise ValueError(
                f"Service script {script_path.name} is missing '# schedule:' metadata."
            )

        name = name_match.group(1).strip()
        description = desc_match.group(1).strip()
        version = ver_match.group(1).strip()
        schedule = sched_match.group(1).strip()
        timeout = int(timeout_match.group(1)) if timeout_match else 20

        # Run validations
        if not (3 <= len(name) <= 60):
            raise ValueError(
                f"Service script {script_path.name} has an invalid"
                f" name '{name}' must be between 3 and 60 characters."
            )

        if len(description) > 255:
            raise ValueError(
                f"Service script {script_path.name} has an invalid"
                " description cannot exceed 255 characters."
            )

        validate_schedule(schedule)

        # Generate ID (logic: kebab-case)
        service_id = name.replace(" ", "-").lower()

        # Check if the service is enabled in systemd
        # The unit name is always prefix + id + .timer
        is_enabled = system.is_unit_enabled(
            f"{SSI_AGENT_UNIT_PREFIX}{service_id}.timer"
        )

        return Service(
            id=service_id,
            name=name,
            description=description,
            version=version,
            schedule=schedule,
            script=script_path,
            timeout=timeout,
            is_enabled=is_enabled,
        )

    except Exception as e:
        logger.error(f"Failed to parse service script {script_path.name}: {e}")
        raise


def load_from_id(service_id: str) -> Service | None:
    """
    Attempts to load a service by its ID by looking
    in the installed scripts directory.
    """
    script_path = INSTALLED_SERVICE_SCRIPTS_DIR / f"{service_id}.bash"

    if not script_path.exists():
        return None

    try:
        return load_from_file(script_path)
    except Exception as e:
        logger.error(f"Error loading service {service_id}: {e}")
        return None


def list_services(all: bool = False) -> list[Service]:
    """
    Returns the all installed or only the enabled services.

    Args:
        all (bool): Whether to return all installed services or only the enabled ones.

    Returns:
        list[Service]: The list of installed services.
    """
    if not INSTALLED_SERVICE_SCRIPTS_DIR.exists():
        logger.debug(
            f"Scripts directory {INSTALLED_SERVICE_SCRIPTS_DIR} does not exist yet."
        )
        return []

    services = []
    # Find all .bash files in the installed scripts directory
    for script_file in INSTALLED_SERVICE_SCRIPTS_DIR.glob("*.bash"):
        try:
            service = load_from_file(script_file)
            if all or service.is_enabled:
                services.append(service)
        except Exception as e:
            logger.warning(f"Skipping invalid service script {script_file.name}: {e}")

    return services
