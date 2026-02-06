# Service Scripts

## What is a Service Script?

A **service script** is a self-contained BASH script that performs a monitoring check and reports its status. Each service script:

- Monitors a specific service, system component, or health check
- Runs on a defined schedule via systemd timers
- Outputs status in a standardized format
- Is completely independent and transparent

## Philosophy

The SSI Agent follows a core philosophy for service scripts:

> **"What you see is exactly what is going to be executed."**

This means:

1. **No Magic** — Scripts are executed exactly as written, with no hidden modifications
2. **Self-Contained** — Each script contains everything it needs to run
3. **Transparent** — Anyone can read the script and understand exactly what it does
4. **Independent** — Scripts don't depend on the SSI Agent at runtime

## Why BASH?

BASH was chosen for service scripts because:

- **Universal** — Available on virtually all Linux systems
- **Native** — No additional runtime or interpreter needed
- **Transparent** — Easy to read, understand, and audit
- **Powerful** — Can invoke any system command or tool
- **Portable** — Scripts can be tested independently of the SSI Agent

## Anatomy of a Service Script

Every service script follows a standardized structure with defined **blocks**:

```bash
#!/bin/bash                           # ← Shebang (Required)

# --- Manifest --- #                   # ← Manifest (Required)
# name: My Service
# description: Does something useful
# version: 1.0
# schedule: *:0/05:00
# timeout: 30

# --- Overview --- #                   # ← Overview (Optional)
# Detailed explanation of what this script does

# --- Standard Constants --- #          # ← Standard Constants (Required)
STATUS_OK="OK"
STATUS_UPDATE="UPDATE"
STATUS_WARNING="WARNING"
STATUS_FAILURE="FAILURE"
TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")

# --- Configurations --- #              # ← Configurations (Optional)
MY_SETTING="value"

# --- Dependencies --- #              # ← Dependencies (Optional)
# curl, jq

# --- Main --- #                        # ← Main (Required)
# The actual monitoring logic goes here
echo "$TIMESTAMP, $STATUS_OK, Everything is fine"
```

## How Service Scripts Are Executed

1. **You add a script** with `ssi add my-script.bash`
2. **SSI creates** systemd service and timer units
3. **systemd timer** triggers the script on schedule
4. **Script runs** and outputs to `/var/log/ssi-agent/<id>.log`
5. **SSI daemon** watches the log file and sends updates to backend

```mermaid
flowchart LR
    T["Timer"] --> SU["Service Unit"] --> S["Script"] --> LF["Log File"] --> D["Daemon"] --> B["Backend"]
```

## Output Format

Service scripts must output status in this exact format:

```
<TIMESTAMP>, <STATUS>, <MESSAGE>
```

Example:

```
2024-01-15 10:30:00, OK, API is healthy
```

See [Status Codes](03-status-codes.md) for the complete reference.

## In This Section

- [Block Structure](01-structure.md) — Detailed breakdown of each block
- [Manifest Reference](02-manifest-reference.md) — Manifest field specifications
- [Status Codes](03-status-codes.md) — Output format and status values
- [Library](04-library.md) — Walkthrough of real service scripts
- [Best Practices](05-best-practices.md) — Tips for writing reliable scripts
