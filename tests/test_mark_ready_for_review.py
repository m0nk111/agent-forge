"""Tests for mark_ready_for_review functionality in PRReviewAgent."""

import unittest
from unittest.mock import Mock, patch, MagicMock
from engine.operations.pr_review_agent import PRReviewAgent


class TestMarkReadyForReview(unittest.TestCase):
    """Test suite for marking draft PRs as ready for review."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.agent = PRReviewAgent(
            github_token="test_token",
            bot_account="test-bot"
        )
    
    @patch.object(PRReviewAgent, '_github_request')
    def test_mark_ready_success(self, mock_request):
        """Test successfully marking PR as ready for review."""
        # Mock PR fetch
        pr_data = {
            'node_id': 'PR_test123',
            'draft': True,
            'number': 95
        }
        
        # Mock GraphQL response
        graphql_response = {
            'data': {
                'markPullRequestReadyForReview': {
                    'pullRequest': {
                        'isDraft': False
                    }
                }
            }
        }
        
        mock_request.side_effect = [
            (200, pr_data),  # PR fetch
            (200, graphql_response)  # GraphQL mutation
        ]
        
        result = self.agent.mark_ready_for_review('owner/repo', 95, 'tests passing')
        
        self.assertTrue(result)
        self.assertEqual(mock_request.call_count, 2)
    
    @patch.object(PRReviewAgent, '_github_request')
    def test_mark_ready_already_ready(self, mock_request):
        """Test marking PR that's already ready (should succeed idempotently)."""
        pr_data = {
            'node_id': 'PR_test123',
            'draft': False,  # Already ready
            'number': 95
        }
        
        mock_request.return_value = (200, pr_data)
        
        result = self.agent.mark_ready_for_review('owner/repo', 95)
        
        self.assertTrue(result)
        # Should only fetch PR, not call GraphQL
        self.assertEqual(mock_request.call_count, 1)
    
    @patch.object(PRReviewAgent, '_github_request')
    def test_mark_ready_pr_fetch_failed(self, mock_request):
        """Test failure when PR fetch fails."""
        mock_request.return_value = (404, None)
        
        result = self.agent.mark_ready_for_review('owner/repo', 95)
        
        self.assertFalse(result)
    
    @patch.object(PRReviewAgent, '_github_request')
    def test_mark_ready_missing_node_id(self, mock_request):
        """Test failure when PR missing node_id."""
        pr_data = {
            'draft': True,
            'number': 95
            # Missing node_id
        }
        
        mock_request.return_value = (200, pr_data)
        
        result = self.agent.mark_ready_for_review('owner/repo', 95)
        
        self.assertFalse(result)
    
    @patch.object(PRReviewAgent, '_github_request')
    def test_mark_ready_graphql_error(self, mock_request):
        """Test failure when GraphQL mutation fails."""
        pr_data = {
            'node_id': 'PR_test123',
            'draft': True,
            'number': 95
        }
        
        graphql_response = {
            'errors': [
                {'message': 'Permission denied'}
            ]
        }
        
        mock_request.side_effect = [
            (200, pr_data),
            (200, graphql_response)  # Has errors
        ]
        
        result = self.agent.mark_ready_for_review('owner/repo', 95)
        
        self.assertFalse(result)
    
    @patch.object(PRReviewAgent, '_github_request')
    def test_mark_ready_network_error(self, mock_request):
        """Test handling of network errors."""
        mock_request.side_effect = Exception("Network error")
        
        result = self.agent.mark_ready_for_review('owner/repo', 95)
        
        self.assertFalse(result)
    
    @patch.object(PRReviewAgent, '_github_request')
    def test_mark_ready_invalid_repo_format(self, mock_request):
        """Test handling of invalid repo format."""
        result = self.agent.mark_ready_for_review('invalid-repo', 95)
        
        self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()
