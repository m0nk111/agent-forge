# Agent-Forge Data Flow

> **Detailed data flow diagrams showing how information moves through the system**

## Table of Contents

1. [Issue Processing Flow](#issue-processing-flow)
2. [Monitoring Data Flow](#monitoring-data-flow)
3. [Configuration Flow](#configuration-flow)
4. [WebSocket Message Flow](#websocket-message-flow)
5. [Git Operations Flow](#git-operations-flow)

---

## Issue Processing Flow

### Complete Issue Lifecycle

```mermaid
sequenceDiagram
    participant User
    participant GitHub
    participant Polling
    participant IssueHandler
    participant BotAgent
    participant CodeAgent
    participant GitOps
    participant Monitor
    participant WebSocket
    participant Dashboard

    User->>GitHub: Create Issue
    Note over GitHub: Issue assigned to bot account
    
    loop Every 5 minutes
        Polling->>GitHub: Poll for new issues
        GitHub-->>Polling: Return assigned issues
    end
    
    Polling->>IssueHandler: New issue detected
    IssueHandler->>IssueHandler: Validate & parse
    IssueHandler->>BotAgent: Assign issue
    
    BotAgent->>Monitor: Update state: "working"
    Monitor->>WebSocket: Broadcast state change
    WebSocket->>Dashboard: Display agent working
    
    BotAgent->>GitOps: Create feature branch
    GitOps->>GitHub: git checkout -b feature/issue-123
    
    BotAgent->>CodeAgent: Request code solution
    CodeAgent->>CodeAgent: Analyze requirements
    CodeAgent->>CodeAgent: Generate code (Qwen LLM)
    CodeAgent-->>BotAgent: Return solution
    
    BotAgent->>GitOps: Apply code changes
    GitOps->>GitOps: Modify files
    GitOps->>GitHub: git commit & push
    
    BotAgent->>GitHub: Create Pull Request
    GitHub-->>BotAgent: PR #456 created
    
    BotAgent->>GitHub: Comment on issue
    Note over GitHub: "Created PR #456"
    
    BotAgent->>Monitor: Update state: "idle"
    Monitor->>WebSocket: Broadcast completion
    WebSocket->>Dashboard: Show agent idle
    
    GitHub->>User: Notify PR created
```

### Issue Processing States

```mermaid
stateDiagram-v2
    [*] --> Detected: Polling finds issue
    Detected --> Validated: IssueHandler checks
    Validated --> Assigned: Bot accepts task
    Assigned --> InProgress: Creating branch
    InProgress --> Coding: Generating solution
    Coding --> Testing: Running tests
    Testing --> CommitReview: Self-review
    CommitReview --> PullRequest: Create PR
    PullRequest --> Completed: Update issue
    Completed --> [*]
    
    Validated --> Rejected: Invalid format
    Coding --> Failed: Generation error
    Testing --> Failed: Tests fail
    Failed --> InProgress: Retry
    Rejected --> [*]
```

---

## Monitoring Data Flow

### Real-Time Agent State Updates

```mermaid
flowchart TD
    subgraph "Agent Layer"
        BA[Bot Agent]
        CA[Coordinator Agent]
        QA[Code Agent]
    end
    
    subgraph "Monitoring Layer"
        MS[Monitor Service]
        STATE[(Agent States)]
        METRICS[(Metrics DB)]
    end
    
    subgraph "Communication Layer"
        WS[WebSocket Handler<br/>Port 7997]
    end
    
    subgraph "Frontend Layer"
        DASH[dashboard.html]
        UNIFIED[unified_dashboard.html]
        MONITOR[monitoring_dashboard.html]
    end
    
    BA -->|update_agent()| MS
    CA -->|update_agent()| MS
    QA -->|update_agent()| MS
    
    MS --> STATE
    MS --> METRICS
    
    MS -->|broadcast()| WS
    
    WS -->|agent_state message| DASH
    WS -->|agent_state message| UNIFIED
    WS -->|agent_state message| MONITOR
    
    DASH -->|render| USER1[User Browser 1]
    UNIFIED -->|render| USER2[User Browser 2]
    MONITOR -->|render| USER3[User Browser 3]
```

### Log Streaming Flow

```mermaid
sequenceDiagram
    participant Agent
    participant Logger
    participant MonitorService
    participant WebSocket
    participant Dashboard

    Agent->>Logger: logger.info("Processing task")
    Logger->>MonitorService: Send log entry
    
    MonitorService->>MonitorService: Format log
    Note over MonitorService: Add timestamp<br/>Add agent_id<br/>Add level
    
    MonitorService->>WebSocket: broadcast_log()
    
    WebSocket->>Dashboard: WebSocket message
    Note over Dashboard: type: "log"<br/>data: {<br/>  timestamp: 1696000000,<br/>  agent_id: "bot-1",<br/>  level: "INFO",<br/>  message: "Processing task"<br/>}
    
    Dashboard->>Dashboard: Append to log container
    Dashboard->>Dashboard: Auto-scroll if enabled
```

---

## Configuration Flow

### Configuration Update Process

```mermaid
flowchart TD
    START([User opens config_ui.html]) --> LOAD
    LOAD[Load current config] --> EDIT
    EDIT[Edit YAML] --> VALIDATE
    VALIDATE{Valid?}
    
    VALIDATE -->|No| ERROR[Show errors]
    ERROR --> EDIT
    
    VALIDATE -->|Yes| SEND[POST /api/config]
    SEND --> SERVER[Service Manager]
    
    SERVER --> CM[Config Manager]
    CM --> PARSE[Parse YAML]
    PARSE --> CHECK{Validation}
    
    CHECK -->|Fail| REJECT[Return 400]
    REJECT --> ERROR2[Display error]
    ERROR2 --> EDIT
    
    CHECK -->|Pass| BACKUP[Backup old config]
    BACKUP --> SAVE[Save to config/agents/*.yaml]
    SAVE --> RELOAD[Reload agents]
    
    RELOAD --> BA[Restart Bot Agent]
    RELOAD --> CA[Restart Coordinator]
    RELOAD --> QA[Restart Code Agent]
    
    BA --> SUCCESS[Return 200]
    CA --> SUCCESS
    QA --> SUCCESS
    
    SUCCESS --> NOTIFY[Show success message]
    NOTIFY --> REFRESH[Refresh UI]
    REFRESH --> END([Configuration applied])
```

### Config File Hierarchy

```mermaid
graph TD
    ENV[Environment Variables] --> RUNTIME
    
    subgraph "Config Files"
        SYSTEM[config/system.yaml]
        AGENTS[config/agents/*.yaml]
        BOT[config/bot_config.yaml]
        COORD[config/coordinator_config.yaml]
        REPOS[config/repositories.yaml]
    end
    
    SYSTEM --> RUNTIME[Runtime Configuration]
    AGENTS --> RUNTIME
    BOT --> RUNTIME
    COORD --> RUNTIME
    REPOS --> RUNTIME
    
    RUNTIME --> SM[Service Manager]
    SM --> SERVICES[All Services]
    
    style ENV fill:#f59e0b
    style RUNTIME fill:#10b981
```

---

## WebSocket Message Flow

### Message Types and Flow

```mermaid
flowchart LR
    subgraph "Backend (Port 7997)"
        WS_SERVER[WebSocket Server]
        HANDLERS[Message Handlers]
    end
    
    subgraph "Message Types"
        AGENT_STATE[agent_state<br/>Agent status updates]
        LOG[log<br/>Log entries]
        SYSTEM[system<br/>System events]
        HEARTBEAT[heartbeat<br/>Keep-alive]
    end
    
    subgraph "Frontend Clients"
        DASH[dashboard.html]
        UNIFIED[unified_dashboard.html]
        MONITOR[monitoring_dashboard.html]
    end
    
    WS_SERVER --> AGENT_STATE
    WS_SERVER --> LOG
    WS_SERVER --> SYSTEM
    WS_SERVER --> HEARTBEAT
    
    AGENT_STATE --> DASH
    AGENT_STATE --> UNIFIED
    AGENT_STATE --> MONITOR
    
    LOG --> DASH
    LOG --> UNIFIED
    LOG --> MONITOR
    
    SYSTEM --> DASH
    SYSTEM --> UNIFIED
    SYSTEM --> MONITOR
    
    HEARTBEAT --> DASH
    HEARTBEAT --> UNIFIED
    HEARTBEAT --> MONITOR
    
    DASH --> |Ack| WS_SERVER
    UNIFIED --> |Ack| WS_SERVER
    MONITOR --> |Ack| WS_SERVER
```

### WebSocket Connection Lifecycle

```mermaid
stateDiagram-v2
    [*] --> Connecting: Dashboard loads
    Connecting --> Trying: ws://host:7997/ws/monitor
    
    Trying --> Connected: onopen event
    Trying --> Retry: onerror event
    
    Retry --> Trying: After 5s delay
    
    Connected --> Receiving: onmessage event
    Receiving --> Connected: Process message
    
    Connected --> Disconnected: onclose event
    Disconnected --> Trying: Reconnect
    
    Connected --> [*]: User closes tab
```

---

## Git Operations Flow

### Branch and Commit Flow

```mermaid
sequenceDiagram
    participant BA as Bot Agent
    participant GO as Git Operations
    participant Local as Local Repo
    participant Remote as GitHub Remote

    BA->>GO: create_branch("feature/issue-123")
    GO->>Local: git fetch origin
    Local-->>GO: Latest refs
    
    GO->>Local: git checkout main
    GO->>Local: git pull origin main
    GO->>Local: git checkout -b feature/issue-123
    GO-->>BA: Branch created
    
    BA->>GO: modify_files([file1, file2])
    GO->>Local: Write changes
    
    BA->>GO: commit("feat: implement feature")
    GO->>Local: git add .
    GO->>Local: git commit -m "feat: implement feature"
    GO-->>BA: Commit created
    
    BA->>GO: push_branch()
    GO->>Remote: git push origin feature/issue-123
    Remote-->>GO: Push successful
    GO-->>BA: Branch pushed
    
    BA->>Remote: Create Pull Request via API
    Remote-->>BA: PR #456 created
```

### Pull Request Review Flow

```mermaid
flowchart TD
    PR_CREATED[PR Created] --> WEBHOOK[GitHub Webhook]
    WEBHOOK --> POLLING[Polling detects]
    POLLING --> REVIEWER[PR Reviewer Agent]
    
    REVIEWER --> FETCH[Fetch PR diff]
    FETCH --> ANALYZE[Analyze changes]
    
    ANALYZE --> CHECK_STYLE[Check code style]
    ANALYZE --> CHECK_TESTS[Check tests]
    ANALYZE --> CHECK_DOCS[Check docs]
    
    CHECK_STYLE --> SCORE[Calculate score]
    CHECK_TESTS --> SCORE
    CHECK_DOCS --> SCORE
    
    SCORE --> DECISION{Score >= 7?}
    
    DECISION -->|Yes| APPROVE[Post approval]
    DECISION -->|No| REQUEST[Request changes]
    
    APPROVE --> COMMENT_A[Add positive comments]
    REQUEST --> COMMENT_R[Add improvement suggestions]
    
    COMMENT_A --> DONE[Review complete]
    COMMENT_R --> DONE
```

---

## Data Persistence

### Storage Locations

```mermaid
graph TD
    subgraph "Configuration"
        C1[config/system.yaml]
        C2[config/agents/*.yaml]
        C3[config/bot_config.yaml]
    end
    
    subgraph "Runtime Data"
        R1[Agent States<br/>In-Memory]
        R2[Metrics<br/>In-Memory]
        R3[Logs<br/>stdout/stderr]
    end
    
    subgraph "Persistent Storage"
        P1[config/backups/]
        P2[logs/]
        P3[.git/]
    end
    
    C1 --> P1
    C2 --> P1
    C3 --> P1
    
    R3 --> P2
    
    style R1 fill:#f59e0b
    style R2 fill:#f59e0b
    style P1 fill:#10b981
    style P2 fill:#10b981
    style P3 fill:#10b981
```

---

## Performance Considerations

### Rate Limiting Flow

```mermaid
flowchart TD
    REQUEST[Agent makes API call] --> CHECK{Rate limit OK?}
    
    CHECK -->|Yes| EXECUTE[Execute request]
    CHECK -->|No| WAIT[Wait/backoff]
    
    WAIT --> CHECK
    
    EXECUTE --> UPDATE[Update counter]
    UPDATE --> SUCCESS{Success?}
    
    SUCCESS -->|Yes| DONE[Return response]
    SUCCESS -->|No| RETRY{Retry?}
    
    RETRY -->|Yes| BACKOFF[Exponential backoff]
    RETRY -->|No| FAIL[Return error]
    
    BACKOFF --> EXECUTE
```

### Caching Strategy

```mermaid
graph LR
    REQ[Request] --> CACHE{In cache?}
    
    CACHE -->|Yes| VALID{Still valid?}
    CACHE -->|No| FETCH[Fetch from source]
    
    VALID -->|Yes| RETURN[Return cached]
    VALID -->|No| FETCH
    
    FETCH --> STORE[Store in cache]
    STORE --> RETURN
```

---

## Related Documentation

- [Architecture Overview](architecture-overview.md) - System architecture diagram
- [Component Interactions](component-interactions.md) - Component communication
- [ARCHITECTURE.md](../../ARCHITECTURE.md) - Complete architecture guide

---

**Last Updated**: 2025-10-06  
**Maintained by**: Agent-Forge Team
