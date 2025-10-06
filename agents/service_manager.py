"""Service manager for running Agent-Forge as a systemd service.

This module manages all Agent-Forge services in a single process that can be
controlled by systemd. It handles:
- Starting/stopping polling service
- Starting/stopping monitoring service  
- Starting/stopping web UI
- Graceful shutdown on SIGTERM/SIGINT
- Systemd watchdog keepalive
- Health checks

Usage:
    # As systemd service
    systemctl start agent-forge
    
    # Standalone
    python -m agents.service_manager
    
    # With custom config
    python -m agents.service_manager --config /path/to/config.yaml
"""

import asyncio
import logging
import os
import signal
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Dict, Any
import subprocess

# Try to import systemd for notify support
try:
    from systemd import daemon, journal
    HAS_SYSTEMD = True
except ImportError:
    HAS_SYSTEMD = False
    print("Warning: systemd package not available. Install with: pip install systemd-python")

logger = logging.getLogger(__name__)


@dataclass
class ServiceConfig:
    """Configuration for service manager."""
    
    # Polling service
    enable_polling: bool = True
    polling_interval: int = 300  # 5 minutes
    polling_repos: list = None
    
    # Monitoring service  
    enable_monitoring: bool = True
    monitoring_port: int = 7997  # Standard monitoring port (matches dashboard)
    
    # Web UI
    enable_web_ui: bool = True
    web_ui_port: int = 8897  # Standard dashboard port
    
    # Code Agent (formerly Qwen Agent)
    enable_code_agent: bool = True
    qwen_model: str = "qwen2.5-coder:32b"  # Keep param name for backward compat
    qwen_base_url: str = "http://localhost:11434"  # Keep param name for backward compat
    
    # Health check
    health_check_interval: int = 30  # seconds
    
    # Systemd
    watchdog_enabled: bool = True
    
    def __post_init__(self):
        """Initialize default values."""
        if self.polling_repos is None:
            self.polling_repos = ["m0nk111/agent-forge", "m0nk111/stepperheightcontrol"]


class ServiceManager:
    """Manages all Agent-Forge services as a unified systemd service."""
    
    def __init__(self, config: ServiceConfig):
        """Initialize service manager.
        
        Args:
            config: Service configuration
        """
        self.config = config
        self.running = False
        self.services: Dict[str, Any] = {}
        self.tasks: Dict[str, asyncio.Task] = {}
        self.health_status: Dict[str, bool] = {}
        self.start_time = time.time()
        
        # Setup signal handlers
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
        
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals.
        
        Args:
            signum: Signal number
            frame: Current stack frame
        """
        sig_name = signal.Signals(signum).name
        logger.info(f"Received signal {sig_name}, initiating graceful shutdown...")
        self.running = False
        
    async def _start_polling_service(self):
        """Start autonomous polling service."""
        try:
            from agents.polling_service import PollingService, PollingConfig
            
            logger.info("Starting polling service...")
            
            # Create polling config
            config = PollingConfig(
                interval_seconds=self.config.polling_interval,
                github_token=os.getenv("BOT_GITHUB_TOKEN") or os.getenv("GITHUB_TOKEN"),
                github_username="m0nk111-qwen-agent",
                repositories=["m0nk111/agent-forge", "m0nk111/stepperheightcontrol"],
                watch_labels=["agent-ready", "auto-assign"],
                max_concurrent_issues=3,
                state_file="/opt/agent-forge/data/polling_state.json"
            )
            
            # Create service with monitoring enabled
            service = PollingService(config, enable_monitoring=True)
            self.services['polling'] = service
            self.health_status['polling'] = True
            
            # Run polling service
            await service.run()
            
        except Exception as e:
            logger.error(f"Polling service error: {e}", exc_info=True)
            self.health_status['polling'] = False
            raise
    
    async def _start_code_agent(self):
        """Start code agent."""
        try:
            from agents.code_agent import CodeAgent
            
            logger.info("Starting code agent...")
            
            # Create agent instance
            agent = CodeAgent(
                model=self.config.qwen_model,
                ollama_url=self.config.qwen_base_url,
                project_root="/opt/agent-forge",
                enable_monitoring=True,
                agent_id="qwen-main-agent"
            )
            
            self.services['code_agent'] = agent
            self.health_status['code_agent'] = True
            
            logger.info("✅ Code agent initialized and registered with monitor")
            
            # Keep agent alive (it handles issues via polling service callbacks)
            while self.running:
                await asyncio.sleep(10)
                # Agent stays registered and ready
            
        except Exception as e:
            logger.error(f"Code agent error: {e}", exc_info=True)
            self.health_status['code_agent'] = False
            raise
            
    async def _start_monitoring_service(self):
        """Start real-time monitoring service with WebSocket."""
        try:
            from agents.monitor_service import get_monitor
            from agents.websocket_handler import create_monitoring_app
            import uvicorn
            
            logger.info("Starting monitoring service...")
            
            # Get monitor instance
            monitor = get_monitor()
            await monitor.start()
            self.services['monitoring'] = monitor
            self.health_status['monitoring'] = True
            
            # Start WebSocket server in background
            config = uvicorn.Config(
                create_monitoring_app(),
                host="0.0.0.0",
                port=self.config.monitoring_port,
                log_level="info"
            )
            server = uvicorn.Server(config)
            
            logger.info(f"Monitoring service started on port {self.config.monitoring_port}")
            
            # Run server
            await server.serve()
            
        except Exception as e:
            logger.error(f"Monitoring service error: {e}", exc_info=True)
            self.health_status['monitoring'] = False
            raise
            
    async def _start_web_ui(self):
        """Start web UI server."""
        try:
            logger.info("Starting web UI...")
            
            # Use simple HTTP server for static files
            # Bind to 0.0.0.0 to allow network access
            cmd = [
                "python3", "-m", "http.server",
                str(self.config.web_ui_port),
                "--directory", "frontend",
                "--bind", "0.0.0.0"
            ]
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=Path(__file__).parent.parent
            )
            
            self.services['web_ui'] = process
            self.health_status['web_ui'] = True
            
            logger.info(f"Web UI started on port {self.config.web_ui_port} (accessible on all interfaces)")
            
            # Monitor process
            while self.running:
                if process.poll() is not None:
                    logger.error("Web UI process died")
                    self.health_status['web_ui'] = False
                    break
                await asyncio.sleep(5)
                
        except Exception as e:
            logger.error(f"Web UI error: {e}", exc_info=True)
            self.health_status['web_ui'] = False
            raise
            
    async def _watchdog_ping(self):
        """Send keepalive to systemd watchdog."""
        if not HAS_SYSTEMD or not self.config.watchdog_enabled:
            return
            
        try:
            # Get watchdog interval from systemd
            watchdog_usec = os.getenv('WATCHDOG_USEC')
            if not watchdog_usec:
                logger.warning("WATCHDOG_USEC not set, watchdog disabled")
                return
                
            # Ping at half the watchdog interval
            interval = int(watchdog_usec) / 2_000_000  # Convert to seconds
            
            logger.info(f"Systemd watchdog enabled (interval: {interval}s)")
            
            while self.running:
                # Check if all services are healthy
                all_healthy = all(self.health_status.values())
                
                if all_healthy:
                    daemon.notify('WATCHDOG=1')
                    logger.debug("Sent watchdog keepalive")
                else:
                    logger.warning(f"Services unhealthy: {self.health_status}")
                    
                await asyncio.sleep(interval)
                
        except Exception as e:
            logger.error(f"Watchdog error: {e}", exc_info=True)
            
    async def _health_check_loop(self):
        """Periodic health checks for all services."""
        try:
            while self.running:
                await asyncio.sleep(self.config.health_check_interval)
                
                # Check polling service
                if 'polling' in self.services:
                    polling = self.services['polling']
                    self.health_status['polling'] = polling.running
                    
                # Check monitoring service
                if 'monitoring' in self.services:
                    # Monitoring service health is updated by the service itself
                    pass
                    
                # Check web UI process
                if 'web_ui' in self.services:
                    process = self.services['web_ui']
                    self.health_status['web_ui'] = process.poll() is None
                    
                # Log health status
                uptime = time.time() - self.start_time
                logger.info(f"Health check (uptime: {uptime:.0f}s): {self.health_status}")
                
        except Exception as e:
            logger.error(f"Health check error: {e}", exc_info=True)
            
    def get_health_status(self) -> Dict[str, Any]:
        """Get current health status.
        
        Returns:
            Dictionary with health information
        """
        return {
            'running': self.running,
            'uptime': time.time() - self.start_time,
            'services': self.health_status.copy(),
            'all_healthy': all(self.health_status.values())
        }
        
    async def start(self):
        """Start all services."""
        logger.info("=== Agent-Forge Service Manager Starting ===")
        logger.info(f"Configuration: {self.config}")
        
        self.running = True
        
        # Notify systemd we're starting
        if HAS_SYSTEMD:
            daemon.notify('STATUS=Starting services...')
        
        try:
            # Start polling service
            if self.config.enable_polling:
                self.tasks['polling'] = asyncio.create_task(
                    self._start_polling_service()
                )
                await asyncio.sleep(1)  # Let it initialize
                
            # Start monitoring service
            if self.config.enable_monitoring:
                self.tasks['monitoring'] = asyncio.create_task(
                    self._start_monitoring_service()
                )
                await asyncio.sleep(1)
                
            # Start web UI
            if self.config.enable_web_ui:
                self.tasks['web_ui'] = asyncio.create_task(
                    self._start_web_ui()
                )
                await asyncio.sleep(1)
            
            # Start code agent
            if self.config.enable_code_agent:
                self.tasks['code_agent'] = asyncio.create_task(
                    self._start_code_agent()
                )
                await asyncio.sleep(1)
                
            # Start watchdog
            self.tasks['watchdog'] = asyncio.create_task(
                self._watchdog_ping()
            )
            
            # Start health checks
            self.tasks['health'] = asyncio.create_task(
                self._health_check_loop()
            )
            
            # Notify systemd we're ready
            if HAS_SYSTEMD:
                daemon.notify('READY=1')
                daemon.notify('STATUS=All services running')
                
            logger.info("=== All services started successfully ===")
            logger.info(f"Services: {list(self.services.keys())}")
            
            # Wait for shutdown signal
            while self.running:
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"Service manager error: {e}", exc_info=True)
            raise
        finally:
            await self.shutdown()
            
    async def shutdown(self):
        """Gracefully shutdown all services."""
        logger.info("=== Agent-Forge Service Manager Shutting Down ===")
        
        # Notify systemd we're stopping
        if HAS_SYSTEMD:
            daemon.notify('STOPPING=1')
            daemon.notify('STATUS=Shutting down...')
        
        self.running = False
        
        # Stop polling service
        if 'polling' in self.services:
            logger.info("Stopping polling service...")
            try:
                self.services['polling'].stop()
                await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"Error stopping polling: {e}")
                
        # Stop monitoring service
        if 'monitoring' in self.services:
            logger.info("Stopping monitoring service...")
            try:
                await self.services['monitoring'].stop()
            except Exception as e:
                logger.error(f"Error stopping monitoring: {e}")
                
        # Stop web UI
        if 'web_ui' in self.services:
            logger.info("Stopping web UI...")
            try:
                process = self.services['web_ui']
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
            except Exception as e:
                logger.error(f"Error stopping web UI: {e}")
                
        # Cancel all tasks
        for name, task in self.tasks.items():
            if not task.done():
                logger.info(f"Cancelling task: {name}")
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
                except Exception as e:
                    logger.error(f"Error cancelling {name}: {e}")
                    
        logger.info("=== Shutdown complete ===")


def setup_logging():
    """Configure logging for systemd journal or console."""
    if HAS_SYSTEMD and journal:
        # Use systemd journal handler
        handler = journal.JournalHandler(SYSLOG_IDENTIFIER='agent-forge')
        formatter = logging.Formatter('%(name)s[%(process)d]: %(levelname)s - %(message)s')
    else:
        # Use console handler
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
    handler.setFormatter(formatter)
    
    # Configure root logger
    logging.root.setLevel(logging.INFO)
    logging.root.addHandler(handler)
    
    # Suppress noisy libraries
    logging.getLogger('asyncio').setLevel(logging.WARNING)


async def main():
    """Main entry point for service manager."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Agent-Forge Service Manager")
    parser.add_argument("--config", help="Path to config file")
    parser.add_argument("--no-polling", action="store_true", help="Disable polling service")
    parser.add_argument("--no-monitoring", action="store_true", help="Disable monitoring")
    parser.add_argument("--no-web-ui", action="store_true", help="Disable web UI")
    parser.add_argument("--no-qwen", action="store_true", help="Disable Qwen agent")
    parser.add_argument("--polling-interval", type=int, default=300, help="Polling interval (seconds)")
    parser.add_argument("--web-port", type=int, default=8080, help="Web UI port")
    parser.add_argument("--monitor-port", type=int, default=8765, help="Monitoring WebSocket port")
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging()
    
    logger.info("Agent-Forge Service Manager starting...")
    logger.info(f"Python: {sys.version}")
    logger.info(f"Systemd support: {HAS_SYSTEMD}")
    
    # Create config
    config = ServiceConfig(
        enable_polling=not args.no_polling,
        enable_monitoring=not args.no_monitoring,
        enable_web_ui=not args.no_web_ui,
        enable_code_agent=not args.no_qwen,  # Keep --no-qwen flag for backward compat
        polling_interval=args.polling_interval,
        web_ui_port=args.web_port,
        monitoring_port=args.monitor_port,
        watchdog_enabled=HAS_SYSTEMD
    )
    
    # Create and start service manager
    manager = ServiceManager(config)
    
    try:
        await manager.start()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        logger.info("Service manager exited")


if __name__ == "__main__":
    asyncio.run(main())
