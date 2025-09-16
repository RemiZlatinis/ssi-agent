"""CLI tool for managing the Service Status Indicator Agent."""

import click
import requests

from . import commands, config
from .service import Service


@click.group()  # type: ignore[misc]
def main() -> None:
    """A CLI tool for managing the Service Status Indicator Agent."""
    pass


@main.command()  # type: ignore[misc]
@click.argument("service_script_path", type=click.Path(exists=True, dir_okay=False))  # type: ignore[misc]
def add(service_script_path: str) -> None:
    """Add a new service."""
    try:
        service = Service(service_script_path)
        if service.exists():
            click.echo(f"Service '{service.name}' already exists.")
            return

        service.enable()
        click.echo(f"Service '{service.name}' added successfully.")
    except Exception as e:
        click.echo(f"Failed to add service: {e}")


@main.command()  # type: ignore[misc]
@click.argument("service_id")  # type: ignore[misc]
@click.option("-f", "--force", is_flag=True, help="Force removal of the service.")  # type: ignore[misc]
def remove(service_id: str, force: bool) -> None:
    """Remove a service by its ID."""
    if force:
        try:
            commands.force_remove(service_id)
            click.echo(f"Service '{service_id}' removed forcefully.")
        except Exception as e:
            click.echo(f"Failed to force remove service: {e}")
        return

    service = Service.get_service(service_id)
    if not service:
        click.echo(f"Service '{service_id}' not found.")
        return

    try:
        service.disable()
        click.echo(f"Service '{service.name}' removed successfully.")
    except Exception as e:
        click.echo(f"Failed to remove service: {e}")


@main.command()  # type: ignore[misc]
def list() -> None:
    """List all available services."""
    services = Service.get_services()
    if not services:
        click.echo("No services found.")
        return

    # Determine the maximum width for each column for pretty printing
    max_id_len = max([len(s.id) for s in services] + [len("ID")])
    max_name_len = max([len(s.name) for s in services] + [len("Name")])
    max_version_len = max([len(s.version) for s in services] + [len("Version")])
    max_schedule_len = max([len(s.schedule) for s in services] + [len("Schedule")])
    max_status_len = max(
        [len(str(s.get_last_status()) or "N/A") for s in services] + [len("Status")]
    )

    # Header
    header = (
        f"{'ID':<{max_id_len}} | {'Name':<{max_name_len}} | "
        f"{'Version':<{max_version_len}} | {'Schedule':<{max_schedule_len}}"
        f" | {'Status':<{max_status_len}}"
    )
    click.echo(header)
    click.echo("-" * len(header))

    # Rows
    for service in services:
        status = service.get_last_status() or "N/A"
        click.echo(
            f"{service.id:<{max_id_len}} | {service.name:<{max_name_len}} | "
            f"{service.version:<{max_version_len}}"
            f" | {service.schedule:<{max_schedule_len}} | "
            f"{str(status):<{max_status_len}}"
        )


@main.command()  # type: ignore[misc]
@click.argument("service_id", required=False)  # type: ignore[misc]
@click.option("-d", "--details", is_flag=True, help="Display detailed status.")  # type: ignore[misc]
def status(service_id: str | None, details: bool) -> None:
    """Display the status of a service or all services."""
    if service_id:
        service = Service.get_service(service_id)
        if not service:
            click.echo(f"Service '{service_id}' not found.")
            return
        services = [service]
    else:
        services = Service.get_services()

    if details:
        for service in services:
            timestamp, status, message = service.get_last_status_details()
            click.echo(f"Service: {service.name} ({service.id})")
            click.echo(f"  - Status: {status or 'N/A'}")
            click.echo(f"  - Timestamp: {timestamp or 'N/A'}")
            click.echo(f"  - Message: {message or 'N/A'}")
    else:
        for service in services:
            click.echo(f"{service.name}: {service.get_last_status() or 'N/A'}")


@main.command()  # type: ignore[misc]
@click.argument("service_id")  # type: ignore[misc]
def run(service_id: str) -> None:
    """Runs a service script by its service ID."""
    service = Service.get_service(service_id)
    if not service:
        click.echo(f"Service '{service_id}' not found.")
        return
    try:
        service.run()
        click.echo(f"Service '{service.name}' script was triggered.")
    except Exception as e:
        click.echo(f"Failed to run service script: {e}")


@main.command()  # type: ignore[misc]
@click.argument("uuid_agent_key")  # type: ignore[misc]
def register(uuid_agent_key: str) -> None:
    """Register the agent with an agent key."""
    try:
        response = requests.post(
            config.URI_REGISTER, json={"key": uuid_agent_key}, timeout=5
        )
        response.raise_for_status()  # Raise an exception for HTTP errors
        response_message = response.json().get("message", "No message from server.")

        config.save_agent_key(uuid_agent_key)
        click.echo(response_message)
    except requests.exceptions.RequestException as e:
        click.echo(f"Failed to register agent key: {e}")
        if e.response:
            click.echo(f"Backend response: {e.response.text}")
    except Exception as e:
        click.echo(f"Failed to register agent key: {e}")


@main.command()  # type: ignore[misc]
def unregister() -> None:
    """Unregister the agent and remove the agent key."""
    agent_key = config.get_agent_key()
    if not agent_key:
        click.echo("No agent key found. Agent is not registered.")
        return

    try:
        headers = {"Authorization": f"Agent {agent_key}"}
        response = requests.post(config.URI_UNREGISTER, headers=headers, timeout=5)
        response.raise_for_status()  # Raise an exception for HTTP errors
        response_message = response.json().get("message", "No message from server.")

        config.remove_agent_key()
        click.echo(response_message)
    except requests.exceptions.RequestException as e:
        click.echo(f"Failed to unregister agent: {e}")
        if e.response:
            click.echo(f"Backend response: {e.response.text}")
    except Exception as e:
        click.echo(f"Failed to unregister agent: {e}")


@main.command()  # type: ignore[misc]
def whoami() -> None:
    """Display information about the current agent."""
    agent_key = config.get_agent_key()
    if not agent_key:
        click.echo("No agent key found. Agent is not registered.")
        return

    try:
        headers = {"Authorization": f"Agent {agent_key}"}
        response = requests.get(config.URI_WHOAMI, headers=headers, timeout=5)
        response.raise_for_status()  # Raise an exception for HTTP errors
        agent_data = response.json()

        click.echo("Agent Information:")
        click.echo(f"  ID: {agent_data.get('id')}")
        click.echo(f"  Name: {agent_data.get('name')}")
        click.echo(f"  Created At: {agent_data.get('created_at')}")
        click.echo(f"  IP Address: {agent_data.get('ip_address')}")
        click.echo(f"  Registration Status: {agent_data.get('registration_status')}")

        owner_data = agent_data.get("owner")
        if owner_data:
            click.echo("  Owner:")
            click.echo(f"    ID: {owner_data.get('id')}")
            click.echo(f"    Username: {owner_data.get('username')}")
            click.echo(f"    Email: {owner_data.get('email') or 'N/A'}")

    except requests.exceptions.RequestException as e:
        click.echo(f"Failed to retrieve agent information: {e}")
        if e.response:
            click.echo(f"Backend response: {e.response.text}")
    except Exception as e:
        click.echo(f"Failed to retrieve agent information: {e}")


if __name__ == "__main__":
    main()
