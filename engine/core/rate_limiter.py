"""
Rate Limiter and Anti-Spam Protection for GitHub Operations

Prevents spam and abuse by:
- Rate limiting API calls (per endpoint)
- Tracking operation history
- Detecting suspicious patterns
- Enforcing cooldown periods
- Monitoring duplicate actions
"""

import time
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
from enum import Enum

logger = logging.getLogger(__name__)


class OperationType(Enum):
    """Types of operations that can be rate limited."""
    ISSUE_COMMENT = "issue_comment"
    PR_COMMENT = "pr_comment"
    ISSUE_CREATE = "issue_create"
    PR_CREATE = "pr_create"
    ISSUE_UPDATE = "issue_update"
    PR_UPDATE = "pr_update"
    LABEL_UPDATE = "label_update"
    ASSIGNMENT = "assignment"
    API_READ = "api_read"
    API_WRITE = "api_write"


@dataclass
class RateLimitConfig:
    """Rate limit configuration for different operation types."""
    
    # GitHub API limits
    github_api_hourly_limit: int = 5000  # GitHub's limit
    github_api_safety_threshold: int = 4500  # Stop before hitting limit
    
    # Comment limits (prevent spam)
    comments_per_minute: int = 3
    comments_per_hour: int = 30
    comments_per_day: int = 200
    
    # Issue/PR creation limits
    issues_per_hour: int = 10
    prs_per_hour: int = 5
    
    # Update operation limits
    updates_per_minute: int = 5
    updates_per_hour: int = 50
    
    # Cooldown periods (seconds)
    comment_cooldown: int = 20  # 20 seconds between comments
    issue_cooldown: int = 60  # 1 minute between issue creations
    pr_cooldown: int = 120  # 2 minutes between PR creations
    
    # Duplicate detection
    duplicate_detection_window: int = 3600  # 1 hour
    max_duplicate_operations: int = 2  # Allow 2 identical operations max
    
    # Burst detection
    burst_window: int = 60  # 1 minute
    max_burst_operations: int = 10  # Max 10 operations per minute


@dataclass
class OperationRecord:
    """Record of a single operation."""
    operation_type: OperationType
    timestamp: float
    target: str  # repo, issue number, etc.
    content_hash: Optional[str] = None  # For duplicate detection
    success: bool = True


class RateLimiter:
    """
    Rate limiter with anti-spam protection.
    
    Features:
    - Per-operation-type rate limiting
    - Time-window based tracking
    - Duplicate operation detection
    - Burst protection
    - Cooldown enforcement
    """
    
    def __init__(self, config: Optional[RateLimitConfig] = None):
        """
        Initialize rate limiter.
        
        Args:
            config: Rate limit configuration (uses defaults if None)
        """
        self.config = config or RateLimitConfig()
        
        # Operation history tracking
        self.operations: deque = deque(maxlen=10000)  # Keep last 10k operations
        
        # Per-type operation tracking
        self.operations_by_type: Dict[OperationType, deque] = defaultdict(
            lambda: deque(maxlen=1000)
        )
        
        # Last operation timestamps (for cooldowns)
        self.last_operation_time: Dict[OperationType, float] = {}
        
        # Content hashes (for duplicate detection)
        self.content_hashes: Dict[str, List[float]] = defaultdict(list)
        
        # GitHub API rate limit tracking
        self.api_calls_remaining: int = self.config.github_api_hourly_limit
        self.api_reset_time: Optional[float] = None
        
        logger.info("🛡️ Rate limiter initialized with anti-spam protection")
    
    def check_rate_limit(
        self,
        operation_type: OperationType,
        target: str,
        content: Optional[str] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if an operation is allowed.
        
        Args:
            operation_type: Type of operation
            target: Target (repo, issue, etc.)
            content: Optional content (for duplicate detection)
        
        Returns:
            Tuple of (allowed: bool, reason: Optional[str])
        """
        now = time.time()
        
        # 1. Check GitHub API limits
        if self.api_calls_remaining < 100:
            return False, f"GitHub API rate limit low ({self.api_calls_remaining} remaining)"
        
        # 2. Check cooldown period
        if operation_type in self.last_operation_time:
            cooldown = self._get_cooldown(operation_type)
            time_since_last = now - self.last_operation_time[operation_type]
            if time_since_last < cooldown:
                wait_time = int(cooldown - time_since_last)
                return False, f"Cooldown active. Wait {wait_time}s before next {operation_type.value}"
        
        # 3. Check operation-specific limits
        allowed, reason = self._check_operation_limits(operation_type, now)
        if not allowed:
            return False, reason
        
        # 4. Check for duplicates
        if content:
            content_hash = self._hash_content(content)
            if self._is_duplicate(content_hash, now):
                return False, "Duplicate operation detected (same content within 1 hour)"
        
        # 5. Check burst protection
        if self._is_burst_detected(now):
            return False, "Burst detected. Too many operations in short time"
        
        return True, None
    
    def record_operation(
        self,
        operation_type: OperationType,
        target: str,
        content: Optional[str] = None,
        success: bool = True
    ):
        """
        Record an operation.
        
        Args:
            operation_type: Type of operation
            target: Target identifier
            content: Optional content (for duplicate tracking)
            success: Whether operation succeeded
        """
        now = time.time()
        content_hash = self._hash_content(content) if content else None
        
        record = OperationRecord(
            operation_type=operation_type,
            timestamp=now,
            target=target,
            content_hash=content_hash,
            success=success
        )
        
        # Add to global history
        self.operations.append(record)
        
        # Add to type-specific history
        self.operations_by_type[operation_type].append(record)
        
        # Update last operation time
        self.last_operation_time[operation_type] = now
        
        # Track content hash
        if content_hash:
            self.content_hashes[content_hash].append(now)
        
        logger.debug(f"📊 Recorded {operation_type.value} operation on {target}")
    
    def update_github_rate_limit(self, remaining: int, reset_time: int):
        """
        Update GitHub API rate limit info from response headers.
        
        Args:
            remaining: Remaining API calls
            reset_time: Unix timestamp when limit resets
        """
        self.api_calls_remaining = remaining
        self.api_reset_time = reset_time
        
        if remaining < 1000:
            logger.warning(f"⚠️ GitHub API rate limit low: {remaining} remaining")
    
    def get_stats(self) -> Dict:
        """Get rate limiter statistics."""
        now = time.time()
        
        # Count operations in time windows
        last_minute = sum(1 for op in self.operations if now - op.timestamp < 60)
        last_hour = sum(1 for op in self.operations if now - op.timestamp < 3600)
        last_day = sum(1 for op in self.operations if now - op.timestamp < 86400)
        
        # Count by type (last hour)
        by_type = {}
        for op_type in OperationType:
            count = sum(
                1 for op in self.operations_by_type[op_type]
                if now - op.timestamp < 3600
            )
            by_type[op_type.value] = count
        
        return {
            "operations_last_minute": last_minute,
            "operations_last_hour": last_hour,
            "operations_last_day": last_day,
            "by_type": by_type,
            "github_api_remaining": self.api_calls_remaining,
            "api_reset_time": datetime.fromtimestamp(self.api_reset_time).isoformat() if self.api_reset_time else None
        }
    
    def _get_cooldown(self, operation_type: OperationType) -> int:
        """Get cooldown period for operation type."""
        cooldowns = {
            OperationType.ISSUE_COMMENT: self.config.comment_cooldown,
            OperationType.PR_COMMENT: self.config.comment_cooldown,
            OperationType.ISSUE_CREATE: self.config.issue_cooldown,
            OperationType.PR_CREATE: self.config.pr_cooldown,
        }
        return cooldowns.get(operation_type, 10)  # Default 10s
    
    def _check_operation_limits(
        self,
        operation_type: OperationType,
        now: float
    ) -> Tuple[bool, Optional[str]]:
        """Check operation-specific limits."""
        ops = self.operations_by_type[operation_type]
        
        # Count in different time windows
        last_minute = sum(1 for op in ops if now - op.timestamp < 60)
        last_hour = sum(1 for op in ops if now - op.timestamp < 3600)
        last_day = sum(1 for op in ops if now - op.timestamp < 86400)
        
        # Check limits based on operation type
        if operation_type in (OperationType.ISSUE_COMMENT, OperationType.PR_COMMENT):
            if last_minute >= self.config.comments_per_minute:
                return False, f"Comment rate limit: {self.config.comments_per_minute}/min exceeded"
            if last_hour >= self.config.comments_per_hour:
                return False, f"Comment rate limit: {self.config.comments_per_hour}/hour exceeded"
            if last_day >= self.config.comments_per_day:
                return False, f"Comment rate limit: {self.config.comments_per_day}/day exceeded"
        
        elif operation_type == OperationType.ISSUE_CREATE:
            if last_hour >= self.config.issues_per_hour:
                return False, f"Issue creation rate limit: {self.config.issues_per_hour}/hour exceeded"
        
        elif operation_type == OperationType.PR_CREATE:
            if last_hour >= self.config.prs_per_hour:
                return False, f"PR creation rate limit: {self.config.prs_per_hour}/hour exceeded"
        
        elif operation_type in (OperationType.ISSUE_UPDATE, OperationType.PR_UPDATE, OperationType.LABEL_UPDATE):
            if last_minute >= self.config.updates_per_minute:
                return False, f"Update rate limit: {self.config.updates_per_minute}/min exceeded"
            if last_hour >= self.config.updates_per_hour:
                return False, f"Update rate limit: {self.config.updates_per_hour}/hour exceeded"
        
        return True, None
    
    def _is_duplicate(self, content_hash: str, now: float) -> bool:
        """Check if operation is a duplicate."""
        if content_hash not in self.content_hashes:
            return False
        
        # Count occurrences within detection window
        recent_ops = [
            ts for ts in self.content_hashes[content_hash]
            if now - ts < self.config.duplicate_detection_window
        ]
        
        return len(recent_ops) >= self.config.max_duplicate_operations
    
    def _is_burst_detected(self, now: float) -> bool:
        """Check if burst activity is detected."""
        recent_ops = sum(
            1 for op in self.operations
            if now - op.timestamp < self.config.burst_window
        )
        return recent_ops >= self.config.max_burst_operations
    
    @staticmethod
    def _hash_content(content: str) -> str:
        """Generate hash of content for duplicate detection."""
        import hashlib
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def cleanup_old_records(self, max_age_hours: int = 24):
        """
        Clean up old operation records.
        
        Args:
            max_age_hours: Maximum age of records to keep
        """
        now = time.time()
        cutoff = now - (max_age_hours * 3600)
        
        # Clean content hashes
        for content_hash in list(self.content_hashes.keys()):
            self.content_hashes[content_hash] = [
                ts for ts in self.content_hashes[content_hash]
                if ts > cutoff
            ]
            if not self.content_hashes[content_hash]:
                del self.content_hashes[content_hash]
        
        logger.debug(f"🧹 Cleaned up operation records older than {max_age_hours}h")


# Global rate limiter instance
_global_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """Get or create global rate limiter instance."""
    global _global_rate_limiter
    if _global_rate_limiter is None:
        _global_rate_limiter = RateLimiter()
    return _global_rate_limiter


def reset_rate_limiter():
    """Reset global rate limiter (for testing)."""
    global _global_rate_limiter
    _global_rate_limiter = None
