"""Service Status Indicator Models"""

from enum import Enum


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
