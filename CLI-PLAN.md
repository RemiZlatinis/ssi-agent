Service Management
   * `add`: Register a new service with the agent. This would take a script path, a name, and a schedule
     (e.g., a cron expression or a simple interval), then generate and install the necessary systemd unit
      files from the templates.
   * `remove`: De-register a service, stopping it and removing its systemd unit files.
   * `update`: Modify the configuration of an existing service (e.g., change its schedule or the script
     it runs).

  Service Control & Status
   * `list`: Show all services managed by the agent, including their name, status (enabled/disabled,
     active/inactive), and last/next run times.
   * `status <service_name>`: Display detailed information for a single service.
   * `start <service_name>`: Manually trigger a service to run immediately.
   * `stop <service_name>`: Manually stop a currently running service.
   * `logs <service_name>`: View the recent logs for a specific service to help with debugging.

  Agent Administration
   * `install`: A command to set up the agent itself as a system-wide service.
   * `uninstall`: Remove the agent service from the system.