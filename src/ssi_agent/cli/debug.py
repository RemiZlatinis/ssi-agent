"""
SSI Agent CLI - Debug Commands
"""

from datetime import datetime

import click

from ssi_agent import config, loader, system
from ssi_agent.constants import LOG_DIR
from ssi_agent.models import Status


@click.group(name="debug")
def debug() -> None:
    """Diagnostic and manual override commands."""
    pass


@debug.command(name="set-status")
@click.argument("service_id")
@click.argument(
    "status", type=click.Choice([s.value for s in Status], case_sensitive=False)
)
@click.argument("message", required=False)
def set_status(service_id: str, status: str, message: str | None) -> None:
    """
    Manually inject a status update into a service log.

    This is useful for testing the agent's monitoring and backend reporting.
    """
    srv = loader.load_from_id(service_id)
    if not srv:
        click.echo(f"❌ Service '{service_id}' is not installed.")
        return

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    msg = message or f"Manual status override to {status}"
    log_line = f"{timestamp}, {status}, {msg}"

    log_path = LOG_DIR / f"{service_id}.log"

    try:
        system.write_log_line(log_path, log_line)
        click.echo(f"✅ Injected status '{status}' into {log_path.name}")
    except Exception as e:
        click.secho(f"❌ Failed to write log: {e}", fg="red", err=True)


@debug.command(name="set-backend")
@click.argument("url")
def set_backend(url: str) -> None:
    """Override the backend API URL in the configuration."""
    try:
        config.set_backend_url(url)
        click.echo(f"✅ Backend URL updated to: {url}")
    except Exception as e:
        click.secho(f"❌ Failed to update config: {e}", fg="red", err=True)


@debug.command(name="logs")
@click.option("-f", "--follow", is_flag=True, help="Follow log output.")
@click.option("-n", "--lines", default=50, help="Number of last lines to show.")
def agent_logs(follow: bool, lines: int) -> None:
    """Display the ssi-agent daemon logs."""
    log_path = LOG_DIR / "_agent.log"

    if not log_path.exists():
        click.echo(f"❌ Agent log file not found at: {log_path}")
        return

    try:
        system.tail_file(log_path, lines=lines, follow=follow)
    except Exception as e:
        click.secho(f"❌ Failed to display logs: {e}", fg="red", err=True)
