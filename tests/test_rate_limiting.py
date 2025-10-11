"""Tests for GitHub API rate limit handling in PR review agent."""

import time
from unittest.mock import Mock, patch

import pytest

from engine.operations.pr_review_agent import PRReviewAgent


class TestRateLimitHandling:
    """Test GitHub API rate limit handling."""
    
    @pytest.fixture
    def agent(self):
        """Create PR review agent for testing."""
        with patch('engine.operations.pr_review_agent.PRReviewAgent._load_github_token', return_value='test-token'):
            return PRReviewAgent()
    
    def test_successful_request(self, agent):
        """Test successful API request."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '{"key": "value"}'
        mock_response.json.return_value = {"key": "value"}
        mock_response.headers = {
            'X-RateLimit-Remaining': '5000',
            'X-RateLimit-Reset': str(int(time.time()) + 3600)
        }
        
        with patch('requests.get', return_value=mock_response):
            status, data = agent._github_request('GET', 'https://api.github.com/test')
            
            assert status == 200
            assert data == {"key": "value"}
    
    def test_rate_limit_warning(self, agent, caplog):
        """Test warning when rate limit is low."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '{"key": "value"}'
        mock_response.json.return_value = {"key": "value"}
        mock_response.headers = {
            'X-RateLimit-Remaining': '50',  # Low remaining
            'X-RateLimit-Reset': str(int(time.time()) + 3600)
        }
        
        with patch('requests.get', return_value=mock_response):
            status, data = agent._github_request('GET', 'https://api.github.com/test')
            
            assert status == 200
            assert "rate limit low" in caplog.text.lower()
    
    def test_429_retry_after(self, agent, caplog):
        """Test 429 response with Retry-After header."""
        # First request returns 429
        mock_response_429 = Mock()
        mock_response_429.status_code = 429
        mock_response_429.headers = {
            'Retry-After': '1',  # Short wait for testing
            'X-RateLimit-Remaining': '0',
            'X-RateLimit-Reset': str(int(time.time()) + 60)
        }
        
        # Second request succeeds
        mock_response_200 = Mock()
        mock_response_200.status_code = 200
        mock_response_200.text = '{"key": "value"}'
        mock_response_200.json.return_value = {"key": "value"}
        mock_response_200.headers = {
            'X-RateLimit-Remaining': '4999',
            'X-RateLimit-Reset': str(int(time.time()) + 3600)
        }
        
        with patch('requests.get', side_effect=[mock_response_429, mock_response_200]):
            with patch('time.sleep') as mock_sleep:  # Don't actually sleep in tests
                status, data = agent._github_request('GET', 'https://api.github.com/test')
                
                # Should succeed after retry
                assert status == 200
                assert data == {"key": "value"}
                
                # Should have waited
                mock_sleep.assert_called_once_with(1)
    
    def test_429_max_retries(self, agent, caplog):
        """Test 429 exhausts max retries."""
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.headers = {
            'Retry-After': '1',
            'X-RateLimit-Remaining': '0'
        }
        
        with patch('requests.get', return_value=mock_response):
            with patch('time.sleep'):  # Don't actually sleep
                status, data = agent._github_request('GET', 'https://api.github.com/test', max_retries=2)
                
                # Should fail after max retries
                assert status == 429
                assert data is None
                assert "max retries" in caplog.text.lower()
    
    def test_403_rate_limit_exceeded(self, agent, caplog):
        """Test 403 response when rate limit is exceeded."""
        # First request returns 403 with rate limit headers
        mock_response_403 = Mock()
        mock_response_403.status_code = 403
        mock_response_403.headers = {
            'X-RateLimit-Remaining': '0',
            'X-RateLimit-Reset': str(int(time.time()) + 1)  # Short wait for testing
        }
        
        # Second request succeeds
        mock_response_200 = Mock()
        mock_response_200.status_code = 200
        mock_response_200.text = '{"key": "value"}'
        mock_response_200.json.return_value = {"key": "value"}
        mock_response_200.headers = {
            'X-RateLimit-Remaining': '5000',
            'X-RateLimit-Reset': str(int(time.time()) + 3600)
        }
        
        with patch('requests.get', side_effect=[mock_response_403, mock_response_200]):
            with patch('time.sleep') as mock_sleep:  # Don't actually sleep
                status, data = agent._github_request('GET', 'https://api.github.com/test')
                
                # Should succeed after retry
                assert status == 200
                
                # Should have waited for reset + buffer
                assert mock_sleep.called
                wait_time = mock_sleep.call_args[0][0]
                assert wait_time >= 1  # At least the reset time
    
    def test_403_not_rate_limit(self, agent, caplog):
        """Test 403 response that is not rate limit related."""
        mock_response = Mock()
        mock_response.status_code = 403
        mock_response.headers = {
            'X-RateLimit-Remaining': '5000'  # Not rate limited
        }
        
        with patch('requests.get', return_value=mock_response):
            status, data = agent._github_request('GET', 'https://api.github.com/test')
            
            # Should not retry
            assert status == 403
            assert data is None
    
    def test_500_retry_exponential_backoff(self, agent):
        """Test 500 error retries with exponential backoff."""
        # First two requests return 500
        mock_response_500 = Mock()
        mock_response_500.status_code = 500
        mock_response_500.headers = {}
        
        # Third request succeeds
        mock_response_200 = Mock()
        mock_response_200.status_code = 200
        mock_response_200.text = '{"key": "value"}'
        mock_response_200.json.return_value = {"key": "value"}
        mock_response_200.headers = {
            'X-RateLimit-Remaining': '5000'
        }
        
        with patch('requests.get', side_effect=[mock_response_500, mock_response_500, mock_response_200]):
            with patch('time.sleep') as mock_sleep:
                status, data = agent._github_request('GET', 'https://api.github.com/test')
                
                # Should succeed after retries
                assert status == 200
                
                # Should have exponential backoff: 5s, then 10s
                assert mock_sleep.call_count == 2
                assert mock_sleep.call_args_list[0][0][0] == 5  # First wait: 5s
                assert mock_sleep.call_args_list[1][0][0] == 10  # Second wait: 10s
    
    def test_network_error_retry(self, agent):
        """Test network error retry logic."""
        import requests.exceptions
        
        # First request raises network error
        # Second request succeeds
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '{"key": "value"}'
        mock_response.json.return_value = {"key": "value"}
        mock_response.headers = {}
        
        with patch('requests.get', side_effect=[requests.exceptions.ConnectionError("Network error"), mock_response]):
            with patch('time.sleep') as mock_sleep:
                status, data = agent._github_request('GET', 'https://api.github.com/test')
                
                # Should succeed after retry
                assert status == 200
                assert data == {"key": "value"}
                
                # Should have waited
                assert mock_sleep.called
    
    def test_network_error_max_retries(self, agent, caplog):
        """Test network error exhausts max retries."""
        import requests.exceptions
        
        with patch('requests.get', side_effect=requests.exceptions.ConnectionError("Network error")):
            with patch('time.sleep'):
                status, data = agent._github_request('GET', 'https://api.github.com/test', max_retries=1)
                
                # Should fail after max retries
                assert status == 0
                assert data is None
                assert "network error after" in caplog.text.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
