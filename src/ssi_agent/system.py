"""
SSI Agent - System Abstraction Layer

This module provides an interface for interacting with the Linux system
(systemd, protected file systems). It abstracts away subprocess calls
and sudo requirements, providing a typed and exception-safe API.
"""

import logging
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)


# --- Internal Execution Engine ---


def _run(
    cmd: list[str], check: bool = True, capture: bool = True
) -> subprocess.CompletedProcess[str]:
    """
    Executes a command and handles standard failure cases.

    Args:
        cmd: List of command arguments.
        check: If True, raises SystemdError on non-zero exit code.
        capture: If True, captures stdout and stderr.
    """
    try:
        result = subprocess.run(cmd, check=check, capture_output=capture, text=True)
        return result
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.strip() if e.stderr else str(e)
        logger.error(f"Command execution failed: {' '.join(cmd)}")
        logger.debug(f"Process Stderr: {error_msg}")
        raise RuntimeError(f"System command failed: {error_msg}") from e
    except FileNotFoundError as e:
        logger.error(f"Binary not found: {cmd[0]}")
        raise RuntimeError(f"Required system binary '{cmd[0]}' is missing.") from e


# --- Systemd Management ---


def restart_agent() -> None:
    """Restarts the agent."""
    _run(["sudo", "systemctl", "restart", "ssi-agent.service"])
    logger.info("Agent restarted successfully.")


def reload_daemon() -> None:
    """Reloads the systemd manager configuration (systemctl daemon-reload)."""
    _run(["sudo", "systemctl", "daemon-reload"])


def enable_unit(unit_name: str, now: bool = True) -> None:
    """
    Enables a systemd unit.

    Args:
        unit_name: Full name of the unit (e.g., 'ssi_service.timer').
        now: If True, also starts the unit immediately.
    """
    cmd = ["sudo", "systemctl", "enable"]
    if now:
        cmd.append("--now")
    cmd.append(unit_name)
    _run(cmd)


def disable_unit(unit_name: str, now: bool = True) -> None:
    """
    Disables a systemd unit.

    Args:
        unit_name: Full name of the unit.
        now: If True, also stops the unit immediately.
    """
    cmd = ["sudo", "systemctl", "disable"]
    if now:
        cmd.append("--now")
    cmd.append(unit_name)
    _run(cmd)


def start_unit(unit_name: str, background: bool = False) -> None:
    """
    Starts a systemd unit.

    Args:
        unit_name: Full name of the unit.
        background: If True, invokes start without waiting or completion.
    """
    cmd = ["sudo", "systemctl", "start", unit_name]
    if background:
        try:
            # We use Popen here to fire and forget
            subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as e:
            raise RuntimeError(f"Failed to spawn background start for {unit_name}: {e}")
    else:
        _run(cmd)


def is_unit_enabled(unit_name: str) -> bool:
    """Returns True if the unit is enabled in systemd."""
    try:
        # systemctl is-enabled returns 0 if enabled, 1 if disabled.
        result = _run(["systemctl", "is-enabled", unit_name], check=False)
        return result.stdout.strip() == "enabled"
    except (RuntimeError, subprocess.SubprocessError):
        return False


def list_units(pattern: str, state: str = "enabled") -> list[str]:
    """
    Queries systemd for unit files matching a pattern.

    Returns:
        A list of unit names (e.g., ['ssi_web.timer', 'ssi_db.timer']).
    """
    cmd = ["systemctl", "list-unit-files", pattern, "--no-legend", "--no-pager"]
    if state:
        cmd.extend(["--state", state])

    result = _run(cmd)
    # Each line is "unit_name.type status"
    return [line.split()[0] for line in result.stdout.splitlines() if line.strip()]


# --- Privileged File Management ---


def copy_file(src: Path, dst: Path, mode: str | None = None) -> None:
    """
    Copies a file to a destination using sudo.

    Args:
        src: Source path.
        dst: Destination path.
        mode: Optional octal permissions (e.g., '755').
    """
    _run(["sudo", "cp", str(src), str(dst)])
    if mode:
        set_permissions(dst, mode)


def move_file(src: Path, dst: Path) -> None:
    """Moves a file using sudo."""
    _run(["sudo", "mv", str(src), str(dst)])


def remove_file(path: Path) -> None:
    """Removes a file using sudo. Does nothing if file doesn't exist."""
    if path.exists():
        _run(["sudo", "rm", str(path)])


def make_directory(path: Path, parents: bool = True) -> None:
    """Creates a directory using sudo."""
    cmd = ["sudo", "mkdir"]
    if parents:
        cmd.append("-p")
    cmd.append(str(path))
    _run(cmd)


def set_permissions(path: Path, mode: str) -> None:
    """Sets octal permissions for a file/directory using sudo chmod."""
    _run(["sudo", "chmod", mode, str(path)])


def write_log_line(log_path: Path, content: str) -> None:
    """
    Appends a line to a log file in a privileged directory.
    Useful for manual status overrides.
    """
    # Use tee -a to append without shell interpolation
    try:
        subprocess.run(
            ["sudo", "tee", "-a", str(log_path)],
            input=content + "\n",
            text=True,
            stdout=subprocess.DEVNULL,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to write log line to {log_path}: {e}")
        raise RuntimeError(f"Failed to write to log file: {e}")


def tail_file(path: Path, lines: int = 50, follow: bool = False) -> None:
    """
    Executes a privileged tail on a file and streams output to stdout.

    This is an interactive command that bypasses the internal '_run'
    capture to allow real-time streaming to the user's terminal.
    """
    cmd = ["sudo", "tail", f"-n{lines}"]
    if follow:
        cmd.append("-f")
    cmd.append(str(path))

    try:
        # We don't use _run here because we want to allow
        # the process to take over the terminal's stdout.
        subprocess.run(cmd)
    except KeyboardInterrupt:
        # Expected when following with -f
        pass
