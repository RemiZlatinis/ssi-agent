from models import service_from_file


def main():
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
