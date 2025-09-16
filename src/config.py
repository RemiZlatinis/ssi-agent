"""Configuration management for the Service Status Indicator Agent."""

import json

from .constants import CONFIG_DIR, CONFIG_FILE


def save_agent_key(agent_key: str) -> None:
    """Saves the agent key to the config file."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    config = {}
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE) as f:
                config = json.load(f)
        except json.JSONDecodeError:
            # Handle empty or corrupted file
            pass

    config["agent_key"] = agent_key

    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)


def get_agent_key() -> str | None:
    """Retrieves the agent key from the config file."""
    if not CONFIG_FILE.exists():
        return None

    try:
        with open(CONFIG_FILE) as f:
            config = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return None

    return config.get("agent_key")  # type: ignore[no-any-return]


def remove_agent_key() -> None:
    """Removes the agent key from the config file."""
    if not CONFIG_FILE.exists():
        return

    try:
        with open(CONFIG_FILE) as f:
            config = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return

    if "agent_key" in config:
        del config["agent_key"]
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=4)
