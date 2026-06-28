# Quick Service Script Guide

This guide is a quick reference for developers who are already familiar with writing SSI service scripts and want to quickly start a new script.

---

## Copy-Pastable Boilerplate

Create your service script (e.g., `my-check.bash`) and paste the following template:

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

# --- Dependencies --- #
# curl - HTTP requests
# jq   - JSON parsing

# --- Main --- #
# 1. Verify dependencies are available
for cmd in curl jq; do
    if ! command -v "$cmd" &>/dev/null; then
        echo "$TIMESTAMP, $STATUS_FAILURE, Required dependency '$cmd' is missing."
        exit 1
    fi
done

# 2. Add monitoring logic here
# Example check:
USAGE=50

# 3. Output results and exit with correct status code
if [ "$USAGE" -ge "$CRITICAL_THRESHOLD" ]; then
    echo "$TIMESTAMP, $STATUS_FAILURE, Critical failure: value is ${USAGE}%"
    exit 1
elif [ "$USAGE" -ge "$WARNING_THRESHOLD" ]; then
    echo "$TIMESTAMP, $STATUS_WARNING, Warning: value is ${USAGE}%"
    exit 0
else
    echo "$TIMESTAMP, $STATUS_OK, Normal: value is ${USAGE}%"
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
chmod +x my-check.bash
./my-check.bash
```

### 2. Add to Agent
Register the script with the agent (creates systemd services and timers):
```bash
ssi add my-check.bash
```

### 3. Run Manually
Force execution of the service immediately:
```bash
ssi run my-check
```

### 4. Check Status
List registered services and their current state:
```bash
ssi service status
```

### 5. Debug Logs
Tail the logs for your specific service or watch the daemon:
```bash
# Service output logs
tail -f /var/log/ssi-agent/my-check.log

# Daemon events
ssi debug logs -f
```
