#!/usr/bin/env python3
"""Test script to register a dummy agent with the monitor."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from engine.runners.monitor_service import get_monitor, AgentStatus


async def main():
    """Register test agent and update status."""
    monitor = get_monitor()
    await monitor.start()
    
    print("📡 Registering test agent...")
    
    # Register agent (not async)
    monitor.register_agent(
        agent_id="test-agent-1",
        agent_name="Test Agent (Polling Service)"
    )
    
    # Update status (not async)
    monitor.update_agent_status(
        agent_id="test-agent-1",
        status=AgentStatus.IDLE,
        current_task="Waiting for issues..."
    )
    
    # Log some messages (not async)
    monitor.add_log(
        agent_id="test-agent-1",
        level="INFO",
        message="Test agent registered successfully"
    )
    
    monitor.add_log(
        agent_id="test-agent-1",
        level="INFO",
        message="Polling repositories for new issues"
    )
    
    print("✅ Test agent registered!")
    print("🌐 Check dashboard at: http://192.168.1.26:8897/dashboard.html")
    print("   You should see 'Test Agent (Polling Service)' in IDLE state")
    print()
    print("Press Ctrl+C to exit (agent will remain registered)")
    
    # Keep running
    try:
        while True:
            await asyncio.sleep(10)
            monitor.add_log(
                agent_id="test-agent-1",
                level="INFO",
                message=f"Heartbeat - agent still alive"
            )
    except KeyboardInterrupt:
        print("\n👋 Exiting...")


if __name__ == "__main__":
    asyncio.run(main())
