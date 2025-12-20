# Manifest Reference

The **Manifest** block contains metadata about the service script. This metadata is parsed by the SSI Agent when adding a service.

## Manifest Format

Each manifest field is a comment line with the format:

```bash
# field: value
```

## Fields

### `name` (Required)

The human-readable name of the service.

```bash
# name: API Health
```

**Constraints:**

- Minimum: 3 characters
- Maximum: 60 characters
- Allowed: Letters, numbers, spaces, hyphens

**What it's used for:**

- Display name in the mobile app
- Deriving the service ID (name → snake_case)

**Examples:**

```bash
# --- Manifest --- #
# name: API Health
# name: ZFS Zpool Health
# name: System Updates
# name: Daily Backup Verifier
```

---

### `description` (Required)

A short description of what the service monitors.

```bash
# description: Checks the health of an API that has a health check endpoint
```

**Constraints:**

- Maximum: 255 characters

**What it's used for:**

- Displayed in the mobile app
- systemd unit file Description field

**Examples:**

```bash
# description: Checks the health of an API endpoint
# description: Monitors available system updates on Debian/Ubuntu
# description: Verifies BTRFS filesystem integrity via scrub
```

---

### `version` (Required)

The version of the service script.

```bash
# version: 1.0
```

**Format:**

- Any string (typically semver like `1.0`, `1.0.0`, `2.1.3`)
  _For simplicity, we recommend x.y format like `1.0`, `1.1`, `2.0`._

**What it's used for:**

- Tracking script versions
- Future: Detecting when to update

**Examples:**

```bash
# version: 1.0
# version: 1.1
# version: 2.0
```

---

### `schedule` (Required)

The schedule for running the service script, in systemd OnCalendar format.

```bash
# schedule: *:0/01:00
```

**Format:** systemd OnCalendar expression

**Common patterns:**

| Pattern              | Meaning                          |
| -------------------- | -------------------------------- |
| `*:0/01:00`          | Every 1 minute                   |
| `*:0/05:00`          | Every 5 minutes                  |
| `*:0/15:00`          | Every 15 minutes                 |
| `*-*-* 06:00:00`     | Daily at 6:00 AM                 |
| `*-*-* 00:00:00`     | Daily at midnight                |
| `Mon *-*-* 00:00:00` | Every Monday at midnight         |
| `*-*-01 00:00:00`    | First of every month at midnight |

**Understanding the format:**

```
DayOfWeek Year-Month-Day Hour:Minute:Second

Examples:
*-*-* 06:00:00       = Every day at 06:00:00
Mon *-*-* 06:00:00   = Every Monday at 06:00:00
*:0/5:00             = Every 5 minutes (at :00, :05, :10, etc.)
*:*:0/30             = Every 30 seconds
```

**Testing your schedule:**

Use `systemd-analyze calendar` to verify:

```bash
systemd-analyze calendar "*:0/05:00"
```

Output:

```
  Original form: *:0/05:00
Normalized form: *-*-* *:00/5:00
    Next elapse: Fri 2024-01-15 10:35:00 UTC
       (in UTC): Fri 2024-01-15 10:35:00 UTC
       From now: 2min 30s left
```

---

### `timeout` (Optional)

Maximum execution time in seconds. The script will be killed if it exceeds this duration.

```bash
# timeout: 30
```

**Default:** 20 seconds

**Constraints:**

- Minimum: 1 second
- Recommended maximum: Match your schedule interval

**What it's used for:**

- systemd `TimeoutSec` directive
- Preventing hung scripts from blocking the system

**Examples:**

```bash
# timeout: 10      # Quick API check
# timeout: 60      # Longer health check
# timeout: 300     # 5-minute ZFS scrub status check
# timeout: 86400   # Full day for very long operations
```

---

## Complete Manifest Example

```bash
# name: API Health
# description: Checks the health of an API that has a health check endpoint
# version: 1.0
# schedule: *:0/01:00
# timeout: 10
```

---

## Validation

When you run `ssi add`, the manifest is validated:

| Field         | Validation                        |
| ------------- | --------------------------------- |
| `name`        | Required, 3-60 chars              |
| `description` | Required, max 255 chars           |
| `version`     | Required                          |
| `schedule`    | Required, valid OnCalendar format |
| `timeout`     | Optional, must be > 0 if provided |

**Error examples:**

```
ValueError: Service name must be between 3 and 60 characters.
ValueError: Service description cannot exceed 255 characters.
ValueError: Service script must contain a schedule metadata.
ValueError: Invalid schedule format...
```

---

## Service ID Derivation

The service ID is automatically derived from the `name` field:

1. Convert to lowercase
2. Replace spaces with underscores

**Examples:**

| Name                  | Service ID              |
| --------------------- | ----------------------- |
| API Health            | `api_health`            |
| ZFS Zpool Health      | `zfs_zpool_health`      |
| System Updates        | `system_updates`        |
| Daily Backup Verifier | `daily_backup_verifier` |

The service ID is used for:

- systemd unit file names (`ssi_api_health.service`)
- Log file names (`api_health.log`)
- CLI commands (`ssi status api_health`)
