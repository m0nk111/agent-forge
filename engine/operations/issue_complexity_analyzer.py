"""
Issue Complexity Analyzer

Analyzes GitHub issues to determine complexity and recommend handling strategy:
- Simple: Direct to single agent (code_agent)
- Complex: Requires coordinator orchestration with sub-issues
- Uncertain: Start with single agent but enable escalation

Used by coordinator for intelligent triage before issue execution.
"""

import logging
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ComplexitySignals:
    """Signals that indicate issue complexity."""
    
    # Metrics
    description_length: int
    task_count: int
    file_mentions: int
    code_blocks: int
    dependency_mentions: int
    
    # Keywords
    has_refactor_keywords: bool
    has_architecture_keywords: bool
    has_multi_component_keywords: bool
    
    # Labels
    has_complex_labels: bool
    
    # Derived
    confidence_score: float = 0.0
    reasoning: List[str] = None
    
    def __post_init__(self):
        if self.reasoning is None:
            self.reasoning = []


class IssueComplexityAnalyzer:
    """Analyzes issue complexity for intelligent routing."""
    
    # Complexity thresholds
    SIMPLE_THRESHOLD = 10
    COMPLEX_THRESHOLD = 25
    
    # Keyword patterns
    REFACTOR_KEYWORDS = [
        'refactor', 'redesign', 'rewrite', 'restructure', 
        'migrate', 'upgrade', 'modernize'
    ]
    
    ARCHITECTURE_KEYWORDS = [
        'architecture', 'system design', 'infrastructure',
        'framework', 'platform', 'integration'
    ]
    
    MULTI_COMPONENT_KEYWORDS = [
        'multiple', 'several', 'across', 'throughout',
        'coordinate', 'orchestrate', 'synchronize'
    ]
    
    COMPLEX_LABELS = [
        'refactor', 'architecture', 'multi-agent',
        'infrastructure', 'breaking-change', 'epic'
    ]
    
    def __init__(self, llm_agent=None):
        """
        Initialize analyzer.
        
        Args:
            llm_agent: Optional LLM agent for semantic analysis
        """
        self.llm_agent = llm_agent
        logger.info("🔍 Issue Complexity Analyzer initialized")
    
    def analyze_issue(
        self,
        title: str,
        body: str,
        labels: List[str],
        use_llm: bool = False
    ) -> Dict:
        """
        Analyze issue complexity and recommend handling strategy.
        
        Args:
            title: Issue title
            body: Issue description
            labels: Issue labels
            use_llm: Whether to use LLM for deeper analysis
        
        Returns:
            Dict with complexity analysis and routing recommendation
        """
        logger.info(f"🔍 Analyzing issue complexity...")
        logger.info(f"   Title: {title[:60]}...")
        logger.info(f"   Body length: {len(body)} chars")
        logger.info(f"   Labels: {labels}")
        
        # Gather signals
        signals = self._gather_signals(title, body, labels)
        
        # Calculate complexity score
        score = self._calculate_complexity_score(signals)
        
        # Determine complexity level
        if score <= self.SIMPLE_THRESHOLD:
            complexity = 'simple'
            routing = 'code_agent'
            confidence = 0.85
            reasoning = "Issue appears straightforward - single agent can handle"
        elif score <= self.COMPLEX_THRESHOLD:
            complexity = 'uncertain'
            routing = 'code_agent_with_escalation'
            confidence = 0.60
            reasoning = "Issue complexity unclear - start with agent but allow escalation"
        else:
            complexity = 'complex'
            routing = 'coordinator'
            confidence = 0.90
            reasoning = "Issue is complex - requires coordinator orchestration"
        
        # Optionally use LLM for semantic analysis
        if use_llm and self.llm_agent:
            llm_analysis = self._llm_semantic_analysis(title, body)
            # Adjust based on LLM insight
            if llm_analysis.get('override_complexity'):
                complexity = llm_analysis['override_complexity']
                routing = llm_analysis['override_routing']
                confidence = llm_analysis['confidence']
                reasoning = llm_analysis['reasoning']
        
        result = {
            'complexity': complexity,
            'score': score,
            'routing': routing,
            'confidence': confidence,
            'reasoning': reasoning,
            'signals': {
                'description_length': signals.description_length,
                'task_count': signals.task_count,
                'file_mentions': signals.file_mentions,
                'code_blocks': signals.code_blocks,
                'has_refactor_keywords': signals.has_refactor_keywords,
                'has_architecture_keywords': signals.has_architecture_keywords,
                'has_complex_labels': signals.has_complex_labels
            },
            'thresholds': {
                'simple': self.SIMPLE_THRESHOLD,
                'complex': self.COMPLEX_THRESHOLD
            },
            'escalation_enabled': complexity == 'uncertain'
        }
        
        logger.info(f"📊 Complexity: {complexity} (score: {score}, confidence: {confidence:.0%})")
        logger.info(f"🎯 Routing: {routing}")
        logger.info(f"💡 Reasoning: {reasoning}")
        
        return result
    
    def _gather_signals(self, title: str, body: str, labels: List[str]) -> ComplexitySignals:
        """Gather complexity signals from issue."""
        
        # Combine title and body for analysis
        full_text = f"{title}\n{body}".lower()
        
        # Count tasks (checkboxes)
        task_count = body.count('- [ ]') + body.count('- [x]')
        
        # Count file mentions (.py, .js, .ts, etc.)
        file_pattern = r'\b\w+\.(py|js|ts|jsx|tsx|java|go|cpp|c|h|rb|php|cs|swift|kt|rs)\b'
        file_mentions = len(re.findall(file_pattern, body, re.IGNORECASE))
        
        # Count code blocks
        code_blocks = body.count('```')
        
        # Count dependency mentions
        dependency_pattern = r'(depends on|blocked by|requires|needs) #\d+'
        dependency_mentions = len(re.findall(dependency_pattern, body, re.IGNORECASE))
        
        # Check for refactor keywords
        has_refactor = any(kw in full_text for kw in self.REFACTOR_KEYWORDS)
        
        # Check for architecture keywords
        has_architecture = any(kw in full_text for kw in self.ARCHITECTURE_KEYWORDS)
        
        # Check for multi-component keywords
        has_multi_component = any(kw in full_text for kw in self.MULTI_COMPONENT_KEYWORDS)
        
        # Check labels
        has_complex_labels = any(label.lower() in self.COMPLEX_LABELS for label in labels)
        
        return ComplexitySignals(
            description_length=len(body),
            task_count=task_count,
            file_mentions=file_mentions,
            code_blocks=code_blocks,
            dependency_mentions=dependency_mentions,
            has_refactor_keywords=has_refactor,
            has_architecture_keywords=has_architecture,
            has_multi_component_keywords=has_multi_component,
            has_complex_labels=has_complex_labels
        )
    
    def _calculate_complexity_score(self, signals: ComplexitySignals) -> int:
        """
        Calculate complexity score from signals.
        
        Scoring:
        - Description length: 0-5 points
        - Task count: 0-10 points
        - File mentions: 0-8 points
        - Code blocks: 0-3 points
        - Dependencies: 0-5 points
        - Refactor keywords: 0-8 points
        - Architecture keywords: 0-10 points
        - Multi-component: 0-6 points
        - Complex labels: 0-10 points
        
        Total: 0-65 points
        """
        score = 0
        
        # Description length (0-5 points)
        if signals.description_length > 2000:
            score += 5
        elif signals.description_length > 1000:
            score += 3
        elif signals.description_length > 500:
            score += 1
        
        # Task count (0-10 points)
        if signals.task_count >= 10:
            score += 10
        elif signals.task_count >= 5:
            score += 6
        elif signals.task_count >= 3:
            score += 3
        
        # File mentions (0-8 points)
        if signals.file_mentions >= 8:
            score += 8
        elif signals.file_mentions >= 4:
            score += 5
        elif signals.file_mentions >= 2:
            score += 2
        
        # Code blocks (0-3 points)
        if signals.code_blocks >= 6:
            score += 3
        elif signals.code_blocks >= 3:
            score += 2
        
        # Dependencies (0-5 points)
        score += min(signals.dependency_mentions * 2, 5)
        
        # Keywords (0-8 points for refactor)
        if signals.has_refactor_keywords:
            score += 8
        
        # Keywords (0-10 points for architecture)
        if signals.has_architecture_keywords:
            score += 10
        
        # Keywords (0-6 points for multi-component)
        if signals.has_multi_component_keywords:
            score += 6
        
        # Complex labels (0-10 points)
        if signals.has_complex_labels:
            score += 10
        
        return score
    
    def _llm_semantic_analysis(self, title: str, body: str) -> Dict:
        """
        Use LLM for deeper semantic analysis (optional).
        
        This is a more expensive but more accurate analysis using LLM.
        """
        if not self.llm_agent:
            return {}
        
        prompt = f"""Analyze this GitHub issue and determine its complexity:

Title: {title}

Description:
{body[:1000]}  # Truncate to save tokens

Please analyze:
1. How many components/modules does this affect?
2. Are there architectural implications?
3. Does it require coordination between multiple concerns?
4. Estimated effort (hours)?

Respond with JSON:
{{
    "complexity": "simple|uncertain|complex",
    "confidence": 0.0-1.0,
    "reasoning": "brief explanation",
    "estimated_effort_hours": number,
    "requires_sub_issues": boolean
}}
"""
        
        try:
            response = self.llm_agent.query(prompt)
            # Parse LLM response (simplified - needs proper JSON parsing)
            # This would need proper implementation
            return {}
        except Exception as e:
            logger.warning(f"⚠️  LLM analysis failed: {e}")
            return {}
    
    def should_use_coordinator(self, analysis: Dict) -> bool:
        """Helper to check if coordinator should be used."""
        return analysis['routing'] == 'coordinator'
    
    def escalation_enabled(self, analysis: Dict) -> bool:
        """Helper to check if escalation is enabled."""
        return analysis.get('escalation_enabled', False)
