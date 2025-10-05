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

## Project Structure

```
agent-forge/
├── agents/              # Agent implementations
│   └── qwen_agent.py        # Generic Qwen agent (config-driven)
├── configs/             # Project configurations
│   └── caramba_personality_ai.yaml  # Example: Caramba Issue #7
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
