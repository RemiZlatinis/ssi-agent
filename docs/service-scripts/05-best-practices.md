# Best Practices

Guidelines for writing reliable, maintainable service scripts.

## Script Structure

### ✅ Do

- Follow the standard block order (Shebang → Manifest → Constants → Main)
- Use clear block markers (`# --- Block Name --- #`)
- Keep scripts focused on a single check
- Use descriptive variable names

### ❌ Don't

- Skip required blocks
- Mix configuration with logic
- Create overly complex multi-purpose scripts
- Use cryptic variable names

## Output Guidelines

### ✅ Do

```bash
# Clear, actionable messages
echo "$TIMESTAMP, $STATUS_OK, API responded in 45ms"
echo "$TIMESTAMP, $STATUS_WARNING, Disk usage at 87%"
echo "$TIMESTAMP, $STATUS_FAILURE, Connection refused after 3 retries"
```

### ❌ Don't

```bash
# Vague or unhelpful messages
echo "$TIMESTAMP, $STATUS_OK, OK"
echo "$TIMESTAMP, $STATUS_FAILURE, Error"
```

## Error Handling

### Always handle edge cases

```bash
# Check if command exists
if ! command -v curl &> /dev/null; then
    echo "$TIMESTAMP, $STATUS_FAILURE, curl not installed"
    exit 1
fi

# Handle empty responses
if [ -z "$RESPONSE" ]; then
    echo "$TIMESTAMP, $STATUS_WARNING, Empty response received"
fi
```

### Use appropriate exit codes

```bash
# Exit 0 for successful execution
echo "$TIMESTAMP, $STATUS_WARNING, 5 updates available"
exit 0  # Script ran successfully

# Exit 1 for failures
echo "$TIMESTAMP, $STATUS_FAILURE, Cannot connect"
exit 1  # Indicate failure condition
```

## Configuration

### Use sensible defaults

```bash
# --- Configurations --- #
TIMEOUT="${TIMEOUT:-30}"
RETRIES="${RETRIES:-3}"
URL="${URL:-https://api.example.com/health}"
```

### Group related settings

```bash
# --- Configurations --- #
# API Settings
API_URL="https://api.example.com"
API_TIMEOUT=30

# Thresholds
WARNING_THRESHOLD=80
CRITICAL_THRESHOLD=95
```

## Testing

### Test locally before adding

```bash
# Make executable
chmod +x my-script.bash

# Run directly
./my-script.bash

# Verify output format
./my-script.bash | grep -E "^[0-9]{4}-[0-9]{2}-[0-9]{2}"
```

### Test with `ssi run`

```bash
# After adding the service
ssi run my_service

# Check the log
tail -f /var/log/ssi-agent/my_service.log
```

## Performance

### Avoid unnecessary work

```bash
# Good: Check reachability first
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$URL")
if [ "$HTTP_CODE" != "200" ]; then
    echo "$TIMESTAMP, $STATUS_FAILURE, Unreachable"
    exit 1
fi

# Then do the actual check
RESPONSE=$(curl -s "$URL")
```

### Set appropriate timeouts

```bash
# Use curl timeout
RESPONSE=$(curl -s --max-time 10 "$URL")

# Match manifest timeout to expected duration
# timeout: 15
```

## Security

### Never hardcode secrets

```bash
# Bad
API_KEY="sk-1234567890"

# Good - use environment variables
API_KEY="${API_KEY:?API_KEY environment variable required}"
```

### Validate input

```bash
# Validate URL format
if [[ ! "$URL" =~ ^https?:// ]]; then
    echo "$TIMESTAMP, $STATUS_FAILURE, Invalid URL format"
    exit 1
fi
```

## Common Patterns

### Threshold-based checks

```bash
if [ "$VALUE" -ge "$CRITICAL" ]; then
    echo "$TIMESTAMP, $STATUS_FAILURE, Critical: $VALUE"
elif [ "$VALUE" -ge "$WARNING" ]; then
    echo "$TIMESTAMP, $STATUS_WARNING, Warning: $VALUE"
else
    echo "$TIMESTAMP, $STATUS_OK, Normal: $VALUE"
fi
```

### Retry logic

```bash
for i in $(seq 1 $RETRIES); do
    RESPONSE=$(curl -s "$URL")
    if [ -n "$RESPONSE" ]; then
        break
    fi
    sleep 2
done
```

### Cleanup on exit

```bash
TEMP_FILE=$(mktemp)
trap "rm -f $TEMP_FILE" EXIT

# Use temp file...
```

## Checklist

Before adding a service script:

- [ ] Shebang is `#!/bin/bash`
- [ ] All required manifest fields present
- [ ] Standard constants block included
- [ ] Output follows correct format
- [ ] Exit codes are appropriate
- [ ] Tested locally
- [ ] Dependencies documented
- [ ] Timeout is reasonable
