"""Tests for creative status generator."""

import pytest
from engine.operations.creative_status import generate_issue_motif


class TestCreativeStatus:
    """Test creative status generator functionality."""
    
    def test_generate_bug_motif(self):
        """Test bug-themed motif generation."""
        motif = generate_issue_motif("Fix login bug", ["bug", "agent-ready"])
        
        # Verify output structure
        assert isinstance(motif, str)
        lines = motif.split('\n')
        assert len(lines) == 3
        
        # Verify theme selection (bug theme)
        assert any(emoji in motif for emoji in ["🐛"])
        
    def test_generate_docs_motif(self):
        """Test docs-themed motif generation."""
        motif = generate_issue_motif("Write installation guide", ["docs", "documentation"])
        
        # Verify output structure
        assert isinstance(motif, str)
        lines = motif.split('\n')
        assert len(lines) == 3
        
        # Verify theme selection (docs theme)
        assert any(emoji in motif for emoji in ["📚"])
    
    def test_generate_ops_motif(self):
        """Test ops-themed motif generation."""
        motif = generate_issue_motif("Deploy monitoring service", ["ops", "infrastructure"])
        
        # Verify output structure
        assert isinstance(motif, str)
        lines = motif.split('\n')
        assert len(lines) == 3
        
        # Verify theme selection (ops theme)
        assert any(emoji in motif for emoji in ["🛠️", "🛰️", "🛎️"])
    
    def test_generate_default_motif(self):
        """Test default-themed motif generation."""
        motif = generate_issue_motif("Add new feature", ["enhancement"])
        
        # Verify output structure
        assert isinstance(motif, str)
        lines = motif.split('\n')
        assert len(lines) == 3
        
        # Verify theme selection (default theme)
        assert any(emoji in motif for emoji in ["✨", "🌟", "🎨"])
    
    def test_deterministic_output(self):
        """Test that output is deterministic for same inputs."""
        title = "Fix login bug"
        labels = ["bug", "critical"]
        
        motif1 = generate_issue_motif(title, labels)
        motif2 = generate_issue_motif(title, labels)
        
        # Same input should produce same output
        assert motif1 == motif2
    
    def test_different_titles_different_output(self):
        """Test that different titles produce different outputs."""
        labels = ["bug"]
        
        motif1 = generate_issue_motif("Fix login bug", labels)
        motif2 = generate_issue_motif("Refactor authentication system", labels)
        
        # Different titles with significantly different character sums should produce different outputs
        assert motif1 != motif2
    
    def test_empty_labels(self):
        """Test motif generation with no labels."""
        motif = generate_issue_motif("Some task", [])
        
        # Should default to default theme
        assert isinstance(motif, str)
        lines = motif.split('\n')
        assert len(lines) == 3
    
    def test_mixed_case_labels(self):
        """Test that label matching is case-insensitive."""
        motif1 = generate_issue_motif("Task", ["BUG"])
        motif2 = generate_issue_motif("Task", ["bug"])
        
        # Should select same theme regardless of case
        # (Both should use bug theme, so output should be identical)
        assert motif1 == motif2
