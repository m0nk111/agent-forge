"""
Context window management for Qwen agent.

Manages sliding context window to stay within token limits while
providing relevant historical context for tasks.

Author: Agent Forge
"""

from typing import Dict, List, Optional, Tuple
from pathlib import Path
import re


class ContextManager:
    """
    Manage context window to stay within model token limits.
    
    Features:
    - Track task history with code and results
    - Smart truncation when approaching token limit
    - Prioritize recent and relevant context
    - Token counting approximation (4 chars ≈ 1 token)
    """
    
    def __init__(self, max_tokens: int = 6000):
        """
        Initialize context manager.
        
        Args:
            max_tokens: Maximum tokens for context (default 6000, leaving room for prompts)
        """
        self.max_tokens = max_tokens
        self.task_history: List[Dict[str, str]] = []
        self.total_tokens = 0
        self.truncation_events = 0
        
    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text.
        
        Uses approximation: ~4 characters per token
        This is conservative for English text with code.
        
        Args:
            text: Text to estimate tokens for
            
        Returns:
            Estimated token count
        """
        return len(text) // 4
    
    def add_task_result(
        self,
        task_description: str,
        code_generated: str,
        success: bool,
        phase_name: str = ""
    ) -> None:
        """
        Add task result to history.
        
        Args:
            task_description: Description of the task
            code_generated: Code that was generated (or empty if failed)
            success: Whether task succeeded
            phase_name: Name of the phase this task belongs to
        """
        entry = {
            'task': task_description,
            'code': code_generated,
            'success': success,
            'phase': phase_name,
            'tokens': self.estimate_tokens(task_description + code_generated)
        }
        
        self.task_history.append(entry)
        self.total_tokens += entry['tokens']
        
        # Trim if exceeding limit
        if self.total_tokens > self.max_tokens:
            self._trim_to_limit()
    
    def _trim_to_limit(self) -> None:
        """
        Remove oldest context entries until within token limit.
        
        Strategy:
        1. Keep most recent tasks (last 3)
        2. Keep successful tasks over failed ones
        3. Remove oldest entries first
        """
        if not self.task_history:
            return
        
        # Always keep last 3 tasks (most relevant)
        protected_count = min(3, len(self.task_history))
        
        # Calculate current total
        self.total_tokens = sum(entry['tokens'] for entry in self.task_history)
        
        # Remove oldest non-protected entries until under limit
        while self.total_tokens > self.max_tokens and len(self.task_history) > protected_count:
            # Find oldest non-protected entry, prefer failed tasks
            candidates = self.task_history[:-protected_count]
            
            # Prioritize removing failed tasks
            failed = [i for i, entry in enumerate(candidates) if not entry['success']]
            if failed:
                remove_idx = failed[0]
            else:
                remove_idx = 0
            
            removed = self.task_history.pop(remove_idx)
            self.total_tokens -= removed['tokens']
            self.truncation_events += 1
    
    def get_context_summary(self, max_entries: int = 5) -> str:
        """
        Get formatted summary of recent task history.
        
        Args:
            max_entries: Maximum number of entries to include
            
        Returns:
            Formatted context string for prompt injection
        """
        if not self.task_history:
            return ""
        
        # Get most recent entries
        recent = self.task_history[-max_entries:]
        
        lines = ["\n📚 RECENT TASK HISTORY:"]
        
        for i, entry in enumerate(recent, 1):
            status = "✅" if entry['success'] else "❌"
            phase = f"[{entry['phase']}]" if entry['phase'] else ""
            lines.append(f"{i}. {status} {phase} {entry['task']}")
            
            # Include code snippet for successful tasks
            if entry['success'] and entry['code']:
                # Truncate code if too long
                code = entry['code']
                if len(code) > 500:
                    code = code[:500] + "\n... (truncated)"
                lines.append(f"   Code: {code[:200]}...")
        
        lines.append(f"\nContext: {len(self.task_history)} tasks, ~{self.total_tokens} tokens")
        
        return "\n".join(lines)
    
    def get_relevant_context(
        self,
        current_task: str,
        max_tokens: int = 2000
    ) -> str:
        """
        Get most relevant context for current task.
        
        Uses keyword matching to find related previous tasks.
        
        Args:
            current_task: Description of current task
            max_tokens: Maximum tokens to return
            
        Returns:
            Formatted relevant context string
        """
        if not self.task_history:
            return ""
        
        # Extract keywords from current task
        keywords = self._extract_keywords(current_task.lower())
        
        # Score each history entry by keyword relevance
        scored = []
        for entry in self.task_history:
            task_lower = entry['task'].lower()
            score = sum(1 for kw in keywords if kw in task_lower)
            if score > 0:
                scored.append((score, entry))
        
        # Sort by relevance (score) and recency
        scored.sort(key=lambda x: (x[0], self.task_history.index(x[1])), reverse=True)
        
        # Build context string within token budget
        lines = []
        tokens_used = 0
        
        for score, entry in scored:
            entry_text = f"{entry['task']}\n{entry['code'][:300]}..."
            entry_tokens = self.estimate_tokens(entry_text)
            
            if tokens_used + entry_tokens > max_tokens:
                break
            
            status = "✅" if entry['success'] else "❌"
            lines.append(f"{status} {entry['task']}")
            if entry['code']:
                lines.append(f"   {entry['code'][:200]}...")
            
            tokens_used += entry_tokens
        
        if lines:
            return "\n🔍 RELEVANT PREVIOUS TASKS:\n" + "\n".join(lines) + "\n"
        else:
            return ""
    
    def _extract_keywords(self, text: str) -> List[str]:
        """
        Extract meaningful keywords from text.
        
        Args:
            text: Text to extract keywords from
            
        Returns:
            List of keywords
        """
        # Remove common words
        stopwords = {
            'a', 'an', 'the', 'is', 'are', 'was', 'were', 'be', 'been',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
            'should', 'could', 'can', 'may', 'might', 'must', 'for', 'and',
            'or', 'but', 'in', 'on', 'at', 'to', 'from', 'with', 'by'
        }
        
        # Extract words (alphanumeric + hyphens)
        words = re.findall(r'\b[\w-]+\b', text)
        
        # Filter stopwords and short words
        keywords = [w for w in words if len(w) > 2 and w not in stopwords]
        
        return keywords
    
    def get_metrics(self) -> Dict[str, any]:
        """
        Get context management metrics.
        
        Returns:
            Dict with metrics (task_count, total_tokens, truncation_events)
        """
        return {
            'task_count': len(self.task_history),
            'total_tokens': self.total_tokens,
            'max_tokens': self.max_tokens,
            'truncation_events': self.truncation_events,
            'usage_percent': (self.total_tokens / self.max_tokens * 100) if self.max_tokens > 0 else 0
        }
    
    def clear(self) -> None:
        """Clear all context history."""
        self.task_history.clear()
        self.total_tokens = 0
        self.truncation_events = 0


# Test harness
if __name__ == '__main__':
    print("🧪 Testing ContextManager...\n")
    
    cm = ContextManager(max_tokens=1000)  # Small limit for testing
    
    # Add some tasks
    cm.add_task_result(
        task_description="Create app/services/test/ directory",
        code_generated="mkdir -p app/services/test",
        success=True,
        phase_name="Phase 1"
    )
    
    cm.add_task_result(
        task_description="Create __init__.py file",
        code_generated="# Test service\n\nfrom .service import TestService\n\n" * 20,  # Long code
        success=True,
        phase_name="Phase 1"
    )
    
    cm.add_task_result(
        task_description="Add API endpoint for test",
        code_generated="@app.get('/api/test')\nasync def test_endpoint():\n    return {'status': 'ok'}",
        success=True,
        phase_name="Phase 2"
    )
    
    cm.add_task_result(
        task_description="Fix import error",
        code_generated="",
        success=False,
        phase_name="Phase 2"
    )
    
    # Test metrics
    print("📊 Metrics after adding tasks:")
    metrics = cm.get_metrics()
    for key, value in metrics.items():
        print(f"   {key}: {value}")
    
    # Test context summary
    print(f"\n{cm.get_context_summary()}")
    
    # Test relevant context
    print("\n" + "="*60)
    print("Relevant context for 'Create new API endpoint':")
    print(cm.get_relevant_context("Create new API endpoint for users"))
    
    # Add many more tasks to trigger truncation
    print("\n" + "="*60)
    print("Adding 10 more tasks to trigger truncation...")
    for i in range(10):
        cm.add_task_result(
            task_description=f"Task {i+5}: Do something {i}",
            code_generated=f"# Code for task {i}\n" * 50,
            success=(i % 2 == 0),
            phase_name=f"Phase {i//3 + 1}"
        )
    
    print(f"\n📊 Metrics after truncation:")
    metrics = cm.get_metrics()
    for key, value in metrics.items():
        print(f"   {key}: {value}")
    
    print(f"\n{cm.get_context_summary()}")
    
    print("\n✅ ContextManager tests completed!")
