"""
SSI Agent - Daemon Module

This module serves as the main entry point and orchestrator for the
Service Status Indicator (SSI) Agent background process. It is responsible
for initializing the agent's core components, managing the application
lifecycle, and coordinating communication between the local system and
the remote backend.

The Daemon acts as the "Application Layer" of the agent,
binding together the:
1.  **System/Service Layer**: To discover and read logs from services.
2.  **Network Layer (Client)**: To maintain the WebSocket connection
        with the SSI backend.
3.  **Monitor Layer**: To observe file system events and service state
        changes.

Key Responsibilities:
---------------------
*   **Initialization**: Loads configuration, verifies agent registration
        keys, and sets up logging.
*   **Connection Management**: Establishes and maintains the persistent
        WebSocket connection using the `client` module. It handles
        reconnection strategies (though implementation details reside
        in `client`).
*   **Orchestration**: Instantiates the `LogMonitor` and
        `ServiceMonitor` (from the `monitor` module) and attaches them to
        the active WebSocket connection.
*   **Lifecycle Management**: Handles startup sequences, keeps the main
        thread alive, and manages graceful shutdown on system signals
        (SIGINT, SIGTERM) to ensure resources (sockets, observers) are
        closed properly.

Usage:
------
This module is intended to be executed directly as a script or via the
installed package entry point. It checks for the existence of the
`agent_key` and waits for registration if the key is missing.

    $ python -m ssi_agent.daemon

Architecture:
-------------
    [Daemon] <-------- orchestrates --------> [Client (WebSocket)]
       |
       +---------> [Monitor (Watchdog)] ----> [System Logs]
       +---------> [Service Manager] -------> [System Services]

"""

import asyncio
import logging

from . import client, config, monitor
from .logging_config import setup_logging

logger = logging.getLogger(__name__)


async def daemon():
    """
    The main async event loop for the daemon.

    This function:
    1. Checks environment prerequisites.
    2. Enters a persistent loop to maintain the backend connection.
    3. Initializes the Network Client and Monitors.
    4. Handles errors and ensures resources are cleaned up on retry.
    """

    # THIS LOGIC SHOULD BE ON THE LOGGING MODULE
    # it never logs the warning because the LOG_DIR does not exist
    # if not os.path.exists(LOG_DIR):
    #     logger.warning(f"Log directory {LOG_DIR} does not exist. Creating it...")
    #     os.makedirs(LOG_DIR, exist_ok=True)

    while True:
        # Reset state variables for each connection attempt
        connection = None
        log_monitor = None
        service_monitor = None

        try:
            # 1. Credential Check
            agent_key = config.get_agent_key()
            if not agent_key:
                logger.info(
                    "No agent key found. Please register the agent first. Waiting..."
                )
                await asyncio.sleep(10)
                continue

            logger.debug(f"Using agent key: {agent_key}")

            # 2. Establish Connection
            connection = await client.connect_with_retry(agent_key)

            # 3. Initial Handshake
            services = await client.send_agent_hello(connection, agent_key)
            if services is None:
                raise ConnectionError("Failed to complete agent_hello handshake")

            logger.debug(f"Initial services: {services}")

            # 4. Start Monitoring
            # Log Monitor: Watches for file changes in LOG_DIR
            log_monitor = monitor.LogMonitor(connection, agent_key)
            log_monitor.start()

            # # Service Monitor: Watches for systemd service variations
            service_monitor = monitor.ServiceMonitor(connection, agent_key, services)
            service_monitor.start()

            logger.info("SSI Agent is running.")

            # 5. Keep Alive
            # We wait here until the connection is closed.
            # This prevents the loop from spinning and restarting everything
            # immediately.
            await connection.wait_closed()

            logger.warning("WebSocket connection closed. Restarting monitors...")

        except Exception as e:
            logger.error(f"Daemon error or connection lost: {e}. Reconnecting...")
            # Brief pause to prevent tight loops on hard failures
            if not isinstance(e, ConnectionError):
                await asyncio.sleep(5)

        finally:
            # 6. Cleanup
            # Ensure we stop threads and observers before trying to reconnect
            if log_monitor:
                log_monitor.stop()
            if service_monitor:
                service_monitor.stop()
            if connection:
                await connection.close()


def main():
    """
    Entry point for the script.
    """
    # Initialize logging first
    setup_logging()

    logger.info("Starting SSI Agent Daemon...")
    try:
        asyncio.run(daemon())
    except KeyboardInterrupt:
        logger.info("\nStopping daemon...")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        exit(1)

    # Clean exit
    exit(0)


if __name__ == "__main__":
    main()
