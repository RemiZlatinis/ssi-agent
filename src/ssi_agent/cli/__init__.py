"""
SSI Agent CLI package

This package implements the command-line interface for the SSI Agent using Click.
It is organized into groups for services, authentication, and debugging.
"""

import click

from .auth import auth
from .debug import debug
from .service import service


@click.group()
@click.version_option()
def main() -> None:
    """
    SSI Agent CLI - Monitor and manage services.

    This tool allows you to register the agent with the SSI backend,
    add/remove service scripts, and monitor their execution status.
    """
    pass


# Register subgroups
main.add_command(service)
main.add_command(auth)
main.add_command(debug)


if __name__ == "__main__":
    main()
