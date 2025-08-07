"""Command functions for interacting with systemd and managing service files."""

import subprocess
from pathlib import Path

from constants import PREFIX, SCRIPTS_DIR, SERVICES_DIR


def _execute(command: str) -> str:
    """Runs a command in the shell and handles errors."""
    try:
        result = subprocess.run(
            command, check=True, capture_output=True, text=True, shell=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {command}")
        print(f"Stderr: {e.stderr.strip()}")
        exit(1)
    except FileNotFoundError:
        print(f"Command not found: {command}")
        exit(1)


def get_enabled_services() -> list[str]:
    """Returns a list of enabled services."""
    command = (
        'systemctl list-unit-files "ssi_*.timer" --state=enabled --no-legend --no-pager '
        "| awk '{print $1}'"
    )
    output = _execute(command)
    output = output.replace(".timer", "").replace("ssi_", "")
    return output.splitlines() if output else []


def reload_daemon():
    """Reloads the systemd daemon."""
    _execute("sudo systemctl daemon-reload")


def is_enabled(service_id: str) -> bool:
    """Checks if the corresponding time unit for the service is enabled."""
    command = ["systemctl", "is-enabled", f"{service_id}.timer"]
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        return result.stdout.strip() == "enabled"
    except subprocess.CalledProcessError as e:
        return False
        # if e.returncode == 4:
        #     print(f"Service {service_id} is not installed.")
        # print(f"Error on calling systemctl is-enabled for {service_id}.timer")
        # exit(1)


def install_script(service_id: str, script: Path) -> None:
    """Installs a service script to the scripts directory."""
    target_script = SCRIPTS_DIR / f"{service_id}.bash"

    # Ensure the scripts directory exists
    subprocess.run(["sudo", "mkdir", "-p", str(SCRIPTS_DIR)], check=True)

    try:
        # Copy the script to the scripts directory
        subprocess.run(["sudo", "cp", str(script), str(target_script)], check=True)
        # Make the script executable
        subprocess.run(["sudo", "chmod", "755", str(target_script)], check=True)
        print(f"Script {script.name} installed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error installing script {script.name}: {e}")
        exit(1)


def remove_script(script: Path) -> None:
    """Removes a service script from the scripts directory."""
    script_path = SCRIPTS_DIR / script.name

    if not script_path.exists():
        print(f"Script {script_path} does not exist.")
        return

    try:
        subprocess.run(["sudo", "rm", str(script_path)], check=True)
        print(f"Script {script_path} removed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error removing script {script_path}: {e}")
        exit(1)


def install_unit_file(file: Path) -> None:
    """Installs a service unit file to the services directory."""
    # Ensure the services directory exists
    subprocess.run(["sudo", "mkdir", "-p", str(SERVICES_DIR)], check=True)

    try:
        # Move the temp unit file to the services directory
        subprocess.run(["sudo", "mv", str(file), str(SERVICES_DIR)], check=True)
        print(f"Service unit file {file.name} installed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error installing service unit file {file.name}: {e}")
        exit(1)


def remove_unit(file: Path) -> None:
    """Removes a service unit file from the services directory."""
    try:
        subprocess.run(["sudo", "rm", str(file)], check=True)
        print(f"Service unit file {file.name} removed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error removing service unit file {file.name}: {e}")
        exit(1)


def enable(service_id: str) -> None:
    """Enables the service by enabling its timer."""
    command = ["sudo", "systemctl", "enable", "--now", f"{service_id}.timer"]
    try:
        subprocess.run(command, check=True)
        print(f"Service {service_id} enabled successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error enabling service {service_id}: {e}")
        exit(1)


def run(service_id: str) -> None:
    """Runs the service immediately."""
    command = ["sudo", "systemctl", "start", f"{service_id}.service"]
    try:
        subprocess.run(command, check=True)
        print(f"Service {service_id} started successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error starting service {service_id}: {e}")
        exit(1)


def disable(service_id: str) -> None:
    """Disables the service by disabling its timer."""
    command = ["sudo", "systemctl", "disable", "--now", f"{service_id}.timer"]
    try:
        subprocess.run(command, check=True)
        print(f"Service {service_id} disabled successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error disabling service {service_id}: {e}")
        exit(1)


def exists(service_id: str) -> bool:
    """
    Checks if the service exists in the system.

    Returns:
        `True` if all files exist
        `False` if none exist
        `False` if some files are missing and prints an error message.
    """
    service_unit = SERVICES_DIR / f"{PREFIX + service_id}.service"
    timer_unit = SERVICES_DIR / f"{PREFIX + service_id}.timer"
    script = SCRIPTS_DIR / f"{service_id.replace("_", "-")}.bash"

    all_files_exists = all(
        [
            service_unit.exists(),
            timer_unit.exists(),
            script.exists(),
        ]
    )
    no_files_exists = all(
        [
            not service_unit.exists(),
            not timer_unit.exists(),
            not script.exists(),
        ]
    )

    if all_files_exists:
        return True
    elif no_files_exists:
        return False
    else:
        if not service_unit.exists():
            print(f"Service unit file of {service_unit} is missing.")
        if not timer_unit.exists():
            print(f"Timer unit file of {timer_unit} is missing.")
        if not script.exists():
            print(f"Script file of {script} is missing.")
        print(f"Service {service_id} is not properly installed.")
        return False


def force_remove(service_id: str) -> None:
    """Forcefully removes the service by disabling its timer and removing all related files."""
    service_unit = SERVICES_DIR / f"{PREFIX + service_id}.service"
    timer_unit = SERVICES_DIR / f"{PREFIX + service_id}.timer"
    script = SCRIPTS_DIR / f"{service_id.replace('_', '-')}.bash"

    if service_unit.exists():
        remove_unit(service_unit)
    if timer_unit.exists():
        _execute(f"sudo systemctl disable --now {timer_unit.name}")
        remove_unit(timer_unit)
    if script.exists():
        remove_script(script)
