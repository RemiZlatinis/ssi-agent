from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class Status(Enum):
    OK = "OK"
    UPDATE = "UPDATE"
    WARNING = "WARNING"
    FAILURE = "FAILURE"
    ERROR = "ERROR"

    def __str__(self) -> str:
        return self.value

@dataclass
class Service:
    name: str
    description: str
    version: str
    interval: str
    script: str

    status: Status = field(default=Status.ERROR)
    timeout: int = field(default=20)
    message: str = field(default="")
    is_active: bool= field(default=False)
    last_check: Optional[datetime] = field(default=None)

    def __post_init__(self) -> None:
        """Validate service attributes after initialization."""
        if not self.name:
            raise ValueError("Service name cannot be empty")
        if self.timeout < 0:
            raise ValueError("Timeout must be positive")