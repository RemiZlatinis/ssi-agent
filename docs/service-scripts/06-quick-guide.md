# Quick Guide for Service-Scripts

This guide is a quick reference for those who are already familiar with writing SSI service-scripts and want to quickly start a new script.

---

## Boilerplate

Create your service-script (e.g., check API health -> `api-health.bash`, check system updates -> `system-updates.bash`) and paste the following template:

```bash
#!/bin/bash

# --- Manifest --- #
# name: Service Name
# description: Concise description of the check (max 255 chars)
# version: 1.0.0
# schedule: *:0/15:00
# timeout: 20

# --- Standard Constants --- #
STATUS_OK="OK"
STATUS_UPDATE="UPDATE"
STATUS_WARNING="WARNING"
STATUS_FAILURE="FAILURE"
TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")

# --- Configurations --- #
# Define configurations and default values using ${VAR:-default}
WARNING_THRESHOLD="${WARNING_THRESHOLD:-80}"
CRITICAL_THRESHOLD="${CRITICAL_THRESHOLD:-95}"
MOUNT_POINT="${MOUNT_POINT:-/}"

# --- Dependencies --- #
# df

# --- Main --- #
# Check the disk usage percentage of the configured mount point
USAGE=$(df -h "$MOUNT_POINT" | awk 'NR==2 {print $5}' | tr -d '%')

if [ "$USAGE" -ge "$CRITICAL_THRESHOLD" ]; then
    echo "$TIMESTAMP, $STATUS_FAILURE, Disk usage critical: ${USAGE}%"
    exit 1
elif [ "$USAGE" -ge "$WARNING_THRESHOLD" ]; then
    echo "$TIMESTAMP, $STATUS_WARNING, Disk usage high: ${USAGE}%"
    exit 0
else
    echo "$TIMESTAMP, $STATUS_OK, Disk usage normal: ${USAGE}%"
    exit 0
fi
```

---

## Quick Reference

### Output Format
The agent parses only the **last line** of the stdout to determine final status. Use this exact format:
```text
<YYYY-MM-DD HH:MM:SS>, <STATUS>, <MESSAGE>
```
*Example:* `2026-06-28 12:00:00, OK, Service is healthy`

### Exit Codes
* **`exit 0`**: Script completed successfully (regardless of whether status is `OK` or `WARNING`).
* **`exit 1`**: Script encountered an internal error or critical service failure.

### Manifest Fields
* **`name`** *(Required)*: Human-readable name shown in UI (3-60 chars).
* **`description`** *(Required)*: Short summary of the script (max 255 chars).
* **`version`** *(Required)*: Semantic version (e.g. `1.0.0`).
* **`schedule`** *(Required)*: systemd timer `OnCalendar` schedule (e.g. `*:0/05:00` for every 5 mins).
* **`timeout`** *(Optional)*: Max execution time in seconds (default: `20`).

---

## CLI Cheatsheet

### 1. Test Locally
Make the script executable and run it directly to verify formatting and output:
```bash
chmod +x api-health.bash
./api-health.bash
```

### 2. Add to Agent
Register the script with the agent (creates systemd services and timers):
```bash
ssi service add api-health.bash
```

### 3. Run Manually
Force execution of the service immediately (uses the service ID derived from the name/filename):
```bash
ssi service run api-health
```

### 4. Check Status
List registered services and their current status:
```bash
# Get summary status of all services
ssi service status

# List all installed service configurations
ssi service list
```

### 5. Debug Logs
Tail the logs for your specific service or watch the daemon:
```bash
# Service output logs
tail -f /var/log/ssi-agent/api-health.log

# Daemon events
ssi debug logs -f
```
