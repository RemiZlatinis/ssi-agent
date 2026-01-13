"""Helper parser functions"""

from datetime import UTC, datetime

from .models import Status


def parse_log_line(line: str) -> tuple[datetime | None, Status | None, str | None]:
    """
    Parses a log line to extract the timestamp, status and optional message.

    Args:
        line (str): The log line to parse.

    Returns:
        tuple[str, str, str | None]: A tuple containing the timestamp,
        the status and optionally the message.
    """
    parts = line.split(",", 2)

    timestamp = parts[0].strip()
    timestamp_dt: datetime | None = (
        datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S") if timestamp else None
    )

    # Convert to UTC
    local_timezone = datetime.now().astimezone().tzinfo
    timestamp_dt = (
        timestamp_dt.replace(tzinfo=local_timezone).astimezone(UTC)
        if timestamp_dt
        else None
    )

    status_str = parts[1].strip()
    status: Status | None = Status[status_str] if status_str in Status else None

    message = parts[2].strip() if len(parts) > 2 else None

    return timestamp_dt, status, message
