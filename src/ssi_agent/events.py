"""
SSI Agent - Event Models

This module defines the Data Transfer Objects (DTOs) used for communication
between the SSI Agent and the SSI Backend via WebSockets.

These classes act as wrappers or "Envelopes" for the core data models,
ensuring that every message sent over the wire follows a consistent
schema that the backend can parse.

Naming Convention:
    All classes in this module should suffix with 'Event' to distinguish
    them from internal domain models.
"""

from pydantic import BaseModel

from .models import ServiceInfo, StatusUpdate


class AgentHelloEvent(BaseModel):
    """
    The initial handshake event sent by the agent upon connection.
    Contains the agent identification and the list of currently managed services.
    """

    event: str = "agent_hello"
    agent_key: str
    services: list[ServiceInfo]


class ServiceAddedEvent(BaseModel):
    """
    Sent when a new service is added to the agent's management list.
    """

    event: str = "service_added"
    service: ServiceInfo


class ServiceRemovedEvent(BaseModel):
    """
    Sent when a service is removed from the agent's management list.
    """

    event: str = "service_removed"
    service_id: str


class StatusUpdateEvent(BaseModel):
    """
    Sent whenever a service status changes or a new heartbeat/log line is processed.
    """

    event: str = "status_update"
    update: StatusUpdate
