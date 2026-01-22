"""Service Status Indicator Models"""

from pathlib import Path

from pydantic import BaseModel, Field

from ssi_agent.events import ServiceStatus


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


Status = ServiceStatus
