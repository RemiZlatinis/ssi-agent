"""Configuration management for the Service Status Indicator Agent."""

import json
from pathlib import Path

APP_NAME = "ssi-agent"
CONFIG_DIR = Path.home() / ".config" / APP_NAME
CONFIG_FILE = CONFIG_DIR / "config.json"

BACKEND_HOST = "192.168.1.20:8000"
URI_REGISTER = f"http://{BACKEND_HOST}/api/agents/register/"
URI_UNREGISTER = f"http://{BACKEND_HOST}/api/agents/unregister/"
URI_WHOAMI = f"http://{BACKEND_HOST}/api/agents/me/"


def save_agent_key(agent_key: str):
    """Saves the agent key to the config file."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    config = {}
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r") as f:
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
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return None

    return config.get("agent_key")
