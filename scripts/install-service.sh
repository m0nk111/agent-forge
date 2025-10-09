#!/bin/bash
# Installation script for Agent-Forge systemd service
# Usage: sudo ./scripts/install-service.sh

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
SERVICE_NAME="agent-forge"
SERVICE_USER="agent-forge"
SERVICE_GROUP="agent-forge"
INSTALL_DIR="/opt/agent-forge"
SERVICE_FILE="/etc/systemd/system/agent-forge.service"

echo -e "${GREEN}=== Agent-Forge Service Installation ===${NC}"
echo

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Error: This script must be run as root${NC}"
    echo "Usage: sudo ./scripts/install-service.sh"
    exit 1
fi

# Get the script directory (where agent-forge is located)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
echo "Source directory: $SCRIPT_DIR"

# Step 1: Create service user and group
echo -e "${YELLOW}Step 1: Creating service user and group...${NC}"
if id "$SERVICE_USER" &>/dev/null; then
    echo "User $SERVICE_USER already exists"
else
    useradd --system --no-create-home --shell /bin/false "$SERVICE_USER"
    echo "Created system user: $SERVICE_USER"
fi

# Step 2: Create installation directory
echo -e "${YELLOW}Step 2: Creating installation directory...${NC}"
mkdir -p "$INSTALL_DIR"/{logs,data,config,venv}
echo "Created directories in $INSTALL_DIR"

# Step 3: Copy files
echo -e "${YELLOW}Step 3: Copying application files...${NC}"
rsync -av --exclude='venv' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.git' \
    --exclude='logs/*' \
    --exclude='*.log' \
    "$SCRIPT_DIR/" "$INSTALL_DIR/"
echo "Files copied to $INSTALL_DIR"

# Step 4: Create Python virtual environment
echo -e "${YELLOW}Step 4: Setting up Python virtual environment...${NC}"
python3 -m venv "$INSTALL_DIR/venv"
source "$INSTALL_DIR/venv/bin/activate"

# Install dependencies
if [ -f "$INSTALL_DIR/requirements.txt" ]; then
    echo "Installing Python dependencies..."
    pip install --upgrade pip
    pip install -r "$INSTALL_DIR/requirements.txt"
else
    echo -e "${YELLOW}Warning: requirements.txt not found, installing minimal dependencies${NC}"
    pip install systemd-python
fi

deactivate

# Step 5: Set ownership and permissions
echo -e "${YELLOW}Step 5: Setting ownership and permissions...${NC}"
chown -R "$SERVICE_USER:$SERVICE_GROUP" "$INSTALL_DIR"
chmod -R 755 "$INSTALL_DIR"
chmod 775 "$INSTALL_DIR"/{logs,data,config}  # Writable directories

# Step 6: Install systemd service
echo -e "${YELLOW}Step 6: Installing systemd service...${NC}"
if [ -f "$INSTALL_DIR/systemd/agent-forge.service" ]; then
    cp "$INSTALL_DIR/systemd/agent-forge.service" "$SERVICE_FILE"
    echo "Installed systemd unit file: $SERVICE_FILE"
else
    echo -e "${RED}Error: systemd/agent-forge.service not found${NC}"
    exit 1
fi

# Step 7: Create environment file
echo -e "${YELLOW}Step 7: Creating environment file...${NC}"
cat > "/etc/default/agent-forge" <<EOF
# Agent-Forge environment variables
# Uncomment and configure as needed

# GitHub credentials (required)
# BOT_GITHUB_TOKEN=your_token_here

# Service configuration
# LOG_LEVEL=INFO
# POLLING_INTERVAL=300
# WEB_UI_PORT=8080
# MONITORING_PORT=8765

# Resource limits
# MAX_CONCURRENT_ISSUES=3
EOF

chmod 600 "/etc/default/agent-forge"
echo "Created environment file: /etc/default/agent-forge"
echo -e "${YELLOW}⚠️  Edit /etc/default/agent-forge to add GitHub token!${NC}"

# Step 8: Reload systemd and enable service
echo -e "${YELLOW}Step 8: Configuring systemd...${NC}"
systemctl daemon-reload
echo "Systemd daemon reloaded"

# Step 9: Enable service (but don't start yet)
echo -e "${YELLOW}Step 9: Enabling service...${NC}"
systemctl enable agent-forge.service
echo "Service enabled for auto-start on boot"

# Installation complete
echo
echo -e "${GREEN}=== Installation Complete! ===${NC}"
echo
echo "Next steps:"
echo "1. Edit /etc/default/agent-forge and add your GitHub token"
echo "2. Configure repositories in $INSTALL_DIR/config/polling_config.yaml"
echo "3. Start the service:"
echo "   ${GREEN}sudo systemctl start agent-forge${NC}"
echo
echo "Useful commands:"
echo "  ${GREEN}sudo systemctl status agent-forge${NC}    # Check service status"
echo "  ${GREEN}sudo systemctl stop agent-forge${NC}      # Stop service"
echo "  ${GREEN}sudo systemctl restart agent-forge${NC}   # Restart service"
echo "  ${GREEN}sudo journalctl -u agent-forge -f --no-pager${NC}    # View logs (follow)"
echo "  ${GREEN}sudo journalctl -u agent-forge --since today --no-pager${NC}  # Today's logs"
echo
echo -e "${YELLOW}⚠️  Don't forget to configure your GitHub token!${NC}"
