"""
SSI Agent CLI - Authentication Commands
"""

import itertools
import time

import click
import requests

from ssi_agent import config, system


@click.group(name="auth")
def auth() -> None:
    """Agent registration and identity management."""
    pass


@auth.command(name="register")
def register() -> None:
    """Register this agent with the SSI backend."""
    # Check if already registered
    key = config.get_agent_key()
    if key:
        click.echo(
            "Agent is already registered. Use 'auth unregister' first if you want"
            " to re-register."
        )
        return

    uri_initiate = config.get_uri("initiate_registration")
    uri_status = config.get_uri("registration_status")

    try:
        response = requests.post(uri_initiate, timeout=10)
        response.raise_for_status()
        data = response.json()

        code = data.get("code")
        reg_id = data.get("id")

        click.secho(
            f"🔑 Registration Code: {code[:3]}-{code[3:]}", bold=True, fg="cyan"
        )
        click.echo("Please enter this code on the SSI dashboard to link this agent.")

        spinner = itertools.cycle("🕐🕑🕒🕓🕔🕕🕖🕗🕘🕙🕚🕛")

        while True:
            try:
                # Poll for status
                status_resp = requests.get(f"{uri_status}{reg_id}/", timeout=5)
                status_resp.raise_for_status()
                status_data = status_resp.json()
                reg_status = status_data.get("status")

                if reg_status == "completed":
                    auth_key = status_data.get("credentials", {}).get("key")
                    if auth_key:
                        # Finalize registration with the backend
                        uri_finalize = config.get_uri("register_finalize")
                        headers = {"Authorization": f"Agent {auth_key}"}
                        try:
                            finalize_resp = requests.post(
                                uri_finalize, headers=headers, timeout=10
                            )
                            finalize_resp.raise_for_status()
                            config.save_agent_key(auth_key)
                            # Clear line
                            click.echo("\r" + " " * 50 + "\r", nl=False)
                            click.secho(
                                "✅ Registration completed successfully!", fg="green"
                            )
                        except requests.exceptions.RequestException as e:
                            click.echo("\r" + " " * 50 + "\r", nl=False)
                            click.secho(
                                f"❌ Finalization failed: {e}."
                                " Please try registering again.",
                                fg="red",
                            )
                    else:
                        click.echo("\r" + " " * 50 + "\r", nl=False)
                        click.secho(
                            "❌ Registration completed but no key received.", fg="red"
                        )
                    break
                elif reg_status == "expired":
                    click.echo("\r" + " " * 50 + "\r", nl=False)
                    click.secho("❌ Registration code has expired.", fg="red")
                    break
                elif reg_status == "pending":
                    # Update spinner
                    for _ in range(10):
                        click.echo(
                            f"\r{next(spinner)} Waiting for completion...", nl=False
                        )
                        time.sleep(0.5 / 10)

            except requests.exceptions.RequestException as e:
                # Handle 410 Gone (expired)
                if e.response and e.response.status_code == 410:
                    click.echo("\r" + " " * 50 + "\r", nl=False)
                    click.secho("❌ Registration code expired.", fg="red")
                    break
                raise e

    except Exception as e:
        click.secho(f"❌ Registration failed: {e}", fg="red", err=True)


@auth.command(name="unregister")
@click.confirmation_option(
    prompt="Are you sure you want to delete this agent? This action is permanent and"
    " will remove all associated data."
)
def unregister() -> None:
    """Permanently delete the agent and remove all associated data."""
    agent_key = config.get_agent_key()
    if not agent_key:
        click.echo("Agent is not registered.")
        return

    uri_unregister = config.get_uri("unregister")

    try:
        headers = {"Authorization": f"Agent {agent_key}"}
        response = requests.delete(uri_unregister, headers=headers, timeout=10)
        response.raise_for_status()

        config.remove_agent_key()
        click.echo("✅ Agent deleted successfully from backend.")

        # Restart the agent
        system.restart_agent()
    except Exception as e:
        # We remove the local key even if the server call fails
        # to allow "cleaning" the state
        config.remove_agent_key()
        click.secho(
            f"⚠️ Server deletion failed ({e}), but local key was removed.",
            fg="yellow",
        )


@auth.command(name="whoami")
def whoami() -> None:
    """Display information about the registered agent."""
    agent_key = config.get_agent_key()
    if not agent_key:
        click.echo("This agent is not registered.")
        return

    uri_whoami = config.get_uri("whoami")

    try:
        headers = {"Authorization": f"Agent {agent_key}"}
        response = requests.get(uri_whoami, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()

        click.secho("Agent Identity:", bold=True)
        click.echo(f"  ID:        {data.get('id')}")
        click.echo(f"  Name:      {data.get('name')}")
        click.echo(f"  Status:    {data.get('registration_status')}")
        click.echo(f"  IP:        {data.get('ip_address')}")

        owner = data.get("owner")
        if owner:
            click.echo(
                f"  Owner:     {owner.get('username')}"
                f" ({owner.get('email') or 'no email'})"
            )

    except Exception as e:
        click.secho(f"❌ Failed to fetch agent info: {e}", fg="red", err=True)
