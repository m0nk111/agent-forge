"""Tests for autonomous polling service."""

import asyncio
import json
import pytest
from pathlib import Path
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch, AsyncMock

from engine.runners.polling_service import (
    PollingService,
    PollingConfig,
    IssueState
)


def _utc_iso(delta: timedelta = timedelta(0)) -> str:
    """Return ISO string in UTC with Z suffix, optionally offset by delta."""
    return (datetime.now(timezone.utc) + delta).isoformat().replace("+00:00", "Z")


@pytest.fixture
def temp_state_file(tmp_path):
    """Create temporary state file."""
    return str(tmp_path / "test_polling_state.json")


@pytest.fixture
def test_config(temp_state_file):
    """Create test configuration."""
    return PollingConfig(
        interval_seconds=10,
        github_username="test-bot",
        repositories=["owner/repo1", "owner/repo2"],
        watch_labels=["agent-ready", "test-label"],
        max_concurrent_issues=2,
        state_file=temp_state_file
    )


@pytest.fixture
def polling_service(test_config):
    """Create polling service instance."""
    return PollingService(test_config)


class TestPollingConfig:
    """Test polling configuration."""
    
    def test_default_values(self):
        """Test default configuration values."""
        config = PollingConfig()
        assert config.interval_seconds == 300
        assert config.github_username == "m0nk111-post"  # Updated: m0nk111-bot suspended
        assert config.max_concurrent_issues == 3
        assert config.claim_timeout_minutes == 60
        assert "agent-ready" in config.watch_labels
        assert "auto-assign" in config.watch_labels
    
    def test_custom_values(self):
        """Test custom configuration."""
        config = PollingConfig(
            interval_seconds=60,
            repositories=["test/repo"],
            watch_labels=["custom-label"],
            max_concurrent_issues=5
        )
        assert config.interval_seconds == 60
        assert config.repositories == ["test/repo"]
        assert config.watch_labels == ["custom-label"]
        assert config.max_concurrent_issues == 5
    
    def test_github_token_from_env(self, monkeypatch):
        """Test GitHub token loading from environment."""
        monkeypatch.setenv("BOT_GITHUB_TOKEN", "test-token-123")
        config = PollingConfig()
        assert config.github_token == "test-token-123"


class TestIssueState:
    """Test issue state tracking."""
    
    def test_issue_state_creation(self):
        """Test creating issue state."""
        state = IssueState(
            issue_number=123,
            repository="owner/repo",
            claimed_by="test-bot",
            claimed_at="2025-01-01T00:00:00"
        )
        assert state.issue_number == 123
        assert state.repository == "owner/repo"
        assert state.claimed_by == "test-bot"
        assert state.error_count == 0
        assert not state.completed
    
    def test_issue_state_with_errors(self):
        """Test issue state with error tracking."""
        state = IssueState(
            issue_number=456,
            repository="owner/repo",
            claimed_by="test-bot",
            claimed_at="2025-01-01T00:00:00",
            last_error="Test error",
            error_count=3
        )
        assert state.last_error == "Test error"
        assert state.error_count == 3


class TestPollingService:
    """Test polling service functionality."""
    
    def test_service_initialization(self, polling_service, test_config):
        """Test service initialization."""
        assert polling_service.config == test_config
        assert isinstance(polling_service.state, dict)
        assert not polling_service.running
    
    def test_get_issue_key(self, polling_service):
        """Test issue key generation."""
        key = polling_service.get_issue_key("owner/repo", 123)
        assert key == "owner/repo#123"
    
    def test_state_persistence(self, polling_service, temp_state_file):
        """Test state save and load."""
        # Add state
        polling_service.state["owner/repo#1"] = IssueState(
            issue_number=1,
            repository="owner/repo",
            claimed_by="test-bot",
            claimed_at="2025-01-01T00:00:00"
        )
        
        # Save
        polling_service.save_state()
        assert Path(temp_state_file).exists()
        
        # Create new service and load
        new_service = PollingService(polling_service.config)
        assert "owner/repo#1" in new_service.state
        assert new_service.state["owner/repo#1"].issue_number == 1
    
    def test_cleanup_old_state(self, polling_service):
        """Test cleanup of old completed issues."""
        # Add old completed issue
        old_time = _utc_iso(-timedelta(days=10))
        polling_service.state["owner/repo#1"] = IssueState(
            issue_number=1,
            repository="owner/repo",
            claimed_by="test-bot",
            claimed_at=old_time,
            completed=True,
            completed_at=old_time
        )
        
        # Add recent completed issue
        recent_time = _utc_iso()
        polling_service.state["owner/repo#2"] = IssueState(
            issue_number=2,
            repository="owner/repo",
            claimed_by="test-bot",
            claimed_at=recent_time,
            completed=True,
            completed_at=recent_time
        )
        
        # Cleanup
        polling_service.cleanup_old_state()
        
        # Old issue should be removed, recent kept
        assert "owner/repo#1" not in polling_service.state
        assert "owner/repo#2" in polling_service.state
    
    def test_filter_actionable_issues(self, polling_service):
        """Test filtering actionable issues."""
        issues = [
            {
                'number': 1,
                'repository': 'owner/repo',
                'title': 'Issue 1',
                'labels': [{'name': 'agent-ready'}]
            },
            {
                'number': 2,
                'repository': 'owner/repo',
                'title': 'Issue 2',
                'labels': [{'name': 'bug'}]  # No watch label
            },
            {
                'number': 3,
                'repository': 'owner/repo',
                'title': 'Issue 3',
                'labels': [{'name': 'test-label'}]
            }
        ]
        
        actionable = polling_service.filter_actionable_issues(issues)
        assert len(actionable) == 2
        assert actionable[0]['number'] == 1
        assert actionable[1]['number'] == 3
    
    def test_filter_skips_processing(self, polling_service):
        """Test filtering skips already processing issues."""
        # Mark issue as processing
        polling_service.state["owner/repo#1"] = IssueState(
            issue_number=1,
            repository="owner/repo",
            claimed_by="test-bot",
            claimed_at=_utc_iso(),
            completed=False
        )
        
        issues = [
            {
                'number': 1,
                'repository': 'owner/repo',
                'title': 'Issue 1',
                'labels': [{'name': 'agent-ready'}]
            }
        ]
        
        actionable = polling_service.filter_actionable_issues(issues)
        assert len(actionable) == 0
    
    def test_filter_skips_completed(self, polling_service):
        """Test filtering skips completed issues."""
        # Mark issue as completed
        polling_service.state["owner/repo#1"] = IssueState(
            issue_number=1,
            repository="owner/repo",
            claimed_by="test-bot",
            claimed_at=_utc_iso(),
            completed=True,
            completed_at=_utc_iso()
        )
        
        issues = [
            {
                'number': 1,
                'repository': 'owner/repo',
                'title': 'Issue 1',
                'labels': [{'name': 'agent-ready'}]
            }
        ]
        
        actionable = polling_service.filter_actionable_issues(issues)
        assert len(actionable) == 0
    
    def test_get_processing_count(self, polling_service):
        """Test counting processing issues."""
        # Add processing issues
        polling_service.state["owner/repo#1"] = IssueState(
            issue_number=1,
            repository="owner/repo",
            claimed_by="test-bot",
            claimed_at=_utc_iso(),
            completed=False
        )
        polling_service.state["owner/repo#2"] = IssueState(
            issue_number=2,
            repository="owner/repo",
            claimed_by="test-bot",
            claimed_at=_utc_iso(),
            completed=False
        )
        
        # Add completed issue
        polling_service.state["owner/repo#3"] = IssueState(
            issue_number=3,
            repository="owner/repo",
            claimed_by="test-bot",
            claimed_at=_utc_iso(),
            completed=True,
            completed_at=_utc_iso()
        )
        
        count = polling_service.get_processing_count()
        assert count == 2
    
    @pytest.mark.asyncio
    async def test_claim_issue_success(self, polling_service):
        """Test successful issue claiming."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout='', stderr='')
            
            result = await polling_service.claim_issue("owner/repo", 123)
            assert result is True
            mock_run.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_claim_issue_failure(self, polling_service):
        """Test failed issue claiming."""
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = Exception("API error")
            
            result = await polling_service.claim_issue("owner/repo", 123)
            assert result is False
    
    def test_is_issue_claimed_not_claimed(self, polling_service):
        """Test checking unclaimed issue."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(
                returncode=0,
                stdout=json.dumps({'comments': []}),
                stderr=''
            )
            
            result = polling_service.is_issue_claimed("owner/repo", 123)
            assert result is False
    
    def test_is_issue_claimed_recently(self, polling_service):
        """Test checking recently claimed issue."""
        recent_time = _utc_iso()
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(
                returncode=0,
                stdout=json.dumps({
                    'comments': [{
                        'body': '🤖 Agent test-bot started working on this issue',
                        'createdAt': recent_time
                    }]
                }),
                stderr=''
            )
            
            result = polling_service.is_issue_claimed("owner/repo", 123)
            assert result is True
    
    def test_is_issue_claimed_expired(self, polling_service):
        """Test checking issue with expired claim."""
        old_time = _utc_iso(-timedelta(hours=2))
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(
                returncode=0,
                stdout=json.dumps({
                    'comments': [{
                        'body': '🤖 Agent test-bot started working on this issue',
                        'createdAt': old_time
                    }]
                }),
                stderr=''
            )
            
            result = polling_service.is_issue_claimed("owner/repo", 123)
            assert result is False  # Claim expired
    
    @pytest.mark.asyncio
    async def test_check_assigned_issues(self, polling_service):
        """Test checking assigned issues via GitHub API."""
        mock_issues = [
            {'number': 1, 'title': 'Test 1', 'labels': [], 'assignees': []},
            {'number': 2, 'title': 'Test 2', 'labels': [], 'assignees': []}
        ]
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(
                returncode=0,
                stdout=json.dumps(mock_issues),
                stderr=''
            )
            
            issues = await polling_service.check_assigned_issues()
            assert len(issues) == 4  # 2 repos × 2 issues
            assert all('repository' in issue for issue in issues)


@pytest.mark.asyncio
async def test_service_stop(polling_service):
    """Test stopping the service."""
    polling_service.running = True
    polling_service.stop()
    assert not polling_service.running


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
