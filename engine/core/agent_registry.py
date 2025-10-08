"""
Agent Registry - Unified agent lifecycle management.

Manages agent registration, startup, and on-demand loading based on role.
Follows industry best practices for multi-agent orchestration.
"""

import asyncio
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Any
from pathlib import Path

from engine.core.config_manager import AgentConfig, AgentRole

logger = logging.getLogger(__name__)


class AgentLifecycle(str, Enum):
    """Agent lifecycle strategies."""
    ALWAYS_ON = "always-on"      # Start immediately, keep running
    ON_DEMAND = "on-demand"      # Register but start when needed
    DISABLED = "disabled"        # Not loaded


class AgentState(str, Enum):
    """Agent runtime states."""
    REGISTERED = "registered"    # Registered but not started
    STARTING = "starting"        # Initialization in progress
    RUNNING = "running"          # Active and processing
    IDLE = "idle"               # Active but no tasks
    STOPPING = "stopping"       # Shutdown in progress
    STOPPED = "stopped"         # Cleanly stopped
    ERROR = "error"             # Error state


@dataclass
class ManagedAgent:
    """Container for managed agent instance."""
    config: AgentConfig
    lifecycle: AgentLifecycle
    state: AgentState
    instance: Optional[Any] = None
    task: Optional[asyncio.Task] = None
    error: Optional[str] = None


class AgentRegistry:
    """
    Unified agent lifecycle manager.
    
    Manages all agents regardless of role, with lifecycle strategies:
    - Always-on: coordinator, developer (immediate start)
    - On-demand: bot, reviewer, tester, documenter, researcher (lazy loading)
    
    Industry best practices:
    - Resource efficiency (only run what's needed)
    - Scalability (add agents without code changes)
    - Observability (unified monitoring)
    - Fault tolerance (isolated agent failures)
    """
    
    def __init__(self, config_manager, monitor=None):
        """
        Initialize agent registry.
        
        Args:
            config_manager: ConfigManager instance
            monitor: AgentMonitor instance for status tracking
        """
        self.config_manager = config_manager
        self.monitor = monitor
        self.agents: Dict[str, ManagedAgent] = {}
        self.running = False
        
        logger.info("🔧 AgentRegistry initialized")
    
    def _get_lifecycle_strategy(self, role: str) -> AgentLifecycle:
        """
        Determine lifecycle strategy based on agent role.
        
        Industry standard patterns:
        - Orchestrators/coordinators: Always-on (task distribution)
        - Workers/developers: Always-on (long-running tasks)
        - Utilities/bots: On-demand (event-driven)
        - Reviewers/testers: On-demand (triggered by events)
        
        Args:
            role: Agent role (coordinator, developer, bot, etc.)
            
        Returns:
            AgentLifecycle strategy
        """
        # Always-on roles (core functionality)
        if role in [AgentRole.COORDINATOR, AgentRole.DEVELOPER]:
            return AgentLifecycle.ALWAYS_ON
        
        # On-demand roles (event-driven)
        if role in [AgentRole.BOT, AgentRole.REVIEWER, AgentRole.TESTER, 
                   AgentRole.DOCUMENTER, AgentRole.RESEARCHER]:
            return AgentLifecycle.ON_DEMAND
        
        # Default to on-demand for unknown roles
        logger.warning(f"Unknown role '{role}', defaulting to on-demand lifecycle")
        return AgentLifecycle.ON_DEMAND
    
    async def load_agents(self) -> Dict[str, str]:
        """
        Load all enabled agents from configuration.
        
        Returns:
            Dictionary of agent_id -> lifecycle strategy
        """
        agents = self.config_manager.get_agents()
        loaded = {}
        
        for agent_config in agents:
            if not agent_config.enabled:
                logger.debug(f"⏭️  Skipping disabled agent: {agent_config.agent_id}")
                continue
            
            # Determine lifecycle strategy
            lifecycle = self._get_lifecycle_strategy(agent_config.role)
            
            # Create managed agent container
            managed_agent = ManagedAgent(
                config=agent_config,
                lifecycle=lifecycle,
                state=AgentState.REGISTERED
            )
            
            self.agents[agent_config.agent_id] = managed_agent
            loaded[agent_config.agent_id] = lifecycle.value
            
            # Register with monitoring service
            if self.monitor:
                self.monitor.register_agent(
                    agent_id=agent_config.agent_id,
                    name=agent_config.name or agent_config.agent_id,
                    role=agent_config.role,
                    model=agent_config.model_name,
                    capabilities=agent_config.capabilities
                )
            
            logger.info(f"📋 Registered: {agent_config.agent_id} ({agent_config.role}) - {lifecycle.value}")
        
        return loaded
    
    async def start_always_on_agents(self) -> List[str]:
        """
        Start all agents with always-on lifecycle.
        
        Returns:
            List of started agent IDs
        """
        started = []
        
        for agent_id, managed in self.agents.items():
            if managed.lifecycle != AgentLifecycle.ALWAYS_ON:
                continue
            
            try:
                await self._start_agent(agent_id)
                started.append(agent_id)
            except Exception as e:
                logger.error(f"❌ Failed to start {agent_id}: {e}", exc_info=True)
                managed.state = AgentState.ERROR
                managed.error = str(e)
        
        return started
    
    async def _start_agent(self, agent_id: str):
        """
        Start a specific agent.
        
        Args:
            agent_id: Agent identifier
        """
        if agent_id not in self.agents:
            raise ValueError(f"Agent {agent_id} not registered")
        
        managed = self.agents[agent_id]
        
        if managed.state == AgentState.RUNNING:
            logger.warning(f"⚠️  Agent {agent_id} already running")
            return
        
        logger.info(f"🚀 Starting agent: {agent_id} ({managed.config.role})")
        managed.state = AgentState.STARTING
        
        # Update monitoring
        if self.monitor:
            self.monitor.update_agent_status(
                agent_id=agent_id,
                status="starting",
                current_task="Initializing agent"
            )
        
        # Import and instantiate agent based on role
        if managed.config.role == AgentRole.DEVELOPER:
            await self._start_developer_agent(managed)
        elif managed.config.role == AgentRole.BOT:
            await self._start_bot_agent(managed)
        elif managed.config.role == AgentRole.COORDINATOR:
            await self._start_coordinator_agent(managed)
        else:
            raise NotImplementedError(f"Agent role {managed.config.role} not yet implemented")
        
        managed.state = AgentState.IDLE
        
        # Update monitoring
        if self.monitor:
            self.monitor.update_agent_status(
                agent_id=agent_id,
                status="idle",
                current_task=None
            )
        
        logger.info(f"✅ Agent started: {agent_id}")
    
    async def _start_developer_agent(self, managed: ManagedAgent):
        """Start developer agent (code generation)."""
        from engine.runners.code_agent import CodeAgent
        import os
        
        config = managed.config
        
        # Set GitHub token as environment variable
        if config.github_token:
            os.environ['GITHUB_TOKEN'] = config.github_token
            logger.info(f"   GitHub: Authenticated as {config.agent_id}")
        else:
            logger.warning(f"   GitHub: No token - operations may fail")
        
        # Create agent instance
        agent = CodeAgent(
            model=config.model_name,
            ollama_url=config.api_base_url or "http://localhost:11434",
            project_root=config.shell_working_dir or "/opt/agent-forge",
            enable_monitoring=True,
            agent_id=config.agent_id
        )
        
        managed.instance = agent
        logger.info(f"   Model: {config.model_provider}/{config.model_name}")
        logger.info(f"   Shell: {config.shell_permissions if config.local_shell_enabled else 'disabled'}")
    
    async def _start_bot_agent(self, managed: ManagedAgent):
        """Start bot agent (GitHub operations)."""
        from engine.runners.bot_agent import BotAgent
        
        config = managed.config
        
        # Create bot instance
        # Use agent_id as username (e.g., m0nk111-bot)
        agent = BotAgent(
            agent_id=config.agent_id,
            username=config.agent_id,  # Bot username same as agent_id
            github_token=config.github_token,
            monitor=self.monitor
        )
        
        managed.instance = agent
        logger.info(f"   GitHub: {config.agent_id}")
    
    async def _start_coordinator_agent(self, managed: ManagedAgent):
        """Start coordinator agent (task orchestration)."""
        # TODO: Implement coordinator agent
        logger.warning(f"⚠️  Coordinator agent not yet implemented")
        raise NotImplementedError("Coordinator agent not yet implemented")
    
    async def start_on_demand(self, agent_id: str) -> bool:
        """
        Start an on-demand agent.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            True if started successfully
        """
        if agent_id not in self.agents:
            logger.error(f"❌ Unknown agent: {agent_id}")
            return False
        
        managed = self.agents[agent_id]
        
        if managed.lifecycle != AgentLifecycle.ON_DEMAND:
            logger.warning(f"⚠️  Agent {agent_id} is not on-demand (lifecycle: {managed.lifecycle})")
            return False
        
        try:
            await self._start_agent(agent_id)
            return True
        except Exception as e:
            logger.error(f"❌ Failed to start {agent_id}: {e}", exc_info=True)
            managed.state = AgentState.ERROR
            managed.error = str(e)
            return False
    
    async def stop_agent(self, agent_id: str):
        """
        Stop a running agent.
        
        Args:
            agent_id: Agent identifier
        """
        if agent_id not in self.agents:
            logger.error(f"❌ Unknown agent: {agent_id}")
            return
        
        managed = self.agents[agent_id]
        
        if managed.state not in [AgentState.RUNNING, AgentState.IDLE]:
            logger.warning(f"⚠️  Agent {agent_id} not running (state: {managed.state})")
            return
        
        logger.info(f"⏹️  Stopping agent: {agent_id}")
        managed.state = AgentState.STOPPING
        
        # Stop agent instance (if it has cleanup methods)
        if managed.instance and hasattr(managed.instance, 'shutdown'):
            try:
                await managed.instance.shutdown()
            except Exception as e:
                logger.error(f"Error during agent shutdown: {e}")
        
        managed.instance = None
        managed.state = AgentState.STOPPED
        
        logger.info(f"✅ Agent stopped: {agent_id}")
    
    async def stop_all(self):
        """Stop all running agents."""
        logger.info("⏹️  Stopping all agents...")
        
        for agent_id, managed in self.agents.items():
            if managed.state in [AgentState.RUNNING, AgentState.IDLE]:
                await self.stop_agent(agent_id)
        
        logger.info("✅ All agents stopped")
    
    def get_agent_status(self) -> Dict[str, dict]:
        """
        Get status of all agents.
        
        Returns:
            Dictionary of agent statuses
        """
        status = {}
        
        for agent_id, managed in self.agents.items():
            status[agent_id] = {
                "agent_id": agent_id,
                "role": managed.config.role,
                "lifecycle": managed.lifecycle.value,
                "state": managed.state.value,
                "enabled": managed.config.enabled,
                "error": managed.error
            }
        
        return status
    
    def get_agent(self, agent_id: str) -> Optional[Any]:
        """
        Get agent instance.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            Agent instance or None
        """
        if agent_id in self.agents:
            return self.agents[agent_id].instance
        return None
