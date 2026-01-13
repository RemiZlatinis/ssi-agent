"""
SSI Agent CLI - Service Commands
"""

from pathlib import Path

import click

from .. import loader, manager, parsers
from ..constants import LOG_DIR


@click.group(name="service")
def service():
    """Manage service scripts and their monitoring state."""
    pass


@service.command(name="add")
@click.argument("script_path", type=click.Path(exists=True, dir_okay=False))
@click.option(
    "--no-start", is_flag=True, help="Don't enable/start the service immediately."
)
def add_service(script_path: str, no_start: bool):
    """
    Install a new service script.

    This copies the script to the agent's internal directory and sets up
    the required systemd units.
    """
    try:
        path = Path(script_path)
        service_id = manager.add(path, start_now=not no_start)
        click.echo(f"✅ Service '{service_id}' added successfully.")
    except Exception as e:
        click.secho(f"❌ Error adding service: {e}", fg="red", err=True)


@service.command(name="remove")
@click.argument("service_id")
def remove_service(service_id: str):
    """Uninstall a service script and remove its systemd units."""
    try:
        manager.remove(service_id)
        click.echo(f"✅ Service '{service_id}' removed.")
    except Exception as e:
        click.secho(f"❌ Error removing service: {e}", fg="red", err=True)


@service.command(name="enable")
@click.argument("service_id")
def enable_service(service_id: str):
    """Enable the systemd timer for an installed service."""
    try:
        manager.enable(service_id)
        click.echo(f"✅ Service '{service_id}' enabled.")
    except Exception as e:
        click.secho(f"❌ Error enabling service: {e}", fg="red", err=True)


@service.command(name="disable")
@click.argument("service_id")
def disable_service(service_id: str):
    """Disable the systemd timer for a service."""
    try:
        manager.disable(service_id)
        click.echo(f"✅ Service '{service_id}' disabled.")
    except Exception as e:
        click.secho(f"❌ Error disabling service: {e}", fg="red", err=True)


@service.command(name="run")
@click.argument("service_id")
def run_service(service_id: str):
    """Trigger an immediate run of the service script."""
    try:
        manager.run(service_id)
        click.echo(f"🚀 Service '{service_id}' triggered.")
    except Exception as e:
        click.secho(f"❌ Error running service: {e}", fg="red", err=True)


@service.command(name="list")
@click.option(
    "--all",
    "show_all",
    is_flag=True,
    help="Show all installed services, including disabled ones.",
)
def list_services(show_all: bool):
    """List installed services and their basic info."""
    services = loader.list_services(all=show_all)
    if not services:
        click.echo("No services found.")
        return

    # Table formatting
    max_id = max(len(s.id) for s in services)
    max_name = max(len(s.name) for s in services)

    header = (
        f"{'ID':<{max_id}} | {'NAME':<{max_name}} | "
        f"{'VERSION'} | {'ENABLED'} | {'SCHEDULE'}"
    )
    click.echo(header)
    click.echo("-" * len(header))

    for s in services:
        enabled_str = "Yes" if s.is_enabled else "No"
        click.echo(
            f"{s.id:<{max_id}} | {s.name:<{max_name}} | "
            f"{s.version:<7} | {enabled_str:<7} | {s.schedule}"
        )


@service.command(name="status")
@click.argument("service_id", required=False)
@click.option("--details", is_flag=True, help="Show full log metadata.")
def status(service_id: str | None, details: bool):
    """Display the last known status of services from logs."""
    if service_id:
        srv = loader.load_from_id(service_id)
        if not srv:
            click.echo(f"Service '{service_id}' not found.")
            return
        services = [srv]
    else:
        services = loader.list_services(all=True)

    if not services:
        click.echo("No services found.")
        return

    for s in services:
        log_file = LOG_DIR / f"{s.id}.log"
        if not log_file.exists():
            click.echo(f"{s.name}: No logs found.")
            continue

        try:
            lines = log_file.read_text().splitlines()
            if not lines:
                click.echo(f"{s.name}: Log file empty.")
                continue

            timestamp, status, message = parsers.parse_log_line(lines[-1].strip())

            if details:
                click.echo(f"Service: {s.name} ({s.id})")
                click.secho(f"  Status:    {status}", fg=_get_status_color(status))
                click.echo(f"  Timestamp: {timestamp or 'N/A'}")
                click.echo(f"  Message:   {message or 'N/A'}")
                click.echo("")
            else:
                color_status = click.style(str(status), fg=_get_status_color(status))
                click.echo(f"{s.name:<20}: {color_status}")

        except Exception as e:
            click.echo(f"{s.name}: Error reading logs ({e})")


def _get_status_color(status):
    from ..models import Status

    if status == Status.OK:
        return "green"
    if status in (Status.WARNING, Status.UPDATE):
        return "yellow"
    if status in (Status.FAILURE, Status.ERROR):
        return "red"
    return "white"
