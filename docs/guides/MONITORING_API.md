# Monitoring API Reference 📊

**Real-time monitoring API endpoints for Agent-Forge**

Last Updated: October 7, 2025

---

## Overview

The Monitoring API provides real-time status information about agents, services, and system activity. All endpoints are served by the monitoring service on port **7997**.

**Base URL**: `http://localhost:7997`

**Protocol**: HTTP REST + WebSocket  
**Data Format**: JSON

---

## REST Endpoints

### GET /api/agents

Get status of all registered AI agents.

**Returns**: Active AI agents (not infrastructure services)

#### Request
```bash
curl http://localhost:7997/api/agents | jq .
```

#### Response
```json
{
  "agents": [
    {
      "agent_id": "your-agent",
      "agent_name": "Qwen Agent - Generic Project",
      "status": "idle",
      "current_task": null,
      "current_issue": null,
      "current_pr": null,
      "progress": 0.0,
      "phase": null,
      "started_at": null,
      "last_update": 1759876978.473456,
      "error_message": null,
      "cpu_usage": 0.0,
      "memory_usage": 0.0,
      "api_calls": 0,
      "api_rate_limit_remaining": 5000
    },
    {
      "agent_id": "your-bot-account",
      "agent_name": "GitHub Bot Agent",
      "status": "offline",
      "current_task": "Agent configured but not running",
      "last_update": 1759876978.473456
    }
  ],
  "total": 2
}
```

#### Agent Status Values
- `idle` - Agent is ready for tasks
- `working` - Agent is actively processing a task
- `error` - Agent encountered an error
- `offline` - Agent is not running

---

### GET /api/services

Get status of infrastructure services.

**Returns**: Infrastructure services (polling, monitoring, web_ui, agent_runtime)

#### Request
```bash
curl http://localhost:7997/api/services | jq .
```

#### Response
```json
{
  "services": {
    "polling": {
      "name": "polling",
      "status": "online",
      "healthy": true,
      "last_update": 1759876978.473456
    },
    "monitoring": {
      "name": "monitoring",
      "status": "online",
      "healthy": true,
      "last_update": 1759876978.473456
    },
    "web_ui": {
      "name": "web_ui",
      "status": "online",
      "healthy": true,
      "last_update": 1759876978.473456
    },
    "agent_runtime": {
      "name": "agent_runtime",
      "status": "online",
      "healthy": true,
      "last_update": 1759876978.473456
    }
  },
  "total": 4
}
```

#### Service Status Values
- `online` - Service is running and healthy
- `offline` - Service is not running or unhealthy

---

### GET /api/agents/{agent_id}/status

Get detailed status for a specific agent.

#### Request
```bash
curl http://localhost:7997/api/agents/your-agent/status | jq .
```

#### Response
```json
{
  "agent_id": "your-agent",
  "agent_name": "Qwen Agent - Generic Project",
  "status": "working",
  "current_task": "Fixing bug in config_manager.py",
  "current_issue": 42,
  "progress": 65.0,
  "phase": "Testing changes",
  "api_calls": 15,
  "api_rate_limit_remaining": 4985
}
```

---

### GET /api/agents/{agent_id}/logs

Get recent log entries for a specific agent.

#### Query Parameters
- `limit` (optional, default=100) - Number of log entries to return

#### Request
```bash
curl "http://localhost:7997/api/agents/your-agent/logs?limit=50" | jq .
```

#### Response
```json
{
  "agent_id": "your-agent",
  "logs": [
    {
      "timestamp": 1759876978.123456,
      "agent_id": "your-agent",
      "level": "INFO",
      "message": "Starting task: Fix config loading",
      "context": {
        "issue": 42,
        "repo": "your-org/your-project"
      }
    },
    {
      "timestamp": 1759876980.234567,
      "agent_id": "your-agent",
      "level": "DEBUG",
      "message": "Reading file: engine/core/config_manager.py",
      "context": null
    }
  ],
  "total": 2
}
```

#### Log Levels
- `DEBUG` - Detailed diagnostic information
- `INFO` - General informational messages
- `WARNING` - Warning messages
- `ERROR` - Error messages

---

### GET /api/activity

Get recent activity timeline across all agents.

#### Query Parameters
- `limit` (optional, default=100) - Number of events to return
- `agent_id` (optional) - Filter by specific agent

#### Request
```bash
curl "http://localhost:7997/api/activity?limit=10" | jq .
```

#### Response
```json
{
  "events": [
    {
      "timestamp": 1759876978.123456,
      "agent_id": "your-agent",
      "event_type": "issue_claimed",
      "description": "Claimed issue #42: Fix config loading",
      "metadata": {
        "repo": "your-org/your-project",
        "issue": 42
      }
    },
    {
      "timestamp": 1759876990.234567,
      "agent_id": "your-agent",
      "event_type": "pr_created",
      "description": "Created PR #43: Fix config manager",
      "metadata": {
        "repo": "your-org/your-project",
        "pr": 43
      }
    }
  ],
  "total": 2
}
```

#### Event Types
- `issue_claimed` - Agent claimed an issue
- `issue_completed` - Agent completed an issue
- `pr_created` - Agent created a pull request
- `pr_merged` - Pull request was merged
- `error` - Error occurred

---

## WebSocket Endpoints

### WS /ws/monitor

Real-time updates for all agents.

**Receives**: Agent status updates, log entries, activity events

#### Connect
```javascript
const ws = new WebSocket('ws://localhost:7997/ws/monitor');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Received:', data);
};
```

#### Message Types

**Agent Update**
```json
{
  "type": "agent_update",
  "agent": {
    "agent_id": "your-agent",
    "status": "working",
    "current_task": "Fixing bug",
    "progress": 50.0
  }
}
```

**Log Entry**
```json
{
  "type": "log_entry",
  "agent_id": "your-agent",
  "log": {
    "timestamp": 1759876978.123,
    "level": "INFO",
    "message": "Task completed"
  }
}
```

---

### WS /ws/logs/{agent_id}

Real-time log stream for a specific agent.

**Receives**: Log entries from specific agent

#### Connect
```javascript
const agentId = 'your-agent';
const ws = new WebSocket(`ws://localhost:7997/ws/logs/${agentId}`);

ws.onmessage = (event) => {
  const log = JSON.parse(event.data);
  console.log(`[${log.level}] ${log.message}`);
};
```

---

## Architecture Notes

### Services vs Agents

**Services** (Infrastructure):
- `polling` - GitHub repository polling service
- `monitoring` - Monitoring API and WebSocket service
- `web_ui` - Dashboard HTTP server
- `agent_runtime` - Unified agent runtime with role-based lifecycle management

**Agents** (AI Workers):
- `your-agent` - Developer agent (always-on, Qwen 2.5 Coder)
- `your-bot-agent` - Bot agent (on-demand, GitHub operations)

Services are part of the infrastructure and managed by `service_manager`.  
Agents are AI workers managed by `agent_runtime` (AgentRegistry) with role-based lifecycle:
- **Always-on**: coordinator, developer (start immediately)
- **On-demand**: bot, reviewer, tester, documenter, researcher (lazy loading)

### Status Updates

- Service health status is updated every 30 seconds by `service_manager`
- Agent status is updated in real-time when agents report their state
- WebSocket clients receive immediate notifications of all changes

---

## Examples

### Check All System Status
```bash
#!/bin/bash
echo "=== Services ==="
curl -s http://localhost:7997/api/services | jq '.services | to_entries[] | "\(.key): \(.value.status)"'

echo -e "\n=== Agents ==="
curl -s http://localhost:7997/api/agents | jq '.agents[] | "\(.agent_id): \(.status)"'
```

### Monitor Agent Progress
```bash
#!/bin/bash
AGENT_ID="your-agent"

while true; do
  STATUS=$(curl -s http://localhost:7997/api/agents/${AGENT_ID}/status)
  TASK=$(echo "$STATUS" | jq -r '.current_task // "idle"')
  PROGRESS=$(echo "$STATUS" | jq -r '.progress')
  
  echo "[$(date +%H:%M:%S)] Task: $TASK | Progress: ${PROGRESS}%"
  sleep 5
done
```

### Dashboard Integration
```javascript
// Real-time dashboard updates
const ws = new WebSocket('ws://localhost:7997/ws/monitor');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  if (data.type === 'agent_update') {
    updateAgentCard(data.agent);
  } else if (data.type === 'log_entry') {
    appendToLogViewer(data.log);
  }
};

// Fetch initial state
async function loadInitialState() {
  const agents = await fetch('http://localhost:7997/api/agents').then(r => r.json());
  const services = await fetch('http://localhost:7997/api/services').then(r => r.json());
  
  renderAgents(agents.agents);
  renderServices(services.services);
}
```

---

## Related Documentation

- [ARCHITECTURE.md](../ARCHITECTURE.md) - System architecture overview
- [DEPLOYMENT.md](DEPLOYMENT.md) - Deployment guide
- [API.md](API.md) - Full API reference
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Common issues

---

**Monitoring Service Version**: 1.0  
**Port**: 7997  
**Last Updated**: October 7, 2025
