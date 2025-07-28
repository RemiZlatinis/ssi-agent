import subprocess
from pathlib import Path

from models import service_from_file


def initialize():
    print("Initializing the service status indicator...")

    print("Validate services parent folder")
    parent_folder_path = Path("/etc/systemd/system/service-status-indicator")
    if not parent_folder_path.exists():
        print(f"Creating parent folder: {parent_folder_path}")
        try:
            # Use sudo to create the directory, as it's in a protected location.
            # This is safer than running the entire script with sudo.
            subprocess.run(
                ["sudo", "mkdir", "-p", str(parent_folder_path)],
                check=True,
                capture_output=True,
            )
        except subprocess.CalledProcessError as e:
            print(f"Error creating parent folder: {e.stderr.decode()}")
            raise
    else:
        print(f"Parent folder already exists: {parent_folder_path}")


def main():
    initialize()

    service = service_from_file("examples/service-example.bash")
    print(f"Service Name: {service.name}")
    print(f"Service Description: {service.description}")
    print(f"Service Version: {service.version}")
    print(f"Service Interval: {service.interval}")
    print(f"Service Timeout: {service.timeout}")
    print(f"\n {'-'*20} \n")
    print(service.script)


if __name__ == "__main__":
    main()
