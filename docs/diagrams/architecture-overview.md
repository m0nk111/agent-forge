# Agent-Forge Architecture Overview

> **Visual representation of the Agent-Forge system architecture**

## System Architecture Diagram

```mermaid
graph TB
    subgraph "GitHub"
        GH_API[GitHub API]
        GH_ISSUES[Issues]
        GH_PRS[Pull Requests]
        GH_REPOS[Repositories]
    end

    subgraph "Service Manager (Port 8080)"
        SM[Service Manager<br/>REST API]
        
        subgraph "Core Services"
            PS[Polling Service<br/>Issue Detection]
            MS[Monitor Service<br/>Agent Tracking]
            WS[WebSocket Handler<br/>Port 7997]
        end
        
        subgraph "Agents"
            BOT[Bot Agent<br/>GitHub Operations]
            COORD[Coordinator Agent<br/>Orchestration]
            CODE[Code Agent<br/>Qwen 2.5 Coder]
        end
        
        subgraph "Supporting Modules"
            IH[Issue Handler]
            GO[Git Operations]
            CM[Config Manager]
        end
    end

    subgraph "Frontend (Port 8897)"
        INDEX[index.html<br/>Landing Page]
        DASH[dashboard.html<br/>⭐ DEFAULT]
        UNIFIED[unified_dashboard.html<br/>NEW Unified UI]
        MONITOR[monitoring_dashboard.html<br/>Classic View]
        CONFIG[config_ui.html<br/>Configuration]
    end

    subgraph "Local LLM"
        OLLAMA[Ollama<br/>Port 11434]
        QWEN[Qwen 2.5 Coder<br/>7B/14B/32B]
    end

    subgraph "External LLMs"
        OPENAI[OpenAI<br/>GPT-4]
        ANTHROPIC[Anthropic<br/>Claude]
        GOOGLE[Google<br/>Gemini]
    end

    %% GitHub connections
    GH_API --> GH_ISSUES
    GH_API --> GH_PRS
    GH_API --> GH_REPOS

    %% Service Manager orchestration
    SM --> PS
    SM --> MS
    SM --> WS
    SM --> BOT
    SM --> COORD
    SM --> CODE

    %% Polling flow
    PS --> |Poll every 5 min| GH_API
    PS --> IH
    IH --> BOT

    %% Bot workflow
    BOT --> GO
    BOT --> CODE
    GO --> GH_API

    %% Coordinator workflow
    COORD --> BOT
    COORD --> CODE

    %% Code Agent LLM connections
    CODE --> OLLAMA
    OLLAMA --> QWEN
    
    BOT -.-> OPENAI
    BOT -.-> ANTHROPIC
    BOT -.-> GOOGLE
    
    COORD -.-> OPENAI
    COORD -.-> ANTHROPIC

    %% Monitoring flow
    MS --> WS
    BOT --> MS
    COORD --> MS
    CODE --> MS

    %% Frontend connections
    WS --> |WebSocket<br/>ws://host:7997| DASH
    WS --> |WebSocket<br/>ws://host:7997| UNIFIED
    WS --> |WebSocket<br/>ws://host:7997| MONITOR
    
    INDEX --> |Auto-redirect| DASH
    
    DASH --> |REST API<br/>http://host:8080| SM
    UNIFIED --> |REST API<br/>http://host:8080| SM
    CONFIG --> |REST API<br/>http://host:8080| SM

    %% Config management
    CM --> BOT
    CM --> COORD
    CM --> CODE
    CM --> PS

    %% Styling
    classDef primary fill:#3b82f6,stroke:#1e40af,stroke-width:3px,color:#fff
    classDef secondary fill:#10b981,stroke:#059669,stroke-width:2px,color:#fff
    classDef frontend fill:#f59e0b,stroke:#d97706,stroke-width:2px,color:#000
    classDef external fill:#8b5cf6,stroke:#6d28d9,stroke-width:2px,color:#fff
    classDef github fill:#ef4444,stroke:#dc2626,stroke-width:2px,color:#fff

    class SM primary
    class BOT,COORD,CODE secondary
    class DASH,UNIFIED frontend
    class OLLAMA,OPENAI,ANTHROPIC,GOOGLE external
    class GH_API,GH_ISSUES,GH_PRS,GH_REPOS github
```

## Component Descriptions

### Service Manager (Port 8080)
**Central orchestrator** that manages all services and agents. Provides REST API for external control.

**Key Responsibilities**:
- Start/stop all services
- Health monitoring
- Configuration management
- Graceful shutdown handling
- Systemd integration

### Core Services

#### Polling Service
- Polls GitHub repositories every 5 minutes
- Detects new issues assigned to bot accounts
- Triggers issue handler workflows
- Manages GitHub API rate limits

#### Monitor Service
- Tracks agent states (idle, working, error)
- Collects metrics (CPU, memory, API calls)
- Broadcasts state updates via WebSocket
- Stores historical data

#### WebSocket Handler (Port 7997)
- Real-time bidirectional communication
- Broadcasts agent state updates
- Streams logs to dashboards
- Handles multiple client connections

### Agents

#### Bot Agent
- **Purpose**: GitHub operations executor
- **LLM**: Any (GPT-4, Claude, Qwen)
- **Tasks**: Issue processing, branch creation, commits, PR management

#### Coordinator Agent
- **Purpose**: High-level orchestration
- **LLM**: High-capability models (GPT-4, Claude Opus)
- **Tasks**: Task distribution, workflow management, decision-making

#### Code Agent (Qwen)
- **Purpose**: Code generation and analysis
- **LLM**: Qwen 2.5 Coder (local via Ollama)
- **Tasks**: Code generation, refactoring, documentation

### Frontend (Port 8897)

#### dashboard.html ⭐ **DEFAULT**
- Main entry point after `index.html` redirect
- Agent overview and basic monitoring
- Live status indicators
- Quick actions

#### unified_dashboard.html (NEW)
- Modern unified interface
- Agent configuration modal
- Real-time log streaming
- Sliding sidebar for settings

#### monitoring_dashboard.html
- Classic monitoring view
- Detailed metrics and graphs
- Historical data visualization

#### config_ui.html
- YAML configuration editor
- Agent settings management
- Validation and apply

## Data Flow Paths

### Issue Processing Flow
```
GitHub Issue → Polling Service → Issue Handler → Bot Agent → Code Agent → Git Operations → GitHub API
```

### Monitoring Flow
```
Agent State Change → Monitor Service → WebSocket Handler → Frontend Dashboards
```

### Configuration Flow
```
config_ui.html → REST API (/api/config) → Config Manager → Service Manager → Agents Reload
```

## Port Allocation

| Port | Service | Protocol | Access |
|------|---------|----------|--------|
| **8080** | Service Manager | HTTP | REST API |
| **7997** | WebSocket | WebSocket | Real-time updates |
| **8897** | Frontend | HTTP | Dashboard hosting |
| 11434 | Ollama | HTTP | Local LLM inference |

## Network Topology

```
┌─────────────────────────────────────────┐
│  LAN Network (192.168.1.x)              │
│                                         │
│  ┌─────────────┐      ┌──────────────┐ │
│  │ Your PC     │      │ Other Device │ │
│  │ Agent-Forge │◄────►│ Browser      │ │
│  │             │      │              │ │
│  │ 0.0.0.0:8897│      │              │ │
│  │ 0.0.0.0:7997│      │              │ │
│  └─────────────┘      └──────────────┘ │
│         │                               │
└─────────┼───────────────────────────────┘
          │
          ▼
    ┌──────────┐
    │ Internet │
    │ GitHub   │
    └──────────┘
```

## Technology Stack

### Backend
- **Language**: Python 3.12+
- **Async**: asyncio, aiohttp
- **WebSocket**: FastAPI WebSockets
- **LLM**: Ollama (local), OpenAI API, Anthropic API

### Frontend
- **HTML/CSS/JavaScript**: Vanilla (no frameworks)
- **WebSocket**: Native WebSocket API
- **Styling**: Custom CSS with dark theme

### Infrastructure
- **Process Manager**: systemd
- **Logging**: Python logging + systemd journal
- **Config**: YAML files
- **Git**: GitPython

## Related Diagrams

- [Data Flow Diagram](data-flow.md) - Detailed data flow through the system
- [Component Interactions](component-interactions.md) - How components communicate

## See Also

- [ARCHITECTURE.md](../../ARCHITECTURE.md) - Complete architecture documentation
- [AGENT_ONBOARDING.md](../AGENT_ONBOARDING.md) - Quick start for new agents
- [PORT_REFERENCE.md](../PORT_REFERENCE.md) - Port allocation guide

---

**Last Updated**: 2025-10-06  
**Maintained by**: Agent-Forge Team
