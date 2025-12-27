# SSI Agent

> **Context for AI Agents**

> **Role**: You are an expert Python developer working on the **SSI Agent** component. This is the Linux daemon responsible for running service scripts and reporting status to the backend.

## 🧠 Project Overview

**Service Status Indicator (SSI)** is a monitoring ecosystem designed to decouple monitoring logic (BASH scripts) from communication infrastructure.

This repository (`ssi-agent`) contains the **Agent** component.

### 🌍 Global Architecture Context

_Essential context since this repo works as part of a distributed system._

The system flows data from the Edge (Servers/Agents) to the Core (Backend) and finally to the User (Mobile/Web Client).

**The Three-Piece Puzzle:**

1.  **The Agent (Worker)**:
    - **This Repository**. Installed on Linux/Systemd.
    - Executes service scripts, captures standardized CSV logs, and streams them to the Backend.
2.  **The Backend (Brain)**:
    - **Closed Source**.
    - Central hub that receives updates from Agents and pushes real-time notifications to Clients.
3.  **The Client (Status Board)**:
    - Mobile/Web Interface (React Native).
    - Connects to Backend to display status.

### Core Responsibilities (Agent)

- **Execution**: Run BASH service scripts via `systemd` timers.
- **Observation**: Watch log files for standardized CSV output lines.
- **Reporting**: Stream status updates to the `ssi-backend` via WebSocket.
- **Management**: Provide a CLI (`ssi`) for users to add/remove services.

## 🛠️ Tech Stack & Environment

| Category          | Technology                   | Constraint                |
| :---------------- | :--------------------------- | :------------------------ |
| **Language**      | Python 3.12+                 | **Strict** (use `poetry`) |
| **CLI Framework** | `click`                      | **Strict**                |
| **Orchestrator**  | `systemd` (Service & Timers) | **Strict** (Linux only)   |
| **Communication** | `websockets` (AsyncIO)       | **Strict**                |
| **OS Target**     | Linux (Systemd-based)        | **Strict**                |

## 🏗️ Architecture & Mental Models

The agent operates as a **bridge** between local BASH scripts and the remote Backend.

- **Service Scripts**: Simple BASH scripts that output standardized CSV logs. The agent _does not_ execute them directly; it configures `systemd` to run them.
- **The Daemon**: A background process (`src/agent.py`) that uses `watchdog` to tail log files. It is **event-driven** (file modified -> parse line -> send WebSocket message).
- **The CLI**: A separate synchronous tool (`src/cli.py`) that manipulates files in `/opt/ssi-agent` and generates systemd unit files.

## ⛔ Non-Negotiables & Constraints

You **MUST NOT** violate these rules:

1.  **Linux Only**: Do not add cross-platform abstractions (Windows/Mac). Tying to `systemd` is a feature, not a bug.
2.  **Unattended Operation**: The daemon must never prompt for user input. It runs in the background.
3.  **Deterministic**: The system must be predictable. No "AI magic" or self-healing logic beyond simple retries.

### Forbidden Patterns

- ❌ **Background Threads**: Use `asyncio` for I/O or `systemd` timers for scheduling. Avoid spawning `threading.Thread` unless strictly necessary for blocking I/O (like `watchdog`).
- ❌ **`eval()` / `exec()`**: Security risk.
- ❌ **Auto-Update**: The agent does not update itself.

## 📝 Code Style & Philosophy

- **Boring Code**: Clarity over cleverness. Explicit dependencies.
- **Robustness**: Fail fast on config errors, fail soft (retry) on network errors.
- **Logging**: Log everything meaningful to stdout/journald.

## 🔄 Development Workflow

> **CRITICAL**: Because this daemon interacts with `systemd`, it requires a specific environment. The way to develop is to use a container with systemd enabled with Podman.

### 🐳 Containerized Environment (Podman)

Use the provided `DevContainerfile` to spin up a systemd-enabled environment.

1.  **Build Image**:

    ```bash
    podman build -t ssi-dev .
    ```

2.  **Run Container**:

    ```bash
    # Mounts current directory to /opt/ssi-agent
    podman run -d --name ssi-agent-dev \
      --replace \
      --systemd=always \
      -v "${PWD}:/opt/ssi-agent" \
      ssi-dev
    ```

3.  **Access Shell**:
    ```bash
    podman exec -it ssi-agent-dev bash
    ```

### 🧪 common tasks (Inside Container)

- **Restart Service** (after code changes):
  ```bash
  systemctl restart ssi-agent
  ```
- **View Logs**:
  ```bash
  journalctl -u ssi-agent -f
  ```
- **Run Internal Tests**:
  ```bash
  poetry run pytest
  ```

### Commit Guidelines

**Message Format:**

```
type(scope): short description

Optional extended body:
- Explain why, not just what
- Reference related issues if applicable
```

**Types**: `feat`, `fix`, `chore`, `docs`, `refactor`, `test`, `perf`  
**Scopes**: `daemon`, `cli`, `checks`, `websocket`, `config`, `systemd`

<!--
TODO(ssi-agent): Update these scopes after the src/ module refactor is completed. Current scope mapping assumes legacy module layout.
-->
