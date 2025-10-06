# Agent-Forge 🤖

**Multi-agent orchestration platform for GitHub automation with role-based LLM assignment, real-time monitoring, and intelligent task distribution**

Agent-Forge is an intelligent multi-agent system that automates GitHub workflows using specialized AI agents powered by various LLMs (OpenAI, Anthropic, Google, local models). Each agent has a specific role (coder, reviewer, coordinator, polling) and can be assigned different LLMs based on the task requirements. Features include autonomous issue detection, automated code reviews, real-time WebSocket monitoring, and comprehensive logging.

## 🌟 Key Features

- 🤖 **Multi-Agent Orchestration**: Specialized agents for different roles (coding, reviewing, coordinating, polling)
- 🎯 **Role-Based LLM Assignment**: Assign different LLMs to agents based on their specialization
- 📊 **Real-Time Monitoring**: WebSocket-powered dashboard for live agent status and logs
- 🔄 **Autonomous Operation**: Automatic issue detection and task distribution
- 🧪 **Agent Modes**: Switch between idle, test, and production modes per agent
- 🔍 **Code Review Automation**: AI-powered PR reviews with quality scoring
- ✅ **Instruction Validation**: Automatic enforcement of Copilot instructions and project standards
- 📝 **Comprehensive Logging**: Structured logging with real-time updates
- 🌐 **LAN Access**: Dashboard accessible from any device on your network
- 🔒 **Bot Account Support**: Dedicated bot account for GitHub operations (no email spam)

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- Ollama installed and running (for local models)
- At least one LLM model pulled (e.g., `ollama pull qwen2.5-coder:7b`)
- GitHub personal access token (for GitHub integration)

### Installation

```bash
git clone https://github.com/m0nk111/agent-forge.git
cd agent-forge
pip install -r requirements.txt
```

### Basic Usage

```bash
# Start the service manager (all services in one)
python3 -m agents.service_manager --web-port 8897 --monitor-port 7997

# Or use individual components:

# Start monitoring dashboard
./scripts/launch_dashboard.sh

# Run autonomous polling agent
python3 agents/polling_service.py --repos owner/repo --interval 300

# Execute agent with config file
python3 agents/code_agent.py --config configs/caramba_personality_ai.yaml --phase 1
```

## 📊 Monitoring & Dashboard

Agent-Forge includes a real-time monitoring dashboard for tracking agent activity, logs, and progress.

### Starting the Dashboard

```bash
# Start dashboard server (accessible on LAN)
./scripts/launch_dashboard.sh

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
python3 agents/code_agent.py --config configs/my_project.yaml --phase 1 --enable-monitoring --agent-id "my-agent"

# Test monitoring integration
python3 tests/test_qwen_monitoring.py
```

See [docs/QWEN_MONITORING.md](docs/QWEN_MONITORING.md) for detailed documentation.

## 🏗️ Architecture

### Agent Roles

Agent-Forge supports multiple specialized agent roles:

1. **Coder Agent**: Implements features, fixes bugs, writes code
   - Best LLMs: GPT-4 Turbo, Qwen2.5-Coder 32B, DeepSeek-Coder 33B
   
2. **Code Review Agent**: Reviews PRs, provides feedback, ensures quality
   - Best LLMs: GPT-4 Turbo, Claude 3 Sonnet, Qwen2.5-Coder 32B
   
3. **Coordinator Agent**: Plans tasks, assigns work, manages project
   - Best LLMs: Claude 3 Opus, GPT-4 Turbo, Mixtral 8x22B
   
4. **Polling Agent**: Monitors GitHub, detects issues, triggers workflows
   - Best LLMs: GPT-3.5 Turbo, Gemini Pro (free), Llama 3 8B

### Service Architecture

```
agent-forge/
├── agents/              # Agent implementations
│   ├── service_manager.py      # Central service orchestrator
│   ├── code_agent.py           # Generic code agent (config-driven, any LLM)
│   ├── polling_service.py      # Autonomous GitHub polling
│   ├── pr_reviewer.py          # Automated code review
│   ├── bot_agent.py            # Bot account operations
│   ├── file_editor.py          # File editing operations
│   ├── terminal_operations.py  # Terminal command execution
│   ├── test_runner.py          # Test execution and parsing
│   ├── codebase_search.py      # Code search (grep/semantic)
│   ├── error_checker.py        # Syntax/lint/type checking
│   ├── workspace_tools.py      # Project structure exploration
│   └── context_manager.py      # Context window management
├── frontend/            # Real-time monitoring dashboard
│   └── dashboard.html          # WebSocket-powered UI
├── configs/             # Agent configurations
├── docs/                # Documentation
└── scripts/             # Deployment and utility scripts
```

## 📚 Documentation

- [Agent Architecture](docs/ARCHITECTURE.md) - System design and components
- [LLM Provider Setup](docs/LLM_PROVIDER_SETUP.md) - API key setup for all providers
- [Role-LLM Matrix](docs/ROLE_LLM_MATRIX.md) - Recommended LLMs per agent role
- [Agent Roles](docs/AGENT_ROLES.md) - Detailed role descriptions
- [Monitoring Guide](docs/QWEN_MONITORING.md) - Dashboard and WebSocket setup
- [Bot Usage Guide](docs/BOT_USAGE_GUIDE.md) - Bot account setup and usage
- [Instruction Validation Guide](docs/INSTRUCTION_VALIDATION_GUIDE.md) - Enforce project standards
- [Security Guide](docs/SECURITY.md) - Security best practices
- [Licensing Guide](docs/LICENSING.md) - Dual-license overview and decision matrix
- [Commercial License Terms](docs/COMMERCIAL-LICENSE.md) - Proprietary usage agreement

## 🎯 Use Cases

- 🎯 **Issue Implementation**: Autonomous implementation of GitHub issues
- 🔧 **Feature Development**: Multi-phase feature additions
- 🔍 **Code Reviews**: Automated PR reviews with quality scoring
- 📝 **Documentation**: Auto-generate docs from code
- 🧪 **Test Generation**: Create unit/integration tests
- 🔄 **Refactoring**: Large-scale code improvements
- 🐛 **Bug Fixing**: Automated debugging workflows
- 📊 **Project Coordination**: Multi-agent task planning and distribution

## 🔧 Advanced Features

### Multi-LLM Support

Configure different LLMs for different agents:

```yaml
# config/agent_config.yaml
agents:
  coder:
    llm: "gpt-4-turbo"
    fallback: "qwen2.5-coder:32b"
  
  reviewer:
    llm: "claude-3-sonnet"
    fallback: "gpt-4-turbo"
  
  coordinator:
    llm: "claude-3-opus"
    fallback: "gpt-4-turbo"
```

### Autonomous Polling

Monitor GitHub repositories for new issues automatically:

```bash
python3 agents/polling_service.py \
  --repos owner/repo1 owner/repo2 \
  --interval 300 \
  --labels agent-ready auto-assign \
  --max-concurrent 3
```

### Automated Code Review

AI-powered PR reviews with comprehensive checks:

```bash
python -m agents.pr_reviewer owner/repo 42 --username my-bot
```

### Instruction Validation

Automatically enforce project standards defined in `.github/copilot-instructions.md`:

```python
from agents.instruction_validator import InstructionValidator

# Initialize validator
validator = InstructionValidator(project_root="/path/to/project")

# Validate file location (blocks root directory violations)
result = validator.validate_file_location("test.py")
if not result.valid:
    print(f"❌ {result.message}")

# Validate commit message (enforces conventional commits)
result = validator.validate_commit_message("update files")
if not result.valid:
    # Auto-fix invalid format
    fixed = validator.auto_fix_commit_message("update files")
    print(f"✅ Auto-fixed: {fixed}")

# Generate compliance report
report = validator.generate_compliance_report(
    changed_files=["agents/test.py", "CHANGELOG.md"],
    commit_message="feat(validator): add validation"
)
print(report.get_summary())
```

**Features:**
- ✅ File location validation (root directory rule)
- ✅ Commit message format enforcement (conventional commits)
- ✅ Changelog requirement checking
- ✅ Port usage validation (assigned ranges)
- ✅ Documentation language checking (English)
- ✅ Auto-fix for common violations
- ✅ Educational feedback explaining rules

**Integration:**
- Automatically integrated into `IssueHandler`, `FileEditor`, and `GitOperations`
- Non-breaking and optional (fails gracefully if disabled)
- Configurable via `config/instruction_rules.yaml`

See [Instruction Validation Guide](docs/INSTRUCTION_VALIDATION_GUIDE.md) for detailed usage.

### Bot Account Operations

Dedicated bot account for GitHub operations:

```bash
python -m agents.bot_agent create \
  --repo owner/repo \
  --title "New feature" \
  --body "Description" \
  --labels "enhancement,high-priority"
```

## 🌐 Supported LLM Providers

### Commercial
- **OpenAI**: GPT-4 Turbo, GPT-4, GPT-3.5 Turbo
- **Anthropic**: Claude 3 Opus, Sonnet, Haiku
- **Google**: Gemini Pro (free tier available)
- **Cohere**: Command models
- **Together AI**: Open source model hosting

### Local (via Ollama)
- **Qwen2.5-Coder**: 7B, 14B, 32B (specialized for code)
- **DeepSeek-Coder**: 6.7B, 33B
- **CodeLlama**: 7B, 13B, 34B
- **Mixtral**: 8x7B, 8x22B (strong reasoning)
- **Llama 3**: 8B, 70B

See [docs/LLM_PROVIDER_SETUP.md](docs/LLM_PROVIDER_SETUP.md) for setup guides and cost comparison.

## 🔐 Security

- 🔒 **Token Security**: Store GitHub tokens securely in environment variables
- 🛡️ **Terminal Whitelist**: Configurable command whitelist/blacklist
- ✅ **Operation Approval**: Critical operations require confirmation
- 📝 **Audit Logging**: All operations logged for security review
- 🚫 **Bot Account Isolation**: Separate bot account prevents email spam

## 📦 Project Structure

```
agent-forge/
├── agents/              # Agent implementations
├── configs/             # Project configurations
├── docs/                # Documentation
├── frontend/            # Real-time monitoring dashboard
├── scripts/             # Deployment and utility scripts
├── tests/               # Unit tests
└── README.md
```

## 🚀 Deployment

### Systemd Service (Production)

```bash
# Install as system service
sudo ./scripts/install-service.sh

# Configure environment
sudo nano /etc/default/agent-forge
# Add: BOT_GITHUB_TOKEN=your_token_here

# Start service
sudo systemctl start agent-forge
sudo systemctl enable agent-forge

# View logs
sudo journalctl -u agent-forge -f
```

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📄 License

Agent-Forge is **dual licensed**:

- **GNU Affero General Public License v3.0 (AGPLv3)** — see [LICENSE](LICENSE)
- **Agent Forge Commercial License** — see [docs/COMMERCIAL-LICENSE.md](docs/COMMERCIAL-LICENSE.md)

Choose the license that matches your use case. See [docs/LICENSING.md](docs/LICENSING.md) for guidance and FAQs.

## 🙏 Credits

Created for the Caramba AI platform project.

Powered by:
- [Ollama](https://ollama.com) - Local LLM runtime
- [FastAPI](https://fastapi.tiangolo.com) - Backend framework
- [WebSocket](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket) - Real-time communication

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/m0nk111/agent-forge/issues)
- **Discussions**: [GitHub Discussions](https://github.com/m0nk111/agent-forge/discussions)
- **Documentation**: [docs/](docs/)

---

**Status**: Active Development | **Version**: 0.2.0 | **Python**: 3.12+

Made with ❤️ by the Agent-Forge community
