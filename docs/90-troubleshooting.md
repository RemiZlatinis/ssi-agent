# Troubleshooting

Common issues and their solutions.

## Agent Issues

### Agent won't start

**Symptoms:** `systemctl status ssi-agent` shows failed state

**Solutions:**

1. Check the logs:

   ```bash
   journalctl -u ssi-agent -n 50
   ```

2. Verify configuration file:

   ```bash
   python3 -m json.tool /etc/ssi-agent/config.json
   ```

3. Check if agent is registered:
   ```bash
   ssi whoami
   ```

### Agent not connecting to backend

**Symptoms:** Agent running but no data in mobile app

**Solutions:**

1. Verify backend URL:

   ```bash
   cat /etc/ssi-agent/config.json | grep backend_url
   ```

2. Test connectivity:

   ```bash
   curl -I https://api.service-status-indicator.com/api/health/
   ```

3. Check for firewall issues:

   ```bash
   sudo iptables -L -n
   ```

4. Restart the agent:
   ```bash
   sudo systemctl restart ssi-agent
   ```

### Registration fails

**Symptoms:** `ssi register` times out or fails

**Solutions:**

1. Check network connectivity to backend
2. Verify backend URL is correct
3. Check backend logs for errors
4. Try again after a few minutes

---

## Service Script Issues

### Service not running on schedule

**Symptoms:** Timer exists but script never executes

**Solutions:**

1. Check timer status:

   ```bash
   systemctl list-timers | grep ssi_
   ```

2. Verify timer is enabled:

   ```bash
   systemctl is-enabled ssi_my_service.timer
   ```

3. Check service status:

   ```bash
   systemctl status ssi_my_service.service
   ```

4. Reload systemd:
   ```bash
   sudo systemctl daemon-reload
   ```

### Script runs but status not reported

**Symptoms:** Log file has output but no update in app

**Solutions:**

1. Check output format matches expected:

   ```
   YYYY-MM-DD HH:MM:SS, STATUS, Message
   ```

2. Verify log file exists:

   ```bash
   ls -la /var/log/ssi-agent/
   ```

3. Check agent is watching the file:
   ```bash
   journalctl -u ssi-agent | grep my_service
   ```

### "Service script must be a .bash file"

**Solution:** Rename your script with `.bash` extension:

```bash
mv my-script.sh my-script.bash
```

### "Service name must be between 3 and 60 characters"

**Solution:** Update the `# name:` field in your script.

### "Invalid schedule format"

**Solution:** Verify your schedule using:

```bash
systemd-analyze calendar "your-schedule-here"
```

---

## Permission Issues

### "Permission denied" when adding service

**Solutions:**

1. Check you're in the admin group:

   ```bash
   groups
   ```

2. Use sudo if needed:
   ```bash
   sudo ssi add my-script.bash
   ```

### Can't write to log directory

**Solutions:**

1. Check permissions:

   ```bash
   ls -la /var/log/ssi-agent/
   ```

2. Fix ownership:
   ```bash
   sudo chown -R ssi-agent:ssi-agent /var/log/ssi-agent/
   ```

---

## Log Inspection

### View agent daemon logs

```bash
journalctl -u ssi-agent -f
```

### View service script logs

```bash
tail -f /var/log/ssi-agent/<service_id>.log
```

### View systemd timer logs

```bash
journalctl -u ssi_<service_id>.timer
journalctl -u ssi_<service_id>.service
```

---

## Reset and Recovery

### Completely reset agent

```bash
# Unregister
ssi unregister

# Re-register
ssi register

# Restart
sudo systemctl restart ssi-agent
```

### Force remove broken service

```bash
ssi remove broken_service --force
```

### Reinstall agent

```bash
cd ssi-agent
sudo ./install.sh --remove
sudo ./install.sh
```
