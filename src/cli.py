"""CLI tool for managing the Service Status Indicator Agent."""

import click

from service import Service


@click.group()
def main():
    """A CLI tool for managing the Service Status Indicator Agent."""
    pass


@main.command()
def list():
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
        f"{'Version':<{max_version_len}} | {'Schedule':<{max_schedule_len}} | {'Status':<{max_status_len}}"
    )
    click.echo(header)
    click.echo("-" * len(header))

    # Rows
    for service in services:
        status = service.get_last_status() or "N/A"
        click.echo(
            f"{service.id:<{max_id_len}} | {service.name:<{max_name_len}} | "
            f"{service.version:<{max_version_len}} | {service.schedule:<{max_schedule_len}} | "
            f"{str(status):<{max_status_len}}"
        )


@main.command()
@click.argument("service_id", required=False)
@click.option("-d", "--details", is_flag=True, help="Display detailed status.")
def status(service_id: str, details: bool):
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


if __name__ == "__main__":
    main()
