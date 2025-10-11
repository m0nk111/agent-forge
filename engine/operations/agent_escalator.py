"""
Agent Escalation System

Allows agents to escalate issues to coordinator when complexity exceeds their capability.

Escalation triggers:
- Too many files affected (>5)
- Multiple architectural components
- Stuck/blocked for extended time (>30 min)
- Failed attempts (>2)
- Explicit complexity markers discovered during research

Usage:
    escalator = AgentEscalator(agent_id="code_agent_1")
    
    # During execution
    if escalator.should_escalate(context):
        result = escalator.escalate_to_coordinator(
            issue_data=issue,
            progress_so_far=work_done,
            reason="Too many interconnected components"
        )
"""

import logging
import os
from typing import Dict, List, Optional
from datetime import datetime, timezone
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class EscalationContext:
    """Context for escalation decision."""
    
    # Work metrics
    files_affected: int = 0
    components_touched: List[str] = field(default_factory=list)
    failed_attempts: int = 0
    time_spent_minutes: float = 0.0
    
    # Discovery metrics
    discovered_dependencies: int = 0
    architecture_changes_needed: bool = False
    requires_coordination: bool = False
    
    # Agent state
    is_stuck: bool = False
    blocker_description: Optional[str] = None
    
    # Research findings
    research_notes: List[str] = field(default_factory=list)


@dataclass
class EscalationResult:
    """Result of escalation action."""
    
    escalated: bool
    coordinator_plan_id: Optional[str] = None
    sub_issues_created: List[int] = field(default_factory=list)
    message: str = ""
    next_action: str = ""  # 'wait_for_coordinator', 'continue', 'abort'


class AgentEscalator:
    """Manages agent escalation to coordinator."""
    
    # Escalation thresholds
    MAX_FILES_SIMPLE = 5
    MAX_COMPONENTS_SIMPLE = 3
    MAX_FAILED_ATTEMPTS = 2
    MAX_STUCK_TIME_MINUTES = 30
    
    def __init__(
        self,
        agent_id: str,
        github_token: Optional[str] = None,
        coordinator_agent = None
    ):
        """
        Initialize escalator.
        
        Args:
            agent_id: ID of the agent that may escalate
            github_token: GitHub token for posting comments
            coordinator_agent: Coordinator agent instance (optional)
        """
        self.agent_id = agent_id
        self.github_token = github_token or os.getenv('GITHUB_TOKEN')
        self.coordinator = coordinator_agent
        
        # Track escalation state
        self.escalation_started_at = None
        self.escalation_reason = None
        
        logger.info(f"🚨 Escalator initialized for {agent_id}")
    
    def should_escalate(self, context: EscalationContext) -> bool:
        """
        Determine if issue should be escalated to coordinator.
        
        Args:
            context: Current execution context
        
        Returns:
            True if escalation recommended
        """
        reasons = []
        
        # Too many files
        if context.files_affected > self.MAX_FILES_SIMPLE:
            reasons.append(f"Too many files affected ({context.files_affected} > {self.MAX_FILES_SIMPLE})")
        
        # Too many components
        if len(context.components_touched) > self.MAX_COMPONENTS_SIMPLE:
            reasons.append(f"Too many components ({len(context.components_touched)} > {self.MAX_COMPONENTS_SIMPLE})")
        
        # Failed attempts
        if context.failed_attempts >= self.MAX_FAILED_ATTEMPTS:
            reasons.append(f"Multiple failed attempts ({context.failed_attempts})")
        
        # Stuck too long
        if context.time_spent_minutes > self.MAX_STUCK_TIME_MINUTES:
            reasons.append(f"Stuck for too long ({context.time_spent_minutes:.0f} min)")
        
        # Architecture changes needed
        if context.architecture_changes_needed:
            reasons.append("Architecture changes required")
        
        # Explicit coordination needed
        if context.requires_coordination:
            reasons.append("Multi-agent coordination required")
        
        # Agent explicitly stuck
        if context.is_stuck:
            reasons.append(f"Agent blocked: {context.blocker_description}")
        
        if reasons:
            logger.warning(f"🚨 Escalation recommended for {self.agent_id}")
            for reason in reasons:
                logger.warning(f"   - {reason}")
            self.escalation_reason = "; ".join(reasons)
            return True
        
        return False
    
    def escalate_to_coordinator(
        self,
        owner: str,
        repo: str,
        issue_number: int,
        issue_data: Dict,
        progress_so_far: Dict,
        reason: str
    ) -> EscalationResult:
        """
        Escalate issue to coordinator for orchestration.
        
        Args:
            owner: Repository owner
            repo: Repository name
            issue_number: Issue number
            issue_data: Full issue data from GitHub
            progress_so_far: What the agent has done so far
            reason: Escalation reason
        
        Returns:
            EscalationResult with coordinator plan details
        """
        logger.warning(f"🚨 ESCALATING issue #{issue_number} to coordinator")
        logger.warning(f"   Reason: {reason}")
        
        self.escalation_started_at = datetime.now(timezone.utc)
        
        # Post escalation comment to issue
        self._post_escalation_comment(
            owner, repo, issue_number, 
            reason, progress_so_far
        )
        
        # If coordinator available, trigger it
        if self.coordinator:
            plan = self._trigger_coordinator(
                owner, repo, issue_number,
                issue_data, progress_so_far
            )
            
            return EscalationResult(
                escalated=True,
                coordinator_plan_id=plan.get('plan_id'),
                sub_issues_created=plan.get('sub_issues', []),
                message=f"Escalated to coordinator - {len(plan.get('sub_issues', []))} sub-issues created",
                next_action='wait_for_coordinator'
            )
        else:
            # No coordinator available - just flag for manual review
            logger.warning("⚠️  No coordinator available - flagging for manual review")
            
            self._add_needs_coordination_label(owner, repo, issue_number)
            
            return EscalationResult(
                escalated=True,
                message="Flagged for manual review - coordinator not available",
                next_action='abort'
            )
    
    def _post_escalation_comment(
        self,
        owner: str,
        repo: str,
        issue_number: int,
        reason: str,
        progress: Dict
    ):
        """Post comment explaining escalation."""
        import requests
        
        comment = f"""🚨 **Agent Escalation - Coordinator Needed**

Agent `{self.agent_id}` has escalated this issue to the coordinator for multi-agent orchestration.

**Escalation Reason:**
{reason}

**Progress So Far:**
"""
        
        # Add progress details
        if progress.get('files_analyzed'):
            comment += f"\n- Files analyzed: {len(progress['files_analyzed'])}"
        if progress.get('research_findings'):
            comment += f"\n- Research findings: {len(progress['research_findings'])} items"
        if progress.get('attempted_solutions'):
            comment += f"\n- Attempted solutions: {progress['attempted_solutions']}"
        
        comment += """

**Next Steps:**
The coordinator agent will:
1. Break down this issue into sub-issues
2. Create an execution plan
3. Assign specialized agents to each sub-issue
4. Monitor progress and coordinate work

⏳ Estimated coordination setup time: 2-5 minutes
"""
        
        try:
            url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}/comments"
            headers = {
                'Authorization': f'token {self.github_token}',
                'Accept': 'application/vnd.github.v3+json'
            }
            response = requests.post(url, json={'body': comment}, headers=headers)
            response.raise_for_status()
            logger.info(f"✅ Posted escalation comment to issue #{issue_number}")
        except Exception as e:
            logger.error(f"❌ Failed to post escalation comment: {e}")
    
    def _trigger_coordinator(
        self,
        owner: str,
        repo: str,
        issue_number: int,
        issue_data: Dict,
        progress: Dict
    ) -> Dict:
        """
        Trigger coordinator to take over.
        
        Args:
            owner: Repository owner
            repo: Repository name
            issue_number: Issue number
            issue_data: Full issue data
            progress: Agent's progress so far
        
        Returns:
            Dict with coordinator plan details
        """
        logger.info(f"🔄 Triggering coordinator for issue #{issue_number}")
        
        # This would call the coordinator's analyze_issue method
        # For now, return placeholder
        
        if self.coordinator:
            try:
                # Call coordinator to analyze and create plan
                plan = self.coordinator.analyze_issue(
                    owner=owner,
                    repo=repo,
                    issue_number=issue_number,
                    existing_progress=progress
                )
                
                # Coordinator creates sub-issues and execution plan
                execution_plan = self.coordinator.create_execution_plan(plan)
                
                logger.info(f"✅ Coordinator created plan: {execution_plan.plan_id}")
                logger.info(f"   Sub-issues: {len(execution_plan.sub_tasks)}")
                
                return {
                    'plan_id': execution_plan.plan_id,
                    'sub_issues': [task.id for task in execution_plan.sub_tasks],
                    'status': 'planning_complete'
                }
            except Exception as e:
                logger.error(f"❌ Coordinator trigger failed: {e}")
                return {'status': 'failed', 'error': str(e)}
        
        return {'status': 'no_coordinator'}
    
    def _add_needs_coordination_label(self, owner: str, repo: str, issue_number: int):
        """Add 'needs-coordination' label to issue."""
        import requests
        
        try:
            url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}/labels"
            headers = {
                'Authorization': f'token {self.github_token}',
                'Accept': 'application/vnd.github.v3+json'
            }
            response = requests.post(
                url, 
                json={'labels': ['needs-coordination']}, 
                headers=headers
            )
            response.raise_for_status()
            logger.info(f"✅ Added 'needs-coordination' label to #{issue_number}")
        except Exception as e:
            logger.error(f"❌ Failed to add label: {e}")
    
    def check_escalation_triggers(
        self,
        files_changed: List[str],
        time_elapsed_minutes: float,
        failed_attempts: int = 0
    ) -> Optional[EscalationContext]:
        """
        Quick check for escalation triggers.
        
        Returns:
            EscalationContext if escalation needed, None otherwise
        """
        context = EscalationContext(
            files_affected=len(files_changed),
            time_spent_minutes=time_elapsed_minutes,
            failed_attempts=failed_attempts
        )
        
        if self.should_escalate(context):
            return context
        
        return None
