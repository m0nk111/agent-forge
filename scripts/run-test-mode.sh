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
echo "🚀 Starting polling service..."
echo ""

# Run polling service
python3 engine/runners/polling_service.py
