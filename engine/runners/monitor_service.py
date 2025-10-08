"""
Real-time agent monitoring service for tracking agent status, logs, and progress.

This service provides:
- Agent status tracking (active, idle, working, error)
- Live log streaming
- Progress tracking with phase information
- Historical activity timeline
- Health metrics (CPU, memory, API usage)
"""

import asyncio
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Set
from collections import deque


class AgentStatus(str, Enum):
    """Agent status states."""
    IDLE = "idle"
    WORKING = "working"
    ERROR = "error"
    OFFLINE = "offline"


@dataclass
class AgentState:
    """Current state of an agent."""
    agent_id: str
    agent_name: str
    status: AgentStatus
    current_task: Optional[str] = None
    current_issue: Optional[int] = None
    current_pr: Optional[int] = None
    progress: float = 0.0  # 0-100
    phase: Optional[str] = None
    started_at: Optional[float] = None
    last_update: float = field(default_factory=time.time)
    error_message: Optional[str] = None
    
    # Health metrics
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    api_calls: int = 0
    api_rate_limit_remaining: int = 5000
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data['status'] = self.status.value
        return data


@dataclass
class LogEntry:
    """Log entry from an agent."""
    timestamp: float
    agent_id: str
    level: str  # INFO, WARNING, ERROR, DEBUG
    message: str
    context: Optional[dict] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


@dataclass
class ActivityEvent:
    """Historical activity event."""
    timestamp: float
    agent_id: str
    event_type: str  # issue_claimed, issue_completed, pr_created, pr_merged, error
    description: str
    metadata: Optional[dict] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


class AgentMonitor:
    """
    Real-time agent monitoring service.
    
    Tracks agent states, logs, and activity across multiple agents.
    Provides WebSocket API for live updates to dashboard.
    """
    
    def __init__(self, max_logs_per_agent: int = 1000, max_activity_events: int = 10000):
        """
        Initialize agent monitor.
        
        Args:
            max_logs_per_agent: Maximum log entries to store per agent
            max_activity_events: Maximum activity events to store globally
        """
        self.agents: Dict[str, AgentState] = {}
        self.services: Dict[str, dict] = {}  # Service health status
        self.logs: Dict[str, deque] = {}  # agent_id -> deque of LogEntry
        self.activity: deque = deque(maxlen=max_activity_events)
        self.max_logs_per_agent = max_logs_per_agent
        
        # WebSocket connections
        self.websocket_clients: Set[object] = set()
        
        # Background tasks
        self._running = False
        self._cleanup_task: Optional[asyncio.Task] = None
    
    async def start(self):
        """Start monitoring service."""
        if self._running:
            return
        
        self._running = True
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        print("🔄 AgentMonitor started")
    
    async def stop(self):
        """Stop monitoring service."""
        self._running = False
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        print("⏹️ AgentMonitor stopped")
    
    def register_agent(self, agent_id: str, agent_name: str) -> AgentState:
        """
        Register a new agent for monitoring.
        
        Args:
            agent_id: Unique agent identifier
            agent_name: Human-readable agent name
        
        Returns:
            AgentState: Initial agent state
        """
        if agent_id not in self.agents:
            state = AgentState(
                agent_id=agent_id,
                agent_name=agent_name,
                status=AgentStatus.IDLE
            )
            self.agents[agent_id] = state
            self.logs[agent_id] = deque(maxlen=self.max_logs_per_agent)
            
            # Log activity
            self._add_activity(
                agent_id=agent_id,
                event_type="agent_registered",
                description=f"Agent {agent_name} registered"
            )
            
            # Notify clients
            asyncio.create_task(self._broadcast_agent_update(agent_id))
            
            print(f"✅ Agent registered: {agent_name} ({agent_id})")
        
        return self.agents[agent_id]
    
    def update_agent_status(
        self,
        agent_id: str,
        status: Optional[AgentStatus] = None,
        current_task: Optional[str] = None,
        current_issue: Optional[int] = None,
        current_pr: Optional[int] = None,
        progress: Optional[float] = None,
        phase: Optional[str] = None,
        error_message: Optional[str] = None
    ):
        """
        Update agent status.
        
        Args:
            agent_id: Agent identifier
            status: New status
            current_task: Current task description
            current_issue: Current issue number
            current_pr: Current PR number
            progress: Progress percentage (0-100)
            phase: Current phase description
            error_message: Error message if status is ERROR
        """
        if agent_id not in self.agents:
            print(f"⚠️ Unknown agent: {agent_id}")
            return
        
        agent = self.agents[agent_id]
        old_status = agent.status
        
        # Update fields
        if status is not None:
            agent.status = status
            if status == AgentStatus.WORKING and agent.started_at is None:
                agent.started_at = time.time()
            elif status in (AgentStatus.IDLE, AgentStatus.ERROR):
                agent.started_at = None
        
        # Always update these fields when explicitly provided (even if None to clear)
        # Only skip update if parameter was not provided at all (using **kwargs pattern would be better)
        # For now, we update whenever the function is called with the parameter
        agent.current_task = current_task
        agent.current_issue = current_issue
        agent.current_pr = current_pr
        
        if progress is not None:
            agent.progress = max(0.0, min(100.0, progress))
        
        agent.phase = phase
        agent.error_message = error_message
        
        agent.last_update = time.time()
        
        # Log status changes
        if status is not None and status != old_status:
            self._add_activity(
                agent_id=agent_id,
                event_type="status_changed",
                description=f"Status changed: {old_status.value} → {status.value}",
                metadata={"old_status": old_status.value, "new_status": status.value}
            )
        
        # Notify clients
        asyncio.create_task(self._broadcast_agent_update(agent_id))
    
    def update_services(self, services: Dict[str, bool]):
        """
        Update service health status.
        
        Args:
            services: Dictionary of service_name -> healthy (bool)
        """
        timestamp = time.time()
        for service_name, healthy in services.items():
            self.services[service_name] = {
                "name": service_name,
                "status": "online" if healthy else "offline",
                "healthy": healthy,
                "last_update": timestamp
            }
    
    def get_services(self) -> Dict[str, dict]:
        """
        Get all service statuses.
        
        Returns:
            Dictionary of service statuses
        """
        return self.services.copy()
    
    def update_agent_metrics(
        self,
        agent_id: str,
        cpu_usage: Optional[float] = None,
        memory_usage: Optional[float] = None,
        api_calls: Optional[int] = None,
        api_rate_limit_remaining: Optional[int] = None
    ):
        """
        Update agent health metrics.
        
        Args:
            agent_id: Agent identifier
            cpu_usage: CPU usage percentage (0-100)
            memory_usage: Memory usage percentage (0-100)
            api_calls: Total API calls made
            api_rate_limit_remaining: Remaining API rate limit
        """
        if agent_id not in self.agents:
            return
        
        agent = self.agents[agent_id]
        
        if cpu_usage is not None:
            agent.cpu_usage = cpu_usage
        if memory_usage is not None:
            agent.memory_usage = memory_usage
        if api_calls is not None:
            agent.api_calls = api_calls
        if api_rate_limit_remaining is not None:
            agent.api_rate_limit_remaining = api_rate_limit_remaining
        
        agent.last_update = time.time()
        
        # Notify clients (metrics update)
        asyncio.create_task(self._broadcast_agent_update(agent_id))
    
    def add_log(
        self,
        agent_id: str,
        level: str,
        message: str,
        context: Optional[dict] = None
    ):
        """
        Add log entry for agent.
        
        Args:
            agent_id: Agent identifier
            level: Log level (INFO, WARNING, ERROR, DEBUG)
            message: Log message
            context: Optional context dictionary
        """
        if agent_id not in self.logs:
            return
        
        entry = LogEntry(
            timestamp=time.time(),
            agent_id=agent_id,
            level=level,
            message=message,
            context=context
        )
        
        self.logs[agent_id].append(entry)
        
        # Notify clients (log update)
        asyncio.create_task(self._broadcast_log_entry(entry))
    
    def _add_activity(
        self,
        agent_id: str,
        event_type: str,
        description: str,
        metadata: Optional[dict] = None
    ):
        """Add activity event."""
        event = ActivityEvent(
            timestamp=time.time(),
            agent_id=agent_id,
            event_type=event_type,
            description=description,
            metadata=metadata
        )
        self.activity.append(event)
    
    def get_agent_state(self, agent_id: str) -> Optional[AgentState]:
        """Get current agent state."""
        return self.agents.get(agent_id)
    
    def get_all_agents(self) -> List[AgentState]:
        """Get all agent states (active + configured)."""
        from engine.core.config_manager import get_config_manager
        
        # Start with active agents
        all_agents = list(self.agents.values())
        active_ids = {agent.agent_id for agent in all_agents}
        
        # Add configured agents that aren't active
        try:
            config_manager = get_config_manager()
            configured_agents = config_manager.get_agents()
            
            for agent_config in configured_agents:
                if agent_config.agent_id not in active_ids:
                    # Create inactive agent state
                    inactive_state = AgentState(
                        agent_id=agent_config.agent_id,
                        agent_name=agent_config.name or agent_config.agent_id,
                        status=AgentStatus.OFFLINE,
                        current_task="Agent configured but not running",
                        progress=0.0,
                        last_update=time.time()
                    )
                    all_agents.append(inactive_state)
        except Exception as e:
            # Log error but don't fail - return active agents only
            import logging
            logging.error(f"❌ Failed to load configured agents: {e}")
        
        return all_agents
    
    def get_agent_logs(
        self,
        agent_id: str,
        limit: int = 100,
        level: Optional[str] = None
    ) -> List[LogEntry]:
        """
        Get agent logs.
        
        Args:
            agent_id: Agent identifier
            limit: Maximum number of logs to return
            level: Filter by log level
        
        Returns:
            List of log entries (most recent first)
        """
        if agent_id not in self.logs:
            return []
        
        logs = list(self.logs[agent_id])
        
        # Filter by level if specified
        if level:
            logs = [log for log in logs if log.level == level]
        
        # Return most recent first
        logs.reverse()
        return logs[:limit]
    
    def get_activity_timeline(
        self,
        agent_id: Optional[str] = None,
        limit: int = 100
    ) -> List[ActivityEvent]:
        """
        Get activity timeline.
        
        Args:
            agent_id: Filter by specific agent (None for all agents)
            limit: Maximum number of events to return
        
        Returns:
            List of activity events (most recent first)
        """
        events = list(self.activity)
        
        # Filter by agent if specified
        if agent_id:
            events = [e for e in events if e.agent_id == agent_id]
        
        # Return most recent first
        events.reverse()
        return events[:limit]
    
    async def register_websocket(self, websocket):
        """Register WebSocket client for live updates."""
        self.websocket_clients.add(websocket)
        print(f"🔌 WebSocket client connected (total: {len(self.websocket_clients)})")
    
    async def unregister_websocket(self, websocket):
        """Unregister WebSocket client."""
        self.websocket_clients.discard(websocket)
        print(f"🔌 WebSocket client disconnected (total: {len(self.websocket_clients)})")
    
    async def _broadcast_agent_update(self, agent_id: str):
        """Broadcast agent state update to all WebSocket clients."""
        if not self.websocket_clients:
            return
        
        agent = self.agents.get(agent_id)
        if not agent:
            return
        
        message = {
            "type": "agent_update",
            "agent": agent.to_dict()  # Changed from "data" to "agent" for frontend compatibility
        }
        
        await self._broadcast(message)
    
    async def _broadcast_log_entry(self, entry: LogEntry):
        """Broadcast log entry to all WebSocket clients."""
        if not self.websocket_clients:
            return
        
        message = {
            "type": "log_entry",
            "agent_id": entry.agent_id,  # Add agent_id at top level for frontend
            "log": entry.to_dict()        # Log data nested for compatibility
        }
        
        await self._broadcast(message)
    
    async def _broadcast(self, message: dict):
        """Broadcast message to all WebSocket clients."""
        if not self.websocket_clients:
            return
        
        import json
        message_json = json.dumps(message)
        
        # Send to all clients
        disconnected = set()
        for client in self.websocket_clients:
            try:
                await client.send_text(message_json)
            except Exception:
                disconnected.add(client)
        
        # Remove disconnected clients
        for client in disconnected:
            self.websocket_clients.discard(client)
    
    async def _cleanup_loop(self):
        """Background task to detect offline agents."""
        while self._running:
            try:
                await asyncio.sleep(60)  # Check every minute
                
                current_time = time.time()
                timeout = 300  # 5 minutes
                
                for agent_id, agent in self.agents.items():
                    if agent.status != AgentStatus.OFFLINE:
                        if current_time - agent.last_update > timeout:
                            print(f"⚠️ Agent {agent_id} timed out (no updates for {timeout}s)")
                            agent.status = AgentStatus.OFFLINE
                            agent.started_at = None
                            await self._broadcast_agent_update(agent_id)
            
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"❌ Cleanup loop error: {e}")


# Global monitor instance
_monitor: Optional[AgentMonitor] = None


def get_monitor() -> AgentMonitor:
    """Get global agent monitor instance."""
    global _monitor
    if _monitor is None:
        _monitor = AgentMonitor()
    return _monitor
