# Service Script Library

This document provides a collection of production-ready service scripts.

## Example 1: API Health Check

**File:** `api-health.bash`

```bash
#!/bin/bash

# --- Manifest --- #
# name: API Health
# description: Checks the health of an API that has a health check endpoint
# version: 1.0
# schedule: *:0/01:00
# timeout: 10

# --- Overview --- #
# Calls the health check endpoint and verifies the response.
# Returns "OK" if response matches expected JSON.
# Returns "WARNING" if response differs.
# Returns "FAILURE" if API is unreachable.

# --- Standard Constants --- #
STATUS_OK="OK"
STATUS_UPDATE="UPDATE"
STATUS_WARNING="WARNING"
STATUS_FAILURE="FAILURE"
TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")

# --- Configurations --- #
URL="https://api.example.com/health/"
read -r -d '' EXPECTED_RESPONSE << 'EOF'
{"status": "healthy"}
EOF

# --- Main --- #
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$URL" 2>/dev/null)

if [ "$HTTP_CODE" != "200" ]; then
    echo "$TIMESTAMP, $STATUS_FAILURE, API unreachable (code: $HTTP_CODE)"
    exit 1
fi

RESPONSE=$(curl -s "$URL" 2>/dev/null)

if [[ "$EXPECTED_RESPONSE" == "$RESPONSE" ]]; then
    echo "$TIMESTAMP, $STATUS_OK, API is healthy"
else
    echo "$TIMESTAMP, $STATUS_WARNING, Response mismatch"
fi
```

## Example 2: System Updates

**File:** `system-updates.bash`

```bash
#!/bin/bash

# --- Manifest --- #
# name: System Updates
# description: Checking for system updates on Debian/Ubuntu
# version: 1.0
# schedule: *:0/01:00
# timeout: 20

# --- Overview --- #
# Checks for available updates on a Debian system.
# Returns "OK" if system is up to date.
# Returns "UPDATE" if updates are available.

# --- Standard Constants --- #
STATUS_OK="OK"
STATUS_UPDATE="UPDATE"
STATUS_WARNING="WARNING"
STATUS_FAILURE="FAILURE"
TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")

# --- Configurations --- #
MSG_OK="System is up to date"

# --- Dependencies --- #
# apt-check (from update-notifier-common package)

# --- Main --- #
updates=$(/usr/lib/update-notifier/apt-check 2>&1)
IFS=';' read -ra update_array <<< "$updates"
total_updates=${update_array[0]}
security_updates=${update_array[1]}

if [ "$total_updates" -gt 0 ]; then
    echo "$TIMESTAMP, $STATUS_UPDATE, $total_updates updates ($security_updates security)"
else
    echo "$TIMESTAMP, $STATUS_OK, $MSG_OK"
fi
```

## Example 3: Disk Usage Monitor

**File:** `disk-usage.bash`

```bash
#!/bin/bash

# --- Manifest --- #
# name: Disk Usage
# description: Monitors root partition disk usage
# version: 1.0
# schedule: *:0/15:00
# timeout: 10

# --- Standard Constants --- #
STATUS_OK="OK"
STATUS_WARNING="WARNING"
STATUS_FAILURE="FAILURE"
TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")

# --- Configurations --- #
MOUNT_POINT="/"
WARNING_THRESHOLD=80
CRITICAL_THRESHOLD=95

# --- Main --- #
USAGE=$(df -h "$MOUNT_POINT" | awk 'NR==2 {print $5}' | tr -d '%')

if [ "$USAGE" -ge "$CRITICAL_THRESHOLD" ]; then
    echo "$TIMESTAMP, $STATUS_FAILURE, Critical: ${USAGE}%"
    exit 1
elif [ "$USAGE" -ge "$WARNING_THRESHOLD" ]; then
    echo "$TIMESTAMP, $STATUS_WARNING, High usage: ${USAGE}%"
else
    echo "$TIMESTAMP, $STATUS_OK, Normal: ${USAGE}%"
fi
```

## Example 4: Long-Running ZFS Scrub

**File:** `zpool-health.bash`

```bash
#!/bin/bash

# --- Manifest --- #
# name: ZFS Zpool Health
# description: Checks the health of ZFS zpools
# version: 1.0
# schedule: *-*-* 06:00:00
# timeout: 300000

# --- Standard Constants --- #
STATUS_OK="OK"
STATUS_UPDATE="UPDATE"
STATUS_WARNING="WARNING"
STATUS_FAILURE="FAILURE"
TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")

# --- Configurations --- #
POOL_NAME="data_pool"

# --- Dependencies --- #
# zpool (ZFS utilities)

# --- Main --- #
if ! command -v zpool &> /dev/null; then
    echo "$TIMESTAMP, $STATUS_FAILURE, zpool command not found"
    exit 1
fi

zpool scrub "$POOL_NAME" &> /dev/null

# Report progress
while zpool status "$POOL_NAME" | grep -q 'scrub in progress'; do
    echo "$(date +"%Y-%m-%d %H:%M:%S"), $STATUS_UPDATE, Scrub in progress..."
    sleep 30
done

# Check final status
POOL_STATUS=$(zpool status "$POOL_NAME" | grep "state:" | awk '{print $2}')

if [ "$POOL_STATUS" = "ONLINE" ]; then
    echo "$TIMESTAMP, $STATUS_OK, Pool is healthy"
else
    echo "$TIMESTAMP, $STATUS_FAILURE, Pool state: $POOL_STATUS"
    exit 1
fi
```

## Key Takeaways

1. **Always include all required blocks** (Shebang, Manifest, Standard Constants, Main)
2. **Use configuration variables** for customizable values
3. **Document dependencies** for transparency
4. **Use appropriate status codes** for each scenario
5. **Exit with proper codes** (0 for success, 1 for failure)
