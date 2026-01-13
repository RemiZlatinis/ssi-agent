"""Validation functions for the Service Status Indicator Agent."""

import re


def validate_schedule(schedule: str) -> None:
    """Validates the systemd timer schedule format.

    Args:
        schedule: Schedule string in systemd timer OnCalendar format

    Raises:
        ValueError: If schedule format is invalid

    Examples of valid formats:
        - *:0/01:00      (Every minute)
        - *:00:00        (Every hour)
        - 0/1:00:00      (Every hour, alternative format)
        - Mon *-*-* 00:00:00  (Every Monday at midnight)
        - *-*-* 00:00:00     (Every day at midnight)
        - daily
        - weekly
        - monthly
        - hourly
    """
    # Special time units
    if schedule.lower() in {"daily", "weekly", "monthly", "hourly"}:
        return

    # Complex schedule patterns
    patterns = [
        # Time-based formats
        r"^\*:[0-9]+/[0-9]+$",  # Every N minutes (simplified format)
        r"^\*:[0-9]+/[0-9]{2}:[0-9]{2}$",  # Every N minutes/hours (extended format)
        r"^\*:[0-9]{2}:[0-9]{2}$",  # Every hour
        r"^0/[0-9]+:[0-9]{2}:[0-9]{2}$",  # Every hour, alternative format
        # Day-based schedules
        r"^(Mon|Tue|Wed|Thu|Fri|Sat|Sun)\s+\*-\*-\*\s+[0-9]{2}:[0-9]{2}:[0-9]{2}$",
        # Generic time-based schedules
        r"^\*-\*-\*\s+[0-9]{2}:[0-9]{2}:[0-9]{2}$",
    ]

    for pattern in patterns:
        if re.match(pattern, schedule):
            return

    raise ValueError(
        f"Invalid schedule format: {schedule}\n"
        "Expected format examples:\n"
        "- *:0/01:00 (every minute)\n"
        "- *:00:00 (every hour)\n"
        "- 0/1:00:00 (every hour, alternative format)\n"
        "- Mon *-*-* 00:00:00 (every Monday at midnight)\n"
        "- *-*-* 00:00:00 (every day at midnight)\n"
        "- daily, weekly, monthly, hourly"
    )
