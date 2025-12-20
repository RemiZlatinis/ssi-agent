# Status Codes & Output Format

Service scripts communicate their status through standardized output.

## Output Format

Every status line must follow this exact format:

```
<TIMESTAMP>, <STATUS>, <MESSAGE>
```

| Component | Format                   | Example               |
| --------- | ------------------------ | --------------------- |
| TIMESTAMP | `YYYY-MM-DD HH:MM:SS`    | `2024-01-15 10:30:00` |
| STATUS    | One of the defined codes | `OK`                  |
| MESSAGE   | Free-form description    | `API is healthy`      |

## Standard Status Codes

### `OK`

Everything is working as expected.

```bash
echo "$TIMESTAMP, $STATUS_OK, API is healthy"
```

**Use when:** All checks passed, service operating normally.

### `UPDATE`

An operation is in progress.

```bash
echo "$TIMESTAMP, $STATUS_UPDATE, Scrub in progress: 45%"
```

**Use when:** Long-running operation executing, progress updates.

### `WARNING`

Something needs attention but isn't critical.

```bash
echo "$TIMESTAMP, $STATUS_WARNING, Disk usage at 85%"
```

**Use when:** Threshold approaching, non-critical failures.

### `FAILURE`

A critical failure occurred.

```bash
echo "$TIMESTAMP, $STATUS_FAILURE, Database connection refused"
```

**Use when:** Service is down, critical check failed.

### `ERROR` (Optional)

Script internal error.

```bash
echo "$TIMESTAMP, $STATUS_ERROR, Missing configuration"
```

### `UNKNOWN` (Optional)

Status could not be determined.

```bash
echo "$TIMESTAMP, $STATUS_UNKNOWN, Unable to determine status"
```

## Standard Constants Block

```bash
# --- Standard Constants --- #
STATUS_OK="OK"
STATUS_UPDATE="UPDATE"
STATUS_WARNING="WARNING"
STATUS_FAILURE="FAILURE"
TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")
```

## Exit Codes

| Exit Code | Meaning                       |
| --------- | ----------------------------- |
| `0`       | Script completed successfully |
| `1`       | Script encountered an error   |

## Multiple Output Lines

The **last line** determines the final status. Use multiple lines for progress:

```bash
echo "$TIMESTAMP, $STATUS_UPDATE, Starting scrub..."
sleep 60
echo "$TIMESTAMP, $STATUS_UPDATE, Scrub 50% complete"
sleep 60
echo "$TIMESTAMP, $STATUS_OK, Scrub completed"
```
