#!/usr/bin/env python3
"""
Test environment setup and runner script.
Starts the test container, runs the installer, and executes tests.
"""

import sys

from .dev import INSTALL_SCRIPT, run_compose_command

SERVICE_NAME = "test"


def main() -> None:
    """Start test container, run installer, and execute tests."""
    print("Starting test container...")
    result = run_compose_command(["up", "--build", "-d", SERVICE_NAME])
    if result.returncode != 0:
        print("Failed to start test container", file=sys.stderr)
        sys.exit(result.returncode)

    print("Running installer inside test container...")
    result = run_compose_command(["exec", SERVICE_NAME, "bash", "-c", INSTALL_SCRIPT])
    if result.returncode != 0:
        print("Installer failed", file=sys.stderr)
        sys.exit(result.returncode)

    print("Installing Pytest...")
    result = run_compose_command(
        ["exec", SERVICE_NAME, "./venv/bin/pip", "install", "pytest"]
    )
    if result.returncode != 0:
        print("Failed to install test dependencies", file=sys.stderr)
        sys.exit(result.returncode)

    print("Running tests...")
    result = run_compose_command(
        [
            "exec",
            SERVICE_NAME,
            "./venv/bin/python",
            "-m",
            "pytest",
            "-o",
            "addopts=-ra -q",  # For E2E testing we don't need coverage.
            # So, we override the `addopts` of the config file
        ]
    )
    if result.returncode != 0:
        print("Tests failed", file=sys.stderr)
        sys.exit(result.returncode)

    print("All tests passed!")


if __name__ == "__main__":
    main()
