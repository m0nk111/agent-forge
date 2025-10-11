# Testing Guide 🧪

Comprehensive guide for testing Agent-Forge components.

---

## 📋 Table of Contents

- [Testing Philosophy](#testing-philosophy)
- [Test Structure](#test-structure)
- [Running Tests](#running-tests)
- [Unit Tests](#unit-tests)
- [Integration Tests](#integration-tests)
- [End-to-End Tests](#end-to-end-tests)
- [Test Coverage](#test-coverage)
- [Mocking and Fixtures](#mocking-and-fixtures)
- [CI/CD Testing](#cicd-testing)

---

## 🎯 Testing Philosophy

### Testing Pyramid

```
         /\
        /  \  E2E Tests (few, slow, expensive)
       /____\
      /      \  Integration Tests (some, moderate speed)
     /________\
    /          \  Unit Tests (many, fast, cheap)
   /____________\
```

**Ratios**:
- Unit Tests: 70%
- Integration Tests: 20%
- E2E Tests: 10%

### Key Principles

1. **Fast Feedback**: Tests should run quickly for rapid development
2. **Isolation**: Each test should be independent
3. **Repeatability**: Tests should produce consistent results
4. **Maintainability**: Tests should be easy to understand and update
5. **Coverage**: Aim for 85%+ code coverage

---

## 📁 Test Structure

### Directory Layout

```
tests/
├── __init__.py
├── conftest.py                 # Shared fixtures
├── unit/                       # Fast, isolated tests
│   ├── __init__.py
│   ├── test_bot_agent.py
│   ├── test_code_agent.py
│   ├── test_coordinator_agent.py
│   ├── test_config_manager.py
│   ├── test_github_client.py
│   ├── test_instruction_validator.py
│   └── test_workspace_tools.py
├── integration/                # Component interaction tests
│   ├── __init__.py
│   ├── test_github_integration.py
│   ├── test_ollama_integration.py
│   ├── test_websocket_integration.py
│   ├── test_database_integration.py
│   └── test_validator_integration.py
├── e2e/                        # Full workflow tests
│   ├── __init__.py
│   ├── test_issue_processing.py
│   ├── test_pr_creation.py
│   └── test_monitoring_dashboard.py
├── fixtures/                   # Test data
│   ├── sample_issues.json
│   ├── sample_prs.json
│   ├── mock_ollama_responses.json
│   └── test_repositories.yaml
└── helpers/                    # Test utilities
    ├── __init__.py
    ├── mock_github.py
    ├── mock_ollama.py
    └── test_utils.py
```

### Test File Naming

- `test_*.py` - Test files
- `*_test.py` - Alternative (both work)
- `conftest.py` - Pytest configuration and fixtures

### Test Function Naming

```python
def test_<component>_<action>_<expected_result>():
    """Clear description of what is being tested."""
    pass

# Examples:
def test_bot_agent_initializes_with_valid_config():
def test_code_agent_handles_missing_model_gracefully():
def test_github_client_retries_on_rate_limit():
```

---

## 🚀 Running Tests

### Basic Commands

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/unit/test_bot_agent.py

# Run specific test function
pytest tests/unit/test_bot_agent.py::test_bot_agent_initialization

# Run specific test class
pytest tests/unit/test_bot_agent.py::TestBotAgent

# Run tests matching pattern
pytest -k "bot_agent"

# Run tests with specific marker
pytest -m "unit"
pytest -m "integration"
pytest -m "slow"
```

### Parallel Execution

```bash
# Install pytest-xdist
pip install pytest-xdist

# Run tests in parallel (4 workers)
pytest -n 4

# Auto-detect CPU count
pytest -n auto
```

### Watch Mode

```bash
# Install pytest-watch
pip install pytest-watch

# Run tests on file changes
ptw

# With specific options
ptw -- -v -x
```

### Failed Tests Only

```bash
# Run only failed tests from last run
pytest --lf

# Run failed tests first, then all
pytest --ff
```

---

## 🔬 Unit Tests

### Purpose

Test individual functions/methods in isolation without external dependencies.

### Characteristics

- **Fast**: < 100ms per test
- **Isolated**: No network, filesystem, or database
- **Mocked**: External dependencies are mocked
- **Focused**: One logical concept per test

### Example: Testing Bot Agent

```python
# tests/unit/test_bot_agent.py
import pytest
from unittest.mock import Mock, patch
from agents.bot_agent import BotAgent

class TestBotAgent:
    """Test suite for BotAgent class."""
    
    def test_initialization_with_valid_config(self):
        """Test BotAgent initializes correctly with valid configuration."""
        agent = BotAgent(
            name="test-bot",
            model="qwen2.5-coder:7b",
            mode="idle"
        )
        
        assert agent.name == "test-bot"
        assert agent.model == "qwen2.5-coder:7b"
        assert agent.mode == "idle"
        assert agent.status == "idle"
    
    def test_initialization_with_invalid_model(self):
        """Test BotAgent raises error with invalid model."""
        with pytest.raises(ValueError, match="Invalid model"):
            BotAgent(name="test-bot", model="invalid-model")
    
    @patch('agents.bot_agent.requests.post')
    def test_github_api_call_with_retry(self, mock_post):
        """Test GitHub API call retries on failure."""
        # Setup mock to fail twice, then succeed
        mock_post.side_effect = [
            Mock(ok=False, status_code=502),
            Mock(ok=False, status_code=502),
            Mock(ok=True, json=lambda: {"id": 123})
        ]
        
        agent = BotAgent(name="test-bot")
        result = agent._call_github_api("https://api.github.com/test")
        
        assert result["id"] == 123
        assert mock_post.call_count == 3
    
    def test_branch_name_generation(self):
        """Test branch name follows conventions."""
        agent = BotAgent(name="test-bot")
        
        branch = agent._generate_branch_name(issue_number=42, title="Fix bug in parser")
        
        assert branch.startswith("fix/")
        assert "42" in branch
        assert "parser" in branch.lower()
        assert " " not in branch  # No spaces
        assert branch == branch.lower()  # All lowercase
```

### Testing Patterns

#### Arrange-Act-Assert (AAA)

```python
def test_config_loading():
    # Arrange: Set up test data
    config_data = {"agent": {"model": "qwen2.5-coder:7b"}}
    
    # Act: Execute the code under test
    config = ConfigManager.load(config_data)
    
    # Assert: Verify the result
    assert config.get("agent.model") == "qwen2.5-coder:7b"
```

#### Given-When-Then (BDD style)

```python
def test_agent_processes_assigned_issue():
    """
    Given: An agent is idle and monitoring GitHub
    When: A new issue is assigned to the agent
    Then: The agent should process the issue
    """
    # Given
    agent = BotAgent(name="bot-1", mode="production")
    issue = create_test_issue(assignee="bot-1")
    
    # When
    result = agent.process_issue(issue)
    
    # Then
    assert result["status"] == "success"
    assert result["branch_created"] is True
```

---

## 🔗 Integration Tests

### Purpose

Test interaction between multiple components with real external services.

### Characteristics

- **Slower**: 1-10 seconds per test
- **Real Services**: Use actual GitHub API, Ollama, database
- **Setup/Teardown**: Require environment setup
- **Marked**: Use `@pytest.mark.integration`

### Example: GitHub Integration

```python
# tests/integration/test_github_integration.py
import pytest
import os
from agents.github_client import GitHubClient
from agents.bot_agent import BotAgent

@pytest.mark.integration
class TestGitHubIntegration:
    """Integration tests for GitHub operations."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test environment."""
        self.token = os.getenv("GITHUB_TEST_TOKEN")
        if not self.token:
            pytest.skip("GITHUB_TEST_TOKEN not set")
        
        self.client = GitHubClient(token=self.token)
        self.repo = "your-org/your-project-test"
    
    def test_fetch_open_issues(self):
        """Test fetching real open issues from GitHub."""
        issues = self.client.get_issues(self.repo, state="open")
        
        assert isinstance(issues, list)
        if issues:
            assert "number" in issues[0]
            assert "title" in issues[0]
            assert "state" in issues[0]
    
    def test_create_and_close_issue(self):
        """Test full issue lifecycle."""
        # Create issue
        issue = self.client.create_issue(
            repo=self.repo,
            title="Test issue - can be deleted",
            body="This is a test issue for integration testing."
        )
        
        assert issue["number"] > 0
        assert issue["state"] == "open"
        
        # Close issue
        updated = self.client.update_issue(
            repo=self.repo,
            issue_number=issue["number"],
            state="closed"
        )
        
        assert updated["state"] == "closed"
    
    def test_create_branch_and_pr(self):
        """Test creating branch and pull request."""
        # Create test branch
        branch_name = f"test/integration-{int(time.time())}"
        self.client.create_branch(
            repo=self.repo,
            branch=branch_name,
            from_branch="main"
        )
        
        # Create file
        self.client.create_file(
            repo=self.repo,
            path="test_file.txt",
            content="Test content",
            message="test: add test file",
            branch=branch_name
        )
        
        # Create PR
        pr = self.client.create_pull_request(
            repo=self.repo,
            title="Test PR",
            body="Integration test PR",
            head=branch_name,
            base="main"
        )
        
        assert pr["number"] > 0
        assert pr["state"] == "open"
        
        # Cleanup: Close PR
        self.client.update_pull_request(
            repo=self.repo,
            pr_number=pr["number"],
            state="closed"
        )
```

### Example: Ollama Integration

```python
# tests/integration/test_ollama_integration.py
import pytest
import requests
from agents.code_agent import CodeAgent

@pytest.mark.integration
class TestOllamaIntegration:
    """Integration tests for Ollama LLM."""
    
    @pytest.fixture(autouse=True)
    def check_ollama(self):
        """Check if Ollama is running."""
        try:
            response = requests.get("http://localhost:11434/api/tags")
            if response.status_code != 200:
                pytest.skip("Ollama not running")
        except requests.exceptions.ConnectionError:
            pytest.skip("Ollama not accessible")
    
    def test_model_availability(self):
        """Test required model is available."""
        response = requests.get("http://localhost:11434/api/tags")
        models = response.json()["models"]
        model_names = [m["name"] for m in models]
        
        assert "qwen2.5-coder:7b" in model_names
    
    def test_code_generation(self):
        """Test actual code generation with Ollama."""
        agent = CodeAgent(name="test-agent", model="qwen2.5-coder:7b")
        
        result = agent.generate_code(
            prompt="Write a Python function to calculate fibonacci numbers"
        )
        
        assert result is not None
        assert len(result) > 50
        assert "def" in result or "fibonacci" in result.lower()
    
    def test_code_generation_with_context(self):
        """Test code generation with project context."""
        agent = CodeAgent(name="test-agent", model="qwen2.5-coder:7b")
        
        context = {
            "repo": "your-org/your-project",
            "issue_title": "Add retry mechanism",
            "issue_body": "Implement exponential backoff for API calls",
            "files": ["engine/runners/bot_agent.py"]
        }
        
        result = agent.generate_solution(context)
        
        assert result is not None
        assert "retry" in result.lower() or "backoff" in result.lower()
```

---

## 🌐 End-to-End Tests

### Purpose

Test complete user workflows from start to finish.

### Characteristics

- **Slowest**: 10-60 seconds per test
- **Full System**: All components running
- **Real Environment**: Production-like setup
- **Marked**: Use `@pytest.mark.e2e`

### Example: Full Issue Processing

```python
# tests/e2e/test_issue_processing.py
import pytest
import time
from agents.service_manager import ServiceManager
from tests.helpers.github_helper import create_test_issue, wait_for_pr

@pytest.mark.e2e
class TestIssueProcessing:
    """End-to-end tests for issue processing workflow."""
    
    @pytest.fixture(scope="class")
    def service_manager(self):
        """Start service manager for E2E tests."""
        manager = ServiceManager(
            service_port=8180,  # Use different ports
            monitor_port=7997,
            web_port=8997
        )
        manager.start()
        
        # Wait for services to be ready
        time.sleep(5)
        
        yield manager
        
        # Cleanup
        manager.stop()
    
    def test_complete_issue_workflow(self, service_manager):
        """
        Test complete workflow:
        1. Create issue
        2. Assign to bot
        3. Wait for bot to process
        4. Verify PR created
        5. Verify code changes
        """
        # 1. Create test issue
        issue = create_test_issue(
            repo="your-org/your-project-test",
            title="Add hello world function",
            body="Create a simple hello world function in Python",
            assignee="your-bot-agent"
        )
        
        # 2. Wait for polling to detect issue (max 6 minutes)
        time.sleep(360)
        
        # 3. Check if PR was created
        pr = wait_for_pr(
            repo="your-org/your-project-test",
            issue_number=issue["number"],
            timeout=600  # 10 minutes
        )
        
        assert pr is not None, "PR was not created"
        assert f"#{issue['number']}" in pr["title"]
        
        # 4. Verify PR content
        files = get_pr_files(pr["number"])
        assert len(files) > 0, "PR has no file changes"
        
        # 5. Verify code was added
        diff = get_pr_diff(pr["number"])
        assert "def hello" in diff or "print" in diff
```

---

## 📊 Test Coverage

### Measuring Coverage

```bash
# Run with coverage
pytest --cov=agents --cov-report=html --cov-report=term

# View HTML report
open htmlcov/index.html

# Terminal report with missing lines
pytest --cov=agents --cov-report=term-missing

# Generate XML (for CI)
pytest --cov=agents --cov-report=xml
```

### Coverage Configuration

```ini
# setup.cfg or pyproject.toml
[tool.coverage.run]
source = agents
omit =
    */tests/*
    */venv/*
    */__pycache__/*

[tool.coverage.report]
precision = 2
show_missing = True
skip_covered = False

# Fail if coverage below threshold
fail_under = 70

exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:
```

### Coverage Targets

| Component | Minimum | Target |
|-----------|---------|--------|
| Core Agents | 80% | 90% |
| Utilities | 70% | 85% |
| API Endpoints | 75% | 85% |
| Configuration | 60% | 75% |
| Overall | 70% | 85% |

---

## 🎭 Mocking and Fixtures

### Pytest Fixtures

```python
# tests/conftest.py
import pytest
from agents.bot_agent import BotAgent
from agents.config_manager import ConfigManager

@pytest.fixture
def bot_agent():
    """Provide a bot agent instance for testing."""
    return BotAgent(name="test-bot", model="qwen2.5-coder:7b")

@pytest.fixture
def sample_issue():
    """Provide sample GitHub issue data."""
    return {
        "number": 42,
        "title": "Fix bug in parser",
        "body": "Parser fails on special characters",
        "assignee": {"login": "bot-1"},
        "state": "open",
        "labels": [{"name": "bug"}]
    }

@pytest.fixture
def mock_config(tmp_path):
    """Provide temporary configuration."""
    config_file = tmp_path / "test_config.yaml"
    config_file.write_text("""
    agent:
      model: qwen2.5-coder:7b
      mode: test
    """)
    return ConfigManager(config_file)

@pytest.fixture(scope="session")
def ollama_running():
    """Check if Ollama is available (session-scoped)."""
    try:
        response = requests.get("http://localhost:11434/api/tags")
        return response.status_code == 200
    except:
        return False
```

### Using Fixtures

```python
def test_bot_processes_issue(bot_agent, sample_issue):
    """Test using multiple fixtures."""
    result = bot_agent.process_issue(sample_issue)
    assert result["status"] == "success"

def test_skip_if_ollama_not_running(ollama_running):
    """Test that requires Ollama."""
    if not ollama_running:
        pytest.skip("Ollama not available")
    # Test code...
```

### Mocking External Calls

```python
from unittest.mock import Mock, patch, MagicMock

# Mock requests.post
@patch('requests.post')
def test_api_call(mock_post):
    mock_post.return_value = Mock(
        ok=True,
        json=lambda: {"result": "success"}
    )
    # Test code...

# Mock multiple methods
@patch.object(BotAgent, '_call_github_api')
@patch.object(BotAgent, '_call_ollama_api')
def test_agent_workflow(mock_ollama, mock_github):
    mock_github.return_value = {"issue": "data"}
    mock_ollama.return_value = "generated code"
    # Test code...

# Mock with context manager
def test_with_mock():
    with patch('agents.bot_agent.time.sleep') as mock_sleep:
        # Test without actually sleeping
        agent.retry_with_backoff()
        assert mock_sleep.called
```

---

## 🔄 CI/CD Testing

### GitHub Actions Workflow

```yaml
# .github/workflows/tests.yml
name: Tests

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.12, 3.13]
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt
      
      - name: Run unit tests
        run: pytest tests/unit/ -v --cov=agents
      
      - name: Run integration tests
        run: pytest tests/integration/ -v
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TEST_TOKEN }}
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
```

### Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: pytest-unit
        name: pytest unit tests
        entry: pytest tests/unit/ -v
        language: system
        pass_filenames: false
        always_run: true
```

---

## 🎯 Best Practices

### DO ✅

- Write tests first (TDD)
- Keep tests simple and focused
- Use descriptive test names
- Test edge cases and error conditions
- Mock external dependencies
- Clean up after tests (fixtures/teardown)
- Run tests before committing
- Maintain high coverage

### DON'T ❌

- Test implementation details
- Write flaky tests
- Use sleep() for timing (use proper waits)
- Share state between tests
- Skip writing tests for "simple" code
- Commit failing tests
- Ignore coverage reports

---

**Happy Testing! 🧪**

*Last updated: October 6, 2025*
