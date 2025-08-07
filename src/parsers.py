"""Helper parser functions"""


def parse_log_line(line: str) -> tuple[str, str, str | None]:
    """
    Parses a log line to extract the timestamp, status and optional message.

    Args:
        line (str): The log line to parse.

    Returns:
        tuple[str, str, str | None]: A tuple containing the timestamp, the status and optionaly the message.
    """
    parts = line.split(",", 2)
    timestamp = parts[0].strip()
    status = parts[1].strip()
    message = parts[2].strip() if len(parts) > 2 else None

    return timestamp, status, message
