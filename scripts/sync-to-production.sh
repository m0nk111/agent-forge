#!/bin/bash
# sync-to-production.sh
# Sync development to production with proper permissions

set -e

DEV_DIR="/home/flip/agent-forge"
PROD_DIR="/opt/agent-forge"

echo "🔄 Syncing $DEV_DIR → $PROD_DIR..."

# Sync files (exclude venv, cache, git)
sudo rsync -av \
  --exclude='venv/' \
  --exclude='__pycache__/' \
  --exclude='.git/' \
  --exclude='*.pyc' \
  "$DEV_DIR/" "$PROD_DIR/"

# Fix ownership
echo "🔒 Fixing ownership..."
sudo chown -R agent-forge:agent-forge "$PROD_DIR"

# Ensure secrets directory has correct permissions
echo "🔐 Fixing secrets permissions..."
sudo chown -R agent-forge:agent-forge "$PROD_DIR/secrets"
sudo chmod 700 "$PROD_DIR/secrets"
sudo chmod 700 "$PROD_DIR/secrets/agents"
sudo chmod 600 "$PROD_DIR/secrets/agents/"*.token 2>/dev/null || true

# Restart service
echo "🔄 Restarting agent-forge service..."
sudo systemctl restart agent-forge

echo "✅ Sync complete!"
echo ""
echo "Check status with:"
echo "  sudo systemctl status agent-forge"
echo "  curl http://localhost:7997/api/services | jq ."
echo "  curl http://localhost:7997/api/agents | jq ."
