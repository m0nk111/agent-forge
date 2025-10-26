"""Issue filtering logic for polling service.

Handles filtering of GitHub issues based on labels, state, and claims.
"""

import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from engine.runners.polling_models import IssueState
from engine.runners.state_manager import StateManager


logger = logging.getLogger(__name__)


def _utc_now() -> datetime:
    """Return current UTC time as timezone-aware datetime."""
    return datetime.now(timezone.utc)


def _parse_iso_timestamp(value: str) -> datetime:
    """Parse ISO timestamp supporting legacy naive and Zulu formats."""
    normalized = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


class IssueFilter:
    """Filters issues based on actionability criteria."""
    
    def __init__(
        self,
        state_manager: StateManager,
        watch_labels: List[str],
        claim_timeout_minutes: int,
        creative_logs_enabled: bool = False,
        github_claim_checker=None  # NEW: Optional GitHub claim checker callback
    ):
        """Initialize issue filter.
        
        Args:
            state_manager: State manager for claim tracking
            watch_labels: Labels that make issues actionable
            claim_timeout_minutes: Minutes before claim expires
            creative_logs_enabled: Whether to enable creative logging
            github_claim_checker: Optional callback to check GitHub for claims (polling_service.is_issue_claimed)
        """
        self.state_manager = state_manager
        self.watch_labels = watch_labels
        self.claim_timeout_minutes = claim_timeout_minutes
        self.creative_logs_enabled = creative_logs_enabled
        self.github_claim_checker = github_claim_checker  # NEW
    
    def _get_issue_key(self, issue: Dict) -> str:
        """Generate unique key for issue.
        
        Args:
            issue: Issue dictionary
            
        Returns:
            Unique key string
        """
        return f"{issue['repository']}#{issue['number']}"
    
    def _get_issue_labels(self, issue: Dict) -> List[str]:
        """Extract label names from issue.
        
        Args:
            issue: Issue dictionary
            
        Returns:
            List of label names
        """
        return [label['name'] for label in issue.get('labels', [])]
    
    def _has_watch_label(self, issue_labels: List[str]) -> bool:
        """Check if issue has any watch labels.
        
        Args:
            issue_labels: List of issue label names
            
        Returns:
            True if any watch label is present
        """
        return any(label in self.watch_labels for label in issue_labels)
    
    def _is_completed(self, issue_key: str) -> bool:
        """Check if issue is marked as completed.
        
        Args:
            issue_key: Issue key (repo#number)
            
        Returns:
            True if issue is completed
        """
        return self.state_manager.is_completed(issue_key)
    
    def _is_claim_valid(self, issue_key: str) -> bool:
        """Check if issue has valid (non-expired) claim.
        
        Args:
            issue_key: Issue key (repo#number)
            
        Returns:
            True if claim is valid and not expired
        """
        state = self.state_manager.get(issue_key)
        
        if not state:
            return False
        
        # No claim exists
        if state.claimed_by is None:
            logger.info(f"   ⚠️  Issue in state but no claim - allowing processing")
            return False
        
        # Claim exists but no timestamp
        if not state.claimed_at:
            logger.info(f"   ⚠️  Claim exists but no timestamp - allowing processing")
            return False
        
        # Check if claim expired
        try:
            claimed_at = _parse_iso_timestamp(state.claimed_at)
            now = _utc_now()
            age_minutes = (now - claimed_at).total_seconds() / 60
            
            logger.info(f"   Claim age: {age_minutes:.1f} min (timeout: {self.claim_timeout_minutes} min)")
            
            if age_minutes < self.claim_timeout_minutes:
                logger.info(f"   ❌ Skipping: claim still valid (expires in {self.claim_timeout_minutes - age_minutes:.1f} min)")
                return True
            else:
                logger.info(f"   ⚠️  Claim expired ({age_minutes:.1f} min > {self.claim_timeout_minutes} min) - allowing re-processing")
                # Remove expired state to allow fresh claim
                self.state_manager.delete(issue_key)
                return False
        except Exception as e:
            logger.warning(f"   ⚠️  Error parsing claim timestamp: {e} - allowing processing")
            return False
    
    def _log_creative_motif(self, issue_key: str, issue: Dict) -> None:
        """Log creative motif for issue if enabled.
        
        Args:
            issue_key: Issue key
            issue: Issue dictionary
        """
        if not self.creative_logs_enabled:
            return
        
        try:
            from engine.operations.creative_status import generate_issue_motif
            motif = generate_issue_motif(
                issue.get('title', ''),
                self._get_issue_labels(issue)
            )
            logger.info("🎨 Creative pulse for %s:%s%s", issue_key, os.linesep, motif)
        except Exception as e:
            logger.debug(f"Error generating creative motif: {e}")
    
    def is_actionable(self, issue: Dict) -> bool:
        """Check if single issue is actionable.
        
        Args:
            issue: Issue dictionary
            
        Returns:
            True if issue is actionable
        """
        try:
            issue_key = self._get_issue_key(issue)
            issue_labels = self._get_issue_labels(issue)
            
            logger.info(f"🔍 Evaluating issue {issue_key}: {issue['title']}")
            logger.info(f"   Labels: {issue_labels}")
            logger.info(f"   Watch labels: {self.watch_labels}")
            logger.info(f"   In state: {self.state_manager.has(issue_key)}")
            
            # Skip if completed
            if self._is_completed(issue_key):
                logger.info(f"   ❌ Skipping: already completed")
                return False
            
            # Skip if valid claim exists (local state check)
            if self._is_claim_valid(issue_key):
                return False
            
            # NEW: Also check GitHub comments for claims (remote check)
            logger.info(f"   🐛 DEBUG: github_claim_checker = {self.github_claim_checker is not None}")
            if self.github_claim_checker:
                logger.info(f"   🔍 Checking GitHub for existing claims...")
                repo = issue['repository']
                issue_number = issue['number']
                if self.github_claim_checker(repo, issue_number):
                    logger.info(f"   ❌ Skipping: issue claimed on GitHub (remote check)")
                    return False
                else:
                    logger.info(f"   ✅ No active claim found on GitHub")
            else:
                logger.warning(f"   ⚠️  GitHub claim checker not configured - skipping remote check")
            
            # Check labels
            has_watch_label = self._has_watch_label(issue_labels)
            logger.info(f"   Has watch label: {has_watch_label}")
            
            if has_watch_label:
                logger.info(f"   ✅ Issue is actionable!")
                logger.info(f"Actionable issue found: {issue_key} - {issue['title']}")
                self._log_creative_motif(issue_key, issue)
                return True
            else:
                logger.info(f"   ❌ Skipping: no watch labels match")
                return False
                
        except Exception as e:
            logger.error(f"Error evaluating issue: {e}", exc_info=True)
            return False
    
    def filter_actionable_issues(self, issues: List[Dict]) -> List[Dict]:
        """Filter issues based on labels and state.
        
        Args:
            issues: List of issue dictionaries
            
        Returns:
            Filtered list of actionable issues
        """
        actionable = []
        
        logger.info(f"🐛 DEBUG: Filtering {len(issues)} issues")
        
        for idx, issue in enumerate(issues):
            logger.info(f"🐛 DEBUG: Processing issue {idx+1}/{len(issues)}")
            logger.info(f"🐛 DEBUG: Issue dict keys: {list(issue.keys())}")
            logger.info(f"🐛 DEBUG: Issue repository: {issue.get('repository')}")
            logger.info(f"🐛 DEBUG: Issue number: {issue.get('number')}")
            
            if self.is_actionable(issue):
                actionable.append(issue)
        
        logger.info(f"🐛 DEBUG: filter_actionable_issues returning {len(actionable)} issues")
        return actionable
