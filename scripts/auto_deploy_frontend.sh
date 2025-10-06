#!/bin/bash
#
# Agent-Forge Frontend Auto-Deploy Script
# Monitors git repository and automatically deploys frontend changes
#

set -e

# Configuration
REPO_DIR="/home/flip/agent-forge"
FRONTEND_DIR="$REPO_DIR/frontend"
LOG_FILE="/var/log/agent-forge-deploy.log"
LOCK_FILE="/var/run/agent-forge-deploy.lock"
FRONTEND_PORT=8897

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Check if another instance is running
if [ -f "$LOCK_FILE" ]; then
    pid=$(cat "$LOCK_FILE")
    if ps -p "$pid" > /dev/null 2>&1; then
        log "⚠️  Another deploy is running (PID: $pid), skipping..."
        exit 0
    else
        log "🔧 Stale lock file found, removing..."
        rm -f "$LOCK_FILE"
    fi
fi

# Create lock file
echo $$ > "$LOCK_FILE"
trap "rm -f $LOCK_FILE" EXIT

log "🔍 Checking for frontend updates..."

# Change to repo directory
cd "$REPO_DIR" || {
    log "❌ Failed to change to repo directory"
    exit 1
}

# Fetch latest changes
git fetch origin main 2>&1 | tee -a "$LOG_FILE" || {
    log "❌ Failed to fetch from origin"
    exit 1
}

# Get current and remote commit hashes
LOCAL_HASH=$(git rev-parse HEAD)
REMOTE_HASH=$(git rev-parse origin/main)

if [ "$LOCAL_HASH" = "$REMOTE_HASH" ]; then
    log "✅ Already up to date (commit: ${LOCAL_HASH:0:8})"
    exit 0
fi

log "📥 New commits detected!"
log "   Local:  ${LOCAL_HASH:0:8}"
log "   Remote: ${REMOTE_HASH:0:8}"

# Check if frontend files changed
FRONTEND_CHANGED=$(git diff --name-only "$LOCAL_HASH" "$REMOTE_HASH" | grep -c "^frontend/" || echo "0")

if [ "$FRONTEND_CHANGED" -eq 0 ]; then
    log "ℹ️  No frontend changes detected, pulling anyway..."
fi

# Pull latest changes
log "📥 Pulling latest changes..."
git pull origin main 2>&1 | tee -a "$LOG_FILE" || {
    log "❌ Failed to pull changes"
    exit 1
}

# If frontend changed, copy to production and restart service
if [ "$FRONTEND_CHANGED" -gt 0 ]; then
    log "🔄 Frontend files changed ($FRONTEND_CHANGED files)"
    
    # Copy frontend files to production directory
    if [ -d "/opt/agent-forge/frontend" ]; then
        log "   Syncing to /opt/agent-forge/frontend..."
        rsync -av --delete "$FRONTEND_DIR/" /opt/agent-forge/frontend/ 2>&1 | tee -a "$LOG_FILE" || {
            log "⚠️  rsync failed, trying cp..."
            cp -r "$FRONTEND_DIR/"* /opt/agent-forge/frontend/ 2>&1 | tee -a "$LOG_FILE"
        }
        log "✅ Frontend synced to production"
    fi
    
    # Restart agent-forge service (which serves the frontend)
    log "   Restarting agent-forge.service..."
    systemctl restart agent-forge.service 2>&1 | tee -a "$LOG_FILE" || {
        log "❌ Failed to restart service"
        exit 1
    }
    
    sleep 3
    
    # Verify service is running
    if systemctl is-active --quiet agent-forge.service; then
        log "✅ Service restarted successfully"
    else
        log "❌ Service failed to start"
        exit 1
    fi
else
    log "ℹ️  No frontend changes detected"
fi

log "✅ Deployment completed successfully!"
log "   New commit: ${REMOTE_HASH:0:8}"
log "   Frontend changed: $FRONTEND_CHANGED files"

exit 0
