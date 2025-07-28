"""
This module defines the data models used in the Service Status Indicator application.

Classes:
    Status: An enumeration representing the possible statuses of a service.
    Service: A data class representing a service with its attributes and methods.

Functions:
    service_from_file: Creates a Service instance from a file.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional
import re


class Status(Enum):
    """
    An enumeration representing the possible statuses of a service.

    Attributes:
        OK: The service is operating normally.
        UPDATE: The service has updates available.
        WARNING: The service is experiencing issues but is still operational.
        FAILURE: The service has failed.
        ERROR: The service is in an error state.
    """

    OK = "OK"
    UPDATE = "UPDATE"
    WARNING = "WARNING"
    FAILURE = "FAILURE"
    ERROR = "ERROR"

    def __str__(self) -> str:
        return self.value


@dataclass
class Service:
    """
    A data class representing a service with its attributes and methods.

    Attributes:
        name (str): The name of the service.
        description (str): A description of the service.
        version (str): The version of the service.
        interval (str): The interval at which the service should be checked.
        script (str): The script associated with the service.
        status (Status): The current status of the service.
        timeout (int): The timeout for the service.
        message (str): An optional message associated with the service.
        is_active (bool): Whether the service is active.
        last_check (Optional[datetime]): The last time the service was checked.

    Methods:
        __post_init__: Validate service attributes after initialization.
    """

    name: str
    description: str
    version: str
    interval: str
    script: str

    status: Status = field(default=Status.ERROR)
    timeout: int = field(default=20)
    message: str = field(default="")
    is_active: bool = field(default=False)
    last_check: Optional[datetime] = field(default=None)

    def __post_init__(self) -> None:
        """Validate service attributes after initialization."""
        if not self.name:
            raise ValueError("Service name cannot be empty")
        if self.timeout < 0:
            raise ValueError("Timeout must be positive")


def service_from_file(file_path: str | Path) -> Service:
    """Create a Service instance from a file."""
    file_path = Path(file_path)
    if not file_path.is_file():
        raise FileNotFoundError(f"Service file not found: {file_path}")
    with open(file_path, "r", encoding="utf-8") as file:
        data = file.read().strip().splitlines()

        if data[0] != "#!/bin/bash":
            raise ValueError("Invalid service file: must start with '#!/bin/bash'")
        if len(data) < 5:
            # Valid script cannot be less then 6 lines
            raise ValueError("Invalid or misformed service file")

        # Mapping attributes
        name = ""
        if not str(data[2]).startswith("# name:"):
            raise ValueError(
                "Invalid service file: missing or malformed name attribute"
            )
        else:
            name = data[2].split("# name:", 1)[1].strip()
            if not name:
                raise ValueError("Invalid service file: name cannot be empty")

        description = ""
        if not str(data[3]).startswith("# description:"):
            raise ValueError(
                "Invalid service file: missing or malformed description attribute"
            )
        else:
            description = data[3].split("# description:", 1)[1].strip()
            if not description:
                raise ValueError("Invalid service file: description cannot be empty")

        version = ""
        if not str(data[4]).startswith("# version:"):
            raise ValueError(
                "Invalid service file: missing or malformed version attribute"
            )
        else:
            version = data[4].split("# version:", 1)[1].strip()
            if not version:
                raise ValueError("Invalid service file: version cannot be empty")

        interval = ""
        if not str(data[5]).startswith("# interval:"):
            raise ValueError(
                "Invalid service file: missing or malformed interval attribute"
            )
        else:
            interval = data[5].split("# interval:", 1)[1].strip()
            if not interval:
                raise ValueError("Invalid service file: interval cannot be empty")
            # Validate interval format (e.g. 1 * * * *)
            if not re.match(
                r"^(\\d+|\\*) (\\d+|\\*) (\\d+|\\*) (\\d+|\\*) (\\d+|\\*)$", interval
            ):
                raise ValueError(
                    "Invalid service file: interval must be in cron format (e.g. '1 * * * *')"
                )

        timeout = 20
        if str(data[6]).startswith("# timeout:"):
            try:
                timeout = int(data[6].split("# timeout:", 1)[1].strip())
                if timeout < 0:
                    raise ValueError("Invalid service file: timeout must be positive")
            except ValueError as exc:
                raise ValueError(
                    "Invalid service file: timeout must be an integer"
                ) from exc

        return Service(
            name=name,
            description=description,
            version=version,
            interval=interval,
            script="\n".join(data),
            timeout=timeout,
        )
