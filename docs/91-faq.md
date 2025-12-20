# Frequently Asked Questions

## General

### What is the SSI Agent?

The SSI Agent is a lightweight monitoring daemon for Linux systems. It runs BASH scripts on a schedule and reports their status to the SSI backend in real-time.

### What systems are supported?

Linux systems with systemd. This includes:

- Ubuntu 20.04+
- Debian 10+
- Fedora
- CentOS/RHEL 8+
- Arch Linux

Windows and macOS are **not supported**.

### Why systemd?

Systemd provides reliable scheduling, process management, logging, and service supervision. It's the standard init system on modern Linux distributions.

---

## Service Scripts

### Can I use Python/Node.js/other languages?

No. Service scripts must be BASH scripts. However, your BASH script can invoke Python or other interpreters:

```bash
# --- Main ---
python3 /path/to/my-check.py
```

### Why do I need to copy constants to every script?

This ensures complete transparency and independence. Each script contains everything it needs to run, with no hidden dependencies or "magic" values.

### How often can I run a check?

As often as systemd timers support (down to 1 second intervals). However, consider:

- Resource usage on your system
- Load on monitored services
- Backend rate limits

Recommended minimum: 1 minute for most checks.

> **If you really need to monitor something with even higher frequency, the SSI is not the right tool for you.**

### Can one script monitor multiple things?

Technically yes, but it's not recommended. Each script should focus on one check for:

- Clear status per service
- Independent scheduling
- Easier troubleshooting

---

## Backend Connection

### What happens if the backend is unreachable?

The agent daemon automatically reconnects with exponential backoff. Status updates are logged locally and reported when connection is restored.

### Is my data encrypted?

Yes, all communication uses TLS (HTTPS/WSS). The WebSocket connection is encrypted.

### Can I use a self-hosted backend?

Yes:

```bash
ssi set-backend https://your-backend.example.com/
```

---

## Status and Notifications

### What's the difference between WARNING and FAILURE?

- **WARNING**: Something needs attention but isn't critical (e.g., disk 85% full)
- **FAILURE**: Critical issue requiring immediate action (e.g., service down)

### What is UPDATE status for?

`UPDATE` indicates an operation is in progress. Use it for long-running tasks like scrubs or backups to show progress.

### How quickly do status changes appear in the app?

Nearly instantly. The daemon sends updates via WebSocket as soon as it detects changes in log files.

---

## Security

### Where is my agent key stored?

In `/etc/ssi-agent/config.json`. This file has restricted permissions.

### Can someone remotely control my system?

No. The agent only **reports** status to the backend. It cannot receive or execute remote commands.

### Should I run scripts as root?

Service scripts run as the `ssi-agent` system user by default. If a script needs elevated privileges, use sudo within the script (with appropriate sudoers configuration).

---

## Troubleshooting

### How do I check if a service is running?

```bash
ssi status my_service
```

Or check systemd directly:

```bash
systemctl status ssi_my_service.timer
```

### Where are the logs?

- Agent daemon: `journalctl -u ssi-agent`
- Service scripts: `/var/log/ssi-agent/<service_id>.log`

### How do I test a script without adding it?

Run it directly:

```bash
chmod +x my-script.bash
./my-script.bash
```
