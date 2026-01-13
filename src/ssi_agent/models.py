"""Service Status Indicator Models"""

from datetime import datetime
from enum import Enum
from pathlib import Path

from pydantic import BaseModel, Field


class Status(Enum):
    """
    An enumeration representing the possible statuses of a service.
    """

    OK = "OK"
    UPDATE = "UPDATE"
    WARNING = "WARNING"
    FAILURE = "FAILURE"
    ERROR = "ERROR"

    def __str__(self) -> str:
        return self.value


class ServiceInfo(BaseModel):
    """
    A Pydantic model representing the static information about a service
    that is sent to the backend.
    """

    id: str
    name: str
    description: str
    version: str
    schedule: str


class Service(BaseModel):
    """
    Internal data model for a service, including local filesystem paths
    and execution settings.
    """

    id: str
    name: str
    description: str
    version: str
    schedule: str
    script: Path
    timeout: int = Field(default=20, ge=1)
    is_enabled: bool = False  # Is the systemd timer active?


class StatusUpdate(BaseModel):
    """
    Represents a single status update from a service log.
    """

    service_id: str
    timestamp: datetime | None
    status: Status | None
    message: str
