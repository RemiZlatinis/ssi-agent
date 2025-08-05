"""
Observes the services logs and prints the
new lines from any modified log files in real-time.
"""

import os

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from constants import LOG_DIR


class LogHandler(FileSystemEventHandler):
    def __init__(self):
        super().__init__()
        self.file_positions = {}  # Stores last read positions

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
                        print(f"{service_id} {last_line}")
        except Exception as e:
            print(f"Error reading {file_path}: {e}")


def main():
    if not os.path.exists(LOG_DIR):
        print(f"Log directory {LOG_DIR} does not exist.")
        return

    event_handler = LogHandler()
    observer = Observer()
    observer.schedule(event_handler, str(LOG_DIR), recursive=False)
    observer.start()

    print(f"Watching for changes in: {LOG_DIR}")
    try:
        observer.join()
    except KeyboardInterrupt:
        print("\nStopping observer...")
        observer.stop()
    observer.join()


if __name__ == "__main__":
    main()
