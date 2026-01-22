"""
SSI Agent - (Network) Client Module

This module handles all WebSocket communication with the SSI backend.
It encapsulates the connection logic, retry mechanisms, and protocol-specific methods
like the initial handshake.
"""

import asyncio
import logging

from websockets import ClientConnection, ConnectionClosed, State, connect

from . import config, loader
from .constants import (
    WEBSOCKET_CLOSE_TIMEOUT,
    WEBSOCKET_PING_INTERVAL,
    WEBSOCKET_PING_TIMEOUT,
)
from .events import AgentReadyEvent, AgentReadyPayload, AgentServiceDataModel

# Use a module-level logger
logger = logging.getLogger(__name__)

WEBSOCKET_URI = config.get_uri("websocket")


async def connect_with_retry(agent_key: str) -> ClientConnection:
    """
    Establish WebSocket connection with retry logic.

    This function implements an exponential backoff strategy for reconnection.
    It returns a websocket connection object that can be used for sending events.
    """
    retry_delay = 5
    max_retries = 3  # Number of quick retries before increasing delay
    retry_count = 0

    while True:
        try:
            logger.info("Attempting to connect to WebSocket server...")
            connection = await connect(
                f"{WEBSOCKET_URI}{agent_key}/",
                ping_interval=WEBSOCKET_PING_INTERVAL,
                ping_timeout=WEBSOCKET_PING_TIMEOUT,
                close_timeout=WEBSOCKET_CLOSE_TIMEOUT,
            )

            # Successfully connected
            logger.info("WebSocket connection established")
            return connection

        except (
            ConnectionClosed,
            ConnectionRefusedError,
            OSError,
        ) as e:
            # Failed to connect, Exponential backoff up:
            retry_count += 1
            if retry_count > max_retries:
                # - First 3 quick retries
                # - After double the delay up to 30s
                retry_delay = min(30, retry_delay * 2)

            logger.warning(
                f"Connection attempt failed: {e}. Retrying in {retry_delay} seconds..."
            )
            await asyncio.sleep(retry_delay)


async def send_agent_hello(
    connection: ClientConnection, agent_key: str
) -> list[AgentServiceDataModel] | None:
    """
    Send the initial agent_hello event with all current services.

    Returns:
        list[AgentServiceDataModel]: The list of services sent, if successful.
        None: If the transmission failed.
    """
    try:
        # Validate connection status before sending
        if connection.state == State.CLOSED:
            raise ConnectionError("WebSocket connection is closed")

        services = loader.list_services()
        service_infos = []

        for service in services:
            service_info = AgentServiceDataModel(
                id=service.id,
                name=service.name,
                description=service.description,
                version=service.version,
                schedule=service.schedule,
            )
            service_infos.append(service_info)

        hello_event = AgentReadyEvent(
            data=AgentReadyPayload(services=service_infos),
        )

        await connection.send(hello_event.model_dump_json())
        logger.info(f"Sent agent.ready event with {len(service_infos)} services")
        return service_infos

    except Exception as e:
        logger.error(f"Error sending agent_hello event: {e}")
        return None
