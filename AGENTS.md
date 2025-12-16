# AGENTS.md — ssi-agent

> **This file takes precedence over README.md when directives conflict.**  
> **Architectural intent must be preserved over convenience.**

---

## Scope

### What This Repository Is

- Monitoring agent/daemon for Linux systems (systemd-dependent)
- Runs service checks and reports status to backend
- Operates unattended, headless, and predictably
- Built with Python 3.12+, Click CLI, and WebSocket client

### What This Repository Is NOT

- A cross-platform tool (Linux only)
- An interactive application
- A self-updating system
- A standalone monitoring solution

### Interacts With

| Component     | Relationship                            |
| ------------- | --------------------------------------- |
| `ssi-backend` | Reports status via WebSocket connection |

---

## Execution Model

| Aspect           | Specification                                                |
| ---------------- | ------------------------------------------------------------ |
| **Target OS**    | Linux only                                                   |
| **Orchestrator** | systemd (required dependency)                                |
| **Daemon**       | Long-running systemd service                                 |
| **CLI**          | Click-based commands for configuration and manual operations |
| **Scheduling**   | systemd timers for periodic checks                           |
| **BASH Scripts** | Managed and executed via systemd                             |

### Critical Rules

- **Never assume interactive execution**
- All output must be machine-parseable or properly logged
- Daemon mode must be silent except for logging
- CLI commands may produce human-readable output

---

## Resource Constraints

| Resource     | Expectation                                     |
| ------------ | ----------------------------------------------- |
| **CPU**      | Minimal baseline, burst-only during checks      |
| **Memory**   | < 50MB typical usage                            |
| **Disk I/O** | Read-only except logs and config cache          |
| **Network**  | WebSocket to backend; graceful timeout handling |

### Network Behavior

- Configurable connection timeouts
- Automatic reconnection with exponential backoff
- Fail gracefully on transient network issues
- Log all connection state changes

---

## Failure Philosophy

### Fail-Fast Scenarios (Fatal Errors)

- Invalid or missing configuration
- Invalid authentication credentials
- Missing systemd (required dependency)
- Corrupt persistent state

### Fail-Soft Scenarios (Log and Retry)

- Transient network failures
- Backend temporarily unavailable
- Individual check failures

### Logging Requirements

| Event Type        | Action                                   |
| ----------------- | ---------------------------------------- |
| Status changes    | Always log                               |
| Connection events | Always log                               |
| Check results     | Log on failure, configurable for success |
| Retries           | Log with attempt count                   |
| Fatal errors      | Log and exit with non-zero code          |

---

## Security & Isolation

### Allowed Access

- Backend API tokens (stored securely, e.g., systemd credentials)
- Local service check scripts
- System status information (read-only)

### Must Never

- Store raw passwords or secrets in logs
- Execute arbitrary remote commands
- Mutate remote state beyond status reporting
- Cache sensitive backend responses

### Trust Model

- Agent authenticates to backend with token
- Agent cannot modify backend configuration
- Agent is semi-trusted (limited permissions)

---

## Update Mechanism

### Current State

- **Update via reinstall** (manual)
- No auto-update functionality

### Rules

- Auto-update is **not implemented** and **forbidden until explicitly designed**
- Version checking may be added in future (read-only)
- Any update mechanism requires human approval

---

## Non-Negotiables

These technologies and patterns **must not be replaced** without explicit architectural approval:

| Category        | Requirement      |
| --------------- | ---------------- |
| Language        | Python 3.12+     |
| CLI Framework   | Click            |
| Real-time       | WebSocket client |
| Orchestration   | systemd          |
| Target OS       | Linux only       |
| Package Manager | Poetry           |

---

## Forbidden Patterns

AI agents **must not introduce** the following:

| Pattern                            | Reason                                |
| ---------------------------------- | ------------------------------------- |
| Background threads                 | Use systemd timers instead            |
| `eval()` or `exec()`               | Security risk, unpredictable behavior |
| Dynamic code execution             | Must be deterministic                 |
| Auto-updating behavior             | Not designed, security concern        |
| Cross-platform abstractions        | Linux/systemd only                    |
| Interactive prompts in daemon mode | Must run unattended                   |
| Excessive dependencies             | Minimize attack surface               |
| Silent error recovery              | All failures must be logged           |

---

## Change Discipline

| Action                         | Allowed Freely | Requires Approval | Forbidden |
| ------------------------------ | :------------: | :---------------: | :-------: |
| Add new check type             |       ✅       |                   |           |
| Modify logging format          |       ✅       |                   |           |
| Add new CLI command            |       ✅       |                   |           |
| Add configuration option       |       ✅       |                   |           |
| Change WebSocket protocol      |                |        ✅         |           |
| Add OS dependencies            |                |        ✅         |           |
| Add network endpoints          |                |        ✅         |           |
| Implement auto-update          |                |        ✅         |           |
| Remove systemd dependency      |                |                   |    ❌     |
| Add Windows/macOS support      |                |                   |    ❌     |
| Add interactive daemon prompts |                |                   |    ❌     |

---

## Commit Message Format

```
type(scope): short description

Optional extended body:
- Explain why, not just what
- Reference related issues if applicable
```

**Types**: `feat`, `fix`, `chore`, `docs`, `refactor`, `test`, `perf`  
**Scopes**: `daemon`, `cli`, `checks`, `websocket`, `config`, `systemd`

---

## Code Philosophy

> **Opt for boring, deterministic code.**

- Predictability over cleverness
- Explicit over implicit
- Log everything meaningful
- Fail loudly, recover gracefully
- Minimal dependencies

---

## Explicit Non-Goals

The following are **not responsibilities** of this repository:

- Storing historical status data (that's `ssi-backend`)
- Displaying status to users (that's `ssi-client-mobile`)
- Running on non-Linux systems
- Self-healing or auto-recovery beyond simple retries
- Complex decision logic about service state
