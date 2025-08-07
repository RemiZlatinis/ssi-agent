"""Command functions for interacting with systemd and managing service files."""

import subprocess
from pathlib import Path

from constants import SERVICES_DIR, SCRIPTS_DIR


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


def install_script(script: Path) -> None:
    """Installs a service script to the scripts directory."""
    target_script = SCRIPTS_DIR / script.name

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
