# Qwen Agent Monitoring Integration

## Overview

The Qwen Agent now supports real-time monitoring dashboard integration, allowing you to track agent activity, progress, and logs in a live web interface.

## Features

- **Real-time Status Updates**: See agent status (idle, working, error, offline)
- **Progress Tracking**: Monitor task progress with phase information
- **Live Log Streaming**: View agent logs as they happen
- **Health Metrics**: Track CPU usage, memory usage, and API calls
- **Task Information**: See current task, issue number, and PR number

## Usage

### Enable Monitoring

Add the `--enable-monitoring` flag when running the Qwen agent:

```bash
python3 agents/code_agent.py --config configs/my_project.yaml --phase 1 --enable-monitoring
```

### Optional: Custom Agent ID

Specify a custom agent ID for better identification:

```bash
python3 agents/code_agent.py --config configs/my_project.yaml --phase 1 --enable-monitoring --agent-id "my-qwen-agent"
```

If not specified, an auto-generated ID will be used.

### View Dashboard

Open the monitoring dashboard in your browser:

```
http://localhost:8897/dashboard.html
```

The dashboard will automatically connect via WebSocket to `ws://localhost:7997/ws/monitor` and display real-time updates.

## Programmatic Usage

### In Your Code

```python
from agents.qwen_agent import CodeAgent

# Create agent with monitoring enabled
agent = CodeAgent(
    config_path="configs/my_project.yaml",
    enable_monitoring=True,
    agent_id="my-custom-agent-id"
)

# Use monitoring helper methods
agent._log("INFO", "Starting task...")
agent._update_status(
    status="working",
    task="Implementing feature X",
    issue=42,
    progress=25.0,
    phase="Phase 1: Analysis"
)
agent._update_metrics(
    cpu=35.2,
    memory=48.5,
    api_calls=10,
    api_rate_limit=4990
)
```

### Monitoring Helper Methods

The CodeAgent class provides three helper methods for monitoring:

#### `_log(level, message)`

Add a log entry to the monitoring dashboard.

**Parameters:**
- `level` (str): Log level - "INFO", "WARNING", "ERROR", "SUCCESS"
- `message` (str): Log message

**Example:**
```python
agent._log("INFO", "Processing file: main.py")
agent._log("SUCCESS", "Task completed successfully")
agent._log("ERROR", "Failed to parse configuration")
```

#### `_update_status(...)`

Update agent status and task information.

**Parameters:**
- `status` (str|AgentStatus): Agent status - "idle", "working", "error", "offline"
- `task` (str): Current task description
- `issue` (int): Current GitHub issue number
- `pr` (int): Current GitHub PR number
- `progress` (float): Progress percentage (0-100)
- `phase` (str): Current phase description
- `error` (str): Error message if status is "error"

**Example:**
```python
agent._update_status(
    status="working",
    task="Implementing authentication",
    issue=17,
    progress=50.0,
    phase="Phase 2: Implementation"
)
```

#### `_update_metrics(...)`

Update agent health metrics.

**Parameters:**
- `cpu` (float): CPU usage percentage (0-100)
- `memory` (float): Memory usage percentage (0-100)
- `api_calls` (int): Total API calls made
- `api_rate_limit` (int): Remaining API rate limit

**Example:**
```python
agent._update_metrics(
    cpu=58.3,
    memory=62.1,
    api_calls=45,
    api_rate_limit=4955
)
```

## Testing

Run the test script to verify monitoring integration:

```bash
python3 tests/test_qwen_monitoring.py
```

This will:
1. Start the monitoring service
2. Create a test agent with monitoring enabled
3. Simulate some activity (progress updates, logs, metrics)
4. Keep the server running so you can view the dashboard

The test script demonstrates all monitoring features and serves as a reference implementation.

## Architecture

### Components

1. **AgentMonitor** (`agents/monitor_service.py`)
   - Central monitoring service
   - Tracks all agent states
   - Manages WebSocket connections
   - Broadcasts updates to dashboard

2. **CodeAgent** (`agents/code_agent.py`)
   - Autonomous coding agent
   - Optional monitoring integration
   - Helper methods for status/log updates
   - Auto-registration with monitor service

3. **WebSocket Server** (`agents/websocket_handler.py`)
   - Real-time communication
   - Broadcasts agent updates
   - Handles client connections
   - Runs on port 7997

4. **Dashboard** (`frontend/dashboard.html`)
   - Web-based UI
   - Real-time updates via WebSocket
   - Agent status display
   - Live log streaming
   - Served on port 8897

### Data Flow

```
CodeAgent → AgentMonitor → WebSocket Server → Dashboard (Browser)
```

1. Agent calls `_log()`, `_update_status()`, or `_update_metrics()`
2. AgentMonitor updates internal state
3. WebSocket server broadcasts update to connected clients
4. Dashboard receives update and refreshes UI

## Implementation Details

### Initialization

Monitoring is opt-in and initialized during agent creation:

```python
def __init__(
    self,
    config_path: Optional[str] = None,
    model: Optional[str] = None,
    ollama_url: str = "http://localhost:11434",
    project_root: Optional[str] = None,
    enable_monitoring: bool = False,  # <-- New parameter
    agent_id: Optional[str] = None     # <-- New parameter
):
    # ... existing initialization ...
    
    # Initialize monitoring (optional)
    self.monitor = None
    self.agent_id = agent_id or f"qwen-agent-{id(self)}"
    if enable_monitoring:
        try:
            from .monitor_service import get_monitor
            self.monitor = get_monitor()
            self.monitor.register_agent(self.agent_id, f"Qwen Agent - {self.project_name}")
            self.print_success(f"Monitoring enabled for agent {self.agent_id}")
        except Exception as e:
            self.print_warning(f"Could not enable monitoring: {e}")
            self.monitor = None
```

### Helper Methods

All helper methods check if monitoring is enabled before calling monitor service:

```python
def _log(self, level: str, message: str):
    """Add log entry to monitor if enabled"""
    if self.monitor:
        self.monitor.add_log(self.agent_id, level, message)
```

This means you can safely call monitoring methods even if monitoring is disabled - they will simply do nothing.

## Best Practices

1. **Use Descriptive Task Names**: Make task descriptions clear and specific
2. **Update Progress Regularly**: Update progress at meaningful checkpoints
3. **Log Important Events**: Log key decisions, errors, and completions
4. **Phase Names**: Use clear phase names to show workflow stages
5. **Metrics Updates**: Update metrics when they change significantly

## Example Integration

Here's how to integrate monitoring into an existing Qwen agent workflow:

```python
def execute_phase(self, phase_num: int, dry_run: bool = False) -> bool:
    """Execute a single phase with monitoring."""
    
    if phase_num not in self.phases:
        self.print_error(f"Phase {phase_num} not found in config")
        return False
    
    phase = self.phases[phase_num]
    phase_name = phase.get('name', f'Phase {phase_num}')
    
    # Update status: Starting phase
    self._update_status(
        status="working",
        task=f"Executing {phase_name}",
        progress=0.0,
        phase=phase_name
    )
    self._log("INFO", f"🚀 Starting {phase_name}")
    
    tasks = phase.get('tasks', [])
    total_tasks = len(tasks)
    
    for i, task_desc in enumerate(tasks, 1):
        # Update progress for each task
        progress = (i / total_tasks) * 100
        self._update_status(progress=progress)
        self._log("INFO", f"📝 Task {i}/{total_tasks}: {task_desc}")
        
        # Execute task...
        success = self.execute_task(task_desc, dry_run)
        
        if success:
            self._log("SUCCESS", f"✅ Completed: {task_desc}")
        else:
            self._log("ERROR", f"❌ Failed: {task_desc}")
            self._update_status(
                status="error",
                error=f"Failed to complete task: {task_desc}"
            )
            return False
    
    # Phase complete
    self._update_status(
        status="idle",
        progress=100.0
    )
    self._log("SUCCESS", f"🎉 Completed {phase_name}")
    
    return True
```

## Troubleshooting

### Agent Not Appearing in Dashboard

1. Verify monitoring is enabled: `--enable-monitoring` flag
2. Check if AgentMonitor is running (should see "🔄 AgentMonitor started")
3. Verify WebSocket server is running on port 7997
4. Check browser console for WebSocket connection errors

### WebSocket Connection Failed

1. Ensure nothing else is using port 7997
2. Check firewall settings
3. Verify HTTP server is running on port 8897
4. Try connecting to `ws://localhost:7997/ws/monitor` directly

### Logs Not Appearing

1. Verify monitoring is enabled on the agent
2. Check if `_log()` calls are being made
3. Verify WebSocket connection is active (check dashboard footer)
4. Look for errors in terminal output

## Future Enhancements

Potential improvements for monitoring integration:

- [ ] Multiple agent support (parallel monitoring)
- [ ] Historical data persistence (database storage)
- [ ] Performance metrics graphs (charts/visualization)
- [ ] Alert notifications (Slack, email)
- [ ] Agent comparison view (side-by-side)
- [ ] Export logs to file
- [ ] Advanced filtering and search
- [ ] Pause/resume agent from dashboard
- [ ] Remote command execution
- [ ] Mobile-responsive dashboard

## Related Files

- `agents/code_agent.py` - Main agent with monitoring integration
- `agents/monitor_service.py` - Monitoring service and state management
- `agents/websocket_handler.py` - WebSocket server for real-time updates
- `frontend/dashboard.html` - Web dashboard UI
- `tests/test_qwen_monitoring.py` - Test script demonstrating monitoring
- `scripts/demo_qwen_working.py` - Simulation of agent working on issues

## See Also

- [Agent Forge README](../README.md) - Main project documentation
- [Issue #27](https://github.com/m0nk111/agent-forge/issues/27) - Unified dashboard implementation
- [Architecture Documentation](../docs/ARCHITECTURE.md) - System architecture
