"""Service Status Indicator Models"""

from enum import Enum
from pydantic import BaseModel
from typing import List
from datetime import datetime


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


class AgentHelloEvent(BaseModel):
    event: str = "agent_hello"
    agent_key: str
    services: List[ServiceInfo]


class ServiceAddedEvent(BaseModel):
    event: str = "service_added"
    service: ServiceInfo


class ServiceRemovedEvent(BaseModel):
    event: str = "service_removed"
    service_id: str


class StatusUpdate(BaseModel):
    """
    Represents a single status update from a service log.
    """

    service_id: str
    timestamp: datetime | None
    status: Status | None
    message: str


class StatusUpdateEvent(BaseModel):
    event: str = "status_update"
    update: StatusUpdate
