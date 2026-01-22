from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel


class ServiceStatus(str, Enum):
    OK = "OK"
    UPDATE = "UPDATE"
    WARNING = "WARNING"
    FAILURE = "FAILURE"
    ERROR = "ERROR"
    UNKNOWN = "UNKNOWN"

    def __str__(self) -> str:
        return self.value


# --- Models ---


class AgentServiceDataModel(BaseModel):
    id: str  # This is the human readable service-id
    name: str
    description: str
    version: str
    schedule: str


# --- Payloads ---


class AgentReadyPayload(BaseModel):
    services: list[AgentServiceDataModel]


class AgentServiceAddedPayload(BaseModel):
    service: AgentServiceDataModel


class AgentServiceRemovedPayload(BaseModel):
    service_id: str


class AgentServiceStatusUpdatePayload(BaseModel):
    service_id: str
    status: ServiceStatus
    message: str
    timestamp: datetime


# --- Event Models ---


class AgentReadyEvent(BaseModel):
    type: Literal["agent.ready"] = "agent.ready"
    data: AgentReadyPayload


class AgentServiceAddedEvent(BaseModel):
    type: Literal["agent.service_added"] = "agent.service_added"
    data: AgentServiceAddedPayload


class AgentServiceRemovedEvent(BaseModel):
    type: Literal["agent.service_removed"] = "agent.service_removed"
    data: AgentServiceRemovedPayload


class AgentServiceStatusUpdateEvent(BaseModel):
    type: Literal["agent.service_status_update"] = "agent.service_status_update"
    data: AgentServiceStatusUpdatePayload


AgentEvent = (
    AgentReadyEvent
    | AgentServiceAddedEvent
    | AgentServiceRemovedEvent
    | AgentServiceStatusUpdateEvent
)
