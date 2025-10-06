# Agent-Forge System Diagrams - Enterprise Edition

> **Complete visual documentation of Agent-Forge multi-agent platform**

## 📋 Diagram Index

1. [High-Level System Architecture](#high-level-system-architecture)
2. [Deployment Architecture](#deployment-architecture)
3. [Agent Lifecycle State Machine](#agent-lifecycle-state-machine)
4. [Request Flow Sequence](#request-flow-sequence)
5. [WebSocket Communication](#websocket-communication)
6. [Configuration Management](#configuration-management)
7. [Error Handling Flow](#error-handling-flow)
8. [Security Architecture](#security-architecture)
9. [Database Schema](#database-schema)
10. [CI/CD Pipeline](#cicd-pipeline)

---

## 1. High-Level System Architecture

```mermaid
C4Context
    title System Context - Agent-Forge Multi-Agent Platform

    Person(user, "Developer", "Interacts with dashboard")
    Person(maintainer, "Maintainer", "Monitors system health")
    
    System_Boundary(agentforge, "Agent-Forge") {
        System(web, "Web Dashboard", "React/Vite frontend")
        System(api, "REST API", "FastAPI backend")
        System(agents, "Agent System", "Multi-agent orchestration")
        System(ws, "WebSocket Server", "Real-time updates")
    }
    
    System_Ext(github, "GitHub", "Issue tracking & PR management")
    System_Ext(ollama, "Ollama", "Local LLM inference")
    
    Rel(user, web, "Views agents & metrics")
    Rel(maintainer, web, "Monitors system")
    Rel(web, api, "REST calls", "HTTPS")
    Rel(web, ws, "Real-time updates", "WebSocket")
    Rel(api, agents, "Task assignment")
    Rel(agents, github, "GitHub operations", "REST API")
    Rel(agents, ollama, "Code generation", "HTTP")
    Rel(ws, agents, "State changes")
```

---

## 2. Deployment Architecture

### 2.1 Development Deployment

```mermaid
graph TB
    subgraph "Developer Machine"
        subgraph "Terminal"
            CLI[python -m agents.service_manager]
        end
        
        subgraph "Service Manager Process"
            SM[Service Manager<br/>:8080]
            WS[WebSocket<br/>:7997]
            FRONT[Frontend<br/>:8897]
        end
        
        subgraph "Agents"
            BOT[Bot Agent]
            CODE[Code Agent]
            COORD[Coordinator]
        end
        
        subgraph "Local Services"
            OLLAMA[Ollama<br/>:11434]
            DB[(SQLite DB)]
        end
    end
    
    CLI --> SM
    SM --> BOT
    SM --> CODE
    SM --> COORD
    CODE --> OLLAMA
    SM --> DB
    
    subgraph "External"
        GITHUB[GitHub API]
    end
    
    BOT --> GITHUB
    
    USER[Browser] --> FRONT
    USER --> WS
    USER --> SM
```

### 2.2 Production Deployment (Systemd)

```mermaid
graph TB
    subgraph "Linux Server"
        subgraph "Systemd"
            SERVICE[agent-forge.service]
            WATCHDOG[Systemd Watchdog]
        end
        
        subgraph "Nginx Reverse Proxy :80/:443"
            NGINX[Nginx]
            SSL[SSL/TLS<br/>Let's Encrypt]
        end
        
        subgraph "Agent-Forge Process"
            SM[Service Manager<br/>127.0.0.1:8080]
            WS[WebSocket<br/>127.0.0.1:7997]
            FRONT[Frontend<br/>127.0.0.1:8897]
        end
        
        subgraph "Agents"
            BOT[Bot Agent]
            CODE[Code Agent]
            COORD[Coordinator]
            POLL[Polling Service]
        end
        
        subgraph "Data"
            DB[(SQLite DB<br/>WAL Mode)]
            LOGS[Log Files<br/>Rotation]
            CONFIG[YAML Config<br/>.env]
        end
        
        subgraph "Local LLM"
            OLLAMA[Ollama Service<br/>:11434]
        end
    end
    
    SERVICE --> SM
    WATCHDOG -.->|monitors| SERVICE
    
    NGINX --> SM
    NGINX --> WS
    NGINX --> FRONT
    SSL --> NGINX
    
    SM --> BOT
    SM --> CODE
    SM --> COORD
    SM --> POLL
    
    POLL -->|detects issues| BOT
    CODE --> OLLAMA
    
    SM --> DB
    SM --> LOGS
    SM --> CONFIG
    
    subgraph "Internet"
        USER[Users<br/>HTTPS]
        GITHUB[GitHub API]
        LETSENCRYPT[Let's Encrypt]
    end
    
    USER --> SSL
    BOT --> GITHUB
    SSL -.->|renewal| LETSENCRYPT
```

### 2.3 Docker Deployment (Planned)

```mermaid
graph TB
    subgraph "Docker Compose"
        subgraph "agent-forge container"
            SM[Service Manager]
            AGENTS[Agents]
            FRONT[Frontend]
        end
        
        subgraph "ollama container"
            OLLAMA[Ollama Service]
            MODELS[Models Volume]
        end
        
        subgraph "nginx container"
            NGINX[Nginx<br/>Reverse Proxy]
        end
        
        subgraph "Volumes"
            CONFIG[config/]
            DATA[data/]
            LOGS[logs/]
        end
    end
    
    NGINX --> SM
    AGENTS --> OLLAMA
    SM --> CONFIG
    SM --> DATA
    SM --> LOGS
    OLLAMA --> MODELS
    
    USER[External Users] --> NGINX
    AGENTS --> GITHUB[GitHub API]
```

---

## 3. Agent Lifecycle State Machine

```mermaid
stateDiagram-v2
    [*] --> Created: Agent Initialized
    
    Created --> Idle: Start Agent
    
    Idle --> Working: Task Assigned
    Idle --> Stopped: Stop Command
    
    Working --> Processing: Fetch Issue Details
    Processing --> CodeGeneration: Request Solution
    CodeGeneration --> Committing: Apply Changes
    Committing --> PRCreation: Push Branch
    PRCreation --> Idle: Success
    
    Working --> Error: Exception
    Processing --> Error: API Failure
    CodeGeneration --> Error: LLM Error
    Committing --> Error: Git Failure
    PRCreation --> Error: GitHub Error
    
    Error --> Idle: Retry Exhausted
    Error --> Working: Retry Attempt
    
    Stopped --> Idle: Restart
    Stopped --> [*]: Terminate
    
    note right of Idle
        Agent ready for tasks
        Monitoring enabled
        Resource cleanup
    end note
    
    note right of Working
        Task in progress
        Resource allocated
        Timeout monitoring
    end note
    
    note right of Error
        Error logged
        Retry logic active
        Notifications sent
    end note
```

---

## 4. Request Flow Sequence

### 4.1 Issue Processing Flow

```mermaid
sequenceDiagram
    participant P as Polling Service
    participant GH as GitHub API
    participant C as Coordinator
    participant B as Bot Agent
    participant CA as Code Agent
    participant O as Ollama
    participant M as Monitor Service
    participant WS as WebSocket
    participant UI as Dashboard
    
    loop Every 5 minutes
        P->>GH: GET /repos/{owner}/{repo}/issues
        GH-->>P: Issue list
    end
    
    P->>P: Filter assigned issues
    P->>C: New issue detected #42
    
    C->>B: Assign issue #42
    B->>M: Update state: working
    M->>WS: Broadcast state change
    WS-->>UI: Real-time update
    
    B->>GH: GET /repos/{owner}/{repo}/issues/42
    GH-->>B: Issue details
    
    B->>CA: Request solution
    CA->>O: Generate code for issue
    O-->>CA: Generated code
    CA-->>B: Solution ready
    
    B->>GH: POST /repos/{owner}/{repo}/git/refs
    GH-->>B: Branch created
    
    B->>GH: PUT /repos/{owner}/{repo}/contents/{path}
    GH-->>B: File committed
    
    B->>GH: POST /repos/{owner}/{repo}/pulls
    GH-->>B: PR created #15
    
    B->>GH: POST /repos/{owner}/{repo}/issues/42/comments
    GH-->>B: Comment added
    
    B->>M: Update state: idle
    M->>WS: Broadcast completion
    WS-->>UI: Task completed notification
```

### 4.2 Manual Task Assignment

```mermaid
sequenceDiagram
    participant U as User
    participant D as Dashboard
    participant API as REST API
    participant SM as Service Manager
    participant B as Bot Agent
    participant M as Monitor
    participant WS as WebSocket
    
    U->>D: Assign issue #42 to bot-1
    D->>API: POST /agents/bot-1/assign
    Note over D,API: {repo: "owner/repo", issue: 42}
    
    API->>SM: Validate request
    SM->>SM: Check agent availability
    
    alt Agent available
        SM->>B: Assign task
        B->>M: State: working
        SM-->>API: {status: "assigned"}
        API-->>D: Success response
        D-->>U: Task assigned
        
        M->>WS: Broadcast state
        WS-->>D: Real-time update
        
        B->>B: Process issue
        B->>M: State: idle
        M->>WS: Broadcast completion
        WS-->>D: Task completed
    else Agent busy
        SM-->>API: {error: "agent_busy"}
        API-->>D: Error response
        D-->>U: Agent is busy
    end
```

---

## 5. WebSocket Communication

```mermaid
sequenceDiagram
    participant C as Client Browser
    participant WS as WebSocket Server
    participant M as Monitor Service
    participant A as Agent
    
    C->>WS: Connect ws://localhost:7997/ws/monitor
    WS-->>C: Connection established
    
    WS->>C: {type: "system", event: "connected"}
    
    loop Every 30 seconds
        C->>WS: {type: "ping"}
        WS-->>C: {type: "pong"}
    end
    
    A->>M: State change: working
    M->>WS: New state data
    WS->>C: {type: "agent_state", data: {...}}
    
    A->>M: Log entry: INFO
    M->>WS: New log entry
    WS->>C: {type: "log", data: {...}}
    
    A->>M: Task completed
    M->>WS: Task completion
    WS->>C: {type: "agent_state", status: "idle"}
    
    Note over C,WS: Connection lost
    C->>WS: Reconnect attempt
    WS-->>C: Connection re-established
    WS->>C: State sync (all current states)
```

### WebSocket Message Types

```mermaid
graph LR
    subgraph "Client → Server"
        PING[ping<br/>Heartbeat]
        SUB[subscribe<br/>Agent filter]
        UNSUB[unsubscribe<br/>Stop updates]
    end
    
    subgraph "Server → Client"
        PONG[pong<br/>Heartbeat response]
        STATE[agent_state<br/>Agent status update]
        LOG[log<br/>Log entry]
        SYS[system<br/>System event]
        METRIC[metric<br/>Performance data]
    end
    
    PING --> PONG
    SUB --> STATE
    SUB --> LOG
    UNSUB -.->|stops| STATE
```

---

## 6. Configuration Management

```mermaid
graph TB
    subgraph "Configuration Sources"
        ENV[.env File<br/>Secrets & Tokens]
        YAML[YAML Files<br/>config/*.yaml]
        ARGS[CLI Arguments<br/>--port, --debug]
        DEFAULT[Default Values<br/>Hardcoded]
    end
    
    subgraph "Config Manager"
        CM[ConfigManager]
        VALIDATOR[Schema Validator]
        MERGER[Config Merger]
    end
    
    subgraph "Priority Order"
        P1[1. CLI Arguments]
        P2[2. Environment Variables]
        P3[3. YAML Files]
        P4[4. Default Values]
    end
    
    ENV --> CM
    YAML --> CM
    ARGS --> CM
    DEFAULT --> CM
    
    CM --> VALIDATOR
    VALIDATOR --> MERGER
    
    MERGER --> P1
    P1 --> P2
    P2 --> P3
    P3 --> P4
    
    P4 --> FINAL[Final Configuration]
    
    subgraph "Consumers"
        SM[Service Manager]
        AGENTS[Agents]
        SERVICES[Services]
    end
    
    FINAL --> SM
    FINAL --> AGENTS
    FINAL --> SERVICES
    
    subgraph "Runtime Updates"
        API[REST API<br/>PUT /config]
        RELOAD[Config Reload]
        RESTART[Service Restart]
    end
    
    API --> VALIDATOR
    VALIDATOR --> RELOAD
    RELOAD --> RESTART
    RESTART --> SM
```

---

## 7. Error Handling Flow

```mermaid
graph TB
    START[Operation Started] --> TRY[Try Operation]
    
    TRY --> SUCCESS{Success?}
    SUCCESS -->|Yes| LOG_SUCCESS[Log Success]
    SUCCESS -->|No| CATCH[Catch Exception]
    
    CATCH --> CLASSIFY[Classify Error]
    
    CLASSIFY --> RETRYABLE{Retryable?}
    
    RETRYABLE -->|Yes| CHECK_RETRY{Retry<br/>Attempts<br/>Exhausted?}
    CHECK_RETRY -->|No| BACKOFF[Exponential Backoff]
    BACKOFF --> DELAY[Wait]
    DELAY --> TRY
    
    CHECK_RETRY -->|Yes| PERMANENT_FAIL[Permanent Failure]
    RETRYABLE -->|No| PERMANENT_FAIL
    
    PERMANENT_FAIL --> LOG_ERROR[Log Error]
    LOG_ERROR --> NOTIFY[Send Notifications]
    NOTIFY --> UPDATE_STATE[Update Agent State]
    UPDATE_STATE --> CLEANUP[Cleanup Resources]
    
    LOG_SUCCESS --> END[Operation Complete]
    CLEANUP --> END
    
    subgraph "Error Types"
        RT[Rate Limit<br/>Retry: Yes<br/>Backoff: Exponential]
        NET[Network Error<br/>Retry: Yes<br/>Backoff: Linear]
        AUTH[Auth Error<br/>Retry: No<br/>Action: Alert]
        VAL[Validation Error<br/>Retry: No<br/>Action: Log]
    end
    
    subgraph "Notification Channels"
        LOGS[Log Files]
        WS_NOTIF[WebSocket]
        EMAIL[Email<br/>Future]
        SLACK[Slack<br/>Future]
    end
    
    NOTIFY --> LOGS
    NOTIFY --> WS_NOTIF
    NOTIFY -.-> EMAIL
    NOTIFY -.-> SLACK
```

---

## 8. Security Architecture

```mermaid
graph TB
    subgraph "External Threats"
        ATTACKER[Potential Attacker]
        BOT_TRAFFIC[Bot Traffic]
    end
    
    subgraph "Network Security Layer"
        FW[Firewall<br/>ufw/iptables]
        NGINX[Nginx Reverse Proxy]
        SSL[SSL/TLS<br/>Let's Encrypt]
        RATE[Rate Limiting]
    end
    
    subgraph "Application Security Layer"
        AUTH[Authentication<br/>TODO: API Keys]
        AUTHZ[Authorization<br/>TODO: RBAC]
        INPUT_VAL[Input Validation]
        SANITIZE[Data Sanitization]
    end
    
    subgraph "Service Security"
        SYSTEMD[Systemd Sandbox]
        NO_ROOT[Non-root User]
        PRIV[PrivateTmp]
        PROTECT[ProtectSystem]
    end
    
    subgraph "Data Security"
        ENV_SECRET[.env Secrets<br/>chmod 600]
        TOKEN[GitHub Tokens<br/>Encrypted Storage]
        DB_PERM[Database Permissions<br/>chmod 600]
        LOG_ROTATE[Log Rotation]
    end
    
    subgraph "Agent-Forge Application"
        APP[Application Code]
    end
    
    ATTACKER --> FW
    BOT_TRAFFIC --> FW
    
    FW --> NGINX
    NGINX --> SSL
    SSL --> RATE
    
    RATE --> AUTH
    AUTH --> AUTHZ
    AUTHZ --> INPUT_VAL
    INPUT_VAL --> SANITIZE
    
    SANITIZE --> APP
    
    APP --> SYSTEMD
    SYSTEMD --> NO_ROOT
    NO_ROOT --> PRIV
    PRIV --> PROTECT
    
    APP --> ENV_SECRET
    APP --> TOKEN
    APP --> DB_PERM
    APP --> LOG_ROTATE
    
    subgraph "Security Headers"
        CSP[Content-Security-Policy]
        HSTS[Strict-Transport-Security]
        XFO[X-Frame-Options]
        XCT[X-Content-Type-Options]
    end
    
    NGINX --> CSP
    NGINX --> HSTS
    NGINX --> XFO
    NGINX --> XCT
```

---

## 9. Database Schema

```mermaid
erDiagram
    AGENTS ||--o{ TASKS : processes
    AGENTS ||--o{ LOGS : generates
    TASKS ||--o{ TASK_HISTORY : has
    REPOSITORIES ||--o{ TASKS : contains
    
    AGENTS {
        string id PK
        string name
        string type
        string model
        string status
        string mode
        timestamp created_at
        timestamp last_active
        int tasks_completed
        int tasks_failed
    }
    
    TASKS {
        int id PK
        string agent_id FK
        string repo FK
        int issue_number
        string status
        string priority
        timestamp assigned_at
        timestamp started_at
        timestamp completed_at
        text error_message
        int retry_count
    }
    
    TASK_HISTORY {
        int id PK
        int task_id FK
        string status
        string event
        text details
        timestamp occurred_at
    }
    
    LOGS {
        int id PK
        string agent_id FK
        string level
        text message
        text details
        timestamp created_at
    }
    
    REPOSITORIES {
        string full_name PK
        bool polling_enabled
        int polling_interval
        string assignees
        timestamp last_poll
    }
    
    CONFIGURATION {
        string key PK
        text value
        string type
        timestamp updated_at
    }
```

---

## 10. CI/CD Pipeline

```mermaid
graph TB
    subgraph "Developer Workflow"
        DEV[Developer]
        FORK[Fork Repository]
        BRANCH[Create Feature Branch]
        CODE[Write Code]
        TEST_LOCAL[Run Tests Locally]
        COMMIT[Commit Changes]
        PUSH[Push to Fork]
        PR[Create Pull Request]
    end
    
    subgraph "GitHub Actions - PR Checks"
        TRIGGER[PR Trigger]
        
        subgraph "Lint & Format"
            RUFF[Ruff Linting]
            BLACK[Black Formatting]
            MYPY[Type Checking]
        end
        
        subgraph "Testing"
            UNIT[Unit Tests<br/>pytest]
            INTEGRATION[Integration Tests]
            COVERAGE[Coverage Report<br/>Codecov]
        end
        
        subgraph "Security"
            DEPS[Dependency Check]
            SECRETS[Secret Scanning]
        end
        
        CHECKS_PASS{All Checks Pass?}
    end
    
    subgraph "Code Review"
        REVIEW[Human Review]
        COPILOT[Copilot Review]
        APPROVE{Approved?}
    end
    
    subgraph "Merge & Deploy"
        MERGE[Squash Merge]
        TAG[Create Tag]
        
        subgraph "Deployment"
            BUILD[Build Package]
            TEST_DEPLOY[Test Deployment]
            PROD_DEPLOY[Production Deploy]
        end
        
        RELEASE[GitHub Release]
        CHANGELOG[Update Changelog]
    end
    
    DEV --> FORK
    FORK --> BRANCH
    BRANCH --> CODE
    CODE --> TEST_LOCAL
    TEST_LOCAL --> COMMIT
    COMMIT --> PUSH
    PUSH --> PR
    
    PR --> TRIGGER
    TRIGGER --> RUFF
    TRIGGER --> BLACK
    TRIGGER --> MYPY
    TRIGGER --> UNIT
    TRIGGER --> INTEGRATION
    TRIGGER --> COVERAGE
    TRIGGER --> DEPS
    TRIGGER --> SECRETS
    
    RUFF --> CHECKS_PASS
    BLACK --> CHECKS_PASS
    MYPY --> CHECKS_PASS
    UNIT --> CHECKS_PASS
    INTEGRATION --> CHECKS_PASS
    COVERAGE --> CHECKS_PASS
    DEPS --> CHECKS_PASS
    SECRETS --> CHECKS_PASS
    
    CHECKS_PASS -->|No| NOTIFY_FAIL[Notify Developer]
    NOTIFY_FAIL --> CODE
    
    CHECKS_PASS -->|Yes| REVIEW
    REVIEW --> COPILOT
    COPILOT --> APPROVE
    
    APPROVE -->|No| CODE
    APPROVE -->|Yes| MERGE
    
    MERGE --> TAG
    TAG --> BUILD
    BUILD --> TEST_DEPLOY
    TEST_DEPLOY --> PROD_DEPLOY
    
    PROD_DEPLOY --> RELEASE
    RELEASE --> CHANGELOG
    
    CHANGELOG --> DONE[Deployment Complete]
```

---

## Usage Guide

### Viewing Diagrams

1. **GitHub**: Diagrams render automatically in Markdown
2. **VS Code**: Install "Markdown Preview Mermaid Support" extension
3. **Documentation Sites**: Use mermaid.js integration
4. **Export**: Use mermaid-cli to export as PNG/SVG

### Updating Diagrams

When system architecture changes:

1. Update relevant diagram(s) in this file
2. Update ARCHITECTURE.md references
3. Commit with descriptive message
4. Update CHANGELOG.md

### Diagram Conventions

- **Solid arrows** (→): Direct dependencies/calls
- **Dashed arrows** (-.->): Optional/conditional
- **Bold boxes**: Critical components
- **Subgraphs**: Logical grouping
- **Colors**: (When rendered)
  - Blue: External systems
  - Green: Services
  - Orange: Data stores
  - Red: Security/error paths

---

**Last Updated**: October 6, 2025  
**Diagram Count**: 10 core diagrams + 3 existing = 13 total  
**Coverage**: Complete system visualization
