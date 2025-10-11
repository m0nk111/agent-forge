#!/bin/bash
# Run polling service in test mode with proper environment setup

# Exit on error
set -e

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

echo "🧪 Starting Agent-Forge in TEST MODE"
echo ""

# Load bot token
if [ ! -f "secrets/agents/m0nk111-post.token" ]; then
    echo "❌ Error: Bot token not found at secrets/agents/m0nk111-post.token"
    exit 1
fi

export BOT_GITHUB_TOKEN=$(cat secrets/agents/m0nk111-post.token)
echo "✅ Bot token loaded (${BOT_GITHUB_TOKEN:0:10}...)"

# Set environment
export AGENT_FORGE_ENV=test
echo "✅ Environment: $AGENT_FORGE_ENV"

# Set PYTHONPATH
export PYTHONPATH="$PROJECT_ROOT"
echo "✅ PYTHONPATH: $PYTHONPATH"

echo ""
echo "🤖 Starting service manager (includes agents + monitoring)..."
echo ""

# Start service manager in background with minimal services
# This handles agent registry initialization properly
python3 -m engine.core.service_manager \
    --no-polling \
    --no-web-ui \
    --monitor-port 7998 &

SERVICE_MGR_PID=$!
echo "✅ Service manager started (PID: $SERVICE_MGR_PID)"

# Wait for agents to initialize
echo "⏳ Waiting 15 seconds for agents to initialize..."
sleep 15

echo ""
echo "🚀 Starting polling service..."
echo ""

# Trap to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down..."
    if [ ! -z "$POLLING_PID" ]; then
        echo "   Stopping polling service..."
        kill $POLLING_PID 2>/dev/null || true
    fi
    if [ ! -z "$SERVICE_MGR_PID" ]; then
        echo "   Stopping service manager (agents)..."
        kill $SERVICE_MGR_PID 2>/dev/null || true
    fi
    echo "✅ Cleanup complete"
}

trap cleanup EXIT INT TERM

# Run polling service
python3 engine/runners/polling_service.py &
POLLING_PID=$!

echo "✅ Polling service started (PID: $POLLING_PID)"
echo ""
echo "📊 Services running:"
echo "   • Service Manager (Agents): PID $SERVICE_MGR_PID"
echo "   • Polling Service: PID $POLLING_PID"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Wait for polling service
wait $POLLING_PID
