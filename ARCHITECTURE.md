# Agent-Forge Architecture

> **Version**: 1.0.0  
> **Last Updated**: 2025-10-06  
> **Status**: Living Document

## 📋 Table of Contents

1. [System Overview](#system-overview)
2. [Service Manager](#service-manager)
3. [Agent Roles & Responsibilities](#agent-roles--responsibilities)
4. [Communication Architecture](#communication-architecture)
5. [Frontend Architecture](#frontend-architecture)
6. [Port Allocation](#port-allocation)
7. [Data Flow](#data-flow)
8. [Configuration Management](#configuration-management)
9. [Deployment Architecture](#deployment-architecture)
10. [Security Considerations](#security-considerations)

---

## System Overview

Agent-Forge is a multi-agent orchestration platform for GitHub automation. It consists of:

- **Service Manager**: Central orchestrator running all services
- **Specialized Agents**: Bot, Coordinator, Code Agent (generic LLM, formerly Qwen)
- **Monitoring Infrastructure**: WebSocket server + real-time dashboards
- **Polling Service**: Autonomous GitHub issue detection
- **Configuration Management**: YAML-based agent and system configuration
- **Instruction Validation System**: Automatic enforcement of Copilot instructions (PR #63)
- **Visual Documentation**: Comprehensive Mermaid diagrams for architecture understanding (PR #68)

### Recent Updates (October 2025)

**Agent Refactoring**:
- `qwen_agent.py` renamed to `code_agent.py` for generic LLM support
- `QwenAgent` class renamed to `CodeAgent`
- Service manager updated: `enable_qwen_agent` → `enable_code_agent`
- Backward compatibility maintained via CLI flags

**Instruction Validation** (PR #63):
- Validates file locations, commit messages, changelog updates, port usage, language
- Auto-fix capabilities for common issues
- Integrated into IssueHandler, FileEditor, GitOperations
- 30 unit tests + 4 integration tests (78% code coverage)

**Documentation Enhancement** (PR #68):
- Complete architecture documentation suite
- Visual Mermaid diagrams (1389 lines total)
- Agent onboarding checklist
- Port reference guide with troubleshooting
- Prevents agent confusion between projects

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Service Manager (Port 8080)              │
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Monitor      │  │ WebSocket    │  │ Polling      │      │
│  │ Service      │  │ Handler      │  │ Service      │      │
│  │ (7997)       │  │ (7997)       │  │              │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Code Agent   │  │ Bot Agent    │  │ Coordinator  │      │
│  │ (Qwen)       │  │              │  │ Agent        │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
          ┌────────────────────────────────────┐
          │   Frontend (Port 8897)             │
          │                                    │
          │  • dashboard.html (DEFAULT)        │
          │  • unified_dashboard.html (NEW)    │
          │  • monitoring_dashboard.html       │
          │  • config_ui.html                  │
          └────────────────────────────────────┘
                           │
                           ▼
              ┌───────────────────────┐
              │   GitHub API          │
              │   • Issues            │
              │   • Pull Requests     │
              │   • Repositories      │
              └───────────────────────┘
```

**See Also**: [Visual Diagrams](docs/diagrams/architecture-overview.md)

---

## Service Manager

### Purpose

The Service Manager (`agents/service_manager.py`) is the central orchestrator that:
- Starts and manages all services in a single process
- Handles graceful shutdown on SIGTERM/SIGINT
- Provides systemd integration (watchdog, notify)
- Monitors service health
- Exposes REST API for service control

### Architecture

```python
ServiceManager
├── PollingService      # GitHub issue monitoring
├── MonitorService      # Agent state tracking
├── WebSocketHandler    # Real-time communication
├── CodeAgent          # Code generation (Qwen)
├── BotAgent           # GitHub operations
└── CoordinatorAgent   # Task orchestration
```

### Configuration

**File**: `config/system.yaml`

```yaml
service_manager:
  enable_polling: true
  enable_monitoring: true
  enable_web_ui: true
  enable_code_agent: true
  
  polling_interval: 300  # 5 minutes
  monitoring_port: 7997
  web_ui_port: 8897
  
  polling_repos:
    - "m0nk111/agent-forge"
    - "m0nk111/stepperheightcontrol"
```

### REST API Endpoints

**Base URL**: `http://localhost:8080`

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Service health check |
| `/status` | GET | Detailed service status |
| `/agents` | GET | List all agents and states |
| `/agents/{id}/start` | POST | Start specific agent |
| `/agents/{id}/stop` | POST | Stop specific agent |
| `/config` | GET | Get system configuration |
| `/config` | PUT | Update configuration |

---

## Agent Roles & Responsibilities

### 1. Bot Agent (`agents/bot_agent.py`)

**Purpose**: Executes GitHub operations

**Responsibilities**:
- Process assigned GitHub issues
- Create and manage branches
- Commit code changes
- Create and update pull requests
- Handle GitHub API interactions

**LLM Support**: Any (GPT-4, Claude, Qwen, etc.)

**Configuration**: `config/bot_config.yaml`

### 2. Coordinator Agent (`agents/coordinator_agent.py`)

**Purpose**: High-level task orchestration

**Responsibilities**:
- Task distribution to other agents
- Workflow management
- Priority queue management
- Multi-agent coordination
- Decision-making and planning

**LLM Support**: High-capability models (GPT-4, Claude Opus)

**Configuration**: `config/coordinator_config.yaml`

### 3. Qwen Agent / Code Agent (`agents/qwen_agent.py`)

**Purpose**: Code generation and analysis

**Responsibilities**:
- Generate code solutions
- Code refactoring
- Code review assistance
- Documentation generation
- Local LLM integration (cost-effective)

**LLM Support**: Qwen 2.5 Coder (7B, 14B, 32B) via Ollama

**Configuration**: `config/agents.yaml`

### 4. Polling Service (`agents/polling_service.py`)

**Purpose**: Autonomous GitHub monitoring

**Responsibilities**:
- Poll GitHub repositories for new issues
- Detect assigned issues for bot accounts
- Trigger agent workflows
- Rate limit management

**Configuration**: `polling_config.yaml`

---

## Communication Architecture

### WebSocket Protocol

**Server**: `agents/websocket_handler.py`  
**Port**: 7997  
**Protocol**: WebSocket (ws://)

#### Message Types

```typescript
// Agent State Update
{
  type: "agent_state",
  data: {
    agent_id: string,
    agent_name: string,
    status: "idle" | "working" | "error",
    current_task: string,
    progress: number,
    cpu_usage: number,
    memory_usage: number,
    api_calls: number
  }
}

// Log Entry
{
  type: "log",
  data: {
    timestamp: number,
    agent_id: string,
    level: "INFO" | "WARNING" | "ERROR" | "SUCCESS",
    message: string
  }
}

// System Event
{
  type: "system",
  data: {
    event: "startup" | "shutdown" | "error",
    message: string
  }
}
```

### Agent Communication Flow

```
GitHub Issue
    │
    ▼
PollingService
    │
    ├──> IssueHandler
    │       │
    │       ▼
    │    BotAgent ◄──────┐
    │       │             │
    │       ▼             │
    │    CodeAgent        │
    │       │             │
    │       ▼             │
    │    git_operations   │
    │       │             │
    │       ▼             │
    │    GitHub API ──────┘
    │
    └──> MonitorService
            │
            ▼
        WebSocket
            │
            ▼
        Frontend Dashboards
```

**See Also**: [Data Flow Diagram](docs/diagrams/data-flow.md)

---

## Frontend Architecture

### Directory Structure

```
frontend/
├── index.html                  # Landing page (auto-redirects)
├── dashboard.html              # ⭐ DEFAULT DASHBOARD (main entry)
├── unified_dashboard.html      # New unified dashboard
├── monitoring_dashboard.html   # Classic monitoring view
└── config_ui.html             # Configuration interface
```

### Page Purposes

#### `index.html`
- **Purpose**: Landing page with auto-redirect
- **Auto-redirects to**: `dashboard.html`
- **Use Case**: Entry point for users

#### `dashboard.html` ⭐ **DEFAULT**
- **Purpose**: Main dashboard after login
- **Features**: Agent overview, basic monitoring
- **Port**: 8897
- **Access**: `http://localhost:8897/dashboard.html`
- **WebSocket**: `ws://localhost:7997/ws/monitor`

#### `unified_dashboard.html` (NEW)
- **Purpose**: Modern unified interface
- **Features**:
  - Agent cards with real-time status
  - Configuration modal (gear icon)
  - Live log streaming
  - Sliding sidebar for settings
- **Issues**: #27, #28, #65
- **Access**: `http://localhost:8897/unified_dashboard.html`

#### `monitoring_dashboard.html`
- **Purpose**: Classic monitoring view
- **Features**: Detailed metrics, graphs, historical data
- **Use Case**: Deep monitoring and analysis

#### `config_ui.html`
- **Purpose**: Agent configuration interface
- **Features**: YAML editor, validation, apply config
- **API Endpoint**: `/api/config/agents`

### Frontend-Backend Communication

```
Frontend (8897)
    │
    ├──> WebSocket (7997)
    │    ├─ Real-time agent state
    │    ├─ Log streaming
    │    └─ System events
    │
    └──> REST API (8080)
         ├─ GET /status
         ├─ GET /agents
         ├─ POST /agents/{id}/start
         └─ PUT /config
```

**See Also**: [Component Interaction Diagram](docs/diagrams/component-interactions.md)

---

## Port Allocation

### Port Usage Table

| Port | Service | Protocol | Purpose | Bind Address |
|------|---------|----------|---------|--------------|
| **8080** | Service Manager | HTTP | REST API, service orchestration | `0.0.0.0` |
| **7997** | WebSocket Server | WebSocket | Real-time monitoring, log streaming | `0.0.0.0` |
| **8897** | Frontend HTTP | HTTP | Dashboard hosting | `0.0.0.0` |
| 7996 | Code Agent | HTTP | Code generation API (optional) | `127.0.0.1` |
| 11434 | Ollama | HTTP | Local LLM inference | `127.0.0.1` |

### Port Conflicts

**Common Issues**:
- Port 8897 vs 8898: Always use **8897** for frontend
- Port 7997: Ensure no other WebSocket server is running
- Port 8080: Check for other web services

**Resolution**:
```bash
# Check if port is in use
lsof -i:8897

# Kill process using port
lsof -ti:8897 | xargs kill -9

# Verify port is free
lsof -i:8897  # Should return nothing
```

**See Also**: [Port Reference Guide](docs/PORT_REFERENCE.md)

---

## Data Flow

### Issue Processing Flow

```
1. GitHub Issue Created/Updated
   │
   ▼
2. PollingService detects (every 5 min)
   │
   ▼
3. IssueHandler validates and parses
   │
   ▼
4. BotAgent assigned to issue
   │
   ├──> Creates branch
   │
   ├──> Calls CodeAgent for solution
   │     │
   │     └──> Qwen 2.5 Coder generates code
   │
   ├──> Commits changes
   │
   ├──> Creates Pull Request
   │
   └──> Updates issue with PR link
```

### Monitoring Data Flow

```
Agent State Change
   │
   ▼
MonitorService.update_agent()
   │
   ▼
WebSocketHandler.broadcast()
   │
   ├──> dashboard.html
   ├──> unified_dashboard.html
   └──> monitoring_dashboard.html
        │
        └──> Real-time UI update
```

### Configuration Flow

```
User edits config_ui.html
   │
   ▼
PUT /api/config/agents
   │
   ▼
ConfigManager.validate()
   │
   ▼
ConfigManager.save()
   │
   ├──> config/agents.yaml
   │
   └──> ServiceManager.reload()
        │
        └──> Agents restart with new config
```

---

## Configuration Management

### Configuration Files

| File | Purpose | Format |
|------|---------|--------|
| `config/system.yaml` | System-wide settings | YAML |
| `config/agents.yaml` | Agent definitions | YAML |
| `config/bot_config.yaml` | Bot-specific config | YAML |
| `config/coordinator_config.yaml` | Coordinator settings | YAML |
| `config/repositories.yaml` | GitHub repo mappings | YAML |
| `config/instruction_rules.yaml` | Validation rules | YAML |
| `config/review_criteria.yaml` | PR review criteria | YAML |

### Configuration Hierarchy

```
1. Environment Variables (highest priority)
   ↓
2. config/*.yaml files
   ↓
3. Default values in code (lowest priority)
```

### Environment Variables

```bash
# LLM Configuration
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=...

# GitHub Configuration  
GITHUB_TOKEN=ghp_...
GITHUB_BOT_TOKEN=ghp_...

# Service Configuration
SERVICE_MANAGER_PORT=8080
WEBSOCKET_PORT=7997
FRONTEND_PORT=8897

# Monitoring
ENABLE_MONITORING=true
LOG_LEVEL=INFO
```

### Configuration API

```python
from agents.config_manager import ConfigManager

# Load configuration
config = ConfigManager.load("system")

# Access values
port = config.get("service_manager.monitoring_port", 7997)

# Update configuration
ConfigManager.update("agents", {"bot.model": "gpt-4"})

# Validate configuration
errors = ConfigManager.validate("agents")
```

---

## Deployment Architecture

### Local Development

```bash
# Start all services
python -m agents.service_manager

# Access dashboard
http://localhost:8897/dashboard.html
```

### Systemd Service (Production)

```bash
# Install service
sudo ./scripts/install-service.sh

# Start service
sudo systemctl start agent-forge

# Enable auto-start
sudo systemctl enable agent-forge

# View logs
sudo journalctl -u agent-forge -f
```

**Service File**: `systemd/agent-forge.service`

### Docker (Future)

```yaml
# docker-compose.yml (planned)
services:
  agent-forge:
    build: .
    ports:
      - "8080:8080"
      - "7997:7997"
      - "8897:8897"
    volumes:
      - ./config:/app/config
    environment:
      - GITHUB_TOKEN=${GITHUB_TOKEN}
```

### Network Access

**Local Only**:
```bash
# Bind to localhost
--bind 127.0.0.1
```

**LAN Access** (default):
```bash
# Bind to all interfaces
--bind 0.0.0.0

# Access from other devices
http://192.168.1.26:8897/dashboard.html
```

---

## Security Considerations

### API Tokens

- Store in environment variables (NOT in config files)
- Use `.env` files (excluded from git)
- Rotate tokens regularly
- Use bot accounts with minimal permissions

### WebSocket Security

- Currently no authentication (local network only)
- **TODO**: Add authentication for production
- **TODO**: Support WSS (WebSocket Secure)

### File Permissions

```bash
# Configuration files
chmod 600 config/*.yaml

# Scripts
chmod 700 scripts/*.sh

# Logs
chmod 640 logs/*.log
```

### GitHub Permissions

**Bot Account Requirements**:
- `repo` scope (read/write)
- `workflow` scope (optional, for GitHub Actions)
- `admin:org` (optional, for org-level operations)

**Best Practices**:
- Use dedicated bot accounts
- Limit repository access
- Enable 2FA on bot accounts
- Monitor API rate limits

---

## Appendix

### Related Documentation

- [Agent Onboarding Guide](docs/AGENT_ONBOARDING.md)
- [Visual Diagrams](docs/diagrams/)
- [Port Reference](docs/PORT_REFERENCE.md)
- [Multi-Agent Strategy](docs/MULTI_AGENT_GITHUB_STRATEGY.md)
- [Monitoring Guide](docs/QWEN_MONITORING.md)

### Maintenance

- **Review Frequency**: Quarterly
- **Update Triggers**: Major architecture changes, new services
- **Maintainers**: Agent-Forge Team
- **Issues**: Label with `documentation`

---

**Document Version**: 1.0.0  
**Generated**: 2025-10-06  
**Next Review**: 2026-01-06
