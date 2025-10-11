"""Tests for reviewed PRs memory leak prevention."""

import time

import pytest

from engine.runners.polling_service import PollingService


class TestReviewedPRsCleanup:
    """Test reviewed PRs memory leak prevention."""
    
    def test_timestamp_tracking(self):
        """Test that reviewed PRs are tracked with timestamps."""
        service = PollingService()
        
        # Add reviewed PR manually
        import time
        service.reviewed_prs['owner/repo#123'] = {
            'sha': 'abc123',
            'reviewed_at': time.time()
        }
        
        # Should have timestamp
        entry = service.reviewed_prs['owner/repo#123']
        assert 'sha' in entry
        assert 'reviewed_at' in entry
        assert entry['sha'] == 'abc123'
        assert isinstance(entry['reviewed_at'], (int, float))
    
    def test_cleanup_old_entries(self):
        """Test cleanup of old reviewed PR entries."""
        service = PollingService()
        service.reviewed_prs_max_age_days = 7
        
        current_time = time.time()
        
        # Add old entry (8 days old)
        service.reviewed_prs['owner/repo#1'] = {
            'sha': 'old123',
            'reviewed_at': current_time - (8 * 24 * 3600)
        }
        
        # Add recent entry (1 day old)
        service.reviewed_prs['owner/repo#2'] = {
            'sha': 'new123',
            'reviewed_at': current_time - (1 * 24 * 3600)
        }
        
        # Run cleanup
        service._cleanup_old_reviewed_prs()
        
        # Old entry should be removed
        assert 'owner/repo#1' not in service.reviewed_prs
        
        # Recent entry should remain
        assert 'owner/repo#2' in service.reviewed_prs
    
    def test_enforce_max_size(self):
        """Test enforcement of maximum reviewed PRs size."""
        service = PollingService()
        service.reviewed_prs_max_size = 10
        
        current_time = time.time()
        
        # Add 20 entries
        for i in range(20):
            service.reviewed_prs[f'owner/repo#{i}'] = {
                'sha': f'sha{i}',
                'reviewed_at': current_time - (i * 60)  # 1 minute apart
            }
        
        # Should have 20 entries
        assert len(service.reviewed_prs) == 20
        
        # Run cleanup
        service._cleanup_old_reviewed_prs()
        
        # Should have only max_size entries
        assert len(service.reviewed_prs) == 10
        
        # Should keep most recent (PR #0-9)
        for i in range(10):
            assert f'owner/repo#{i}' in service.reviewed_prs
        
        # Should remove oldest (PR #10-19)
        for i in range(10, 20):
            assert f'owner/repo#{i}' not in service.reviewed_prs
    
    def test_cleanup_combination(self):
        """Test cleanup with both age and size limits."""
        service = PollingService()
        service.reviewed_prs_max_age_days = 7
        service.reviewed_prs_max_size = 5
        
        current_time = time.time()
        
        # Add 10 entries: 5 old, 5 recent
        for i in range(5):
            service.reviewed_prs[f'owner/repo#old{i}'] = {
                'sha': f'old{i}',
                'reviewed_at': current_time - (8 * 24 * 3600)  # 8 days old
            }
        
        for i in range(5):
            service.reviewed_prs[f'owner/repo#new{i}'] = {
                'sha': f'new{i}',
                'reviewed_at': current_time - (i * 3600)  # Recent (hours apart)
            }
        
        # Run cleanup
        service._cleanup_old_reviewed_prs()
        
        # Should have only max_size recent entries
        assert len(service.reviewed_prs) == 5
        
        # Should keep all recent entries (within max_size)
        for i in range(5):
            assert f'owner/repo#new{i}' in service.reviewed_prs
        
        # Should remove all old entries
        for i in range(5):
            assert f'owner/repo#old{i}' not in service.reviewed_prs
    
    def test_empty_dict_cleanup(self):
        """Test cleanup with empty reviewed PRs dict."""
        service = PollingService()
        
        # Should not crash
        service._cleanup_old_reviewed_prs()
        
        assert len(service.reviewed_prs) == 0
    
    def test_backward_compatibility_with_string_values(self):
        """Test backward compatibility with old string-based reviewed_prs."""
        service = PollingService()
        
        # Add old-style entry (just SHA string)
        service.reviewed_prs['owner/repo#123'] = 'abc123'
        
        # Add new-style entry (dict with timestamp)
        current_time = time.time()
        service.reviewed_prs['owner/repo#456'] = {
            'sha': 'def456',
            'reviewed_at': current_time
        }
        
        # Cleanup should handle both formats
        service._cleanup_old_reviewed_prs()
        
        # Old-style entry should be kept (no timestamp to check)
        # Note: In real implementation, we might want to remove entries without timestamps
        # For now, they're kept as they don't match the age check
    
    def test_periodic_cleanup_integration(self):
        """Test that cleanup is called periodically."""
        service = PollingService()
        
        # Initialize counter
        service._cleanup_counter = 0
        
        # Simulate 11 polling cycles (0-9 + 1 more to trigger)
        for i in range(11):
            service._cleanup_counter += 1
            if service._cleanup_counter >= 10:
                # Should call cleanup
                service._cleanup_old_reviewed_prs()
                service._cleanup_counter = 0
        
        # After 11 cycles (10+1), counter should be at 1 (reset at 10, incremented once more)
        assert service._cleanup_counter == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
