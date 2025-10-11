"""
Coordinator Issue Gateway

The coordinator acts as the MANDATORY entry point for all issues.
Every issue with 'agent-ready' label MUST go through the coordinator first.

Workflow:
1. Polling service detects issue with 'agent-ready' label
2. Polling service calls coordinator.process_issue()
3. Coordinator analyzes with LLM + IssueComplexityAnalyzer
4. Coordinator decides:
   - SIMPLE: Delegate to code_agent
   - NEEDS_RESEARCH: Delegate to code_agent with escalation enabled
   - COMPLEX: Create sub-issues and orchestrate

The coordinator is the INTELLIGENCE HUB - it makes ALL routing decisions.
"""

import logging
import os
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class CoordinatorGateway:
    """
    Gateway interface for coordinator as mandatory entry point.
    
    This is the ONLY way issues enter the system. No bypassing the coordinator.
    """
    
    def __init__(self, coordinator_agent):
        """
        Initialize gateway.
        
        Args:
            coordinator_agent: CoordinatorAgent instance
        """
        self.coordinator = coordinator_agent
        logger.info("🎯 Coordinator Gateway initialized - ALL issues must pass through here")
    
    def process_issue(
        self,
        owner: str,
        repo: str,
        issue_number: int,
        issue_data: Dict
    ) -> Dict:
        """
        Process issue through coordinator gateway.
        
        This is the MANDATORY entry point. Coordinator analyzes and decides routing.
        
        Args:
            owner: Repository owner
            repo: Repository name
            issue_number: Issue number
            issue_data: Full issue data from GitHub
        
        Returns:
            Dict with routing decision and execution details
        """
        logger.info(f"🎯 COORDINATOR GATEWAY: Processing issue #{issue_number}")
        logger.info(f"   Repository: {owner}/{repo}")
        logger.info(f"   Title: {issue_data.get('title', 'N/A')}")
        
        # Step 1: Analyze complexity with LLM + metrics
        analysis = self.coordinator.analyze_issue_complexity(
            title=issue_data.get('title', ''),
            body=issue_data.get('body', ''),
            labels=[l['name'] for l in issue_data.get('labels', [])]
        )
        
        logger.info(f"📊 Complexity Analysis:")
        logger.info(f"   Complexity: {analysis['complexity']}")
        logger.info(f"   Score: {analysis['score']}")
        logger.info(f"   Confidence: {analysis['confidence']:.0%}")
        logger.info(f"   Reasoning: {analysis['reasoning']}")
        
        # Step 2: Make routing decision
        decision = self._make_routing_decision(analysis, issue_data)
        
        logger.info(f"🎯 Routing Decision: {decision['action']}")
        
        # Step 3: Execute decision
        if decision['action'] == 'DELEGATE_SIMPLE':
            return self._delegate_to_code_agent(
                owner, repo, issue_number, issue_data,
                escalation=False
            )
        
        elif decision['action'] == 'DELEGATE_WITH_ESCALATION':
            return self._delegate_to_code_agent(
                owner, repo, issue_number, issue_data,
                escalation=True
            )
        
        elif decision['action'] == 'ORCHESTRATE':
            return self._orchestrate_complex_issue(
                owner, repo, issue_number, issue_data,
                analysis
            )
        
        else:
            logger.error(f"❌ Unknown action: {decision['action']}")
            return {'status': 'error', 'message': 'Unknown routing action'}
    
    def _make_routing_decision(
        self,
        analysis: Dict,
        issue_data: Dict
    ) -> Dict:
        """
        Make routing decision based on complexity analysis.
        
        Args:
            analysis: Complexity analysis from coordinator
            issue_data: Full issue data
        
        Returns:
            Dict with action and reasoning
        """
        complexity = analysis['complexity']
        score = analysis['score']
        confidence = analysis['confidence']
        
        # SIMPLE: Direct delegation
        if complexity == 'simple':
            return {
                'action': 'DELEGATE_SIMPLE',
                'reasoning': 'Issue is straightforward - delegate to code_agent',
                'escalation': False
            }
        
        # UNCERTAIN: Delegate with escalation capability
        elif complexity == 'uncertain':
            return {
                'action': 'DELEGATE_WITH_ESCALATION',
                'reasoning': 'Complexity unclear - delegate with escalation enabled',
                'escalation': True
            }
        
        # COMPLEX: Coordinator orchestration
        else:  # 'complex'
            return {
                'action': 'ORCHESTRATE',
                'reasoning': 'Issue is complex - coordinator will create sub-issues',
                'escalation': False  # Coordinator handles it
            }
    
    def _delegate_to_code_agent(
        self,
        owner: str,
        repo: str,
        issue_number: int,
        issue_data: Dict,
        escalation: bool
    ) -> Dict:
        """
        Delegate issue to code_agent.
        
        Args:
            owner: Repository owner
            repo: Repository name
            issue_number: Issue number
            issue_data: Full issue data
            escalation: Whether to enable escalation
        
        Returns:
            Dict with delegation details
        """
        logger.info(f"👨‍💻 DELEGATING to code_agent (escalation: {escalation})")
        
        # Post coordination comment
        self._post_coordination_comment(
            owner, repo, issue_number,
            action='delegate',
            escalation=escalation
        )
        
        # Get code_agent from registry
        code_agent = self.coordinator.get_available_agent(role='developer')
        
        if not code_agent:
            logger.error("❌ No code_agent available in registry!")
            return {
                'status': 'error',
                'message': 'No code_agent available',
                'action': 'delegate_failed'
            }
        
        # Start code_agent execution
        # This would actually call the code_agent's execute method
        logger.info(f"   Agent: {code_agent.agent_id}")
        logger.info(f"   Escalation enabled: {escalation}")
        
        # Return delegation info for polling service
        return {
            'status': 'delegated',
            'action': 'DELEGATE_WITH_ESCALATION' if escalation else 'DELEGATE_SIMPLE',
            'agent_id': code_agent.agent_id,
            'escalation_enabled': escalation,
            'message': f"Delegated to {code_agent.agent_id}"
        }
    
    def _orchestrate_complex_issue(
        self,
        owner: str,
        repo: str,
        issue_number: int,
        issue_data: Dict,
        analysis: Dict
    ) -> Dict:
        """
        Orchestrate complex issue with sub-tasks.
        
        Args:
            owner: Repository owner
            repo: Repository name
            issue_number: Issue number
            issue_data: Full issue data
            analysis: Complexity analysis
        
        Returns:
            Dict with orchestration details
        """
        logger.info(f"🎼 ORCHESTRATING complex issue")
        
        # Post coordination comment
        self._post_coordination_comment(
            owner, repo, issue_number,
            action='orchestrate',
            analysis=analysis
        )
        
        # Create execution plan
        plan = self.coordinator.create_execution_plan(
            owner=owner,
            repo=repo,
            issue_number=issue_number,
            issue_data=issue_data
        )
        
        # Create sub-issues
        sub_issues = self.coordinator.create_sub_issues(
            owner=owner,
            repo=repo,
            parent_issue=issue_number,
            plan=plan
        )
        
        logger.info(f"✅ Created {len(sub_issues)} sub-issues")
        for sub in sub_issues:
            logger.info(f"   #{sub['number']}: {sub['title']}")
        
        # Assign agents to sub-issues
        assignments = self.coordinator.assign_tasks(plan)
        
        return {
            'status': 'orchestrating',
            'action': 'ORCHESTRATE',
            'plan_id': plan.plan_id,
            'sub_issues': [s['number'] for s in sub_issues],
            'assignments': assignments,
            'message': f"Orchestrating with {len(sub_issues)} sub-issues"
        }
    
    def _post_coordination_comment(
        self,
        owner: str,
        repo: str,
        issue_number: int,
        action: str,
        escalation: bool = False,
        analysis: Optional[Dict] = None
    ):
        """Post comment explaining coordinator's decision."""
        import requests
        
        if action == 'delegate':
            if escalation:
                comment = f"""🎯 **Coordinator Decision: Delegate with Monitoring**

The coordinator has analyzed this issue and determined it needs a code agent with escalation capability.

**Analysis:**
- Complexity appears moderate
- Starting with single agent approach
- Escalation enabled if complexity increases during work

**Next Steps:**
1. Code agent will begin implementation
2. Coordinator monitors progress
3. If complexity emerges, agent can escalate back to coordinator

⏳ Agent will begin work shortly...
"""
            else:
                comment = f"""🎯 **Coordinator Decision: Simple Delegation**

The coordinator has analyzed this issue and determined it's straightforward.

**Analysis:**
- Issue is simple enough for single agent
- No orchestration needed
- Direct implementation approach

**Next Steps:**
Code agent will begin implementation immediately.

⏳ Agent will begin work shortly...
"""
        
        elif action == 'orchestrate':
            metrics = analysis.get('signals', {}) if analysis else {}
            comment = f"""🎯 **Coordinator Decision: Complex Issue Orchestration**

The coordinator has analyzed this issue and determined it requires multi-agent orchestration.

**Complexity Analysis:**
- Score: {analysis.get('score', 'N/A')} points
- Complexity: {analysis.get('complexity', 'N/A')}
- Confidence: {analysis.get('confidence', 0):.0%}

**Detected Signals:**
"""
            if metrics.get('file_mentions'):
                comment += f"\n- Files mentioned: {metrics['file_mentions']}"
            if metrics.get('task_count'):
                comment += f"\n- Tasks detected: {metrics['task_count']}"
            if metrics.get('has_architecture_keywords'):
                comment += "\n- Architecture changes detected"
            if metrics.get('has_refactor_keywords'):
                comment += "\n- Refactoring needed"
            
            comment += """

**Coordinator Actions:**
1. Breaking down into sub-issues
2. Creating execution plan with dependencies
3. Assigning specialized agents to each sub-issue
4. Monitoring progress and coordinating work

⏳ Sub-issues will be created shortly...
"""
        
        else:
            return
        
        # Post comment
        try:
            token = os.getenv('GITHUB_TOKEN')
            url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}/comments"
            headers = {
                'Authorization': f'token {token}',
                'Accept': 'application/vnd.github.v3+json'
            }
            response = requests.post(url, json={'body': comment}, headers=headers)
            response.raise_for_status()
            logger.info(f"✅ Posted coordinator decision comment")
        except Exception as e:
            logger.error(f"❌ Failed to post comment: {e}")
