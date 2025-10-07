#!/bin/bash
# quick-deploy.sh - Run all deployment checks
set -e

echo "🔍 Running deployment checks..."

# Change to project directory
cd "$(dirname "$0")/.." || exit 1

# Tests
echo "1️⃣ Running tests..."
if ! pytest tests/ -v; then
    echo "❌ Tests failed!"
    exit 1
fi

# Security check
echo "2️⃣ Checking for secrets in git..."
if git log --all -p | grep -qi "ghp_"; then
    echo "❌ Found potential secrets in git history!"
    exit 1
fi

# Update services
echo "3️⃣ Updating systemd services..."
sudo cp systemd/*.service /etc/systemd/system/
sudo systemctl daemon-reload

# Restart services
echo "4️⃣ Restarting services..."
sudo systemctl restart agent-forge agent-forge-auth

# Wait for services
echo "5️⃣ Waiting for services to start..."
sleep 5

# Verify
echo "6️⃣ Verifying services..."
if ! systemctl is-active --quiet agent-forge; then
    echo "❌ agent-forge not running"
    exit 1
fi

if ! systemctl is-active --quiet agent-forge-auth; then
    echo "❌ agent-forge-auth not running"
    exit 1
fi

# Health checks
echo "7️⃣ Health checks..."
if ! curl -sf http://localhost:7996/health > /dev/null; then
    echo "❌ Auth service unhealthy"
    exit 1
fi

if ! curl -sf http://localhost:7998/api/config/health > /dev/null; then
    echo "❌ Config API unhealthy"
    exit 1
fi

echo "✅ Deployment complete!"
echo "📊 Check dashboard: http://$(hostname -I | cut -d' ' -f1):8897/dashboard.html"
