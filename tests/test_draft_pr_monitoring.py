"""Tests for draft PR monitoring in BotOperations."""

import unittest
from unittest.mock import Mock, patch, MagicMock
from engine.operations.bot_operations import BotOperations


class TestDraftPRMonitoring(unittest.TestCase):
    """Test suite for draft PR monitoring functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        with patch('engine.operations.bot_operations.get_account_manager'):
            with patch.object(BotOperations, '__init__', lambda x, y=None: None):
                self.bot = BotOperations()
                self.bot.username = 'test-bot'
                self.bot.owner = 'test-owner'
                self.bot.token = 'test_token'
                self.bot.headers = {'Authorization': 'Bearer test_token'}
    
    @patch('engine.operations.bot_operations.requests.get')
    def test_list_draft_prs_by_author(self, mock_get):
        """Test listing draft PRs by specific author."""
        # Mock PR list response
        prs_data = [
            {
                'number': 95,
                'draft': True,
                'user': {'login': 'test-bot'},
                'title': 'Test PR 1'
            },
            {
                'number': 96,
                'draft': False,  # Not draft
                'user': {'login': 'test-bot'},
                'title': 'Test PR 2'
            },
            {
                'number': 97,
                'draft': True,
                'user': {'login': 'other-user'},  # Different author
                'title': 'Test PR 3'
            }
        ]
        
        # Mock PR details response
        pr_details = {
            'number': 95,
            'draft': True,
            'latest_review_state': 'APPROVED',
            'critical_issues': [],
            'has_unresolved_issues': False
        }
        
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.side_effect = [prs_data, pr_details, [], []]
        mock_get.return_value = mock_response
        
        result = self.bot.list_draft_prs_by_author('test-repo')
        
        # Should return only draft PR by test-bot
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['number'], 95)
    
    @patch('engine.operations.bot_operations.requests.get')
    def test_get_pr_details_with_critical_issues(self, mock_get):
        """Test extracting critical issues from PR comments."""
        pr_data = {
            'number': 95,
            'draft': True,
            'title': 'Test PR'
        }
        
        reviews = [
            {'state': 'COMMENTED'},
            {'state': 'APPROVED'}
        ]
        
        comments = [
            {
                'body': '## Critical Issues\n❌ Missing docstring\n❌ Type hint error'
            },
            {
                'body': 'Looks good overall'
            }
        ]
        
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.side_effect = [pr_data, reviews, comments]
        mock_get.return_value = mock_response
        
        result = self.bot._get_pr_details('test-repo', 95)
        
        self.assertEqual(result['latest_review_state'], 'APPROVED')
        self.assertEqual(len(result['critical_issues']), 2)
        self.assertTrue(result['has_unresolved_issues'])
    
    def test_should_fix_draft_pr_approved_no_issues(self):
        """Test that approved PR with no issues should be fixed."""
        pr_data = {
            'number': 95,
            'latest_review_state': 'APPROVED',
            'has_unresolved_issues': False,
            'critical_issues': []
        }
        
        result = self.bot.should_fix_draft_pr(pr_data)
        
        self.assertTrue(result)
    
    def test_should_fix_draft_pr_approved_with_issues(self):
        """Test that approved PR with issues should NOT be auto-fixed yet."""
        pr_data = {
            'number': 95,
            'latest_review_state': 'APPROVED',
            'has_unresolved_issues': True,
            'critical_issues': ['❌ Missing docstring']
        }
        
        result = self.bot.should_fix_draft_pr(pr_data)
        
        self.assertFalse(result)  # For now, don't auto-fix
    
    def test_should_fix_draft_pr_not_approved(self):
        """Test that non-approved PR should not be fixed."""
        pr_data = {
            'number': 95,
            'latest_review_state': 'COMMENTED',
            'has_unresolved_issues': False,
            'critical_issues': []
        }
        
        result = self.bot.should_fix_draft_pr(pr_data)
        
        self.assertFalse(result)
    
    def test_should_fix_draft_pr_changes_requested(self):
        """Test that PR with changes requested should not be fixed."""
        pr_data = {
            'number': 95,
            'latest_review_state': 'CHANGES_REQUESTED',
            'has_unresolved_issues': True,
            'critical_issues': ['❌ Critical bug']
        }
        
        result = self.bot.should_fix_draft_pr(pr_data)
        
        self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()
