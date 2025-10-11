"""Unit tests for refactored polling service modules."""

import os
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from engine.runners.polling_models import PollingConfig, IssueState
from engine.runners.config_override_handler import ConfigOverrideHandler
from engine.runners.state_manager import StateManager
from engine.runners.issue_filter import IssueFilter


class TestPollingModels:
    """Test polling data models."""
    
    def test_polling_config_defaults(self):
        """Test PollingConfig default values."""
        config = PollingConfig()
        assert config.interval_seconds == 300
        assert config.max_concurrent_issues == 3
        assert config.claim_timeout_minutes == 60
        assert config.watch_labels == ["agent-ready", "auto-assign"]
    
    def test_polling_config_post_init(self, monkeypatch):
        """Test PollingConfig __post_init__ loads token from env."""
        # Clear existing env vars first
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        monkeypatch.delenv("BOT_GITHUB_TOKEN", raising=False)
        
        monkeypatch.setenv("GITHUB_TOKEN", "test_token_123")
        config = PollingConfig()
        assert config.github_token == "test_token_123"
    
    def test_issue_state_creation(self):
        """Test IssueState creation."""
        state = IssueState(
            issue_number=42,
            repository="owner/repo",
            claimed_by="bot",
            claimed_at="2025-10-11T12:00:00Z"
        )
        assert state.issue_number == 42
        assert state.repository == "owner/repo"
        assert state.completed is False
        assert state.error_count == 0


class TestConfigOverrideHandler:
    """Test configuration override logic."""
    
    def test_no_override_for_defaults(self):
        """Test that default values are not applied as overrides."""
        base = PollingConfig(interval_seconds=600, github_username="user1")
        override = PollingConfig()  # All defaults
        
        handler = ConfigOverrideHandler(base)
        handler.apply_overrides(override)
        
        # Base values should not be changed by defaults
        assert base.interval_seconds == 600
        assert base.github_username == "user1"
    
    def test_explicit_override_applied(self):
        """Test that explicit non-default values are applied."""
        base = PollingConfig(interval_seconds=600)
        override = PollingConfig(interval_seconds=120, github_username="bot")
        
        handler = ConfigOverrideHandler(base)
        handler.apply_overrides(override)
        
        assert base.interval_seconds == 120
        assert base.github_username == "bot"
    
    def test_env_token_not_overridden(self, monkeypatch):
        """Test that env-derived token doesn't override YAML token."""
        monkeypatch.setenv("GITHUB_TOKEN", "env_token")
        
        base = PollingConfig(github_token="yaml_token")
        override = PollingConfig()  # Will get env_token from __post_init__
        
        handler = ConfigOverrideHandler(base)
        handler.apply_overrides(override)
        
        # YAML token should be preserved
        assert base.github_token == "yaml_token"


class TestStateManager:
    """Test state persistence manager."""
    
    def test_load_empty_state(self):
        """Test loading when no state file exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = Path(tmpdir) / "state.json"
            manager = StateManager(state_file)
            manager.load()
            
            assert len(manager.state) == 0
    
    def test_save_and_load_state(self):
        """Test saving and loading state."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = Path(tmpdir) / "state.json"
            manager = StateManager(state_file)
            
            # Add state
            state = IssueState(
                issue_number=42,
                repository="owner/repo",
                claimed_by="bot",
                claimed_at="2025-10-11T12:00:00Z"
            )
            manager.set("owner/repo#42", state)
            manager.save()
            
            # Load in new manager
            manager2 = StateManager(state_file)
            manager2.load()
            
            assert len(manager2.state) == 1
            loaded = manager2.get("owner/repo#42")
            assert loaded is not None
            assert loaded.issue_number == 42
            assert loaded.claimed_by == "bot"
    
    def test_cleanup_old_entries(self):
        """Test cleanup of old completed issues."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = Path(tmpdir) / "state.json"
            manager = StateManager(state_file)
            
            # Add old completed issue
            old_time = (datetime.now(timezone.utc) - timedelta(days=10)).isoformat()
            old_state = IssueState(
                issue_number=1,
                repository="owner/repo",
                claimed_by="bot",
                claimed_at=old_time,
                completed=True,
                completed_at=old_time
            )
            manager.set("owner/repo#1", old_state)
            
            # Add recent completed issue
            recent_time = (datetime.now(timezone.utc) - timedelta(days=3)).isoformat()
            recent_state = IssueState(
                issue_number=2,
                repository="owner/repo",
                claimed_by="bot",
                claimed_at=recent_time,
                completed=True,
                completed_at=recent_time
            )
            manager.set("owner/repo#2", recent_state)
            
            # Cleanup
            manager.cleanup_old_entries(days=7)
            
            # Old should be removed, recent should remain
            assert not manager.has("owner/repo#1")
            assert manager.has("owner/repo#2")


class TestIssueFilter:
    """Test issue filtering logic."""
    
    def test_filter_by_watch_labels(self):
        """Test filtering issues by watch labels."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = Path(tmpdir) / "state.json"
            state_manager = StateManager(state_file)
            
            filter = IssueFilter(
                state_manager=state_manager,
                watch_labels=["agent-ready", "auto-assign"],
                claim_timeout_minutes=60
            )
            
            issues = [
                {
                    "number": 1,
                    "repository": "owner/repo",
                    "title": "Issue 1",
                    "labels": [{"name": "agent-ready"}]
                },
                {
                    "number": 2,
                    "repository": "owner/repo",
                    "title": "Issue 2",
                    "labels": [{"name": "bug"}]
                },
                {
                    "number": 3,
                    "repository": "owner/repo",
                    "title": "Issue 3",
                    "labels": [{"name": "auto-assign"}]
                }
            ]
            
            actionable = filter.filter_actionable_issues(issues)
            
            assert len(actionable) == 2
            assert actionable[0]["number"] == 1
            assert actionable[1]["number"] == 3
    
    def test_skip_completed_issues(self):
        """Test that completed issues are skipped."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = Path(tmpdir) / "state.json"
            state_manager = StateManager(state_file)
            
            # Mark issue as completed
            completed_state = IssueState(
                issue_number=1,
                repository="owner/repo",
                claimed_by="bot",
                claimed_at="2025-10-11T12:00:00Z",
                completed=True,
                completed_at="2025-10-11T13:00:00Z"
            )
            state_manager.set("owner/repo#1", completed_state)
            
            filter = IssueFilter(
                state_manager=state_manager,
                watch_labels=["agent-ready"],
                claim_timeout_minutes=60
            )
            
            issues = [
                {
                    "number": 1,
                    "repository": "owner/repo",
                    "title": "Completed Issue",
                    "labels": [{"name": "agent-ready"}]
                }
            ]
            
            actionable = filter.filter_actionable_issues(issues)
            
            assert len(actionable) == 0
    
    def test_skip_claimed_issues(self):
        """Test that issues with valid claims are skipped."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = Path(tmpdir) / "state.json"
            state_manager = StateManager(state_file)
            
            # Add recent claim
            now = datetime.now(timezone.utc)
            claimed_state = IssueState(
                issue_number=1,
                repository="owner/repo",
                claimed_by="bot",
                claimed_at=now.isoformat()
            )
            state_manager.set("owner/repo#1", claimed_state)
            
            filter = IssueFilter(
                state_manager=state_manager,
                watch_labels=["agent-ready"],
                claim_timeout_minutes=60
            )
            
            issues = [
                {
                    "number": 1,
                    "repository": "owner/repo",
                    "title": "Claimed Issue",
                    "labels": [{"name": "agent-ready"}]
                }
            ]
            
            actionable = filter.filter_actionable_issues(issues)
            
            assert len(actionable) == 0
    
    def test_allow_expired_claims(self):
        """Test that issues with expired claims are allowed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = Path(tmpdir) / "state.json"
            state_manager = StateManager(state_file)
            
            # Add old claim (expired)
            old_time = datetime.now(timezone.utc) - timedelta(minutes=120)
            claimed_state = IssueState(
                issue_number=1,
                repository="owner/repo",
                claimed_by="bot",
                claimed_at=old_time.isoformat()
            )
            state_manager.set("owner/repo#1", claimed_state)
            
            filter = IssueFilter(
                state_manager=state_manager,
                watch_labels=["agent-ready"],
                claim_timeout_minutes=60  # 1 hour timeout
            )
            
            issues = [
                {
                    "number": 1,
                    "repository": "owner/repo",
                    "title": "Expired Claim Issue",
                    "labels": [{"name": "agent-ready"}]
                }
            ]
            
            actionable = filter.filter_actionable_issues(issues)
            
            # Should be actionable since claim expired
            assert len(actionable) == 1
