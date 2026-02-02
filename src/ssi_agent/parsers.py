"""Helper parser functions"""

from datetime import UTC, datetime

from .events import ServiceStatus


def parse_log_line(
    line: str,
) -> tuple[datetime | None, ServiceStatus | None, str | None]:
    """
    Parses a log line to extract the timestamp, status and optional message.

    Args:
        line (str): The log line to parse.

    Returns:
        tuple[datetime | None, ServiceStatus | None, str | None]: A tuple containing
        the timestamp, the status and optionally the message.
    """
    try:
        parts = line.split(",", 2)
        if len(parts) < 2:
            return None, None, None

        timestamp = parts[0].strip()
        timestamp_dt: datetime | None = (
            datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S") if timestamp else None
        )

        # Convert to UTC
        local_timezone = datetime.now().astimezone().tzinfo
        if timestamp_dt:
            timestamp_dt = timestamp_dt.replace(tzinfo=local_timezone).astimezone(UTC)

        status_str = parts[1].strip()
        status = ServiceStatus(status_str)

        message = parts[2].strip() if len(parts) > 2 else None

        return timestamp_dt, status, message
    except (ValueError, IndexError):
        return None, None, None
