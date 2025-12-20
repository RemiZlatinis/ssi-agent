# Configuration

## Configuration File

The SSI Agent stores its configuration in JSON format at:

```
/etc/ssi-agent/config.json
```

### Default Configuration

After installation, the default configuration looks like:

```json
{
  "backend_url": "https://api.service-status-indicator.com/",
  "log_level": "INFO",
  "log_dir": "/var/log/ssi-agent",
  "config_dir": "/etc/ssi-agent"
}
```

### Configuration Options

| Option        | Type   | Default                                     | Description                                            |
| ------------- | ------ | ------------------------------------------- | ------------------------------------------------------ |
| `backend_url` | string | `https://api.service-status-indicator.com/` | URL of the SSI backend                                 |
| `agent_key`   | string | _(none)_                                    | Authentication key (set during registration)           |
| `log_level`   | string | `INFO`                                      | Logging verbosity: `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `log_dir`     | string | `/var/log/ssi-agent`                        | Directory for service log files                        |
| `config_dir`  | string | `/etc/ssi-agent`                            | Directory for configuration files                      |

### Modifying Configuration

#### Via CLI

The recommended way to modify configuration is using the CLI:

```bash
# Set the backend URL
ssi set-backend https://your-backend.example.com/
```

#### Manual Editing

You can also edit the configuration file directly:

```bash
sudo nano /etc/ssi-agent/config.json
```

After manual changes, restart the daemon:

```bash
sudo systemctl restart ssi-agent
```

---

## File Permissions

The configuration directory uses ACLs to allow admin users to modify settings without `sudo`:

```
/etc/ssi-agent/           (drwxrwxr-x+ ssi-agent:ssi-agent)
└── config.json           (-rw-rw-r--+ ssi-agent:ssi-agent)
```

Users in the `sudo` (Debian) or `wheel` (RHEL) group have write access.

---

## Agent Key

The `agent_key` is a sensitive value that authenticates the agent with the backend. It is:

- Generated during registration
- Stored in `config.json`
- Used for WebSocket authentication
- **Should not be shared or exposed**

If the agent key is compromised:

1. Run `ssi unregister`
2. Run `ssi register` to obtain a new key

---

## Logging Configuration

### Log Levels

| Level     | Description                           |
| --------- | ------------------------------------- |
| `DEBUG`   | Detailed debugging information        |
| `INFO`    | General operational messages          |
| `WARNING` | Warning messages for potential issues |
| `ERROR`   | Error messages for failures           |

To change the log level, edit `config.json`:

```json
{
  "log_level": "DEBUG"
}
```

Then restart the daemon:

```bash
sudo systemctl restart ssi-agent
```

### Log Locations

| Log Type        | Location                              |
| --------------- | ------------------------------------- |
| Agent daemon    | `journalctl -u ssi-agent`             |
| Service scripts | `/var/log/ssi-agent/<service_id>.log` |

---

## Backend URL Configuration

The backend URL can be configured for different environments:

### Production (Default)

```bash
ssi set-backend https://api.service-status-indicator.com/
```

### Self-Hosted Backend

```bash
ssi set-backend https://your-domain.com/
```

### Local Development

```bash
ssi set-backend http://localhost:8000/
```

**Note:** For local development, HTTP is acceptable. For production, always use HTTPS.

---

## Systemd Service Configuration

The agent daemon is managed by systemd with the following service file:

```
/etc/systemd/system/ssi-agent.service
```

### Viewing the Service File

```bash
cat /etc/systemd/system/ssi-agent.service
```

### Modifying Daemon Behavior

If you need to customize the daemon (e.g., add environment variables), create a drop-in file:

```bash
sudo mkdir -p /etc/systemd/system/ssi-agent.service.d/
sudo nano /etc/systemd/system/ssi-agent.service.d/override.conf
```

Example override:

```ini
[Service]
Environment="SSI_LOG_LEVEL=DEBUG"
```

Reload and restart:

```bash
sudo systemctl daemon-reload
sudo systemctl restart ssi-agent
```

---

## Troubleshooting Configuration Issues

### "backend_url not found in config file"

The configuration file is missing or malformed. Recreate it:

```bash
sudo tee /etc/ssi-agent/config.json << EOF
{
    "backend_url": "https://api.service-status-indicator.com/"
}
EOF
```

### "Config file is not valid JSON"

The configuration file has a syntax error. Validate it:

```bash
python3 -m json.tool /etc/ssi-agent/config.json
```

Fix any reported errors.

### Permission Denied When Registering

Ensure your user is in the admin group:

```bash
# Debian/Ubuntu
sudo usermod -aG sudo $USER

# RHEL/CentOS
sudo usermod -aG wheel $USER
```

Log out and back in for the change to take effect.
