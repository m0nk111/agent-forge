# Agent Configuration Directory

This directory contains all agent profile configurations for the Agent-Forge platform.

## 📁 Directory Structure

```
config/agents/
├── README.md (this file)
├── coordinator-agent.yaml ⭐ (Default: GPT-5)
├── coordinator-agent-gpt4turbo-backup.yaml (Backup: GPT-4 Turbo)
├── coordinator-agent-4o.yaml (Alternative: GPT-4o)
├── coordinator-agent-gpt5.yaml (Source: GPT-5)
├── developer-agent.yaml (GPT-4)
├── reviewer-agent.yaml (GPT-4)
├── tester-agent.yaml (GPT-3.5-turbo)
├── documenter-agent.yaml (GPT-3.5-turbo)
├── researcher-agent.yaml (GPT-4)
└── [bot agents]
```

## 🎯 Default Coordinator: GPT-5

**As of October 11, 2025**, the default coordinator uses **GPT-5 Chat Latest**.

### Why GPT-5?

Based on comprehensive testing and benchmarking:

✅ **44% faster** than GPT-4o for complex planning (10.8s vs 21.7s)
✅ **Equal or better quality** (5/5 on all metrics)
✅ **More detailed responses** (94+ lines vs 69 for GPT-4o)
✅ **Better structured output** with comprehensive analysis
✅ **Latest technology** (2025 GPT-5 generation)
✅ **Minimal cost increase** (only $3/month more than GPT-4o)

### Test Results

**Real Task**: Redis caching implementation plan

| Metric | GPT-4o | GPT-5 | Winner |
|--------|--------|-------|--------|
| Response Time | 21.69s | 10.76s | **GPT-5 (-50%)** |
| Quality Score | 5/5 | 5/5 | Tie |
| Lines Generated | 69 | 94 | **GPT-5 (+36%)** |
| Token Speed | 25 tok/s | 51 tok/s | **GPT-5 (+104%)** |

**Verdict**: GPT-5 is the clear winner for coordinator tasks!

## 📊 Available Coordinator Options

### 1. coordinator-agent.yaml ⭐ **DEFAULT**
- **Model**: gpt-5-chat-latest
- **Speed**: 10-12s (complex tasks)
- **Cost**: ~$0.0105/task
- **Use**: Production (recommended)

### 2. coordinator-agent-4o.yaml
- **Model**: gpt-4o
- **Speed**: 20-22s (complex tasks)
- **Cost**: ~$0.0075/task
- **Use**: Budget-conscious option

### 3. coordinator-agent-gpt4turbo-backup.yaml
- **Model**: gpt-4-turbo
- **Speed**: 25-30s (complex tasks)
- **Cost**: ~$0.025/task
- **Use**: Fallback/testing

## 🚀 Usage

### Use Default Coordinator (GPT-5)
```bash
python3 scripts/launch_agent.py --agent coordinator
```

### Use Specific Coordinator
```bash
# GPT-4o (budget)
python3 scripts/launch_agent.py --agent coordinator-4o

# GPT-4 Turbo (fallback)
python3 scripts/launch_agent.py --agent coordinator-gpt4turbo-backup
```

### Switch Default Coordinator

To change the default coordinator back to GPT-4o:
```bash
cd config/agents
cp coordinator-agent-4o.yaml coordinator-agent.yaml
```

To restore GPT-5 as default:
```bash
cd config/agents
cp coordinator-agent-gpt5.yaml coordinator-agent.yaml
```

## 💰 Cost Comparison

**Per 1000 coordination tasks:**

| Model | Cost | vs GPT-5 |
|-------|------|----------|
| GPT-5 (default) | $10.50 | Baseline |
| GPT-4o | $7.50 | -$3/month |
| GPT-4 Turbo | $25.00 | +$14.50/month |
| GPT-4 Classic | $60.00 | +$49.50/month |

**Monthly difference** (GPT-5 vs GPT-4o): Only **$3**

**Time saved per month** (100 complex tasks): ~17 minutes

**ROI**: Speed and quality improvements are **worth the $3/month**!

## 🧪 Testing

All agents can be tested using:

```bash
# Test GPT-5 coordinator
python3 scripts/test_gpt5_models.py

# Compare GPT-5 vs GPT-4o
python3 scripts/compare_gpt5_gpt4o.py

# Quality test (complex tasks)
python3 scripts/quality_test_gpt5.py
```

## 📖 Documentation

- **Model Comparison**: `docs/COORDINATOR_MODEL_COMPARISON.md`
- **Agent Roles**: `docs/AGENT_ROLE_CONFIGS.md`
- **Launcher Guide**: `docs/AGENT_LAUNCHER_GUIDE.md`
- **Test Results**: `docs/LLM_TEST_RESULTS.md`

## 🔄 Fallback Chain

All agents are configured with automatic fallback:

**GPT-5 Coordinator:**
1. Primary: gpt-5-chat-latest
2. Fallback: gpt-4o
3. Secondary: gpt-4-turbo

This ensures reliability even if primary model is unavailable.

## ⚙️ Configuration Format

Each agent config includes:

```yaml
agent_id: "unique-agent-id"
name: "Human-readable name"
role: "coordinator|developer|reviewer|tester|documenter|researcher|bot"
description: "What this agent does"

llm:
  provider: "openai|anthropic|google|ollama"
  model_name: "model-identifier"
  temperature: 0.7
  max_tokens: 4096
  fallback:
    model: "fallback-model"
    secondary_fallback: "secondary-fallback-model"

capabilities:
  - "capability1"
  - "capability2"

# ... (role-specific settings)
```

## 🔍 Finding Agents

List all available agents:
```bash
python3 scripts/launch_agent.py --list
```

Filter by role:
```bash
python3 scripts/launch_agent.py --list | grep coordinator
```

## 📝 Notes

- **Last Updated**: October 11, 2025
- **Default Changed**: GPT-4 Turbo → GPT-5 Chat Latest
- **Reason**: 50% faster, same quality, minimal cost increase
- **Status**: Production tested and approved ✅

## 🎯 Recommendation

**Use GPT-5 as default coordinator** for best performance and quality. Only switch to GPT-4o if cost is absolutely critical (saves $3/month but loses 50% speed).
