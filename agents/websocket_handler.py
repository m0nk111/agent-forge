"""
FastAPI WebSocket endpoints for real-time agent monitoring.

Provides:
- /ws/monitor - Real-time agent status updates
- /ws/logs/{agent_id} - Live log streaming for specific agent
- /api/agents - REST endpoint for agent list
- /api/agents/{agent_id}/status - Agent status endpoint
- /api/agents/{agent_id}/logs - Historical logs endpoint
- /api/activity - Activity timeline endpoint
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List
import json

from agents.monitor_service import get_monitor, AgentStatus


def setup_monitoring_routes(app: FastAPI):
    """
    Setup monitoring routes on FastAPI app.
    
    Args:
        app: FastAPI application instance
    """
    monitor = get_monitor()
    
    # WebSocket: Real-time agent status updates
    @app.websocket("/ws/monitor")
    async def websocket_monitor(websocket: WebSocket):
        """
        WebSocket endpoint for real-time agent monitoring.
        
        Clients receive:
        - agent_update: When any agent status changes
        - log_entry: When new log entries are added
        
        Message format:
        {
            "type": "agent_update" | "log_entry",
            "data": {...}
        }
        """
        await websocket.accept()
        await monitor.register_websocket(websocket)
        
        try:
            # Send initial state
            agents = monitor.get_all_agents()
            initial_message = {
                "type": "initial_state",
                "data": {
                    "agents": [agent.to_dict() for agent in agents]
                }
            }
            await websocket.send_text(json.dumps(initial_message))
            
            # Keep connection alive and handle client messages
            while True:
                # Wait for messages (ping/pong, subscriptions, etc.)
                try:
                    data = await websocket.receive_text()
                    message = json.loads(data)
                    
                    # Handle client messages
                    if message.get("type") == "ping":
                        await websocket.send_text(json.dumps({"type": "pong"}))
                    
                except json.JSONDecodeError:
                    pass
        
        except WebSocketDisconnect:
            pass
        finally:
            await monitor.unregister_websocket(websocket)
    
    # WebSocket: Live log streaming for specific agent
    @app.websocket("/ws/logs/{agent_id}")
    async def websocket_logs(websocket: WebSocket, agent_id: str):
        """
        WebSocket endpoint for live log streaming from specific agent.
        
        Sends log entries in real-time as they are added.
        """
        await websocket.accept()
        
        # Create filtered websocket wrapper
        class FilteredWebSocket:
            def __init__(self, ws, agent_id):
                self.ws = ws
                self.agent_id = agent_id
            
            async def send_text(self, data: str):
                message = json.loads(data)
                # Only send logs for this agent
                if message.get("type") == "log_entry":
                    if message["data"]["agent_id"] == self.agent_id:
                        await self.ws.send_text(data)
                # Send all other message types
                else:
                    await self.ws.send_text(data)
        
        filtered_ws = FilteredWebSocket(websocket, agent_id)
        await monitor.register_websocket(filtered_ws)
        
        try:
            # Send recent logs
            recent_logs = monitor.get_agent_logs(agent_id, limit=50)
            for log in reversed(recent_logs):  # Send in chronological order
                await websocket.send_text(json.dumps({
                    "type": "log_entry",
                    "data": log.to_dict()
                }))
            
            # Keep connection alive
            while True:
                try:
                    data = await websocket.receive_text()
                    message = json.loads(data)
                    
                    if message.get("type") == "ping":
                        await websocket.send_text(json.dumps({"type": "pong"}))
                
                except json.JSONDecodeError:
                    pass
        
        except WebSocketDisconnect:
            pass
        finally:
            await monitor.unregister_websocket(filtered_ws)
    
    # REST API: Get all agents
    @app.get("/api/agents")
    async def get_agents():
        """
        Get list of all agents and their current status.
        
        Returns:
            List of agent states
        """
        agents = monitor.get_all_agents()
        return {
            "agents": [agent.to_dict() for agent in agents],
            "total": len(agents)
        }
    
    # REST API: Get specific agent status
    @app.get("/api/agents/{agent_id}/status")
    async def get_agent_status(agent_id: str):
        """
        Get status for specific agent.
        
        Args:
            agent_id: Agent identifier
        
        Returns:
            Agent state
        """
        agent = monitor.get_agent_state(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
        
        return agent.to_dict()
    
    # REST API: Get agent logs
    @app.get("/api/agents/{agent_id}/logs")
    async def get_agent_logs(
        agent_id: str,
        limit: int = 100,
        level: Optional[str] = None
    ):
        """
        Get historical logs for specific agent.
        
        Args:
            agent_id: Agent identifier
            limit: Maximum number of logs to return (default 100)
            level: Filter by log level (INFO, WARNING, ERROR, DEBUG)
        
        Returns:
            List of log entries (most recent first)
        """
        if agent_id not in monitor.agents:
            raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
        
        logs = monitor.get_agent_logs(agent_id, limit=limit, level=level)
        return {
            "agent_id": agent_id,
            "logs": [log.to_dict() for log in logs],
            "total": len(logs)
        }
    
    # REST API: Get activity timeline
    @app.get("/api/activity")
    async def get_activity(
        agent_id: Optional[str] = None,
        limit: int = 100
    ):
        """
        Get activity timeline.
        
        Args:
            agent_id: Filter by specific agent (optional)
            limit: Maximum number of events to return (default 100)
        
        Returns:
            List of activity events (most recent first)
        """
        events = monitor.get_activity_timeline(agent_id=agent_id, limit=limit)
        return {
            "events": [event.to_dict() for event in events],
            "total": len(events)
        }
    
    print("✅ Monitoring routes registered:")
    print("   - WebSocket: ws://localhost:7997/ws/monitor")
    print("   - WebSocket: ws://localhost:7997/ws/logs/{agent_id}")
    print("   - REST: GET /api/agents")
    print("   - REST: GET /api/agents/{agent_id}/status")
    print("   - REST: GET /api/agents/{agent_id}/logs")
    print("   - REST: GET /api/activity")


def create_monitoring_app() -> FastAPI:
    """
    Create standalone FastAPI app for monitoring.
    
    Returns:
        FastAPI application with monitoring routes
    """
    app = FastAPI(
        title="Agent-Forge Monitoring API",
        description="Real-time agent monitoring and log streaming",
        version="0.1.0"
    )
    
    # CORS for frontend
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # In production, specify exact origins
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Setup routes
    setup_monitoring_routes(app)
    
    # Startup/shutdown events
    @app.on_event("startup")
    async def startup():
        monitor = get_monitor()
        await monitor.start()
        print("🚀 Monitoring service started")
    
    @app.on_event("shutdown")
    async def shutdown():
        monitor = get_monitor()
        await monitor.stop()
        print("⏹️ Monitoring service stopped")
    
    return app


if __name__ == "__main__":
    import uvicorn
    
    app = create_monitoring_app()
    
    print("🔄 Starting monitoring server on http://localhost:7997")
    print("📊 WebSocket endpoint: ws://localhost:7997/ws/monitor")
    print("📡 REST API: http://localhost:7997/api/agents")
    
    uvicorn.run(app, host="0.0.0.0", port=7997, log_level="info")
