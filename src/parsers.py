"""Helper parser functions"""

from datetime import datetime

from .models import Status


def parse_log_line(line: str) -> tuple[datetime | None, Status | None, str | None]:
    """
    Parses a log line to extract the timestamp, status and optional message.

    Args:
        line (str): The log line to parse.

    Returns:
        tuple[str, str, str | None]: A tuple containing the timestamp, the status and optionally the message.
    """
    parts = line.split(",", 2)

    timestamp = parts[0].strip()
    timestamp = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S") if timestamp else None

    status = parts[1].strip()
    status = Status[status] if status in Status else None

    message = parts[2].strip() if len(parts) > 2 else None

    return timestamp, status, message
