# GPT-5 Coordinator Quick Reference

**Last Updated**: October 11, 2025  
**Status**: Production Ready ✅  
**Default Coordinator**: GPT-5 Chat Latest

---

## 🚀 Quick Start

### Use GPT-5 Coordinator (Default)

```bash
# Option 1: Use default coordinator (GPT-5)
python3 scripts/launch_agent.py --agent coordinator --issue 123

# Option 2: Explicitly specify GPT-5
python3 scripts/launch_agent.py --agent coordinator-gpt5 --issue 123

# Option 3: Interactive mode
python3 scripts/launch_agent.py --agent coordinator --interactive
```

### Run Demo

```bash
# Full interactive demo (3 scenarios)
python3 scripts/demo_gpt5_coordinator.py

# Quick performance test
python3 scripts/compare_gpt5_gpt4o.py

# Quality test (complex planning)
python3 scripts/quality_test_gpt5.py
```

---

## 📊 Performance Stats

| Metric | GPT-5 | GPT-4o | Improvement |
|--------|-------|--------|-------------|
| **Complex Planning** | 10-12s | 20-22s | **50% faster** |
| **Medium Tasks** | 6-7s | 5-6s | Similar |
| **Simple Tasks** | 2-3s | 3-5s | Faster |
| **Token Speed** | 51 tok/s | 25 tok/s | **2x faster** |
| **Quality Score** | 5/5 | 5/5 | Equal |
| **Detail Level** | 94 lines | 69 lines | **36% more** |

**Bottom Line**: GPT-5 is **50% faster** for complex coordination with **same quality**!

---

## 💰 Cost Comparison

**Per Task:**
- GPT-5: $0.0105
- GPT-4o: $0.0075
- Difference: $0.003 per task

**Per Month (1000 tasks):**
- GPT-5: $10.50
- GPT-4o: $7.50
- Difference: **$3/month**

**ROI**: 
- Time saved: ~10s per complex task
- At 100 complex tasks/month: **17 minutes saved**
- Better quality: More detailed, better structured
- **Verdict**: $3/month is worth it!

---

## 🎯 When to Use Each Model

### Use GPT-5 (Default) ⭐ RECOMMENDED

**Best for:**
- ✅ Complex planning & architecture decisions
- ✅ Multi-phase project coordination
- ✅ Risk assessment & mitigation strategies
- ✅ Detailed implementation plans
- ✅ Task breakdown (5+ subtasks)
- ✅ Critical production coordination

**Performance:**
- 50% faster than GPT-4o
- More detailed responses
- Better structured output
- Latest technology

### Use GPT-4o

**Best for:**
- 💰 Budget-conscious projects
- 💰 High-volume simple tasks
- 💰 Non-critical coordination

**Performance:**
- Still fast (20-22s)
- Good quality (5/5)
- Saves $3/month

### Use GPT-4 Turbo

**Best for:**
- 🔄 Fallback option only
- 🔄 Testing/validation

**Performance:**
- Slower (25-30s)
- More expensive ($25/1K tasks)

---

## 📝 Example Use Cases

### 1. Complex Task Breakdown

```bash
python3 scripts/launch_agent.py --agent coordinator --issue 150
```

**Input**: GitHub issue with complex requirements  
**Output**: 5-7 phase implementation plan with:
- Architecture overview
- Technical decisions
- Testing strategy
- Rollout plan
- Risk mitigation

**GPT-5 Advantage**: 50% faster, 36% more detail

### 2. Risk Analysis

```bash
python3 scripts/launch_agent.py --agent coordinator --interactive
> analyze risks for kubernetes migration
```

**Output**: Comprehensive risk analysis with:
- Technical risks (infrastructure, data, network)
- Business risks (downtime, compliance)
- Operational risks (team, monitoring)
- Mitigation strategies
- Rollback plan

**GPT-5 Advantage**: More thorough, better structured

### 3. Multi-Agent Coordination

```bash
python3 scripts/launch_agent.py --agent coordinator --issue 175
```

**Output**: Coordination plan with:
- Task assignment to agents
- Dependency mapping
- Progress tracking
- Blocker resolution

**GPT-5 Advantage**: Faster coordination, better decisions

---

## 🔄 Alternative Coordinators

### Switch to GPT-4o (Budget)

```bash
# Temporary (one-time use)
python3 scripts/launch_agent.py --agent coordinator-4o --issue 123

# Permanent (change default)
cd config/agents
cp coordinator-agent-4o.yaml coordinator-agent.yaml
```

### Switch to GPT-4 Turbo (Fallback)

```bash
# Restore backup
cd config/agents
cp coordinator-agent-gpt4turbo-backup.yaml coordinator-agent.yaml
```

### Restore GPT-5 (Recommended)

```bash
cd config/agents
cp coordinator-agent-gpt5.yaml coordinator-agent.yaml
```

---

## 🧪 Testing Commands

### Test GPT-5 Availability

```bash
python3 scripts/test_gpt5_models.py
```

**Output**: Tests all 10 GPT-5 variants  
**Shows**: Availability, speed, quality

### Compare GPT-5 vs GPT-4o

```bash
python3 scripts/compare_gpt5_gpt4o.py
```

**Output**: Side-by-side speed comparison  
**Shows**: Response time, quality, winner

### Quality Test (Complex Task)

```bash
python3 scripts/quality_test_gpt5.py
```

**Output**: Detailed quality analysis  
**Shows**: Structure, detail, comprehensiveness

### Run Full Demo

```bash
python3 scripts/demo_gpt5_coordinator.py
```

**Output**: Interactive demo with 3 scenarios  
**Shows**: Real-world coordination examples

---

## 🎛️ Configuration

### Check Current Coordinator Model

```bash
python3 -c "
import yaml
with open('config/agents/coordinator-agent.yaml') as f:
    config = yaml.safe_load(f)
    print(f\"Model: {config['llm']['model_name']}\")
"
```

**Expected Output**: `Model: gpt-5-chat-latest`

### View All Available Agents

```bash
python3 scripts/launch_agent.py --list
```

### View Coordinator Options Only

```bash
python3 scripts/launch_agent.py --list | grep coordinator
```

---

## 📚 Documentation

- **Model Comparison**: `docs/COORDINATOR_MODEL_COMPARISON.md`
- **Agent Config Guide**: `config/agents/README.md`
- **Agent Roles**: `docs/AGENT_ROLE_CONFIGS.md`
- **Launcher Guide**: `docs/AGENT_LAUNCHER_GUIDE.md`
- **Test Results**: `docs/LLM_TEST_RESULTS.md`

---

## ⚠️ Troubleshooting

### GPT-5 Not Available

**Error**: `404 Not Found` or `model_not_found`

**Solution**: Check model name
```bash
# Should be: gpt-5-chat-latest
# NOT: gpt-5 (may have issues)
```

### Fallback to GPT-4o

**Automatic fallback chain**:
1. Try: `gpt-5-chat-latest`
2. Fallback: `gpt-4o`
3. Secondary: `gpt-4-turbo`

### Slow Response Times

**Check**:
- Internet connection
- OpenAI API status
- Rate limits (30K TPM, 500 RPM)

**Solution**: Wait and retry, or use GPT-4o temporarily

### Cost Concerns

**Monitor usage**:
```bash
# Check OpenAI usage dashboard
# https://platform.openai.com/usage
```

**Reduce costs**:
- Use GPT-4o for simple tasks
- Use GPT-5 only for complex coordination
- Set monthly budget alerts

---

## 🎯 Best Practices

### 1. Use GPT-5 for Complex Tasks

**Good**:
- Implementation plans (5+ phases)
- Architecture decisions
- Risk analysis
- Multi-agent coordination

**Overkill** (use GPT-4o instead):
- Simple queries
- Status updates
- Quick questions

### 2. Monitor Performance

Track these metrics:
- Response time (should be 10-15s for complex)
- Quality score (should be 5/5)
- Cost per task
- User satisfaction

### 3. Provide Clear Context

**Good prompt**:
```
Issue #123: Add caching layer

Requirements:
- Redis cluster
- Cache invalidation
- Monitoring
- Backward compatible

Create implementation plan with 5 phases.
```

**Bad prompt**:
```
Add caching
```

### 4. Review Outputs

GPT-5 is excellent but not perfect:
- ✅ Verify technical decisions
- ✅ Check feasibility
- ✅ Validate dependencies
- ✅ Adjust time estimates

---

## 📞 Support

**Questions?**
- Check: `docs/COORDINATOR_MODEL_COMPARISON.md`
- Review: `config/agents/README.md`
- Run: `python3 scripts/demo_gpt5_coordinator.py`

**Issues?**
- Test: `python3 scripts/test_gpt5_models.py`
- Fallback: Use `coordinator-4o` temporarily
- Report: Create GitHub issue

---

## ✅ Summary

**Current Status**: GPT-5 Chat Latest is **default coordinator**

**Performance**: 50% faster, same quality, 36% more detail

**Cost**: $3/month more than GPT-4o (worth it!)

**Recommendation**: **Keep GPT-5 as default** ⭐

**Usage**: Just use `--agent coordinator` (GPT-5 by default)

---

**Last Updated**: October 11, 2025  
**Next Review**: When GPT-5 Pro/Codex become available
