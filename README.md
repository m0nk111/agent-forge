# Agent Forge 🔨

**Multi-LLM Agent Framework powered by Ollama**

Agent Forge is a framework for creating autonomous coding agents using different LLMs via Ollama. Each agent can work on specific tasks, issues, or projects using the strengths of different models (Qwen2.5-Coder, CodeLlama, DeepSeek-Coder, etc.).

## Features

- 🤖 **Multi-Model Support**: Use different LLMs for different tasks
- 📋 **Phase-Based Execution**: Break down complex tasks into manageable phases
- 🎨 **Code Generation**: Automatic file creation from LLM output
- 🔄 **Streaming Support**: Real-time output for long-running generations
- 🧪 **Dry Run Mode**: Test agent behavior without making changes
- 🎯 **Custom Tasks**: Execute one-off tasks outside predefined phases
- 📊 **Progress Tracking**: Detailed status and completion metrics

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
# Check Ollama status and available models
python3 agents/qwen_caramba_issue7.py --help

# Execute a specific phase (dry run)
python3 agents/qwen_caramba_issue7.py --phase 1 --dry-run

# Execute a specific phase (real)
python3 agents/qwen_caramba_issue7.py --phase 1

# Execute all phases
python3 agents/qwen_caramba_issue7.py --phase all

# Execute a custom task
python3 agents/qwen_caramba_issue7.py --task "Create authentication middleware"
```

## Project Structure

```
agent-forge/
├── agents/              # Agent implementations
│   ├── qwen_caramba_issue7.py    # Qwen agent for Caramba Issue #7
│   └── ...              # More agents for different projects/models
├── templates/           # Agent templates for new projects
├── lib/                 # Shared libraries
│   ├── ollama_client.py    # Ollama API client
│   ├── code_parser.py      # Parse LLM output into files
│   └── logger.py           # Colored logging utilities
├── docs/                # Documentation
├── tests/               # Unit tests
├── examples/            # Example configurations
└── README.md
```

## Creating a New Agent

Agents in Agent Forge follow a standard pattern. See `templates/agent_template.py` for a starting point.

### Example: Creating an Agent for a New Project

```python
from lib.ollama_client import OllamaClient
from lib.code_parser import CodeParser

agent = OllamaClient(model="qwen2.5-coder:7b")
parser = CodeParser(project_root="/path/to/project")

# Define phases
phases = {
    1: {"name": "Setup", "tasks": ["Create structure", "Add config"]},
    2: {"name": "Implementation", "tasks": ["Write core logic"]}
}

# Execute
agent.execute_phases(phases)
```

## Supported Models

Agent Forge works with any Ollama-compatible model, but is optimized for:

- **qwen2.5-coder:7b** - Excellent for Python/FastAPI (4.7GB)
- **codellama:7b** - Strong general coding (3.8GB)
- **deepseek-coder:6.7b** - Fast, efficient (3.8GB)
- **starcoder2:7b** - Multi-language support (4.0GB)

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

## Roadmap

- [ ] Multi-agent orchestration (agents working together)
- [ ] Web UI for monitoring agent progress
- [ ] Integration with GitHub Issues API
- [ ] Support for streaming to file (incremental saves)
- [ ] Agent memory/context management
- [ ] Model performance benchmarking
- [ ] Docker containerization
- [ ] CI/CD pipeline integration

---

**Status**: Active Development | **Version**: 0.1.0 | **Python**: 3.12+
