# GPT-4 Coding Agent

OpenAI GPT-4 powered autonomous coding agent using the existing `m0nk111-qwen-agent` GitHub identity.

## Features

- 🤖 **OpenAI GPT-4** for high-quality code generation
- 🔄 **Automatic fallback** to local Ollama if OpenAI unavailable
- 🎯 **Same GitHub identity** as qwen-agent (seamless integration)
- 💰 **Cost optimized**: ~$0.25 per issue
- ✅ **Full autonomous pipeline**: Issue → Code → Tests → PR

## Setup

### 1. OpenAI API Key

Add your OpenAI key to `keys.json`:

```bash
# Option A: Manual
echo '{"OPENAI_API_KEY": "sk-proj-..."}' > keys.json
chmod 600 keys.json

# Option B: Via KeyManager (recommended)
python3 -c "
from engine.core.key_manager import KeyManager
km = KeyManager()
km.set_key('OPENAI_API_KEY', 'sk-proj-...')
"
```

### 2. GitHub Token

Use the existing CODEAGENT_GITHUB_TOKEN:

```bash
# Load from tokens.env
source /etc/agent-forge/tokens.env

# Or export manually
export CODEAGENT_GITHUB_TOKEN='ghp_...'
```

### 3. Test Connection

```bash
python3 tests/test_openai_integration.py
```

Expected output:
```
✅ Key loaded successfully
✅ Connection successful!
✅ Chat completion works
✅ Code generation works
```

## Usage

### Interactive Mode

```bash
python3 scripts/launch_gpt4_agent.py
```

Commands:
- `query <prompt>` - Query GPT-4 directly
- `issue <number>` - Handle GitHub issue
- `cost` - Show cost estimates
- `help` - Show commands
- `quit` - Exit

Example:
```
> query Write a function to calculate fibonacci
> issue 92
> cost
> quit
```

### Handle Specific Issue

```bash
python3 scripts/launch_gpt4_agent.py --issue 92
```

### Custom Repository

```bash
python3 scripts/launch_gpt4_agent.py --issue 5 --repo m0nk111/my-project
```

### Custom Configuration

```bash
python3 scripts/launch_gpt4_agent.py --config config/agents/custom-gpt4.yaml
```

## Configuration

Edit `config/agents/gpt4-coding-agent.yaml`:

```yaml
# LLM Settings
model_provider: "openai"
model_name: "gpt-4"              # or "gpt-3.5-turbo" for cheaper
temperature: 0.7                 # 0.0-1.0 (lower = more deterministic)
max_tokens: 4096                 # Max response length

# GitHub Settings
github:
  username: "m0nk111-qwen-agent"
  token_env: "CODEAGENT_GITHUB_TOKEN"

# Cost Limits
cost_limits:
  max_tokens_per_request: 4096
  max_requests_per_hour: 100
```

## Cost Optimization

### Per Task Type

| Task | Model | Cost | When to Use |
|------|-------|------|-------------|
| Complex features | GPT-4 | $0.25 | New architecture, complex logic |
| Simple features | GPT-3.5 | $0.01 | CRUD, utilities, simple functions |
| Documentation | GPT-3.5 | $0.005 | README, docstrings, comments |
| Local development | Ollama | Free | Testing, experiments, learning |

### Switch Models

```python
# Use GPT-4 for complex tasks
agent = CodeAgent(llm_provider="openai", model="gpt-4")

# Use GPT-3.5 for simple tasks (25x cheaper)
agent = CodeAgent(llm_provider="openai", model="gpt-3.5-turbo")

# Use Ollama for free local testing
agent = CodeAgent(llm_provider="local", model="qwen2.5-coder:7b")
```

## Automatic Fallback

If OpenAI fails (quota, network, etc.), agent automatically falls back to Ollama:

```
⚠️  OpenAI error: Rate limit exceeded
   Falling back to Ollama...
🏠 Querying Ollama: qwen2.5-coder:7b...
```

No crashes, always a working LLM! ✅

## Monitoring

View agent activity in real-time:

```bash
# Terminal 1: Start monitoring
python3 -m engine.runners.monitor_service

# Terminal 2: Use agent
python3 scripts/launch_gpt4_agent.py --issue 92

# Browser: Open dashboard
http://localhost:8897
```

## GitHub Identity

**Important**: This agent uses the **same GitHub account** as the local Qwen agent:

- GitHub username: `m0nk111-qwen-agent`
- GitHub token: `CODEAGENT_GITHUB_TOKEN`
- Commits appear as: `m0nk111-qwen-agent <m0nk111@users.noreply.github.com>`

This means:
- ✅ Seamless transition between GPT-4 and Qwen
- ✅ Same permissions and access
- ✅ Consistent git history
- ✅ No need for separate GitHub account (yet)

## Example: Issue Resolution

```bash
# Start agent for Issue #92
python3 scripts/launch_gpt4_agent.py --issue 92
```

What happens:
1. 🔍 **Fetch issue** from GitHub (#92: Create calculator module)
2. 🌐 **Query GPT-4** for implementation code
3. 📝 **Write files** (engine/utils/calculator.py)
4. 🌐 **Query GPT-4** for test code
5. 📝 **Write tests** (tests/test_calculator.py)
6. ✅ **Run tests** with pytest
7. 🔧 **Create branch** (feature/issue-92)
8. 💾 **Commit changes** (as m0nk111-qwen-agent)
9. 🚀 **Push to GitHub**
10. 📋 **Create PR** with description
11. ✅ **Update issue** with completion comment

Total time: ~2 minutes  
Total cost: ~$0.25

## Comparison: GPT-4 vs Qwen

| Aspect | GPT-4 (Cloud) | Qwen 2.5 Coder (Local) |
|--------|---------------|------------------------|
| **Quality** | ⭐⭐⭐⭐⭐ (Best) | ⭐⭐⭐⭐ (Very Good) |
| **Speed** | 5-10 seconds | 2-3 seconds |
| **Cost** | $0.25/issue | Free |
| **Availability** | Needs internet | Works offline |
| **Context** | 128K tokens | 32K tokens |
| **Languages** | All major | Code-focused |

**Recommendation**: 
- Use GPT-4 for production issues
- Use Qwen for development/testing
- Agent automatically falls back if needed

## Troubleshooting

### OpenAI Key Not Found

```bash
# Check key exists
python3 -c "from engine.core.key_manager import KeyManager; print(KeyManager().get_key('OPENAI_API_KEY'))"

# Add key if missing
python3 -c "from engine.core.key_manager import KeyManager; KeyManager().set_key('OPENAI_API_KEY', 'sk-proj-...')"
```

### GitHub Token Not Found

```bash
# Check token
echo $CODEAGENT_GITHUB_TOKEN

# Load from tokens.env
source /etc/agent-forge/tokens.env
```

### Rate Limit Exceeded

OpenAI has rate limits. If exceeded:
- ✅ Agent automatically falls back to Ollama
- ⏳ Wait a few minutes and try again
- 💰 Upgrade OpenAI tier for higher limits

### Connection Failed

```bash
# Test OpenAI connection
python3 tests/test_openai_integration.py

# Test GitHub connection
python3 tests/test_github_integration.sh
```

## Future Plans

### Separate GitHub Account

Currently using `m0nk111-qwen-agent` for both GPT-4 and Qwen. Future:

```yaml
# config/agents/gpt4-dedicated.yaml
github:
  username: "m0nk111-gpt4-agent"  # New dedicated account
  token_env: "GPT4_GITHUB_TOKEN"
```

Benefits:
- Clear separation in git history
- Different permissions per agent
- Better cost tracking

### Multi-Model Strategy

```yaml
# config/agents/smart-agent.yaml
task_routing:
  complex: "gpt-4"        # $0.25/issue
  medium: "gpt-3.5-turbo" # $0.01/issue  
  simple: "qwen-local"    # free
```

Auto-select model based on task complexity.

## Support

- 📖 Documentation: `/docs/`
- 🐛 Issues: `https://github.com/m0nk111/agent-forge/issues`
- 💬 Discussions: GitHub Discussions

## License

See [LICENSE](../LICENSE) file.
