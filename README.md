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
