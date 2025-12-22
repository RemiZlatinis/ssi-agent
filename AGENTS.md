# SSI Agent (ssi-agent repository)

> **This project is the Agent component of the SSI system.**

## Overview _(of the whole SSI system)_

_Full title & subtitle: Service Status Indicator (SSI) - Simplified Script-Driven Monitoring System_

The Service Status Indicator (SSI) is a monitoring system designed to decouple the monitoring logic of the needed infrastructure to communicate the information.

In practice, SSI allows power-users and system admins to monitor anything using BASH scripts. Those called **service scripts**, as long as they follow the SSI conventions and the standardized output, the system handles the rest. _(Capturing the outcome, sending, and notifying the end-user through the backend in real-time)_

The SSI is a three-piece puzzle. The _Backend_, _Agent_, and _Frontend_ are the key components. The _**Agent**_ is the piece of the software installed on any Linux system with systemd, and is where the _service scripts_ act. It’s composed of two parts, the _daemon_ and the _CLI_. The _CLI_ validates and configures the Service and Timer units of systemd needed for the added _service scripts_ to run. The _service scripts_ are producing standardized logs where the _daemon_ collects and sends them to the _Backend_ in real-time. The _Frontend_ then receives the information through push notifications or maintains a real-time communication channel with the _Backend_.

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

## Development commands

_Note: During the development and testing the ssi-agent should run in a container with systemd init to simulate the environment and eliminate system inconsistencies._

- Build the development container with `podman build -t ssi-dev .`
- Run the development container with `podman run -d --name ssi-agent-dev --replace --systemd=always -v "${PWD}:/opt/ssi-agent" ssi-dev`

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
