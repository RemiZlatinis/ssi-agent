from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional, TypedDict
import re

from .constants import PREFIX, SERVICES_DIR, SCRIPTS_DIR, LOG_DIR
from .models import Status
from .parsers import parse_log_line
from .validators import validate_schedule
from . import commands

ServiceDict = TypedDict(
    "ServiceDict",
    {
        "name": str,
        "description": str,
        "version": str,
        "schedule": str,
        "script": Path,
        "timeout": int,
    },
)


@dataclass
class Service:
    """ """

    # Attributes parsed from the service script
    name: str
    description: str
    version: str
    schedule: str  # OnCalendar format for systemd timers
    script: Path

    # Derived attributes
    id: str = field(init=False)
    timeout: int = field(default=20)  # in seconds

    def __init__(self, service_script: Path | str):
        """Initializes a Service object from a service script file.

        Args:
            service_script: Path to the service script file
        """
        service_script = Path(service_script)
        if not service_script.exists() and not service_script.is_file():
            raise FileNotFoundError(f"Service script {service_script} does not exist.")
        if service_script.suffix != ".bash":
            raise ValueError("Service script must be a .bash file.")

        # Parse the service script to extract metadata
        service_data = self._script_parser(service_script)
        self.name = service_data["name"]
        self.description = service_data["description"]
        self.version = service_data["version"]
        self.schedule = service_data["schedule"]
        self.script = service_data["script"]
        self.timeout = service_data["timeout"]
        self.__post_init__()

    def __post_init__(self) -> None:
        """Validate service attributes after initialization and set derived fields."""
        # Validate attributes
        if not (3 <= len(self.name) <= 60):
            raise ValueError("Service name must be between 3 and 60 characters.")
        if len(self.description) > 255:
            raise ValueError("Service description cannot exceed 255 characters.")
        if self.timeout <= 1:
            raise ValueError("Timeout cannot be less then a second.")
        if self.timeout > 60:
            raise ValueError("Timeout cannot be greater than 60 seconds.")

        validate_schedule(self.schedule)

        # Set the id based on the name in snake case
        self.id = self.name.replace(" ", "_").lower()

    @classmethod
    def _get_script_for_service(cls, service_id: str) -> Optional[Path]:
        """
        Retrieves the script path from a service unit file.

        Args:
            service_id: The ID of the service

        Returns:
            Path object if script is found, None otherwise
        """
        service_unit = Path(SERVICES_DIR) / f"{PREFIX + service_id}.service"
        if not service_unit.exists():
            print(f"Service unit file {service_unit.name} does not exist.")
            return None

        try:
            with open(service_unit, "r", encoding="utf-8") as f:
                content = f.read()
                # ExecStart=/bin/bash -c 'some/path/to/script.bash'
                script_match = re.search(
                    r"^ExecStart=/bin/bash -c '(.+)'", content, re.MULTILINE
                )
                if script_match:
                    script_path = script_match.group(1).strip()
                    script_path = Path(script_path)
                    if script_path.exists():
                        return script_path
                    else:
                        print(f"Script {script_path} does not exist.")
                        return None
        except Exception as e:
            print(f"Error reading service unit file: {e}")

        return None

    @classmethod
    def _script_parser(cls, script: Path) -> ServiceDict:
        """Parses a service script file and returns a ServiceDict.

        Args:
            script: Path to the service script file
        """
        if not script.exists():
            raise FileNotFoundError(f"Service script {script} does not exist.")

        try:
            with open(script, "r", encoding="utf-8") as f:
                content = f.read()

                # Extract metadata from the script
                name = re.search(r"# name:\s*(.+)", content)
                description = re.search(r"# description:\s*(.+)", content)
                version = re.search(r"# version:\s*(.+)", content)
                schedule = re.search(r"# schedule:\s*(.+)", content)
                timeout = re.search(r"# timeout:\s*(\d+)", content)

                if not name:
                    raise ValueError("Service script must contain a name metadata.")
                if not description:
                    raise ValueError(
                        "Service script must contain a description metadata."
                    )
                if not version:
                    raise ValueError("Service script must contain a version metadata.")
                if not schedule:
                    raise ValueError("Service script must contain a schedule metadata.")

                return ServiceDict(
                    name=name.group(1).strip(),
                    description=description.group(1).strip(),
                    version=version.group(1).strip(),
                    schedule=schedule.group(1).strip(),
                    script=script,
                    timeout=int(timeout.group(1).strip()) if timeout else 20,
                )
        except Exception as e:
            raise ValueError(f"Failed to parse service script: {e}") from e

    @classmethod
    def get_services(cls) -> list["Service"]:
        """Returns a list of all enabled services."""
        services_ids = commands.get_enabled_services()
        services = []

        for service_id in services_ids:
            service = cls.get_service(service_id)
            if service:
                services.append(service)

        return services

    @classmethod
    def get_service(cls, service_id: str) -> Optional["Service"]:
        """Retrieves a service by its ID.

        Args:
            service_id: The ID of the service

        Returns:
            Service object if found, None otherwise
        """
        script_path = cls._get_script_for_service(service_id)
        if script_path and script_path.exists():
            return Service(script_path)
        return None

    def to_dict(self) -> dict[str, str | Path | int]:
        """Converts the service to a dictionary representation."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "schedule": self.schedule,
            "script": str(self.script),
            "timeout": self.timeout,
        }

    def is_enabled(self) -> bool:
        """Checks if the service is enabled on the system."""
        return commands.is_enabled(PREFIX + self.id)

    def enable(self) -> None:
        """
        Enables the service.

        This method installs the service script, creates the service and timer unit files,
        and enables the service timer.
        """
        if self.is_enabled():
            print(f"Service {self.name} is already enabled.")
            return

        # If the script in not installed, copy it to the scripts directory
        script_target = SCRIPTS_DIR / f"{self.id.replace("_", "-")}.bash"
        if not script_target.exists():
            commands.install_script(self.id, self.script)
        else:
            print(
                f"Script {self.id.replace('_', '-')}.bash already exists in {SCRIPTS_DIR}. Skipping installation."
            )

        # If service unit does not exists, create it
        service_file = Path(SERVICES_DIR) / f"{PREFIX+self.id}.service"
        if not service_file.exists():
            # Create service unit file
            content = ""
            service_template_path = Path(__file__).parent / "templates" / "base.service"
            with open(service_template_path, "r", encoding="utf-8") as f:
                template_content = f.read()
                content = template_content.format(
                    id=self.id,
                    description=self.description,
                    script=(SCRIPTS_DIR / self.script.name).absolute(),
                    timeout=self.timeout,
                )
            if not content:
                raise ValueError("Failed to create service unit file content")

            # Write service unit file
            service_unit = Path(f"{PREFIX+self.id}.service")
            with open(service_unit, "w", encoding="utf-8") as file:
                file.write(content)

            # Move the service unit file to the services directory
            commands.install_unit_file(service_unit)
        else:
            print(
                f"Service unit file {service_file.name} already exists. Skipping creation."
            )

        # If timer unit does not exists, create it
        timer_file = Path(SERVICES_DIR) / f"{PREFIX+self.id}.timer"
        if not timer_file.exists():
            # Create timer unit file
            content = ""
            timer_template_path = Path(__file__).parent / "templates" / "base.timer"
            with open(timer_template_path, "r", encoding="utf-8") as f:
                template_content = f.read()
                content = template_content.format(
                    description=self.description,
                    schedule=self.schedule,
                )
            if not content:
                raise ValueError("Failed to create timer unit file content")

            # Write timer unit file
            timer_unit = Path(f"{PREFIX+self.id}.timer")
            with open(timer_unit, "w", encoding="utf-8") as file:
                file.write(content)

            # Move the timer unit file to the services directory
            commands.install_unit_file(timer_unit)
        else:
            print(
                f"Timer unit file {timer_file.name} already exists. Skipping creation."
            )

        commands.reload_daemon()
        commands.enable(PREFIX + self.id)

    def disable(self) -> None:
        """Disables the service."""
        if not self.is_enabled():
            print(f"Service {self.name} is already disabled.")
            return

        # Remove the script
        commands.remove_script(self.script)

        # Disable the service timer
        commands.disable(PREFIX + self.id)

        # Remove its units
        units = [
            Path(SERVICES_DIR) / f"{PREFIX+self.id}.service",
            Path(SERVICES_DIR) / f"{PREFIX+self.id}.timer",
        ]
        for unit in units:
            commands.remove_unit(unit)

        print(f"Service {self.name} disabled successfully.")

    def run(self) -> None:
        """Runs the service script."""
        if not self.exists():
            raise ValueError(f"Service {self.name} does not exist.")

        try:
            commands.run(PREFIX + self.id)
        except Exception as e:
            print(f"Error running service {self.name}: {e}")

    def get_last_status(self) -> Status | None:
        """Retrieves the last status of the service from its logs."""
        service_logs = LOG_DIR / f"{self.id}.log"
        if not service_logs.exists():
            print(f"No logs found for service {self.name}.")
            return None
        try:
            with open(service_logs, "r", encoding="utf-8") as f:
                lines = f.readlines()
                if not lines:
                    return None
                return parse_log_line(lines[-1].strip())[1]  # Return the status part
        except Exception as e:
            print(f"Error reading logs for service {self.name}: {e}")
            return None

    def get_last_status_details(
        self,
    ) -> tuple[datetime | None, Status | None, str | None]:
        """Retrieves the last status of the service from its logs with details."""
        service_logs = LOG_DIR / f"{self.id}.log"
        if not service_logs.exists():
            print(f"No logs found for service {self.name}.")
            return None, None, None
        try:
            with open(service_logs, "r", encoding="utf-8") as f:
                lines = f.readlines()
                if not lines:
                    return None, None, None
                return parse_log_line(lines[-1].strip())  # Return the parsed log line
        except Exception as e:
            print(f"Error reading logs for service {self.name}: {e}")
            return None, None, None

    def exists(self) -> bool:
        """Checks if the service exists in the system."""
        return commands.exists(self.id)
