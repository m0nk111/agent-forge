#!/bin/bash
# Uninstallation script for Agent-Forge systemd service
# Usage: sudo ./scripts/uninstall-service.sh

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
ENV_FILE="/etc/default/agent-forge"

echo -e "${RED}=== Agent-Forge Service Uninstallation ===${NC}"
echo

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Error: This script must be run as root${NC}"
    echo "Usage: sudo ./scripts/uninstall-service.sh"
    exit 1
fi

# Confirm uninstallation
echo -e "${YELLOW}This will remove:${NC}"
echo "  - Systemd service"
echo "  - Installation directory: $INSTALL_DIR"
echo "  - Service user: $SERVICE_USER"
echo "  - Environment file: $ENV_FILE"
echo
read -p "Are you sure you want to uninstall? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "Uninstallation cancelled"
    exit 0
fi

echo

# Step 1: Stop service
echo -e "${YELLOW}Step 1: Stopping service...${NC}"
if systemctl is-active --quiet agent-forge; then
    systemctl stop agent-forge
    echo "Service stopped"
else
    echo "Service not running"
fi

# Step 2: Disable service
echo -e "${YELLOW}Step 2: Disabling service...${NC}"
if systemctl is-enabled --quiet agent-forge 2>/dev/null; then
    systemctl disable agent-forge
    echo "Service disabled"
else
    echo "Service not enabled"
fi

# Step 3: Remove systemd unit file
echo -e "${YELLOW}Step 3: Removing systemd unit file...${NC}"
if [ -f "$SERVICE_FILE" ]; then
    rm "$SERVICE_FILE"
    echo "Removed $SERVICE_FILE"
else
    echo "Service file not found"
fi

# Step 4: Reload systemd
echo -e "${YELLOW}Step 4: Reloading systemd...${NC}"
systemctl daemon-reload
systemctl reset-failed 2>/dev/null || true
echo "Systemd reloaded"

# Step 5: Backup and remove installation directory
echo -e "${YELLOW}Step 5: Removing installation directory...${NC}"
if [ -d "$INSTALL_DIR" ]; then
    # Ask if user wants to backup data
    read -p "Backup data and config before removal? (yes/no): " BACKUP
    
    if [ "$BACKUP" = "yes" ]; then
        BACKUP_DIR="/tmp/agent-forge-backup-$(date +%Y%m%d-%H%M%S)"
        mkdir -p "$BACKUP_DIR"
        
        # Backup important directories
        [ -d "$INSTALL_DIR/data" ] && cp -r "$INSTALL_DIR/data" "$BACKUP_DIR/"
        [ -d "$INSTALL_DIR/config" ] && cp -r "$INSTALL_DIR/config" "$BACKUP_DIR/"
        [ -d "$INSTALL_DIR/logs" ] && cp -r "$INSTALL_DIR/logs" "$BACKUP_DIR/"
        
        echo "Backup created: $BACKUP_DIR"
    fi
    
    # Remove installation directory
    rm -rf "$INSTALL_DIR"
    echo "Removed $INSTALL_DIR"
else
    echo "Installation directory not found"
fi

# Step 6: Remove environment file
echo -e "${YELLOW}Step 6: Removing environment file...${NC}"
if [ -f "$ENV_FILE" ]; then
    rm "$ENV_FILE"
    echo "Removed $ENV_FILE"
else
    echo "Environment file not found"
fi

# Step 7: Remove service user
echo -e "${YELLOW}Step 7: Removing service user...${NC}"
read -p "Remove service user '$SERVICE_USER'? (yes/no): " REMOVE_USER

if [ "$REMOVE_USER" = "yes" ]; then
    if id "$SERVICE_USER" &>/dev/null; then
        userdel "$SERVICE_USER" 2>/dev/null || true
        # Also remove group if it exists
        groupdel "$SERVICE_GROUP" 2>/dev/null || true
        echo "Removed user: $SERVICE_USER"
    else
        echo "User not found"
    fi
else
    echo "Skipped user removal"
fi

# Uninstallation complete
echo
echo -e "${GREEN}=== Uninstallation Complete! ===${NC}"
echo

if [ "$BACKUP" = "yes" ]; then
    echo -e "${YELLOW}Backup location: $BACKUP_DIR${NC}"
    echo "You can restore from this backup or delete it when no longer needed"
fi

echo
echo "Agent-Forge has been removed from your system"
