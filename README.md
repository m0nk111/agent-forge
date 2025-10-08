# Agent-Forge 🤖

> **Multi-agent orchestration platform for autonomous GitHub automation**

[![License](https://img.shields.io/badge/license-AGPL--3.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Agent-Forge is an intelligent multi-agent system that automates GitHub workflows using specialized AI agents powered by various LLMs (OpenAI, Anthropic, Google, local models). Features include **unified agent runtime** with role-based lifecycle management, autonomous issue detection, automated code reviews, real-time WebSocket monitoring, and comprehensive logging.

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
│   │   └── permissions.py      # Role-based permissions
│   ├── runners/                 # Agent implementations
│   │   ├── code_agent.py       # Developer agent (always-on)
│   │   ├── bot_agent.py        # Bot agent (on-demand)
│   │   ├── coordinator_agent.py # Coordinator agent (always-on)
│   │   ├── monitor_service.py  # Monitoring & health checks
│   │   └── polling_service.py  # GitHub polling service
│   ├── operations/              # Operations modules
│   │   ├── file_editor.py      # File editing
│   │   ├── git_operations.py   # Git operations
│   │   ├── github_api_helper.py # GitHub API wrapper
│   │   └── terminal_operations.py # Terminal execution
│   └── validation/              # Validation modules
│       ├── instruction_validator.py # Copilot instructions
│       └── instruction_parser.py    # Rule parsing
│
├── config/                      # Configuration files (YAML)
│   ├── agents/                  # Per-agent configs
│   │   ├── m0nk111-qwen-agent.yaml  # Developer agent config
│   │   └── m0nk111-bot.yaml         # Bot agent config
│   ├── services/                # Service configs
│   │   ├── coordinator.yaml     # Coordinator config
│   │   └── polling.yaml         # Polling config
│   ├── system/                  # System configs
│   │   ├── system.yaml          # Global system settings
│   │   ├── repositories.yaml    # Monitored repositories
│   │   └── trusted_agents.yaml  # Agent trust list
│   └── rules/                   # Validation rules
│       ├── instruction_rules.yaml   # Instruction validation
│       ├── review_criteria.yaml     # PR review criteria
│       └── security_audit.yaml      # Security rules
│
├── frontend/                    # Web dashboards
│   ├── dashboard.html          # Main monitoring dashboard ⭐
│   ├── config_ui.html          # Configuration UI
│   └── monitoring_dashboard.html # Legacy monitoring
│
├── docs/                        # Documentation
│   ├── ARCHITECTURE.md         # System architecture
│   ├── AGENT_ONBOARDING.md     # Agent quick start
│   ├── MONITORING_API.md       # API documentation
│   ├── PORT_REFERENCE.md       # Port allocation guide
│   └── diagrams/               # Architecture diagrams
│
├── secrets/                     # Secrets (gitignored)
│   └── agents/                 # Agent tokens
│       ├── m0nk111-qwen-agent.token
│       └── m0nk111-bot.token
│
├── scripts/                     # Utility scripts
│   ├── sync-to-production.sh   # Production deployment
│   ├── start-service.sh        # Service startup
│   └── install-service.sh      # Systemd installation
│
├── systemd/                     # Systemd service files
│   └── agent-forge.service     # Main service unit
│
├── tests/                       # Test suite
│   ├── test_agent_registry.py  # Registry tests
│   ├── test_instruction_validator.py # Validation tests
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
sudo journalctl -u agent-forge -f
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
