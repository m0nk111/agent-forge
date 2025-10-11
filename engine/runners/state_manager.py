"""State management for polling service.

Handles persistence of issue tracking state to disk,
including claim tracking and completion status.
"""

import fcntl
import json
import logging
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict

from engine.runners.polling_models import IssueState


logger = logging.getLogger(__name__)


def _utc_now() -> datetime:
    """Return current UTC time as timezone-aware datetime."""
    return datetime.now(timezone.utc)


def _parse_iso_timestamp(value: str) -> datetime:
    """Parse ISO timestamp supporting legacy naive and Zulu formats.
    
    Args:
        value: ISO timestamp string
        
    Returns:
        Timezone-aware datetime object
    """
    normalized = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


class StateManager:
    """Manages polling service state persistence."""
    
    def __init__(self, state_file: Path):
        """Initialize state manager.
        
        Args:
            state_file: Path to state file
        """
        self.state_file = state_file
        self.state: Dict[str, IssueState] = {}
    
    def load(self) -> None:
        """Load polling state from disk with file locking."""
        if not self.state_file.exists():
            logger.info("No existing state file, starting fresh")
            self.state = {}
            return
        
        try:
            with self.state_file.open('r') as f:
                # Acquire shared lock for reading
                fcntl.flock(f.fileno(), fcntl.LOCK_SH)
                try:
                    data = json.load(f)
                    self.state = {
                        key: IssueState(**value)
                        for key, value in data.items()
                    }
                    logger.info(f"Loaded state: {len(self.state)} tracked issues")
                finally:
                    # Release lock
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        except Exception as e:
            logger.error(f"Failed to load state: {e}")
            self.state = {}
    
    def save(self) -> None:
        """Save polling state to disk with file locking and atomic write.
        
        Uses atomic write pattern (write to temp file + rename) to prevent
        corruption if process crashes during write.
        """
        temp_file = None
        try:
            data = {
                key: asdict(value)
                for key, value in self.state.items()
            }
            
            # Write to temporary file first (atomic write pattern)
            temp_file = self.state_file.with_suffix('.tmp')
            with temp_file.open('w') as f:
                # Acquire exclusive lock for writing
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                try:
                    json.dump(data, f, indent=2)
                    f.flush()  # Ensure data is written to disk
                finally:
                    # Release lock
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)
            
            # Atomic rename (replaces old file)
            temp_file.replace(self.state_file)
            logger.debug(f"Saved state: {len(self.state)} tracked issues")
        except Exception as e:
            logger.error(f"Failed to save state: {e}")
            # Clean up temp file if it exists
            if temp_file and temp_file.exists():
                try:
                    temp_file.unlink()
                except Exception:
                    pass
    
    def cleanup_old_entries(self, days: int = 7) -> None:
        """Remove old completed/closed issues from state.
        
        Args:
            days: Number of days after which to remove completed issues
        """
        now = _utc_now()
        cutoff = now - timedelta(days=days)
        
        to_remove = []
        for key, issue_state in self.state.items():
            if not issue_state.completed or not issue_state.completed_at:
                continue
            
            try:
                completed_time = _parse_iso_timestamp(issue_state.completed_at)
                if completed_time < cutoff:
                    to_remove.append(key)
            except Exception as e:
                logger.warning(f"Error parsing completion time for {key}: {e}")
        
        for key in to_remove:
            del self.state[key]
            logger.info(f"Cleaned up old state: {key}")
        
        if to_remove:
            self.save()
    
    def get(self, key: str) -> IssueState | None:
        """Get issue state by key.
        
        Args:
            key: Issue key (repo#number)
            
        Returns:
            IssueState if found, None otherwise
        """
        return self.state.get(key)
    
    def set(self, key: str, state: IssueState) -> None:
        """Set issue state.
        
        Args:
            key: Issue key (repo#number)
            state: IssueState object
        """
        self.state[key] = state
    
    def delete(self, key: str) -> None:
        """Delete issue state.
        
        Args:
            key: Issue key (repo#number)
        """
        if key in self.state:
            del self.state[key]
    
    def has(self, key: str) -> bool:
        """Check if state exists for key.
        
        Args:
            key: Issue key (repo#number)
            
        Returns:
            True if state exists
        """
        return key in self.state
    
    def is_completed(self, key: str) -> bool:
        """Check if issue is marked as completed.
        
        Args:
            key: Issue key (repo#number)
            
        Returns:
            True if issue is completed
        """
        state = self.get(key)
        return state is not None and state.completed
