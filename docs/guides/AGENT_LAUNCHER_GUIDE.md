# Agent Launcher Guide

Complete guide for using the universal agent launcher in Agent-Forge.

## Overview

The agent launcher (`scripts/launch_agent.py`) is a universal tool that automatically discovers and launches any agent profile from the `config/agents/` directory. It supports multiple LLM providers (OpenAI GPT-4, Anthropic Claude, Google Gemini, local Ollama) and provides interactive and direct issue handling modes.

## Features

- **Auto-Discovery**: Scans `config/agents/` directory for all available agent profiles
- **Multi-Provider**: Supports OpenAI, Anthropic, Google, and local Ollama models
- **Fuzzy Matching**: Use short names (e.g., "gpt4" matches "gpt4-coding-agent")
- **Interactive Mode**: Shell-like interface with agent selection and commands
- **Direct Issue Handling**: Autonomous issue resolution from command line
- **Profile Validation**: Checks API keys and tokens before launching

## Quick Start

```bash
# List all available agents
python3 scripts/launch_agent.py --list

# Launch specific agent
python3 scripts/launch_agent.py --agent gpt4-coding-agent

# Handle issue with specific agent
python3 scripts/launch_agent.py --agent gpt4 --issue 92

# Interactive mode with agent selection
python3 scripts/launch_agent.py --interactive
```

## Available Agents

The launcher scans `config/agents/*.yaml` for agent profiles. Currently available:

- **gpt4-coding-agent**: OpenAI GPT-4 for commercial-grade code generation (~$0.25/issue)
- **local-agent-qwen**: Local Qwen model via Ollama (free, good for development)
- **your-agent**: Production Qwen agent with GitHub integration
- **your-bot-agent**: Bot agent for GitHub operations

## Setup

### 1. API Keys (if using commercial providers)

For OpenAI agents (like `gpt4-coding-agent`), add your API key to `keys.json`:

```json
{
  "OPENAI_API_KEY": "sk-proj-..."
}
```

For other providers:
- **Anthropic**: Add `ANTHROPIC_API_KEY`
- **Google**: Add `GOOGLE_API_KEY`
- **Local Ollama**: No API key needed

### 2. GitHub Token (optional, for issue handling)

If you want agents to handle GitHub issues, set the environment variable:

```bash
export CODEAGENT_GITHUB_TOKEN="ghp_..."
```

Or add to your shell profile (`.bashrc`, `.zshrc`):

```bash
echo 'export CODEAGENT_GITHUB_TOKEN="ghp_..."' >> ~/.bashrc
source ~/.bashrc
```

### 3. Test Connection

```bash
python3 scripts/launch_agent.py --agent gpt4
```

Should output:
```
✅ Agent ready
```

## Usage

### List Available Agents

```bash
python3 scripts/launch_agent.py --list
```

Output:
```
📋 Available Agent Profiles:
====================================================================================================
ID                        Name                      Provider        Model                Role      
----------------------------------------------------------------------------------------------------
gpt4-coding-agent         GPT-4 Code Generator      openai          gpt-4                developer 
local-agent-qwen          Local Development Agent   local           qwen2.5-coder:7b     developer 
your-bot-agent               M0nk111 Bot Agent         local           qwen2.5-coder:7b     bot       
your-agent        M0nk111 Qwen Agent        local           qwen2.5-coder:7b     developer 
====================================================================================================
```

### Interactive Mode with Agent Selection

```bash
python3 scripts/launch_agent.py --interactive
```

This will:
1. Show all available agents
2. Let you select one by number or ID
3. Launch interactive shell with commands

Example session:
```
🤖 Agent-Forge Interactive Mode
============================================================

Select an agent to launch:
  1. gpt4-coding-agent (openai gpt-4)
  2. local-agent-qwen (local qwen2.5-coder:7b)
  3. your-bot-agent (local qwen2.5-coder:7b)
  4. your-agent (local qwen2.5-coder:7b)

Enter number or agent ID (or 'quit'): 1

✅ Agent gpt4-coding-agent loaded successfully!

Available commands:
  query <prompt>    - Query the agent
  issue <number>    - Handle GitHub issue
  info              - Show agent info
  cost              - Show cost estimates
  help              - Show this help
  quit              - Exit

[gpt4-coding-agent]> query Write a binary search function

📝 Response:
def binary_search(arr: list, target: int) -> int:
    """Binary search implementation."""
    left, right = 0, len(arr) - 1
    while left <= right:
        mid = (left + right) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    return -1

[gpt4-coding-agent]> cost

💰 Cost Estimates (GPT-4):
  Simple query: ~$0.05
  Code generation: ~$0.15
  Full issue resolution: ~$0.25

[gpt4-coding-agent]> quit
👋 Goodbye!
```

### Launch Specific Agent

```bash
# Full agent ID
python3 scripts/launch_agent.py --agent gpt4-coding-agent

# Fuzzy matching (shorter)
python3 scripts/launch_agent.py --agent gpt4

# Local agent (free)
python3 scripts/launch_agent.py --agent local
```

### Direct Issue Handling

```bash
python3 scripts/launch_agent.py --agent gpt4 --issue 92
```

This will:
1. Load the GPT-4 agent
2. Fetch issue #92 from GitHub
3. Generate code solution
4. Run tests and validation
5. Create pull request
6. Add completion comment

Example output:
```
🚀 Creating agent: gpt4-coding-agent
   Provider: openai
   Model: gpt-4
🔌 Testing agent connection...
✅ Agent ready
🎫 Handling issue #92 in your-org/your-project
📝 Generating implementation...
🧪 Running tests...
✅ Tests passed (coverage: 85%)
📤 Creating pull request...
✅ Issue #92 handled successfully!
```

### Custom Repository

```bash
python3 scripts/launch_agent.py --agent gpt4 --issue 5 --repo owner/repo
```

### Custom Config Directory

```bash
python3 scripts/launch_agent.py --config-dir /path/to/configs --list
```

## Configuration

### Agent Profile Structure

Agent profiles are YAML files in `config/agents/` with this structure:

```yaml
# Required fields (root level)
agent_id: "my-agent"
name: "My Custom Agent"
role: "developer"
model_provider: "openai"  # openai, anthropic, google, local
model_name: "gpt-4"

# API key (for commercial providers)
api_key_name: "OPENAI_API_KEY"  # Key name in keys.json

# Optional: Temperature setting
temperature: 0.7

# Optional: Max tokens
max_tokens: 4096

# Optional: GitHub integration
github:
  username: "bot-username"
  email: "bot@example.com"
  token_env: "GITHUB_TOKEN"

# Optional: Fallback configuration
fallback:
  enabled: true
  provider: "local"
  model: "qwen2.5-coder:7b"
```

### Creating New Agent Profile

1. Create YAML file in `config/agents/`:

```bash
nano config/agents/my-agent.yaml
```

2. Add configuration:

```yaml
agent_id: "my-agent"
name: "My Agent"
role: "developer"
model_provider: "openai"
model_name: "gpt-4"
api_key_name: "OPENAI_API_KEY"
```

3. Test it:

```bash
python3 scripts/launch_agent.py --agent my-agent
```

### Provider-Specific Settings

**OpenAI**:
```yaml
model_provider: "openai"
model_name: "gpt-4"  # or gpt-3.5-turbo
api_key_name: "OPENAI_API_KEY"
```

**Anthropic (Claude)**:
```yaml
model_provider: "anthropic"
model_name: "claude-3-opus-20240229"
api_key_name: "ANTHROPIC_API_KEY"
```

**Google (Gemini)**:
```yaml
model_provider: "google"
model_name: "gemini-pro"
api_key_name: "GOOGLE_API_KEY"
```

**Local (Ollama)**:
```yaml
model_provider: "local"
model_name: "qwen2.5-coder:7b"  # No API key needed
```

## Cost Optimization

### Cost by Provider

| Provider | Model | Input | Output | Issue Cost |
|----------|-------|--------|--------|------------|
| OpenAI | GPT-4 | $0.03/1K | $0.06/1K | ~$0.25 |
| OpenAI | GPT-3.5 | $0.0005/1K | $0.0015/1K | ~$0.01 |
| Anthropic | Claude-3 | $0.015/1K | $0.075/1K | ~$0.20 |
| Local | Ollama | Free | Free | $0.00 |

### Strategies

1. **Development**: Use local Qwen agent (free)
   ```bash
   python3 scripts/launch_agent.py --agent local
   ```

2. **Production**: Use GPT-4 for quality
   ```bash
   python3 scripts/launch_agent.py --agent gpt4
   ```

3. **Simple Tasks**: Use GPT-3.5 to save money
   ```yaml
   model_name: "gpt-3.5-turbo"  # 25x cheaper than GPT-4
   ```

4. **Fallback**: Configure automatic fallback to local
   ```yaml
   fallback:
     enabled: true
     provider: "local"
   ```

## Troubleshooting

### "Agent not found"

Check available agents:
```bash
python3 scripts/launch_agent.py --list
```

Make sure your profile has `agent_id` at root level:
```yaml
agent_id: "my-agent"  # ← Must be here
name: "My Agent"
```

### "API key not found"

Add key to `keys.json`:
```bash
nano keys.json
```

```json
{
  "OPENAI_API_KEY": "sk-proj-..."
}
```

Verify:
```bash
python3 -c "from engine.core.key_manager import KeyManager; km = KeyManager(); print(km.get_key('OPENAI_API_KEY')[:10])"
```

### "GitHub token not found"

Set environment variable:
```bash
export CODEAGENT_GITHUB_TOKEN="ghp_..."
```

Or update profile to use different variable:
```yaml
github:
  token_env: "GITHUB_TOKEN"  # Uses $GITHUB_TOKEN instead
```

### "Connection test failed"

For OpenAI:
```bash
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

For local Ollama:
```bash
curl http://localhost:11434/api/tags
```

### Debug Mode

Enable verbose logging:
```bash
python3 scripts/launch_agent.py --agent gpt4 --debug
```

## Advanced Usage

### Multiple Agents in Sequence

```bash
# Test with local first
python3 scripts/launch_agent.py --agent local --issue 92

# If good, deploy with GPT-4
python3 scripts/launch_agent.py --agent gpt4 --issue 92
```

### Agent Comparison

```bash
# Compare responses
python3 scripts/launch_agent.py --agent local --interactive
> query Write a factorial function
> quit

python3 scripts/launch_agent.py --agent gpt4 --interactive
> query Write a factorial function
> quit
```

### Batch Processing

```bash
# Process multiple issues
for issue in 92 93 94; do
  python3 scripts/launch_agent.py --agent gpt4 --issue $issue
done
```

### Custom Scripts

```python
#!/usr/bin/env python3
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.launch_agent import AgentProfileManager, create_agent_from_profile

# Load manager
manager = AgentProfileManager()

# Get profile
profile = manager.get_profile("gpt4")

# Create agent
agent = create_agent_from_profile(profile)

# Use agent
response = agent.query_llm("Your prompt here")
print(response)
```

## Integration

### With Monitoring Dashboard

Start monitoring:
```bash
python3 -m engine.runners.monitor_service
```

Open dashboard: http://localhost:8897

Launch agent:
```bash
python3 scripts/launch_agent.py --agent gpt4 --issue 92
```

Watch real-time progress in dashboard.

### With Polling Service

The polling service automatically uses available agents:

```yaml
# config/services/polling.yaml
service:
  preferred_agent: "gpt4-coding-agent"  # Uses GPT-4
```

### With CI/CD

```yaml
# .github/workflows/agent.yml
name: Agent Handler
on:
  issues:
    types: [labeled]

jobs:
  handle:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Handle issue
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          CODEAGENT_GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          python3 scripts/launch_agent.py --agent gpt4 --issue ${{ github.event.issue.number }}
```

## Migration from Old Scripts

### Old: `launch_gpt4_agent.py`

```bash
python3 scripts/launch_gpt4_agent.py --issue 92
```

### New: `launch_agent.py`

```bash
python3 scripts/launch_agent.py --agent gpt4 --issue 92
```

**Benefits**:
- Works with any agent, not just GPT-4
- Auto-discovers new agent profiles
- No need for separate scripts per agent
- Fuzzy matching support
- Better validation and error messages

## Future Plans

- **Web UI**: Browser-based agent launcher
- **Multi-Agent Workflows**: Chain multiple agents
- **Cost Tracking**: Per-agent usage statistics
- **Model Router**: Automatic best-model selection
- **Team Management**: Multi-user agent sharing

## References

- [Agent Development Guide](AGENT_DEVELOPMENT_GUIDE.md)
- [Agent Roles](AGENT_ROLES.md)
- [Configuration Guide](../config/README.md)
- [API Documentation](API.md)
