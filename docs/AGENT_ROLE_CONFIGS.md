# Agent Role Configuration Overview

Complete overview of all agent roles with optimized LLM assignments.

## 📊 Agent Roles Summary

| Role | Agent ID | Model | Provider | Cost/Issue | Use Case |
|------|----------|-------|----------|------------|----------|
| **Coordinator** | coordinator-agent | GPT-4 | OpenAI | ~$0.30 | Complex planning & orchestration |
| **Developer** | developer-agent | GPT-4 | OpenAI | ~$0.25 | Production code generation |
| **Reviewer** | reviewer-agent | GPT-4 | OpenAI | ~$0.20 | Thorough code reviews |
| **Tester** | tester-agent | GPT-3.5-turbo | OpenAI | ~$0.01 | Test generation & execution |
| **Documenter** | documenter-agent | GPT-3.5-turbo | OpenAI | ~$0.01 | Documentation writing |
| **Researcher** | researcher-agent | GPT-4 | OpenAI | ~$0.25 | Deep analysis & research |
| **Bot** | m0nk111-post | Qwen (local) | Ollama | Free | Automation & posting |

## 🎯 LLM Assignment Strategy

### GPT-4 (High Quality, Higher Cost)
Used for roles requiring:
- Complex reasoning (Coordinator)
- High-quality code (Developer)
- Thorough analysis (Reviewer, Researcher)
- Critical decision-making

**Cost**: $0.03/1K input, $0.06/1K output (~$0.20-0.30 per task)

### GPT-3.5-turbo (Good Quality, Low Cost)
Used for roles with:
- Simpler tasks (Tester, Documenter)
- High volume operations
- Less critical decisions

**Cost**: $0.0005/1K input, $0.0015/1K output (~$0.01 per task)

### Local Ollama (Free, Good Quality)
Used for:
- Development and testing
- High-frequency operations (Bot)
- Budget-conscious scenarios

**Cost**: Free

## 🚀 Usage Examples

### Launch Specific Role

```bash
# Coordinator for complex planning
python3 scripts/launch_agent.py --agent coordinator

# Developer for code generation
python3 scripts/launch_agent.py --agent developer

# Reviewer for PR review
python3 scripts/launch_agent.py --agent reviewer

# Tester for test generation
python3 scripts/launch_agent.py --agent tester

# Documenter for docs
python3 scripts/launch_agent.py --agent documenter

# Researcher for investigation
python3 scripts/launch_agent.py --agent researcher

# Bot for automation
python3 scripts/launch_agent.py --agent post
```

### Handle Issue with Specific Role

```bash
# Use coordinator for complex issue
python3 scripts/launch_agent.py --agent coordinator --issue 100

# Use developer for feature request
python3 scripts/launch_agent.py --agent developer --issue 101

# Use tester for test-related issue
python3 scripts/launch_agent.py --agent tester --issue 102
```

### Interactive Mode by Role

```bash
# Research mode
python3 scripts/launch_agent.py --agent researcher --interactive

# Review mode
python3 scripts/launch_agent.py --agent reviewer --interactive
```

## 🔧 Role-Specific Configurations

### 1. Coordinator Agent
- **Model**: GPT-4 (best reasoning)
- **Temperature**: 0.7 (balanced)
- **Key Features**:
  - Task breakdown up to 10 subtasks
  - 3-level planning depth
  - Automatic progress monitoring
  - Blocker detection and handling
- **Always-on**: Yes (monitors continuously)

### 2. Developer Agent
- **Model**: GPT-4 (high-quality code)
- **Temperature**: 0.7 (creative but consistent)
- **Key Features**:
  - Follows PEP 8 style guide
  - Requires 80% test coverage
  - Runs static analysis (flake8, bandit, mypy)
  - Auto-creates feature branches and PRs
- **Fallback**: GPT-3.5-turbo for simple tasks (typos, comments)
- **Always-on**: No (on-demand)

### 3. Reviewer Agent
- **Model**: GPT-4 (thorough analysis)
- **Temperature**: 0.5 (consistent reviews)
- **Key Features**:
  - Security, performance, style checks
  - Blocks on security issues
  - Provides code suggestions
  - Checks test coverage (80% min)
- **Read-only**: Yes (no code changes)
- **Always-on**: No (triggered by PRs)

### 4. Tester Agent
- **Model**: GPT-3.5-turbo (cost-effective)
- **Temperature**: 0.7 (standard)
- **Key Features**:
  - Generates unit & integration tests
  - Parallel test execution (4 threads)
  - Posts results to PRs
  - Fails on coverage drop >5%
- **Fallback**: Local Qwen (free)
- **Always-on**: No (triggered by PRs/commits)

### 5. Documenter Agent
- **Model**: GPT-3.5-turbo (cost-effective)
- **Temperature**: 0.7 (standard)
- **Key Features**:
  - Generates README, guides, API docs
  - Maintains changelog (Keep a Changelog format)
  - Uses emoji for readability
  - Includes examples
- **Fallback**: Local Qwen (free)
- **Always-on**: No (on-demand)

### 6. Researcher Agent
- **Model**: GPT-4 (deep analysis)
- **Temperature**: 0.8 (creative research)
- **Key Features**:
  - Multi-source research (GitHub, Stack Overflow, docs)
  - Depth-3 investigation
  - Pattern analysis
  - 30-day research cache
- **Read-only**: Yes (no code changes)
- **Always-on**: No (on-demand)

### 7. Bot Agent
- **Model**: Qwen local (free, consistent)
- **Temperature**: 0.5 (consistent responses)
- **Key Features**:
  - Issue triage and labeling
  - Automated responses
  - Project board management
  - Rate limiting (500 ops/hour)
  - Anti-spam protection
- **Read-only**: Yes (no code changes)
- **Always-on**: Can be (for automation)

## 💰 Cost Optimization Strategies

### Strategy 1: Role-Based Selection
```bash
# Use expensive GPT-4 only for complex tasks
python3 scripts/launch_agent.py --agent coordinator --issue 100  # Complex: $0.30

# Use cheap GPT-3.5 for simple tasks
python3 scripts/launch_agent.py --agent tester --issue 101      # Simple: $0.01

# Use free local for automation
python3 scripts/launch_agent.py --agent post --issue 102        # Free: $0.00
```

### Strategy 2: Fallback Configuration
All agents have fallbacks configured:
- **GPT-4 agents** → GPT-3.5-turbo on simple tasks
- **GPT-3.5 agents** → Local Qwen on budget mode
- Automatic fallback on API errors

### Strategy 3: Development vs Production
```bash
# Development: Use local agents (free)
export USE_LOCAL_AGENTS=true

# Production: Use OpenAI agents (quality)
export USE_LOCAL_AGENTS=false
```

## 🔄 Workflow Examples

### Example 1: Complete Feature Development
```bash
# 1. Coordinator plans the feature
python3 scripts/launch_agent.py --agent coordinator --issue 100

# 2. Developer implements
python3 scripts/launch_agent.py --agent developer --issue 100

# 3. Tester creates tests
python3 scripts/launch_agent.py --agent tester --issue 100

# 4. Reviewer reviews PR
python3 scripts/launch_agent.py --agent reviewer --issue 100

# 5. Documenter updates docs
python3 scripts/launch_agent.py --agent documenter --issue 100

# 6. Bot closes issue and posts summary
python3 scripts/launch_agent.py --agent post --issue 100
```

### Example 2: Bug Investigation
```bash
# 1. Researcher investigates root cause
python3 scripts/launch_agent.py --agent researcher --issue 101

# 2. Developer fixes bug
python3 scripts/launch_agent.py --agent developer --issue 101

# 3. Tester validates fix
python3 scripts/launch_agent.py --agent tester --issue 101
```

### Example 3: Documentation Sprint
```bash
# Use cost-effective documenter for all doc issues
for issue in 102 103 104 105; do
  python3 scripts/launch_agent.py --agent documenter --issue $issue
done
```

## 🎛️ Customization

### Override Model per Task
```bash
# Use GPT-3.5 for developer (cheaper)
# Edit config/agents/developer-agent.yaml
model_name: "gpt-3.5-turbo"

# Or create custom variant
cp config/agents/developer-agent.yaml config/agents/developer-cheap.yaml
# Edit model_name in developer-cheap.yaml
```

### Add Custom Roles
```bash
# Create new role config
nano config/agents/my-custom-agent.yaml
```

```yaml
agent_id: "my-custom-agent"
name: "My Custom Agent"
role: "custom"  # Any role name
model_provider: "openai"
model_name: "gpt-4"
```

```bash
# Verify it's discovered
python3 scripts/launch_agent.py --list
# Should show: my-custom-agent ... custom
```

## 📈 Performance Metrics

Based on testing:

| Role | Avg Time | Success Rate | Avg Cost | Quality Score |
|------|----------|--------------|----------|---------------|
| Coordinator | 2-3 min | 95% | $0.30 | 9.5/10 |
| Developer | 3-5 min | 90% | $0.25 | 9.0/10 |
| Reviewer | 1-2 min | 98% | $0.20 | 9.5/10 |
| Tester | 2-4 min | 92% | $0.01 | 8.5/10 |
| Documenter | 1-2 min | 95% | $0.01 | 8.0/10 |
| Researcher | 3-5 min | 88% | $0.25 | 9.0/10 |
| Bot | <1 min | 99% | $0.00 | 9.0/10 |

## 🔒 Security Considerations

### Role Permissions
- **Read-only roles**: Reviewer, Researcher, Bot (cannot modify code)
- **Write roles**: Developer, Tester, Documenter (can modify specific files)
- **Admin roles**: Coordinator (full access)

### Token Management
All agents use secure token storage:
- **OpenAI API Key**: Stored in `keys.json` (chmod 600)
- **GitHub Token**: Stored in environment or `keys.json`
- **Never committed**: `.gitignore` protects secrets

## 🔮 Future Enhancements

- **Multi-agent workflows**: Chain agents automatically
- **Cost tracking**: Per-agent usage statistics
- **Model router**: Automatic best-model selection
- **Team management**: Multi-user agent sharing
- **A/B testing**: Compare different models per role
- **Anthropic Claude**: Add Claude-3 agents for certain roles
- **Google Gemini**: Add Gemini agents as alternatives

## 📚 References

- [Agent Launcher Guide](AGENT_LAUNCHER_GUIDE.md)
- [Agent Roles Documentation](AGENT_ROLES.md)
- [Agent Development Guide](AGENT_DEVELOPMENT_GUIDE.md)
- [Cost Optimization](../config/README.md)
