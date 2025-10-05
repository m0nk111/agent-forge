"""Tests for service manager."""

import asyncio
import os
import signal
import pytest
from unittest.mock import Mock, patch, MagicMock
from agents.service_manager import ServiceManager, ServiceConfig


class TestServiceConfig:
    """Tests for ServiceConfig dataclass."""
    
    def test_default_values(self):
        """Test default configuration values."""
        config = ServiceConfig()
        assert config.enable_polling is True
        assert config.enable_monitoring is True
        assert config.enable_web_ui is True
        assert config.polling_interval == 300
        assert config.health_check_interval == 30
        assert config.watchdog_enabled is True
        assert len(config.polling_repos) == 2
        
    def test_custom_values(self):
        """Test custom configuration."""
        config = ServiceConfig(
            enable_polling=False,
            polling_interval=600,
            web_ui_port=9000
        )
        assert config.enable_polling is False
        assert config.polling_interval == 600
        assert config.web_ui_port == 9000


class TestServiceManager:
    """Tests for ServiceManager class."""
    
    def test_initialization(self):
        """Test service manager initialization."""
        config = ServiceConfig()
        manager = ServiceManager(config)
        
        assert manager.config == config
        assert manager.running is False
        assert len(manager.services) == 0
        assert len(manager.tasks) == 0
        assert len(manager.health_status) == 0
        
    def test_signal_handler(self):
        """Test signal handler sets running to False."""
        config = ServiceConfig()
        manager = ServiceManager(config)
        manager.running = True
        
        # Simulate SIGTERM
        manager._signal_handler(signal.SIGTERM, None)
        
        assert manager.running is False
        
    def test_get_health_status(self):
        """Test health status retrieval."""
        config = ServiceConfig()
        manager = ServiceManager(config)
        manager.running = True
        manager.health_status = {
            'polling': True,
            'monitoring': True,
            'web_ui': False
        }
        
        status = manager.get_health_status()
        
        assert status['running'] is True
        assert status['services']['polling'] is True
        assert status['services']['monitoring'] is True
        assert status['services']['web_ui'] is False
        assert status['all_healthy'] is False  # web_ui is False
        
    @pytest.mark.asyncio
    async def test_shutdown_stops_services(self):
        """Test shutdown method stops all services."""
        config = ServiceConfig()
        manager = ServiceManager(config)
        manager.running = True
        
        # Mock services
        mock_polling = Mock()
        mock_polling.stop = Mock()
        manager.services['polling'] = mock_polling
        
        mock_monitoring = Mock()
        mock_monitoring.stop = Mock(return_value=asyncio.sleep(0))
        manager.services['monitoring'] = mock_monitoring
        
        mock_process = Mock()
        mock_process.terminate = Mock()
        mock_process.wait = Mock()
        manager.services['web_ui'] = mock_process
        
        # Run shutdown
        await manager.shutdown()
        
        # Verify services were stopped
        mock_polling.stop.assert_called_once()
        mock_monitoring.stop.assert_called_once()
        mock_process.terminate.assert_called_once()
        
    @pytest.mark.asyncio
    async def test_health_check_updates_status(self, tmp_path):
        """Test health check loop updates service status."""
        config = ServiceConfig(health_check_interval=1)
        manager = ServiceManager(config)
        
        # Mock polling service
        mock_polling = Mock()
        mock_polling.running = True
        manager.services['polling'] = mock_polling
        manager.health_status['polling'] = False
        
        # Run one health check cycle
        manager.running = True
        task = asyncio.create_task(manager._health_check_loop())
        await asyncio.sleep(1.5)  # Wait for one check
        manager.running = False
        
        try:
            await asyncio.wait_for(task, timeout=2)
        except asyncio.TimeoutError:
            task.cancel()
            
        # Health status should be updated
        assert manager.health_status['polling'] is True


class TestServiceManagerIntegration:
    """Integration tests for service manager."""
    
    @pytest.mark.asyncio
    async def test_start_with_disabled_services(self):
        """Test starting manager with all services disabled."""
        config = ServiceConfig(
            enable_polling=False,
            enable_monitoring=False,
            enable_web_ui=False,
            watchdog_enabled=False
        )
        
        manager = ServiceManager(config)
        
        # Start and immediately stop
        start_task = asyncio.create_task(manager.start())
        await asyncio.sleep(0.5)
        manager.running = False
        
        try:
            await asyncio.wait_for(start_task, timeout=2)
        except asyncio.TimeoutError:
            # Force cancel if it doesn't stop
            start_task.cancel()
            try:
                await start_task
            except asyncio.CancelledError:
                pass
                
        # Should not have started any services
        assert len(manager.services) == 0
        
    @pytest.mark.asyncio  
    @patch('agents.polling_service.PollingService')
    async def test_start_polling_service(self, mock_polling_class):
        """Test starting polling service."""
        # Setup mock
        mock_instance = Mock()
        mock_instance.run = Mock(return_value=asyncio.sleep(0))
        mock_polling_class.return_value = mock_instance
        
        config = ServiceConfig(
            enable_polling=True,
            enable_monitoring=False,
            enable_web_ui=False,
            watchdog_enabled=False
        )
        
        manager = ServiceManager(config)
        
        # Start service
        task = asyncio.create_task(manager._start_polling_service())
        await asyncio.sleep(0.5)
        
        # Cancel task
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
            
        # Verify service was created
        assert 'polling' in manager.services
        assert manager.health_status['polling'] is True


def test_import_service_manager():
    """Test that service manager module can be imported."""
    from agents import service_manager
    assert hasattr(service_manager, 'ServiceManager')
    assert hasattr(service_manager, 'ServiceConfig')
    assert hasattr(service_manager, 'main')
