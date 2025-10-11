# Agent-Forge Architecture

> **Version**: 2.0.0  
> **Last Updated**: 2025-10-11  
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

Agent-Forge is a multi-agent orchestration platform for GitHub automation with **unified agent runtime**. It consists of:

- **Service Manager**: Central orchestrator with unified agent runtime
- **Agent Registry**: Role-based lifecycle management (always-on vs on-demand)
- **Specialized Agents**: Bot, Coordinator, Code Agent (generic LLM support)
- **Monitoring Infrastructure**: WebSocket server + real-time dashboards
- **Polling Service**: Autonomous GitHub issue detection
- **Configuration Management**: YAML-based agent and system configuration
- **Instruction Validation System**: Automatic enforcement of Copilot instructions (PR #63)
- **Visual Documentation**: Comprehensive Mermaid diagrams for architecture understanding (PR #68)

### Recent Updates (October 2025)

**Unified Agent Runtime** (October 2025):
- Industry-standard architecture following LangChain, AutoGPT, MS Semantic Kernel patterns
- `engine/core/agent_registry.py`: Centralized agent lifecycle manager
- Role-based lifecycle: always-on (coordinator, developer) vs on-demand (bot, reviewer, tester, documenter, researcher)
- Resource-efficient: lazy loading for event-driven agents
- Scalable: add roles without code changes
- Breaking change: `code_agent` → `agent_runtime` service
- CLI: `--no-agent-runtime` (new), `--no-qwen` (deprecated but backward compatible)

**Agent Refactoring**:
- `qwen_agent.py` renamed to `code_agent.py` for generic LLM support
- `QwenAgent` class renamed to `CodeAgent`
- Service manager updated: `enable_qwen_agent` → `enable_code_agent` → `enable_agent_runtime`
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

**Intelligent Issue Routing & Complexity Analysis** (October 11, 2025):
- **Coordinator-First Gateway**: ALL issues with `agent-ready` label MUST pass through coordinator first
- **IssueComplexityAnalyzer**: Pre-flight complexity analysis with 9 metrics (0-65 points)
- **AgentEscalator**: Mid-execution escalation from code agent back to coordinator
- **Separation of Concerns**: Coordinator = Intelligence (decides), Polling = Execution (executes)
- Routing decisions: SIMPLE (escalation disabled), UNCERTAIN (escalation enabled), COMPLEX (multi-agent orchestration)
- See: [Intelligent Issue Routing Guide](docs/guides/INTELLIGENT_ISSUE_ROUTING.md)

**PR Lifecycle Management** (October 11, 2025):
- **ConflictComplexityAnalyzer**: Intelligent merge conflict analysis with 7 metrics (0-55 points)
- **Automated PR Review**: LLM-powered and static analysis code reviews
- **Smart Draft PR Recovery**: Automatic re-review when drafts become ready
- **Conflict Resolution**: Auto-resolve simple conflicts, close/reopen for complex cases
- **Rate Limiter**: Intelligent rate limit handling with retry logic and bypass for internal operations
- **Self-Review Prevention**: Bot accounts never review their own PRs
- **Race Condition Prevention**: File-based locking for concurrent PR operations

**Repository Management** (October 2025):
- Automated repository access management system
- Configurable bot account selection for operations
- Centralized GitHub account configuration (`config/system/github_accounts.yaml`)

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

The Service Manager (`engine/core/service_manager.py`) is the central orchestrator that:
- Starts and manages all services in a single process
- Manages unified agent runtime via AgentRegistry
- Handles graceful shutdown on SIGTERM/SIGINT
- Provides systemd integration (watchdog, notify)
- Monitors service health
- Exposes REST API via monitoring service

### Architecture

```python
ServiceManager
├── AgentRuntime (AgentRegistry)  # Unified agent lifecycle manager
│   ├── CodeAgent (always-on)     # Developer agent
│   ├── BotAgent (on-demand)      # GitHub operations
│   └── CoordinatorAgent (always-on)  # Task orchestration
├── PollingService                # GitHub issue monitoring
├── MonitorService                # Agent state tracking + REST API
├── WebSocketHandler              # Real-time communication
└── Web UI Process                # Frontend dashboard
```

### Agent Registry

**File**: `engine/core/agent_registry.py`

The AgentRegistry implements role-based lifecycle management following industry patterns:

**Lifecycle Strategies**:
- **Always-on**: Agents start immediately and run continuously
  - Coordinator: Task orchestration, planning
  - Developer: Code generation, bug fixes
- **On-demand**: Agents register but only start when triggered (lazy loading)
  - Bot: GitHub operations (comments, labels, close issues)
  - Reviewer: PR reviews, code quality checks
  - Tester: Test execution, validation
  - Documenter: Documentation generation
  - Researcher: Information gathering, analysis

**Lifecycle States**:
```
REGISTERED → STARTING → RUNNING → IDLE → STOPPING → STOPPED
                   ↓
                 ERROR
```

**Key Methods**:
- `load_agents()`: Load and register all enabled agents from config
- `start_always_on_agents()`: Start coordinator and developer agents immediately
- `start_on_demand(agent_id)`: Lazy-load specific agent when triggered
- `stop_agent(agent_id)`: Graceful agent shutdown
- `get_agent_status()`: Query agent lifecycle state

**Industry Patterns**:
- **LangChain/LangGraph**: Supervisor agent pattern with worker agents
- **AutoGPT**: Sub-agent spawning for specialized tasks
- **Microsoft Semantic Kernel**: Plugin/skill lazy loading

### Configuration

**File**: `config/system.yaml`

```yaml
service_manager:
  enable_polling: true
  enable_monitoring: true
  enable_web_ui: true
  enable_agent_runtime: true  # Unified agent runtime (replaces enable_code_agent)
  
  polling_interval: 300  # 5 minutes
  monitoring_port: 7997
  web_ui_port: 8897
  
  polling_repos:
    - "m0nk111/agent-forge"
    - "m0nk111/stepperheightcontrol"
```

**Agent Configs**: `config/agents/{agent-id}.yaml`

Each agent has individual config:
- `agent_id`: Unique identifier (e.g., m0nk111-qwen-agent)
- `role`: Agent role (developer, bot, coordinator, reviewer, tester, documenter, researcher)
- `enabled`: Whether agent should be loaded
- `model_provider`: LLM provider (local, openai, anthropic, google)
- `model_name`: Specific model (qwen2.5-coder:7b, gpt-4, etc)
- `github_token`: GitHub authentication (loaded from secrets/)

### REST API Endpoints

**Base URL**: `http://localhost:7997` (monitoring service)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/services` | GET | Infrastructure service health (polling, monitoring, web_ui, agent_runtime) |
| `/api/agents` | GET | List all agents and states |
| `/api/agents/{id}/status` | GET | Detailed agent status |
| `/api/agents/{id}/logs` | GET | Agent logs |
| `/api/activity` | GET | Historical activity events |
| `/config` | PUT | Update configuration |

---

## Agent Roles & Responsibilities

### Services vs Agents Distinction

**Important**: The system distinguishes between **Services** (infrastructure) and **Agents** (AI workers).

**Services** (Infrastructure Components):
- `polling` - GitHub repository polling service (`engine/runners/polling_service.py`)
- `monitoring` - Monitoring API and WebSocket service (`engine/runners/monitor_service.py`)
- `web_ui` - Dashboard HTTP server (Python HTTP server)
- `code_agent` - Code agent runtime wrapper (service that runs the agent)

**Agents** (AI Workers):
- `m0nk111-post` - Bot agent for orchestration (role: bot)
- `m0nk111-qwen-agent` - Primary developer agent (role: developer)

**Key Differences**:
- **Services** are managed by `service_manager` and register via `self.services` dict
- **Agents** register themselves via `monitor.register_agent()` and appear in `/api/agents`
- **Services** appear in `/api/services` with health status (online/offline)
- **Agents** have detailed status (idle/working/error/offline) and task tracking

**API Endpoints**:
- `GET /api/services` - Infrastructure service health (polling, monitoring, web_ui, code_agent)
- `GET /api/agents` - AI agent status (all bot and coder agents)

### 1. Bot Agent (`engine/runners/bot_agent.py`)

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

**Configuration**: `config/agents/*.yaml`

### 4. Polling Service (`agents/polling_service.py`)

**Purpose**: Autonomous GitHub monitoring

**Responsibilities**:
- Poll GitHub repositories for new issues
- Detect assigned issues for bot accounts
- Trigger agent workflows
- Rate limit management

**Configuration**: `polling_config.yaml`

---

## Coordinator-First Gateway Architecture

### Overview

**Philosophy**: The coordinator is the MANDATORY entry point for ALL issues with `agent-ready` label. No issue bypasses the coordinator's analysis.

**User Requirement** (verbatim): 
> "IK WIL DAT DE COORDINATOR ALS EERSTE BEPAALD, WAT IS DIT ISSUE. SIMPLE, MORERESEARCH, COMPLEX. geen precheck door de poller, de poller zet meteen de coordinator in."

### Architecture Components

```
┌─────────────────────────────────────────────────────────────┐
│                   COORDINATOR-FIRST GATEWAY                  │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Polling Service (Execution Layer)                    │  │
│  │  - Detects agent-ready issues                         │  │
│  │  - Triggers coordinator gateway IMMEDIATELY           │  │
│  │  - Receives decision from coordinator                 │  │
│  │  - Executes decision (starts agents, monitors)        │  │
│  └────────────────┬─────────────────────────────────────┘  │
│                   │                                           │
│                   ▼                                           │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Coordinator Gateway (Intelligence Layer)             │  │
│  │  - Analyzes EVERY issue (MANDATORY)                   │  │
│  │  - Determines complexity (SIMPLE/UNCERTAIN/COMPLEX)   │  │
│  │  - Makes routing decision                             │  │
│  │  - Tags issue with decision label                     │  │
│  │  - Posts explanation comment                          │  │
│  │  - Returns decision object (does NOT execute)         │  │
│  └────────────────┬─────────────────────────────────────┘  │
│                   │                                           │
│                   ▼                                           │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  IssueComplexityAnalyzer                              │  │
│  │  - 9 complexity signals (0-65 points)                 │  │
│  │  - LLM semantic analysis (optional)                   │  │
│  │  - Returns: complexity, score, routing, confidence    │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                               │
└─────────────────────────────────────────────────────────────┘
                         │
                         ▼
          ┌──────────────────────────┐
          │  Routing Decision         │
          │                           │
          │  SIMPLE:                  │
          │  → start_code_agent       │
          │  → escalation=False       │
          │                           │
          │  UNCERTAIN:               │
          │  → start_code_agent       │
          │  → escalation=True        │
          │                           │
          │  COMPLEX:                 │
          │  → start_coordinator      │
          │  → multi-agent            │
          └──────────────────────────┘
```

### Separation of Concerns

**Intelligence Layer** (Coordinator Gateway):
- **Purpose**: Analysis, decision-making, explanation
- **Responsibilities**:
  - Analyze issue complexity using IssueComplexityAnalyzer
  - Consult LLM for semantic understanding (optional)
  - Make routing decision (SIMPLE/UNCERTAIN/COMPLEX)
  - Tag issue with decision label (`coordinator-approved-simple`, etc.)
  - Post detailed explanation comment for humans
  - Return decision object to polling service
- **Does NOT**: Execute decisions, start agents, manage workflows
- **File**: `engine/operations/coordinator_gateway.py` (~380 lines)

**Execution Layer** (Polling Service):
- **Purpose**: Workflow execution, agent lifecycle management
- **Responsibilities**:
  - Detect agent-ready issues
  - Trigger coordinator gateway for EVERY issue
  - Receive decision object from coordinator
  - Execute decision: start agents, configure escalation, monitor progress
  - Handle agent failures, timeouts, escalations
- **Does NOT**: Make routing decisions, analyze complexity
- **File**: `engine/runners/polling_service.py`

**Benefits**:
- **Testability**: Mock decisions independently of execution
- **Flexibility**: Change routing logic without touching execution
- **Transparency**: Explicit decision trail with labels and comments
- **Scalability**: Add new decision types without execution refactor

### IssueComplexityAnalyzer

**File**: `engine/operations/issue_complexity_analyzer.py` (363 lines)

**Purpose**: Objective, metrics-based complexity analysis BEFORE agent assignment

**9 Complexity Signals** (0-65 points total):

1. **Description Length** (0-5 points):
   - `<100 chars`: 0 pts
   - `100-500 chars`: 1-3 pts
   - `>500 chars`: 4-5 pts

2. **Task Count** (0-10 points):
   - Detects: "TODO", "task", numbered lists, bullet points
   - `1-2 tasks`: 2 pts
   - `3-5 tasks`: 5 pts
   - `>5 tasks`: 10 pts

3. **File Mentions** (0-8 points):
   - Detects: file paths, file extensions
   - `1-2 files`: 2 pts
   - `3-5 files`: 5 pts
   - `>5 files`: 8 pts

4. **Code Blocks** (0-3 points):
   - Detects: triple backticks, code fences
   - `1 block`: 1 pt
   - `2 blocks`: 2 pts
   - `>2 blocks`: 3 pts

5. **Dependency Mentions** (0-5 points):
   - Keywords: "dependency", "import", "require", "install"
   - Each mention: +1 pt (max 5)

6. **Refactoring Keywords** (0-8 points):
   - Keywords: "refactor", "restructure", "reorganize", "migrate"
   - Each mention: +2 pts (max 8)

7. **Architecture Keywords** (0-10 points):
   - Keywords: "architecture", "design", "pattern", "system", "integration"
   - Each mention: +2 pts (max 10)

8. **Multi-Component Keywords** (0-6 points):
   - Keywords: "multiple", "several", "all", "across", "various"
   - Each mention: +2 pts (max 6)

9. **Complex Labels** (0-10 points):
   - Labels: "complex", "architecture", "refactor", "breaking-change"
   - Each label: +5 pts (max 10)

**Thresholds**:
- **SIMPLE**: ≤10 points (straightforward, single-component)
- **UNCERTAIN**: 11-25 points (needs investigation, possible escalation)
- **COMPLEX**: >25 points (multi-component, architecture changes)

**LLM Integration** (optional):
- Semantic analysis via CoordinatorAgent
- Validates metric-based score
- Provides reasoning and confidence score

**Returns**:
```python
{
    'complexity': 'simple' | 'uncertain' | 'complex',
    'score': 0-65,
    'routing': 'start_code_agent' | 'start_coordinator_orchestration',
    'confidence': 0.0-1.0,
    'reasoning': str,
    'escalation_enabled': bool
}
```

### AgentEscalator

**File**: `engine/operations/agent_escalator.py` (354 lines)

**Purpose**: Allow code agent to escalate mid-execution when complexity exceeds initial assessment

**Escalation Triggers**:

1. **File Count**: >5 files modified
2. **Component Count**: >3 components/directories touched
3. **Failed Attempts**: ≥2 consecutive failures
4. **Stuck Time**: >30 minutes without progress
5. **Architecture Changes**: Detected structural modifications
6. **Explicit Request**: Agent determines coordination needed

**EscalationContext** (dataclass):
```python
{
    # Work metrics
    'files_modified': int,
    'components_touched': set[str],
    'failed_attempts': int,
    'work_duration_minutes': int,
    
    # Discovery metrics
    'architecture_changes_detected': bool,
    'unexpected_dependencies': list[str],
    'coordination_needed': bool
}
```

**Escalation Workflow**:
1. Code agent calls `should_escalate(context)` during work
2. If True: `escalate_to_coordinator(issue, context, progress_summary)`
3. AgentEscalator:
   - Posts escalation comment explaining reasons
   - Adds `needs-coordination` label
   - Triggers coordinator with progress report
   - Returns control to coordinator

**Integration**:
- Code agent checks escalation triggers after each major step
- Escalation preserves work progress (branch, commits)
- Coordinator can continue work or reassign to different agent

### CoordinatorGateway

**File**: `engine/operations/coordinator_gateway.py` (~380 lines)

**Purpose**: Mandatory gateway implementing separation of concerns

**Key Method**: `process_issue(owner, repo, issue_number, issue_data)`

**Workflow**:
```python
def process_issue(self, owner, repo, issue_number, issue_data):
    # 1. ANALYZE (Intelligence)
    analysis = self.coordinator.analyze_issue_complexity(
        issue_data,
        use_llm=True  # Optional semantic analysis
    )
    
    # 2. DECIDE (Intelligence)
    decision = self._make_routing_decision(analysis)
    
    # 3. TAG (Intelligence)
    self._tag_issue_with_decision(
        owner, repo, issue_number, decision
    )
    
    # 4. EXPLAIN (Intelligence)
    self._post_decision_comment(
        owner, repo, issue_number, decision, analysis
    )
    
    # 5. RETURN (NOT execute)
    return {
        'status': 'decision_made',
        'decision': decision,  # SIMPLE | UNCERTAIN | COMPLEX
        'action': 'start_code_agent' | 'start_coordinator_orchestration',
        'escalation_enabled': True/False,
        'instructions': str
    }
```

**Routing Decisions**:

1. **DELEGATE_SIMPLE** (score ≤10):
   - Action: `start_code_agent`
   - Escalation: False
   - Label: `coordinator-approved-simple`
   - Comment: "Straightforward task, code agent can handle independently"

2. **DELEGATE_WITH_ESCALATION** (score 11-25):
   - Action: `start_code_agent`
   - Escalation: True
   - Label: `coordinator-approved-uncertain`
   - Comment: "Initial work delegated, escalation enabled if complexity emerges"

3. **ORCHESTRATE** (score >25):
   - Action: `start_coordinator_orchestration`
   - Multi-agent: True
   - Label: `coordinator-approved-complex`
   - Comment: "Complex task requiring coordination and multi-agent approach"

**Decision Labels**:
- `coordinator-approved-simple`: Simple task, no escalation
- `coordinator-approved-uncertain`: Uncertain complexity, escalation enabled
- `coordinator-approved-complex`: Complex task, multi-agent orchestration

**Comments Posted**:
```markdown
🎯 **Coordinator Analysis Complete**

**Complexity Assessment**: UNCERTAIN (18 points)

**Key Indicators**:
- 3 files mentioned
- Architecture keywords detected: "design", "integration"
- 4 tasks identified

**Routing Decision**: DELEGATE_WITH_ESCALATION
- Code agent will start work
- Escalation enabled if complexity emerges
- Coordinator monitoring progress

**Confidence**: 85%
```

### Workflow Example

**Scenario**: Issue #123 "Refactor authentication system"

```
1. GitHub Issue Created
   - Title: "Refactor authentication system"
   - Body: Mentions "auth.py", "database.py", "api.py", "OAuth integration"
   - Label: agent-ready

2. Polling Service
   - Detects agent-ready issue
   - Triggers: coordinator_gateway.process_issue(#123)

3. Coordinator Gateway (Intelligence)
   - IssueComplexityAnalyzer runs:
     * File mentions: 3 files = 5 pts
     * Architecture keywords: "refactor", "system", "integration" = 8 pts
     * Refactor keywords: 2 pts
     * Total: 15 pts → UNCERTAIN
   
   - LLM Analysis (optional):
     * Semantic: "Authentication refactor affects multiple components"
     * Confidence: 80%
   
   - Decision: DELEGATE_WITH_ESCALATION
   
   - Tags: coordinator-approved-uncertain
   
   - Comment: "Delegating to code agent with escalation enabled..."
   
   - Returns: {decision: UNCERTAIN, action: start_code_agent, escalation: True}

4. Polling Service (Execution)
   - Receives decision object
   - Calls: issue_handler.start_code_agent(#123, escalation_enabled=True)
   - Monitors: code agent progress

5. Code Agent
   - Starts work on issue #123
   - Modifies auth.py, database.py
   - Discovers: "OAuth requires changes to 8 files, not 3"
   - EscalationContext: files_modified=2, unexpected_dependencies=True
   
   - Calls: agent_escalator.should_escalate(context)
   - Result: True (unexpected dependencies)
   
   - Calls: agent_escalator.escalate_to_coordinator(#123, context, progress)

6. AgentEscalator
   - Posts: "🚀 Escalating to coordinator: Found 8 files need changes, not 3"
   - Adds label: needs-coordination
   - Triggers: coordinator orchestration with progress report
   
7. Coordinator (Orchestration)
   - Reviews: code agent's progress (branch, commits)
   - Decision: "Too complex for single agent, split into 2 PRs"
   - Assigns: PR #1 (auth.py, database.py) to code agent
   - Assigns: PR #2 (OAuth integration) to specialized reviewer
```

### Configuration

**Coordinator Gateway**: `config/services/coordinator.yaml`
```yaml
coordinator:
  gateway:
    use_llm_analysis: true  # Enable semantic analysis
    llm_model: "gpt-4"
    confidence_threshold: 0.7
```

**Complexity Analyzer**: `engine/operations/issue_complexity_analyzer.py`
```python
SIMPLE_THRESHOLD = 10   # ≤10 points = simple
COMPLEX_THRESHOLD = 25  # >25 points = complex
```

**Escalation Triggers**: `engine/operations/agent_escalator.py`
```python
MAX_FILES_SIMPLE = 5            # Escalate if >5 files
MAX_COMPONENTS_SIMPLE = 3       # Escalate if >3 components
MAX_FAILED_ATTEMPTS = 2         # Escalate after 2 failures
MAX_STUCK_TIME_MINUTES = 30     # Escalate if stuck >30min
```

### Testing

**Unit Tests**:
- `tests/test_issue_complexity_analyzer.py`: All 9 metrics, thresholds
- `tests/test_agent_escalator.py`: Trigger conditions, escalation workflow
- `tests/test_coordinator_gateway.py`: Decision logic, labeling, comments

**Integration Tests**:
- `tests/test_integration_coordinator_gateway.py`: End-to-end workflow
- Mock GitHub API, verify labels and comments

**See Also**:
- [Intelligent Issue Routing Guide](docs/guides/INTELLIGENT_ISSUE_ROUTING.md) (~700 lines)
- [Separation of Concerns Guide](docs/guides/SEPARATION_OF_CONCERNS.md) (~600 lines)

---

## PR Lifecycle Management

### Overview

Automated PR management system with intelligent conflict resolution, code review, and lifecycle tracking.

### ConflictComplexityAnalyzer

**File**: `engine/operations/conflict_analyzer.py` (266 lines)

**Purpose**: Analyze PR merge conflicts to determine auto-resolve vs manual intervention vs close/reopen

**7 Conflict Metrics** (0-55 points total):

1. **Conflicted Files** (0-10 points):
   - `1-2 files`: 3 pts
   - `3-5 files`: 6 pts
   - `>5 files`: 10 pts

2. **Conflict Markers** (0-10 points):
   - Count of `<<<<<<<`, `=======`, `>>>>>>>`
   - `1-5 markers`: 2 pts
   - `6-10 markers`: 5 pts
   - `>10 markers`: 10 pts

3. **Lines Affected** (0-10 points):
   - Total lines in conflict regions
   - `<50 lines`: 2 pts
   - `50-200 lines`: 5 pts
   - `>200 lines`: 10 pts

4. **Files Overlap** (0-5 points):
   - Percentage of PR files in conflict
   - `<25%`: 1 pt
   - `25-50%`: 3 pts
   - `>50%`: 5 pts

5. **Age Days** (0-5 points):
   - PR age since creation
   - `<7 days`: 1 pt
   - `7-30 days`: 3 pts
   - `>30 days`: 5 pts

6. **Commits Behind** (0-10 points):
   - How many commits behind base branch
   - `<5 commits`: 2 pts
   - `5-20 commits`: 5 pts
   - `>20 commits`: 10 pts

7. **Core Files Affected** (0-5 points):
   - Conflicts in critical files (e.g., main.py, __init__.py, config files)
   - Each core file: +2 pts (max 5)

**Thresholds**:
- **SIMPLE**: ≤8 points (auto-resolve)
- **MODERATE**: 9-14 points (manual fix)
- **COMPLEX**: ≥15 points (close/reopen)

**Actions**:
1. **auto_resolve**: Simple conflicts, automatic resolution
2. **manual_fix**: Moderate conflicts, request human intervention
3. **close_and_recreate**: Complex conflicts, close PR and reopen issue

**Integration**: PR review agent checks conflicts before review/merge

### PR Review Agent

**File**: `engine/operations/pr_review_agent.py`

**Features**:
- **Static Analysis**: Automated code quality checks (always)
- **LLM Review**: Deep semantic code review (optional, `--use-llm`)
- **Conflict Handling**: ConflictComplexityAnalyzer integration
- **Self-Review Prevention**: Bot never reviews own PRs
- **Rate Limit Handling**: Intelligent retry with exponential backoff
- **Race Condition Prevention**: File-based locking for concurrent operations

**Workflow**:
```
1. PR Detected
   ↓
2. Check Conflicts
   ↓
3. ConflictComplexityAnalyzer.analyze()
   ↓
4a. SIMPLE → Attempt auto-resolve
4b. MODERATE → Comment requesting manual fix
4c. COMPLEX → Close PR, reopen issue with agent-ready label
   ↓
5. (If no conflicts) Perform Code Review
   ↓
6. (If approved) Merge PR
```

**Review Methods**:
- Static Analysis: File extension checks, basic linting
- LLM Review: GPT-4/Claude semantic analysis, best practices

**Review Comments**:
```markdown
## 🤖 Automated Code Review

**Review Method**: Static Analysis
**LLM Model**: N/A

### Analysis Results
✅ **Approved**: Code meets quality standards

- File structure looks good
- No obvious issues detected
```

### Smart Draft PR Recovery

**File**: `engine/runners/polling_service.py`

**Feature**: Automatically re-review draft PRs when they become ready

**Workflow**:
1. Draft PR detected → Skip review, mark as `draft:pending`
2. Draft PR becomes ready → Trigger automatic re-review
3. Memory leak prevention: Periodic cleanup of old PR states

**Configuration**: `config/services/polling.yaml`
```yaml
polling:
  draft_pr_recovery: true
  memory_cleanup_hours: 24  # Clean up PR state older than 24h
```

### Rate Limiter

**Purpose**: Prevent GitHub API rate limit exhaustion

**Features**:
- **Intelligent Bypass**: Internal operations (list PRs, list issues) bypass limiter
- **Retry Logic**: Exponential backoff on rate limit errors
- **Operation Types**:
  - `ISSUE_COMMENT`: Normal rate limiting (5 req/min)
  - `API_READ`: Bypass limiter (no delay)

**Configuration**: `engine/operations/rate_limiter.py`
```python
RATE_LIMITS = {
    'ISSUE_COMMENT': 5,  # 5 comments per minute
    'API_READ': 0        # No limit (bypass)
}
```

**Integration**: GitHub API helper checks rate limits before operations

### GitHub Actions Integration

**File**: `.github/workflows/pr-review.yml`

**Triggers**:
- `pull_request`: [opened, synchronize, reopened, ready_for_review]

**Workflow**:
1. PR event triggers GitHub Action
2. Action calls polling service: `curl http://localhost:7997/api/trigger/pr-review`
3. Polling service detects PR and triggers review workflow

### Configuration

**PR Review**: `config/services/pr_review.yaml`
```yaml
pr_review:
  enable_llm_review: false  # Static analysis by default
  llm_model: "gpt-4"
  auto_merge: true          # Auto-merge approved PRs
  conflict_analyzer: true   # Enable conflict complexity analysis
```

**Polling**: `config/services/polling.yaml`
```yaml
polling:
  pr_review_enabled: true
  draft_pr_recovery: true
  rate_limiter_bypass_internal: true
```

### Testing

**Unit Tests**:
- `tests/test_conflict_analyzer.py`: All 7 metrics, thresholds, actions
- `tests/test_pr_review_agent.py`: Review workflow, conflict handling

**Integration Tests**:
- `tests/test_draft_pr_monitoring.py`: Draft PR recovery workflow
- `tests/test_merge_workflow.py`: End-to-end PR lifecycle

**See Also**:
- [PR Lifecycle Management Entry](CHANGELOG.md#pr-lifecycle-management)

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

### Project Directory Structure

```
agent-forge/
├── ARCHITECTURE.md          # System architecture (this file)
├── README.md                # Project overview
├── CHANGELOG.md             # Version history
├── LICENSE                  # License information
│
├── engine/                  # ⭐ CORE ENGINE (Python modules)
│   ├── core/                # Core system components
│   │   ├── config_manager.py      # Configuration management
│   │   ├── service_manager.py     # Service orchestration
│   │   ├── context_manager.py     # Context tracking
│   │   ├── key_manager.py         # API key management
│   │   └── permissions.py         # Permission presets
│   │
│   ├── operations/          # Agent operations
│   │   ├── workspace_tools.py     # File/directory operations
│   │   ├── file_editor.py         # File editing
│   │   ├── terminal_operations.py # Shell commands
│   │   ├── github_api_helper.py   # GitHub API wrapper
│   │   ├── codebase_search.py     # Code search
│   │   ├── git_operations.py      # Git operations
│   │   ├── web_fetcher.py         # Web scraping
│   │   └── websocket_handler.py   # WebSocket routes
│   │
│   ├── runners/             # Service runners
│   │   ├── bot_agent.py           # GitHub bot agent
│   │   ├── code_agent.py          # Code agent (generic LLM)
│   │   ├── coordinator_agent.py   # Coordinator agent
│   │   ├── monitor_service.py     # Monitoring service
│   │   └── polling_service.py     # GitHub polling
│   │
│   └── validation/          # Validation & security
│       ├── instruction_parser.py  # Rule parsing
│       ├── instruction_validator.py # Validation logic
│       └── security_auditor.py    # Security checks
│
├── config/                  # ⭐ CONFIGURATION (YAML files)
│   ├── agents/              # Agent configurations
│   │   ├── m0nk111-post.yaml         # Bot agent
│   │   └── m0nk111-qwen-agent.yaml   # Developer agent
│   │
│   ├── services/            # Service configurations
│   │   ├── coordinator.yaml          # Coordinator settings
│   │   └── polling.yaml              # Polling settings
│   │
│   ├── system/              # System-wide configurations
│   │   ├── system.yaml               # System settings
│   │   ├── repositories.yaml         # Monitored repos
│   │   ├── github_accounts.yaml      # GitHub accounts (centralized) ⭐
│   │   └── trusted_agents.yaml       # Agent permissions (deprecated)
│   │
│   ├── rules/               # Policy & validation rules
│   │   ├── instruction_rules.yaml    # Copilot instructions
│   │   ├── review_criteria.yaml      # PR review rules
│   │   └── security_audit.yaml       # Security rules
│   │
│   └── development/         # Development configs
│       └── test_task.yaml            # Test task definitions
│
├── secrets/                 # ⭐ SECRETS (DO NOT COMMIT)
│   └── agents/              # Agent tokens (600 permissions)
│       ├── m0nk111-post.token        # Bot orchestrator
│       ├── m0nk111-qwen-agent.token  # Developer agent
│       └── m0nk111.token             # Admin account (emergency only)
│
├── frontend/                # Web dashboards
│   ├── dashboard.html              # ⭐ DEFAULT DASHBOARD
│   ├── unified_dashboard.html      # Unified view
│   ├── monitoring_dashboard.html   # Classic monitoring
│   └── config_ui.html             # Configuration UI
│
├── docs/                    # Documentation
│   ├── MONITORING_API.md           # Monitoring API reference
│   ├── DEPLOYMENT.md               # Deployment guide
│   ├── AGENT_ROLES.md              # Agent role definitions
│   └── diagrams/                   # Visual diagrams
│
├── scripts/                 # Utility scripts
│   ├── start-service.sh            # Start agent-forge service
│   ├── install-service.sh          # Install systemd service
│   └── monitor-cli.py              # CLI monitoring tool
│
├── systemd/                 # Systemd service files
│   └── agent-forge.service         # Service definition
│
└── tests/                   # Test suite
    ├── test_bot_agent.py
    ├── test_coordinator_agent.py
    ├── test_instruction_validator.py
    └── test_polling_service.py
```

### Key Directory Conventions

**Rule**: Narrow and deep directory structure for better organization

**Engine Module** (`engine/`):
- All Python code in `engine/` (no more `agents/` directory in root)
- Organized by function: `core/`, `operations/`, `runners/`, `validation/`
- Imports use `engine.*` prefix (e.g., `from engine.core import config_manager`)

**Configuration** (`config/`):
- Hierarchical structure: `agents/`, `services/`, `system/`, `rules/`
- All YAML configuration files
- No Python code in `config/` directory

**Secrets** (`secrets/`):
- **DO NOT COMMIT** - gitignored
- Token files: `secrets/agents/{agent_id}.token`
- Permissions: `agent-forge:agent-forge` ownership, mode `600`
- Loaded automatically by `ConfigManager`

**Root Directory**:
- **Only** allowed: README.md, CHANGELOG.md, LICENSE, ARCHITECTURE.md, config files
- **No** scripts, tests, or agent code in root
- Keeps root clean for navigation

### Frontend Dashboard Structure

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
   ├──> config/agents/*.yaml
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
| `config/agents/*.yaml` | Agent definitions (per agent) | YAML |
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
sudo journalctl -u agent-forge -f --no-pager
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
