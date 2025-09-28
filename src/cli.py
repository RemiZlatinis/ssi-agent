"""CLI tool for managing the Service Status Indicator Agent."""

import itertools
from time import sleep

import click
import requests

from . import commands, config
from .models import Status
from .service import Service

URI_INITIATE_REGISTRATION = config.get_uri("initiate_registration")
URI_REGISTRATION_STATUS = config.get_uri("registration_status")
URI_UNREGISTER = config.get_uri("unregister")
URI_WHOAMI = config.get_uri("whoami")


@click.group()
def main() -> None:
    """A CLI tool for managing the Service Status Indicator Agent."""
    pass


@main.command()
@click.argument("service_script_path", type=click.Path(exists=True, dir_okay=False))
@click.option("-u", "--update", is_flag=True, help="Update an existing service.")
def add(service_script_path: str, update: bool) -> None:
    """Add a new service."""
    try:
        service = Service(service_script_path)
        if service.exists() and not update:
            click.echo(f"Service '{service.name}' already exists.")
            return

        if service.exists():
            service.disable()

        service.enable()
        action = "updated" if update else "added"
        click.echo(f"Service '{service.name}' {action} successfully.")
    except Exception as e:
        click.echo(f"Failed to add service: {e}")


@main.command()
@click.argument("service_id")
@click.option("-f", "--force", is_flag=True, help="Force removal of the service.")
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


@main.command()
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


@main.command()
@click.argument("service_id", required=False)
@click.option("-d", "--details", is_flag=True, help="Display detailed status.")
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


@main.command()
@click.argument("service_id")
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


@main.group()
def debug() -> None:
    """Commands for debugging services."""
    pass


@debug.command(name="set-status")
@click.argument("service_id")
@click.argument(
    "status", type=click.Choice([s.value for s in Status], case_sensitive=False)
)
def set_status(service_id: str, status: Status) -> None:
    """Manually set the status of a service for debugging."""
    # This is a mock implementation as requested.
    # A real implementation would write a new log line to the service's log file.
    service = Service.get_service(service_id)
    status = Status(status.value.upper())
    if not service:
        click.echo(f"Service '{service_id}' not found.")
        return
    commands.set_service_status(service_id, status)
    click.echo(f"The service '{service.name}' status set to '{status}'.")


@debug.command(name="set-backend")
@click.argument("backend_url")
def set_backend(backend_url: str) -> None:
    """Manually set the backend URL in the configuration file."""
    try:
        config.set_backend_url(backend_url)
        click.echo(f"Backend URL set to '{backend_url}'.")
    except Exception as e:
        click.echo(f"Failed to set backend URL: {e}")


@main.command()
def register() -> None:
    """
    Register the agent.

    Flow:
    1. Agent CLI request for a registration pair (6 digits code + UUID).
    2. User enters the code to the front-end client.
    3.

    """
    response = None
    try:
        # Check if is already registered
        key = config.get_agent_key()
        if key:
            click.echo(
                "Agent is already registered. [You can use"
                " 'ssi unregister' command to unregister']"
            )
            return

        response = requests.post(URI_INITIATE_REGISTRATION, timeout=5)
        response.raise_for_status()  # Raise an exception for HTTP errors
        data = response.json()

        code = data.get("code")
        click.echo(f"🔑 Registration code: {code[:3]}-{code[3:]}")

        registration_id = data.get("id")
        spinner = itertools.cycle("🕐🕑🕒🕓🕔🕕🕖🕗🕘🕙🕚🕛")
        while True:
            response = requests.get(
                f"{URI_REGISTRATION_STATUS}{registration_id}/", timeout=5
            )
            response.raise_for_status()
            data = response.json()
            reg_status = data.get("status")

            if reg_status == "completed":
                # Clear the line and print final message
                click.echo("\r" + " " * 40 + "\r", nl=False)
                key = data.get("credentials").get("key")
                if type(key) is str:
                    config.save_agent_key(key)
                click.echo("✅ Registration completed.")
                break
            elif reg_status == "expired":
                click.echo("\r" + " " * 40 + "\r", nl=False)
                click.echo("❌ Registration expired. Please try again.")
                break
            elif reg_status == "pending":
                for _ in range(12):
                    click.echo(
                        f"\r{next(spinner)} Registration is pending...", nl=False
                    )
                    sleep(5 / 12)  # 5 seconds / 12 icons
    except requests.exceptions.RequestException as e:
        # Note: Truthiness is implemented to be `False` if status code ≥ 400
        if e.response is not None:
            if e.response.status_code == 410:
                click.echo("\r" + " " * 40 + "\r", nl=False)
                click.echo("❌ Registration code expired. Please try again.")
            elif e.response.status_code == 403:
                click.echo("❌ Too many tries. Try later.")
            else:
                click.echo(f"Failed to register agent: {e.response.text}")
    except Exception as e:
        click.echo(f"Failed to register agent (Unknown): {e}")


@main.command()
def unregister() -> None:
    """Unregister the agent and remove the agent key."""
    agent_key = config.get_agent_key()
    if not agent_key:
        click.echo(
            "No agent key found. Agent is not registered. [You can use"
            " 'ssi register' command to register]"
        )
        return

    try:
        headers = {"Authorization": f"Agent {agent_key}"}
        response = requests.post(URI_UNREGISTER, headers=headers, timeout=5)
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


@main.command()
def whoami() -> None:
    """Display information about the current agent."""
    agent_key = config.get_agent_key()
    if not agent_key:
        click.echo("No agent key found. Agent is not registered.")
        return

    try:
        headers = {"Authorization": f"Agent {agent_key}"}
        response = requests.get(URI_WHOAMI, headers=headers, timeout=5)
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
