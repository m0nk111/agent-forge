# Agent-Forge: Developer Onboarding & Project Goals

> **📖 Purpose**: Complete onboarding guide and project roadmap for developers (human & AI agents)  
> **🎯 Status**: In Active Development (2025-10-09)  
> **👥 Audience**: New contributors, AI agent developers, project stakeholders

---

## 📋 Table of Contents

1. [Quick Start for New Developers](#quick-start-for-new-developers)
2. [What Agent-Forge Is](#what-agent-forge-is)
3. [What Currently Works](#what-currently-works)
4. [Project Goals & Vision](#project-goals--vision)
5. [Development Roadmap](#development-roadmap)
6. [How to Contribute](#how-to-contribute)
7. [Essential Documentation Map](#essential-documentation-map)
8. [Known Issues & Limitations](#known-issues--limitations)

---

## 🚀 Quick Start for New Developers

### I'm a Human Developer

**1. Installation (15 minutes)**
- Read: [INSTALLATION.md](INSTALLATION.md) - Complete setup guide
- Install: Python 3.12+, Ollama, Git, systemd
- Configure: Create GitHub bot account (optional but recommended)

**2. Architecture Understanding (30 minutes)**
- Read: [ARCHITECTURE.md](../ARCHITECTURE.md) - System overview with diagrams
- Read: [AGENT_ROLES.md](AGENT_ROLES.md) - 7 agent types and responsibilities
- Explore: Port allocation (8080, 7997, 8897, 7996, 11434)

**3. First Contribution (1-2 hours)**
- Read: [CONTRIBUTING.md](CONTRIBUTING.md) - Contribution guidelines
- Read: [AGENT_DEVELOPMENT_GUIDE.md](AGENT_DEVELOPMENT_GUIDE.md) - Create custom agents
- Try: Run existing tests: `pytest tests/ -v`
- Create: Simple Hello World agent (see guide above)

**4. Deep Dive (ongoing)**
- Read: [TESTING.md](TESTING.md) - Testing strategy (70/20/10 pyramid)
- Read: [SECURITY_AUDIT.md](SECURITY_AUDIT.md) - Security scanning process
- Read: [DEPLOYMENT.md](DEPLOYMENT.md) - Production deployment
- Explore: Codebase with semantic search or grep

### I'm an AI Agent Developer

**1. System Context (required reading)**
- [ARCHITECTURE.md](../ARCHITECTURE.md) - System architecture, ports, services
- [AGENT_ROLES.md](AGENT_ROLES.md) - Agent types (Coordinator, Developer, Bot, Reviewer, Tester, Documenter, Researcher)
- [MULTI_AGENT_GITHUB_STRATEGY.md](MULTI_AGENT_GITHUB_STRATEGY.md) - Multi-agent coordination patterns

**2. Development Guidelines (required reading)**
- [AGENT_DEVELOPMENT_GUIDE.md](AGENT_DEVELOPMENT_GUIDE.md) - Create custom agents with examples
- [INSTRUCTION_VALIDATION_GUIDE.md](INSTRUCTION_VALIDATION_GUIDE.md) - Pre-commit validation rules
- [TESTING.md](TESTING.md) - Test pyramid, coverage targets, best practices
- [ERROR_RECOVERY.md](ERROR_RECOVERY.md) - Retry policies, circuit breakers, graceful degradation

**3. Operational Knowledge (required reading)**
- [PERFORMANCE_BENCHMARKS.md](PERFORMANCE_BENCHMARKS.md) - System metrics, capacity planning
- [MONITORING_API.md](MONITORING_API.md) - Real-time monitoring endpoints
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Common issues and solutions
- [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md) - Deployment procedures, rollback, emergencies

**4. Security & Best Practices (required reading)**
- [SECURITY_AUDIT.md](SECURITY_AUDIT.md) - Security scanning, audit criteria, scoring
- [TOKEN_SECURITY.md](TOKEN_SECURITY.md) - Token management, secrets handling
- [ANTI_SPAM_PROTECTION.md](ANTI_SPAM_PROTECTION.md) - Rate limiting rules
- [LESSONS_LEARNED.md](LESSONS_LEARNED.md) - Historical knowledge, avoid past mistakes

---

## 💡 What Agent-Forge Is

**Vision**: Autonomous multi-agent platform that transforms GitHub issues into pull requests without human intervention.

**Core Concept**: 
- User creates GitHub issue: "Create ASCII art of a rocket"
- Agent-Forge detects issue → assigns agent → generates content → creates PR → runs security audit → merges (if approved)
- **Zero human clicks** from issue creation to merged PR

**Key Differentiators**:
- ✅ **Multi-Agent Architecture**: 7 specialized agent roles work together
- ✅ **Security-First**: Mandatory security audit for non-trusted contributors
- ✅ **Real-Time Monitoring**: WebSocket-based live agent status and logs
- ✅ **Local LLM Support**: Ollama integration (no API costs)
- ✅ **GitHub Native**: Deep GitHub integration (issues, PRs, comments, reviews)

---

## ✅ What Currently Works

### Issue-to-PR Pipeline ✅

**1. Issue Detection** (Polling Service)
- ✅ Monitors GitHub repositories (config: `config/repositories.yaml`)
- ✅ Detects new issues with labels or assigned to bot account
- ✅ Claim mechanism prevents duplicate work (60min timeout)
- ✅ Smart task recognition (infers "create file X" from descriptions)
- ✅ Subject normalization (Dutch → English: stoel → chair)

**Implementation**: `engine/runners/polling_service.py`  
**Config**: `config/services/polling.yaml`  
**Documentation**: [BOT_USAGE_GUIDE.md](BOT_USAGE_GUIDE.md)

**2. Agent Assignment** (Coordinator)
- ✅ Evaluates issue type (creative vs. code vs. review)
- ✅ Assigns appropriate agent (Developer, Bot, Researcher)
- 🔄 Task delegation with full context (in progress)
- 🔄 Priority queue for urgent issues (planned)

**Implementation**: `engine/core/coordinator_agent.py`  
**Documentation**: [AGENT_ROLES.md](AGENT_ROLES.md), [MULTI_AGENT_GITHUB_STRATEGY.md](MULTI_AGENT_GITHUB_STRATEGY.md)

**3. Task Execution** (Agent Operations)
- ✅ **ASCII Art Generation**: `engine/operations/llm_file_editor.py`
  - Extracts subject from issue
  - Generates ASCII art via LLM
  - Writes to `docs/<subject>.md` with fenced code blocks
  - Test suite: `tests/test_issue_handler_sun.py`
- 🔄 **Code Generation**: Infer structure, generate with tests (in progress)
- 🔄 **Creative Text**: Poems, research notes, tutorials (in progress)

**Implementation**: `engine/operations/llm_file_editor.py`, `engine/operations/file_editor.py`  
**Documentation**: [AGENT_DEVELOPMENT_GUIDE.md](AGENT_DEVELOPMENT_GUIDE.md)

**4. PR Creation** (Bot Agent)
- ✅ Commits changes with agent signature
- ✅ Updates CHANGELOG.md automatically
- ✅ Creates branch (format: `feat/<issue>-<slug>`)
- ✅ Opens PR with description referencing issue
- 🔄 Rendered Markdown preview (planned)
- 🔄 Test results in PR body (planned)

**Implementation**: `engine/operations/bot_agent.py`, `engine/operations/github_api_helper.py`  
**Documentation**: [BOT_USAGE_GUIDE.md](BOT_USAGE_GUIDE.md)

**5. Security Audit** (Automated)
- ✅ Scans PRs from non-trusted contributors
- ✅ 6 security checks: secrets, injection, malware, dependencies, licenses, code analysis
- ✅ Security scoring (0-100, min 70 to pass)
- ✅ Blocks merge on critical/high severity
- ✅ Detailed report as PR comment

**Implementation**: `engine/validation/security_auditor.py`  
**Documentation**: [SECURITY_AUDIT.md](SECURITY_AUDIT.md)

**6. Monitoring & Dashboard** (Real-Time)
- ✅ WebSocket monitoring (port 7997)
- ✅ Unified dashboard (port 8897)
- ✅ Agent status cards (idle, working, error, offline)
- ✅ Live log streaming with emoji conventions (🐛, 🔍, ⚠️, ❌, ✅)
- ✅ Activity timeline across all agents

**Implementation**: `engine/runners/monitor_service.py`, `frontend/unified_dashboard.html`  
**Documentation**: [MONITORING_API.md](MONITORING_API.md), [QWEN_MONITORING.md](QWEN_MONITORING.md)

### Supporting Infrastructure ✅

**Authentication**
- ✅ SSH/PAM authentication (system credentials)
- ✅ JWT sessions (24h expiry)
- ✅ Login page with auto-redirect
- 🔄 Google OAuth (optional, partially implemented)

**Implementation**: `api/auth_routes.py`, `frontend/login.html`  
**Documentation**: [SSH_AUTHENTICATION.md](SSH_AUTHENTICATION.md), [INSTALLATION.md](INSTALLATION.md#dashboard-authentication-setup)

**Configuration Management**
- ✅ YAML-based configuration (`config/agents.yaml`, `config/system.yaml`)
- ✅ Hot-reload for some configs (not all yet)
- ✅ Secrets management (`secrets/agents/*.token` with 600 permissions)
- ✅ Environment variable support

**Implementation**: `engine/core/config_manager.py`  
**Documentation**: [TOKEN_SECURITY.md](TOKEN_SECURITY.md)

**Validation & Quality**
- ✅ Pre-commit instruction validation
- ✅ Conventional commit enforcement
- ✅ Changelog requirement checks
- ✅ File location rules (root directory cleanup)
- ✅ Port usage validation

**Implementation**: `engine/validation/instruction_validator.py`, `engine/validation/instruction_parser.py`  
**Documentation**: [INSTRUCTION_VALIDATION_GUIDE.md](INSTRUCTION_VALIDATION_GUIDE.md)

**Rate Limiting**
- ✅ Comment limits: 3/min, 30/hour, 200/day
- ✅ Issue limits: 10/hour, 50/day
- ✅ PR limits: 5/hour, 20/day
- ✅ Duplicate detection (10min cache)
- ✅ Exponential backoff on violations

**Implementation**: `engine/operations/github_api_helper.py` (rate limiting logic)  
**Documentation**: [ANTI_SPAM_PROTECTION.md](ANTI_SPAM_PROTECTION.md)

---

## 🎯 Project Goals & Vision

---

## 🎯 Project Goals & Vision

### Primary Goal: Full Autonomous Issue-to-PR Pipeline

**The Vision**: User creates GitHub issue → Agent-Forge handles everything → PR merged without human intervention

**Completion Criteria**: Platform can automatically:

1. **Detect** newly created GitHub issues
2. **Assign** appropriate agent based on issue type
3. **Execute** task end-to-end:
   - Generate ASCII art (e.g., chair, rocket, diagram)
   - Write creative text (poems, research notes)
   - Implement functional code modules with tests
4. **Produce** pull requests with documentation updates
5. **Audit** security and quality automatically
6. **Merge** if all checks pass (trusted agents only)

Until all above works reliably, development continues.

### Acceptance Criteria (Detailed)

#### Core Automation
- [x] **Issue Detection**: Polling service detects new issues automatically
- [x] **Agent Assignment**: Coordinator assigns agent based on issue type
- [ ] **Autonomous Execution**: Agent completes task without human prompts (70% done)
- [ ] **PR Creation**: Agent commits, updates changelog, creates PR (90% done, needs preview)
- [x] **Security Audit**: Mandatory audit for non-trusted contributors
- [ ] **PR Review**: Reviewer agent validates before merge (50% done)
- [ ] **Auto-Merge**: Trusted agent PRs merge automatically after checks (not started)

#### Monitoring & Validation
- [x] **Real-time Monitoring**: WebSocket shows agent status and logs
- [x] **Dashboard Integration**: Unified dashboard with all agents visible
- [x] **Structured Logging**: Emoji conventions (🐛, 🔍, ⚠️, ❌, ✅, 📊, 🔧)
- [x] **Rate Limiting**: Anti-spam protection enforced
- [x] **Instruction Validation**: Pre-commit validation for all rules

#### Artifact Quality
- [x] **Markdown Generation**: ASCII art in `docs/<subject>.md` with proper fencing
- [ ] **Code Quality**: Generated code passes security scans (80% done)
- [x] **Changelog Discipline**: Every change has CHANGELOG.md entry
- [x] **Conventional Commits**: All commits follow format
- [ ] **Test Coverage**: Generated code includes tests (50% done, needs code gen)

#### Testing & Repeatability
- [x] **ASCII Tests**: `tests/test_issue_handler_sun.py` passes
- [ ] **Integration Tests**: End-to-end with real GitHub API (30% done)
- [ ] **E2E Validation**: Dry-run full workflow without production deploy (not started)
- [ ] **PR Verification**: Generated PRs meet all quality standards (70% done)

### Secondary Goals

**Developer Experience**
- [x] Comprehensive documentation (32 markdown files)
- [x] Quick start guide for new developers (this document)
- [ ] Video tutorials for setup and development (not started)
- [ ] Interactive demo environment (not started)

**Performance & Scalability**
- [ ] Handle 50+ issues/day per agent (currently ~12-15)
- [ ] Support 10+ concurrent agents (currently tested with 3-5)
- [ ] Horizontal scaling via containers (not started)
- [ ] Database migration from SQLite to PostgreSQL (not started)

**Advanced Features**
- [ ] Multi-agent collaboration on complex issues (not started)
- [ ] Natural language issue processing (improved context understanding)
- [ ] Code refactoring and optimization suggestions (not started)
- [ ] Automated dependency updates (not started)

---

## 🔧 Development Roadmap

### Phase 1: Issue Detection ✅ COMPLETE

**Status**: ✅ Implemented and working in production

**Achievements**:
- [x] Polling service monitors GitHub repositories
- [x] Detects new issues with labels or bot assignment
- [x] Claim mechanism prevents duplicate work (60min timeout)
- [x] Smart task recognition (infers file creation from descriptions)
- [x] Subject normalization (Dutch → English slugs)

**Key Files**:
- `engine/runners/polling_service.py` - Main polling loop
- `config/services/polling.yaml` - Configuration
- `config/repositories.yaml` - Monitored repositories

**Documentation**: [BOT_USAGE_GUIDE.md](BOT_USAGE_GUIDE.md)

---

### Phase 2: Agent Assignment ✅ MOSTLY COMPLETE

**Status**: 🔄 Core implemented, refinement in progress

**Achievements**:
- [x] Coordinator evaluates issue type
- [x] Assigns appropriate agent role
- [ ] Task delegation with full context (in progress)
- [ ] Priority queue for urgent issues (planned)
- [ ] Conflict resolution for multi-agent scenarios (planned)

**Key Files**:
- `engine/core/coordinator_agent.py` - Coordination logic
- `config/agents.yaml` - Agent definitions and capabilities

**Documentation**: [AGENT_ROLES.md](AGENT_ROLES.md), [MULTI_AGENT_GITHUB_STRATEGY.md](MULTI_AGENT_GITHUB_STRATEGY.md)

**Next Steps**:
1. Implement priority queue (labels: critical, security)
2. Add conflict resolution when multiple agents could handle same issue
3. Improve context passing (include issue labels, comments, assignee history)

---

### Phase 3: Task Execution 🔄 IN PROGRESS

**Status**: ✅ ASCII art working, 🔄 code generation in progress

#### 3A: ASCII Art Generation ✅ COMPLETE

**Achievements**:
- [x] Extract subject from issue title/body
- [x] Generate ASCII art via LLM with style hints
- [x] Write to `docs/<subject>.md` with fenced text blocks
- [x] Test suite with stubbed LLM responses

**Key Files**:
- `engine/operations/llm_file_editor.py` - LLM-based file generation
- `tests/test_issue_handler_sun.py` - ASCII art test suite

**Documentation**: [ASCII_AUTOMATION_WORKFLOW.md](ASCII_AUTOMATION_WORKFLOW.md)

#### 3B: Code Module Generation ✅ FUNCTIONAL

**Status**: 85% complete - **Core infrastructure working, E2E validation pending**

**Achievements** (2025-10-10):
- [x] **Core Implementation**: `code_generator.py` (459 lines) with full workflow
  - Module specification inference from issue text (regex + keyword matching)
  - LLM-powered implementation generation with type hints and docstrings
  - Automatic test suite generation (pytest, fixtures, >80% coverage target)
  - Static analysis integration (bandit security, flake8 style)
  - Automated test execution with pass/fail parsing
  - Retry mechanism (max 3 attempts) with error feedback to LLM
- [x] **Integration**: Connected to `issue_handler.py` workflow
  - Code generation detection in `_task_to_action` (keywords: implement, module, function, class)
  - Full execution in `_execute_plan` with result tracking
  - Issue context passing (title, body, labels) for spec inference
- [x] **Unit Tests**: 22 tests, all passing ✅
  - ModuleSpec inference (7 tests): explicit paths, keywords, edge cases
  - Code generation workflow (4 tests): success, retry, failures
  - Static analysis (3 tests), test execution (3 tests), response cleaning (3 tests)
  - GenerationResult dataclass (2 tests)
- [x] **Integration Tests**: Real LLM validation ✅
  - Calculator module: LLM generates complete implementation + tests
  - Static analysis passed, retry mechanism functional
  - Minor issue: generated tests use absolute imports (prompt tuning needed, not blocker)
  - Test execution: 67 seconds with qwen2.5-coder:7b
- [ ] **E2E Pipeline**: End-to-end issue → PR flow (not tested yet)
- [ ] **Prompt Optimization**: Fix import patterns in generated tests

**Key Files** (implemented):
- `engine/operations/code_generator.py` - Code generation logic ✅
- `tests/test_code_generator.py` - Unit tests (22 passing) ✅
- `tests/test_code_generator_integration.py` - Integration tests ✅
- Static analysis: uses existing bandit/flake8 tools ✅
- Test runner: uses existing pytest integration ✅

**Documentation**: [CHANGELOG.md](../CHANGELOG.md#phase-3b-autonomous-code-module-generation) (comprehensive entry)

**Known Limitations**:
- Generated test imports need refinement (absolute vs relative paths)
- Keyword-based path inference uses fixed mappings (helper → engine/operations/helper.py)
- No coverage metric calculation yet (pytest-cov integration pending)
- Retry mechanism error accumulation could be improved

**Next Steps**:
1. ~~Design code generation prompt templates~~ ✅ **DONE**
2. ~~Implement file structure inference~~ ✅ **DONE**
3. ~~Add test generation logic~~ ✅ **DONE**
4. ~~Integrate with static analysis tools~~ ✅ **DONE**
5. ~~Create retry mechanism for failed generations~~ ✅ **DONE**
6. **NEW**: End-to-end pipeline validation (create test GitHub issue, verify full flow)
7. **NEW**: Prompt optimization for better import patterns
8. **NEW**: Coverage metric integration (pytest-cov)

#### 3C: Creative Text Generation 🔄 PLANNED

**Status**: Not started, lower priority

**Scope**:
- Poems, research notes, tutorials
- Proper formatting (headings, lists, code blocks)
- Grammar and spell check

**Documentation**: [AGENT_DEVELOPMENT_GUIDE.md](AGENT_DEVELOPMENT_GUIDE.md)

---

### Phase 4: PR Creation ✅ MOSTLY COMPLETE

**Status**: ✅ Core implemented, needs enhancement

**Achievements**:
- [x] Bot agent commits changes with agent signature
- [x] Updates CHANGELOG.md automatically
- [x] Creates branch (format: `feat/<issue>-<slug>`)
- [x] Opens PR with description referencing issue
- [ ] Rendered Markdown preview (not started)
- [ ] Test results in PR body (not started)
- [ ] Auto-label PR based on changes (not started)

**Key Files**:
- `engine/operations/bot_agent.py` - Bot operations
- `engine/operations/github_api_helper.py` - GitHub API wrapper
- `engine/operations/git_operations.py` - Git commands

**Documentation**: [BOT_USAGE_GUIDE.md](BOT_USAGE_GUIDE.md)

**Next Steps**:
1. Add Markdown rendering for ASCII art PRs (show preview image)
2. Include test results and coverage report in PR body
3. Auto-label PRs (ascii-art, code, docs, bugfix)
4. Link PR to project board (move issue to "In Review")

---

### Phase 5: Security & Review ✅ SECURITY COMPLETE, 🔄 REVIEW IN PROGRESS

**Status**: ✅ Security audit working, 🔄 code review partial

#### 5A: Security Audit ✅ COMPLETE

**Achievements**:
- [x] 6 security checks: secrets, injection, malware, dependencies, licenses, code analysis
- [x] Security scoring (0-100, min 70 to pass)
- [x] Block merge on critical/high severity
- [x] Detailed report as PR comment
- [x] Trusted agent bypass

**Key Files**:
- `engine/validation/security_auditor.py` - Main audit logic
- `config/agents.yaml` - Trusted agent configuration

**Documentation**: [SECURITY_AUDIT.md](SECURITY_AUDIT.md), [TOKEN_SECURITY.md](TOKEN_SECURITY.md)

#### 5B: PR Code Review 🔄 IN PROGRESS

**Status**: 40% complete, needs LLM integration

**TODO**:
- [ ] Automated code review (style, logic, best practices)
- [ ] Suggest improvements via review comments
- [ ] Request changes if tests fail or coverage drops
- [ ] Approve PR if all checks pass
- [ ] Integration with PR reviewer agent

**Key Files** (to enhance):
- `engine/operations/pr_reviewer.py` - PR review logic (stub exists)

**Documentation**: [AGENT_ROLES.md](AGENT_ROLES.md) (Reviewer Agent section)

**Next Steps**:
1. Design review prompt templates
2. Implement diff analysis
3. Add comment posting logic
4. Create review criteria configuration
5. Test with real PRs

---

### Phase 6: Monitoring & Validation ✅ COMPLETE, 🔄 ENHANCEMENTS PLANNED

**Status**: ✅ Core monitoring working, enhancements planned

**Achievements**:
- [x] WebSocket monitoring with real-time agent status
- [x] Unified dashboard with agent cards and log viewer
- [x] Activity timeline across all agents
- [x] Structured logging with emoji conventions
- [ ] Alerting for stuck agents (not started)
- [ ] Performance metrics tracking (partial)
- [ ] Historical analytics (not started)

**Key Files**:
- `engine/runners/monitor_service.py` - WebSocket server
- `frontend/unified_dashboard.html` - Dashboard UI
- `api/monitoring_routes.py` - REST API endpoints

**Documentation**: [MONITORING_API.md](MONITORING_API.md), [QWEN_MONITORING.md](QWEN_MONITORING.md)

**Next Steps**:
1. Implement alerting (email, Slack, webhook)
2. Add performance metrics (task time, success rate, error rate)
3. Create historical analytics dashboard
4. Add log filtering and search
5. Implement agent health checks with auto-restart

---

## 🤝 How to Contribute

### For Human Developers

**1. Pick an Issue**
- Browse: [GitHub Issues](https://github.com/m0nk111/agent-forge/issues)
- Filter: `good-first-issue`, `help-wanted`, `documentation`
- Claim: Comment "I'll work on this" before starting

**2. Development Workflow**
```bash
# Clone and setup
git clone https://github.com/m0nk111/agent-forge.git
cd agent-forge
pip install -r requirements.txt

# Create branch
git checkout -b feat/my-feature

# Make changes
# ... edit files ...

# Test
pytest tests/ -v

# Commit (follows conventional commits)
git commit -m "feat(module): description"

# Push and create PR
git push origin feat/my-feature
```

**3. Quality Checklist**
- [ ] Tests added/updated
- [ ] CHANGELOG.md entry added
- [ ] Documentation updated
- [ ] Code passes linting: `pylint engine/ api/`
- [ ] All tests pass: `pytest tests/ -v`

**Documentation**: [CONTRIBUTING.md](CONTRIBUTING.md), [TESTING.md](TESTING.md)

### For AI Agent Developers

**1. Understand System**
- Read all required documentation (see "I'm an AI Agent Developer" section above)
- Study existing agent implementations in `engine/operations/`
- Review test suites in `tests/`

**2. Autonomous Workflow**
- Claim issue by self-assigning
- Comment "🤖 Starting work on this issue"
- Follow instruction validation rules strictly
- Create PR with comprehensive description
- Respond to review comments

**3. Quality Standards**
- All code must pass security audit
- Minimum 70% test coverage
- Conventional commit messages
- CHANGELOG.md entry required
- No secrets in code (use `secrets/agents/*.token`)

**Documentation**: [AGENT_DEVELOPMENT_GUIDE.md](AGENT_DEVELOPMENT_GUIDE.md), [INSTRUCTION_VALIDATION_GUIDE.md](INSTRUCTION_VALIDATION_GUIDE.md)

---

## 📚 Essential Documentation Map

### 🚀 Getting Started (Read First)
1. **[README.md](../README.md)** - Project overview, quick start
2. **[INSTALLATION.md](INSTALLATION.md)** - Complete setup guide (system + bot + auth)
3. **[ARCHITECTURE.md](../ARCHITECTURE.md)** - System architecture with diagrams
4. **This Document** - Onboarding and project goals

### 🏗️ Architecture & Design
5. **[AGENT_ROLES.md](AGENT_ROLES.md)** - 7 agent types and responsibilities
6. **[AGENT_DEVELOPMENT_GUIDE.md](AGENT_DEVELOPMENT_GUIDE.md)** - Create custom agents (NEW ⭐)
7. **[MULTI_AGENT_GITHUB_STRATEGY.md](MULTI_AGENT_GITHUB_STRATEGY.md)** - Multi-agent coordination
8. **[ASCII_AUTOMATION_WORKFLOW.md](ASCII_AUTOMATION_WORKFLOW.md)** - ASCII art pipeline details

### 🔒 Security & Quality
9. **[SECURITY_AUDIT.md](SECURITY_AUDIT.md)** - Security scanning process
10. **[TOKEN_SECURITY.md](TOKEN_SECURITY.md)** - Token management (with Quick Start ⭐)
11. **[SSH_AUTHENTICATION.md](SSH_AUTHENTICATION.md)** - Dashboard authentication (NEW ⭐)
12. **[ANTI_SPAM_PROTECTION.md](ANTI_SPAM_PROTECTION.md)** - Rate limiting rules
13. **[INSTRUCTION_VALIDATION_GUIDE.md](INSTRUCTION_VALIDATION_GUIDE.md)** - Pre-commit validation

### 🧪 Testing & Operations
14. **[TESTING.md](TESTING.md)** - Testing strategy (70/20/10 pyramid)
15. **[ERROR_RECOVERY.md](ERROR_RECOVERY.md)** - Retry policies, circuit breakers (NEW ⭐)
16. **[PERFORMANCE_BENCHMARKS.md](PERFORMANCE_BENCHMARKS.md)** - Metrics, capacity planning (NEW ⭐)
17. **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Common issues and solutions
18. **[MONITORING_API.md](MONITORING_API.md)** - Real-time monitoring endpoints
19. **[QWEN_MONITORING.md](QWEN_MONITORING.md)** - Qwen-specific monitoring

### 🚢 Deployment & Operations
20. **[DEPLOYMENT.md](DEPLOYMENT.md)** - Production deployment guide
21. **[DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md)** - Step-by-step + rollback (ENHANCED ⭐)
22. **[BOT_USAGE_GUIDE.md](BOT_USAGE_GUIDE.md)** - Bot agent operations
23. **[LOCAL_SHELL_ACCESS.md](LOCAL_SHELL_ACCESS.md)** - Shell access configuration

### 📖 Reference & Planning
24. **[API.md](API.md)** - API documentation
25. **[PORT_REFERENCE.md](PORT_REFERENCE.md)** - Port assignments (8080, 7997, 8897, 7996, 11434)
26. **[REFACTOR_PLAN.md](REFACTOR_PLAN.md)** - Directory refactor plan (Issue #69)
27. **[LESSONS_LEARNED.md](LESSONS_LEARNED.md)** - Historical knowledge, avoid past mistakes
28. **[AGENT_ONBOARDING.md](AGENT_ONBOARDING.md)** - Agent workflow details
29. **[CONSOLIDATION_PLAN.md](CONSOLIDATION_PLAN.md)** - Doc consolidation strategy

### 🤝 Contributing
30. **[CONTRIBUTING.md](CONTRIBUTING.md)** - Contribution guidelines
31. **[LICENSE](../LICENSE)** - Open source license
32. **[COMMERCIAL-LICENSE.md](COMMERCIAL-LICENSE.md)** - Commercial terms

**⭐ = Recently created or significantly enhanced (2025-10-09)**

### Documentation Tips

**For Quick Reference:**
- PORT_REFERENCE.md - Port assignments
- API.md - REST endpoints
- MONITORING_API.md - WebSocket monitoring

**For Troubleshooting:**
- TROUBLESHOOTING.md - Common problems
- ERROR_RECOVERY.md - Recovery strategies
- DEPLOYMENT_CHECKLIST.md - Rollback procedures

**For Development:**
- AGENT_DEVELOPMENT_GUIDE.md - Create agents
- TESTING.md - Testing strategy
- INSTRUCTION_VALIDATION_GUIDE.md - Validation rules

### Current Limitations

1. **Code Generation Not Fully Autonomous**
   - ASCII art generation: ✅ Works end-to-end
   - Creative text: 🔄 Partial (needs testing with more examples)
   - Code modules: ❌ Not yet implemented (see Phase 3B roadmap)
   - **Workaround**: Manual implementation or use ASCII art pipeline as template

2. **PR Preview Missing**
   - PRs lack rendered Markdown preview
   - No test results or coverage report in PR body
   - **Workaround**: Review PR files directly, run tests locally

3. **Agent Assignment Logic Basic**
   - No priority queue for urgent issues
   - No conflict resolution for multi-agent scenarios
   - **Workaround**: Manual assignment via labels or issue assignment

4. **Limited LLM Model Support**
   - Currently tested with Ollama (qwen2.5-coder:32b)
   - No fallback for model errors
   - **Workaround**: Ensure Ollama is running, check model availability

5. **No Horizontal Scaling**
   - Single-instance deployment only
   - SQLite database limits concurrency
   - **Workaround**: Use systemd service restart, avoid simultaneous high loads

6. **Rate Limiting Edge Cases**
   - Cooldown can block legitimate operations
   - No manual override for trusted users
   - **Workaround**: Wait for cooldown period, check logs for rate limit status

### Technical Debt

See **[REFACTOR_PLAN.md](REFACTOR_PLAN.md)** for detailed technical debt tracking.

**High Priority**:
- **Directory Structure**: Root directory cleanup (Issue #69) - move all files to narrow/deep subdirectories
- **Test Coverage**: Integration tests need assertions (many use print statements only)
- **Error Recovery**: Implement retry policies and circuit breakers (see [ERROR_RECOVERY.md](ERROR_RECOVERY.md))

**Medium Priority**:
- **Database Migration**: SQLite → PostgreSQL for better concurrency
- **Configuration Validation**: JSON Schema for YAML config files
- **API Documentation**: OpenAPI spec for REST endpoints

**Low Priority**:
- **Frontend Framework**: Migrate from vanilla HTML/JS to React or Vue
- **Logging Standardization**: Use structured logging library (structlog)
- **Monitoring Alerts**: Email/Slack notifications for stuck agents

### Security Considerations

See **[SECURITY_AUDIT.md](SECURITY_AUDIT.md)** and **[TOKEN_SECURITY.md](TOKEN_SECURITY.md)** for comprehensive security information.

**Current Risks**:
- **Token Exposure**: GitHub tokens in `secrets/agents/*.token` (file permissions mitigate)
- **Injection Attacks**: LLM-generated code not fully sandboxed (bandit scans mitigate)
- **SSH Authentication**: PAM authentication requires root access (systemd service runs as user)
- **Rate Limit Bypass**: Trusted agents bypass rate limits (intentional, minimal risk)

**Mitigation Status**:
- ✅ Security audit mandatory for non-trusted contributors
- ✅ Secrets detection in code (regex patterns, entropy analysis)
- ✅ Injection pattern detection (SQL, command, path traversal)
- ✅ Dependency CVE scanning (safety tool)
- 🔄 Sandboxed code execution (planned, not implemented)
- 🔄 Token rotation automation (manual process documented)

### Scalability Concerns

See **[PERFORMANCE_BENCHMARKS.md](PERFORMANCE_BENCHMARKS.md)** for detailed capacity planning.

**Current Capacity**:
- **Issues per day**: ~15-20 per agent (limited by LLM inference time)
- **Concurrent agents**: 3-5 (tested), 10+ (theoretical, untested)
- **Repository monitoring**: 5 repositories (current config)
- **Database**: SQLite suitable for <100 issues/day, <10,000 total issues

**Bottlenecks**:
- **LLM Inference**: 10-30 seconds per generation (Ollama on RTX 4090)
- **GitHub API**: 5,000 requests/hour (authenticated), rate limiting protection
- **Polling Frequency**: 60-second intervals (configurable in `config/services/polling.yaml`)
- **WebSocket Connections**: ~50 concurrent (single monitor_service instance)

**Scaling Strategies**:
- **Horizontal Scaling**: Multiple agent instances with load balancer (not implemented)
- **Database Sharding**: Partition by repository or agent (requires PostgreSQL)
- **Model Optimization**: Use smaller LLM models (qwen2.5-coder:7b) for simple tasks
- **Caching**: Cache LLM responses for similar tasks (not implemented)

### Known Bugs & Workarounds

See **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** for step-by-step debugging guides.

**Active Bugs**:
- **Polling Service Restart**: Occasionally fails to reconnect to GitHub API after network disruption
  - **Workaround**: `systemctl restart agent-forge`, check logs for "Connection reset by peer"
  - **Fix ETA**: Not scheduled (low priority, rare occurrence)

- **Dashboard WebSocket Timeout**: Browser disconnects after 10 minutes idle
  - **Workaround**: Refresh dashboard page, WebSocket reconnects automatically
  - **Fix ETA**: Not scheduled (acceptable behavior, reconnect works)

- **CHANGELOG.md Merge Conflicts**: Multiple agents editing simultaneously
  - **Workaround**: Manual resolution, use `git pull --rebase`
  - **Fix ETA**: Q2 2025 (requires locking mechanism or append-only log)

**Recently Fixed**:
- ✅ Claim timeout username mismatch (fixed 2025-10-08, commit 3626a3d)
- ✅ SSH authentication systemd compatibility (fixed 2025-10-09, commit 9e1d49b)
- ✅ Token security quickstart duplication (fixed 2025-10-09, consolidated docs)

### Documentation Gaps

**Missing Documentation** (planned):
- [ ] Video tutorial for setup and first contribution
- [ ] Interactive API documentation (Swagger UI)
- [ ] Agent development example (full walkthrough with code)
- [ ] Performance tuning guide (LLM model selection, batch processing)
- [ ] Disaster recovery procedures (backup, restore, rollback)

**Incomplete Documentation** (in progress):
- 🔄 ERROR_RECOVERY.md - Needs more retry policy examples
- 🔄 PERFORMANCE_BENCHMARKS.md - Needs load testing results
- 🔄 AGENT_DEVELOPMENT_GUIDE.md - Needs advanced agent patterns
- 🔄 DEPLOYMENT_CHECKLIST.md - Needs rollback procedures

**Documentation Quality**:
- ✅ 32 markdown files (reduced from 38, -16%)
- ✅ Visual diagrams in ARCHITECTURE.md (Mermaid)
- ✅ Quick Start sections in major guides
- ✅ Code examples in most technical docs
- 🔄 Cross-references need validation (some broken links)

---

## 🎉 Next Steps & Contributing

Ready to contribute? See **[CONTRIBUTING.md](CONTRIBUTING.md)** for detailed guidelines.

**For New Contributors**:
1. Join discussion on [GitHub Issues](https://github.com/m0nk111/agent-forge/issues)
2. Look for `good-first-issue` or `help-wanted` labels
3. Comment "I'll work on this" to claim issue
4. Follow development workflow in "How to Contribute" section above

**For AI Agent Developers**:
1. Read required documentation (see "I'm an AI Agent Developer" section)
2. Test locally with `pytest tests/ -v`
3. Create PR following quality checklist
4. Respond to security audit and code review comments

**Priority Development Areas** (help wanted):
- 🔴 **High Priority**: Code generation (Phase 3B), PR preview, test coverage
- 🟡 **Medium Priority**: Priority queue, conflict resolution, database migration
- 🟢 **Low Priority**: Frontend framework, monitoring alerts, video tutorials

**Questions or Issues?**
- 📧 Create GitHub issue: [Report Bug](https://github.com/m0nk111/agent-forge/issues/new?labels=bug)
- 💬 Discuss feature: [Feature Request](https://github.com/m0nk111/agent-forge/issues/new?labels=enhancement)
- 📚 Documentation: [Docs Issue](https://github.com/m0nk111/agent-forge/issues/new?labels=documentation)

---
**Document Version**: 2.0 (2025-10-09)  
**Last Updated**: 2025-10-09 by documentation consolidation effort  
**Previous Version**: 1.0 (provisional goal structure)  
**Status**: � Living document, updated as project evolves

