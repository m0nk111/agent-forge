#!/bin/bash
# Launch Agent-Forge Dashboard Server
# This script starts a simple HTTP server for the dashboard on all network interfaces

# Go to project root (one level up from scripts/)
cd "$(dirname "$0")/.."

PORT=8897
FRONTEND_DIR="frontend"

# Get the machine's IP address
IP_ADDR=$(hostname -I | awk '{print $1}')

echo "🚀 Starting Agent-Forge Dashboard Server"
echo "=================================="
echo "📂 Serving from: $FRONTEND_DIR"
echo "🌐 Port: $PORT"
echo "🔗 Local access: http://localhost:$PORT/dashboard.html"
echo "🏠 LAN access: http://$IP_ADDR:$PORT/dashboard.html"
echo ""
echo "Press Ctrl+C to stop"
echo "=================================="

# Start HTTP server on all interfaces (0.0.0.0)
python3 -m http.server $PORT --directory $FRONTEND_DIR --bind 0.0.0.0
