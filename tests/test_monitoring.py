#!/usr/bin/env python3
"""
Test script for agent monitoring service.

Demonstrates:
- Agent registration
- Status updates
- Log streaming
- Progress tracking
- WebSocket connectivity
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import time
from engine.runners.monitor_service import get_monitor, AgentStatus


async def simulate_agent_activity():
    """Simulate agent activity for testing."""
    monitor = get_monitor()
    await monitor.start()
    
    print("🧪 Starting monitoring test...\n")
    
    # Register test agents
    print("1️⃣ Registering agents...")
    agent1 = monitor.register_agent("qwen-agent-1", "Qwen Agent 1")
    agent2 = monitor.register_agent("qwen-agent-2", "Qwen Agent 2")
    print(f"   ✅ Registered: {agent1.agent_name}")
    print(f"   ✅ Registered: {agent2.agent_name}\n")
    
    await asyncio.sleep(1)
    
    # Agent 1: Start working on issue #17
    print("2️⃣ Agent 1: Starting work on issue #17...")
    monitor.update_agent_status(
        agent_id="qwen-agent-1",
        status=AgentStatus.WORKING,
        current_task="Implementing polling service",
        current_issue=17,
        progress=10.0,
        phase="Phase 1: Analyzing requirements"
    )
    monitor.add_log("qwen-agent-1", "INFO", "🚀 Started working on issue #17")
    monitor.add_log("qwen-agent-1", "INFO", "📖 Reading issue requirements...")
    print("   ✅ Agent 1 now WORKING\n")
    
    await asyncio.sleep(2)
    
    # Agent 2: Start working on issue #18
    print("3️⃣ Agent 2: Starting work on issue #18...")
    monitor.update_agent_status(
        agent_id="qwen-agent-2",
        status=AgentStatus.WORKING,
        current_task="Implementing instruction validator",
        current_issue=18,
        progress=15.0,
        phase="Phase 1: Parsing copilot instructions"
    )
    monitor.add_log("qwen-agent-2", "INFO", "🚀 Started working on issue #18")
    monitor.add_log("qwen-agent-2", "INFO", "📖 Parsing copilot-instructions.md...")
    print("   ✅ Agent 2 now WORKING\n")
    
    await asyncio.sleep(2)
    
    # Agent 1: Progress update
    print("4️⃣ Agent 1: Progress update (30%)...")
    monitor.update_agent_status(
        agent_id="qwen-agent-1",
        progress=30.0,
        phase="Phase 2: Implementing PollingService"
    )
    monitor.add_log("qwen-agent-1", "INFO", "✅ Created agents/polling_service.py")
    monitor.add_log("qwen-agent-1", "INFO", "🔄 Implementing async polling loop...")
    monitor.update_agent_metrics(
        agent_id="qwen-agent-1",
        cpu_usage=45.2,
        memory_usage=62.3,
        api_calls=15,
        api_rate_limit_remaining=4985
    )
    print("   ✅ Agent 1 progress: 30%\n")
    
    await asyncio.sleep(2)
    
    # Agent 2: Warning
    print("5️⃣ Agent 2: Warning encountered...")
    monitor.add_log("qwen-agent-2", "WARNING", "⚠️ Complex rule found: may need LLM interpretation")
    monitor.add_log("qwen-agent-2", "INFO", "🔧 Adding LLM-based rule parser...")
    print("   ⚠️ Agent 2 logged warning\n")
    
    await asyncio.sleep(2)
    
    # Agent 1: More progress
    print("6️⃣ Agent 1: Progress update (60%)...")
    monitor.update_agent_status(
        agent_id="qwen-agent-1",
        progress=60.0,
        phase="Phase 3: Adding tests"
    )
    monitor.add_log("qwen-agent-1", "INFO", "✅ Created config/polling_config.yaml")
    monitor.add_log("qwen-agent-1", "INFO", "✅ Created scripts/start_polling.py")
    monitor.add_log("qwen-agent-1", "INFO", "🧪 Writing tests...")
    print("   ✅ Agent 1 progress: 60%\n")
    
    await asyncio.sleep(2)
    
    # Agent 2: Error!
    print("7️⃣ Agent 2: Error encountered!")
    monitor.update_agent_status(
        agent_id="qwen-agent-2",
        status=AgentStatus.ERROR,
        error_message="Failed to parse instruction file: Invalid YAML format"
    )
    monitor.add_log(
        "qwen-agent-2",
        "ERROR",
        "❌ Failed to parse copilot-instructions.md",
        context={"error": "Invalid YAML format", "line": 42}
    )
    print("   ❌ Agent 2 encountered error\n")
    
    await asyncio.sleep(2)
    
    # Agent 2: Recovering
    print("8️⃣ Agent 2: Recovering from error...")
    monitor.update_agent_status(
        agent_id="qwen-agent-2",
        status=AgentStatus.WORKING,
        error_message=None
    )
    monitor.add_log("qwen-agent-2", "INFO", "✅ Error resolved: using markdown parser instead")
    print("   ✅ Agent 2 recovered\n")
    
    await asyncio.sleep(2)
    
    # Agent 1: Completing
    print("9️⃣ Agent 1: Completing work (100%)...")
    monitor.update_agent_status(
        agent_id="qwen-agent-1",
        progress=100.0,
        phase="Phase 4: Creating PR",
        current_pr=26
    )
    monitor.add_log("qwen-agent-1", "INFO", "✅ All tests passing (85% coverage)")
    monitor.add_log("qwen-agent-1", "INFO", "🎉 Created PR #26")
    await asyncio.sleep(1)
    monitor.update_agent_status(
        agent_id="qwen-agent-1",
        status=AgentStatus.IDLE,
        current_task=None,
        current_issue=None,
        progress=0.0,
        phase=None
    )
    print("   ✅ Agent 1 completed issue #17!\n")
    
    await asyncio.sleep(2)
    
    # Show summary
    print("=" * 60)
    print("📊 MONITORING SUMMARY")
    print("=" * 60)
    
    agents = monitor.get_all_agents()
    for agent in agents:
        print(f"\n🤖 {agent.agent_name} ({agent.agent_id})")
        print(f"   Status: {agent.status.value}")
        print(f"   Task: {agent.current_task or 'None'}")
        print(f"   Progress: {agent.progress}%")
        print(f"   API calls: {agent.api_calls}")
        print(f"   CPU: {agent.cpu_usage}%")
        print(f"   Memory: {agent.memory_usage}%")
    
    print(f"\n📜 Recent Activity:")
    activity = monitor.get_activity_timeline(limit=5)
    for event in activity:
        timestamp = time.strftime("%H:%M:%S", time.localtime(event.timestamp))
        print(f"   [{timestamp}] {event.event_type}: {event.description}")
    
    print("\n✅ Test complete! Monitoring service working correctly.\n")
    print("🚀 Next steps:")
    print("   1. Start WebSocket server: python agents/websocket_handler.py")
    print("   2. Connect dashboard to ws://localhost:7997/ws/monitor")
    print("   3. View live updates in browser!")
    
    # Keep running for WebSocket testing
    print("\n⏳ Keeping service alive for 30 seconds (for WebSocket testing)...")
    await asyncio.sleep(30)
    
    await monitor.stop()


if __name__ == "__main__":
    asyncio.run(simulate_agent_activity())
