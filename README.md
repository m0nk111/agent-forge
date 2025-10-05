# Agent Forge 🔨

**Multi-LLM Agent Framework powered by Ollama**

Agent Forge is a framework for creating autonomous coding agents using different LLMs via Ollama. Each agent can work on specific tasks, issues, or projects using the strengths of different models (Qwen2.5-Coder, CodeLlama, DeepSeek-Coder, etc.).

## Features

### Core Capabilities
- 🤖 **Multi-Model Support**: Use different LLMs for different tasks
- 📋 **Phase-Based Execution**: Break down complex tasks into manageable phases
- 🎨 **Code Generation**: Automatic file creation from LLM output
- 🔄 **Streaming Support**: Real-time output for long-running generations
- 🧪 **Dry Run Mode**: Test agent behavior without making changes
- 🎯 **Custom Tasks**: Execute one-off tasks outside predefined phases
- 📊 **Progress Tracking**: Detailed status and completion metrics

### Advanced Capabilities (Recently Added)
- ✏️ **File Editing**: Edit existing files with `replace_in_file()`, `insert_at_line()`, `append_to_file()`
- 🖥️ **Terminal Execution**: Run commands securely with whitelist/blacklist controls
- 🧪 **Test Execution**: Auto-detect and run pytest/jest tests with result parsing
- 🔍 **Codebase Search**: grep-based search, find functions/classes/imports across projects
- 🐛 **Error Checking**: Syntax validation, linting (pylint/flake8/eslint), type checking (mypy)
- 🌐 **Web Documentation**: Fetch docs from trusted sources (Python docs, GitHub, Stack Overflow) with caching
- 🤖 **Autonomous Polling**: Automatically check for assigned GitHub issues and start workflows (Issue #17)
- 🔍 **Automated Code Review**: AI-powered PR reviews with quality checks and feedback (Issue #25)
- 🤖 **Bot Account Agent**: Dedicated bot for GitHub operations without email spam (Issue #35)
- 🌐 **External Knowledge**: MCP integration placeholders
- 📚 **Documentation Loading**: Auto-load project docs (ARCHITECTURE.md, README.md, etc.)
- 🗂️ **Workspace Awareness**: Explore project structure, validate paths, find files
- 🧠 **Context Management**: Sliding window (6000 tokens) with smart truncation

## Quick Start

### Prerequisites

- Python 3.12+
- Ollama installed and running
- At least one LLM model pulled (e.g., `ollama pull qwen2.5-coder:7b`)

### Installation

```bash
git clone https://github.com/m0nk111/agent-forge.git
cd agent-forge
pip install -r requirements.txt
```

### Basic Usage

```bash
# List available configs
ls configs/

# Check Ollama status
python3 agents/qwen_agent.py --help

# Execute with config file (dry run)
python3 agents/qwen_agent.py --config configs/caramba_personality_ai.yaml --phase 1 --dry-run

# Execute a specific phase (real)
python3 agents/qwen_agent.py --config configs/caramba_personality_ai.yaml --phase 1

# Execute all phases
python3 agents/qwen_agent.py --config configs/caramba_personality_ai.yaml --phase all

# Execute a custom task
python3 agents/qwen_agent.py --task "Create authentication middleware" --project-root /path/to/project
```

## Monitoring & Dashboard

Agent Forge includes a real-time monitoring dashboard for tracking agent activity, logs, and progress.

### Starting the Dashboard

```bash
# Start dashboard server (accessible on LAN)
./launch_dashboard.sh

# Or manually:
python3 -m http.server 8897 --directory frontend --bind 0.0.0.0
```

### Accessing the Dashboard

- **Local**: http://localhost:8897/dashboard.html
- **LAN**: http://192.168.1.26:8897/dashboard.html (replace with your machine's IP)
- **Auto-detection**: The dashboard automatically detects your network and connects to the WebSocket server

### WebSocket Server

The monitoring service runs on port 7997 and is accessible from:
- Local: ws://localhost:7997/ws/monitor
- LAN: ws://192.168.1.26:7997/ws/monitor

### Using Monitoring with Agents

Enable monitoring when running agents:

```bash
# Run agent with monitoring enabled
python3 agents/qwen_agent.py --config configs/my_project.yaml --phase 1 --enable-monitoring --agent-id "my-agent"

# Test monitoring integration
python3 test_qwen_monitoring.py
```

See [docs/QWEN_MONITORING.md](docs/QWEN_MONITORING.md) for detailed documentation.

## Project Structure

```
agent-forge/
├── agents/              # Agent implementations
│   ├── qwen_agent.py           # Generic Qwen agent (config-driven)
│   ├── file_editor.py          # File editing operations
│   ├── terminal_operations.py  # Terminal command execution
│   ├── test_runner.py          # Test execution and parsing
│   ├── codebase_search.py      # Code search (grep/semantic)
│   ├── error_checker.py        # Syntax/lint/type checking
│   ├── mcp_client.py           # MCP integration (placeholder)
│   ├── workspace_tools.py      # Project structure exploration
│   ├── context_manager.py      # Context window management
│   ├── git_operations.py       # Git commit/push operations
│   └── bot_operations.py       # GitHub issue/PR management
├── configs/             # Project configurations
│   └── caramba_personality_ai.yaml  # Example: Caramba Issue #7
├── docs/                # Documentation
│   ├── AGENT_CHANGELOG_POLICY.md
│   ├── BOT_USAGE_GUIDE.md
│   └── ...
├── tests/               # Unit tests
├── examples/            # Example configurations
└── README.md
```

## Creating a New Agent

Agents in Agent Forge are driven by YAML configuration files. Create a new config file in `configs/` for your project.

### Example: Creating an Agent Configuration

```yaml
# configs/my_project.yaml
project:
  name: "My Project"
  root: "/path/to/project"
  issue: "Feature XYZ"

model:
  name: "qwen2.5-coder:7b"
  ollama_url: "http://localhost:11434"

context:
  description: "Brief project description"
  structure: |
    - src/ - Source code
    - tests/ - Unit tests
  tech_stack:
    - "Python 3.12"
    - "FastAPI"
  
phases:
  1:
    name: "Setup"
    hours: 2
    tasks:
      - "Create project structure"
      - "Add configuration files"
```

Then run:
```bash
python3 agents/qwen_agent.py --config configs/my_project.yaml --phase 1 --dry-run
```

## Supported Models

Agent Forge works with any Ollama-compatible model, but is optimized for:

- **qwen2.5-coder:7b** - Excellent for Python/FastAPI (4.7GB)
- **codellama:7b** - Strong general coding (3.8GB)
- **deepseek-coder:6.7b** - Fast, efficient (3.8GB)
- **starcoder2:7b** - Multi-language support (4.0GB)

## Agent Capabilities Deep Dive

### 1. File Operations
```python
# Edit existing files
agent.file_editor.replace_in_file('src/main.py', 'old_code', 'new_code')
agent.file_editor.insert_at_line('src/main.py', 42, 'new_code')
agent.file_editor.append_to_file('README.md', '\n## New Section\n')

# Create new files (via code generation)
# Agent automatically parses "# File: path/to/file.py" markers
```

### 2. Terminal Execution
```python
# Run commands securely
result = agent.terminal.run_command('pytest tests/', timeout=60)
print(f"Exit code: {result['returncode']}")
print(f"Output: {result['stdout']}")

# Background processes
pid = agent.terminal.run_background('npm run dev', log_file='dev.log')
```

**Security**: Whitelist (pytest, npm, git, docker, etc.) + Blacklist (rm -rf, sudo, etc.)

### 3. Test Execution
```python
# Auto-detect framework (pytest, jest, npm test)
results = agent.test_runner.run_tests()
print(f"Passed: {results['passed']}/{results['tests_run']}")

# Parse failures for self-correction
for failure in results['failures']:
    context = agent.test_runner.get_failure_context(failure)
    # Use context to fix code
```

### 4. Codebase Search
```python
# Find function definitions
results = agent.codebase_search.find_function('process_data', 'python')

# Search with context
results = agent.codebase_search.grep_search('API_KEY', context_lines=3)

# Track dependencies
results = agent.codebase_search.find_imports('fastapi', 'python')
```

### 5. Error Checking
```python
# Fast syntax check (no dependencies)
result = agent.error_checker.check_syntax('src/main.py')
if not result['valid']:
    print(f"Syntax errors: {result['errors']}")

# Run linter (pylint/flake8/eslint)
result = agent.error_checker.run_linter('src/main.py')

# Type checking (mypy)
result = agent.error_checker.check_types('src/main.py')

# All checks at once
result = agent.error_checker.check_all('src/main.py')
```

### 6. Workspace Awareness
```python
# Explore project structure
structure = agent.workspace.get_project_structure(max_depth=3)

# Find files by pattern
files = agent.workspace.find_files('*.py', max_depth=5)

# Safe file reading
content = agent.workspace.read_file('src/config.py', max_size=100_000)
```

### 7. Context Management
```python
# Automatic sliding window (6000 token limit)
agent.context.add_task_result(
    task_description="Implement user authentication",
    code_generated=code[:1000],
    success=True
)

# Get relevant context for new task
context = agent.context.get_relevant_context("add password reset", max_tokens=1500)

# View metrics
metrics = agent.context.get_metrics()
print(f"Tasks: {metrics['task_count']}, Tokens: {metrics['total_tokens']}")
```

### 8. GitHub Integration
```python
# Create issues
from agents.bot_operations import BotOperations
bot = BotOperations()
bot.create_issue('agent-forge', 'Feature request', 'Description...', labels=['enhancement'])

# Close with comment
bot.add_comment('agent-forge', 5, 'Implementation complete!')
bot.update_issue('agent-forge', 5, state='closed')
```

### 9. Web Documentation Fetching (Issue #11)
```python
from agents.web_fetcher import WebFetcher

# Initialize with caching
fetcher = WebFetcher(cache_dir='~/.agent-forge/docs-cache', max_size=2000000)

# Fetch Python documentation
docs = fetcher.fetch_docs('https://docs.python.org/3/library/asyncio.html')

# Quick Python docs helper
docs = fetcher.search_python_docs('os.path')  # Fetches os.path module docs

# Get GitHub README
readme = fetcher.get_github_readme('python', 'cpython')

# Automatic features:
# - Domain whitelisting (Python docs, GitHub, Stack Overflow, etc.)
# - Rate limiting (1s between requests by default)
# - Content size limits (prevents huge downloads)
# - HTML text extraction (clean, readable text)
# - 24-hour caching (faster repeat access)
```

**Trusted Domains**: docs.python.org, github.com, stackoverflow.com, readthedocs.org, pytorch.org, tensorflow.org, fastapi.tiangolo.com, and [20+ more](agents/web_fetcher.py#L54)

### 10. Autonomous Polling (Issue #17)
```python
from agents.polling_service import PollingService, PollingConfig

# Configure polling
config = PollingConfig(
    interval_seconds=300,  # 5 minutes
    repositories=["owner/repo1", "owner/repo2"],
    watch_labels=["agent-ready", "auto-assign"],
    max_concurrent_issues=3
)

# Start polling service
service = PollingService(config)
await service.run()  # Runs continuously

# Or poll once
await service.poll_once()
```

**CLI Usage**:
```bash
# Start autonomous polling (continuous)
python3 agents/polling_service.py --repos owner/repo1 owner/repo2 --interval 300

# Poll once and exit
python3 agents/polling_service.py --repos owner/repo --once

# Custom labels and concurrency
python3 agents/polling_service.py --repos owner/repo --labels agent-ready bug --max-concurrent 5
```

**Features**:
- 🔄 **Automatic Issue Detection**: Periodically checks for assigned issues with specific labels
- 🔒 **Issue Locking**: Prevents duplicate work by multiple agents (comment-based claiming)
- 💾 **State Persistence**: Tracks processing/completed issues across restarts (polling_state.json)
- ⚡ **Concurrent Processing**: Configurable max concurrent issues per agent
- 🧹 **Auto Cleanup**: Removes old completed issues from state (7 day retention)
- 🤝 **Multi-Agent Coordination**: Claim timeout prevents permanent locks (default: 1 hour)
- 📊 **Structured Logging**: All polling events logged for debugging

**Configuration** (`polling_config.yaml`):
```yaml
interval_seconds: 300          # Poll every 5 minutes
repositories:
  - "owner/repo1"
  - "owner/repo2"
watch_labels:
  - "agent-ready"              # Manually triggered
  - "auto-assign"              # Automatically processed
max_concurrent_issues: 3       # Work on 3 issues simultaneously
claim_timeout_minutes: 60      # Claim expires after 1 hour
```

### 11. Automated Code Review (Issue #25)

AI-powered automated code review for pull requests with comprehensive quality checks.

```python
from agents.pr_reviewer import PRReviewer, ReviewCriteria

# Initialize reviewer
reviewer = PRReviewer(
    github_username="my-agent-bot",
    criteria=ReviewCriteria(
        check_code_quality=True,
        check_testing=True,
        check_documentation=True,
        check_security=True,
        require_changelog=True,
        strictness_level="normal"  # relaxed, normal, strict
    )
)

# Review a PR
should_approve, summary, comments = await reviewer.review_pr(
    repo="owner/repo",
    pr_number=42,
    pr_data={
        'title': 'feat: Add awesome feature',
        'body': 'PR description',
        'user': {'login': 'contributor'}
    },
    files=[
        {
            'filename': 'agents/feature.py',
            'patch': '@@ ... @@\n+def new_function():\n+    pass'
        }
    ]
)

print(summary)  # Comprehensive review with scores and feedback
# Post to GitHub: submit_review(repo, pr_number, summary, 'APPROVE' if should_approve else 'REQUEST_CHANGES', comments)
```

**CLI Usage**:
```bash
# Review a PR (mock data for testing)
python -m agents.pr_reviewer owner/repo 42 --username my-bot

# With custom criteria
python -m agents.pr_reviewer owner/repo 42 --config config/review_criteria.yaml
```

**Review Categories**:
- 🎨 **Code Quality**: Readability, maintainability, best practices, line length, print statements
- 🔒 **Security**: Hardcoded credentials, SQL injection, eval() usage, shell=True
- 🧪 **Testing**: Test coverage, test-to-code ratio, tests for new features
- 📝 **Documentation**: README updates, CHANGELOG entries, docstrings, PR description
- ✅ **Standards**: Conventional commits, proper error handling, logging practices

**Checks Performed**:
```python
# Code Quality
✓ No hardcoded credentials
✓ Using logging instead of print()
✓ Line length < 120 characters
✓ No bare except clauses
✓ No TODO/FIXME without issues

# Security
✓ No SQL injection risks
✓ No eval() usage
✓ shell=True only with sanitized input
✓ Input validation present

# Testing
✓ Tests included for new features
✓ Test-to-code ratio >= 0.5
✓ Edge cases covered

# Documentation
✓ README updated for significant changes
✓ CHANGELOG entry present
✓ PR description descriptive (>50 chars)
✓ Docstrings for complex logic
```

**Configuration** (`config/review_criteria.yaml`):
```yaml
review:
  check_code_quality: true
  check_testing: true
  check_documentation: true
  check_security: true
  require_changelog: true
  min_test_coverage: 80
  strictness_level: "normal"  # relaxed, normal, strict

code_quality:
  max_line_length: 120
  warn_print_statements: true
  warn_todo_comments: true
  check_hardcoded_secrets: true

security:
  check_sql_injection: true
  check_eval_usage: true
  warn_shell_true: true

testing:
  require_tests_for_features: true
  min_test_ratio: 0.5

documentation:
  require_readme_updates: true
  require_changelog: true

behavior:
  skip_tag: "[skip-review]"
  re_review_on_update: true
  cache_duration: 24  # hours
```

**Review Output Example**:
```markdown
## 🤖 Automated Code Review

**PR**: feat: Add awesome feature
**Author**: @contributor
**Files Changed**: 3

---

### 📊 Quality Scores

**Code Quality**: ████████░░ 80%
**Documentation**: ██████████ 100%
**Testing**: ███████░░░ 70%
**Overall**: ████████░░ 83%

### 💪 Strengths

✅ High code quality with minimal issues
✅ Well-documented changes
✅ CHANGELOG.md updated

### 🔴 Critical Issues

- `agents/feature.py:42`: ⚠️ Possible hardcoded credential detected

### ⚠️ Warnings

- `agents/utils.py:15`: 💡 Consider using logging instead of print()

### ✅ Review Checklist

- [x] Code quality acceptable
- [x] Tests included
- [x] Documentation updated
- [x] CHANGELOG entry present
- [ ] No critical issues

### 🎯 Review Decision

🔄 **CHANGES REQUESTED**

Please address the issues mentioned above before merging.

---
*Automated review by my-agent-bot • Agent Forge PR Reviewer v1.0*
```

**Features**:
- 🤖 **AI-Powered**: Optional LLM analysis for intelligent feedback
- 📊 **Quality Scoring**: Comprehensive scoring across multiple dimensions
- 💬 **Line-Specific Comments**: Comments attached to exact lines
- ✅ **Approval Logic**: Configurable approval thresholds (relaxed/normal/strict)
- 🎯 **Smart Filtering**: Skip own PRs, respect [skip-review] tag
- 📈 **Metrics**: Track code quality, testing, documentation scores
- ⚙️ **Configurable**: Customize checks, thresholds, and behavior
- 🔄 **Re-Review**: Automatically re-review after updates

**Strictness Levels**:
- **Relaxed**: Allow up to 1 error, score ≥ 0.5
- **Normal**: No errors, score ≥ 0.6 (default)
- **Strict**: No errors/warnings, score ≥ 0.8

**Integration with Polling** (future):
```python
# In polling_service.py
async def check_pull_requests(self, repo: str):
    prs = await self.github.list_pull_requests(repo, state='open')
    
    for pr in prs:
        # Skip if already reviewed
        reviews = await self.github.get_pr_reviews(repo, pr['number'])
        if any(r['user']['login'] == self.username for r in reviews):
            continue
        
        # Trigger review
        await self.pr_reviewer.review_pr(repo, pr['number'])
```

**Benefits**:
- **Consistency**: Uniform code quality across all PRs
- **Efficiency**: Instant feedback for contributors
- **Quality**: Catch issues before merge
- **Learning**: Educational feedback explains best practices
- **Automation**: Reduces manual review workload
claim_timeout_minutes: 60      # Claim expires after 1 hour
```

**Workflow**:
1. Service polls GitHub API for assigned issues
2. Filters issues by labels (`agent-ready`, `auto-assign`)
3. Checks if already processing or completed
4. Verifies no other agent claimed issue (comment check)
5. Claims issue (adds 🤖 comment with timestamp)
6. Launches IssueHandler workflow automatically
7. Updates state on completion
8. Repeat after interval

This enables fully autonomous agents that continuously monitor and work on issues without manual intervention!

### 12. Bot Account Agent (Issue #35)

Dedicated bot account for automated GitHub operations without email spam.

```python
from agents.bot_agent import BotAgent
from pathlib import Path

# Initialize bot
bot = BotAgent(
    agent_id="m0nk111-bot",
    username="m0nk111-bot",
    github_token=os.getenv("BOT_GITHUB_TOKEN"),
    config_file=Path("config/bot_config.yaml")
)

# Create issue
issue = await bot.create_issue(
    repo="owner/repo",
    title="New feature request",
    body="Please implement feature X",
    labels=["enhancement", "high-priority"],
    assignees=["developer1"]
)
print(f"Created issue #{issue['number']}")

# Add progress comment
await bot.add_comment(
    repo="owner/repo",
    issue_number=issue['number'],
    body="🤖 Implementation started. ETA: 2 hours"
)

# Update labels as work progresses
await bot.update_labels(
    repo="owner/repo",
    issue_number=issue['number'],
    add_labels=["in-progress"],
    remove_labels=["pending"]
)

# Close when done
await bot.close_issue(
    repo="owner/repo",
    issue_number=issue['number'],
    state_reason="completed",
    comment="✅ All tasks completed. Ready for review."
)
```

**CLI Usage**:
```bash
# Create issue
python -m agents.bot_agent create --repo owner/repo \
  --title "New feature" --body "Description" \
  --labels "enhancement,high-priority" --assignees "dev1,dev2"

# Add comment
python -m agents.bot_agent comment --repo owner/repo \
  --issue 42 --body "✅ Task completed"

# Assign issue
python -m agents.bot_agent assign --repo owner/repo \
  --issue 42 --assignees "developer1,reviewer1"

# Update labels
python -m agents.bot_agent labels --repo owner/repo \
  --issue 42 --labels "in-progress,reviewed"

# Close issue
python -m agents.bot_agent close --repo owner/repo \
  --issue 42 --body "✅ Closing after completion"

# View bot status
python -m agents.bot_agent status --repo owner/repo
```

**Core Operations**:
- 📝 **Issue Management**: Create, close, reopen issues
- 💬 **Commenting**: Add status updates and notifications
- 👥 **Assignments**: Assign issues to team members
- 🏷️ **Labels**: Add/remove labels for organization
- 📊 **Project Updates**: Update GitHub Projects v2 fields (planned)
- 🔄 **Workflow Triggers**: Trigger GitHub Actions (planned)

**Features**:
- 🚀 **Rate Limiting**: Automatic rate limit detection and pausing
- 🔁 **Retry Logic**: Automatic retry on failures (configurable attempts)
- 📈 **Metrics Tracking**: Operations count, success rate, response times
- 🎯 **Error Handling**: Comprehensive error handling with logging
- 📊 **Dashboard Integration**: Real-time status display
- 🔒 **Security**: Token-based authentication, operation approval
- ⏱️ **Response Times**: Track and optimize API performance
- 📝 **Operation History**: Keep last 100 operations for debugging

**Configuration** (`config/bot_config.yaml`):
```yaml
bot:
  agent_id: m0nk111-bot
  username: m0nk111-bot
  
  capabilities:
    - create_issues
    - add_comments
    - assign_tasks
    - update_labels
    - close_issues
  
  rate_limiting:
    max_operations_per_hour: 500
    pause_threshold: 4800
  
  behavior:
    retry_attempts: 3
    retry_delay: 5  # seconds
    command_timeout: 30
  
  monitoring:
    enabled: true
    report_interval: 60
```

**Metrics Dashboard**:
```
🤖 m0nk111-bot | BOT | ACTIVE
├─ Operations: 1,247
├─ Issues Created: 89
├─ Comments: 342
├─ Assignments: 156
├─ Success Rate: 98.5%
├─ Avg Response: 0.85s
├─ Rate Limit: 4,823/5,000
└─ Last Active: 2 minutes ago
```

**Integration with Coordinator**:
```python
# Coordinator creates execution plan
plan = await coordinator.create_plan(issue)

# Bot notifies assignees
for task in plan.sub_tasks:
    await bot.add_comment(
        repo=plan.repository,
        issue_number=plan.issue_number,
        body=f"""🎯 **Sub-Task Assigned**
        
**Task**: {task.title}
**Assignee**: @{task.assigned_to}
**Priority**: {task.priority}
**Estimated Effort**: {task.estimated_effort}m

{task.description}
"""
    )
    
    # Assign the task
    await bot.assign_issue(
        repo=plan.repository,
        issue_number=task.issue_number,
        assignees=[task.assigned_to]
    )
```

**Comment Templates**:
```python
# Task assignment template
task_assigned = """
🤖 **Task Assigned**

@{assignee} has been assigned to this issue.

**Priority**: {priority}
**Estimated Effort**: {effort}

Please update progress using the checklist above.
"""

# Blocker detected template
blocker_detected = """
🔴 **Blocker Detected**

**Issue**: {blocker_description}
**Impact**: Work on {task_id} is blocked

@{coordinator} Please review and provide guidance.
"""

# Task completed template
task_completed = """
✅ **Task Completed**

All checklist items have been completed.
Implementation ready for review.

**Time Taken**: {duration}
**Changes**: {files_changed} files
"""
```

**Security**:
- 🔐 **Token Security**: Store BOT_GITHUB_TOKEN securely in environment
- 🛡️ **Minimal Permissions**: Use only required GitHub token scopes
- ✅ **Operation Approval**: Critical operations require human approval
- 📝 **Audit Logging**: All operations logged for security review
- 🚫 **Blacklist**: Dangerous operations permanently blocked

**Environment Setup**:
```bash
# Set bot token
export BOT_GITHUB_TOKEN="ghp_your_token_here"
export BOT_GITHUB_USERNAME="m0nk111-bot"

# Add bot as collaborator on repositories
gh api repos/owner/repo/collaborators/m0nk111-bot -X PUT

# Configure repository permissions (write access minimum)
```

**Required GitHub Token Scopes**:
- `repo`: Full control of repositories
- `workflow`: Update GitHub Actions workflows
- `write:discussion`: Read and write discussions
- `project`: Full control of projects (for future project updates)

**Benefits**:
- **No Email Spam**: Bot account isolates automation notifications
- **Clean History**: Bot operations clearly identified
- **Audit Trail**: Complete operation history for debugging
- **Collaboration**: Multi-agent coordination without conflicts
- **Reliability**: Automatic retries and error handling
- **Performance**: Fast response times with metrics tracking
- **Scalability**: Handle hundreds of operations per hour

---

### 13. Coordinator Agent (Issue #36)

The **Coordinator Agent** is the "brain" of the multi-agent system. It analyzes GitHub issues, breaks them down into sub-tasks, assigns work to appropriate agents based on skills and availability, monitors progress, and dynamically adapts execution plans when blockers are encountered.

**Key Features**:
- 🧠 **LLM-Powered Planning**: Use Qwen2.5:72b or Claude for intelligent task breakdown
- 📊 **Complexity Analysis**: Automatic issue complexity assessment
- 🎯 **Smart Assignment**: Match tasks to agents based on skills, role, and current load
- 📈 **Progress Monitoring**: Real-time tracking of task completion and blockers
- 🔄 **Dynamic Adaptation**: Automatically adjust plans when blockers are detected
- 🤖 **Bot Integration**: All notifications routed through bot agent
- 💾 **Plan Persistence**: Save/load execution plans as JSON
- 🔗 **Dependency Resolution**: Topological sort ensures correct task ordering

**Python API**:
```python
from agents.coordinator_agent import CoordinatorAgent
from pathlib import Path

# Initialize coordinator with LLM and bot
coordinator = CoordinatorAgent(
    agent_id="coordinator",
    llm_agent=qwen_agent,  # LLM for planning
    bot_agent=bot,         # Bot for notifications
    config_file=Path("config/coordinator_config.yaml")
)

# Register available agents
coordinator.register_agent(
    agent_id="qwen-dev",
    role="developer",
    skills=["python", "javascript", "testing"],
    max_concurrent_tasks=3
)

coordinator.register_agent(
    agent_id="pr-reviewer",
    role="reviewer",
    skills=["code-review", "security", "best-practices"],
    max_concurrent_tasks=5
)

# Analyze issue and create execution plan
plan = await coordinator.analyze_issue(
    repo="m0nk111/agent-forge",
    issue_number=42
)

print(f"Created plan: {plan.plan_id}")
print(f"Sub-tasks: {len(plan.sub_tasks)}")
print(f"Required roles: {', '.join(plan.required_roles)}")
print(f"Estimated effort: {plan.total_estimated_effort}m")

# Assign tasks to agents
assignments = await coordinator.assign_tasks(plan)

for assignment in assignments:
    task = next(t for t in plan.sub_tasks if t.id == assignment.task_id)
    print(f"  {task.title} → {assignment.agent_id}")

# Monitor progress
status = await coordinator.monitor_progress(plan.plan_id)

print(f"Completion: {status['completion_percentage']:.1f}%")
print(f"Pending: {status['status_counts']['pending']}")
print(f"In Progress: {status['status_counts']['in_progress']}")
print(f"Completed: {status['status_counts']['completed']}")
print(f"Blocked: {status['status_counts']['blocked']}")

# Adapt plan if blockers encountered
if status['blockers']:
    updated_plan = await coordinator.adapt_plan(
        plan_id=plan.plan_id,
        blockers=status['blockers']
    )
    print(f"Plan adapted: {len(updated_plan.sub_tasks)} tasks (was {len(plan.sub_tasks)})")
```

**CLI Usage**:
```bash
# Analyze issue and create plan
python -m agents.coordinator_agent analyze \
  --repo m0nk111/agent-forge \
  --issue 42

# Assign tasks
python -m agents.coordinator_agent assign \
  --plan-id plan-42-20240104-120000

# Monitor progress
python -m agents.coordinator_agent monitor \
  --plan-id plan-42-20240104-120000

# View plan status
python -m agents.coordinator_agent status \
  --plan-id plan-42-20240104-120000
```

**Planning Workflow**:
```
1. Fetch Issue Data
   ├─ Get issue from GitHub
   └─ Extract title, body, labels

2. Analyze Complexity (LLM)
   ├─ Assess complexity (low/medium/high)
   ├─ Estimate effort (hours)
   ├─ Identify risks
   └─ Determine scope (bugfix/feature/refactor)

3. Create Sub-Tasks (LLM)
   ├─ Break down into actionable tasks
   ├─ Set dependencies between tasks
   ├─ Estimate effort per task
   ├─ Assign priorities (1-5)
   └─ Identify required skills

4. Build Dependency Graph
   ├─ Extract task relationships
   ├─ Create directed graph
   └─ Validate no cycles

5. Identify Required Roles
   ├─ Map tasks to agent roles
   └─ Determine coordinator/developer/reviewer/tester needs

6. Create Execution Plan
   ├─ Generate unique plan ID
   ├─ Calculate total estimated effort
   └─ Set status to PLANNING

7. Notify via Bot
   └─ Comment on issue with plan summary
```

**Configuration** (`config/coordinator_config.yaml`):
```yaml
coordinator:
  agent_id: coordinator
  role: coordinator
  
  llm:
    model: qwen2.5:72b        # Primary LLM for planning
    endpoint: http://localhost:11434
    temperature: 0.3          # Lower = more deterministic
    max_tokens: 4096
  
  fallback_llm:
    model: qwen2.5:7b         # Fallback if primary unavailable
  
  planning:
    max_sub_tasks: 20         # Maximum tasks per plan
    default_task_effort: 30   # Default minutes per task
    max_concurrent_tasks: 5   # Max parallel tasks per agent
  
  monitoring:
    check_interval: 300       # Check progress every 5 minutes
    blocker_threshold: 1800   # Flag blockers after 30 minutes
    auto_detect_blockers: true
    notify_progress: true
  
  agents:
    qwen-dev:
      role: developer
      skills: [python, javascript, testing]
      max_concurrent_tasks: 3
    
    bot-agent:
      role: bot
      skills: [github-operations, notifications]
      max_concurrent_tasks: 10
    
    pr-reviewer:
      role: reviewer
      skills: [code-review, security, best-practices]
      max_concurrent_tasks: 5
  
  assignment:
    strategy: skill_match     # Match based on skills
    skill_weights:
      exact_match: 10         # Exact skill match bonus
      related: 5              # Related skill bonus
      general: 2              # General capability bonus
    
    auto_assign:
      - pattern: "implement"
        role: developer
      - pattern: "test"
        role: tester
      - pattern: "review"
        role: reviewer
  
  dependencies:
    auto_detect: true
    patterns:
      - design → implement → test → document → deploy
  
  blockers:
    auto_resolve: true
    categories:
      missing_dependency:
        handler: create_installation_task
      permission:
        handler: escalate_to_human
      technical:
        handler: create_research_task
      waiting:
        handler: notify_and_wait
  
  notifications:
    templates:
      plan_created: "🎯 **Execution Plan Created**..."
      task_assigned: "📋 **Task Assigned**..."
      blocker_detected: "🔴 **Blocker Detected**..."
      plan_adapted: "🔄 **Plan Adapted**..."
      progress_update: "📊 **Progress Update**..."
```

**Agent Matching Algorithm**:
```python
def calculate_agent_score(task, agent):
    score = 0
    
    # Role match (10 points for exact match)
    if matches_role(task, agent.role):
        score += 10
    
    # Load factor (prefer less loaded agents)
    load_factor = agent.current_task_count / agent.max_concurrent_tasks
    score += (1 - load_factor) * 5
    
    return score
```

**Dependency Resolution**:
```
Topological Sort Algorithm:

1. Calculate in-degree for each task
   (number of dependencies)

2. Add tasks with in-degree 0 to queue
   (no dependencies)

3. Process queue:
   - Remove task from queue
   - Add to sorted list
   - For each dependent task:
     - Decrease its in-degree
     - If in-degree becomes 0, add to queue

4. Sort tasks at same level by priority

Result: Tasks ordered by dependencies,
        parallel tasks grouped by priority
```

**Progress Monitoring**:
```python
# Monitor checks every 5 minutes (configurable)
status = {
    'plan_id': 'plan-42-20240104-120000',
    'status': 'EXECUTING',
    'completion_percentage': 66.7,
    'status_counts': {
        'pending': 0,
        'in_progress': 1,
        'completed': 2,
        'blocked': 0,
        'failed': 0
    },
    'completed_tasks': [
        'task-42-1: Design architecture',
        'task-42-2: Implement core logic'
    ],
    'blockers': []  # Empty if no blockers
}
```

**Plan Adaptation**:
```python
# When blocker detected
blocker = {
    'task_id': 'task-42-3',
    'issue': 'Missing dependency: requests library',
    'solution': 'Install requests library'
}

# Coordinator creates new task
new_task = SubTask(
    id='task-42-3-fix-1',
    title='Install requests library',
    description='Add requests to requirements.txt and install',
    priority=5,  # High priority
    estimated_effort=15,
    depends_on=[]
)

# Insert before blocked task
plan.sub_tasks.insert(2, new_task)

# Update dependencies
plan.dependencies_graph['task-42-3'] = ['task-42-3-fix-1']
plan.dependencies_graph['task-42-3-fix-1'] = []

# Notify via bot
await bot.add_comment(
    repo=plan.repository,
    issue_number=plan.issue_number,
    body=f"🔄 Plan adapted to resolve blocker on {blocker['task_id']}"
)
```

**Integration Example**:
```python
# Complete workflow from issue to execution

# 1. Coordinator analyzes issue
plan = await coordinator.analyze_issue("m0nk111/agent-forge", 42)

# 2. Assigns tasks to agents
assignments = await coordinator.assign_tasks(plan)

# 3. Developer agent works on assigned tasks
for assignment in assignments:
    if assignment.agent_id == "qwen-dev":
        task = coordinator.get_plan(plan.plan_id).sub_tasks[assignment.task_id]
        
        # Agent implements the task
        result = await qwen_agent.execute_task(task.description)
        
        # Update task status
        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.now()

# 4. Coordinator monitors progress
status = await coordinator.monitor_progress(plan.plan_id)

# 5. Bot notifies team of progress
await bot.add_comment(
    repo=plan.repository,
    issue_number=plan.issue_number,
    body=f"📊 Progress: {status['completion_percentage']:.1f}% complete"
)

# 6. If blockers detected, adapt plan
if status['blockers']:
    updated_plan = await coordinator.adapt_plan(plan.plan_id, status['blockers'])
    
    # Reassign new fix tasks
    new_assignments = await coordinator.assign_tasks(updated_plan)
```

**Benefits**:
- **Intelligence**: LLM-powered planning breaks down complex issues automatically
- **Flexibility**: Comprehensive configuration for different workflows
- **Scalability**: Handle large issues with 20+ sub-tasks
- **Adaptability**: Dynamic plan changes based on real-world blockers
- **Visibility**: Complete progress tracking with status updates
- **Collaboration**: Multi-agent coordination with skill-based assignment
- **Reliability**: Fallback to rule-based logic if LLM unavailable
- **Persistence**: Plans saved to JSON for recovery after crashes

**Multi-Agent System Architecture**:
```
┌─────────────────────────────────────────┐
│         Coordinator Agent               │
│  (Plans, Assigns, Monitors, Adapts)     │
└────────────┬────────────────────────────┘
             │
    ┌────────┴────────┐
    ├─ Developer Agents (Qwen, Claude)
    ├─ Bot Agent (GitHub operations)
    ├─ PR Reviewer (Code quality)
    ├─ Tester Agent (Run tests)
    └─ Documenter (Write docs)

Flow:
1. Coordinator analyzes issue → creates plan
2. Coordinator assigns tasks → agents work
3. Agents report progress → coordinator monitors
4. Blocker detected → coordinator adapts plan
5. All tasks complete → coordinator closes issue
```

---

## Architecture

### Agent Lifecycle

1. **Initialization**: Load model, check availability
2. **Planning**: Define phases and tasks
3. **Execution**: Query LLM for each task
4. **Parsing**: Extract file paths and code from output
5. **Creation**: Write files to project structure
6. **Reporting**: Track success/failure metrics

### Communication Protocol

Agents use a structured prompt format:

```
System Prompt: Project context, tech stack, requirements
User Prompt: Specific task with output format instructions
Response: Structured code with file markers
```

## Use Cases

- 🎯 **Issue Implementation**: Autonomous implementation of GitHub issues
- 🔧 **Feature Development**: Multi-phase feature additions
- 📝 **Documentation**: Auto-generate docs from code
- 🧪 **Test Generation**: Create unit/integration tests
- 🔄 **Refactoring**: Large-scale code improvements
- 🐛 **Bug Fixing**: Automated debugging workflows

## Workspace Tools (Issue #8)

Agents include powerful workspace exploration and file reading capabilities:

### Precise Line-Range Reading

Read specific sections of files instead of entire contents - saves tokens and improves efficiency:

```python
from agents.workspace_tools import WorkspaceTools

tools = WorkspaceTools("/path/to/project")

# Read lines 50-75 from a file
code_section = tools.read_file_lines("src/main.py", 50, 75)

# Read just the imports (lines 1-10)
imports = tools.read_file_lines("src/utils.py", 1, 10)
```

### Function Extraction

Extract specific function definitions using AST parsing:

```python
# Read specific function with all decorators
function_code = tools.read_function("agents/qwen_agent.py", "execute_phase")

# Read class method
method_code = tools.read_function("lib/ollama_client.py", "generate")

# Works with async functions too
async_code = tools.read_function("api/routes.py", "handle_request")
```

**Benefits:**
- 🎯 Target specific code sections
- 💰 Efficient token usage (only read what you need)
- 🔍 Automatic function boundary detection
- 📚 Includes decorators and docstrings
- ⚡ Fast for large files

## Configuration

Agents can be configured via:

1. **Command-line arguments**: `--model`, `--phase`, `--task`
2. **Environment variables**: `OLLAMA_URL`, `PROJECT_ROOT`
3. **Config files**: `agents/config.yaml` (optional)

## Performance Tips

- Use smaller models (7B) for faster iteration
- Enable streaming for long-running tasks
- Use dry-run mode to validate before execution
- Break large tasks into smaller phases
- Fine-tune system prompts for better output

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## License

MIT License - see LICENSE file for details

## Credits

Created for the Caramba AI platform project.
Powered by [Ollama](https://ollama.com).

---

## Systemd Service (Production Deployment)

Agent-Forge can run as a systemd service for continuous autonomous operation in production environments.

### Features

- ✅ **Automatic startup** on system boot
- ✅ **Automatic restart** on failure (up to 5 times)
- ✅ **Resource limits** (80% CPU, 4GB RAM)
- ✅ **Systemd watchdog** integration (60-second keepalive)
- ✅ **Graceful shutdown** (30-second timeout)
- ✅ **Security hardening** (PrivateTmp, ProtectSystem, NoNewPrivileges)
- ✅ **Structured logging** via systemd journal

### Installation

```bash
# Install as system service (creates user, installs to /opt/agent-forge)
sudo ./scripts/install-service.sh

# Configure GitHub token (required!)
sudo nano /etc/default/agent-forge
# Add: BOT_GITHUB_TOKEN=your_token_here

# Configure repositories
sudo nano /opt/agent-forge/polling_config.yaml

# Start service
sudo systemctl start agent-forge

# Enable auto-start on boot
sudo systemctl enable agent-forge
```

### Service Management

```bash
# Check status
sudo systemctl status agent-forge

# View logs (follow)
sudo journalctl -u agent-forge -f

# View today's logs
sudo journalctl -u agent-forge --since today

# Restart service
sudo systemctl restart agent-forge

# Stop service
sudo systemctl stop agent-forge

# Disable auto-start
sudo systemctl disable agent-forge
```

### Health Monitoring

```bash
# Check if service is running
systemctl is-active agent-forge

# Check if service is enabled
systemctl is-enabled agent-forge

# View service health status
systemctl show agent-forge --property=ActiveState,SubState,Result
```

### Configuration

Edit `/etc/default/agent-forge` for environment variables:

```bash
# GitHub credentials (required)
BOT_GITHUB_TOKEN=ghp_your_token_here

# Service configuration
LOG_LEVEL=INFO
POLLING_INTERVAL=300        # 5 minutes
WEB_UI_PORT=8080
MONITORING_PORT=8765

# Resource limits  
MAX_CONCURRENT_ISSUES=3
```

Edit `/opt/agent-forge/polling_config.yaml` for polling settings:

```yaml
interval_seconds: 300
github:
  username: "your-bot-name"
repositories:
  - "owner/repo1"
  - "owner/repo2"
watch_labels:
  - "agent-ready"
  - "auto-assign"
max_concurrent_issues: 3
```

### Troubleshooting

#### Service won't start

```bash
# Check service status
sudo systemctl status agent-forge

# View full logs
sudo journalctl -u agent-forge -n 100 --no-pager

# Check systemd unit file
sudo systemctl cat agent-forge

# Validate configuration
/opt/agent-forge/venv/bin/python3 -m agents.service_manager --help
```

#### Permission errors

```bash
# Check ownership
ls -la /opt/agent-forge/

# Fix permissions
sudo chown -R agent-forge:agent-forge /opt/agent-forge/
sudo chmod 775 /opt/agent-forge/{logs,data,config}
```

#### Service crashes/restarts frequently

```bash
# Check resource usage
systemctl show agent-forge --property=CPUUsageNSec,MemoryCurrent

# View crash logs
sudo journalctl -u agent-forge --priority=err --since today

# Increase resource limits
sudo systemctl edit agent-forge
# Add:
# [Service]
# MemoryLimit=8G
# CPUQuota=150%
```

#### Watchdog timeout

If service shows watchdog timeout, increase the interval:

```bash
sudo systemctl edit agent-forge
# Add:
# [Service]
# WatchdogSec=120
```

### Uninstallation

```bash
# Stop and remove service
sudo ./scripts/uninstall-service.sh

# Optional: Backup data before removal
# Script will prompt for backup location
```

### Architecture

The service manager runs all Agent-Forge components in a single process:

- **Polling Service**: Monitors GitHub for assigned issues (5-minute intervals)
- **Monitoring Service**: WebSocket server for real-time progress tracking
- **Web UI**: Static file server for dashboards (port 8080)
- **Watchdog**: Keepalive signals to systemd every 30 seconds

All services shut down gracefully on SIGTERM (systemd stop) with cleanup.

---

## Roadmap

### ✅ Completed (v0.2.0)
- [x] File editing capabilities (replace, insert, append, delete)
- [x] Terminal command execution with security controls
- [x] Test execution and result parsing (pytest/jest)
- [x] Codebase search (grep, function/class finder)
- [x] Error checking (syntax, linting, type checking)
- [x] Documentation auto-loading (ARCHITECTURE.md, README.md, etc.)
- [x] Workspace awareness and file exploration
- [x] Context window management (6000 token sliding window)
- [x] GitHub issue/PR management via bot account

### 🚧 In Progress
- [ ] MCP integration (Context7, Pylance, GitHub MCP)
- [ ] Self-correction loops (test → fix → test)
- [ ] Enhanced web documentation fetching

### 📋 Planned (Low Priority)
- [ ] Precise line-range file reading
- [ ] Multi-file parallel editing
- [ ] Interactive debugging (pdb/DAP integration)
- [ ] Multi-agent orchestration (agents working together)
- [ ] Web UI for monitoring agent progress
- [ ] Agent memory/context persistence
- [ ] Model performance benchmarking
- [ ] Docker containerization
- [ ] CI/CD pipeline integration

---

**Status**: Active Development | **Version**: 0.2.0 | **Python**: 3.12+
