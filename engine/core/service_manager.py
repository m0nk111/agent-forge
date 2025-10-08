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
    enable_agent_runtime: bool = True  # Unified agent runtime for all roles
    qwen_model: str = "qwen2.5-coder:7b"  # Model must exist in Ollama (check with: ollama list)
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
            from engine.runners.polling_service import PollingService, PollingConfig
            from pathlib import Path
            
            logger.info("Starting polling service...")
            
            # Load GitHub token for qwen-agent from secrets
            token_file = Path("/opt/agent-forge/secrets/agents/m0nk111-qwen-agent.token")
            github_token = None
            if token_file.exists():
                try:
                    github_token = token_file.read_text().strip()
                    logger.info("✅ Loaded GitHub token for polling service")
                except Exception as e:
                    logger.error(f"❌ Failed to load GitHub token: {e}")
            else:
                logger.warning("⚠️ GitHub token file not found, using environment variable")
                github_token = os.getenv("BOT_GITHUB_TOKEN") or os.getenv("GITHUB_TOKEN")
            
            # Create polling config
            config = PollingConfig(
                interval_seconds=self.config.polling_interval,
                github_token=github_token,
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
    
    async def _start_agent_runtime(self):
        """Start unified agent runtime for all agent roles."""
        try:
            from engine.core.config_manager import get_config_manager
            from engine.core.agent_registry import AgentRegistry
            
            logger.info("Starting unified agent runtime...")
            
            # Get monitoring service
            monitor = self.services.get('monitoring')
            
            # Create agent registry
            config_manager = get_config_manager()
            registry = AgentRegistry(config_manager, monitor=monitor)
            
            # Load all enabled agents
            loaded = await registry.load_agents()
            logger.info(f"📋 Loaded {len(loaded)} agents:")
            for agent_id, lifecycle in loaded.items():
                logger.info(f"   - {agent_id}: {lifecycle}")
            
            # Start always-on agents (coordinator, developer)
            started = await registry.start_always_on_agents()
            logger.info(f"✅ Started {len(started)} always-on agents")
            
            # Store registry for later use
            self.services['agent_runtime'] = registry
            self.health_status['agent_runtime'] = True
            
            logger.info("✅ Agent runtime initialized")
            
            # Keep runtime alive and send heartbeats for idle agents
            while self.running:
                await asyncio.sleep(60)  # Heartbeat every 60s (cleanup timeout is 300s)
                
                # Send heartbeat for idle agents to prevent timeout
                from engine.runners.monitor_service import AgentStatus
                for agent_id, managed in registry.agents.items():
                    from engine.core.agent_registry import AgentState as RegistryAgentState
                    if managed.state == RegistryAgentState.IDLE and monitor:
                        monitor.update_agent_status(
                            agent_id=agent_id,
                            status=AgentStatus.IDLE,
                            current_task=None
                        )
            
        except Exception as e:
            logger.error(f"Agent runtime error: {e}", exc_info=True)
            self.health_status['agent_runtime'] = False
            raise
            
    async def _start_monitoring_service(self):
            raise
            
    async def _start_monitoring_service(self):
        """Start real-time monitoring service with WebSocket."""
        try:
            from engine.runners.monitor_service import get_monitor
            from engine.operations.websocket_handler import create_monitoring_app
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
                cwd=Path(__file__).parent.parent.parent  # Go up to project root (engine/core/ -> engine/ -> root)
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
                logger.debug(f"🔄 Watchdog loop: running={self.running}, health={self.health_status}")
                
                # Check if all services are healthy
                all_healthy = all(self.health_status.values())
                
                if all_healthy:
                    daemon.notify('WATCHDOG=1')
                    logger.info("✅ Sent watchdog keepalive")
                else:
                    logger.warning(f"⚠️ Services unhealthy, skipping watchdog: {self.health_status}")
                    
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
                
                # Check agent runtime (unified agent registry)
                if 'agent_runtime' in self.services:
                    # Agent runtime health is tracked via agent registry
                    self.health_status['agent_runtime'] = True
                    
                # Update monitoring service with health status
                if 'monitoring' in self.services:
                    try:
                        monitor = self.services['monitoring']
                        monitor.update_services(self.health_status)
                    except Exception as e:
                        logger.error(f"Failed to update monitoring service: {e}")
                    
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
            # Start watchdog FIRST to prevent timeout during startup
            self.tasks['watchdog'] = asyncio.create_task(
                self._watchdog_ping()
            )
            
            # Start monitoring service (needed by other services)
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
            
            # Start agent runtime BEFORE polling (polling depends on it)
            if self.config.enable_agent_runtime:
                self.tasks['agent_runtime'] = asyncio.create_task(
                    self._start_agent_runtime()
                )
                await asyncio.sleep(2)  # Give agent runtime time to initialize
            
            # Start polling service AFTER agent runtime is ready
            if self.config.enable_polling:
                self.tasks['polling'] = asyncio.create_task(
                    self._start_polling_service()
                )
                await asyncio.sleep(1)  # Let it initialize
                
                # Inject agent_registry into polling service
                if 'agent_runtime' in self.services:
                    polling_service = self.services['polling']
                    polling_service.agent_registry = self.services['agent_runtime']
                    logger.info("✅ Agent registry injected into polling service")
                
            # Start health checks
            self.tasks['health'] = asyncio.create_task(
                self._health_check_loop()
            )
            
            # Initialize service status in monitoring
            if 'monitoring' in self.services:
                try:
                    monitor = self.services['monitoring']
                    monitor.update_services(self.health_status)
                    logger.info("✅ Initial service status sent to monitoring")
                except Exception as e:
                    logger.error(f"Failed to initialize monitoring service status: {e}")
            
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
    parser.add_argument("--no-agent-runtime", action="store_true", help="Disable agent runtime")
    parser.add_argument("--no-qwen", action="store_true", help="Disable agent runtime (deprecated, use --no-agent-runtime)")
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
        enable_agent_runtime=not (args.no_agent_runtime or args.no_qwen),  # Support both flags
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
