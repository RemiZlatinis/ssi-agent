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

1. **The Agent (Worker)**:
   - **This Repository**. Installed on Linux/Systemd.
   - Executes service scripts, captures standardized CSV logs, and streams them to the Backend.
2. **The Backend (Brain)**:
   - **Closed Source**.
   - Central hub that receives updates from Agents and pushes real-time notifications to Clients.
3. **The Client (Status Board)**:
   - Mobile/Web Interface (React Native).
   - Connects to Backend to display status.

### Core Responsibilities (Agent)

- **Execution**: Run BASH service scripts via `systemd` timers.
- **Observation**: Watch log files for standardized CSV output lines.
- **Reporting**: Stream status updates to the `ssi-backend` via WebSocket.
- **Management**: Provide a CLI (`ssi`) for users to add/remove services.

## 🛠️ Tech Stack & Environment

| Category          | Technology                   | Constraint                |
| :---------------- | :--------------------------- | :------------------------ | ---------------------------------- |
| **Language**      | Python 3.12+                 | **Strict** (use `poetry`) |
| **CLI Framework** | `click`                      | **Strict**                |
| **File Watching** | `watchdog`                   | **Strict**                |
| **Orchestrator**  | `systemd` (Service & Timers) | **Strict** (Linux only)   |
| **Communication** | `websockets` (AsyncIO)       | **Strict**                |
| **OS Target**     | Linux (Systemd-based)        | **Strict**                | ## 🏗️ Architecture & Mental Models |

The agent operates as a **bridge** between local BASH scripts and the remote Backend.

- **Service Scripts**: Simple BASH scripts that output standardized CSV logs. The agent _does not_ execute them directly; it configures `systemd` to run them.
- **The Daemon**: A background process (`src/ssi_agent/daemon.py`) that uses `watchdog` to tail log files. It is **event-driven** (file modified -> parse line -> send WebSocket message).
- **The CLI**: A separate synchronous tool (`src/ssi_agent/cli/`) that manipulates files in `/opt/ssi-agent` and generates systemd unit files.

## ⛔ Non-Negotiables & Constraints

You **MUST NOT** violate these rules:

1. **Linux Only**: Do not add cross-platform abstractions (Windows/Mac). Tying to `systemd` is a feature, not a bug.
2. **Unattended Operation**: The daemon must never prompt for user input. It runs in the background.
3. **Deterministic**: The system must be predictable. No "AI magic" or self-healing logic beyond simple retries.

### Forbidden Patterns

- ❌ **Background Threads**: Use `asyncio` for I/O or `systemd` timers for scheduling. Avoid spawning `threading.Thread` unless strictly necessary for blocking I/O (like `watchdog`).
- ❌ **`eval()` / `exec()`**: Security risk.
- ❌ **Auto-Update**: The agent does not update itself.

## 📝 Code Style & Philosophy

- **Boring Code**: Clarity over cleverness. Explicit dependencies.
- **Robustness**: Fail fast on config errors, fail soft (retry) on network errors.
- **Logging**: Log everything meaningful to stdout/journald.

## 🔄 Development Workflow

> **CRITICAL**: Because this daemon interacts with `systemd`, it requires a specific environment. The recommended way to develop is to use a container with systemd enabled with Podman.

### Prerequisites

Before starting, ensure you have:

- **Python**: Version 3.12 or higher
- **Poetry**: For dependency management (`pip install poetry`)
- **Podman**: For containerized development (`podman --version` should work)
- **VS Code** (optional): For integrated development with Ruff formatter

### Step 1: Install Pre-Commit Hooks

Pre-commit hooks enforce code quality standards (Ruff, Mypy) **before committing**. This is non-negotiable.

**Installation:**

```bash
# On your local machine (outside container)
pip install pre-commit

# Initialize hooks for this repository
pre-commit install
```

**Verification:**

```bash
# Run all checks on all files to ensure setup is working
pre-commit run --all-files

# Expected output: All checks pass with no failures
```

If pre-commit fails, fix the reported issues, stage the changes, and run pre-commit again:

```bash
# After fixing issues
git add .
pre-commit run --all-files
```

**What happens on commit:**

Once installed, pre-commit will automatically run on any `git commit`:

```bash
git commit -m "feat(daemon): improve log parsing"

# Pre-commit checks run automatically:
# - Black/Ruff format check
# - Mypy type checking
# - Other linters

# If checks fail, fix issues and retry the commit
```

### Step 2: Configure VS Code (Recommended)

VS Code can enforce **the same standards as CI/CD** with proper configuration. This catches issues before pre-commit.

**Install Extensions:**

The workspace already includes `.vscode/extensions.json` with recommended extensions. Install:

1. [Pylance](https://marketplace.visualstudio.com/items?itemName=ms-python.vscode-pylance) — Type checking and IntelliSense
2. [Ruff](https://marketplace.visualstudio.com/items?itemName=charliermarsh.ruff) — Formatting and linting

VS Code will prompt you to install recommended extensions; accept the prompt.

**Workspace Settings (Pre-Configured):**

The `.vscode/settings.json` file is already configured with:

```json
{
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.organizeImports.ruff": "explicit",
      "source.fixAll.ruff": "explicit"
    }
  },
  "ruff.lineLength": 88,
  "ruff.lint.select": ["E", "F", "W", "I", "UP"]
}
```

This means:

- **Format on save** with Ruff (Black-compatible)
- **Auto-organize imports** when you save
- **Line length: 88 characters** (matches CI/CD)

**Important Note on Line Length:**

- Ruff's formatter only rewrites code **structurally** (indentation, spacing, quote style, etc.)
- Lines exceeding 88 characters are flagged as violations but require **manual refactoring**
- Use Ruff's auto-fix on save which handles many issues automatically
- For long lines: break them across multiple lines manually or use backslash continuation

### Step 3: Set Up Containerized Development

Because the daemon interacts with `systemd`, development requires a container with systemd enabled.

**Start the development container:**

```bash
podman compose up --build -d
```

This command will automatically:

- Build the development image with systemd enabled
- Install the agent in editable/development mode
- Set up systemd units (`ssi-agent.service`)
- Create the `ssi-agent` user and group
- Initialize log directories

**Access the container shell:**

```bash
podman exec -it ssi-agent-dev-1 bash
```

**Inside the container, interact with the CLI:**

```bash
ssi --help
ssi service add /opt/services/my-service.sh my-service-id
ssi service status
```

_Note: Wait a couple of seconds after `podman compose up` before accessing the container, as the `dev-installer` service needs time to run._

**Stop the development environment:**

```bash
# Just stop the container
podman compose down

# Or remove all data and start fresh
podman compose down --volumes
```

### Step 4: Verify the Setup is Working

Run these commands to verify all components are working correctly:

**Check pre-commit hooks:**

```bash
# Verify hooks are installed
pre-commit run --all-files

# Should output: All checks passed
```

**Check Ruff in VS Code:**

Open any `.py` file in VS Code. It should:

- Show type hints from Pylance
- Auto-format on save (Ruff)
- Show linting warnings/errors in the Problems panel

If issues don't appear, try:

1. Restarting VS Code
2. Running `pre-commit run --all-files` to see if there are errors
3. Checking `.vscode/settings.json` is present

**Check the containerized daemon:**

```bash
# Inside the container
systemctl status ssi-agent

# Should show: active (running)

# View live logs
journalctl -fu ssi-agent
```

**Test the CLI inside the container:**

```bash
# Inside the container
ssi --help
ssi service list
```

### Common Issues & Troubleshooting

**Pre-commit refuses to install:**

- Ensure Python 3.12+ is in your PATH
- Try: `python -m pip install --upgrade pre-commit`

**Ruff extension not formatting in VS Code:**

- Restart VS Code
- Verify `.vscode/settings.json` is present and readable
- Install the Ruff extension manually from the marketplace

**Container fails to start:**

- Ensure Podman is running: `podman --version`
- Check disk space: `df -h`
- Try: `podman compose down --volumes && podman compose up --build -d`

**Daemon not starting in container:**

- Check logs: `journalctl -u ssi-agent -n 50`
- Ensure ssi-agent user exists: `id ssi-agent` (inside container)
- Verify `/opt/ssi-agent` is mounted correctly

### 🧪 Common Tasks

#### Inside Container

- **Restart Service** (after changes on the daemon):

  ```bash
  systemctl restart ssi-agent
  ```

- **View the Daemon Logs**:

  ```bash
  ssi debug logs -f
  ```

- **View Logs for a Service Script**:

  ```bash
  tail -f /var/log/ssi-agent/service-name.log
  ```

#### Outside Container

- **View the Test Logs**:

  _If all the test are passed you will see the container `test-runner-1 exited with code 0`. If a test is failing and you need the details use the following:_

  ```bash
  podman compose up --build test-runner
  ```

### Commit Guidelines

**Message Format:**

```
type(scope): short description

Optional extended body:
- Explain why, not just what
- Reference related issues if applicable
```

**Types**: `feat`, `fix`, `chore`, `docs`, `refactor`, `test`, `perf`, `security`, `build`, `ci`, `style` etc.
**Scopes**: `daemon`, `cli`, `library`, `websocket`, `config`, `systemd` etc.
