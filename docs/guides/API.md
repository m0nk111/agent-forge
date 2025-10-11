# API Reference 📡

Complete API documentation for Agent-Forge REST endpoints.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Authentication](#authentication)
- [Base URL](#base-url)
- [Response Format](#response-format)
- [Error Handling](#error-handling)
- [Service Manager API](#service-manager-api)
- [Agent Control API](#agent-control-api)
- [Configuration API](#configuration-api)
- [Monitoring API](#monitoring-api)
- [GitHub Integration API](#github-integration-api)
- [Rate Limits](#rate-limits)

---

## 🌐 Overview

Agent-Forge provides a RESTful API for managing agents, monitoring system status, and controlling workflows.

**API Version**: v1  
**Protocol**: HTTP/HTTPS  
**Data Format**: JSON

---

## 🔐 Authentication

### Development Mode (Local)

No authentication required for local development:

```bash
curl http://localhost:8080/health
```

### Production Mode

**TODO**: Authentication will be added in future versions.

Planned authentication methods:
- API Key (header-based)
- JWT tokens
- OAuth 2.0

---

## 🌍 Base URL

### Local Development
```
http://localhost:8080
```

### LAN Access
```
http://192.168.1.26:8080
```

### Production (Future)
```
https://agent-forge.example.com/api/v1
```

---

## 📦 Response Format

### Success Response

```json
{
  "status": "success",
  "data": {
    // Response data
  },
  "timestamp": "2025-10-06T14:30:00Z"
}
```

### Error Response

```json
{
  "status": "error",
  "error": {
    "code": "INVALID_REQUEST",
    "message": "Agent not found",
    "details": {
      "agent_id": "bot-999"
    }
  },
  "timestamp": "2025-10-06T14:30:00Z"
}
```

---

## ❌ Error Handling

### HTTP Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 200 | OK | Request successful |
| 201 | Created | Resource created |
| 400 | Bad Request | Invalid request parameters |
| 401 | Unauthorized | Authentication required |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 409 | Conflict | Resource conflict (e.g., duplicate) |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error |
| 503 | Service Unavailable | Service temporarily unavailable |

### Error Codes

| Code | Description |
|------|-------------|
| `INVALID_REQUEST` | Malformed request |
| `AGENT_NOT_FOUND` | Agent ID doesn't exist |
| `AGENT_BUSY` | Agent is processing another task |
| `CONFIG_ERROR` | Configuration validation failed |
| `GITHUB_ERROR` | GitHub API error |
| `OLLAMA_ERROR` | Ollama service error |
| `RATE_LIMIT` | Rate limit exceeded |

---

## 🔧 Service Manager API

### GET /health

**Health check endpoint**

#### Request
```bash
curl http://localhost:8080/health
```

#### Response
```json
{
  "status": "success",
  "data": {
    "service": "agent-forge",
    "version": "0.2.0",
    "uptime": 3600,
    "healthy": true
  }
}
```

---

### GET /status

**Detailed service status**

#### Request
```bash
curl http://localhost:8080/status
```

#### Response
```json
{
  "status": "success",
  "data": {
    "service": "agent-forge",
    "version": "0.2.0",
    "uptime": 3600,
    "agents": {
      "total": 3,
      "idle": 2,
      "working": 1,
      "error": 0
    },
    "services": {
      "polling": {
        "enabled": true,
        "status": "running",
        "last_poll": "2025-10-06T14:25:00Z"
      },
      "monitoring": {
        "enabled": true,
        "status": "running",
        "port": 7997
      },
      "web_ui": {
        "enabled": true,
        "status": "running",
        "port": 8897
      }
    },
    "resources": {
      "cpu_percent": 23.5,
      "memory_mb": 512,
      "disk_usage_percent": 45.2
    }
  }
}
```

---

## 🤖 Agent Control API

### GET /agents

**List all agents**

#### Request
```bash
curl http://localhost:8080/agents
```

#### Response
```json
{
  "status": "success",
  "data": {
    "agents": [
      {
        "id": "bot-1",
        "name": "Bot Agent 1",
        "type": "bot",
        "model": "qwen2.5-coder:7b",
        "status": "idle",
        "mode": "production",
        "current_task": null,
        "tasks_completed": 42,
        "last_active": "2025-10-06T14:20:00Z",
        "uptime": 7200
      },
      {
        "id": "code-1",
        "name": "Code Agent 1",
        "type": "code",
        "model": "qwen2.5-coder:14b",
        "status": "working",
        "mode": "production",
        "current_task": {
          "issue_number": 67,
          "repo": "your-org/your-project",
          "started_at": "2025-10-06T14:28:00Z"
        },
        "tasks_completed": 15,
        "last_active": "2025-10-06T14:30:00Z",
        "uptime": 7200
      }
    ]
  }
}
```

---

### GET /agents/:id

**Get specific agent details**

#### Request
```bash
curl http://localhost:8080/agents/bot-1
```

#### Response
```json
{
  "status": "success",
  "data": {
    "id": "bot-1",
    "name": "Bot Agent 1",
    "type": "bot",
    "model": "qwen2.5-coder:7b",
    "status": "idle",
    "mode": "production",
    "config": {
      "max_tokens": 8192,
      "temperature": 0.7,
      "retry_attempts": 3
    },
    "statistics": {
      "tasks_completed": 42,
      "tasks_failed": 3,
      "avg_completion_time": 180,
      "api_calls_made": 256,
      "tokens_used": 524288
    },
    "current_task": null,
    "last_active": "2025-10-06T14:20:00Z",
    "created_at": "2025-10-06T12:20:00Z",
    "uptime": 7200
  }
}
```

---

### POST /agents/:id/start

**Start an agent**

#### Request
```bash
curl -X POST http://localhost:8080/agents/bot-1/start
```

#### Response
```json
{
  "status": "success",
  "data": {
    "agent_id": "bot-1",
    "status": "idle",
    "message": "Agent started successfully"
  }
}
```

---

### POST /agents/:id/stop

**Stop an agent**

#### Request
```bash
curl -X POST http://localhost:8080/agents/bot-1/stop
```

#### Response
```json
{
  "status": "success",
  "data": {
    "agent_id": "bot-1",
    "status": "stopped",
    "message": "Agent stopped successfully"
  }
}
```

---

### PUT /agents/:id/mode

**Change agent mode**

#### Request
```bash
curl -X PUT http://localhost:8080/agents/bot-1/mode \
  -H "Content-Type: application/json" \
  -d '{"mode": "production"}'
```

**Body Parameters**:
- `mode` (string, required): `"idle"`, `"test"`, or `"production"`

#### Response
```json
{
  "status": "success",
  "data": {
    "agent_id": "bot-1",
    "mode": "production",
    "message": "Mode changed successfully"
  }
}
```

---

### POST /agents/:id/assign

**Assign task to agent**

#### Request
```bash
curl -X POST http://localhost:8080/agents/bot-1/assign \
  -H "Content-Type: application/json" \
  -d '{
    "repo": "your-org/your-project",
    "issue_number": 42,
    "priority": "high"
  }'
```

**Body Parameters**:
- `repo` (string, required): Repository in `owner/repo` format
- `issue_number` (integer, required): GitHub issue number
- `priority` (string, optional): `"low"`, `"medium"`, `"high"` (default: `"medium"`)

#### Response
```json
{
  "status": "success",
  "data": {
    "agent_id": "bot-1",
    "task_id": "task-1728234567",
    "status": "assigned",
    "message": "Task assigned successfully"
  }
}
```

---

## ⚙️ Configuration API

### GET /config

**Get system configuration**

#### Request
```bash
curl http://localhost:8080/config
```

#### Response
```json
{
  "status": "success",
  "data": {
    "service_manager": {
      "enable_polling": true,
      "enable_monitoring": true,
      "enable_web_ui": true,
      "polling_interval": 300,
      "monitoring_port": 7997,
      "web_ui_port": 8897,
      "polling_repos": [
        "your-org/your-project",
        "your-org/example-repo"
      ]
    },
    "agents": {
      "bot_agent": {
        "model": "qwen2.5-coder:7b",
        "mode": "production",
        "max_tokens": 8192
      }
    }
  }
}
```

---

### PUT /config

**Update system configuration**

#### Request
```bash
curl -X PUT http://localhost:8080/config \
  -H "Content-Type: application/json" \
  -d '{
    "service_manager": {
      "polling_interval": 600
    }
  }'
```

#### Response
```json
{
  "status": "success",
  "data": {
    "message": "Configuration updated successfully",
    "restart_required": true
  }
}
```

---

### GET /config/agents

**Get agents configuration**

#### Request
```bash
curl http://localhost:8080/config/agents
```

#### Response
```json
{
  "status": "success",
  "data": {
    "bot_agent": {
      "model": "qwen2.5-coder:7b",
      "mode": "production",
      "max_tokens": 8192,
      "temperature": 0.7,
      "retry_attempts": 3
    },
    "code_agent": {
      "model": "qwen2.5-coder:14b",
      "mode": "production",
      "max_tokens": 16384,
      "temperature": 0.5
    }
  }
}
```

---

### PUT /config/agents/:id

**Update agent configuration**

#### Request
```bash
curl -X PUT http://localhost:8080/config/agents/bot-1 \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen2.5-coder:14b",
    "temperature": 0.5
  }'
```

#### Response
```json
{
  "status": "success",
  "data": {
    "agent_id": "bot-1",
    "message": "Agent configuration updated",
    "restart_required": true
  }
}
```

---

## 📊 Monitoring API

### GET /metrics

**System metrics**

#### Request
```bash
curl http://localhost:8080/metrics
```

#### Response
```json
{
  "status": "success",
  "data": {
    "timestamp": "2025-10-06T14:30:00Z",
    "system": {
      "cpu_percent": 23.5,
      "memory_used_mb": 512,
      "memory_total_mb": 8192,
      "memory_percent": 6.25,
      "disk_used_gb": 45.2,
      "disk_total_gb": 100,
      "disk_percent": 45.2
    },
    "agents": {
      "total": 3,
      "idle": 2,
      "working": 1,
      "error": 0
    },
    "tasks": {
      "total_processed": 157,
      "successful": 149,
      "failed": 8,
      "in_progress": 1
    },
    "api": {
      "requests_total": 1234,
      "requests_per_minute": 12.5,
      "errors_total": 15,
      "avg_response_time_ms": 45.2
    }
  }
}
```

---

### GET /logs

**Recent logs**

#### Request
```bash
curl "http://localhost:8080/logs?limit=50&level=ERROR"
```

**Query Parameters**:
- `limit` (integer, optional): Number of log entries (default: 100, max: 1000)
- `level` (string, optional): Filter by level: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`
- `agent_id` (string, optional): Filter by agent ID
- `since` (string, optional): ISO 8601 timestamp (e.g., `2025-10-06T14:00:00Z`)

#### Response
```json
{
  "status": "success",
  "data": {
    "logs": [
      {
        "timestamp": "2025-10-06T14:30:00Z",
        "level": "ERROR",
        "agent_id": "bot-1",
        "message": "Failed to create pull request",
        "details": {
          "error": "Validation Failed",
          "repo": "your-org/your-project",
          "issue": 42
        }
      }
    ],
    "total": 50,
    "limit": 50
  }
}
```

---

## 🐙 GitHub Integration API

### GET /github/repos

**List configured repositories**

#### Request
```bash
curl http://localhost:8080/github/repos
```

#### Response
```json
{
  "status": "success",
  "data": {
    "repositories": [
      {
        "full_name": "your-org/your-project",
        "polling_enabled": true,
        "assignees": ["your-bot-account"],
        "last_poll": "2025-10-06T14:25:00Z"
      },
      {
        "full_name": "your-org/example-repo",
        "polling_enabled": true,
        "assignees": ["your-bot-account"],
        "last_poll": "2025-10-06T14:25:00Z"
      }
    ]
  }
}
```

---

### GET /github/issues

**Get assigned issues**

#### Request
```bash
curl "http://localhost:8080/github/issues?repo=your-org/your-project&state=open"
```

**Query Parameters**:
- `repo` (string, optional): Filter by repository
- `state` (string, optional): `"open"`, `"closed"`, `"all"` (default: `"open"`)
- `assignee` (string, optional): Filter by assignee

#### Response
```json
{
  "status": "success",
  "data": {
    "issues": [
      {
        "number": 42,
        "title": "Add retry mechanism",
        "state": "open",
        "repo": "your-org/your-project",
        "assignee": "your-bot-account",
        "labels": ["enhancement"],
        "created_at": "2025-10-06T10:00:00Z",
        "updated_at": "2025-10-06T14:20:00Z"
      }
    ],
    "total": 1
  }
}
```

---

### POST /github/poll

**Trigger manual polling**

#### Request
```bash
curl -X POST http://localhost:8080/github/poll
```

#### Response
```json
{
  "status": "success",
  "data": {
    "message": "Polling triggered",
    "repositories_checked": 2,
    "issues_found": 3
  }
}
```

---

## 🚦 Rate Limits

### Current Limits

| Endpoint Category | Limit | Window |
|------------------|-------|--------|
| Health/Status | 100 | 1 minute |
| Agent Control | 20 | 1 minute |
| Configuration | 10 | 1 minute |
| Monitoring | 60 | 1 minute |
| GitHub Integration | 30 | 1 minute |

### Rate Limit Headers

```
X-RateLimit-Limit: 20
X-RateLimit-Remaining: 15
X-RateLimit-Reset: 1728234600
```

### Rate Limit Exceeded

```json
{
  "status": "error",
  "error": {
    "code": "RATE_LIMIT",
    "message": "Rate limit exceeded",
    "details": {
      "limit": 20,
      "remaining": 0,
      "reset": "2025-10-06T14:35:00Z"
    }
  }
}
```

---

## 📝 Examples

### Python Client

```python
import requests

BASE_URL = "http://localhost:8080"

# Get all agents
response = requests.get(f"{BASE_URL}/agents")
agents = response.json()["data"]["agents"]

# Start an agent
requests.post(f"{BASE_URL}/agents/bot-1/start")

# Assign task
requests.post(
    f"{BASE_URL}/agents/bot-1/assign",
    json={
        "repo": "your-org/your-project",
        "issue_number": 42
    }
)

# Monitor status
while True:
    status = requests.get(f"{BASE_URL}/agents/bot-1").json()
    if status["data"]["status"] == "idle":
        break
    time.sleep(5)
```

### Shell Script

```bash
#!/bin/bash
BASE_URL="http://localhost:8080"

# Check health
curl -s $BASE_URL/health | jq .

# Get agent status
curl -s $BASE_URL/agents/bot-1 | jq '.data.status'

# Start agent if idle
STATUS=$(curl -s $BASE_URL/agents/bot-1 | jq -r '.data.status')
if [ "$STATUS" = "idle" ]; then
    curl -X POST $BASE_URL/agents/bot-1/start
fi
```

---

**API Version**: 1.0  
**Last Updated**: October 6, 2025

*For WebSocket API documentation, see [ARCHITECTURE.md](../ARCHITECTURE.md#websocket-protocol)*
