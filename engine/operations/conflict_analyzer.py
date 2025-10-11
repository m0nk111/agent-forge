"""
Merge Conflict Complexity Analyzer

Analyzes merge conflicts to determine optimal resolution strategy:
- Simple: Auto-resolve via rebase
- Moderate: Manual fix with instructions
- Complex: Close PR and recreate from scratch
"""

import logging
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timezone
import requests

logger = logging.getLogger(__name__)


class ConflictComplexityAnalyzer:
    """Analyzes merge conflict complexity to recommend resolution strategy."""
    
    # Complexity thresholds
    SIMPLE_THRESHOLD = 8
    MODERATE_THRESHOLD = 15
    
    def __init__(self, github_token: str):
        """Initialize analyzer with GitHub token."""
        self.token = github_token
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'token {github_token}',
            'Accept': 'application/vnd.github.v3+json'
        })
    
    def analyze_pr_conflicts(self, owner: str, repo: str, pr_number: int) -> Dict:
        """
        Analyze conflict complexity for a PR.
        
        Args:
            owner: Repository owner
            repo: Repository name
            pr_number: Pull request number
        
        Returns:
            Dict with complexity analysis and recommended action
        """
        logger.info(f"🔍 Analyzing conflict complexity for {owner}/{repo}#{pr_number}")
        
        # Gather metrics
        metrics = self._gather_conflict_metrics(owner, repo, pr_number)
        
        # Calculate complexity score
        score = self._calculate_complexity_score(metrics)
        
        # Determine complexity level and action
        if score <= self.SIMPLE_THRESHOLD:
            complexity = 'simple'
            action = 'auto_resolve'
            reasoning = "Conflicts are minimal and can be auto-resolved via rebase"
        elif score <= self.MODERATE_THRESHOLD:
            complexity = 'moderate'
            action = 'manual_fix'
            reasoning = "Conflicts require manual review but are manageable"
        else:
            complexity = 'complex'
            action = 'close_and_recreate'
            reasoning = "Conflicts are too complex - recreating PR from scratch is more efficient"
        
        result = {
            'complexity': complexity,
            'score': score,
            'recommended_action': action,
            'reasoning': reasoning,
            'metrics': metrics,
            'thresholds': {
                'simple': self.SIMPLE_THRESHOLD,
                'moderate': self.MODERATE_THRESHOLD
            }
        }
        
        logger.info(f"📊 Complexity: {complexity} (score: {score}/{self.MODERATE_THRESHOLD})")
        logger.info(f"💡 Recommended action: {action}")
        
        return result
    
    def _gather_conflict_metrics(self, owner: str, repo: str, pr_number: int) -> Dict:
        """Gather all metrics needed for complexity analysis."""
        metrics = {
            'conflicted_files': 0,
            'conflict_markers': 0,
            'lines_affected': 0,
            'files_overlap': False,
            'age_days': 0,
            'commits_behind': 0,
            'total_files_changed': 0,
            'core_files_affected': False
        }
        
        try:
            # Get PR details
            pr_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
            pr_response = self.session.get(pr_url, timeout=30)
            pr_response.raise_for_status()
            pr_data = pr_response.json()
            
            # Calculate PR age
            created_at = datetime.fromisoformat(pr_data['created_at'].replace('Z', '+00:00'))
            age = datetime.now(timezone.utc) - created_at
            metrics['age_days'] = age.days
            
            # Get base and head refs
            base_sha = pr_data['base']['sha']
            head_sha = pr_data['head']['sha']
            
            # Calculate commits behind
            compare_url = f"https://api.github.com/repos/{owner}/{repo}/compare/{head_sha}...{base_sha}"
            compare_response = self.session.get(compare_url, timeout=30)
            if compare_response.status_code == 200:
                compare_data = compare_response.json()
                metrics['commits_behind'] = compare_data.get('ahead_by', 0)
            
            # Get files changed in PR
            files_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/files"
            files_response = self.session.get(files_url, timeout=30)
            files_response.raise_for_status()
            files_data = files_response.json()
            
            metrics['total_files_changed'] = len(files_data)
            
            # Analyze each file for conflicts
            conflicted_files = []
            total_conflict_markers = 0
            total_lines_affected = 0
            
            for file in files_data:
                filename = file['filename']
                
                # Check if file is likely to have conflicts (status: 'modified' usually)
                # We can't directly see conflict markers via API, but we can infer
                if file.get('status') == 'modified':
                    # Estimate based on changes
                    changes = file.get('changes', 0)
                    additions = file.get('additions', 0)
                    deletions = file.get('deletions', 0)
                    
                    # If both adds and deletes, more likely to conflict
                    if additions > 0 and deletions > 0:
                        conflicted_files.append(filename)
                        # Rough estimate: 1 conflict marker per 20 lines of overlap
                        estimated_markers = max(1, min(additions, deletions) // 20)
                        total_conflict_markers += estimated_markers
                        total_lines_affected += changes
                
                # Check for core files
                if self._is_core_file(filename):
                    metrics['core_files_affected'] = True
            
            metrics['conflicted_files'] = len(conflicted_files)
            metrics['conflict_markers'] = total_conflict_markers
            metrics['lines_affected'] = total_lines_affected
            
            # Check for file overlap (same files modified in multiple places)
            # This is a heuristic - real overlap detection would need diff analysis
            if metrics['conflicted_files'] > 2:
                metrics['files_overlap'] = True
            
        except Exception as e:
            logger.error(f"❌ Error gathering metrics: {e}")
        
        return metrics
    
    def _is_core_file(self, filename: str) -> bool:
        """Check if file is a core/critical file."""
        core_patterns = [
            'engine/core/',
            'engine/operations/',
            '__init__.py',
            'setup.py',
            'requirements.txt',
            'config/',
            'README.md'
        ]
        return any(pattern in filename for pattern in core_patterns)
    
    def _calculate_complexity_score(self, metrics: Dict) -> int:
        """
        Calculate complexity score based on metrics.
        
        Scoring (higher = more complex):
        - Conflicted files: 0-10 points
        - Conflict markers: 0-10 points  
        - Lines affected: 0-10 points
        - Files overlap: 0-5 points
        - PR age: 0-5 points
        - Commits behind: 0-10 points
        - Core files: 0-5 points
        
        Total: 0-55 points
        """
        score = 0
        
        # Conflicted files (0-10 points)
        files = metrics['conflicted_files']
        if files <= 2:
            score += 1
        elif files <= 5:
            score += 5
        else:
            score += 10
        
        # Conflict markers (0-10 points)
        markers = metrics['conflict_markers']
        if markers <= 5:
            score += 2
        elif markers <= 15:
            score += 6
        else:
            score += 10
        
        # Lines affected (0-10 points)
        lines = metrics['lines_affected']
        if lines <= 50:
            score += 1
        elif lines <= 200:
            score += 5
        else:
            score += 10
        
        # Files overlap (0-5 points)
        if metrics['files_overlap']:
            score += 5
        
        # PR age (0-5 points)
        age = metrics['age_days']
        if age <= 1:
            score += 0
        elif age <= 3:
            score += 2
        else:
            score += 5
        
        # Commits behind (0-10 points)
        behind = metrics['commits_behind']
        if behind <= 3:
            score += 1
        elif behind <= 10:
            score += 5
        else:
            score += 10
        
        # Core files affected (0-5 points)
        if metrics['core_files_affected']:
            score += 5
        
        return score
    
    def should_close_and_recreate(self, owner: str, repo: str, pr_number: int) -> Tuple[bool, str]:
        """
        Quick check if PR should be closed and recreated.
        
        Returns:
            (should_close, reason)
        """
        analysis = self.analyze_pr_conflicts(owner, repo, pr_number)
        
        should_close = analysis['recommended_action'] == 'close_and_recreate'
        reason = analysis['reasoning']
        
        if should_close:
            metrics = analysis['metrics']
            reason += f"\n\nMetrics: {metrics['conflicted_files']} files, "
            reason += f"{metrics['commits_behind']} commits behind, "
            reason += f"{metrics['age_days']} days old"
        
        return should_close, reason
