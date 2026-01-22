#!/usr/bin/env python3
"""
Development environment setup script.
Starts the dev container and runs the installation script inside it.
"""

import argparse
import subprocess
import sys

BASE_CMD = ["podman", "compose", "-f", "dev/docker-compose.yml"]
CWD = "."
INSTALL_SCRIPT = "./install.sh"
SERVICE_NAME = "dev"


def run_compose_command(args: list[str]) -> subprocess.CompletedProcess[bytes]:
    """Run a command compose"""
    return subprocess.run(
        [
            *BASE_CMD,
            *args,
        ],
        cwd=CWD,
    )


def main() -> None:
    """Start and setup the development environment in the container."""
    parser = argparse.ArgumentParser(
        description="Start the development environment in a container."
    )
    parser.add_argument(
        "--install",
        action="store_true",
        help="Force run the installer even if ssi is already installed",
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Remove volumes before starting the container (requires confirmation)",
    )
    args = parser.parse_args()

    # Handle --clear flag
    if args.clear:
        print("⚠️  Warning: This will remove all volumes and data in the dev container.")
        confirm = input("Are you sure? (y/n): ").strip().lower()
        if confirm == "y":
            print("Removing volumes...")
            result = run_compose_command(["down", "--volumes"])
            if result.returncode != 0:
                print("Failed to remove volumes", file=sys.stderr)
                sys.exit(result.returncode)
            print("✓ Volumes removed")
        else:
            print("Cancelled")
            sys.exit(0)

    print("Starting dev container...")
    result = run_compose_command(["up", "--build", "-d", SERVICE_NAME])

    if result.returncode != 0:
        print("Failed to start dev container", file=sys.stderr)
        sys.exit(result.returncode)

    # Check if ssi is already installed
    if not args.install and _command_exists("ssi"):
        print("\n✓ ssi is already installed in the container\n\n")
    else:
        if args.install:
            print("--install flag provided, running installer...")
        else:
            print("ssi not found, running installer...")

        print("Running installer inside dev container...")
        result = run_compose_command(
            ["exec", SERVICE_NAME, "bash", "-c", INSTALL_SCRIPT]
        )
        if result.returncode != 0:
            print("Installer failed", file=sys.stderr)
            sys.exit(result.returncode)

        print("\n\n✓ Agent setup complete\n\n")

    print("Opening container shell...")
    result = run_compose_command(["exec", SERVICE_NAME, "bash"])
    if result.returncode != 0:
        print("Failed to drop into container shell", file=sys.stderr)
        sys.exit(result.returncode)


def _command_exists(cmd: str) -> bool:
    """Check if a command exists in the container."""
    result = subprocess.run(
        [
            *BASE_CMD,
            "exec",
            SERVICE_NAME,
            "which",
            cmd,
        ],
        capture_output=True,
    )
    return result.returncode == 0


if __name__ == "__main__":
    main()
