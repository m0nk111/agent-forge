"""
Tests for retry utility with exponential backoff.
"""

import pytest
import time
from unittest.mock import Mock, patch
from engine.operations.retry_util import retry_with_backoff, execute_with_retry


class TestRetryWithBackoff:
    """Test suite for retry_with_backoff decorator."""
    
    def test_successful_execution_no_retry(self):
        """Test function succeeds on first attempt (no retries needed)."""
        mock_func = Mock(return_value="success")
        
        decorated = retry_with_backoff(mock_func, max_attempts=3)
        result = decorated()
        
        assert result == "success"
        assert mock_func.call_count == 1
    
    def test_retry_on_failure_eventual_success(self):
        """Test retry logic when function fails then succeeds."""
        mock_func = Mock(side_effect=[
            ValueError("attempt 1"),
            ValueError("attempt 2"),
            "success"  # Succeeds on 3rd attempt
        ])
        
        decorated = retry_with_backoff(mock_func, max_attempts=3, base_delay=0.01)
        result = decorated()
        
        assert result == "success"
        assert mock_func.call_count == 3
    
    def test_max_attempts_exceeded(self):
        """Test that exception is raised after max attempts."""
        mock_func = Mock(side_effect=ValueError("always fails"))
        
        decorated = retry_with_backoff(mock_func, max_attempts=3, base_delay=0.01)
        
        with pytest.raises(ValueError, match="always fails"):
            decorated()
        
        assert mock_func.call_count == 3
    
    def test_exponential_backoff_timing(self):
        """Test that exponential backoff delays are correct."""
        mock_func = Mock(side_effect=[
            ValueError("attempt 1"),
            ValueError("attempt 2"),
            ValueError("attempt 3"),
        ])
        
        decorated = retry_with_backoff(mock_func, max_attempts=3, base_delay=0.1)
        
        start_time = time.time()
        
        with pytest.raises(ValueError):
            decorated()
        
        elapsed = time.time() - start_time
        
        # Expected delays: 0.1s + 0.2s = 0.3s (exponential: 2^0, 2^1)
        # Allow some tolerance for execution time
        assert 0.25 < elapsed < 0.5
    
    def test_with_args_kwargs(self):
        """Test retry with function arguments and keyword arguments."""
        mock_func = Mock(return_value="result")
        
        decorated = retry_with_backoff(mock_func, max_attempts=3)
        result = decorated("arg1", "arg2", key1="value1", key2="value2")
        
        assert result == "result"
        mock_func.assert_called_once_with("arg1", "arg2", key1="value1", key2="value2")
    
    def test_max_delay_cap(self):
        """Test that max_delay caps the exponential backoff."""
        mock_func = Mock(side_effect=[
            ValueError("1"),
            ValueError("2"),
            ValueError("3"),
        ])
        
        decorated = retry_with_backoff(
            mock_func,
            max_attempts=3,
            base_delay=1.0,
            max_delay=1.5
        )
        
        start_time = time.time()
        
        with pytest.raises(ValueError):
            decorated()
        
        elapsed = time.time() - start_time
        
        # Without cap: 1.0 + 2.0 = 3.0s
        # With cap at 1.5: 1.0 + 1.5 = 2.5s
        assert 2.3 < elapsed < 2.8
    
    def test_specific_exceptions_only(self):
        """Test that only specified exceptions are retried."""
        mock_func = Mock(side_effect=KeyError("not retryable"))
        
        # Only retry ValueError, not KeyError
        decorated = retry_with_backoff(
            mock_func,
            max_attempts=3,
            base_delay=0.01,
            exceptions=(ValueError,)
        )
        
        with pytest.raises(KeyError, match="not retryable"):
            decorated()
        
        # Should fail immediately without retries
        assert mock_func.call_count == 1
    
    def test_multiple_exception_types(self):
        """Test retrying on multiple exception types."""
        mock_func = Mock(side_effect=[
            ValueError("error 1"),
            KeyError("error 2"),
            "success"
        ])
        
        decorated = retry_with_backoff(
            mock_func,
            max_attempts=3,
            base_delay=0.01,
            exceptions=(ValueError, KeyError)
        )
        
        result = decorated()
        
        assert result == "success"
        assert mock_func.call_count == 3


class TestExecuteWithRetry:
    """Test suite for execute_with_retry function."""
    
    def test_execute_with_retry_success(self):
        """Test functional interface for retry."""
        mock_func = Mock(return_value="success")
        
        result = execute_with_retry(
            mock_func,
            "arg1",
            max_attempts=3,
            key="value"
        )
        
        assert result == "success"
        mock_func.assert_called_once_with("arg1", key="value")
    
    def test_execute_with_retry_failure(self):
        """Test functional interface handles failures."""
        mock_func = Mock(side_effect=ValueError("failed"))
        
        with pytest.raises(ValueError, match="failed"):
            execute_with_retry(
                mock_func,
                max_attempts=2,
                base_delay=0.01
            )
        
        assert mock_func.call_count == 2
    
    def test_execute_with_retry_eventual_success(self):
        """Test functional interface with retry and success."""
        mock_func = Mock(side_effect=[
            ValueError("fail 1"),
            "success"
        ])
        
        result = execute_with_retry(
            mock_func,
            "arg",
            max_attempts=3,
            base_delay=0.01,
            kwarg="value"
        )
        
        assert result == "success"
        assert mock_func.call_count == 2


class TestRealWorldScenarios:
    """Test real-world usage scenarios."""
    
    def test_simulated_network_call(self):
        """Simulate a flaky network call that eventually succeeds."""
        call_count = 0
        
        def flaky_api_call():
            nonlocal call_count
            call_count += 1
            
            if call_count < 3:
                raise ConnectionError("Network unreachable")
            
            return {"status": "success", "data": [1, 2, 3]}
        
        result = execute_with_retry(
            flaky_api_call,
            max_attempts=5,
            base_delay=0.01,
            exceptions=(ConnectionError,)
        )
        
        assert result["status"] == "success"
        assert call_count == 3
    
    def test_decorator_usage(self):
        """Test using as a decorator."""
        attempt_count = 0
        
        @retry_with_backoff(max_attempts=4, base_delay=0.01)
        def unreliable_operation(value):
            nonlocal attempt_count
            attempt_count += 1
            
            if attempt_count < 3:
                raise RuntimeError(f"Not ready yet (attempt {attempt_count})")
            
            return f"Processed: {value}"
        
        result = unreliable_operation("test_data")
        
        assert result == "Processed: test_data"
        assert attempt_count == 3
