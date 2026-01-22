"""
SSI Agent - Service Manager Module

This module orchestrates the high-level actions for managing services:
adding, removing, enabling, and disabling, etc. It bridges the gap between
the data models (loader.py) and the system operations (system.py).
"""

import logging
import tempfile
from pathlib import Path

from . import loader, models, system
from .constants import (
    INSTALLED_SERVICE_SCRIPTS_DIR,
    SSI_AGENT_UNIT_PREFIX,
    SYSTEM_SERVICES_DIR,
)

logger = logging.getLogger(__name__)


def add(source_script_path: Path, start_now: bool = True) -> str:
    """
    Installs a new service script and sets up its systemd units.

    Args:
        source_script_path: Path to the .bash file provided by the user.
        start_now: If True, enables and starts the service immediately.

    Returns:
        The service_id of the newly added service.
    """
    # 1. Validate and Parse the input script
    service = loader.load_from_file(source_script_path)
    service_id = service.id

    # 2. Check if already installed
    existing = loader.load_from_id(service_id)
    if existing:
        logger.info(f"Service '{service_id}' is already installed. Updating...")

    # 3. Create target directory if it doesn't exist
    system.make_directory(INSTALLED_SERVICE_SCRIPTS_DIR)

    # 4. Copy the script to the internal scripts directory
    # Note: We name it with the ID to stay consistent
    target_script_name = f"{service_id}.bash"
    target_path = INSTALLED_SERVICE_SCRIPTS_DIR / target_script_name
    system.copy_file(source_script_path, target_path, mode="755")

    # 5. Generate and install systemd Units
    _install_systemd_units(service, target_path)

    # 6. Finalize System State
    system.reload_daemon()

    if start_now:
        enable(service_id)
        # Immediate run as requested by user
        run(service_id)

    logger.info(f"Service '{service_id}' added successfully.")
    return service_id


def remove(service_id: str) -> None:
    """
    Completely removes a service from the system.
    """
    service = loader.load_from_id(service_id)
    if not service:
        raise ValueError(f"Service '{service_id}' not found.")

    # 1. Stop and disable
    disable(service_id)

    # 2. Remove files
    unit_prefix = f"{SSI_AGENT_UNIT_PREFIX}{service_id}"
    system.remove_file(SYSTEM_SERVICES_DIR / f"{unit_prefix}.service")
    system.remove_file(SYSTEM_SERVICES_DIR / f"{unit_prefix}.timer")
    system.remove_file(service.script)

    # 3. Cleanup systemd
    system.reload_daemon()
    logger.info(f"Service '{service_id}' removed completely.")


def enable(service_id: str) -> None:
    """Enables the systemd timer for a service."""
    unit_name = f"{SSI_AGENT_UNIT_PREFIX}{service_id}.timer"
    system.enable_unit(unit_name, now=True)
    logger.info(f"Service '{service_id}' enabled.")


def disable(service_id: str) -> None:
    """Disables the systemd timer for a service."""
    unit_name = f"{SSI_AGENT_UNIT_PREFIX}{service_id}.timer"
    system.disable_unit(unit_name, now=True)
    logger.info(f"Service '{service_id}' disabled.")


def run(service_id: str) -> None:
    """Starts the service unit immediately (one-shot run)."""
    unit_name = f"{SSI_AGENT_UNIT_PREFIX}{service_id}.service"
    system.start_unit(unit_name, background=True)
    logger.info(f"Service '{service_id}' invoked for immediate run.")


# --- Internal Helpers ---


def _install_systemd_units(service: models.Service, script_path: Path) -> None:
    """Renders and moves systemd unit files into place."""
    template_dir = Path(__file__).parent / "templates"

    # Prepare metadata for templates
    context = {
        "id": service.id,
        "description": service.description,
        "version": service.version,
        "schedule": service.schedule,
        "timeout": service.timeout,
        "script": str(script_path.absolute()),
    }

    # Render Service Unit
    service_content = _render_template(template_dir / "base.service", context)
    _write_privileged_unit(
        f"{SSI_AGENT_UNIT_PREFIX}{service.id}.service", service_content
    )

    # Render Timer Unit
    timer_content = _render_template(template_dir / "base.timer", context)
    _write_privileged_unit(f"{SSI_AGENT_UNIT_PREFIX}{service.id}.timer", timer_content)


def _render_template(template_path: Path, context: dict[str, object]) -> str:
    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_path}")

    template_text = template_path.read_text(encoding="utf-8")
    return template_text.format(**context)


def _write_privileged_unit(filename: str, content: str) -> None:
    """Writes a file to a temp location and moves it to systemd via sudo."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as tf:
        tf.write(content)
        temp_path = Path(tf.name)

    try:
        dest_path = SYSTEM_SERVICES_DIR / filename
        system.move_file(temp_path, dest_path)
        system.set_permissions(dest_path, "644")
    finally:
        if temp_path.exists():
            temp_path.unlink()
