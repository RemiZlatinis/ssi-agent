"""
Observes the services logs and sends the
new lines from any modified log files to the WebSocket server in real-time.
"""

import os
import asyncio
import websockets
import json

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from constants import LOG_DIR
from service import Service

WEBSOCKET_URI = "ws://localhost:5000"
PING_INTERVAL_SECONDS = 10


class LogHandler(FileSystemEventHandler):
    def __init__(self, websocket, loop):
        super().__init__()
        self.file_positions = {}  # Stores last read positions
        self.websocket = websocket
        self.loop = loop

    def on_modified(self, event):
        if event.is_directory:
            return  # Ignore directory changes

        file_path = event.src_path
        if not str(file_path).startswith(str(LOG_DIR.absolute())):
            return  # Safety check

        try:
            # Initialize file position if first time seeing the file
            if file_path not in self.file_positions:
                self.file_positions[file_path] = 0

            with open(file_path, "r") as f:
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

                        try:
                            timestamp, status, message = last_line.split(",", 2)
                        except ValueError:
                            timestamp, status = last_line.split(",", 1)
                            message = None

                        log_data = {
                            "service": service.to_dict(),
                            "timestamp": timestamp.strip(),
                            "status": status.strip(),
                            "message": message.strip() if message else None,
                        }
                        asyncio.run_coroutine_threadsafe(
                            self.send_log_message(log_data), self.loop
                        )
        except Exception as e:
            print(f"Error reading {file_path}: {e}")

    async def send_log_message(self, log_data):
        try:
            await self.websocket.send(json.dumps(log_data))
        except Exception as e:
            print(f"Error sending log message to WebSocket server: {e}")


async def connect_with_retry():
    """Establish WebSocket connection with retry logic"""
    retry_delay = 5
    max_retries = 3  # Number of quick retries before increasing delay
    retry_count = 0

    while True:
        try:
            websocket = await websockets.connect(
                WEBSOCKET_URI,
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


async def run_daemon():
    if not os.path.exists(LOG_DIR):
        print(f"Log directory {LOG_DIR} does not exist.")
        return

    while True:
        websocket = None
        observer = None
        try:
            try:
                websocket = await connect_with_retry()
                loop = asyncio.get_running_loop()
                event_handler = LogHandler(websocket, loop)
                observer = Observer()
                observer.schedule(event_handler, str(LOG_DIR), recursive=False)
                observer.start()

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


def main():
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
