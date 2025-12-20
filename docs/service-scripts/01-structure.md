# Service Script Block Structure

Every service script follows a standardized structure composed of distinct **blocks**. This document defines each block, its purpose, and requirements.

## Block Overview

| #   | Block Name             | Required | Description                            |
| --- | ---------------------- | -------- | -------------------------------------- |
| 0   | **Shebang**            | ✅ Yes   | Interpreter directive                  |
| 1   | **Manifest**           | ✅ Yes   | Script metadata (name, schedule, etc.) |
| 2   | **Overview**           | ❌ No    | Detailed explanation of the script     |
| 3   | **Standard Constants** | ✅ Yes   | Pre-defined status codes and timestamp |
| 4   | **Configuration**      | ❌ No    | User-customizable settings             |
| 5   | **Dependencies**       | ❌ No    | External tools required by the script  |
| 6   | **Main**               | ✅ Yes   | Core monitoring logic                  |

---

## Block 0: Shebang (Required)

The **Shebang** is the first line of every script. It tells the system which interpreter to use.

```bash
#!/bin/bash
```

**Rules:**

- Must be the very first line of the file
- Must be exactly `#!/bin/bash`
- No other interpreters are supported

---

## Block 1: Manifest (Required)

The **Manifest** contains metadata about the script. It is parsed by the SSI Agent when adding the service.

```bash
# --- Manifest --- #
# name: API Health
# description: Checks the health of an API that has a health check endpoint
# version: 1.0
# schedule: *:0/01:00
# timeout: 10
```

**Fields:**

| Field         | Required | Description                                 |
| ------------- | -------- | ------------------------------------------- |
| `name`        | ✅ Yes   | Human-readable name (3-60 characters)       |
| `description` | ✅ Yes   | Short description (max 255 characters)      |
| `version`     | ✅ Yes   | Version string (e.g., `1.0`, `2.1.3`)       |
| `schedule`    | ✅ Yes   | systemd OnCalendar format                   |
| `timeout`     | ❌ No    | Max execution time in seconds (default: 20) |

See [Manifest Reference](02-manifest-reference.md) for detailed specifications.

---

## Block 2: Overview (Optional)

The **Overview** block provides a detailed explanation of what the script does. Use this to describe:

- What the script monitors
- What conditions trigger each status
- Expected behavior

```bash
# --- Overview --- #
# This script calls the health check endpoint at the configured URL
# and checks for the expected response.
#
# Returns "OK" if the API responds with the expected JSON.
# Returns "WARNING" if the response differs from expected.
# Returns "FAILURE" if the API is unreachable.
```

**Guidelines:**

- Explain **what** the script does, not **how** it does it
- Describe the conditions for each possible status
- Do not explain the code itself (code should be self-documenting)

---

## Block 3: Standard Constants (Required)

The **Standard Constants** block contains pre-defined values that every service script must include. These are **hardcoded by design** to ensure complete transparency and independence.

```bash
# --- Standard Constants --- #
STATUS_OK="OK"
STATUS_UPDATE="UPDATE"
STATUS_WARNING="WARNING"
STATUS_FAILURE="FAILURE"
TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")
```

**Why are these copied to every script?**

1. **Transparency**: What you see is exactly what runs
2. **Independence**: Scripts work without the SSI Agent installed
3. **Auditability**: No hidden values or imports
4. **Reliability**: No external dependencies

**Additional Constants (Optional):**

You may add additional constants like `STATUS_ERROR` if your script uses them:

```bash
STATUS_ERROR="ERROR"
STATUS_UNKNOWN="UNKNOWN"
```

---

## Block 4: Configuration (Optional)

The **Configuration** block contains user-specific settings that customize the script's behavior.

```bash
# --- Configurations --- #
URL="https://api.example.com/health/"
EXPECTED_STATUS=200
RETRY_COUNT=3

# Configuration with defaults (for dynamic configuration)
ALERT_THRESHOLD="${ALERT_THRESHOLD:-90}"
```

**Guidelines:**

- Place all configurable values here
- Use meaningful variable names in UPPER_SNAKE_CASE
- Provide sensible defaults where appropriate
- Use `${VAR:-default}` syntax for optional environment variables

---

## Block 5: Dependencies (Optional)

The **Dependencies** block documents external tools required by the script. This block is purely for documentation and transparency.

```bash
# --- Dependencies --- #
# curl      - HTTP client for API requests
# jq        - JSON parser (optional, for complex responses)
# zpool     - ZFS pool management utility
```

**Guidelines:**

- List each dependency on its own line
- Include a brief description of why it's needed
- This helps users understand what must be installed

---

## Block 6: Main (Required)

The **Main** block contains the core monitoring logic of the script. This is where the actual work happens.

```bash
# --- Main --- #
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$URL" 2>/dev/null)

if [ "$HTTP_CODE" = "200" ]; then
    echo "$TIMESTAMP, $STATUS_OK, API is healthy"
    exit 0
else
    echo "$TIMESTAMP, $STATUS_FAILURE, API returned HTTP $HTTP_CODE"
    exit 1
fi
```

**Rules:**

1. **Output Format**: Must print status in the format:

   ```
   <TIMESTAMP>, <STATUS>, <MESSAGE>
   ```

2. **Exit Codes**:

   - `exit 0` — Script completed successfully (status can be any)
   - `exit 1` — Script encountered an error

3. **Single Final Status**: The last line of output determines the reported status

4. **Streaming Updates**: For long-running scripts, you can output multiple `UPDATE` lines:
   ```bash
   echo "$TIMESTAMP, $STATUS_UPDATE, Scrub in progress: 25%"
   sleep 5
   echo "$TIMESTAMP, $STATUS_UPDATE, Scrub in progress: 50%"
   sleep 5
   echo "$TIMESTAMP, $STATUS_OK, Scrub completed successfully"
   ```

---

## Complete Example

Here's a complete service script with all blocks:

```bash
#!/bin/bash

# --- Manifest --- #
# name: Disk Usage Check
# description: Monitors disk usage and warns if above threshold
# version: 1.0
# schedule: *:0/15:00
# timeout: 30

# --- Overview --- #
# This script checks the disk usage of the root partition.
# Returns "OK" if usage is below 80%.
# Returns "WARNING" if usage is between 80% and 95%.
# Returns "FAILURE" if usage is above 95%.

# --- Standard Constants --- #
STATUS_OK="OK"
STATUS_UPDATE="UPDATE"
STATUS_WARNING="WARNING"
STATUS_FAILURE="FAILURE"
TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")

# --- Configurations --- #
MOUNT_POINT="/"
WARNING_THRESHOLD=80
CRITICAL_THRESHOLD=95

# --- Dependencies --- #
# df - Disk free utility (standard on all Linux systems)

# --- Main --- #
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

## Block Order

Blocks should appear in this order for consistency:

1. Shebang
2. Manifest
3. Overview _(if present)_
4. Standard Constants
5. Configuration _(if present)_
6. Dependencies _(if present)_
7. Main

---

## Block Markers

Use consistent comment markers to identify blocks:

```bash
# --- Block Name --- #
```

This makes scripts easy to scan and understand.
