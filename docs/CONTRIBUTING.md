# Contributing to Agent-Forge 🤝

Thank you for your interest in contributing to Agent-Forge! This document provides guidelines and information for contributors.

---

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Documentation](#documentation)
- [Pull Request Process](#pull-request-process)
- [Issue Reporting](#issue-reporting)
- [Agent Development](#agent-development)

---

## 🤝 Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inspiring community for all. Please be respectful and constructive in your interactions.

### Expected Behavior

- ✅ Use welcoming and inclusive language
- ✅ Respect differing viewpoints and experiences
- ✅ Accept constructive criticism gracefully
- ✅ Focus on what's best for the community
- ✅ Show empathy towards other community members

### Unacceptable Behavior

- ❌ Harassment, trolling, or discriminatory language
- ❌ Personal attacks or insults
- ❌ Publishing others' private information
- ❌ Unethical or unprofessional conduct

---

## 🚀 Getting Started

### Prerequisites

Before contributing, ensure you have:

- **Python 3.12+** installed
- **Git** for version control
- **Ollama** installed and running (for local LLM testing)
- **GitHub account** with SSH keys configured
- Basic understanding of multi-agent systems

### Setting Up Development Environment

1. **Fork the repository**:
   ```bash
   # Fork on GitHub, then clone your fork
   git clone git@github.com:YOUR_USERNAME/agent-forge.git
   cd agent-forge
   ```

2. **Add upstream remote**:
   ```bash
   git remote add upstream git@github.com:m0nk111/agent-forge.git
   git fetch upstream
   ```

3. **Create virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Linux/Mac
   # or
   venv\Scripts\activate  # Windows
   ```

4. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # Development dependencies
   ```

5. **Install Ollama models**:
   ```bash
   ollama pull qwen2.5-coder:7b
   ollama pull qwen2.5-coder:14b  # Optional, for testing
   ```

6. **Configure environment**:
   ```bash
   cp config/agents.yaml.example config/agents.yaml
   cp .env.example .env
   # Edit .env with your GitHub tokens
   ```

7. **Verify setup**:
   ```bash
   python -m pytest tests/
   python -m agents.service_manager --help
   ```

---

## 🔄 Development Workflow

### Branch Strategy

We use **trunk-based development** with feature branches:

```
main (protected)
  │
  ├── feat/your-feature-name
  ├── fix/bug-description
  ├── docs/documentation-update
  └── refactor/code-improvement
```

### Creating a Feature Branch

```bash
# Sync with upstream
git checkout main
git pull upstream main

# Create feature branch
git checkout -b feat/your-feature-name

# Make your changes...

# Commit with conventional commits
git add .
git commit -m "feat: add new agent monitoring feature"

# Push to your fork
git push origin feat/your-feature-name
```

### Branch Naming Conventions

- `feat/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation changes
- `refactor/` - Code refactoring
- `test/` - Test additions/improvements
- `chore/` - Maintenance tasks

---

## 📝 Coding Standards

### Python Style Guide

We follow **PEP 8** with some project-specific conventions:

#### Import Organization

```python
# Standard library imports
import os
import sys
from pathlib import Path

# Third-party imports
import requests
import yaml
from flask import Flask

# Local application imports
from agents.bot_agent import BotAgent
from utils.logger import setup_logger
```

#### Docstrings

Use **Google-style docstrings**:

```python
def process_issue(issue_number: int, repo: str) -> Dict[str, Any]:
    """Process a GitHub issue and generate a solution.
    
    Args:
        issue_number: The GitHub issue number to process
        repo: Repository in format 'owner/repo'
        
    Returns:
        Dictionary containing:
            - status: Success or error status
            - solution: Generated code solution
            - pr_url: URL of created pull request
            
    Raises:
        ValueError: If issue_number is invalid
        GitHubAPIError: If GitHub API call fails
        
    Example:
        >>> result = process_issue(42, "m0nk111/agent-forge")
        >>> print(result['status'])
        'success'
    """
    # Implementation...
```

#### Type Hints

Always use type hints:

```python
from typing import Dict, List, Optional, Any

def get_agent_status(agent_id: str) -> Optional[Dict[str, Any]]:
    """Get agent status by ID."""
    pass

def update_agents(agents: List[str], config: Dict[str, Any]) -> None:
    """Update multiple agents with new configuration."""
    pass
```

#### Naming Conventions

```python
# Classes: PascalCase
class BotAgent:
    pass

# Functions/methods: snake_case
def process_github_issue():
    pass

# Constants: UPPER_SNAKE_CASE
MAX_RETRY_ATTEMPTS = 3
DEFAULT_MODEL = "qwen2.5-coder:7b"

# Private methods: _leading_underscore
def _internal_helper():
    pass
```

### Code Quality Tools

#### Linting with Ruff

```bash
# Check code quality
ruff check .

# Auto-fix issues
ruff check --fix .
```

#### Formatting with Black

```bash
# Format all Python files
black .

# Check formatting without changes
black --check .
```

#### Type Checking with mypy

```bash
# Run type checker
mypy agents/

# Strict mode
mypy --strict agents/bot_agent.py
```

### Configuration Files

Use **YAML** for configuration:

```yaml
# Good: Clear, structured, with comments
agent:
  name: "bot-agent"
  model: "qwen2.5-coder:7b"
  mode: "production"  # idle, test, production
  
  # Retry configuration
  retry:
    max_attempts: 3
    backoff: "exponential"
    initial_delay: 1.0
```

---

## 🧪 Testing Guidelines

### Test Structure

```
tests/
├── unit/                    # Unit tests (fast, isolated)
│   ├── test_bot_agent.py
│   ├── test_code_agent.py
│   └── test_config_manager.py
├── integration/             # Integration tests (slower)
│   ├── test_github_integration.py
│   ├── test_ollama_integration.py
│   └── test_websocket_integration.py
├── e2e/                     # End-to-end tests
│   └── test_full_workflow.py
└── fixtures/                # Test data
    ├── sample_issues.json
    └── mock_responses.json
```

### Writing Tests

#### Unit Tests

```python
import pytest
from agents.bot_agent import BotAgent

def test_bot_agent_initialization():
    """Test BotAgent initializes with correct defaults."""
    agent = BotAgent(name="test-bot", model="qwen2.5-coder:7b")
    
    assert agent.name == "test-bot"
    assert agent.model == "qwen2.5-coder:7b"
    assert agent.status == "idle"

def test_bot_agent_handles_invalid_config():
    """Test BotAgent raises error with invalid configuration."""
    with pytest.raises(ValueError, match="Invalid model"):
        BotAgent(name="test-bot", model="invalid-model")
```

#### Integration Tests

```python
import pytest
from agents.github_client import GitHubClient

@pytest.mark.integration
def test_github_issue_fetching():
    """Test fetching real GitHub issues."""
    client = GitHubClient(token=os.getenv("GITHUB_TOKEN"))
    issues = client.get_issues("m0nk111/agent-forge", state="open")
    
    assert isinstance(issues, list)
    assert len(issues) >= 0
    if issues:
        assert "number" in issues[0]
        assert "title" in issues[0]
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/unit/test_bot_agent.py

# Run tests with coverage
pytest --cov=agents --cov-report=html

# Run only unit tests (fast)
pytest tests/unit/

# Run integration tests (slower)
pytest tests/integration/ -v

# Run with specific markers
pytest -m "not slow"
```

### Test Coverage

**Minimum Coverage**: 70%  
**Target Coverage**: 85%+

```bash
# Generate coverage report
pytest --cov=agents --cov-report=term-missing

# Generate HTML report
pytest --cov=agents --cov-report=html
# Open htmlcov/index.html in browser
```

### Mocking External Services

```python
from unittest.mock import Mock, patch

@patch('agents.bot_agent.requests.post')
def test_ollama_api_call(mock_post):
    """Test Ollama API call with mock."""
    mock_response = Mock()
    mock_response.json.return_value = {"response": "Generated code"}
    mock_post.return_value = mock_response
    
    agent = BotAgent()
    result = agent.generate_code("Fix bug in parser")
    
    assert result == "Generated code"
    mock_post.assert_called_once()
```

---

## 📚 Documentation

### Documentation Standards

#### Code Comments

```python
# Good: Explain WHY, not WHAT
# Retry with exponential backoff to handle rate limits
for attempt in range(MAX_RETRIES):
    response = api_call()
    if response.ok:
        break
    time.sleep(2 ** attempt)

# Bad: Comment states the obvious
# Loop through retry attempts
for attempt in range(MAX_RETRIES):
    ...
```

#### Module Docstrings

```python
"""
Bot Agent Module

This module implements the BotAgent class which handles GitHub operations
for the agent-forge system. It processes issues, creates branches, commits
code, and manages pull requests.

Key Features:
- Automatic issue assignment detection
- Branch management with naming conventions
- Commit message generation following conventional commits
- Pull request creation and updates

Example:
    >>> agent = BotAgent(name="bot-1", model="qwen2.5-coder:7b")
    >>> agent.process_issue(issue_number=42, repo="m0nk111/agent-forge")
    
See Also:
    - agents.code_agent: Code generation functionality
    - agents.coordinator_agent: Task orchestration
"""
```

### Documentation Files

When adding/modifying features, update:

- **README.md**: High-level overview, quick start
- **ARCHITECTURE.md**: Technical deep dive, system design
- **CHANGELOG.md**: All changes (required!)
- **API docs**: If adding/changing endpoints
- **Inline docs**: For complex logic

### Changelog Discipline

**CRITICAL**: Every PR must update `CHANGELOG.md`!

```markdown
## [Unreleased] - 2025-10-06

### Added
- **Feature Name** (PR #XX, commit `abc1234`):
  - Clear description of what was added
  - Why it was added
  - How to use it

### Fixed
- **Bug Description** (Issue #YY, commit `def5678`):
  - What was broken
  - How it was fixed
  - Impact on users
```

---

## 🔀 Pull Request Process

### Before Creating a PR

- [ ] Code follows style guidelines (run `black`, `ruff`)
- [ ] All tests pass (`pytest`)
- [ ] New code has tests (min 70% coverage)
- [ ] Documentation updated (if needed)
- [ ] **CHANGELOG.md updated** (required!)
- [ ] Commit messages follow conventional commits
- [ ] Branch is up-to-date with main

### Creating a Pull Request

1. **Push your branch**:
   ```bash
   git push origin feat/your-feature-name
   ```

2. **Create PR on GitHub**:
   - Go to your fork on GitHub
   - Click "Compare & pull request"
   - Use descriptive title (e.g., "feat: add agent retry mechanism")
   - Fill out PR template completely

3. **PR Description Template**:

   ```markdown
   ## Description
   
   Brief overview of changes (2-3 sentences).
   
   ## Changes
   
   - Added retry mechanism to BotAgent
   - Updated error handling in CodeAgent
   - Added integration tests for retry logic
   
   ## Related Issues
   
   - Fixes #42
   - Related to #38
   
   ## Testing
   
   - [ ] Unit tests added/updated
   - [ ] Integration tests pass
   - [ ] Manual testing completed
   
   ## Checklist
   
   - [x] Code follows style guidelines
   - [x] Tests added and passing
   - [x] Documentation updated
   - [x] CHANGELOG.md updated
   - [x] No breaking changes (or documented)
   
   ## Screenshots (if applicable)
   
   [Add screenshots for UI changes]
   ```

### PR Review Process

1. **Automated Checks**:
   - GitHub Actions run tests
   - Code quality checks (ruff, black)
   - Coverage report generated

2. **Code Review**:
   - At least one maintainer review required
   - Address all comments
   - Request re-review after changes

3. **GitHub Copilot Review** (optional):
   ```bash
   # Request automated Copilot review
   gh pr review --copilot
   ```

4. **Merge Requirements**:
   - All checks passing ✅
   - At least 1 approval ✅
   - CHANGELOG.md updated ✅
   - No merge conflicts ✅

5. **Merge Strategy**:
   - **Squash merge** for features (clean history)
   - **Regular merge** for release branches
   - Delete branch after merge

### After PR Merge

```bash
# Sync your fork
git checkout main
git pull upstream main
git push origin main

# Delete feature branch
git branch -d feat/your-feature-name
git push origin --delete feat/your-feature-name
```

---

## 🐛 Issue Reporting

### Bug Reports

Use the **Bug Report** template:

```markdown
**Description**
Clear description of the bug.

**To Reproduce**
Steps to reproduce:
1. Start service with `python -m agents.service_manager`
2. Open dashboard at http://localhost:8897
3. Click on agent card
4. See error

**Expected Behavior**
What should happen instead.

**Actual Behavior**
What actually happens.

**Environment**
- OS: Ubuntu 24.04
- Python: 3.12.0
- Agent-Forge: v0.2.0
- Ollama: 0.1.32

**Logs**
```
[paste relevant logs here]
```

**Screenshots**
[If applicable]

**Additional Context**
Any other relevant information.
```

### Feature Requests

Use the **Feature Request** template:

```markdown
**Problem Statement**
What problem does this solve?

**Proposed Solution**
How should it work?

**Alternatives Considered**
What other approaches did you consider?

**Implementation Ideas**
Suggestions for implementation (optional).

**Benefits**
Who benefits and how?

**Priority**
Low / Medium / High
```

### Issue Labels

- `bug` - Something isn't working
- `feature` - New feature request
- `documentation` - Documentation improvements
- `enhancement` - Improvement to existing feature
- `good first issue` - Good for newcomers
- `help wanted` - Need community help
- `question` - Further information needed
- `wontfix` - Won't be worked on
- `duplicate` - Duplicate issue

---

## 🤖 Agent Development

### Creating a New Agent

1. **Create agent file**:
   ```bash
   touch agents/your_agent.py
   ```

2. **Implement agent class**:
   ```python
   from agents.base_agent import BaseAgent
   
   class YourAgent(BaseAgent):
       """Your agent description."""
       
       def __init__(self, name: str, model: str, **kwargs):
           super().__init__(name, model, **kwargs)
           # Your initialization
       
       def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
           """Process a task."""
           # Your implementation
           pass
   ```

3. **Add configuration**:
   ```yaml
   # config/agents.yaml
   your_agent:
     model: "qwen2.5-coder:7b"
     mode: "idle"
     max_tokens: 8192
   ```

4. **Add tests**:
   ```python
   # tests/unit/test_your_agent.py
   def test_your_agent_initialization():
       agent = YourAgent(name="test", model="qwen2.5-coder:7b")
       assert agent.name == "test"
   ```

5. **Update documentation**:
   - Add to `ARCHITECTURE.md` under "Agent Roles"
   - Update `README.md` features list
   - Add to `docs/AGENT_ONBOARDING.md`

### Agent Best Practices

- **Single Responsibility**: Each agent should have one clear purpose
- **Error Handling**: Always handle exceptions gracefully
- **Logging**: Use structured logging for debugging
- **State Management**: Keep agents stateless when possible
- **Configuration**: All behavior should be configurable
- **Testing**: Write comprehensive tests for agent logic

---

## 🎯 Development Tips

### Quick Commands

```bash
# Run full CI pipeline locally
./scripts/ci_check.sh

# Start service in development mode
python -m agents.service_manager --debug

# Watch logs in real-time
tail -f logs/agent-forge.log

# Check code quality
ruff check . && black --check . && mypy agents/

# Run fast tests only
pytest -m "not slow" -v
```

### Debugging

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Use breakpoint() for interactive debugging
def process_issue(issue_id):
    breakpoint()  # Drops into debugger
    result = do_something(issue_id)
    return result
```

### Common Issues

See [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) for solutions to common problems.

---

## 📞 Getting Help

### Resources

- **Documentation**: [docs/](docs/)
- **Architecture Guide**: [ARCHITECTURE.md](ARCHITECTURE.md)
- **Agent Onboarding**: [docs/AGENT_ONBOARDING.md](docs/AGENT_ONBOARDING.md)
- **Troubleshooting**: [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)

### Community

- **Issues**: [GitHub Issues](https://github.com/m0nk111/agent-forge/issues)
- **Discussions**: [GitHub Discussions](https://github.com/m0nk111/agent-forge/discussions)
- **Email**: [m0nk111@users.noreply.github.com](mailto:m0nk111@users.noreply.github.com)

### Questions?

If you have questions:

1. Check existing documentation
2. Search closed issues
3. Ask in GitHub Discussions
4. Create a new issue with `question` label

---

## 🏆 Recognition

### Contributors

All contributors are recognized in:
- [GitHub Contributors Page](https://github.com/m0nk111/agent-forge/graphs/contributors)
- Release notes
- CHANGELOG.md

### Types of Contributions

We value all contributions:
- 💻 Code contributions
- 📝 Documentation improvements
- 🐛 Bug reports
- 💡 Feature suggestions
- 🧪 Testing and QA
- 📢 Spreading the word

---

## 📜 License

By contributing, you agree that your contributions will be licensed under the **GNU Affero General Public License v3.0 (AGPL-3.0)**.

See [LICENSE](LICENSE) for full details.

---

**Thank you for contributing to Agent-Forge! 🚀**

*Last updated: October 6, 2025*
