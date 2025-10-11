"""
PR Workflow Orchestrator Module

Orchestrates complete PR review workflows including review, assignment, labeling, and merging.
Extracted from PRReviewAgent for better modularity and single responsibility.
"""

import logging
import re
from typing import Dict, Optional, List

logger = logging.getLogger(__name__)


class WorkflowOrchestrator:
    """
    Orchestrates complete PR review workflows.
    
    Handles multi-step workflows including:
    - PR code review execution
    - Reviewer assignment
    - Label management
    - Merge decision logic
    - Draft conversion for critical issues
    """
    
    def __init__(
        self,
        review_agent,
        github_client,
        review_lock,
        bot_account: str = "post"
    ):
        """
        Initialize workflow orchestrator.
        
        Args:
            review_agent: PR review agent instance (for review_pr method)
            github_client: GitHub API client
            review_lock: ReviewLock instance for preventing concurrent reviews
            bot_account: Bot account name for self-review checks
        """
        self.review_agent = review_agent
        self.github_client = github_client
        self.review_lock = review_lock
        self.bot_account = bot_account
        
    def complete_review_workflow(
        self,
        repo: str,
        pr_number: int,
        auto_assign_reviewers: bool = True,
        auto_label: bool = True,
        reviewers: Optional[List[str]] = None,
        post_comment: bool = True
    ) -> Dict:
        """
        Complete PR review workflow with review, assignment, and labeling.
        
        This method performs the full PR review process:
        1. Review the PR code
        2. Post review comment with status (APPROVE/REQUEST_CHANGES/COMMENT)
        3. Assign reviewers (if specified)
        4. Add appropriate labels based on review results
        5. Assign PR to relevant users
        
        Args:
            repo: Repository in owner/name format
            pr_number: Pull request number
            auto_assign_reviewers: Automatically assign admin as reviewer (default: True)
            auto_label: Automatically add labels based on review (default: True)
            reviewers: List of GitHub usernames to assign as reviewers (default: ['m0nk111'])
            post_comment: Post review comment (default: True)
        
        Returns:
            Dict with workflow results including review_result, assigned_reviewers, added_labels
        """
        workflow_result = {
            'review_result': None,
            'review_posted': False,
            'reviewers_assigned': False,
            'labels_added': False,
            'assignees_updated': False,
            'errors': []
        }
        
        try:
            # Step 1: Review the PR
            logger.info(f"🔍 Starting complete PR review workflow for {repo}#{pr_number}")
            review_result = self.review_agent.review_pr(repo, pr_number)
            workflow_result['review_result'] = review_result
            
            # Step 2: Post review comment with proper status
            if post_comment:
                logger.info("📝 Posting review comment...")
                if self.review_agent.post_review_comment(repo, pr_number, review_result, use_review_api=True):
                    workflow_result['review_posted'] = True
                else:
                    workflow_result['errors'].append("Failed to post review comment")
            
            # Step 3: Assign reviewers
            if auto_assign_reviewers:
                if reviewers is None:
                    reviewers = ['m0nk111']  # Default to admin
                
                logger.info(f"👥 Assigning reviewers: {reviewers}")
                if self.github_client.assign_reviewers(repo, pr_number, reviewers):
                    workflow_result['reviewers_assigned'] = True
                else:
                    workflow_result['errors'].append("Failed to assign reviewers (may be PR author)")
            
            # Step 4: Add labels based on review result
            if auto_label:
                labels = self._determine_labels(review_result)
                
                logger.info(f"🏷️  Adding labels: {labels}")
                if self.github_client.add_labels(repo, pr_number, labels):
                    workflow_result['labels_added'] = True
                    workflow_result['labels'] = labels
                else:
                    workflow_result['errors'].append("Failed to add labels")
            
            # Step 5: Assign PR to admin for visibility
            if auto_assign_reviewers:
                logger.info("📌 Assigning PR to admin...")
                if self.github_client.update_assignees(repo, pr_number, ['m0nk111']):
                    workflow_result['assignees_updated'] = True
                else:
                    workflow_result['errors'].append("Failed to assign PR")
            
            # Summary
            logger.info("✅ PR review workflow complete")
            logger.info(f"   Review posted: {workflow_result['review_posted']}")
            logger.info(f"   Reviewers assigned: {workflow_result['reviewers_assigned']}")
            logger.info(f"   Labels added: {workflow_result['labels_added']}")
            logger.info(f"   Assignees updated: {workflow_result['assignees_updated']}")
            
            if workflow_result['errors']:
                logger.warning(f"⚠️ Errors occurred: {workflow_result['errors']}")
        
        except Exception as e:
            logger.error(f"❌ Workflow error: {e}", exc_info=True)
            workflow_result['errors'].append(str(e))
        
        return workflow_result
    
    def complete_review_and_merge_workflow(
        self,
        repo: str,
        pr_number: int,
        auto_merge_if_approved: bool = False,
        merge_with_suggestions: bool = False,
        merge_method: str = 'squash',
        auto_assign_reviewers: bool = True,
        auto_label: bool = True,
        reviewers: Optional[List[str]] = None,
        post_comment: bool = True
    ) -> Dict:
        """
        Complete workflow: review, assign, label, and optionally merge.
        
        This extends complete_review_workflow() with intelligent merge decision.
        
        Merge Logic:
        - AUTO_MERGE: Fully approved, no issues → merge if auto_merge_if_approved=True
        - MERGE_WITH_CONSIDERATION: Approved with suggestions → merge if merge_with_suggestions=True
        - MANUAL_REVIEW: Critical issues or many warnings → never auto-merge
        - DO_NOT_MERGE: Changes requested → never merge
        
        Args:
            repo: Repository in owner/name format
            pr_number: Pull request number
            auto_merge_if_approved: Auto-merge if fully approved (no issues) (default: False)
            merge_with_suggestions: Merge even if suggestions present (default: False)
            merge_method: Merge method: 'merge', 'squash', 'rebase' (default: squash)
            auto_assign_reviewers: Assign reviewers (default: True)
            auto_label: Add labels (default: True)
            reviewers: List of reviewers (default: ['m0nk111'])
            post_comment: Post review comment (default: True)
        
        Returns:
            Dict with workflow results including merge decision and status
        """
        # 🔒 Acquire review lock to prevent concurrent reviews
        requester = f"{self.bot_account}-pr-review"
        if not self.review_lock.acquire(repo, pr_number, requester):
            logger.warning(f"⏭️ Skipping review of {repo}#{pr_number} - already being reviewed")
            return {
                'skipped': True,
                'reason': 'Review already in progress (locked by another process)',
                'review_result': None,
                'merge_decision': None
            }
        
        try:
            # 🛡️ Check for self-review (bot reviewing own PR)
            if self._is_self_review(repo, pr_number):
                logger.warning(f"🛡️  Skipping self-review: bot cannot review own PR")
                return {
                    'skipped': True,
                    'reason': 'Self-review prevented',
                    'review_result': None,
                    'merge_decision': None
                }
            
            # Run standard review workflow
            workflow_result = self.complete_review_workflow(
                repo=repo,
                pr_number=pr_number,
                auto_assign_reviewers=auto_assign_reviewers,
                auto_label=auto_label,
                reviewers=reviewers,
                post_comment=post_comment
            )
            
            # Evaluate merge decision
            review_result = workflow_result['review_result']
            merge_decision = self._evaluate_merge_decision(review_result)
            workflow_result['merge_decision'] = merge_decision
            
            # Handle critical issues - convert to draft
            if merge_decision['merge_recommendation'] == 'DO_NOT_MERGE':
                self._handle_critical_issues(repo, pr_number, review_result, merge_decision)
                workflow_result['converted_to_draft'] = True
            
            # Execute merge if appropriate
            should_merge = self._should_execute_merge(
                merge_decision,
                auto_merge_if_approved,
                merge_with_suggestions
            )
            
            if should_merge:
                logger.info(f"🚀 Auto-merging PR {repo}#{pr_number}")
                merge_result = self.github_client.merge_pull_request(
                    repo, pr_number, merge_method
                )
                workflow_result['merged'] = merge_result
            else:
                logger.info(f"📌 PR not auto-merged: {merge_decision['merge_recommendation']}")
                workflow_result['merged'] = False
        
        finally:
            # 🔓 Always release lock
            self.review_lock.release(repo, pr_number, requester)
        
        return workflow_result
    
    def _determine_labels(self, review_result: Dict) -> List[str]:
        """
        Determine appropriate labels based on review result.
        
        Args:
            review_result: Review result dictionary
        
        Returns:
            List of label names to add
        """
        labels = []
        
        if review_result['approved']:
            if review_result['issues']:
                labels.append('approved-with-suggestions')
                labels.append('ready-for-merge')
            else:
                labels.append('approved')
                labels.append('ready-for-merge')
        else:
            labels.append('changes-requested')
            labels.append('needs-work')
        
        # Add technical labels
        if self.review_agent.use_llm:
            labels.append('ai-reviewed')
        else:
            labels.append('static-reviewed')
        
        # Add severity labels
        critical_count = sum(1 for issue in review_result['issues'] if 'CRITICAL' in issue)
        if critical_count > 0:
            labels.append('critical-issues')
        
        return labels
    
    def _is_self_review(self, repo: str, pr_number: int) -> bool:
        """
        Check if this would be a self-review (bot reviewing own PR).
        
        Args:
            repo: Repository name
            pr_number: PR number
        
        Returns:
            True if PR author is same as reviewer bot
        """
        try:
            pr_data = self.github_client.get_pr_details(repo, pr_number)
            if pr_data:
                pr_author = pr_data.get('user', {}).get('login', '')
                reviewer_account = f"m0nk111-{self.bot_account}"
                return pr_author == reviewer_account
        except Exception as e:
            logger.error(f"Error checking self-review: {e}")
        
        return False
    
    def _evaluate_merge_decision(self, review_result: Dict) -> Dict:
        """
        Evaluate whether PR should be merged based on review.
        
        Args:
            review_result: Review result dictionary
        
        Returns:
            Dict with merge recommendation and reasoning
        """
        issues = review_result.get('issues', [])
        critical_count = sum(1 for i in issues if 'CRITICAL' in i or '❌' in i)
        warning_count = sum(1 for i in issues if 'WARNING' in i or '⚠️' in i)
        
        if not review_result['approved']:
            return {
                'merge_recommendation': 'DO_NOT_MERGE',
                'reason': 'Changes requested',
                'critical_count': critical_count,
                'warning_count': warning_count
            }
        
        if critical_count > 0:
            return {
                'merge_recommendation': 'DO_NOT_MERGE',
                'reason': f'{critical_count} critical issues',
                'critical_count': critical_count,
                'warning_count': warning_count
            }
        
        if not issues:
            return {
                'merge_recommendation': 'AUTO_MERGE',
                'reason': 'Fully approved, no issues',
                'critical_count': 0,
                'warning_count': 0
            }
        
        if warning_count <= 3:
            return {
                'merge_recommendation': 'MERGE_WITH_CONSIDERATION',
                'reason': f'Approved with {warning_count} minor suggestions',
                'critical_count': 0,
                'warning_count': warning_count
            }
        
        return {
            'merge_recommendation': 'MANUAL_REVIEW',
            'reason': f'Many warnings ({warning_count}), manual review recommended',
            'critical_count': 0,
            'warning_count': warning_count
        }
    
    def _handle_critical_issues(
        self,
        repo: str,
        pr_number: int,
        review_result: Dict,
        merge_decision: Dict
    ):
        """
        Handle critical issues by converting PR to draft and adding comment.
        
        Args:
            repo: Repository name
            pr_number: PR number
            review_result: Review result
            merge_decision: Merge decision dict
        """
        critical_count = merge_decision.get('critical_count', 0)
        if critical_count == 0:
            return
        
        logger.warning(f"⚠️ Converting PR to draft due to {critical_count} critical issue(s)")
        
        # Convert to draft
        if self.github_client.convert_to_draft(repo, pr_number, f"{critical_count} critical issues"):
            # Add explanatory comment
            comment = f"""🚧 **Converted to Draft**

This PR has been automatically converted to draft status because the automated review found **{critical_count} critical issue(s)** that must be addressed before merging.

**Critical Issues:**
"""
            # Extract critical issues from review
            for issue in review_result.get('issues', []):
                if 'CRITICAL' in issue or '❌' in issue:
                    comment += f"- {issue}\n"
            
            comment += """
**Next Steps:**
1. Fix the critical issues listed above
2. Push your changes to this branch
3. Mark this PR as "Ready for review" when done
4. The automated review will run again

Once all critical issues are resolved, this PR can be merged."""
            
            self.github_client.add_comment(repo, pr_number, comment)
    
    def _should_execute_merge(
        self,
        merge_decision: Dict,
        auto_merge_if_approved: bool,
        merge_with_suggestions: bool
    ) -> bool:
        """
        Determine if PR should be auto-merged based on decision and settings.
        
        Args:
            merge_decision: Merge decision dict
            auto_merge_if_approved: Allow auto-merge for fully approved PRs
            merge_with_suggestions: Allow merge with minor suggestions
        
        Returns:
            True if PR should be merged
        """
        recommendation = merge_decision['merge_recommendation']
        
        if recommendation == 'AUTO_MERGE':
            return auto_merge_if_approved
        
        if recommendation == 'MERGE_WITH_CONSIDERATION':
            return merge_with_suggestions
        
        return False
