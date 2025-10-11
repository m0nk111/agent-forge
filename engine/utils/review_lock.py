"""Review lock mechanism to prevent concurrent reviews of same PR.

This module provides file-based locking to prevent race conditions when
multiple processes (polling service + GitHub Actions) try to review the
same PR simultaneously.

Features:
- Atomic lock acquisition using file system
- Automatic lock expiration (prevents deadlocks)
- Lock refresh for long-running operations
- Safe cleanup of stale locks
"""

import fcntl
import logging
import os
import time
from pathlib import Path
from typing import Optional


logger = logging.getLogger(__name__)


class ReviewLock:
    """File-based lock for PR reviews to prevent concurrent access."""
    
    def __init__(self, lock_dir: str = "data/review_locks", lock_timeout: int = 300):
        """Initialize review lock manager.
        
        Args:
            lock_dir: Directory for lock files
            lock_timeout: Lock expiration in seconds (default: 5 minutes)
        """
        self.lock_dir = Path(lock_dir)
        self.lock_timeout = lock_timeout
        self.lock_dir.mkdir(parents=True, exist_ok=True)
        self._active_locks = {}  # {pr_key: file_handle}
    
    def acquire(self, repo: str, pr_number: int, requester: str = "unknown") -> bool:
        """Attempt to acquire lock for PR review.
        
        Args:
            repo: Repository (owner/repo)
            pr_number: PR number
            requester: Identifier of requesting process (for logging)
        
        Returns:
            True if lock acquired, False if already locked by another process
        """
        pr_key = f"{repo}#{pr_number}"
        lock_file = self.lock_dir / f"{repo.replace('/', '_')}_pr{pr_number}.lock"
        
        try:
            # Clean up stale lock if exists
            if lock_file.exists():
                lock_age = time.time() - lock_file.stat().st_mtime
                if lock_age > self.lock_timeout:
                    logger.warning(f"🔓 Removing stale lock for {pr_key} (age: {lock_age:.0f}s)")
                    lock_file.unlink()
            
            # Try to create and lock file atomically
            fd = os.open(str(lock_file), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
            
            # Write lock metadata
            lock_data = f"{requester}|{int(time.time())}\n".encode()
            os.write(fd, lock_data)
            os.fsync(fd)
            
            # Store file descriptor
            self._active_locks[pr_key] = fd
            
            logger.info(f"🔒 Acquired review lock for {pr_key} (requester: {requester})")
            return True
            
        except FileExistsError:
            # Lock already exists (another process has it)
            logger.debug(f"⏭️ Lock already held for {pr_key}, skipping")
            return False
        except Exception as e:
            logger.error(f"❌ Error acquiring lock for {pr_key}: {e}")
            return False
    
    def release(self, repo: str, pr_number: int):
        """Release lock for PR review.
        
        Args:
            repo: Repository (owner/repo)
            pr_number: PR number
        """
        pr_key = f"{repo}#{pr_number}"
        lock_file = self.lock_dir / f"{repo.replace('/', '_')}_pr{pr_number}.lock"
        
        try:
            # Close file descriptor
            if pr_key in self._active_locks:
                os.close(self._active_locks[pr_key])
                del self._active_locks[pr_key]
            
            # Remove lock file
            if lock_file.exists():
                lock_file.unlink()
                logger.info(f"🔓 Released review lock for {pr_key}")
        except Exception as e:
            logger.error(f"❌ Error releasing lock for {pr_key}: {e}")
    
    def refresh(self, repo: str, pr_number: int):
        """Refresh lock to prevent expiration during long operations.
        
        Args:
            repo: Repository (owner/repo)
            pr_number: PR number
        """
        lock_file = self.lock_dir / f"{repo.replace('/', '_')}_pr{pr_number}.lock"
        
        try:
            if lock_file.exists():
                lock_file.touch()
                logger.debug(f"🔄 Refreshed lock for {repo}#{pr_number}")
        except Exception as e:
            logger.error(f"❌ Error refreshing lock: {e}")
    
    def cleanup_stale_locks(self):
        """Clean up all stale locks (expired beyond timeout)."""
        try:
            stale_count = 0
            for lock_file in self.lock_dir.glob("*.lock"):
                lock_age = time.time() - lock_file.stat().st_mtime
                if lock_age > self.lock_timeout:
                    lock_file.unlink()
                    stale_count += 1
                    logger.info(f"�� Removed stale lock: {lock_file.name} (age: {lock_age:.0f}s)")
            
            if stale_count > 0:
                logger.info(f"🧹 Cleaned up {stale_count} stale lock(s)")
        except Exception as e:
            logger.error(f"❌ Error cleaning up stale locks: {e}")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - release all active locks."""
        for pr_key in list(self._active_locks.keys()):
            repo, pr_num_str = pr_key.split('#')
            self.release(repo, int(pr_num_str))
