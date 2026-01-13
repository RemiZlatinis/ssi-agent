# CLI Reference

The SSI Agent provides a command-line interface (`ssi`) for managing services and agent configuration.

## Global Options

```bash
ssi --help     # Show help message
ssi --version  # Show version (if available)
```

---

## Service Management

### `ssi service add`

Add a new service from a BASH script.

```bash
ssi service add <service-script-path> [--no-start]
```

**Arguments:**

- `service-script-path` — Path to the service script (.bash file)

**Options:**

- `--no-start` — Don't enable/start the service immediately.

**Example:**

```bash
ssi service add ~/my-scripts/api-health.bash
ssi service add ./system-check.bash
```

**What it does:**

1. Parses the script to extract metadata (name, description, schedule, etc.)
2. Validates the script structure
3. Copies the script to `/opt/ssi-agent/.installed-service-scripts/`
4. Creates systemd service and timer units
5. Enables and starts the timer

---

### `ssi service remove`

Remove a service by its ID.

```bash
ssi service remove <service-id> [--force]
```

**Arguments:**

- `service-id` — The ID of the service (derived from the name in kebab-case)

**Options:**

- `--force` — Remove the service even if it's currently running or enabled.

**Example:**

```bash
ssi service remove api-health
ssi service remove broken-service --force
```

---

### `ssi service list`

List installed services.

```bash
ssi service list [--all]
```

**Example output:**

```
ID              | Name            | Version | Enabled | Schedule
----------------|-----------------|---------|---------|------------------
api-health      | API Health      | 1.0     | Yes     | *:0/01:00
system-updates  | System Updates  | 1.0     | Yes     | *-*-* 06:00:00
zpool-health    | ZFS Zpool Health| 1.0     | No      | *-*-* 06:00:00
```

---

### `ssi service status`

Display the status of a service or all services.

```bash
ssi service status [service-id] [--details]
```

**Example:**

```bash
# Status of all services
ssi service status

# Status of specific service
ssi service status api-health

# Detailed status
ssi service status api-health --details
```

---

### `ssi service run`

Manually run a service script immediately.

```bash
ssi service run <service-id>
```

**Example:**

```bash
ssi service run api-health
```

---

## Agent Management

### `ssi auth register`

Register the agent with the SSI backend.

```bash
ssi auth register
```

---

### `ssi auth unregister`

Unregister the agent and remove the agent key.

```bash
ssi auth unregister
```

---

### `ssi auth whoami`

Display information about the current agent.

```bash
ssi auth whoami
```

---

## Configuration

### `ssi debug set-backend`

Set the backend URL in the configuration file.

```bash
ssi debug set-backend <backend-url>
```

---

## Debugging

### `ssi debug set-status`

Manually set the status of a service (for debugging purposes).

```bash
ssi debug set-status <service-id> <status> [message]
```

**Example:**

```bash
ssi debug set-status api-health WARNING "Manual check failed"
```

---

### `ssi debug logs`

Display the ssi-agent daemon logs.

```bash
ssi debug logs [-f] [-n <lines>]
```

**Options:**

- `-f`, `--follow` — Follow log output (like `tail -f`)
- `-n`, `--lines <int>` — Number of last lines to show (default: 50)

**Example:**

```bash
# View last 50 lines
ssi debug logs

# Follow logs in real-time
ssi debug logs -f
```

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
2. Replacing spaces with hyphens

For example:

- "API Health" → `api-health`
- "ZFS Zpool Health" → `zfs-zpool-health`

### Viewing Logs

Service logs are stored in `/var/log/ssi-agent/`:

Service scripts: `/var/log/ssi-agent/<service-id>.log`

```bash
# View logs for a specific service
cat /var/log/ssi-agent/api-health.log

# Follow logs in real-time
tail -f /var/log/ssi-agent/api-health.log
```

Agent daemon logs use journald:

```bash
journalctl -u ssi-agent -f
```
