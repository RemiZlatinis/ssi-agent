import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional


import commands
from models import Status
from constants import PREFIX, SERVICES_DIR, SCRIPTS_DIR
from validators import validate_schedule


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
    def _from_file(cls, script: Path) -> "Service":
        """Creates a Service object from a service script file.

        Args:
            script: Path to the service script file

        Returns:
            Service: New service instance

        Raises:
            FileNotFoundError: If script file doesn't exist
            ValueError: If required metadata is missing or invalid
        """
        if not script.exists():
            raise FileNotFoundError(f"Service script {script} does not exist.")

        try:
            with open(script, "r", encoding="utf-8") as f:
                content = f.read()

                # Extract metadata from the script
                name = re.search(r"# name:\s*(.+)", content)
                if not name:
                    raise ValueError("Service script must contain a name metadata.")
                name = name.group(1).strip()

                description = re.search(r"# description:\s*(.+)", content)
                if not description:
                    raise ValueError(
                        "Service script must contain a description metadata."
                    )
                description = description.group(1).strip()

                version = re.search(r"# version:\s*(.+)", content)
                if not version:
                    raise ValueError("Service script must contain a version metadata.")
                version = version.group(1).strip()

                schedule = re.search(r"# schedule:\s*(.+)", content)
                if not schedule:
                    raise ValueError("Service script must contain a schedule metadata.")
                schedule = schedule.group(1).strip()

                return cls(
                    name=name,
                    description=description,
                    version=version,
                    schedule=schedule,
                    script=script,
                )
        except Exception as e:
            raise ValueError(f"Failed to parse service script: {e}") from e

    @classmethod
    def services(cls) -> list["Service"]:
        """Returns a list of all enabled services."""
        services_ids = commands.get_enabled_services()
        services = []

        for service_id in services_ids:
            script_path = cls._get_script_for_service(service_id)
            if script_path and script_path.exists():
                service = cls._from_file(script_path)
                services.append(service)

        return services

    def is_enabled(self) -> bool:
        """Checks if the service is enabled on the system."""
        return commands.is_enabled(PREFIX + self.id)

    def enable(self) -> None:
        """Enables the service."""
        if self.is_enabled():
            print(f"Service {self.name} is already enabled.")
            return

        # If the script in not installed, copy it to the scripts directory
        script_target = SCRIPTS_DIR / self.script.name
        if not script_target.exists():
            commands.install_script(self.script)
        else:
            print(
                f"Script {self.script.name} already exists in {SCRIPTS_DIR}. Skipping installation."
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

        #Remove the script
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
