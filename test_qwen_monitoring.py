#!/usr/bin/env python3
"""
Test script to run Qwen agent with monitoring enabled.

This script:
1. Starts the monitoring service
2. Creates a Qwen agent with monitoring enabled
3. Simulates some work to show in the dashboard
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.monitor_service import get_monitor, AgentStatus
from agents.qwen_agent import QwenAgent


async def test_qwen_with_monitoring():
    """Test Qwen agent with monitoring dashboard."""
    
    # Start monitoring service
    monitor = get_monitor()
    await monitor.start()
    
    print("🧪 Testing Qwen Agent with Monitoring Dashboard")
    print("=" * 70)
    print("📊 Dashboard: http://localhost:8897/dashboard.html")
    print("🔌 WebSocket: ws://localhost:7997/ws/monitor")
    print("=" * 70)
    
    # Create Qwen agent with monitoring enabled
    print("\n1️⃣ Creating Qwen agent with monitoring...")
    agent = QwenAgent(
        config_path=None,  # Use default config
        enable_monitoring=True,
        agent_id="qwen-test-agent"
    )
    
    # Give dashboard time to connect
    await asyncio.sleep(2)
    
    # Simulate some activity
    print("\n2️⃣ Simulating agent activity...")
    
    # Start working
    agent._update_status(
        status=AgentStatus.WORKING,
        task="Testing monitoring integration",
        progress=0.0,
        phase="Phase 1: Initialization"
    )
    agent._log("INFO", "🚀 Started test task")
    await asyncio.sleep(2)
    
    # Progress 1
    agent._update_status(progress=25.0)
    agent._log("INFO", "✅ Monitoring integration working")
    agent._update_metrics(cpu=35.2, memory=48.5, api_calls=5)
    await asyncio.sleep(2)
    
    # Progress 2
    agent._update_status(
        progress=50.0,
        phase="Phase 2: Testing WebSocket"
    )
    agent._log("INFO", "📡 WebSocket connection established")
    agent._log("INFO", "📊 Dashboard receiving updates")
    await asyncio.sleep(2)
    
    # Progress 3
    agent._update_status(progress=75.0)
    agent._log("INFO", "🔄 Testing log streaming")
    agent._update_metrics(cpu=58.3, memory=62.1, api_calls=12)
    await asyncio.sleep(2)
    
    # Complete
    agent._update_status(
        status=AgentStatus.IDLE,
        progress=100.0,
        phase="Phase 3: Complete"
    )
    agent._log("INFO", "✅ Test completed successfully")
    agent._log("SUCCESS", "🎉 All monitoring features working!")
    
    print("\n3️⃣ Test completed!")
    print("=" * 70)
    print("📊 Dashboard showing agent activity")
    print("⏳ Keeping server running for live monitoring...")
    print("   Press Ctrl+C to stop\n")
    
    # Keep running for monitoring
    try:
        while True:
            await asyncio.sleep(10)
            # Send heartbeat
            agent._update_metrics(api_calls=12)
    except KeyboardInterrupt:
        print("\n⏹️ Stopping test...")
        await monitor.stop()


if __name__ == "__main__":
    try:
        asyncio.run(test_qwen_with_monitoring())
    except KeyboardInterrupt:
        print("\n👋 Test stopped")
