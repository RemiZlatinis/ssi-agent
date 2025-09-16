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

check_system_requirements() {
    print_status "Checking system requirements..."

    # Check if running on Linux
    if [[ "$OSTYPE" != "linux-gnu"* ]]; then
        print_error "This installer is designed for Linux systems only"
        exit 1
    fi

    # Check for systemd
    if ! command -v systemctl &> /dev/null; then
        print_error "systemd is required but not found. This installer requires a systemd-based Linux distribution."
        exit 1
    fi

    # Check if systemd is the init system
    if [[ ! -d /run/systemd/system ]]; then
        print_error "systemd does not appear to be the active init system"
        exit 1
    fi

    # Check for Python 3
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is required but not found"
        print_error "Please install Python 3 first (apt install python3)"
        exit 1
    fi

    # Check Python version (minimum 3.9)
    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    if ! python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)'; then
        print_error "Python 3.9 or higher is required. Found: Python $PYTHON_VERSION"
        exit 1
    fi

    # Check for python3-venv
    if ! python3 -c 'import venv' &> /dev/null; then
        print_error "python3-venv is required but not available"
        print_error "Please install it first (apt install python3-venv)"
        exit 1
    fi

    # Check for pip
    if ! command -v pip3 &> /dev/null && ! python3 -m pip --version &> /dev/null; then
        print_error "pip is required but not found"
        print_error "Please install pip first (apt install python3-pip)"
        exit 1
    fi

    # Check for basic build tools (for potential native extensions)
    if ! command -v gcc &> /dev/null; then
        print_warning "gcc not found - some Python packages may fail to install"
        print_warning "Consider installing build-essential: apt install build-essential"
    fi

    print_status "System requirements check passed ✓"
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

uninstall_agent() {
    print_status "Starting Service Status Indicator Agent uninstallation..."

    # Stop and disable service first
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        print_status "Stopping service..."
        systemctl stop "$SERVICE_NAME"
    fi

    if systemctl is-enabled --quiet "$SERVICE_NAME"; then
        print_status "Disabling service..."
        systemctl disable "$SERVICE_NAME"
    fi

    # Remove systemd service file
    if [[ -f "/etc/systemd/system/$SERVICE_NAME.service" ]]; then
        print_status "Removing systemd service file..."
        rm -f "/etc/systemd/system/$SERVICE_NAME.service"
        systemctl daemon-reload
    fi

    # Remove virtual environment
    if [[ -d "$SERVICE_SCRIPTS_DIR/venv" ]]; then
        print_warning "Removing virtual environment..."
        rm -rf "$SERVICE_SCRIPTS_DIR/venv"
    fi

    # Remove application directory
    if [[ -d "$SERVICE_SCRIPTS_DIR" ]]; then
        print_warning "Removing application directory..."
        rm -rf "$SERVICE_SCRIPTS_DIR"
    fi

    # Remove configuration directory
    if [[ -d "$CONFIG_DIR" ]]; then
        print_warning "Removing configuration directory..."
        rm -rf "$CONFIG_DIR"
    fi

    # Ask about log directory (contains user data)
    if [[ -d "$LOG_DIR" ]]; then
        echo ""
        read -p "Remove log directory ($LOG_DIR) containing service logs? [y/N]: " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            print_warning "Removing log directory..."
            rm -rf "$LOG_DIR"
        else
            print_status "Keeping log directory (you can remove it manually later)"
        fi
    fi

    # Remove system user (only if no other files owned by it)
    if id "$SERVICE_USER" &>/dev/null; then
        # Check if user owns any other files
        USER_FILES=$(find / -user "$SERVICE_USER" 2>/dev/null | wc -l)
        if [[ $USER_FILES -le 1 ]]; then  # Only the user's home directory
            print_status "Removing system user..."
            userdel "$SERVICE_USER"
        else
            print_warning "Keeping system user (other files still owned by it)"
        fi
    fi

    print_status "Uninstallation completed!"
    echo ""
    echo "The following may have been removed:"
    echo "  - Systemd service: $SERVICE_NAME"
    echo "  - Application directory: $SERVICE_SCRIPTS_DIR"
    echo "  - Configuration: $CONFIG_DIR"
    echo "  - System user: $SERVICE_USER"
    echo "  - Virtual environment and dependencies"
    echo ""
    echo "Note: Log files may still exist in $LOG_DIR if you chose to keep them"
}

main() {
    # Parse command line arguments
    ACTION="install"

    while [[ $# -gt 0 ]]; do
        case $1 in
            --remove|--uninstall)
                ACTION="uninstall"
                shift
                ;;
            --help|-h)
                echo "Service Status Indicator Agent Installer"
                echo ""
                echo "Usage:"
                echo "  $0                    # Install the agent"
                echo "  $0 --remove          # Uninstall the agent"
                echo "  $0 --uninstall       # Uninstall the agent"
                echo "  $0 --help            # Show this help"
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                echo "Use --help for usage information"
                exit 1
                ;;
        esac
    done

    if [[ "$ACTION" == "uninstall" ]]; then
        check_root
        uninstall_agent
    else
        print_status "Starting Service Status Indicator Agent installation..."

        check_root
        check_system_requirements
        create_user
        create_directories
        create_virtual_environment
        install_service_file
        create_config
        setup_service
        cleanup
    fi
}

# Run main function
main "$@"
