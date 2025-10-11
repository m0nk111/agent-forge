# Agent-Forge 🤖

> **Multi-agent orchestration platform for autonomous GitHub automation**
> **Now powered by GPT-5 for 50% faster coordination!** ⭐

[![License](https://img.shields.io/badge/license-AGPL--3.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![GPT-5](https://img.shields.io/badge/GPT--5-Enabled-brightgreen.svg)](docs/GPT5_QUICK_REFERENCE.md)

Agent-Forge is an intelligent multi-agent system that automates GitHub workflows using specialized AI agents powered by various LLMs (OpenAI GPT-5, GPT-4, Anthropic, Google, local models). Features include **unified agent runtime** with role-based lifecycle management, **GPT-5 powered coordination** (50% faster than GPT-4o), autonomous issue detection, automated code reviews, real-time WebSocket monitoring, and comprehensive logging.

## � Project Evolution

Watch the complete development journey of Agent-Forge visualized with flying files and organic repository growth:

> **📹 Video Location**: `media/agent-forge-gource-latest.mp4`  
> **Quality**: 1080p60 @ CRF 16, ~30 seconds, ~35 MB  
> **Schedule**: Automatically regenerated at 08:00 and 20:00 via cron  
> **Technology**: [Gource](https://gource.io/) visualization with Xvfb rendering  
> **Script**: `/home/flip/scripts/update-gource-videos.sh`

*Video maintained in `/media/` directory and tracked in Git for easy access.*

## �🎯 Latest: GPT-5 Coordinator (October 2025)

**Major Performance Upgrade!** The default coordinator now uses **GPT-5 Chat Latest**:

- ⚡ **50% faster** for complex planning (10.8s vs 21.7s)
- ✨ **Equal quality** (5/5 on all metrics)  
- 📝 **36% more detail** (94 lines vs 69)
- 🚀 **2x faster** token generation (51 tok/s vs 25 tok/s)
- 💰 **Only $3/month** more than GPT-4o

[→ Read GPT-5 Quick Reference](docs/GPT5_QUICK_REFERENCE.md) | [→ Model Comparison](docs/COORDINATOR_MODEL_COMPARISON.md)

---

## 📑 Table of Contents

- [Features](#-features)
- [AI-Generated Codebase](#-ai-generated-codebase)
- [Quick Start](#-quick-start)
- [Architecture](#-architecture)
- [Project Structure](#-project-structure)
- [Configuration](#-configuration)
- [Usage](#-usage)
- [Monitoring](#-monitoring)
- [Security](#-security)
- [Documentation](#-documentation)
- [Development](#-development)
- [License](#-license)

---

## ✨ Features

### Core Capabilities
- 🤖 **Unified Agent Runtime**: Role-based lifecycle management (always-on vs on-demand agents)
- 🎯 **Multi-Role Support**: Coordinator, Developer, Bot, Reviewer, Tester, Documenter, Researcher
- 📊 **Real-Time Monitoring**: WebSocket-powered dashboard with live agent status and logs
- 🔄 **Autonomous Operation**: Automatic issue detection and task distribution
- ✅ **Instruction Validation**: Automatic enforcement of Copilot instructions (#63)
- 🔍 **Code Review Automation**: AI-powered PR reviews with quality scoring

### Technical Features
- 🏗️ **Industry Patterns**: LangChain supervisor model, AutoGPT sub-agents, MS Semantic Kernel lazy loading
- 🎨 **Visual Documentation**: Complete Mermaid diagrams for architecture understanding (#67)
- 🔒 **Security**: SSH/PAM authentication, token management, role-based permissions
- 🌐 **LAN Access**: Dashboard accessible from any device on your network
- 📝 **Comprehensive Logging**: Structured logging with real-time updates
- 🧭 **Workspace Awareness**: Clear project identification prevents agent confusion
- 🌞 **Creative ASCII Illustrations**: Issues that ask for drawings (sun, chair, car, etc.) trigger the agent to craft playful Markdown art and open a PR

### Recent Features (October 2025)

**🎯 Coordinator-First Gateway**:
- ALL issues with `agent-ready` label MUST pass through coordinator analysis
- Intelligent routing: SIMPLE (no escalation) → UNCERTAIN (escalation enabled) → COMPLEX (multi-agent)
- Separation of concerns: Coordinator decides, Polling executes
- See: [Intelligent Issue Routing Guide](docs/guides/INTELLIGENT_ISSUE_ROUTING.md)

**🧠 Intelligent Issue Complexity Analysis**:
- **IssueComplexityAnalyzer**: 9 metrics, 0-65 point scoring system
- Pre-flight analysis: description length, task count, file mentions, code blocks, dependencies
- Keywords: refactoring, architecture, multi-component detection
- Objective thresholds: SIMPLE (≤10), UNCERTAIN (11-25), COMPLEX (>25)

**🚀 Mid-Execution Agent Escalation**:
- **AgentEscalator**: Escalate from code agent to coordinator mid-execution
- Triggers: >5 files, >3 components, 2+ failures, stuck >30min, architecture changes
- Preserves work progress (branch, commits) during escalation
- Automatic handoff with progress summary

**🔀 PR Conflict Intelligence**:
- **ConflictComplexityAnalyzer**: 7 metrics, 0-55 point scoring
- Actions: auto-resolve (simple), manual-fix (moderate), close-and-reopen (complex)
- Integrated into PR review workflow
- Automatic issue reopening with `agent-ready` label for complex conflicts

**🤖 Automated PR Lifecycle Management**:
- LLM-powered code reviews with static analysis fallback
- Smart draft PR recovery (auto re-review when ready)
- Self-review prevention (bots never review own PRs)
- Rate limiter with intelligent bypass for internal operations
- Race condition prevention with file-based locking

**📦 Repository Management**:
- Automated repository access management
- Configurable bot account selection
- Centralized GitHub account configuration
- GitHub Actions integration for PR review triggers

---

## 🤖 AI-Generated Codebase

This project represents a significant achievement in AI-assisted development. **The entire codebase across all repositories is AI-generated**, demonstrating the capabilities of modern language models in software engineering.

### Code Statistics (All Repositories)

- **Total Lines of Code**: 126,065
- **Total Repositories**: 7 (1 public, 6 private)
- **Total Files**: 786
- **Primary Languages**: Python (40K lines), Shell (7K lines), HTML (9K lines)
- **Documentation**: 43K lines of Markdown

#### Repository Breakdown

| Repository | Lines | Language | Type |
|------------|-------|----------|------|
| agent-forge | 34,773 | Python | Public |
| caramba | 32,948 | Python | Private |
| stepperheightcontrol | 31,188 | Python | Private |
| audiotransfer | 13,382 | Python | Private |
| ai-clickforme-assistant | 5,436 | HTML | Private |
| tars-ai-project | 4,473 | Shell | Private |
| nadscab | 3,901 | JavaScript | Private |

### The Meta-AI Concept

This represents a unique case of **"AI inception"** - an autonomous agent system that was itself built entirely using AI-generated code. The practical skills involved include:

- 🎯 **Architecture Design**: Defining what to build and how components should interact
- 📋 **Requirements Engineering**: Guiding AI in the right direction with clear specifications
- 🔍 **Code Review**: Understanding, validating, and refining AI-generated output
- 🔗 **System Integration**: Connecting all components into a cohesive whole
- 🐛 **Debugging**: Troubleshooting and fixing issues when they arise
- 🎨 **Orchestration**: Coordinating multiple AI agents and services

These **AI orchestration skills** may be more valuable than traditional coding in the AI era. The role shifts from writing every line of code to being an architect, conductor, and quality gatekeeper.

---

## 🚀 Quick Start

### Prerequisites

```bash
# Required
- Python 3.12+
- Ollama (for local LLMs)
- GitHub Personal Access Token

# Recommended
- systemd (for production deployment)
- 16GB+ RAM for local LLMs
```

### Installation

```bash
# Clone repository
git clone https://github.com/m0nk111/agent-forge.git
cd agent-forge

# Install dependencies
pip install -r requirements.txt

# Pull LLM model (example)
ollama pull qwen2.5-coder:7b

# Setup secrets
mkdir -p secrets/agents
echo "ghp_YOUR_GITHUB_TOKEN" > secrets/agents/m0nk111-qwen-agent.token
chmod 600 secrets/agents/*.token
```

### Quick Run

```bash
# Start all services
python3 -m engine.core.service_manager

# Or start specific services
python3 -m engine.core.service_manager --no-polling --no-web-ui

# Access dashboard
open http://localhost:8897/dashboard.html
```

---

## 🏗️ Architecture

### Unified Agent Runtime

Agent-Forge uses a **unified agent runtime** with role-based lifecycle management:

**Lifecycle Strategies:**
- **Always-on**: Coordinator, Developer (start immediately, run continuously)
- **On-demand**: Bot, Reviewer, Tester, Documenter, Researcher (lazy loading)

**Key Components:**
- `AgentRegistry`: Centralized lifecycle manager
- `ServiceManager`: Orchestrates all services and agents
- `MonitorService`: Real-time status tracking and health checks
- `PollingService`: Autonomous GitHub issue detection

### Agent Roles

| Role | Lifecycle | Purpose | Best LLMs |
|------|-----------|---------|-----------|
| **Coordinator** | Always-on | Task orchestration, planning | Claude 3 Opus, GPT-4 Turbo |
| **Developer** | Always-on | Code generation, bug fixes | Qwen2.5-Coder 32B, GPT-4 Turbo |
| **Bot** | On-demand | GitHub operations (comments, labels) | GPT-3.5 Turbo, Llama 3 8B |
| **Reviewer** | On-demand | PR reviews, code quality | Claude 3 Sonnet, GPT-4 |
| **Tester** | On-demand | Test execution, validation | Gemini Pro, Llama 3 8B |
| **Documenter** | On-demand | Documentation generation | GPT-4, Claude 3 |
| **Researcher** | On-demand | Information gathering | Gemini Pro, Mixtral |

**See also:** [ARCHITECTURE.md](ARCHITECTURE.md) for detailed system design

---

## 📁 Project Structure

```
agent-forge/
├── engine/                      # Core engine components
│   ├── core/                    # Core orchestration
│   │   ├── agent_registry.py   # Unified agent lifecycle manager ⭐
│   │   ├── service_manager.py  # Service orchestrator
│   │   ├── config_manager.py   # Configuration management
│   │   ├── llm_providers.py    # LLM provider abstraction
│   │   ├── pipeline_orchestrator.py # Multi-stage task pipelines
│   │   ├── context_manager.py  # Context management
│   │   ├── permissions.py      # Role-based permissions
│   │   ├── rate_limiter.py     # API rate limiting
│   │   ├── key_manager.py      # Token/key management
│   │   └── account_manager.py  # GitHub account management
│   ├── runners/                 # Agent implementations
│   │   ├── code_agent.py       # Developer agent (generic LLM)
│   │   ├── bot_agent.py        # Bot agent (on-demand)
│   │   ├── coordinator_agent.py # Coordinator agent (always-on)
│   │   ├── monitor_service.py  # Monitoring & health checks
│   │   └── polling_service.py  # GitHub polling service
│   ├── operations/              # Operations modules
│   │   ├── file_editor.py      # File editing operations
│   │   ├── llm_file_editor.py  # LLM-powered file editing
│   │   ├── git_operations.py   # Git operations
│   │   ├── github_api_helper.py # GitHub API wrapper
│   │   ├── terminal_operations.py # Terminal execution
│   │   ├── code_generator.py   # Code generation
│   │   ├── issue_handler.py    # Issue resolution
│   │   ├── issue_opener_agent.py # Issue creation agent
│   │   ├── issue_complexity_analyzer.py # Issue complexity analysis ⭐
│   │   ├── agent_escalator.py  # Mid-execution escalation ⭐
│   │   ├── coordinator_gateway.py # Coordinator-first gateway ⭐
│   │   ├── conflict_analyzer.py # PR conflict complexity ⭐
│   │   ├── pr_review_agent.py  # Automated PR reviews
│   │   ├── pr_reviewer.py      # PR review operations
│   │   ├── repo_manager.py     # Repository access management
│   │   ├── bot_operations.py   # Bot utility functions
│   │   ├── creative_status.py  # ASCII art generation
│   │   ├── codebase_search.py  # Code search utilities
│   │   ├── test_runner.py      # Test execution
│   │   ├── workspace_tools.py  # Workspace utilities
│   │   ├── websocket_handler.py # WebSocket communication
│   │   ├── mcp_client.py       # MCP protocol client
│   │   ├── web_fetcher.py      # Web content fetching
│   │   ├── shell_runner.py     # Shell command execution
│   │   ├── retry_util.py       # Retry logic utilities
│   │   ├── error_checker.py    # Error detection
│   │   ├── string_utils.py     # String manipulation
│   │   ├── structure_generator.py # Project structure generation
│   │   ├── team_manager.py     # Team management
│   │   ├── repository_creator.py # Repository creation
│   │   └── bootstrap_coordinator.py # Coordinator bootstrapping
│   └── validation/              # Validation modules
│       ├── instruction_validator.py # Copilot instructions validation
│       ├── instruction_parser.py    # Validation rule parsing
│       └── security_auditor.py      # Security audits
│
├── api/                         # REST API endpoints
│   ├── auth_routes.py          # Authentication endpoints
│   └── config_routes.py        # Configuration API
│
├── config/                      # Configuration files (YAML)
│   ├── agents/                  # Per-agent configs
│   ├── services/                # Service configs
│   │   ├── coordinator.yaml     # Coordinator settings
│   │   └── polling.yaml         # Polling configuration
│   ├── system/                  # System configs
│   ├── rules/                   # Validation rules
│   ├── backups/                 # Config backups
│   ├── development/             # Development configs
│   └── keys.example.json        # Example secrets structure
│
├── frontend/                    # Web dashboards
│   ├── dashboard.html          # Main monitoring dashboard ⭐
│   ├── index.html              # Landing page
│   ├── login.html              # Authentication page
│   ├── config_ui.html          # Configuration UI
│   └── monitoring_dashboard.html # Legacy monitoring
│
├── docs/                        # Documentation
│   ├── README.md               # Documentation index
│   ├── guides/                 # User guides
│   │   ├── AGENT_ROLES.md      # Agent role documentation
│   │   ├── AGENT_ONBOARDING.md # Quick start for agents
│   │   ├── MONITORING_API.md   # API documentation
│   │   ├── GPT5_QUICK_REFERENCE.md # GPT-5 usage guide
│   │   ├── INSTRUCTION_VALIDATION_GUIDE.md # Validation guide
│   │   ├── ASCII_AUTOMATION_WORKFLOW.md # ASCII art workflow
│   │   ├── PIPELINE_ARCHITECTURE.md # Pipeline documentation
│   │   ├── ANTI_SPAM_PROTECTION.md # Spam prevention
│   │   ├── INTELLIGENT_ISSUE_ROUTING.md # Issue routing guide ⭐
│   │   └── SEPARATION_OF_CONCERNS.md # Architecture pattern ⭐
│   ├── diagrams/               # Architecture diagrams (Mermaid)
│   ├── internal/               # Internal documentation
│   └── archive/                # Archived documentation
│
├── data/                        # Runtime data
│   └── polling_state.json      # Polling service state
│
├── secrets/                     # Secrets (gitignored)
│   ├── README.md               # Secrets documentation
│   ├── agents/                 # Agent tokens (600 permissions)
│   │   ├── m0nk111.token       # Admin token
│   │   ├── m0nk111-post.token  # Bot orchestrator
│   │   ├── m0nk111-qwen-agent.token # Code agent token
│   │   ├── m0nk111-coder1.token # GPT-5 coder token
│   │   ├── m0nk111-coder2.token # GPT-4o coder token
│   │   └── m0nk111-reviewer.token # Reviewer token
│   └── keys/                   # API keys (600 permissions)
│       └── openai.key          # OpenAI API key
│
├── scripts/                     # Utility scripts
│   ├── launch_agent.py         # Agent launcher
│   ├── manage_repos.py         # Repository management CLI
│   ├── migrate_secrets.py      # Secrets migration tool
│   ├── monitor-cli.py          # CLI monitoring tool
│   ├── test_*.py               # Test scripts
│   ├── demo_*.py               # Demo scripts
│   ├── sync-to-production.sh   # Production deployment
│   ├── quick-deploy.sh         # Quick deployment
│   ├── start-service.sh        # Service startup
│   ├── install-service.sh      # Systemd installation
│   ├── install-polling-service.sh # Polling service install
│   ├── launch_dashboard.sh     # Dashboard launcher
│   ├── launch_monitoring.sh    # Monitoring launcher
│   ├── launch_config_ui.sh     # Config UI launcher
│   ├── secure-tokens.sh        # Token security script
│   └── test_github_integration.sh # GitHub integration test
│
├── systemd/                     # Systemd service files
│   ├── agent-forge.service     # Main service unit
│   ├── agent-forge-polling.service # Polling service unit
│   ├── agent-forge-auth.service # Auth service unit
│   └── tokens.env.example      # Example environment file
│
├── tests/                       # Test suite
│   ├── test_*.py               # Unit/integration tests
│   └── manual/                 # Manual test scripts
│
├── CHANGELOG.md                # Version history
├── ARCHITECTURE.md             # Architecture documentation
├── LICENSE                     # AGPL-3.0 license
├── requirements.txt            # Python dependencies
└── README.md                   # This file

⭐ = Recently added/updated
```

---

## ⚙️ Configuration

### System Configuration

**File:** `config/system/system.yaml`

```yaml
service_manager:
  enable_polling: true
  enable_monitoring: true
  enable_web_ui: true
  enable_agent_runtime: true  # Unified agent runtime
  
  polling_interval: 300  # 5 minutes
  monitoring_port: 7997
  web_ui_port: 8897
  
  polling_repos:
    - "m0nk111/agent-forge"
```

### Agent Configuration

**File:** `config/agents/{agent-id}.yaml`

```yaml
agent_id: m0nk111-qwen-agent
name: M0nk111 Qwen Agent
role: developer  # developer, bot, coordinator, reviewer, tester, documenter, researcher
enabled: true

# LLM Configuration
model_provider: local  # local, openai, anthropic, google
model_name: qwen2.5-coder:7b
api_base_url: http://localhost:11434

# GitHub Configuration
github_token: null  # Loaded from secrets/agents/{agent-id}.token

# Permissions
local_shell_enabled: true
shell_permissions: read_write
file_permissions: read_write
git_permissions: full
github_permissions: full
```

---

## 🎮 Usage

### Service Manager

```bash
# Start all services
python3 -m engine.core.service_manager

# Selective services
python3 -m engine.core.service_manager \
  --no-polling \
  --no-web-ui \
  --no-agent-runtime

# Custom ports
python3 -m engine.core.service_manager \
  --web-port 8080 \
  --monitor-port 8765
```

### Production Deployment

```bash
# Install systemd service
sudo bash scripts/install-service.sh

# Start service
sudo systemctl start agent-forge

# Enable auto-start
sudo systemctl enable agent-forge

# Check status
sudo systemctl status agent-forge

# View logs
sudo journalctl -u agent-forge -f --no-pager
```

### Sync to Production

```bash
# Development → Production sync
bash scripts/sync-to-production.sh

# Manual sync
rsync -av --exclude='.git' \
  /home/flip/agent-forge/ \
  /opt/agent-forge/

sudo chown -R agent-forge:agent-forge /opt/agent-forge
sudo systemctl restart agent-forge
```

---

## 📊 Monitoring

### Dashboard Access

- **Main Dashboard**: http://localhost:8897/dashboard.html
- **Config UI**: http://localhost:8897/config_ui.html
- **API Endpoint**: http://localhost:7997/api

### REST API

```bash
# Services status
curl http://localhost:7997/api/services | jq .

# Agents status
curl http://localhost:7997/api/agents | jq .

# Agent details
curl http://localhost:7997/api/agents/m0nk111-qwen-agent/status | jq .

# Agent logs
curl http://localhost:7997/api/agents/m0nk111-qwen-agent/logs | jq .

# Activity history
curl http://localhost:7997/api/activity | jq .
```

### WebSocket

```javascript
// Connect to monitoring WebSocket
const ws = new WebSocket('ws://localhost:7997/ws/monitor');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Agent update:', data);
};
```

**See also:** [docs/MONITORING_API.md](docs/MONITORING_API.md)

---

## 🔒 Security

### Token Management

```bash
# Create token file
echo "ghp_YOUR_GITHUB_TOKEN" > secrets/agents/my-agent.token
chmod 600 secrets/agents/my-agent.token

# Token is automatically loaded by ConfigManager
# Never commit tokens to git (blocked by .gitignore)
```

### Authentication

Agent-Forge uses **SSH/PAM authentication** for dashboard access:

- Login with system credentials (SSH username/password)
- 24-hour JWT session tokens
- HttpOnly cookies for security
- Authentication service on port 7996

### Permissions

Role-based permissions per agent:
- **Read-only**: Can read files and run read-only commands
- **Developer**: Full file/terminal access, no PR merge
- **Admin**: Full access including PR merge and config changes

**See also:** [docs/TOKEN_SECURITY.md](docs/TOKEN_SECURITY.md)

---

## 📚 Documentation

### Core Documentation
- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture and design
- [CHANGELOG.md](CHANGELOG.md) - Version history and changes
- [LICENSE](LICENSE) - AGPL-3.0 license terms

### Guides
- [docs/AGENT_ONBOARDING.md](docs/AGENT_ONBOARDING.md) - Quick start checklist
- [docs/MONITORING_API.md](docs/MONITORING_API.md) - API documentation
- [docs/PORT_REFERENCE.md](docs/PORT_REFERENCE.md) - Port allocation guide
- [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) - Deployment guide
- [docs/TESTING.md](docs/TESTING.md) - Testing guide

### Visual Documentation
- [docs/diagrams/architecture-overview.md](docs/diagrams/architecture-overview.md) - Architecture diagrams
- [docs/diagrams/data-flow.md](docs/diagrams/data-flow.md) - Data flow diagrams
- [docs/diagrams/component-interactions.md](docs/diagrams/component-interactions.md) - Component diagrams

---

## 🛠️ Development

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/m0nk111/agent-forge.git
cd agent-forge

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install pytest pytest-asyncio black pylint mypy
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_agent_registry.py

# Run with coverage
pytest --cov=engine --cov-report=html

# Run integration tests
pytest tests/test_integration_validator.py
```

### Code Style

```bash
# Format code
black engine/ tests/

# Lint code
pylint engine/

# Type checking
mypy engine/
```

### Contributing

1. Follow the [Copilot Instructions](.github/copilot-instructions.md)
2. Update [CHANGELOG.md](CHANGELOG.md) for all changes
3. Add tests for new features
4. Run linters before committing
5. Use conventional commit messages

---

## 📊 Recent Updates

### October 2025

**✅ Unified Agent Runtime** (Breaking Change):
- Implemented role-based lifecycle management (always-on vs on-demand)
- Following industry patterns: LangChain, AutoGPT, MS Semantic Kernel
- Resource-efficient lazy loading for event-driven agents
- CLI: `--no-agent-runtime` (replaces deprecated `--no-qwen`)

**✅ Instruction Validation System** (PR #63):
- Auto-fix commit messages and changelog entries
- 30+ tests with 78% code coverage
- Validation of file locations, ports, documentation language

**✅ Visual Documentation Suite** (PR #68):
- Complete Mermaid architecture diagrams (1389 lines)
- Agent onboarding checklist
- Port reference guide with troubleshooting

---

## 📄 License

This project is licensed under the **GNU Affero General Public License v3.0 (AGPL-3.0)**.

- ✅ Commercial use allowed with dual licensing
- ✅ Modification and distribution allowed
- ⚠️ Network use requires source disclosure (AGPL clause)
- ⚠️ Must preserve copyright notices

**For commercial licensing without AGPL restrictions:**
Contact: [Commercial License Inquiry](mailto:info@example.com)

See [LICENSE](LICENSE) and [COMMERCIAL-LICENSE.md](COMMERCIAL-LICENSE.md) for details.

---

## 🤝 Support

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/m0nk111/agent-forge/issues)
- **Discussions**: [GitHub Discussions](https://github.com/m0nk111/agent-forge/discussions)

---

**Built with ❤️ by the Agent-Forge team**
