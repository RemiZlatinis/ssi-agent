# CLI Reference

The SSI Agent provides a command-line interface (`ssi`) for managing services and agent configuration.

## Global Options

```bash
ssi --help     # Show help message
ssi --version  # Show version (if available)
```

---

## Service Management

### `ssi add`

Add a new service from a BASH script.

```bash
ssi add <service-script-path> [--update]
```

**Arguments:**

- `service-script-path` — Path to the service script (.bash file)

**Options:**

- `--update` — Update existing service if it already exists

**Example:**

```bash
ssi add ~/my-scripts/api-health.bash
ssi add ./system-check.bash --update
```

**What it does:**

1. Parses the script to extract metadata (name, description, schedule, etc.)
2. Validates the script structure
3. Copies the script to `/opt/ssi-agent/scripts/`
4. Creates systemd service and timer units
5. Enables and starts the timer

---

### `ssi remove`

Remove a service by its ID.

```bash
ssi remove <service-id> [--force]
```

**Arguments:**

- `service-id` — The ID of the service (derived from the name in snake_case)

**Options:**

- `--force` — Force removal even if files are partially missing

**Example:**

```bash
ssi remove api_health
ssi remove broken_service --force
```

**What it does:**

1. Disables the systemd timer
2. Removes the service and timer unit files
3. Removes the script from `/opt/ssi-agent/scripts/`

---

### `ssi list`

List all installed services.

```bash
ssi list
```

**Example output:**

```
ID              | Name            | Status  | Schedule
----------------|-----------------|---------|------------------
api_health      | API Health      | OK      | *:0/01:00
system_updates  | System Updates  | UPDATE  | *-*-* 06:00:00
zpool_health    | ZFS Zpool Health| WARNING | *-*-* 06:00:00
```

---

### `ssi status`

Display the status of a service or all services.

```bash
ssi status [service-id] [--details]
```

**Arguments:**

- `service-id` — (Optional) Specific service to check

**Options:**

- `--details` — Show additional details including last message

**Example:**

```bash
# Status of all services
ssi status

# Status of specific service
ssi status api_health

# Detailed status
ssi status api_health --details
```

---

### `ssi run`

Manually run a service script immediately.

```bash
ssi run <service-id>
```

**Arguments:**

- `service-id` — The ID of the service to run

**Example:**

```bash
ssi run api_health
```

**Note:** This triggers the systemd service unit directly, bypassing the timer. The script runs in the background.

---

## Agent Management

### `ssi register`

Register the agent with the SSI backend.

```bash
ssi register
```

**Flow:**

1. Agent requests a registration code from the backend
2. Displays a 6-digit code
3. User enters the code in the SSI mobile app
4. Agent polls for confirmation
5. Stores the agent key upon successful registration

**Example:**

```bash
$ ssi register
Registration Code: 847293

Enter this code in your SSI mobile app to complete registration.
Waiting for confirmation... Done!

Agent registered successfully.
```

---

### `ssi unregister`

Unregister the agent and remove the agent key.

```bash
ssi unregister
```

**What it does:**

1. Notifies the backend of unregistration
2. Removes the agent key from local configuration
3. The agent will no longer connect to the backend

---

### `ssi whoami`

Display information about the current agent.

```bash
ssi whoami
```

**Example output:**

```
Agent ID: a1b2c3d4-e5f6-7890-abcd-ef1234567890
Agent Name: Home Server
Registered: Yes
Backend URL: https://api.service-status-indicator.com/
Services: 5
```

---

## Configuration

### `ssi set-backend`

Set the backend URL in the configuration file.

```bash
ssi set-backend <backend-url>
```

**Arguments:**

- `backend-url` — The full URL of the SSI backend

**Example:**

```bash
ssi set-backend https://my-ssi-backend.example.com/
```

---

## Debugging

### `ssi debug set-status`

Manually set the status of a service (for debugging purposes).

```bash
ssi debug set-status <service-id> <status>
```

**Arguments:**

- `service-id` — The ID of the service
- `status` — One of: `OK`, `UPDATE`, `WARNING`, `FAILURE`, `ERROR`, `UNKNOWN`

**Example:**

```bash
ssi debug set-status api_health WARNING
```

**Note:** This appends a manual status entry to the service log file, which the daemon will pick up and report to the backend.

---

## Exit Codes

| Code | Meaning           |
| ---- | ----------------- |
| 0    | Success           |
| 1    | General error     |
| 2    | Invalid arguments |

---

## Environment Variables

Currently, the SSI Agent reads configuration from `/etc/ssi-agent/config.json`. Environment variable support may be added in future versions.

---

## Tips

### Finding Service IDs

Service IDs are derived from the service name by:

1. Converting to lowercase
2. Replacing spaces with underscores

For example:

- "API Health" → `api_health`
- "ZFS Zpool Health" → `zfs_zpool_health`

### Viewing Logs

Service logs are stored in `/var/log/ssi-agent/`:

```bash
# View logs for a specific service
cat /var/log/ssi-agent/api_health.log

# Follow logs in real-time
tail -f /var/log/ssi-agent/api_health.log
```

Agent daemon logs use journald:

```bash
journalctl -u ssi-agent -f
```
