# Provisional Goal: Full Issue-to-Agent Automation

> **Status**: In Progress (2025-10-09)  
> **Context**: Defines completion criteria for end-to-end automation workflow until autonomous issue → PR pipeline is operational.

---

## 🎯 Objective

Until the platform can automatically:

1. **Detect** a newly created GitHub issue.
2. **Assign** an Agent Forge automation agent to that issue without manual intervention.
3. **Execute** the issue request end-to-end, including tasks such as:
   - Generating ASCII art (e.g., chair, rocket, diagram, or other character-based illustration).
   - Writing creative text (e.g., poems, short research notes like on a goldfish).
   - Implementing functional code modules (e.g., a screen-bouncing module).
4. **Produce** pull requests and documentation updates that satisfy the issue requirements.

…the current development effort remains incomplete.

---

## ✅ Acceptance Criteria

### Core Automation
- [ ] **Issue Detection**: Polling service (`engine/runners/polling_runner.py`) automatically detects new issues in monitored repositories
- [ ] **Agent Assignment**: Coordinator agent (`engine/core/coordinator_agent.py`) assigns appropriate agent based on issue type (creative vs. code vs. review)
- [ ] **Autonomous Execution**: Assigned agent executes task without human prompts
- [ ] **PR Creation**: Agent commits changes, updates changelog, and creates pull request via bot agent
- [ ] **Security Audit**: Non-trusted contributors trigger mandatory security audit (secrets, injection, malware, license, dependency scanning)
- [ ] **PR Review**: PR reviewer agent validates changes before merge (if enabled)

### Monitoring & Validation
- [ ] **Real-time Monitoring**: WebSocket monitoring (port 7997) shows agent status, task progress, and logs
- [ ] **Dashboard Integration**: Unified dashboard (`frontend/unified_dashboard.html`) displays all agents, services, and activity timeline
- [ ] **Structured Logging**: All debug logs use emoji conventions (🐛, 🔍, ⚠️, ❌, ✅, 📊, 🔧) and DEBUG flag
- [ ] **Rate Limiting**: Anti-spam protection enforces limits (3 comments/min, 30/hour, 200/day; 10 issues/hour, 5 PRs/hour)
- [ ] **Instruction Validation**: Pre-commit validation ensures file locations, commit messages, changelog updates, port usage, and documentation language compliance

### Artifact Quality
- [ ] **Markdown Generation**: ASCII art stored in `docs/<subject>.md` with proper fencing (` ```text `)
- [ ] **Code Quality**: Generated code passes bandit/safety scans, has no injection vulnerabilities, uses environment variables for secrets
- [ ] **Changelog Discipline**: Every code change has CHANGELOG.md entry (newest-first), docs changes have DOCS_CHANGELOG.md entry
- [ ] **Conventional Commits**: All commits follow `type(scope): description` format
- [ ] **Test Coverage**: Generated code includes unit tests (70% coverage target, 70/20/10 unit/integration/e2e ratio)

### Testing & Repeatability
- [ ] **ASCII Automation Tests**: `tests/test_issue_handler_sun.py` passes (stub LLM, assert Markdown structure)
- [ ] **Integration Tests**: Tests for chairs, poems, research summaries, and code modules with real GitHub API (rate-limited)
- [ ] **End-to-End Validation**: Dry-run GitHub issue → agent assignment → PR creation without production deployment
- [ ] **Branch Verification**: Generated branches contain correct files, changelog entries, and documentation updates
- [ ] **PR Review Checklist**: Description explains changes, references issue, includes rendered Markdown preview

---

## 📊 System Context & Integration Points

### Architecture (ARCHITECTURE.md)
- **Multi-Agent System**: 7 agent roles (Coordinator, Developer, Reviewer, Tester, Documenter, Bot, Researcher)
- **Port Allocation**: Service Manager (8080), WebSocket (7997), Frontend (8897), Auth (7996), Ollama (11434)
- **Services**: Polling (Issue detection), Monitoring (Real-time status), Web UI (Dashboard), Agent Runtime (Role-based lifecycle)
- **Lifecycle**: Always-on agents (coordinator, developer) start immediately; on-demand agents (bot, reviewer) lazy load

### Security (SECURITY_AUDIT.md)
- **Trusted Agents**: `m0nk111-bot`, `m0nk111-qwen-agent` bypass security audits
- **Non-Trusted PRs**: Mandatory audit blocks merge on critical/high severity issues (secrets, injection, malware, dependencies, licenses)
- **Security Score**: 0-100 scale, minimum 70.0 to pass (critical=-30, high=-20, medium=-10, low=-5)
- **Audit Tools**: bandit (Python security), safety (dependency CVEs), custom pattern detection

### Rate Limiting (ANTI_SPAM_PROTECTION.md)
- **Comment Limits**: 3/min, 30/hour, 200/day (burst: 5, cooldown: 20-120s)
- **Issue Limits**: 10/hour, 50/day (burst: 3, cooldown: 60-300s)
- **PR Limits**: 5/hour, 20/day (burst: 2, cooldown: 120-600s)
- **Duplicate Detection**: Hash-based with 10-minute cache

### Instruction Validation (INSTRUCTION_VALIDATION_GUIDE.md)
- **File Location Rules**: Root directory only allows README/CHANGELOG/LICENSE/ARCHITECTURE + config files
- **Commit Message Format**: Conventional commits with regex `.{3,}` (allows short commits like "fix: tests")
- **Changelog Required**: Every code change needs CHANGELOG.md entry before commit
- **Port Usage**: Validate within assigned ranges (7000-7999 for Agent-Forge)
- **Auto-Fix**: Commit messages get conventional prefix if missing, changelog entries suggested based on changed files

### Testing Strategy (TESTING.md)
- **Test Pyramid**: 70% unit, 20% integration, 10% e2e
- **Coverage Target**: Minimum 70% overall, 80% for validators
- **Test Organization**: Mirror source structure (`tests/test_<module>.py`)
- **Integration Tests**: Must have assertions (not just print statements)
- **Mock Strategy**: Stub GitHub API, LLM calls to avoid rate limits

### Monitoring (MONITORING_API.md, QWEN_MONITORING.md)
- **WebSocket Updates**: Real-time agent status, log streaming, activity timeline
- **REST Endpoints**: `/api/agents`, `/api/services`, `/api/agents/{id}/status`, `/api/agents/{id}/logs`, `/api/activity`
- **Agent Status**: idle, working, error, offline
- **Service Health**: polling, monitoring, web_ui, agent_runtime (online/offline)
- **Dashboard**: Unified dashboard with agent cards, log viewer, activity feed

### Deployment (DEPLOYMENT.md, INSTALLATION.md)
- **System Requirements**: Python 3.12+, Ollama (optional), Git, systemd
- **Services**: agent-forge (main), agent-forge-auth (SSH/PAM authentication)
- **Configuration**: `config/agents.yaml`, `config/system.yaml`, `config/repositories.yaml`, `secrets/agents/*.token`
- **Port Firewall**: Allow 7996, 7997, 8080, 8897 for LAN access
- **Production**: Nginx reverse proxy, SSL termination, rate limiting, security headers

### Documentation Standards (LESSONS_LEARNED.md)
- **Workspace Identification**: Prominent header prevents agent confusion with other projects (Caramba, AudioTransfer)
- **Visual Diagrams**: Mermaid diagrams improve understanding (architecture, sequence, component)
- **Onboarding Checklists**: Structured reading order, critical warnings highlighted, common mistakes documented
- **Port Reference**: Table format for quick lookup, troubleshooting sections, configuration examples
- **Language Convention**: All docs/code/commits in English, agent communicates in Dutch when appropriate

---

## 🔧 Implementation Roadmap

### Phase 1: Issue Detection (Polling Service)
**Status**: ✅ Implemented
- [x] Polling service monitors GitHub repositories (config: `config/repositories.yaml`)
- [x] Detects new issues with specific labels or assigned to bot account
- [x] Claim mechanism prevents duplicate work (timeout: 60 minutes, configurable in `config/services/polling.yaml`)
- [x] Smart task recognition infers file creation from descriptive requirements (keywords: create, add, new, generate, make)
- [x] Subject normalization (Dutch → English slugs: stoel → chair, auto → car, raket → rocket)

### Phase 2: Agent Assignment (Coordinator)
**Status**: 🔄 In Progress
- [x] Coordinator evaluates issue type (creative vs. code vs. review)
- [x] Assigns appropriate agent (Developer for code, Bot for GitHub ops, Researcher for documentation)
- [ ] Task delegation with context (issue title, body, labels, assignee)
- [ ] Conflict resolution when multiple agents could handle same issue
- [ ] Priority queue for urgent issues (labels: critical, security)

### Phase 3: Task Execution (LLM-Driven File Editor)
**Status**: ✅ Implemented (ASCII Art), 🔄 In Progress (Code Modules)
- [x] ASCII art generation via `engine/operations/llm_file_editor.py`
  - [x] Extract subject from issue (`_extract_ascii_subject()`)
  - [x] Generate prompt with structured Markdown format
  - [x] Write to `docs/<subject>.md` with fenced `text` block
  - [x] Test suite with stubbed LLM responses (`tests/test_issue_handler_sun.py`)
- [ ] Code module generation
  - [ ] Infer file paths and module structure from issue
  - [ ] Generate implementation with tests and documentation
  - [ ] Run static analysis (bandit, flake8) before commit
  - [ ] Execute test suite and validate coverage
- [ ] Creative text generation
  - [ ] Poems, research notes, tutorials
  - [ ] Proper formatting (headings, lists, code blocks)
  - [ ] Grammar and spell check (via LLM or external tool)

### Phase 4: PR Creation (Bot Agent)
**Status**: ✅ Implemented, 🔄 Refinement Needed
- [x] Bot agent commits changes with agent signature
- [x] Updates CHANGELOG.md with entry for changes
- [x] Creates branch (format: `feat/<issue-number>-<slug>` or `fix/<issue-number>-<slug>`)
- [x] Opens PR with description referencing issue
- [ ] Add rendered Markdown preview for ASCII art PRs
- [ ] Include test results and coverage report in PR body
- [ ] Auto-label PR based on changes (ascii-art, code, docs, bugfix)
- [ ] Link PR to project board (move issue to "In Review")

### Phase 5: Security & Review (Security Auditor, PR Reviewer)
**Status**: ✅ Implemented (Security), 🔄 In Progress (Reviewer)
- [x] Security audit for non-trusted contributors (secrets, injection, malware, dependencies, licenses)
- [x] Block merge on critical/high severity issues (score < 70.0)
- [x] Post detailed security report as PR comment
- [ ] Automated code review (style, logic, best practices)
- [ ] Suggest improvements via review comments
- [ ] Request changes if tests fail or coverage drops
- [ ] Approve PR if all checks pass

### Phase 6: Monitoring & Validation
**Status**: ✅ Implemented, 🔄 Enhancement Needed
- [x] WebSocket monitoring with real-time agent status
- [x] Unified dashboard with agent cards and log viewer
- [x] Activity timeline across all agents
- [x] Structured logging with emoji conventions
- [ ] Alerting for stuck agents (working > 30 minutes without progress)
- [ ] Performance metrics (task completion time, success rate, error rate)
- [ ] Historical analytics (agents over time, repository activity heatmap)

---

## 🐛 Known Issues & Constraints

### Current Limitations
1. **LLM Response Quality**: ASCII art quality depends on LLM prompt engineering (style: "like a kid's drawing")
2. **No Retry Logic**: Failed tasks not automatically retried (manual intervention required)
3. **Limited Error Recovery**: Agent errors require service restart (no auto-recovery)
4. **Single-Repository Focus**: Polling service handles multiple repos, but agent workspace assumes single active project
5. **No Conflict Resolution**: Multiple agents claiming same issue not fully prevented (race condition possible)
6. **Manual Merge**: PRs require manual merge approval (no auto-merge even for trusted agents)

### Technical Debt (REFACTOR_PLAN.md)
- **Directory Structure**: Planned refactor to separate agents (data/YAML) from engine (code/Python) [Issue #69]
  - `agents/*.yaml` - Agent definitions (declarative, hot-swappable)
  - `engine/runners/` - Agent type runners (code_runner, bot_runner, coordinator_runner)
  - `engine/core/` - Core infrastructure (config_manager, service_manager)
  - `engine/operations/` - Tools & operations (git_operations, github_api_helper)
  - `engine/validation/` - Validation modules (instruction_parser, instruction_validator)
- **Import Churn**: ~50-60 files need import updates after refactor
- **Config Hot-Reload**: Agents should reload from YAML without service restart (not yet implemented)

### Security Considerations
- **Token Exposure**: Agents load GitHub tokens from `secrets/agents/*.token` (600 permissions required)
- **Trusted Agent Bypass**: Compromised trusted agent can bypass all security audits (mitigation: 2FA, regular audits)
- **Audit Performance**: 5-minute timeout prevents indefinite hangs, but large PRs may timeout

### Scalability Concerns
- **Single-Process Architecture**: All agents run in one Python process (no horizontal scaling)
- **WebSocket Bottleneck**: Single WebSocket server on port 7997 (max ~1000 concurrent connections)
- **Database Locking**: SQLite may lock under concurrent access (WAL mode helps but not sufficient for high load)
- **Rate Limiting**: GitHub API rate limits (5000/hour authenticated) may throttle high-frequency operations

---

## 📋 Next Steps

### Immediate Priorities
1. **Expand Test Coverage**: Create tests for chair, rocket, poem, research note, code module scenarios
2. **PR Enhancement**: Add rendered Markdown preview and test results to PR body
3. **Code Module Generation**: Implement end-to-end code generation with tests and static analysis
4. **Alert System**: Notify when agents stuck or tasks fail
5. **Dry-Run Validation**: Test full workflow in staging environment without production GitHub operations

### Future Enhancements
1. **Directory Refactor**: Complete engine separation (agents data vs. code) [Issue #69]
2. **Auto-Merge**: Trusted agent PRs auto-merge after security audit and tests pass
3. **Multi-Agent Coordination**: Multiple agents collaborate on complex issues (e.g., developer + reviewer + tester)
4. **Horizontal Scaling**: Multi-process or containerized deployment for high-throughput
5. **Advanced Analytics**: Task completion time, success rate trends, error pattern analysis
6. **WebUI Enhancements**: Drag-and-drop task assignment, manual agent control, log filtering

### Documentation Gaps
1. **API Stability**: No OpenAPI spec yet (planned after refactor stabilizes)
2. **Agent Development Guide**: How to create custom agent types
3. **Deployment Playbook**: Step-by-step production deployment with monitoring
4. **Troubleshooting Matrix**: Common errors with root cause and solutions
5. **Performance Tuning**: Optimize Ollama, reduce memory usage, speed up task execution

---

## 📚 Related Documentation

- [ARCHITECTURE.md](../ARCHITECTURE.md) - Complete system architecture and component overview
- [ASCII_AUTOMATION_WORKFLOW.md](ASCII_AUTOMATION_WORKFLOW.md) - Detailed ASCII art pipeline implementation
- [MULTI_AGENT_GITHUB_STRATEGY.md](MULTI_AGENT_GITHUB_STRATEGY.md) - Multi-agent coordination patterns
- [TESTING.md](TESTING.md) - Testing strategy, coverage targets, best practices
- [SECURITY_AUDIT.md](SECURITY_AUDIT.md) - Security scanning for PRs, audit criteria
- [INSTRUCTION_VALIDATION_GUIDE.md](INSTRUCTION_VALIDATION_GUIDE.md) - Pre-commit validation rules
- [MONITORING_API.md](MONITORING_API.md) - Real-time monitoring API reference
- [DEPLOYMENT.md](DEPLOYMENT.md) - Production deployment guide
- [INSTALLATION.md](INSTALLATION.md) - Quick start installation steps
- [LESSONS_LEARNED.md](LESSONS_LEARNED.md) - Key learnings from development
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Common issues and solutions
- [REFACTOR_PLAN.md](REFACTOR_PLAN.md) - Upcoming directory refactor plan

---

**Last Updated**: 2025-10-09  
**Maintained by**: Agent Forge Development Team  
**Questions?**: Create issue with label `documentation`
