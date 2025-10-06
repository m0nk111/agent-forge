# Agent-Forge Component Interactions

> **Detailed diagrams showing how components communicate and orchestrate**

## Table of Contents

1. [Service Manager Orchestration](#service-manager-orchestration)
2. [Agent Communication Patterns](#agent-communication-patterns)
3. [Configuration Management](#configuration-management)
4. [Monitoring Integration](#monitoring-integration)
5. [Error Handling Flow](#error-handling-flow)

---

## Service Manager Orchestration

### Service Lifecycle Management

```mermaid
graph TD
    START([Service Manager Starts]) --> INIT
    
    subgraph "Initialization Phase"
        INIT[Load Configuration]
        INIT --> VALIDATE[Validate Config]
        VALIDATE --> SETUP[Setup Logging]
        SETUP --> NOTIFY[Notify Systemd Ready]
    end
    
    NOTIFY --> SERVICES
    
    subgraph "Service Orchestration"
        SERVICES[Start All Services]
        
        SERVICES --> PS[Polling Service]
        SERVICES --> MS[Monitor Service]
        SERVICES --> WS[WebSocket Handler]
        SERVICES --> CA[Code Agent]
        
        PS --> HEALTH1[Health Check Loop]
        MS --> HEALTH1
        WS --> HEALTH1
        CA --> HEALTH1
        
        HEALTH1 --> WATCHDOG[Systemd Watchdog]
    end
    
    WATCHDOG --> RUNNING[Running State]
    
    RUNNING --> SIGNAL{Signal Received?}
    
    SIGNAL -->|SIGTERM/SIGINT| SHUTDOWN
    SIGNAL -->|SIGHUP| RELOAD[Reload Config]
    SIGNAL -->|None| RUNNING
    
    RELOAD --> RUNNING
    
    subgraph "Shutdown Phase"
        SHUTDOWN[Graceful Shutdown]
        SHUTDOWN --> STOP1[Stop Polling]
        SHUTDOWN --> STOP2[Stop Monitoring]
        SHUTDOWN --> STOP3[Stop WebSocket]
        SHUTDOWN --> STOP4[Stop Code Agent]
        
        STOP1 --> CLEANUP
        STOP2 --> CLEANUP
        STOP3 --> CLEANUP
        STOP4 --> CLEANUP
        
        CLEANUP[Cleanup Resources]
    end
    
    CLEANUP --> END([Exit])
    
    style INIT fill:#3b82f6
    style SERVICES fill:#10b981
    style SHUTDOWN fill:#ef4444
```

### Service Dependencies

```mermaid
graph LR
    subgraph "Core Infrastructure"
        CM[Config Manager]
        LOGGER[Logging System]
        SYSTEMD[Systemd Integration]
    end
    
    subgraph "Service Manager"
        SM[Service Manager<br/>Orchestrator]
    end
    
    subgraph "Services"
        PS[Polling Service]
        MS[Monitor Service]
        WS[WebSocket Handler]
    end
    
    subgraph "Agents"
        BA[Bot Agent]
        COORD[Coordinator]
        CA[Code Agent]
    end
    
    CM --> SM
    LOGGER --> SM
    SYSTEMD --> SM
    
    SM -->|start/stop| PS
    SM -->|start/stop| MS
    SM -->|start/stop| WS
    SM -->|configure| BA
    SM -->|configure| COORD
    SM -->|configure| CA
    
    PS --> BA
    BA --> MS
    COORD --> MS
    CA --> MS
    
    MS --> WS
    
    BA --> CM
    COORD --> CM
    CA --> CM
    
    style SM fill:#3b82f6
    style CM fill:#f59e0b
```

---

## Agent Communication Patterns

### Inter-Agent Communication

```mermaid
sequenceDiagram
    participant PS as Polling Service
    participant IH as Issue Handler
    participant COORD as Coordinator
    participant BA as Bot Agent
    participant CA as Code Agent
    participant MS as Monitor Service
    participant WS as WebSocket

    PS->>IH: New issue detected
    IH->>COORD: Request task assignment
    
    COORD->>COORD: Evaluate issue complexity
    COORD->>MS: Update state: "planning"
    MS->>WS: Broadcast coordinator state
    
    COORD->>BA: Assign issue
    BA->>MS: Update state: "assigned"
    MS->>WS: Broadcast bot state
    
    BA->>CA: Request code generation
    CA->>MS: Update state: "generating"
    MS->>WS: Broadcast code agent state
    
    CA->>CA: Generate solution with LLM
    CA-->>BA: Return code
    CA->>MS: Update state: "idle"
    MS->>WS: Broadcast code agent idle
    
    BA->>BA: Apply code, commit, push
    BA->>MS: Update state: "pr_creation"
    MS->>WS: Broadcast bot state
    
    BA->>COORD: Task completed
    COORD->>MS: Update state: "idle"
    MS->>WS: Broadcast coordinator idle
```

### Message Passing Architecture

```mermaid
graph TD
    subgraph "Agent Layer"
        A1[Bot Agent]
        A2[Coordinator]
        A3[Code Agent]
    end
    
    subgraph "Message Bus (Monitor Service)"
        MB[Message Queue]
        STATE[State Manager]
        SUBS[Subscribers]
    end
    
    subgraph "Communication Layer"
        WS[WebSocket Server]
        REST[REST API]
    end
    
    A1 -->|publish state| MB
    A2 -->|publish state| MB
    A3 -->|publish state| MB
    
    MB --> STATE
    STATE --> SUBS
    
    SUBS -->|broadcast| WS
    SUBS -->|respond| REST
    
    WS -->|real-time| CLIENTS[Dashboards]
    REST -->|request/response| CLIENTS
    
    style MB fill:#10b981
    style WS fill:#3b82f6
```

---

## Configuration Management

### Configuration Load and Apply

```mermaid
flowchart TD
    START([Application Starts]) --> LOAD_ENV
    
    LOAD_ENV[Load Environment Variables] --> LOAD_FILES
    
    subgraph "File Loading"
        LOAD_FILES[Load Config Files]
        LOAD_FILES --> F1[system.yaml]
        LOAD_FILES --> F2[agents.yaml]
        LOAD_FILES --> F3[bot_config.yaml]
        LOAD_FILES --> F4[coordinator_config.yaml]
    end
    
    F1 --> MERGE
    F2 --> MERGE
    F3 --> MERGE
    F4 --> MERGE
    
    MERGE[Merge Configurations] --> VALIDATE
    
    VALIDATE{Validation}
    VALIDATE -->|Pass| APPLY
    VALIDATE -->|Fail| ERROR[Log Errors & Exit]
    
    APPLY[Apply to Components] --> C1[Service Manager]
    APPLY --> C2[Polling Service]
    APPLY --> C3[Monitor Service]
    APPLY --> C4[Agents]
    
    C1 --> READY
    C2 --> READY
    C3 --> READY
    C4 --> READY
    
    READY([System Ready])
    
    ERROR --> END([Exit 1])
    
    style VALIDATE fill:#f59e0b
    style APPLY fill:#10b981
    style ERROR fill:#ef4444
```

### Runtime Configuration Update

```mermaid
sequenceDiagram
    participant UI as config_ui.html
    participant API as REST API
    participant CM as Config Manager
    participant SM as Service Manager
    participant Agent as Agents

    UI->>API: PUT /api/config/agents
    Note over UI: User edited config
    
    API->>CM: validate_config(new_config)
    CM->>CM: Schema validation
    CM->>CM: Value range checks
    
    alt Validation Failed
        CM-->>API: ValidationError
        API-->>UI: 400 Bad Request
        UI->>UI: Show errors
    else Validation Passed
        CM->>CM: backup_current_config()
        CM->>CM: save_config(new_config)
        CM-->>API: Success
        
        API->>SM: reload_config()
        SM->>Agent: stop()
        Agent-->>SM: Stopped
        
        SM->>Agent: start(new_config)
        Agent-->>SM: Started
        
        SM-->>API: Reload complete
        API-->>UI: 200 OK
        UI->>UI: Show success
    end
```

---

## Monitoring Integration

### Agent State Tracking

```mermaid
flowchart LR
    subgraph "Agent Operations"
        START[Agent Starts Task]
        WORK[Processing]
        COMPLETE[Task Complete]
    end
    
    subgraph "Monitoring Hooks"
        H1[State: working]
        H2[Progress: 25%]
        H3[Progress: 50%]
        H4[Progress: 75%]
        H5[State: idle]
    end
    
    subgraph "Monitor Service"
        MS[Monitor Service]
        STATE_DB[(State Database)]
        METRICS[(Metrics)]
    end
    
    subgraph "Broadcast"
        WS[WebSocket]
        CLIENTS[Connected Clients]
    end
    
    START --> H1
    H1 --> MS
    
    WORK --> H2
    H2 --> MS
    
    WORK --> H3
    H3 --> MS
    
    WORK --> H4
    H4 --> MS
    
    COMPLETE --> H5
    H5 --> MS
    
    MS --> STATE_DB
    MS --> METRICS
    MS --> WS
    
    WS --> CLIENTS
    
    style MS fill:#10b981
    style WS fill:#3b82f6
```

### Metrics Collection

```mermaid
graph TD
    subgraph "Data Sources"
        CPU[CPU Usage]
        MEM[Memory Usage]
        API[API Call Count]
        TIME[Task Duration]
    end
    
    subgraph "Collection Layer"
        COLLECTOR[Metrics Collector]
    end
    
    subgraph "Processing"
        AGG[Aggregator]
        CALC[Calculator]
    end
    
    subgraph "Storage"
        TIMESERIES[(Time Series Data)]
        SUMMARY[(Summary Stats)]
    end
    
    subgraph "Consumers"
        DASH[Dashboards]
        ALERTS[Alert System]
        EXPORT[Prometheus Exporter]
    end
    
    CPU --> COLLECTOR
    MEM --> COLLECTOR
    API --> COLLECTOR
    TIME --> COLLECTOR
    
    COLLECTOR --> AGG
    AGG --> CALC
    
    CALC --> TIMESERIES
    CALC --> SUMMARY
    
    TIMESERIES --> DASH
    TIMESERIES --> EXPORT
    SUMMARY --> DASH
    SUMMARY --> ALERTS
    
    style COLLECTOR fill:#10b981
    style CALC fill:#3b82f6
```

---

## Error Handling Flow

### Error Propagation

```mermaid
flowchart TD
    ERROR[Error Occurs] --> CATCH{Caught?}
    
    CATCH -->|No| UNCAUGHT[Uncaught Exception]
    CATCH -->|Yes| LOG[Log Error]
    
    UNCAUGHT --> CRASH[Process Crash]
    CRASH --> SYSTEMD[Systemd Restarts]
    SYSTEMD --> RECOVERY[Recovery Mode]
    
    LOG --> LEVEL{Error Level}
    
    LEVEL -->|WARNING| WARN[Log & Continue]
    LEVEL -->|ERROR| HANDLE[Error Handler]
    LEVEL -->|CRITICAL| ALERT[Alert & Shutdown]
    
    WARN --> MONITOR[Update Monitor]
    MONITOR --> WS[Notify Dashboards]
    WS --> CONTINUE[Continue Operation]
    
    HANDLE --> RETRY{Can Retry?}
    
    RETRY -->|Yes| BACKOFF[Exponential Backoff]
    RETRY -->|No| FAIL[Mark Failed]
    
    BACKOFF --> ATTEMPT[Retry Attempt]
    ATTEMPT --> SUCCESS{Success?}
    
    SUCCESS -->|Yes| RECOVERED[Recovered]
    SUCCESS -->|No| COUNT{Max Retries?}
    
    COUNT -->|No| BACKOFF
    COUNT -->|Yes| FAIL
    
    FAIL --> NOTIFY[Notify User]
    NOTIFY --> MONITOR
    
    ALERT --> SHUTDOWN[Graceful Shutdown]
    SHUTDOWN --> SYSTEMD
    
    style ERROR fill:#ef4444
    style CRASH fill:#dc2626
    style RECOVERED fill:#10b981
```

### Retry Strategy

```mermaid
stateDiagram-v2
    [*] --> Attempt1: Initial try
    
    Attempt1 --> Success: OK
    Attempt1 --> Wait1: Failed
    
    Wait1 --> Attempt2: After 1s
    Attempt2 --> Success: OK
    Attempt2 --> Wait2: Failed
    
    Wait2 --> Attempt3: After 2s
    Attempt3 --> Success: OK
    Attempt3 --> Wait3: Failed
    
    Wait3 --> Attempt4: After 4s
    Attempt4 --> Success: OK
    Attempt4 --> Wait4: Failed
    
    Wait4 --> Attempt5: After 8s
    Attempt5 --> Success: OK
    Attempt5 --> Failed: Max retries
    
    Success --> [*]
    Failed --> [*]
    
    note right of Wait1
        Exponential backoff:
        1s, 2s, 4s, 8s, 16s
    end note
```

---

## WebSocket Communication Patterns

### Connection Management

```mermaid
sequenceDiagram
    participant Client as Dashboard
    participant WS as WebSocket Server
    participant Monitor as Monitor Service
    participant Agent as Agent

    Client->>WS: Connect ws://host:7997/ws/monitor
    WS->>WS: Register client
    WS-->>Client: Connection established
    
    loop Heartbeat every 30s
        WS->>Client: ping
        Client-->>WS: pong
    end
    
    Agent->>Monitor: State update
    Monitor->>WS: broadcast(agent_state)
    WS->>Client: agent_state message
    
    Agent->>Monitor: Log entry
    Monitor->>WS: broadcast(log)
    WS->>Client: log message
    
    alt Connection Lost
        Client-xWS: Connection dropped
        WS->>WS: Remove client
        Client->>Client: Wait 5s
        Client->>WS: Reconnect attempt
    end
    
    Client->>WS: Close connection
    WS->>WS: Unregister client
    WS-->>Client: Connection closed
```

### Broadcast Pattern

```mermaid
graph TD
    EVENT[Event Occurs] --> MONITOR[Monitor Service]
    
    MONITOR --> PREPARE[Prepare Message]
    PREPARE --> FORMAT[Format as JSON]
    
    FORMAT --> WS[WebSocket Handler]
    
    WS --> CLIENTS{Connected Clients}
    
    CLIENTS -->|Client 1| SEND1[Send Message]
    CLIENTS -->|Client 2| SEND2[Send Message]
    CLIENTS -->|Client 3| SEND3[Send Message]
    CLIENTS -->|Client N| SENDN[Send Message]
    
    SEND1 --> ACK1{Acknowledged?}
    SEND2 --> ACK2{Acknowledged?}
    SEND3 --> ACK3{Acknowledged?}
    SENDN --> ACKN{Acknowledged?}
    
    ACK1 -->|No| RETRY1[Retry/Drop]
    ACK2 -->|No| RETRY2[Retry/Drop]
    ACK3 -->|No| RETRY3[Retry/Drop]
    ACKN -->|No| RETRYN[Retry/Drop]
    
    ACK1 -->|Yes| DONE
    ACK2 -->|Yes| DONE
    ACK3 -->|Yes| DONE
    ACKN -->|Yes| DONE
    
    DONE([Broadcast Complete])
    
    style WS fill:#3b82f6
    style DONE fill:#10b981
```

---

## API Request Flow

### REST API Request Lifecycle

```mermaid
sequenceDiagram
    participant Client
    participant Nginx
    participant SM as Service Manager
    participant Handler
    participant Service
    participant DB

    Client->>Nginx: HTTP Request
    Nginx->>SM: Forward request
    
    SM->>Handler: Route to handler
    Handler->>Handler: Validate request
    
    alt Invalid Request
        Handler-->>SM: 400 Bad Request
        SM-->>Nginx: Error response
        Nginx-->>Client: Error message
    else Valid Request
        Handler->>Service: Execute operation
        Service->>DB: Query/Update
        DB-->>Service: Result
        Service-->>Handler: Success
        Handler-->>SM: 200 OK
        SM-->>Nginx: Success response
        Nginx-->>Client: Result
    end
```

---

## Related Documentation

- [Architecture Overview](architecture-overview.md) - System architecture
- [Data Flow](data-flow.md) - Data movement through system
- [ARCHITECTURE.md](../../ARCHITECTURE.md) - Complete architecture guide

---

**Last Updated**: 2025-10-06  
**Maintained by**: Agent-Forge Team
