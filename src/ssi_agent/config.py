"""Configuration management for the Service Status Indicator Agent."""

import json
from typing import Literal, Never

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


def set_backend_url(backend_url: str) -> None:
    """Sets the backend URL in the config file."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    config = {}
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE) as f:
                config = json.load(f)
        except json.JSONDecodeError:
            # Handle empty or corrupted file
            pass

    config["backend_url"] = backend_url

    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)


def get_uri(
    uri: Literal[
        "websocket",
        "unregister",
        "whoami",
        "initiate_registration",
        "registration_status",
        "register_finalize",
    ],
) -> str | Never:
    try:
        with open(CONFIG_FILE) as f:
            config = json.load(f)
            backend_url = config.get("backend_url")
            if not backend_url:
                raise ValueError('"backend_url" not found in config file.')

            s = "s" if backend_url.startswith("https") else ""
            host = backend_url.replace(f"http{s}://", "")
            host = host[:-1] if host.endswith("/") else host

            UriTemplates = {
                "websocket": f"ws{s}://{host}/ws/agent/",
                "unregister": f"http{s}://{host}/api/agents/me/",
                "whoami": f"http{s}://{host}/api/agents/me/",
                "initiate_registration": f"http{s}://{host}/api/agents/register/initiate/",
                "registration_status": f"http{s}://{host}/api/agents/register/status/",
                "register_finalize": f"http{s}://{host}/api/agents/register/finalize/",
            }

            return UriTemplates[uri]
    except json.JSONDecodeError:
        raise ValueError(f"Config file {CONFIG_FILE} is not valid JSON.")
    except FileNotFoundError:
        raise FileNotFoundError(f"Config file {CONFIG_FILE} does not exist.")
