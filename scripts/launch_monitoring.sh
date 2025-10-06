#!/bin/bash
# Launch monitoring dashboard with Qwen simulation

echo "🚀 Starting Agent-Forge Monitoring Dashboard"
echo "============================================"
echo ""

cd /home/flip/agent-forge

# Activate venv
source venv/bin/activate

# Start WebSocket server in background
echo "📡 Starting WebSocket server on port 7997..."
python3 agents/websocket_handler.py > /tmp/websocket_server.log 2>&1 &
WEBSOCKET_PID=$!
echo "   Server PID: $WEBSOCKET_PID"

# Wait for server to start
sleep 2

# Check if server started
if kill -0 $WEBSOCKET_PID 2>/dev/null; then
    echo "✅ WebSocket server started"
else
    echo "❌ Failed to start WebSocket server"
    echo "   Check logs: cat /tmp/websocket_server.log"
    exit 1
fi

# Open dashboard in browser
echo ""
echo "🌐 Opening dashboard in browser..."
DASHBOARD_PATH="file:///home/flip/agent-forge/frontend/monitoring_dashboard.html"

if command -v firefox &> /dev/null; then
    firefox "$DASHBOARD_PATH" &
    echo "✅ Opened in Firefox"
elif command -v google-chrome &> /dev/null; then
    google-chrome "$DASHBOARD_PATH" &
    echo "✅ Opened in Chrome"
elif command -v chromium-browser &> /dev/null; then
    chromium-browser "$DASHBOARD_PATH" &
    echo "✅ Opened in Chromium"
else
    echo "⚠️ No browser found, please open manually:"
    echo "   $DASHBOARD_PATH"
fi

# Wait a bit for browser to connect
sleep 3

# Start Qwen simulation
echo ""
echo "🤖 Starting Qwen agent simulation..."
echo "============================================"
echo ""
python3 scripts/demo_qwen_working.py

# Cleanup
echo ""
echo "🧹 Cleaning up..."
kill $WEBSOCKET_PID 2>/dev/null
echo "✅ Stopped WebSocket server"
echo ""
echo "👋 Dashboard closed"
