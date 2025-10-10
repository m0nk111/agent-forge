#!/bin/bash
# Install Agent-Forge Polling Service as systemd service
#
# This script installs the polling service that monitors GitHub issues
# and automatically triggers the autonomous pipeline.
#
# Usage:
#   sudo ./scripts/install-polling-service.sh
#
# Author: Agent Forge
# Date: 2025-10-10

set -e

echo "🔧 Installing Agent-Forge Polling Service..."
echo "============================================"

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Please run as root (use sudo)"
    exit 1
fi

# Check if service file exists
if [ ! -f "systemd/agent-forge-polling.service" ]; then
    echo "❌ Service file not found: systemd/agent-forge-polling.service"
    exit 1
fi

# Stop existing service if running
if systemctl is-active --quiet agent-forge-polling.service; then
    echo "⏹️  Stopping existing polling service..."
    systemctl stop agent-forge-polling.service
fi

# Copy service file
echo "📄 Installing service file..."
cp systemd/agent-forge-polling.service /etc/systemd/system/

# Reload systemd
echo "🔄 Reloading systemd daemon..."
systemctl daemon-reload

# Configure token (if not already set)
echo ""
echo "⚙️  Configuration:"
echo "   Edit /etc/systemd/system/agent-forge-polling.service"
echo "   and set your GitHub token:"
echo ""
echo "   Environment=\"BOT_GITHUB_TOKEN=your_token_here\""
echo ""

# Ask if user wants to enable auto-start
read -p "Enable auto-start on boot? [y/N] " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "✅ Enabling service..."
    systemctl enable agent-forge-polling.service
else
    echo "⏭️  Skipped auto-start (you can enable later with: systemctl enable agent-forge-polling.service)"
fi

# Ask if user wants to start now
read -p "Start polling service now? [y/N] " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🚀 Starting polling service..."
    systemctl start agent-forge-polling.service
    
    # Wait a moment
    sleep 2
    
    # Show status
    echo ""
    echo "📊 Service status:"
    systemctl status agent-forge-polling.service --no-pager || true
else
    echo "⏭️  Service not started (you can start later with: systemctl start agent-forge-polling.service)"
fi

echo ""
echo "============================================"
echo "✅ Installation complete!"
echo ""
echo "Useful commands:"
echo "  systemctl status agent-forge-polling    # Check status"
echo "  systemctl start agent-forge-polling     # Start service"
echo "  systemctl stop agent-forge-polling      # Stop service"
echo "  systemctl restart agent-forge-polling   # Restart service"
echo "  journalctl -u agent-forge-polling -f    # View logs"
echo ""
