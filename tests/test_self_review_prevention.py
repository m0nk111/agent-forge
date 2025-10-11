"""Tests for self-review prevention in PR review agent."""

from unittest.mock import Mock, patch

import pytest

from engine.operations.pr_review_agent import PRReviewAgent


class TestSelfReviewPrevention:
    """Test self-review prevention mechanism."""
    
    @pytest.fixture
    def agent(self):
        """Create PR review agent for testing."""
        with patch('engine.operations.pr_review_agent.PRReviewAgent._load_github_token', return_value='test-token'):
            return PRReviewAgent(bot_account='post')
    
    def test_self_review_prevented(self, agent, caplog):
        """Test that bot cannot review own PR."""
        # Mock PR data showing PR author is same as reviewer
        mock_pr_data = {
            'number': 123,
            'user': {
                'login': 'm0nk111-post'  # Same as bot account
            },
            'head': {
                'sha': 'abc123'
            }
        }
        
        with patch.object(agent, '_github_request') as mock_request:
            # First call: get PR details
            mock_request.return_value = (200, mock_pr_data)
            
            # Try to review
            result = agent.complete_pr_review_and_merge_workflow(
                repo='owner/repo',
                pr_number=123
            )
            
            # Should be skipped
            assert result['skipped'] is True
            assert 'self-review' in result['reason'].lower()
            assert result['pr_author'] == 'm0nk111-post'
            assert result['reviewer'] == 'm0nk111-post'
            
            # Should log warning
            assert "self-review" in caplog.text.lower()
            assert "cannot review own pr" in caplog.text.lower()
    
    def test_different_author_allowed(self, agent):
        """Test that bot can review PRs from different authors."""
        # Mock PR data showing different author
        mock_pr_data = {
            'number': 123,
            'user': {
                'login': 'm0nk111-coder1'  # Different from reviewer (post)
            },
            'head': {
                'sha': 'abc123'
            },
            'draft': False
        }
        
        # Mock successful review
        mock_review_result = {
            'pr': 'owner/repo#123',
            'approved': True,
            'issues': [],
            'suggestions': [],
            'summary': 'All checks passed'
        }
        
        with patch.object(agent, '_github_request') as mock_request:
            with patch.object(agent, 'complete_pr_review_workflow') as mock_review:
                # First call: get PR details
                mock_request.return_value = (200, mock_pr_data)
                mock_review.return_value = {
                    'review_result': mock_review_result,
                    'errors': []
                }
                
                # Try to review
                result = agent.complete_pr_review_and_merge_workflow(
                    repo='owner/repo',
                    pr_number=123
                )
                
                # Should NOT be skipped
                assert result.get('skipped') is not True
                
                # Should have called review workflow
                mock_review.assert_called_once()
    
    def test_admin_account_mapping(self):
        """Test that 'admin' maps to m0nk111 account."""
        with patch('engine.operations.pr_review_agent.PRReviewAgent._load_github_token', return_value='test-token'):
            agent = PRReviewAgent(bot_account='admin')
            
            # Mock PR data
            mock_pr_data = {
                'user': {
                    'login': 'm0nk111-admin'  # Admin account
                }
            }
            
            with patch.object(agent, '_github_request') as mock_request:
                mock_request.return_value = (200, mock_pr_data)
                
                result = agent.complete_pr_review_and_merge_workflow(
                    repo='owner/repo',
                    pr_number=123
                )
                
                # Should prevent self-review
                assert result.get('skipped') is True
    
    def test_different_bot_accounts(self):
        """Test self-review prevention for different bot accounts."""
        accounts = ['post', 'coder1', 'coder2', 'qwen-agent']
        
        for account in accounts:
            with patch('engine.operations.pr_review_agent.PRReviewAgent._load_github_token', return_value='test-token'):
                agent = PRReviewAgent(bot_account=account)
                
                # Mock PR from same bot
                mock_pr_data = {
                    'user': {
                        'login': f'm0nk111-{account}'
                    }
                }
                
                with patch.object(agent, '_github_request') as mock_request:
                    mock_request.return_value = (200, mock_pr_data)
                    
                    result = agent.complete_pr_review_and_merge_workflow(
                        repo='owner/repo',
                        pr_number=123
                    )
                    
                    # Should prevent self-review
                    assert result.get('skipped') is True
                    assert f'm0nk111-{account}' in result['reason']
    
    def test_failed_pr_fetch(self, agent, caplog):
        """Test handling when PR fetch fails."""
        with patch.object(agent, '_github_request') as mock_request:
            # PR fetch fails
            mock_request.return_value = (404, None)
            
            # Should still attempt review (graceful degradation)
            with patch.object(agent, 'complete_pr_review_workflow') as mock_review:
                mock_review.return_value = {
                    'review_result': {
                        'approved': True,
                        'issues': [],
                        'suggestions': [],
                        'summary': 'OK'
                    },
                    'errors': []
                }
                
                result = agent.complete_pr_review_and_merge_workflow(
                    repo='owner/repo',
                    pr_number=123
                )
                
                # Should continue with review (no pr_data to check author)
                mock_review.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
