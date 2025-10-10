"""Tests for health_checker module.

Comprehensive test suite for service health checking functionality.

Author: Agent-Forge Autonomous Pipeline
Date: 2025-10-10
"""

import pytest
import socket
from unittest.mock import patch, MagicMock
from engine.operations.health_checker import check_service_health


class TestCheckServiceHealth:
    """Test suite for check_service_health function."""
    
    def test_successful_connection(self):
        """Test successful connection to a reachable service."""
        with patch('socket.socket') as mock_socket_class:
            # Mock successful connection
            mock_socket = MagicMock()
            mock_socket_class.return_value = mock_socket
            mock_socket.connect.return_value = None
            
            result = check_service_health('localhost', 8080)
            
            assert result['healthy'] is True
            assert 'reachable' in result['message'].lower()
            assert result['latency_ms'] >= 0
            assert isinstance(result['latency_ms'], float)
            
            # Verify socket was created and closed
            mock_socket_class.assert_called_once_with(socket.AF_INET, socket.SOCK_STREAM)
            mock_socket.connect.assert_called_once_with(('localhost', 8080))
            mock_socket.close.assert_called_once()
    
    def test_connection_timeout(self):
        """Test connection timeout scenario."""
        with patch('socket.socket') as mock_socket_class:
            mock_socket = MagicMock()
            mock_socket_class.return_value = mock_socket
            mock_socket.connect.side_effect = socket.timeout('Connection timed out')
            
            result = check_service_health('unreachable.example.com', 9999)
            
            assert result['healthy'] is False
            assert 'timed out' in result['message'].lower()
            assert result['latency_ms'] == 0.0
    
    def test_connection_refused(self):
        """Test connection refused by target."""
        with patch('socket.socket') as mock_socket_class:
            mock_socket = MagicMock()
            mock_socket_class.return_value = mock_socket
            mock_socket.connect.side_effect = ConnectionRefusedError('Connection refused')
            
            result = check_service_health('localhost', 12345)
            
            assert result['healthy'] is False
            assert 'refused' in result['message'].lower()
            assert result['latency_ms'] == 0.0
    
    def test_dns_resolution_failure(self):
        """Test DNS resolution failure."""
        with patch('socket.socket') as mock_socket_class:
            mock_socket = MagicMock()
            mock_socket_class.return_value = mock_socket
            mock_socket.connect.side_effect = socket.gaierror('Name or service not known')
            
            result = check_service_health('invalid.nonexistent.domain', 80)
            
            assert result['healthy'] is False
            assert 'dns' in result['message'].lower() or 'resolution' in result['message'].lower()
            assert result['latency_ms'] == 0.0
    
    def test_invalid_service_name(self):
        """Test with invalid service name."""
        # Empty string
        result = check_service_health('', 8080)
        assert result['healthy'] is False
        assert 'invalid' in result['message'].lower()
        
        # None
        result = check_service_health(None, 8080)
        assert result['healthy'] is False
        assert 'invalid' in result['message'].lower()
        
        # Non-string
        result = check_service_health(12345, 8080)
        assert result['healthy'] is False
        assert 'invalid' in result['message'].lower()
    
    def test_invalid_port_numbers(self):
        """Test with invalid port numbers."""
        # Port too low
        result = check_service_health('localhost', 0)
        assert result['healthy'] is False
        assert 'invalid port' in result['message'].lower()
        
        # Port too high
        result = check_service_health('localhost', 65536)
        assert result['healthy'] is False
        assert 'invalid port' in result['message'].lower()
        
        # Negative port
        result = check_service_health('localhost', -1)
        assert result['healthy'] is False
        assert 'invalid port' in result['message'].lower()
        
        # Non-integer port
        result = check_service_health('localhost', '8080')
        assert result['healthy'] is False
        assert 'invalid' in result['message'].lower()
    
    def test_network_error(self):
        """Test general network error."""
        with patch('socket.socket') as mock_socket_class:
            mock_socket = MagicMock()
            mock_socket_class.return_value = mock_socket
            mock_socket.connect.side_effect = OSError('Network is unreachable')
            
            result = check_service_health('localhost', 8080)
            
            assert result['healthy'] is False
            assert 'network error' in result['message'].lower() or 'error' in result['message'].lower()
            assert result['latency_ms'] == 0.0
    
    def test_unexpected_exception(self):
        """Test handling of unexpected exceptions."""
        with patch('socket.socket') as mock_socket_class:
            mock_socket = MagicMock()
            mock_socket_class.return_value = mock_socket
            mock_socket.connect.side_effect = RuntimeError('Unexpected error')
            
            result = check_service_health('localhost', 8080)
            
            assert result['healthy'] is False
            assert 'error' in result['message'].lower()
            assert result['latency_ms'] == 0.0
    
    def test_latency_measurement(self):
        """Test that latency is measured correctly."""
        with patch('socket.socket') as mock_socket_class, \
             patch('time.time') as mock_time:
            
            # Mock time to simulate 50ms latency
            mock_time.side_effect = [1000.0, 1000.05]  # 50ms difference
            
            mock_socket = MagicMock()
            mock_socket_class.return_value = mock_socket
            mock_socket.connect.return_value = None
            
            result = check_service_health('localhost', 8080)
            
            assert result['healthy'] is True
            assert result['latency_ms'] == 50.0  # 0.05 * 1000
    
    def test_socket_cleanup_on_error(self):
        """Test that socket is properly closed even on error."""
        with patch('socket.socket') as mock_socket_class:
            mock_socket = MagicMock()
            mock_socket_class.return_value = mock_socket
            mock_socket.connect.side_effect = ConnectionRefusedError()
            
            result = check_service_health('localhost', 8080)
            
            # Socket should still be closed
            mock_socket.close.assert_called_once()
            assert result['healthy'] is False
    
    def test_return_value_structure(self):
        """Test that return value has correct structure."""
        with patch('socket.socket') as mock_socket_class:
            mock_socket = MagicMock()
            mock_socket_class.return_value = mock_socket
            mock_socket.connect.return_value = None
            
            result = check_service_health('localhost', 8080)
            
            # Check all required keys exist
            assert 'healthy' in result
            assert 'message' in result
            assert 'latency_ms' in result
            
            # Check types
            assert isinstance(result['healthy'], bool)
            assert isinstance(result['message'], str)
            assert isinstance(result['latency_ms'], float)
