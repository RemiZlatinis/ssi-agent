#!/bin/bash

# Service Status Indicator Agent Installation Script
# This script installs the agent and sets up systemd service

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
SERVICE_NAME="service-status-indicator-agent"
SERVICE_USER="service-status-indicator"
SERVICE_SCRIPTS_DIR="/opt/service-status-indicator"
CONFIG_DIR="/etc/service-status-indicator"
LOG_DIR="/var/log/service-status-indicator"

# Functions
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_root() {
    if [[ $EUID -ne 0 ]]; then
        print_error "This script must be run as root (sudo)"
        exit 1
    fi
}

create_user() {
    if ! id "$SERVICE_USER" &>/dev/null; then
        print_status "Creating system user: $SERVICE_USER"
        useradd --system --shell /bin/false --home-dir "$SERVICE_SCRIPTS_DIR" --create-home "$SERVICE_USER"
    else
        print_status "User $SERVICE_USER already exists"
    fi
}

create_directories() {
    print_status "Creating directories..."

    mkdir -p "$SERVICE_SCRIPTS_DIR"
    mkdir -p "$CONFIG_DIR"
    mkdir -p "$LOG_DIR"

    # Create bin directory for entry point scripts
    mkdir -p "$SERVICE_SCRIPTS_DIR/bin"

    chown -R "$SERVICE_USER:$SERVICE_USER" "$SERVICE_SCRIPTS_DIR"
    chown "$SERVICE_USER:$SERVICE_USER" "$LOG_DIR"
    chown "$SERVICE_USER:$SERVICE_USER" "$CONFIG_DIR"
    chmod 755 "$SERVICE_SCRIPTS_DIR"
    chmod 755 "$LOG_DIR"
    chmod 755 "$CONFIG_DIR"
}

create_virtual_environment() {
    print_status "Creating Python virtual environment..."

    # Create virtual environment
    python3 -m venv "$SERVICE_SCRIPTS_DIR/venv"

    # Activate and install dependencies
    source "$SERVICE_SCRIPTS_DIR/venv/bin/activate"

    # Install the package and its dependencies
    pip install --upgrade pip
    pip install websockets watchdog click pydantic requests

    # Install the package itself (assuming it's available)
    # pip install /path/to/package.whl or from PyPI when published

    deactivate

    # Set ownership of virtual environment
    chown -R "$SERVICE_USER:$SERVICE_USER" "$SERVICE_SCRIPTS_DIR/venv"
}

install_service_file() {
    print_status "Installing systemd service file..."

    # Get the path to the installed package
    PACKAGE_PATH=$(python3 -c "import src; print(src.__file__.replace('__init__.py', ''))")
    TEMPLATE_PATH="$PACKAGE_PATH/templates/agent.service"

    if [[ ! -f "$TEMPLATE_PATH" ]]; then
        print_error "Service template not found at: $TEMPLATE_PATH"
        exit 1
    fi

    # Copy and customize service file
    cp "$TEMPLATE_PATH" "/etc/systemd/system/$SERVICE_NAME.service"

    # Update paths in service file if needed
    sed -i "s|User=.*|User=$SERVICE_USER|" "/etc/systemd/system/$SERVICE_NAME.service"
    sed -i "s|Group=.*|Group=$SERVICE_USER|" "/etc/systemd/system/$SERVICE_NAME.service"
    sed -i "s|ExecStart=.*|ExecStart=$SERVICE_SCRIPTS_DIR/venv/bin/service-status-indicator-daemon|" "/etc/systemd/system/$SERVICE_NAME.service"
}

setup_service() {
    print_status "Setting up systemd service..."

    systemctl daemon-reload
    systemctl enable "$SERVICE_NAME"
    systemctl start "$SERVICE_NAME"

    print_status "Service status:"
    systemctl status "$SERVICE_NAME" --no-pager -l
}

create_config() {
    print_status "Creating default configuration..."

    cat > "$CONFIG_DIR/config.json" << EOF
{
    "websocket_uri": "ws://localhost:5000",
    "log_level": "INFO",
    "log_dir": "$LOG_DIR",
    "config_dir": "$CONFIG_DIR"
}
EOF

    chown "$SERVICE_USER:$SERVICE_USER" "$CONFIG_DIR/config.json"
    chmod 644 "$CONFIG_DIR/config.json"
}

cleanup() {
    print_status "Installation completed successfully!"
    echo ""
    echo "Next steps:"
    echo "1. Register the agent: service-status-indicator register <agent-key>"
    echo "2. Check service status: systemctl status $SERVICE_NAME"
    echo "3. View logs: journalctl -u $SERVICE_NAME -f"
    echo ""
    echo "Configuration file: $CONFIG_DIR/config.json"
    echo "Log directory: $LOG_DIR"
}

main() {
    print_status "Starting Service Status Indicator Agent installation..."

    check_root
    create_user
    create_directories
    create_virtual_environment
    install_service_file
    create_config
    setup_service
    cleanup
}

# Run main function
main "$@"
