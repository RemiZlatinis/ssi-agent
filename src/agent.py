"""
Observes the services logs and sends the
new lines from any modified log files to the WebSocket server in real-time.
"""

import asyncio
import os
import threading
import time
from typing import Any

import websockets
from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from . import config
from .constants import LOG_DIR, PING_INTERVAL_SECONDS, WEBSOCKET_URI
from .models import (
    AgentHelloEvent,
    ServiceAddedEvent,
    ServiceInfo,
    ServiceRemovedEvent,
    StatusUpdate,
    StatusUpdateEvent,
)
from .parsers import parse_log_line
from .service import Service


class LogHandler(FileSystemEventHandler):
    def __init__(
        self,
        websocket: Any,
        loop: asyncio.AbstractEventLoop,
        agent_key: str,
    ):
        super().__init__()
        self.file_positions: dict[bytes | str, int] = {}  # Stores last read positions
        self.websocket = websocket
        self.loop = loop
        self.agent_key = agent_key

    def on_modified(self, event: FileSystemEvent) -> None:
        if event.is_directory:
            return  # Ignore directory changes

        file_path = event.src_path
        if not str(file_path).startswith(str(LOG_DIR.absolute())):
            return  # Safety check

        try:
            # Initialize file position if first time seeing the file
            if file_path not in self.file_positions:
                self.file_positions[file_path] = 0

            with open(file_path) as f:
                f.seek(self.file_positions[file_path])  # Move to last read position
                new_lines = f.readlines()
                self.file_positions[file_path] = f.tell()  # Update position

                # Print the last line
                if new_lines:
                    last_line = new_lines[-1].strip()
                    if last_line:
                        service_id = str(os.path.basename(file_path)).replace(
                            ".log", ""
                        )
                        service = Service.get_service(service_id)
                        if not service:
                            print(f"Service with ID {service_id} not found.")
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

                        asyncio.run_coroutine_threadsafe(
                            self.send_status_update(status_event), self.loop
                        )
        except Exception as e:
            print(f"Error reading {str(file_path)}: {e}")

    async def send_status_update(self, status_event: StatusUpdateEvent) -> None:
        try:
            await self.websocket.send(status_event.model_dump_json())
        except Exception as e:
            print(f"Error sending status update to WebSocket server: {e}")


async def connect_with_retry() -> Any:
    """Establish WebSocket connection with retry logic"""
    retry_delay = 5
    max_retries = 3  # Number of quick retries before increasing delay
    retry_count = 0

    agent_uuid = config.get_agent_key()

    while True:
        try:
            websocket = await websockets.connect(
                f"{WEBSOCKET_URI}{agent_uuid}/",
                ping_interval=20,
                ping_timeout=60,
                close_timeout=5,
            )
            print("Connected to WebSocket server")
            return websocket
        except (
            websockets.exceptions.ConnectionClosed,
            ConnectionRefusedError,
            OSError,
        ) as e:
            retry_count += 1
            if retry_count > max_retries:
                retry_delay = min(30, retry_delay * 2)  # Exponential backoff up to 30s
                retry_count = 0

            print(
                f"Connection attempt failed: {e}. Retrying in {retry_delay} seconds..."
            )
            await asyncio.sleep(retry_delay)


async def send_agent_hello(websocket: Any, agent_key: str) -> list[ServiceInfo] | None:
    """
    Send the initial agent_hello event with all current services.
    Returns the list of services if successful, None otherwise.
    """
    try:
        services = Service.get_services()
        service_infos = []

        for service in services:
            service_info = ServiceInfo(
                id=service.id,
                name=service.name,
                description=service.description,
                version=service.version,
                schedule=service.schedule,
            )
            service_infos.append(service_info)

        hello_event = AgentHelloEvent(agent_key=agent_key, services=service_infos)

        await websocket.send(hello_event.model_dump_json())
        print(f"Sent agent_hello event with {len(service_infos)} services")
        return service_infos
    except Exception as e:
        print(f"Error sending agent_hello event: {e}")
        return None


def watch_service_changes(
    websocket: Any,
    loop: asyncio.AbstractEventLoop,
    agent_key: str,
    initial_services: list[ServiceInfo] | None,
) -> None:
    """Monitor service changes and send appropriate events."""
    if initial_services is None:
        known_services = set()
    else:
        known_services = {service.id for service in initial_services}
    scan_interval = 15  # seconds

    while True:
        try:
            current_services = Service.get_services()
            current_service_ids = {service.id for service in current_services}

            # Check for new services
            new_services = current_service_ids - known_services
            for service_id in new_services:
                service = next(s for s in current_services if s.id == service_id)
                service_info = ServiceInfo(
                    id=service.id,
                    name=service.name,
                    description=service.description,
                    version=service.version,
                    schedule=service.schedule,
                )
                added_event = ServiceAddedEvent(service=service_info)
                asyncio.run_coroutine_threadsafe(
                    websocket.send(added_event.model_dump_json()), loop
                )
                print(f"Service {service_id} added")

            # Check for removed services
            removed_services = known_services - current_service_ids
            for service_id in removed_services:
                removed_event = ServiceRemovedEvent(service_id=service_id)
                asyncio.run_coroutine_threadsafe(
                    websocket.send(removed_event.model_dump_json()), loop
                )
                print(f"Service {service_id} removed")

            known_services = current_service_ids
            time.sleep(scan_interval)

        except Exception as e:
            print(f"Error in service change watcher: {e}")
            time.sleep(scan_interval)


async def run_daemon() -> None:
    if not os.path.exists(LOG_DIR):
        print(f"Log directory {LOG_DIR} does not exist.")
        return

    # Get agent key
    agent_key = config.get_agent_key()
    if not agent_key:
        print("No agent key found. Please register the agent first.")
        return
    else:
        print(f"Using agent key: {agent_key}")

    while True:
        websocket = None
        observer = None
        service_watcher_thread = None
        try:
            try:
                websocket = await connect_with_retry()
                loop = asyncio.get_running_loop()

                # Send initial agent_hello event
                initial_services = await send_agent_hello(websocket, agent_key)
                if initial_services is None:
                    # Failed to send hello, trigger reconnection
                    raise ConnectionError("Failed to send agent_hello event")

                event_handler = LogHandler(websocket, loop, agent_key)
                observer = Observer()
                observer.schedule(event_handler, str(LOG_DIR), recursive=False)
                observer.start()

                # Start service change detection thread
                service_watcher_thread = threading.Thread(
                    target=watch_service_changes,
                    args=(websocket, loop, agent_key, initial_services),
                    daemon=True,
                )
                service_watcher_thread.start()

                print(f"Watching for changes in: {LOG_DIR}")
                while True:
                    try:
                        await websocket.ping()
                        await asyncio.sleep(PING_INTERVAL_SECONDS)
                    except (
                        websockets.exceptions.ConnectionClosed,
                        websockets.exceptions.ConnectionClosedError,
                        OSError,
                    ) as e:
                        print(f"Connection error: {e}")
                        raise  # Re-raise to trigger reconnection

            except Exception as e:
                print(f"Connection lost: {e}. Reconnecting...")
                if observer:
                    observer.stop()
                    observer.join()
                if websocket:
                    await websocket.close()
                continue

        except KeyboardInterrupt:
            print("\nStopping daemon...")
            if observer:
                observer.stop()
                observer.join()
            if websocket:
                await websocket.close()
            break


def main() -> int:
    """Main entry point"""
    try:
        asyncio.run(run_daemon())
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f"Fatal error: {e}")
        return 1
    return 0


if __name__ == "__main__":
    exit(main())
