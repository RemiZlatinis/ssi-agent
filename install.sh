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
SERVICE_NAME="ssi-agent"
SERVICE_USER="ssi-agent"
INSTALL_DIR="/opt/ssi-agent"
SERVICE_SCRIPTS_DIR="$INSTALL_DIR/.installed-service-scripts"
CONFIG_DIR="/etc/ssi-agent"
LOG_DIR="/var/log/ssi-agent"
BACKEND_URL=${BACKEND_URL:-"https://api.service-status-indicator.com/"}

# Determine admin group for permissions
if [ -f /etc/redhat-release ] || [ -f /etc/arch-release ]; then
    ADMIN_GROUP="wheel"
else
    # Default to sudo for Debian-based and others
    ADMIN_GROUP="sudo"
fi

# Verify admin group exists, fallback if necessary
if ! getent group "$ADMIN_GROUP" >/dev/null; then
    if getent group "sudo" >/dev/null; then
        ADMIN_GROUP="sudo"
    elif getent group "wheel" >/dev/null; then
        ADMIN_GROUP="wheel"
    fi
fi

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

    # Check Python version (minimum 3.12)
    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    if ! python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)'; then
        print_error "Python 3.12 or higher is required. Found: Python $PYTHON_VERSION"
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

    # Check for acl tools
    if ! command -v setfacl &> /dev/null; then
        print_error "setfacl is required but not found"
        print_error "Please install it first (e.g., 'sudo apt install acl')"
        exit 1
    fi

    print_status "System requirements check passed ✓"
}

create_user() {
    if ! id "$SERVICE_USER" &>/dev/null; then
        print_status "Creating system user: $SERVICE_USER"
        useradd --system --shell /bin/false --home-dir "$INSTALL_DIR" --create-home "$SERVICE_USER"
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
    chown "$SERVICE_USER:$SERVICE_USER" "$CONFIG_DIR"
    chmod 755 "$SERVICE_SCRIPTS_DIR"
    chmod 755 "$LOG_DIR"
    chmod 755 "$CONFIG_DIR" # Owner rwx, group rx, other rx

    # Grant admin group write access to the config directory using ACLs
    # This allows admin users to run 'ssi register' without 'sudo'
    setfacl -m g:"$ADMIN_GROUP":rwx "$CONFIG_DIR"
}

create_virtual_environment() {
    print_status "Setting up Python virtual environment..."

    if [[ ! -d "$INSTALL_DIR/venv" ]]; then
        print_status "Creating new virtual environment..."
        python3 -m venv "$INSTALL_DIR/venv"
    else
        print_status "Virtual environment found. Updating if necessary."
    fi

    # Define path to venv pip for clarity and to avoid sourcing the activate script
    VENV_PIP="$INSTALL_DIR/venv/bin/pip"

    print_status "Upgrading pip in virtual environment..."
    "$VENV_PIP" install --upgrade pip

    print_status "Installing/updating the agent and its dependencies..."
    # Use --upgrade to ensure the package is reinstalled if source code has changed
    "$VENV_PIP" install --upgrade .

    # Ensure ownership is correct on every run
    # Set group to ADMIN_GROUP and restrict perms so only owner/group can execute
    chown -R "$SERVICE_USER:$ADMIN_GROUP" "$INSTALL_DIR/venv"
    chmod -R u=rwX,g=rX,o= "$INSTALL_DIR/venv"

    # Make it Editable install if EDITABLE_INSTALL is 1 (True)
    if [[ "${EDITABLE_INSTALL:-0}" == 1 ]]; then
        print_status "Installing agent in editable mode (DEVELOPMENT MODE)..."
        "$VENV_PIP" install -e .
    fi
}

create_symlink() {
    print_status "Creating symlink for ssi-agent CLI..."
    ln -sf "$INSTALL_DIR/venv/bin/ssi-agent" "/usr/local/bin/ssi"
}

install_service_file() {
    print_status "Installing systemd service file..."

    SSI_AGENT_SERVICE_UNIT="$INSTALL_DIR/deploy/ssi-agent.service"
    TARGET="/etc/systemd/system/"
    cp "$SSI_AGENT_SERVICE_UNIT" "$TARGET"
}

setup_service() {
    print_status "Setting up systemd service..."

    systemctl daemon-reload
    systemctl enable "$SERVICE_NAME"
    systemctl restart "$SERVICE_NAME"

    if [ $? -eq 0 ]; then
        print_status "Daemon started successfully."
    else
        print_error "Failed to start daemon. Check logs for details: journalctl -u $SERVICE_NAME"
    fi
}

install_logrotate() {
    print_status "Installing logrotate configuration..."

    LOGROTATE_FILE="$INSTALL_DIR/deploy/logrotate.conf"
    TARGET="/etc/logrotate.d/"
    cp "$LOGROTATE_FILE" "$TARGET"
}

create_config() {
    print_status "Checking for configuration file..."

    if [[ ! -f "$CONFIG_DIR/config.json" ]]; then
        print_status "No configuration file found. Creating default."
        cat > "$CONFIG_DIR/config.json" << EOF
{
    "backend_url": "$BACKEND_URL",
    "log_level": "INFO",
    "log_dir": "$LOG_DIR",
    "config_dir": "$CONFIG_DIR"
}
EOF
    else
        print_status "Existing configuration file found. Settings will be preserved."
    fi

    chown "$SERVICE_USER:$SERVICE_USER" "$CONFIG_DIR/config.json"
    chmod 644 "$CONFIG_DIR/config.json" # Owner rw, group r, other r

    # Grant/update admin group write access to the config file using ACLs
    # This allows admin users to run 'ssi register' without 'sudo'
    setfacl -m g:"$ADMIN_GROUP":rw- "$CONFIG_DIR/config.json"
}

cleanup() {
    print_status "Installation completed successfully!"
    echo ""
    echo "Next steps:"
    echo "1. Register the agent: ssi register <agent-key>"
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
    else
        print_status "Service is not running"
    fi

    if systemctl is-enabled --quiet "$SERVICE_NAME"; then
        print_status "Disabling service..."
        systemctl disable "$SERVICE_NAME"
    else
        print_status "Service is not enabled"
    fi

    # Remove systemd service file
    if [[ -f "/etc/systemd/system/$SERVICE_NAME.service" ]]; then
        print_status "Removing systemd service file..."
        rm -f "/etc/systemd/system/$SERVICE_NAME.service"
        systemctl daemon-reload
    else
        print_status "Systemd service file not found, skipping"
    fi

    # Remove symlink
    if [[ -L "/usr/local/bin/ssi" ]]; then
        print_warning "Removing ssi-agent CLI symlink..."
        rm -f "/usr/local/bin/ssi"
    else
        print_status "ssi-agent CLI symlink not found, skipping"
    fi

    # Remove virtual environment
    if [[ -d "$INSTALL_DIR/venv" ]]; then
        print_warning "Removing virtual environment..."
        rm -rf "$INSTALL_DIR/venv"
    else
        print_status "Virtual environment not found, skipping"
    fi

    # Remove application directory
    if [[ -d "$INSTALL_DIR" ]]; then
        print_warning "Removing application directory..."
        rm -rf "$INSTALL_DIR"
    else
        print_status "Application directory not found, skipping"
    fi

    # Remove configuration directory
    if [[ -d "$CONFIG_DIR" ]]; then
        print_warning "Removing configuration directory..."
        rm -rf "$CONFIG_DIR"
    else
        print_status "Configuration directory not found, skipping"
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
    else
        print_status "Log directory not found, skipping"
    fi

    # Remove system user (only if no other files owned by it)
    if id "$SERVICE_USER" &>/dev/null; then
        print_status "Removing system user..."
        userdel "$SERVICE_USER"
    else
        print_status "System user not found, skipping"
    fi

    print_status "Uninstallation completed!"
    echo ""
    echo "The following may have been removed:"
    echo "  - Systemd service: $SERVICE_NAME"
    echo "  - Application directory: $INSTALL_DIR"
    echo "  - Configurations: $CONFIG_DIR"
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
        create_symlink
        install_service_file
        install_logrotate
        create_config
        setup_service
        cleanup
    fi
}

# Run main function
main "$@"
