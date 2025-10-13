"""
Consensus Engine for Multi-LLM Decision Making

This module implements a weighted voting system to reach consensus among multiple
LLM responses. It handles confidence scoring, conflict resolution, and decision
making based on configurable thresholds.

Architecture:
- Weighted voting based on provider weights and confidence scores
- Minimum confidence threshold (default 0.6)
- Minimum agreement requirement (default 2+ LLMs)
- Conflict detection and resolution strategies
- Similarity analysis for grouping similar fixes

Usage:
    engine = ConsensusEngine(min_confidence=0.6, min_agreement=2)
    decision = engine.reach_consensus(llm_responses, provider_weights)
"""

import os
import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict
import difflib

from engine.operations.multi_llm_orchestrator import LLMResponse, LLMProvider

# Debug flag
DEBUG = os.getenv('DEBUG', 'false').lower() == 'true'

logger = logging.getLogger(__name__)


@dataclass
class ConsensusDecision:
    """Result of consensus analysis"""
    has_consensus: bool
    chosen_fix: str
    confidence: float
    supporting_providers: List[LLMProvider]
    total_weight: float
    reasoning: str
    alternatives: List[Tuple[str, float, List[LLMProvider]]]  # (fix, weight, providers)
    conflicts: List[str]


class ConsensusEngine:
    """Implements weighted voting consensus for multi-LLM decisions"""
    
    def __init__(
        self,
        min_confidence: float = 0.6,
        min_agreement: int = 2,
        similarity_threshold: float = 0.7
    ):
        """
        Initialize consensus engine
        
        Args:
            min_confidence: Minimum weighted confidence required (0.0 to 1.0)
            min_agreement: Minimum number of LLMs that must agree
            similarity_threshold: How similar fixes must be to group (0.0 to 1.0)
        """
        self.min_confidence = min_confidence
        self.min_agreement = min_agreement
        self.similarity_threshold = similarity_threshold
        
        if DEBUG:
            logger.debug(f"🔍 ConsensusEngine initialized")
            logger.debug(f"  - Min confidence: {min_confidence}")
            logger.debug(f"  - Min agreement: {min_agreement} LLMs")
            logger.debug(f"  - Similarity threshold: {similarity_threshold}")
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate similarity between two text strings
        
        Uses SequenceMatcher for code similarity comparison
        
        Args:
            text1: First text
            text2: Second text
        
        Returns:
            Similarity score (0.0 to 1.0)
        """
        if not text1 or not text2:
            return 0.0
        
        # Normalize whitespace
        normalized1 = ' '.join(text1.split())
        normalized2 = ' '.join(text2.split())
        
        # Calculate similarity
        matcher = difflib.SequenceMatcher(None, normalized1, normalized2)
        similarity = matcher.ratio()
        
        return similarity
    
    def _group_similar_fixes(
        self,
        responses: List[LLMResponse],
        provider_weights: Dict[LLMProvider, float]
    ) -> List[Dict]:
        """
        Group similar proposed fixes together
        
        Args:
            responses: List of LLM responses
            provider_weights: Weight for each provider
        
        Returns:
            List of groups, each containing:
                - fix: Representative fix text
                - providers: List of supporting providers
                - confidences: List of confidence scores
                - weights: List of provider weights
                - total_weight: Sum of weights
                - avg_confidence: Average confidence
        """
        groups = []
        
        for response in responses:
            # Skip responses with errors or empty fixes
            if response.error or not response.proposed_fix:
                continue
            
            # Find matching group
            matched = False
            for group in groups:
                similarity = self._calculate_similarity(
                    response.proposed_fix,
                    group['fix']
                )
                
                if similarity >= self.similarity_threshold:
                    # Add to existing group
                    group['providers'].append(response.provider)
                    group['confidences'].append(response.confidence)
                    weight = provider_weights.get(response.provider, 0.5)
                    group['weights'].append(weight)
                    group['total_weight'] += weight * response.confidence
                    group['responses'].append(response)
                    matched = True
                    
                    if DEBUG:
                        logger.debug(f"🔍 Grouped {response.provider.value} with existing group (similarity: {similarity:.2f})")
                    break
            
            if not matched:
                # Create new group
                weight = provider_weights.get(response.provider, 0.5)
                groups.append({
                    'fix': response.proposed_fix,
                    'providers': [response.provider],
                    'confidences': [response.confidence],
                    'weights': [weight],
                    'total_weight': weight * response.confidence,
                    'responses': [response]
                })
                
                if DEBUG:
                    logger.debug(f"🆕 Created new group for {response.provider.value}")
        
        # Calculate average confidence for each group
        for group in groups:
            group['avg_confidence'] = sum(group['confidences']) / len(group['confidences'])
        
        # Sort groups by total weight (descending)
        groups.sort(key=lambda g: g['total_weight'], reverse=True)
        
        return groups
    
    def _detect_conflicts(
        self,
        groups: List[Dict]
    ) -> List[str]:
        """
        Detect significant conflicts between proposed fixes
        
        Args:
            groups: List of fix groups
        
        Returns:
            List of conflict descriptions
        """
        conflicts = []
        
        # Check if top groups have similar weights
        if len(groups) >= 2:
            top_weight = groups[0]['total_weight']
            second_weight = groups[1]['total_weight']
            
            # Conflict if second group is within 20% of top
            if second_weight >= top_weight * 0.8:
                conflicts.append(
                    f"Close decision: Top fix has weight {top_weight:.2f}, "
                    f"second has {second_weight:.2f} (within 20%)"
                )
                
                if DEBUG:
                    logger.debug(f"⚠️ Detected close decision conflict")
        
        # Check for low confidence even in top group
        if groups and groups[0]['avg_confidence'] < 0.7:
            conflicts.append(
                f"Low confidence: Top fix has average confidence {groups[0]['avg_confidence']:.2f}"
            )
            
            if DEBUG:
                logger.debug(f"⚠️ Detected low confidence in top group")
        
        # Check for disagreement (many small groups)
        if len(groups) >= 4:
            conflicts.append(
                f"High disagreement: {len(groups)} different fix proposals"
            )
            
            if DEBUG:
                logger.debug(f"⚠️ Detected high disagreement ({len(groups)} groups)")
        
        return conflicts
    
    def reach_consensus(
        self,
        responses: List[LLMResponse],
        provider_weights: Dict[LLMProvider, float]
    ) -> ConsensusDecision:
        """
        Reach consensus among multiple LLM responses
        
        Args:
            responses: List of LLM responses
            provider_weights: Weight for each provider
        
        Returns:
            ConsensusDecision with consensus result
        """
        if DEBUG:
            logger.debug(f"🔍 Analyzing {len(responses)} responses for consensus")
        
        # Filter out error responses
        valid_responses = [r for r in responses if not r.error and r.proposed_fix]
        
        if not valid_responses:
            logger.error("❌ No valid responses to analyze")
            return ConsensusDecision(
                has_consensus=False,
                chosen_fix="",
                confidence=0.0,
                supporting_providers=[],
                total_weight=0.0,
                reasoning="No valid responses from any provider",
                alternatives=[],
                conflicts=["All providers failed or returned empty fixes"]
            )
        
        # Group similar fixes
        groups = self._group_similar_fixes(valid_responses, provider_weights)
        
        if DEBUG:
            logger.debug(f"📊 Grouped into {len(groups)} similar fix proposals")
            for i, group in enumerate(groups):
                logger.debug(f"  Group {i+1}: {len(group['providers'])} providers, weight {group['total_weight']:.2f}")
        
        # Detect conflicts
        conflicts = self._detect_conflicts(groups)
        
        # Check if top group meets consensus requirements
        if not groups:
            return ConsensusDecision(
                has_consensus=False,
                chosen_fix="",
                confidence=0.0,
                supporting_providers=[],
                total_weight=0.0,
                reasoning="No fix proposals to evaluate",
                alternatives=[],
                conflicts=["No proposed fixes"]
            )
        
        top_group = groups[0]
        num_supporters = len(top_group['providers'])
        total_weight = top_group['total_weight']
        avg_confidence = top_group['avg_confidence']
        
        # Calculate weighted confidence (weight × confidence)
        # Normalize by sum of all supporting provider weights
        sum_weights = sum(top_group['weights'])
        weighted_confidence = total_weight / sum_weights if sum_weights > 0 else 0.0
        
        # Check consensus criteria
        has_consensus = (
            num_supporters >= self.min_agreement and
            weighted_confidence >= self.min_confidence
        )
        
        # Build alternatives list (other groups)
        alternatives = [
            (
                group['fix'],
                group['total_weight'],
                group['providers']
            )
            for group in groups[1:]
        ]
        
        # Build reasoning
        if has_consensus:
            reasoning = (
                f"Consensus reached with {num_supporters} LLMs agreeing "
                f"(weighted confidence: {weighted_confidence:.2f}). "
                f"Supporting providers: {', '.join([p.value for p in top_group['providers']])}."
            )
            
            if conflicts:
                reasoning += f" Note: {'; '.join(conflicts)}"
            
            if DEBUG:
                logger.debug(f"✅ Consensus reached!")
                logger.debug(f"  - Supporters: {num_supporters}")
                logger.debug(f"  - Weighted confidence: {weighted_confidence:.2f}")
                logger.debug(f"  - Providers: {', '.join([p.value for p in top_group['providers']])}")
        else:
            reasons = []
            if num_supporters < self.min_agreement:
                reasons.append(f"only {num_supporters} LLMs agree (need {self.min_agreement})")
            if weighted_confidence < self.min_confidence:
                reasons.append(f"weighted confidence {weighted_confidence:.2f} below threshold {self.min_confidence}")
            
            reasoning = f"No consensus: {'; '.join(reasons)}."
            
            if alternatives:
                reasoning += (
                    f" Alternative fixes proposed by: "
                    f"{', '.join([p.value for providers in [alt[2] for alt in alternatives] for p in providers])}."
                )
            
            if conflicts:
                reasoning += f" Conflicts: {'; '.join(conflicts)}"
            
            if DEBUG:
                logger.debug(f"❌ No consensus")
                logger.debug(f"  - Reasons: {'; '.join(reasons)}")
        
        return ConsensusDecision(
            has_consensus=has_consensus,
            chosen_fix=top_group['fix'] if has_consensus else "",
            confidence=weighted_confidence,
            supporting_providers=top_group['providers'],
            total_weight=total_weight,
            reasoning=reasoning,
            alternatives=alternatives,
            conflicts=conflicts
        )
    
    def explain_decision(self, decision: ConsensusDecision) -> str:
        """
        Generate human-readable explanation of consensus decision
        
        Args:
            decision: ConsensusDecision to explain
        
        Returns:
            Formatted explanation string
        """
        lines = []
        lines.append("="*80)
        lines.append("CONSENSUS DECISION")
        lines.append("="*80)
        
        if decision.has_consensus:
            lines.append("✅ CONSENSUS REACHED")
            lines.append(f"Confidence: {decision.confidence:.2f}")
            lines.append(f"Total Weight: {decision.total_weight:.2f}")
            lines.append(f"Supporting Providers: {', '.join([p.value for p in decision.supporting_providers])}")
            lines.append(f"\nReasoning:\n{decision.reasoning}")
            lines.append(f"\nChosen Fix:\n{decision.chosen_fix}")
            
            if decision.alternatives:
                lines.append(f"\nAlternative Fixes Considered:")
                for i, (fix, weight, providers) in enumerate(decision.alternatives, 1):
                    lines.append(f"\n  Alternative {i} (weight: {weight:.2f}):")
                    lines.append(f"  Providers: {', '.join([p.value for p in providers])}")
                    lines.append(f"  Fix: {fix[:200]}...")
        else:
            lines.append("❌ NO CONSENSUS")
            lines.append(f"Confidence: {decision.confidence:.2f}")
            lines.append(f"Total Weight: {decision.total_weight:.2f}")
            lines.append(f"\nReasoning:\n{decision.reasoning}")
            
            if decision.alternatives:
                lines.append(f"\nProposed Fixes:")
                for i, (fix, weight, providers) in enumerate(decision.alternatives, 1):
                    lines.append(f"\n  Proposal {i} (weight: {weight:.2f}):")
                    lines.append(f"  Providers: {', '.join([p.value for p in providers])}")
                    lines.append(f"  Fix: {fix[:200]}...")
        
        if decision.conflicts:
            lines.append(f"\n⚠️ Conflicts Detected:")
            for conflict in decision.conflicts:
                lines.append(f"  - {conflict}")
        
        lines.append("="*80)
        
        return "\n".join(lines)


# CLI for testing
if __name__ == "__main__":
    import argparse
    import json
    from engine.operations.multi_llm_orchestrator import LLMProvider
    
    parser = argparse.ArgumentParser(description="Test Consensus Engine")
    parser.add_argument("--responses", required=True, help="JSON file with LLM responses")
    parser.add_argument("--min-confidence", type=float, default=0.6, help="Minimum confidence threshold")
    parser.add_argument("--min-agreement", type=int, default=2, help="Minimum LLMs that must agree")
    parser.add_argument("--similarity", type=float, default=0.7, help="Similarity threshold for grouping")
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
        os.environ['DEBUG'] = 'true'
    else:
        logging.basicConfig(level=logging.INFO)
    
    # Load responses from JSON
    with open(args.responses, 'r') as f:
        responses_data = json.load(f)
    
    # Convert to LLMResponse objects
    responses = []
    provider_weights = {}
    
    for data in responses_data:
        provider = LLMProvider(data['provider'])
        responses.append(LLMResponse(
            provider=provider,
            analysis=data.get('analysis', ''),
            proposed_fix=data.get('proposed_fix', ''),
            confidence=data.get('confidence', 0.5),
            reasoning=data.get('reasoning', ''),
            error=data.get('error')
        ))
        provider_weights[provider] = data.get('weight', 0.5)
    
    # Run consensus engine
    engine = ConsensusEngine(
        min_confidence=args.min_confidence,
        min_agreement=args.min_agreement,
        similarity_threshold=args.similarity
    )
    
    decision = engine.reach_consensus(responses, provider_weights)
    
    # Print explanation
    print(engine.explain_decision(decision))
