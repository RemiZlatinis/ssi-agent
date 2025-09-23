"""Command functions for interacting with systemd and managing service files."""

import subprocess
from datetime import datetime
from pathlib import Path

from .constants import LOG_DIR, PREFIX, SCRIPTS_DIR, SERVICES_DIR
from .models import Status


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
        raise
    except FileNotFoundError as e:
        print(f"Command not found: {command.split()[0]}")
        raise e


def get_enabled_services() -> list[str]:
    """Returns a list of enabled services."""
    command = (
        'systemctl list-unit-files "ssi_*.timer"'
        " --state=enabled --no-legend --no-pager "
        "| awk '{print $1}'"
    )
    output = _execute(command)
    output = output.replace(".timer", "").replace("ssi_", "")
    return output.splitlines() if output else []


def reload_daemon() -> None:
    """Reloads the systemd daemon."""
    _execute("sudo systemctl daemon-reload")


def is_enabled(service_id: str) -> bool:
    """Checks if the corresponding time unit for the service is enabled."""
    command = ["systemctl", "is-enabled", f"{service_id}.timer"]
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        return result.stdout.strip() == "enabled"
    except subprocess.CalledProcessError:
        return False
        # if e.returncode == 4:
        #     print(f"Service {service_id} is not installed.")
        # print(f"Error on calling systemctl is-enabled for {service_id}.timer")
        # exit(1)


def install_script(service_id: str, script: Path) -> None:
    """Installs a service script to the scripts directory."""
    target_script = SCRIPTS_DIR / f"{service_id.replace('_', '-')}.bash"

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


def remove_script(service_id: str) -> None:
    """Removes a service script from the scripts directory."""
    target_script = SCRIPTS_DIR / f"{service_id.replace('_', '-')}.bash"

    if not target_script.exists():
        print(f"Script {target_script} does not exist.")
        return

    try:
        subprocess.run(["sudo", "rm", str(target_script)], check=True)
        print(f"Script {target_script} removed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error removing script {target_script}: {e}")
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
    unit = PREFIX + service_id
    command = ["sudo", "systemctl", "enable", "--now", f"{unit}.timer"]
    try:
        subprocess.run(command, check=True)
        print(f"Service {service_id} enabled successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error enabling service {service_id}: {e}")
        exit(1)


def run(service_id: str) -> None:
    """Runs the service immediately."""
    unit = PREFIX + service_id
    command = ["sudo", "systemctl", "start", f"{unit}.service"]
    try:
        subprocess.Popen(command)
    except FileNotFoundError:
        print(f"Error: Command {' '.join(command)} not found.")
        exit(1)
    except Exception as e:
        print(f"Error invoking service {service_id} start: {e}")
        exit(1)


def disable(service_id: str) -> None:
    """Disables the service by disabling its timer."""
    unit = PREFIX + service_id
    command = ["sudo", "systemctl", "disable", "--now", f"{unit}.timer"]
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
    service_script_name = service_id.replace("_", "-")
    script = SCRIPTS_DIR / f"{service_script_name}.bash"

    service_unit_exists = service_unit.exists()
    timer_unit_exists = timer_unit.exists()
    script_exists = script.exists()

    all_files_exist = all([service_unit_exists, timer_unit_exists, script_exists])
    no_files_exist = not any([service_unit_exists, timer_unit_exists, script_exists])

    if all_files_exist:
        return True
    elif no_files_exist:
        return False
    else:
        print(f"Service {service_id} is not properly installed.")
        if not service_unit.exists():
            print(f"Service unit file of {service_unit} is missing.")
        if not timer_unit.exists():
            print(f"Timer unit file of {timer_unit} is missing.")
        if not script.exists():
            print(f"Script file of {script} is missing.")
        return False


def force_remove(service_id: str) -> None:
    """
    Forcefully removes the service by disabling its timer
    and removing all related files.
    """
    service_unit = SERVICES_DIR / f"{PREFIX + service_id}.service"
    timer_unit = SERVICES_DIR / f"{PREFIX + service_id}.timer"
    service_script_name = service_id.replace("_", "-")
    script = SCRIPTS_DIR / f"{service_script_name}.bash"

    if service_unit.exists():
        remove_unit(service_unit)
    if timer_unit.exists():
        _execute(f"sudo systemctl disable --now {timer_unit.name}")
        remove_unit(timer_unit)
    if script.exists():
        remove_script(service_id)


def set_service_status(service_id: str, status: Status) -> None:
    """Appends the give status on the services logs"""
    service_logs = LOG_DIR / f"{service_id}.log"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_log = f"{timestamp}, {status}, Manual status set"
    command = f"sudo sh -c 'echo \"{new_log}\" >> {service_logs}'"
    _execute(command)
