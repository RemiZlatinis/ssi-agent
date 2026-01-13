# Quick Start

This guide will get you up and running with the SSI Agent in under 5 minutes.

## Step 1: Install the Agent

```bash
git clone https://github.com/RemiZlatinis/ssi-agent.git
cd ssi-agent
sudo ./install.sh
```

## Step 2: Register the Agent

Connect your agent to the SSI backend:

```bash
ssi register
```

You'll see output like:

```
Registration Code: 123456

Enter this code in an SSI client to complete registration.
Waiting for confirmation...
```

Open your SSI client, navigate to **Add Agent**, and enter the 6-digit code.

## Step 3: Add Your First Service

Create a simple service script to monitor something. Here's an example that checks if a website is reachable:

_Note the [Block Structure](service-scripts/01-structure.md) of the service script_

```bash
# Create a new service script
cat > ~/website-check.bash << 'EOF'
#!/bin/bash

# --- Manifest --- #
# name: Website Check
# description: Checks if example.com is reachable
# version: 1.0
# schedule: *:0/5:00
# timeout: 30

# --- Standard Constants --- #
STATUS_OK="OK"
STATUS_UPDATE="UPDATE"
STATUS_WARNING="WARNING"
STATUS_FAILURE="FAILURE"
TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")

# --- Configurations --- #
URL="https://example.com"

# --- Main --- #
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$URL" 2>/dev/null)

if [ "$HTTP_CODE" = "200" ]; then
    echo "$TIMESTAMP, $STATUS_OK, Website is reachable"
else
    echo "$TIMESTAMP, $STATUS_FAILURE, Website returned HTTP $HTTP_CODE"
    exit 1
fi
EOF
```

Add the service to the agent:

```bash
ssi add ~/website-check.bash
```

## Step 4: Verify It's Working

List your services:

```bash
ssi list
```

Check the status:

```bash
ssi status
```

Manually run the service to test it:

```bash
ssi run website_check
```

## Step 5: Monitor in the App

Open your SSI mobile app — your new service should appear with its current status!

---

## What Just Happened?

1. **The agent** registered with the backend and received an authentication token
2. **Your service script** was copied to `/opt/ssi-agent/.installed-service-scripts/`
3. **Systemd timer** was created to run the script every 5 minutes
4. **Systemd service** was created to execute the script
5. **The daemon** is watching the log file and sending updates to the backend

## Next Steps

- [Learn about service script structure](service-scripts/01-structure.md)
- [Explore CLI commands](05-cli-reference.md)
- [Browse the service script library](service-scripts/04-library.md)

## Common Commands

| Task                 | Command                   |
| -------------------- | ------------------------- |
| Add a service        | `ssi add <script.bash>`   |
| Remove a service     | `ssi remove <service_id>` |
| List all services    | `ssi list`                |
| Check status         | `ssi status`              |
| Run service manually | `ssi run <service_id>`    |
| View agent info      | `ssi whoami`              |
