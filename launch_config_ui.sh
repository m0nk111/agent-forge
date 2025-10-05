#!/bin/bash
# Launch Configuration UI System
# Starts API server and opens configuration UI

set -e

echo "🚀 Starting Agent-Forge Configuration UI"
echo "========================================"

# Change to project directory
cd /home/flip/agent-forge

# Activate virtual environment
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    echo "✅ Activated virtual environment"
else
    echo "❌ Virtual environment not found"
    echo "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -q fastapi uvicorn pyyaml requests
    echo "✅ Created and activated virtual environment"
fi

# Check dependencies
echo "📦 Checking dependencies..."
pip list | grep -q fastapi || pip install -q fastapi
pip list | grep -q uvicorn || pip install -q uvicorn
pip list | grep -q pyyaml || pip install -q pyyaml
pip list | grep -q requests || pip install -q requests
echo "✅ All dependencies installed"

# Start API server in background
echo "🔧 Starting Configuration API server (port 7996)..."
python3 api/config_routes.py > /tmp/config_api_server.log 2>&1 &
API_PID=$!
echo "✅ API server started (PID: $API_PID)"

# Wait for server to be ready
echo "⏳ Waiting for API server to be ready..."
for i in {1..10}; do
    if curl -s http://localhost:7996/api/config/health > /dev/null; then
        echo "✅ API server is ready"
        break
    fi
    sleep 1
done

# Start HTTP server for frontend
echo "🌐 Starting HTTP server for frontend (port 8898)..."
cd frontend
python3 -m http.server 8898 > /tmp/config_ui_server.log 2>&1 &
UI_PID=$!
cd ..
echo "✅ HTTP server started (PID: $UI_PID)"

# Open browser
echo "🌐 Opening configuration UI..."
echo "   URL: http://localhost:8898/config_ui.html"
echo "   API: http://localhost:7996/docs"

# Try to open in browser (VS Code Simple Browser or system browser)
if command -v code &> /dev/null; then
    code --open-url http://localhost:8898/config_ui.html 2>/dev/null || true
elif command -v xdg-open &> /dev/null; then
    xdg-open http://localhost:8898/config_ui.html 2>/dev/null || true
elif command -v firefox &> /dev/null; then
    firefox http://localhost:8898/config_ui.html 2>/dev/null &
elif command -v google-chrome &> /dev/null; then
    google-chrome http://localhost:8898/config_ui.html 2>/dev/null &
fi

echo ""
echo "✅ Configuration UI is now running!"
echo ""
echo "📊 Access Points:"
echo "   - Configuration UI: http://localhost:8898/config_ui.html"
echo "   - API Documentation: http://localhost:7996/docs"
echo "   - API Health Check: http://localhost:7996/api/config/health"
echo ""
echo "📝 Server Logs:"
echo "   - API Server: /tmp/config_api_server.log"
echo "   - UI Server: /tmp/config_ui_server.log"
echo ""
echo "🛑 To stop servers:"
echo "   kill $API_PID $UI_PID"
echo ""
echo "Press Ctrl+C to stop all servers and exit..."

# Trap Ctrl+C and cleanup
trap "echo ''; echo '🛑 Stopping servers...'; kill $API_PID $UI_PID 2>/dev/null; echo '✅ Servers stopped'; exit 0" INT TERM

# Keep script running
wait
