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
        
        COORDINATOR = INTELLIGENCE LAYER (makes decisions)
        POLLING = EXECUTION LAYER (executes decisions)
        
        This is the MANDATORY entry point. Coordinator analyzes and returns decision.
        Polling service executes the decision.
        
        Args:
            owner: Repository owner
            repo: Repository name
            issue_number: Issue number
            issue_data: Full issue data from GitHub
        
        Returns:
            Dict with routing decision for polling service to execute
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
        
        # Step 3: Post decision comment and tag issue
        self._post_decision_comment(owner, repo, issue_number, decision, analysis)
        self._tag_issue_with_decision(owner, repo, issue_number, decision)
        
        # Step 4: Return decision for polling service to execute
        if decision['action'] == 'DELEGATE_SIMPLE':
            return {
                'status': 'decision_made',
                'decision': 'SIMPLE',
                'action': 'start_code_agent',
                'escalation_enabled': False,
                'reasoning': decision['reasoning'],
                'analysis': analysis,
                'instructions': {
                    'agent_type': 'code_agent',
                    'enable_escalation': False,
                    'priority': 'normal'
                }
            }
        
        elif decision['action'] == 'DELEGATE_WITH_ESCALATION':
            return {
                'status': 'decision_made',
                'decision': 'UNCERTAIN',
                'action': 'start_code_agent',
                'escalation_enabled': True,
                'reasoning': decision['reasoning'],
                'analysis': analysis,
                'instructions': {
                    'agent_type': 'code_agent',
                    'enable_escalation': True,
                    'priority': 'high'
                }
            }
        
        elif decision['action'] == 'ORCHESTRATE':
            return {
                'status': 'decision_made',
                'decision': 'COMPLEX',
                'action': 'start_coordinator_orchestration',
                'reasoning': decision['reasoning'],
                'analysis': analysis,
                'instructions': {
                    'create_sub_issues': True,
                    'build_execution_plan': True,
                    'assign_multiple_agents': True,
                    'priority': 'high'
                }
            }
        
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
    
    def _tag_issue_with_decision(
        self,
        owner: str,
        repo: str,
        issue_number: int,
        decision: Dict
    ):
        """
        Tag issue with coordinator decision labels.
        
        Labels added:
        - coordinator-approved-simple
        - coordinator-approved-uncertain
        - coordinator-approved-complex
        """
        import requests
        
        # Determine label based on decision
        if decision['action'] == 'DELEGATE_SIMPLE':
            label = 'coordinator-approved-simple'
        elif decision['action'] == 'DELEGATE_WITH_ESCALATION':
            label = 'coordinator-approved-uncertain'
        else:  # ORCHESTRATE
            label = 'coordinator-approved-complex'
        
        try:
            token = os.getenv('GITHUB_TOKEN')
            url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}/labels"
            headers = {
                'Authorization': f'token {token}',
                'Accept': 'application/vnd.github.v3+json'
            }
            response = requests.post(url, json={'labels': [label]}, headers=headers)
            response.raise_for_status()
            logger.info(f"✅ Tagged issue with: {label}")
        except Exception as e:
            logger.error(f"❌ Failed to tag issue: {e}")
    
    def _post_decision_comment(
        self,
        owner: str,
        repo: str,
        issue_number: int,
        decision: Dict,
        analysis: Dict
    ):
        """Post comment explaining coordinator's decision."""
        import requests
        
        action = decision['action']
        
        if action == 'DELEGATE_SIMPLE':
            comment = f"""🎯 **Coordinator Decision: Simple Issue - Approved for Code Agent**

The coordinator has analyzed this issue and determined it's straightforward.

**Analysis:**
- Complexity: SIMPLE
- Score: {analysis['score']} points (threshold: 10)
- Confidence: {analysis['confidence']:.0%}
- Reasoning: {analysis['reasoning']}

**Decision:**
✅ Issue approved for direct code agent execution
- No orchestration needed
- Standard implementation approach
- Escalation NOT enabled

**Next Steps:**
The polling service will now start a code agent to implement this issue.

⏳ Agent will begin work shortly...
"""
        
        elif action == 'DELEGATE_WITH_ESCALATION':
            comment = f"""🎯 **Coordinator Decision: Uncertain Complexity - Monitored Execution**

The coordinator has analyzed this issue and determined complexity is unclear.

**Analysis:**
- Complexity: UNCERTAIN
- Score: {analysis['score']} points (threshold: 11-25)
- Confidence: {analysis['confidence']:.0%}
- Reasoning: {analysis['reasoning']}

**Decision:**
⚠️ Starting with code agent but ESCALATION ENABLED
- Single agent approach initially
- Coordinator monitoring enabled
- If complexity increases during work, agent can escalate back
- Coordinator ready to take over if needed

**Next Steps:**
The polling service will now start a code agent with escalation capability.

⏳ Agent will begin work shortly...
"""
        
        elif action == 'ORCHESTRATE':
            metrics = analysis.get('signals', {})
            comment = f"""🎯 **Coordinator Decision: Complex Issue - Orchestration Required**

The coordinator has analyzed this issue and determined it requires multi-agent coordination.

**Complexity Analysis:**
- Complexity: COMPLEX
- Score: {analysis['score']} points (threshold: >25)
- Confidence: {analysis['confidence']:.0%}

**Detected Signals:**
"""
            if metrics.get('file_mentions'):
                comment += f"\n- Files mentioned: {metrics['file_mentions']}"
            if metrics.get('task_count'):
                comment += f"\n- Tasks detected: {metrics['task_count']}"
            if metrics.get('has_architecture_keywords'):
                comment += "\n- Architecture changes detected"
            if metrics.get('has_refactor_keywords'):
                comment += "\n- Refactoring required"
            
            comment += """

**Decision:**
🎼 Coordinator will orchestrate multi-agent workflow
1. Break down into sub-issues
2. Create execution plan with dependencies
3. Assign specialized agents to each sub-issue
4. Monitor progress and coordinate work

**Next Steps:**
The polling service will now trigger coordinator orchestration.

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
