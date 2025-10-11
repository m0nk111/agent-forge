"""Tests for review lock mechanism to prevent concurrent reviews."""

import os
import tempfile
import time
from pathlib import Path

import pytest

from engine.utils.review_lock import ReviewLock


class TestReviewLock:
    """Test review lock mechanism."""
    
    def test_acquire_lock_success(self):
        """Test successful lock acquisition."""
        with tempfile.TemporaryDirectory() as tmpdir:
            lock = ReviewLock(lock_dir=tmpdir)
            
            # Should acquire successfully
            assert lock.acquire("owner/repo", 123, "test-agent")
            
            # Clean up
            lock.release("owner/repo", 123)
    
    def test_acquire_lock_blocked(self):
        """Test lock acquisition when already held."""
        with tempfile.TemporaryDirectory() as tmpdir:
            lock1 = ReviewLock(lock_dir=tmpdir)
            lock2 = ReviewLock(lock_dir=tmpdir)
            
            # First acquisition should succeed
            assert lock1.acquire("owner/repo", 123, "agent1")
            
            # Second acquisition should fail (locked by agent1)
            assert not lock2.acquire("owner/repo", 123, "agent2")
            
            # Clean up
            lock1.release("owner/repo", 123)
    
    def test_release_lock(self):
        """Test lock release allows re-acquisition."""
        with tempfile.TemporaryDirectory() as tmpdir:
            lock1 = ReviewLock(lock_dir=tmpdir)
            lock2 = ReviewLock(lock_dir=tmpdir)
            
            # Acquire and release
            assert lock1.acquire("owner/repo", 123, "agent1")
            lock1.release("owner/repo", 123)
            
            # Should be able to acquire again
            assert lock2.acquire("owner/repo", 123, "agent2")
            
            # Clean up
            lock2.release("owner/repo", 123)
    
    def test_stale_lock_cleanup(self):
        """Test automatic cleanup of stale locks."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create lock with very short timeout
            lock = ReviewLock(lock_dir=tmpdir, lock_timeout=1)
            
            # Acquire lock
            assert lock.acquire("owner/repo", 123, "agent1")
            
            # Wait for timeout
            time.sleep(2)
            
            # New lock manager should clean up and acquire
            lock2 = ReviewLock(lock_dir=tmpdir, lock_timeout=1)
            assert lock2.acquire("owner/repo", 123, "agent2")
            
            # Clean up
            lock2.release("owner/repo", 123)
    
    def test_lock_refresh(self):
        """Test lock refresh prevents expiration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            lock = ReviewLock(lock_dir=tmpdir, lock_timeout=2)
            
            # Acquire lock
            assert lock.acquire("owner/repo", 123, "agent1")
            
            # Wait half timeout
            time.sleep(1)
            
            # Refresh
            lock.refresh("owner/repo", 123)
            
            # Wait another second (would have expired without refresh)
            time.sleep(1)
            
            # Another agent should still not be able to acquire
            lock2 = ReviewLock(lock_dir=tmpdir, lock_timeout=2)
            assert not lock2.acquire("owner/repo", 123, "agent2")
            
            # Clean up
            lock.release("owner/repo", 123)
    
    def test_context_manager(self):
        """Test context manager auto-release."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Use context manager
            with ReviewLock(lock_dir=tmpdir) as lock:
                assert lock.acquire("owner/repo", 123, "agent1")
            
            # Lock should be released after context
            lock2 = ReviewLock(lock_dir=tmpdir)
            assert lock2.acquire("owner/repo", 123, "agent2")
            lock2.release("owner/repo", 123)
    
    def test_multiple_repos_independent(self):
        """Test locks for different repos are independent."""
        with tempfile.TemporaryDirectory() as tmpdir:
            lock = ReviewLock(lock_dir=tmpdir)
            
            # Should be able to lock different repos
            assert lock.acquire("owner/repo1", 123, "agent1")
            assert lock.acquire("owner/repo2", 123, "agent1")
            
            # Clean up
            lock.release("owner/repo1", 123)
            lock.release("owner/repo2", 123)
    
    def test_multiple_prs_independent(self):
        """Test locks for different PRs are independent."""
        with tempfile.TemporaryDirectory() as tmpdir:
            lock = ReviewLock(lock_dir=tmpdir)
            
            # Should be able to lock different PRs
            assert lock.acquire("owner/repo", 123, "agent1")
            assert lock.acquire("owner/repo", 456, "agent1")
            
            # Clean up
            lock.release("owner/repo", 123)
            lock.release("owner/repo", 456)
    
    def test_cleanup_multiple_stale_locks(self):
        """Test cleanup of multiple stale locks."""
        with tempfile.TemporaryDirectory() as tmpdir:
            lock = ReviewLock(lock_dir=tmpdir, lock_timeout=1)
            
            # Create multiple locks
            assert lock.acquire("owner/repo", 1, "agent1")
            assert lock.acquire("owner/repo", 2, "agent1")
            assert lock.acquire("owner/repo", 3, "agent1")
            
            # Wait for timeout
            time.sleep(2)
            
            # Cleanup should remove all stale locks
            lock.cleanup_stale_locks()
            
            # Should be able to acquire all again
            assert lock.acquire("owner/repo", 1, "agent2")
            assert lock.acquire("owner/repo", 2, "agent2")
            assert lock.acquire("owner/repo", 3, "agent2")
            
            # Clean up
            lock.release("owner/repo", 1)
            lock.release("owner/repo", 2)
            lock.release("owner/repo", 3)
    
    def test_lock_file_naming(self):
        """Test lock file naming convention."""
        with tempfile.TemporaryDirectory() as tmpdir:
            lock = ReviewLock(lock_dir=tmpdir)
            lock.acquire("owner/repo", 123, "agent1")
            
            # Check lock file exists with correct name
            lock_file = Path(tmpdir) / "owner_repo_pr123.lock"
            assert lock_file.exists()
            
            # Check lock file content
            content = lock_file.read_text()
            assert "agent1" in content
            
            # Clean up
            lock.release("owner/repo", 123)
            
            # Lock file should be removed
            assert not lock_file.exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
