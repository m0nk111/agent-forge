"""
Tests for Bot Agent.

Tests all bot operations, rate limiting, error handling, retries, and metrics tracking.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from datetime import datetime, timedelta
from pathlib import Path
import subprocess
import json

from engine.runners.bot_agent import BotAgent, BotOperation, BotMetrics


@pytest.fixture
def mock_gh_token(monkeypatch):
    """Mock GitHub token environment variable."""
    monkeypatch.setenv("BOT_GITHUB_TOKEN", "ghp_test_token_123")
    monkeypatch.setenv("BOT_GITHUB_USERNAME", "test-bot")


@pytest.fixture
def bot_agent(mock_gh_token, tmp_path):
    """Create BotAgent instance for testing."""
    return BotAgent(
        agent_id="test-bot",
        username="test-bot",
        github_token="ghp_test_token_123"
    )


@pytest.fixture
def mock_subprocess_success():
    """Mock successful subprocess execution."""
    mock_result = Mock()
    mock_result.returncode = 0
    mock_result.stdout = json.dumps({"number": 42, "url": "https://github.com/test/repo/issues/42", "title": "Test Issue"})
    mock_result.stderr = ""
    return mock_result


@pytest.fixture
def mock_subprocess_failure():
    """Mock failed subprocess execution."""
    mock_result = Mock()
    mock_result.returncode = 1
    mock_result.stdout = ""
    mock_result.stderr = "Error: API request failed"
    return mock_result


class TestBotAgent:
    """Test BotAgent functionality."""
    
    def test_bot_initialization(self, bot_agent):
        """Test bot agent initialization."""
        assert bot_agent.agent_id == "test-bot"
        assert bot_agent.username == "test-bot"
        assert bot_agent.github_token == "ghp_test_token_123"
        assert isinstance(bot_agent.metrics, BotMetrics)
        assert bot_agent.metrics.operations_total == 0
        assert len(bot_agent.operation_history) == 0
    
    def test_bot_initialization_without_token(self, monkeypatch):
        """Test bot initialization without GitHub token."""
        monkeypatch.delenv("BOT_GITHUB_TOKEN", raising=False)
        bot = BotAgent(agent_id="test-bot")
        assert bot.github_token is None
    
    def test_load_default_config(self, bot_agent):
        """Test loading default configuration."""
        assert "capabilities" in bot_agent.config
        assert "create_issues" in bot_agent.config["capabilities"]
        assert bot_agent.config["rate_limiting"]["pause_threshold"] == 4800
        assert bot_agent.config["behavior"]["retry_attempts"] == 3
    
    def test_load_config_from_file(self, tmp_path, mock_gh_token):
        """Test loading configuration from YAML file."""
        config_file = tmp_path / "test_bot_config.yaml"
        config_file.write_text("""
bot:
  capabilities:
    - create_issues
  rate_limiting:
    pause_threshold: 4000
  behavior:
    retry_attempts: 5
""")
        
        bot = BotAgent(config_file=config_file)
        assert bot.config["rate_limiting"]["pause_threshold"] == 4000
        assert bot.config["behavior"]["retry_attempts"] == 5
    
    @pytest.mark.asyncio
    async def test_create_issue_success(self, bot_agent, mock_subprocess_success):
        """Test successful issue creation."""
        with patch("subprocess.run", return_value=mock_subprocess_success):
            result = await bot_agent.create_issue(
                repo="owner/repo",
                title="Test Issue",
                body="Test body",
                labels=["bug"],
                assignees=["developer1"]
            )
        
        assert result["number"] == 42
        assert result["url"] == "https://github.com/test/repo/issues/42"
        assert bot_agent.metrics.operations_total == 1
        assert bot_agent.metrics.issues_created == 1
        assert len(bot_agent.operation_history) == 1
    
    @pytest.mark.asyncio
    async def test_create_issue_with_milestone(self, bot_agent, mock_subprocess_success):
        """Test issue creation with milestone."""
        with patch("subprocess.run", return_value=mock_subprocess_success):
            result = await bot_agent.create_issue(
                repo="owner/repo",
                title="Test Issue",
                body="Test body",
                milestone=1
            )
        
        assert result["number"] == 42
        assert bot_agent.metrics.issues_created == 1
    
    @pytest.mark.asyncio
    async def test_add_comment_success(self, bot_agent, mock_subprocess_success):
        """Test successful comment addition."""
        mock_subprocess_success.stdout = "{}"
        
        with patch("subprocess.run", return_value=mock_subprocess_success):
            result = await bot_agent.add_comment(
                repo="owner/repo",
                issue_number=42,
                body="Test comment"
            )
        
        assert bot_agent.metrics.comments_added == 1
        assert bot_agent.metrics.operations_total == 1
    
    @pytest.mark.asyncio
    async def test_assign_issue_success(self, bot_agent, mock_subprocess_success):
        """Test successful issue assignment."""
        mock_subprocess_success.stdout = "{}"
        
        with patch("subprocess.run", return_value=mock_subprocess_success):
            result = await bot_agent.assign_issue(
                repo="owner/repo",
                issue_number=42,
                assignees=["developer1", "developer2"]
            )
        
        assert bot_agent.metrics.assignments_made == 1
        assert bot_agent.metrics.operations_total == 1
    
    @pytest.mark.asyncio
    async def test_update_labels_add(self, bot_agent, mock_subprocess_success):
        """Test adding labels to issue."""
        mock_subprocess_success.stdout = "{}"
        
        with patch("subprocess.run", return_value=mock_subprocess_success):
            result = await bot_agent.update_labels(
                repo="owner/repo",
                issue_number=42,
                add_labels=["enhancement", "high-priority"]
            )
        
        assert bot_agent.metrics.labels_updated == 1
    
    @pytest.mark.asyncio
    async def test_update_labels_remove(self, bot_agent, mock_subprocess_success):
        """Test removing labels from issue."""
        mock_subprocess_success.stdout = "{}"
        
        with patch("subprocess.run", return_value=mock_subprocess_success):
            result = await bot_agent.update_labels(
                repo="owner/repo",
                issue_number=42,
                remove_labels=["wip"]
            )
        
        assert bot_agent.metrics.labels_updated == 1
    
    @pytest.mark.asyncio
    async def test_update_labels_add_and_remove(self, bot_agent, mock_subprocess_success):
        """Test adding and removing labels simultaneously."""
        mock_subprocess_success.stdout = "{}"
        
        with patch("subprocess.run", return_value=mock_subprocess_success):
            result = await bot_agent.update_labels(
                repo="owner/repo",
                issue_number=42,
                add_labels=["in-progress"],
                remove_labels=["pending"]
            )
        
        assert bot_agent.metrics.labels_updated == 1
    
    @pytest.mark.asyncio
    async def test_close_issue_success(self, bot_agent, mock_subprocess_success):
        """Test successful issue closing."""
        mock_subprocess_success.stdout = "{}"
        
        with patch("subprocess.run", return_value=mock_subprocess_success):
            result = await bot_agent.close_issue(
                repo="owner/repo",
                issue_number=42,
                state_reason="completed"
            )
        
        assert bot_agent.metrics.issues_closed == 1
        assert bot_agent.metrics.operations_total == 1
    
    @pytest.mark.asyncio
    async def test_close_issue_with_comment(self, bot_agent, mock_subprocess_success):
        """Test closing issue with comment."""
        mock_subprocess_success.stdout = "{}"
        
        with patch("subprocess.run", return_value=mock_subprocess_success):
            result = await bot_agent.close_issue(
                repo="owner/repo",
                issue_number=42,
                state_reason="completed",
                comment="✅ All tasks completed"
            )
        
        # Should have 2 operations: comment + close
        assert bot_agent.metrics.operations_total == 2
        assert bot_agent.metrics.comments_added == 1
        assert bot_agent.metrics.issues_closed == 1
    
    @pytest.mark.asyncio
    async def test_reopen_issue_success(self, bot_agent, mock_subprocess_success):
        """Test reopening closed issue."""
        mock_subprocess_success.stdout = "{}"
        
        with patch("subprocess.run", return_value=mock_subprocess_success):
            result = await bot_agent.reopen_issue(
                repo="owner/repo",
                issue_number=42
            )
        
        assert bot_agent.metrics.operations_total == 1
    
    @pytest.mark.asyncio
    async def test_operation_retry_on_failure(self, bot_agent):
        """Test retry logic on failed operations."""
        # Mock: fail twice, then succeed
        call_count = 0
        
        def mock_run(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            
            result = Mock()
            if call_count < 3:
                result.returncode = 1
                result.stderr = "Temporary error"
                result.stdout = ""
            else:
                result.returncode = 0
                result.stdout = json.dumps({"number": 42})
                result.stderr = ""
            return result
        
        with patch("subprocess.run", side_effect=mock_run):
            result = await bot_agent.create_issue(
                repo="owner/repo",
                title="Test",
                body="Test"
            )
        
        assert call_count == 3  # Failed twice, succeeded on third try
        assert result["number"] == 42
        assert bot_agent.metrics.success_count == 1
    
    @pytest.mark.asyncio
    async def test_operation_fails_after_max_retries(self, bot_agent, mock_subprocess_failure):
        """Test operation failure after exhausting retries."""
        with patch("subprocess.run", return_value=mock_subprocess_failure):
            with pytest.raises(RuntimeError, match="GitHub operation failed"):
                await bot_agent.create_issue(
                    repo="owner/repo",
                    title="Test",
                    body="Test"
                )
        
        assert bot_agent.metrics.failure_count == 1
        assert bot_agent.metrics.operations_total == 1
    
    @pytest.mark.asyncio
    async def test_rate_limit_check(self, bot_agent):
        """Test rate limit checking."""
        rate_limit_response = {
            "resources": {
                "core": {
                    "remaining": 4500,
                    "reset": int((datetime.now() + timedelta(hours=1)).timestamp())
                }
            }
        }
        
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps(rate_limit_response)
        
        with patch("subprocess.run", return_value=mock_result):
            await bot_agent._check_rate_limit()
        
        assert bot_agent.metrics.rate_limit_remaining == 4500
        assert bot_agent.metrics.rate_limit_reset is not None
    
    @pytest.mark.asyncio
    async def test_rate_limit_pause(self, bot_agent):
        """Test pausing when rate limit is low."""
        # Set very low rate limit
        rate_limit_response = {
            "resources": {
                "core": {
                    "remaining": 10,  # Below threshold of 4800
                    "reset": int((datetime.now() + timedelta(seconds=2)).timestamp())
                }
            }
        }
        
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps(rate_limit_response)
        
        start_time = datetime.now()
        
        with patch("subprocess.run", return_value=mock_result):
            await bot_agent._check_rate_limit()
        
        elapsed = (datetime.now() - start_time).total_seconds()
        
        # Should have paused for ~2 seconds
        assert elapsed >= 1.5  # Allow some margin
    
    def test_record_operation(self, bot_agent):
        """Test operation recording."""
        bot_agent._record_operation(
            operation_type="create_issue",
            repo="owner/repo",
            target_id=42,
            success=True,
            response_time=1.5
        )
        
        assert bot_agent.metrics.operations_total == 1
        assert bot_agent.metrics.issues_created == 1
        assert bot_agent.metrics.success_count == 1
        assert bot_agent.metrics.total_response_time == 1.5
        assert len(bot_agent.operation_history) == 1
    
    def test_operation_history_limit(self, bot_agent):
        """Test operation history size limit."""
        # Add 150 operations (max is 100)
        for i in range(150):
            bot_agent._record_operation(
                operation_type="test",
                repo="owner/repo",
                target_id=i,
                success=True
            )
        
        assert len(bot_agent.operation_history) == 100
        # Should keep the most recent 100
        assert bot_agent.operation_history[-1].target_id == 149
    
    def test_get_metrics(self, bot_agent):
        """Test getting bot metrics."""
        bot_agent._record_operation("create_issue", "owner/repo", 1, True)
        bot_agent._record_operation("add_comment", "owner/repo", 1, True)
        
        metrics = bot_agent.get_metrics()
        
        assert metrics.operations_total == 2
        assert metrics.issues_created == 1
        assert metrics.comments_added == 1
        assert metrics.success_count == 2
    
    def test_get_recent_operations(self, bot_agent):
        """Test getting recent operations."""
        for i in range(20):
            bot_agent._record_operation("test", "owner/repo", i, True)
        
        recent = bot_agent.get_recent_operations(limit=5)
        
        assert len(recent) == 5
        assert recent[-1].target_id == 19  # Most recent
    
    def test_success_rate_calculation(self, bot_agent):
        """Test success rate calculation."""
        # 7 successes, 3 failures = 70% success rate
        for i in range(7):
            bot_agent._record_operation("test", "owner/repo", i, True)
        for i in range(3):
            bot_agent._record_operation("test", "owner/repo", i, False)
        
        success_rate = bot_agent.get_success_rate()
        
        assert success_rate == 70.0
    
    def test_success_rate_with_no_operations(self, bot_agent):
        """Test success rate with no operations."""
        success_rate = bot_agent.get_success_rate()
        assert success_rate == 100.0
    
    def test_average_response_time(self, bot_agent):
        """Test average response time calculation."""
        bot_agent._record_operation("test", "owner/repo", 1, True, response_time=1.0)
        bot_agent._record_operation("test", "owner/repo", 2, True, response_time=2.0)
        bot_agent._record_operation("test", "owner/repo", 3, True, response_time=3.0)
        
        avg_time = bot_agent.get_average_response_time()
        
        assert avg_time == 2.0  # (1.0 + 2.0 + 3.0) / 3
    
    def test_format_status(self, bot_agent):
        """Test status formatting for dashboard."""
        bot_agent._record_operation("create_issue", "owner/repo", 1, True)
        bot_agent._record_operation("add_comment", "owner/repo", 1, True)
        bot_agent.metrics.rate_limit_remaining = 4500
        
        status = bot_agent.format_status()
        
        assert "🤖" in status
        assert "test-bot" in status
        assert "BOT" in status
        assert "Operations: 2" in status
        assert "Success Rate: 100.0%" in status
        assert "Rate Limit: 4,500" in status
    
    def test_operations_by_type_tracking(self, bot_agent):
        """Test tracking operations by type."""
        bot_agent._record_operation("create_issue", "owner/repo", 1, True)
        bot_agent._record_operation("create_issue", "owner/repo", 2, True)
        bot_agent._record_operation("add_comment", "owner/repo", 1, True)
        bot_agent._record_operation("close_issue", "owner/repo", 1, True)
        
        assert bot_agent.metrics.operations_by_type["create_issue"] == 2
        assert bot_agent.metrics.operations_by_type["add_comment"] == 1
        assert bot_agent.metrics.operations_by_type["close_issue"] == 1


class TestBotOperation:
    """Test BotOperation dataclass."""
    
    def test_bot_operation_creation(self):
        """Test creating BotOperation."""
        op = BotOperation(
            operation_type="create_issue",
            timestamp=datetime.now(),
            repo="owner/repo",
            target_id=42,
            success=True,
            response_time=1.5
        )
        
        assert op.operation_type == "create_issue"
        assert op.repo == "owner/repo"
        assert op.target_id == 42
        assert op.success is True
        assert op.response_time == 1.5
    
    def test_bot_operation_defaults(self):
        """Test BotOperation default values."""
        op = BotOperation(
            operation_type="test",
            timestamp=datetime.now(),
            repo="owner/repo"
        )
        
        assert op.target_id is None
        assert op.success is True
        assert op.error is None
        assert op.response_time == 0.0


class TestBotMetrics:
    """Test BotMetrics dataclass."""
    
    def test_bot_metrics_creation(self):
        """Test creating BotMetrics."""
        metrics = BotMetrics()
        
        assert metrics.operations_total == 0
        assert metrics.issues_created == 0
        assert metrics.success_count == 0
        assert metrics.failure_count == 0
        assert metrics.rate_limit_remaining == 5000
        assert isinstance(metrics.operations_by_type, dict)
    
    def test_bot_metrics_update(self):
        """Test updating bot metrics."""
        metrics = BotMetrics()
        
        metrics.operations_total += 1
        metrics.issues_created += 1
        metrics.success_count += 1
        metrics.operations_by_type["create_issue"] = 1
        
        assert metrics.operations_total == 1
        assert metrics.issues_created == 1
        assert metrics.success_count == 1
        assert metrics.operations_by_type["create_issue"] == 1


# Integration test scenarios
class TestBotAgentIntegration:
    """Test bot agent integration scenarios."""
    
    @pytest.mark.asyncio
    async def test_workflow_create_and_close_issue(self, bot_agent, mock_subprocess_success):
        """Test complete workflow: create issue, comment, close."""
        mock_subprocess_success.stdout = json.dumps({"number": 42})
        
        with patch("subprocess.run", return_value=mock_subprocess_success):
            # Create issue
            issue = await bot_agent.create_issue(
                repo="owner/repo",
                title="New feature",
                body="Description"
            )
            
            # Add comment
            await bot_agent.add_comment(
                repo="owner/repo",
                issue_number=issue["number"],
                body="Work started"
            )
            
            # Close issue
            await bot_agent.close_issue(
                repo="owner/repo",
                issue_number=issue["number"],
                comment="✅ Completed"
            )
        
        # Verify metrics
        assert bot_agent.metrics.operations_total == 4  # create + comment + comment (close) + close
        assert bot_agent.metrics.issues_created == 1
        assert bot_agent.metrics.comments_added == 2
        assert bot_agent.metrics.issues_closed == 1
    
    @pytest.mark.asyncio
    async def test_workflow_with_labels_and_assignment(self, bot_agent, mock_subprocess_success):
        """Test workflow with labels and assignments."""
        mock_subprocess_success.stdout = json.dumps({"number": 42})
        
        with patch("subprocess.run", return_value=mock_subprocess_success):
            # Create issue with labels
            issue = await bot_agent.create_issue(
                repo="owner/repo",
                title="Bug fix",
                body="Fix the bug",
                labels=["bug"]
            )
            
            # Assign to developer
            await bot_agent.assign_issue(
                repo="owner/repo",
                issue_number=issue["number"],
                assignees=["developer1"]
            )
            
            # Update labels
            await bot_agent.update_labels(
                repo="owner/repo",
                issue_number=issue["number"],
                add_labels=["in-progress"],
                remove_labels=["bug"]
            )
        
        assert bot_agent.metrics.operations_total == 3
        assert bot_agent.metrics.assignments_made == 1
        assert bot_agent.metrics.labels_updated == 1
