#!/bin/bash
# Agent-Forge Service Wrapper
# Loads environment and starts service with correct parameters

# Load environment
if [ -f /etc/default/agent-forge ]; then
    source /etc/default/agent-forge
fi

# Set defaults
WEB_UI_PORT=${WEB_UI_PORT:-8897}
MONITORING_PORT=${MONITORING_PORT:-7997}
POLLING_INTERVAL=${POLLING_INTERVAL:-300}

# Start service
exec /opt/agent-forge/venv/bin/python3 -m engine.core.service_manager \
    --web-port "${WEB_UI_PORT}" \
    --monitor-port "${MONITORING_PORT}" \
    --polling-interval "${POLLING_INTERVAL}"
