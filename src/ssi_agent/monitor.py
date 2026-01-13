"""
SSI Agent - Monitor Module

This module monitors system resources and triggers events based on changes.
It contains two main monitors:
1. LogMonitor: Uses `watchdog` to observe changes in log files.
2. ServiceMonitor: Polls for changes in systemd services (added/removed) from the CLI.
"""

import asyncio
import logging
import os
import threading
import time

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer
from websockets import ClientConnection

from . import loader
from .constants import LOG_DIR
from .events import (
    ServiceAddedEvent,
    ServiceRemovedEvent,
    StatusUpdateEvent,
)
from .models import (
    ServiceInfo,
    StatusUpdate,
)
from .parsers import parse_log_line

# Use a module-level logger
logger = logging.getLogger(__name__)


class LogHandler(FileSystemEventHandler):
    """
    Handles file system events for log files.
    Reads new lines from modified log files and sends them to the WebSocket.
    """

    def __init__(
        self,
        connection: ClientConnection,
        loop: asyncio.AbstractEventLoop,
        agent_key: str,
    ):
        super().__init__()
        self.file_positions: dict[bytes | str, int] = {}  # Stores last read positions
        self.connection = connection
        self.loop = loop
        self.agent_key = agent_key

    def on_modified(self, event: FileSystemEvent) -> None:
        if event.is_directory:
            return  # Ignore directory changes

        file_path = event.src_path
        str_path = str(file_path)  # Convert paths to string for comparison to be safe

        if (
            not str_path.startswith(str(LOG_DIR.absolute()))
            or not str_path.endswith(".log")
            or str_path.endswith("_agent.log")  # Ignore the daemon's own logs
        ):
            return  # Safety checks

        try:
            # Initialize file position if first time seeing the file
            if file_path not in self.file_positions:
                self.file_positions[file_path] = 0

            with open(file_path, encoding="utf-8") as f:
                f.seek(self.file_positions[file_path])  # Move to last read position
                new_lines = f.readlines()
                self.file_positions[file_path] = f.tell()  # Update position

                # Process the last line (assuming we only care about the latest status)
                if new_lines:
                    last_line = new_lines[-1].strip()
                    if last_line:
                        service_id = str(os.path.basename(file_path)).replace(
                            ".log", ""
                        )
                        # TODO: Optimization - Cache service lookups?
                        service = loader.load_from_id(service_id)
                        if not service:
                            logger.info(f"Service with ID {service_id} not found.")
                            return

                        timestamp, status, message = parse_log_line(last_line)

                        # Create StatusUpdate and StatusUpdateEvent
                        status_update = StatusUpdate(
                            service_id=service_id,
                            timestamp=timestamp,
                            status=status,
                            message=message or "",  # Handle None message
                        )
                        status_event = StatusUpdateEvent(update=status_update)

                        # Send async message from this sync callback
                        asyncio.run_coroutine_threadsafe(
                            self.send_status_update(status_event), self.loop
                        )
                        logger.info(f"Sent status update: {status_update.status}")
        except Exception as e:
            logger.error(f"Error reading {str_path}: {e}")

    async def send_status_update(self, status_event: StatusUpdateEvent) -> None:
        try:
            if self.connection:
                await self.connection.send(status_event.model_dump_json())
        except Exception as e:
            logger.error(f"Error sending status update to WebSocket server: {e}")


class LogMonitor:
    """
    Orchestrates the watching of log files.
    """

    def __init__(self, connection: ClientConnection, agent_key: str):
        self.connection = connection
        self.agent_key = agent_key
        self.observer = Observer()
        # We need the running loop to schedule async tasks from the watchdog thread
        self.loop = asyncio.get_running_loop()
        self.handler = LogHandler(connection, self.loop, agent_key)

    def start(self) -> None:
        """Starts the watchdog observer."""
        self.observer.schedule(self.handler, str(LOG_DIR), recursive=False)
        self.observer.start()
        logger.info("LogMonitor started.")

    def stop(self) -> None:
        """Stops the watchdog observer."""
        if self.observer.is_alive():
            self.observer.stop()
            self.observer.join()
            logger.info("LogMonitor stopped.")


class ServiceMonitor:
    """
    Polls for changes in the list of available services.
    """

    def __init__(
        self,
        connection: ClientConnection,
        agent_key: str,
        initial_services: list[ServiceInfo] | None,
    ):
        self.connection = connection
        self.agent_key = agent_key
        self.loop = asyncio.get_running_loop()
        self.running = False
        self.thread: threading.Thread | None = None

        # Initialize known services
        if initial_services is None:
            self.known_services = set()
        else:
            self.known_services = {service.id for service in initial_services}

    def start(self) -> None:
        """Starts the monitoring thread."""
        self.running = True
        self.thread = threading.Thread(target=self._watch_loop, daemon=True)
        self.thread.start()
        logger.info("ServiceMonitor started.")

    def stop(self) -> None:
        """Stops the monitoring thread."""
        self.running = False
        if self.thread and self.thread.is_alive():
            # We don't join/block here because the loop relies on sleep
            # and we want to return quickly. The thread will exit on next wake.
            pass
        logger.info("ServiceMonitor stopped.")

    def _watch_loop(self) -> None:
        """Internal loop running in a separate thread."""
        scan_interval = 15  # seconds

        while self.running:
            try:
                current_services = loader.list_services()
                current_service_ids = {service.id for service in current_services}

                # Check for new services
                new_services = current_service_ids - self.known_services
                for service_id in new_services:
                    # Find the full object
                    try:
                        service = next(
                            s for s in current_services if s.id == service_id
                        )
                        service_info = ServiceInfo(
                            id=service.id,
                            name=service.name,
                            description=service.description,
                            version=service.version,
                            schedule=service.schedule,
                        )
                        added_event = ServiceAddedEvent(service=service_info)
                        asyncio.run_coroutine_threadsafe(
                            self.connection.send(added_event.model_dump_json()),
                            self.loop,
                        )
                        logger.info(f"Service {service_id} added")
                    except StopIteration:
                        continue

                # Check for removed services
                removed_services = self.known_services - current_service_ids
                for service_id in removed_services:
                    removed_event = ServiceRemovedEvent(service_id=service_id)
                    asyncio.run_coroutine_threadsafe(
                        self.connection.send(removed_event.model_dump_json()), self.loop
                    )
                    logger.info(f"Service {service_id} removed")

                self.known_services = current_service_ids

                # Sleep in small chunks to allow faster shutdown
                for _ in range(scan_interval):
                    if not self.running:
                        break
                    time.sleep(1)

            except Exception as e:
                logger.error(f"Error in service change monitoring: {e}")
                time.sleep(scan_interval)
