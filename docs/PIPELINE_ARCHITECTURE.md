# Autonomous Pipeline Architecture

## 🎯 Overview

The Agent-Forge autonomous pipeline enables complete Issue→PR workflow without manual intervention:

```
┌─────────────────────────────────────────────────────────────────┐
│                    AUTONOMOUS PIPELINE                           │
└─────────────────────────────────────────────────────────────────┘

1. PollingService (every 5 min)
   ↓ Detects assigned issues with `agent-ready` label
   
2. PipelineOrchestrator
   ↓ Fetches issue details from GitHub API
   
3. IssueHandler  
   ↓ Parses requirements from issue body
   
4. CodeGenerator
   ↓ Generates implementation + tests
   
5. BotAgent (via MCP/GitHubAPI)
   ↓ Creates pull request
   
6. PRReviewer
   ↓ Posts automated code review
   
7. BotAgent (optional)
   ↓ Merges PR if approved
   
8. Close Issue
   ↓ Posts completion summary
```

## 📦 Components

### PipelineOrchestrator (`engine/core/pipeline_orchestrator.py`)

**Central coordinator** that orchestrates the complete workflow.

**Key Features**:
- Multi-source token management (env vars, config, MCP)
- Phase tracking with progress (0.0 → 1.0)
- Error recovery and retry logic
- Safety features (auto-merge disabled by default)
- Monitoring integration support

**Usage**:
```python
from engine.core.pipeline_orchestrator import get_orchestrator, PipelineConfig

# Configure pipeline
config = PipelineConfig(
    default_repos=["m0nk111/agent-forge"],
    auto_merge_on_approval=False,  # Safety first
    require_tests_passing=True
)

# Get orchestrator instance (singleton)
orchestrator = get_orchestrator(config)

# Handle new issue (async)
result = await orchestrator.handle_new_issue(
    repo="m0nk111/agent-forge",
    issue_number=84
)

# Check result
if result['success']:
    print(f"✅ PR created: {result['pr_url']}")
    print(f"📝 Files: {result['files_created']}")
else:
    print(f"❌ Failed: {result['error']}")
```

**Token Management**:
```python
# Priority order:
# 1. BOT_GITHUB_TOKEN (env var) - Recommended for bots
# 2. GITHUB_TOKEN (env var) - Standard fallback
# 3. GH_TOKEN (env var) - GitHub CLI
# 4. Config file (if specified)
# 5. MCP-injected token

# Set MCP token programmatically
orchestrator.set_mcp_token("ghp_xxxxx")
```

### PollingService (`engine/runners/polling_service.py`)

**Issue monitoring service** that triggers the pipeline.

**Integration**:
```python
# Updated to use PipelineOrchestrator
from engine.core.pipeline_orchestrator import get_orchestrator

orchestrator = get_orchestrator()
result = await orchestrator.handle_new_issue(repo, issue_number)
```

**Configuration** (via `config/services/polling.yaml`):
```yaml
polling_interval: 300  # 5 minutes
repositories:
  - m0nk111/agent-forge
username: m0nk111-bot
labels:
  - agent-ready
claim_timeout_minutes: 60
```

### SystemD Service (`systemd/agent-forge-polling.service`)

**Automatic startup** for production deployment.

**Installation**:
```bash
# Edit service file first to set token
sudo nano systemd/agent-forge-polling.service

# Edit this line:
Environment="BOT_GITHUB_TOKEN=your_token_here"

# Install service
sudo ./scripts/install-polling-service.sh

# Start service
sudo systemctl start agent-forge-polling

# View logs
sudo journalctl -u agent-forge-polling -f
```

**Management Commands**:
```bash
systemctl status agent-forge-polling   # Check status
systemctl start agent-forge-polling    # Start
systemctl stop agent-forge-polling     # Stop
systemctl restart agent-forge-polling  # Restart
systemctl enable agent-forge-polling   # Auto-start on boot
systemctl disable agent-forge-polling  # Disable auto-start
```

## 🔧 Pipeline Phases

| Phase | Progress | Description | Status |
|-------|----------|-------------|--------|
| **initialization** | 0.0 | Verify token, setup state | ✅ Ready |
| **fetch_issue** | 0.1 | Get issue details from GitHub | ✅ Ready |
| **parse_requirements** | 0.2 | Extract tasks from issue body | ⚠️ Basic (needs LLM) |
| **generate_code** | 0.4 | Create implementation + tests | ⚠️ Placeholder |
| **run_tests** | 0.6 | Execute test suite | ⚠️ Placeholder |
| **create_pr** | 0.7 | Create pull request | ⚠️ Placeholder |
| **review_pr** | 0.8 | Post automated review | ⚠️ Placeholder |
| **merge_pr** | 0.9 | Merge if approved (optional) | ⚠️ Placeholder |
| **close_issue** | 1.0 | Close with summary | ⚠️ Placeholder |

**Legend**:
- ✅ **Ready**: Fully implemented and tested
- ⚠️ **Placeholder**: Interface ready, needs integration
- ❌ **Missing**: Not yet implemented

## 🧪 Testing

### E2E Test Issues

**Issue #84**: `health_checker.py` - Network utility function
**Issue #85**: `string_utils.py` - String manipulation helpers

These issues are designed as **autonomous pipeline tests**:
- Well-defined requirements
- Low complexity
- Clear acceptance criteria
- Safety (no destructive operations)

**When pipeline is complete**, these issues should be:
1. Automatically detected by PollingService
2. Claimed by bot account
3. Implementation generated
4. Tests written and passing
5. PR created
6. Review posted
7. Merged (if approved)
8. Issue closed

**Current Status**: Issues open, waiting for pipeline integration.

### Manual Testing

```bash
# Test token management
python3 -c "
from engine.core.pipeline_orchestrator import get_orchestrator
orch = get_orchestrator()
token = orch._get_github_token()
print(f'Token found: {bool(token)}')
"

# Test pipeline phases (placeholder)
python3 -c "
import asyncio
from engine.core.pipeline_orchestrator import get_orchestrator

async def test():
    orch = get_orchestrator()
    result = await orch.handle_new_issue('m0nk111/agent-forge', 84)
    print(f'Result: {result}')

asyncio.run(test())
"
```

## 🚀 Next Steps

### Phase 1: Component Integration (Current)
- [ ] Integrate CodeGenerator with PipelineOrchestrator
- [ ] Integrate PRReviewer with PipelineOrchestrator
- [ ] Integrate BotAgent/MCP for PR operations
- [ ] Implement test execution in pipeline
- [ ] Implement issue closing with summary

### Phase 2: Testing & Validation
- [ ] Test with Issue #84 (health_checker)
- [ ] Test with Issue #85 (string_utils)
- [ ] Verify complete autonomous workflow
- [ ] Fix any integration issues
- [ ] Performance optimization

### Phase 3: Production Deployment
- [ ] Deploy polling service with systemd
- [ ] Configure production tokens
- [ ] Enable monitoring
- [ ] Set up alerting
- [ ] Documentation for operators

## 📊 Current Status

**Infrastructure**: ✅ **COMPLETE**
- PipelineOrchestrator created
- PollingService integrated
- SystemD service configured
- Token management multi-source
- Phase tracking implemented

**Integration**: ⏳ **IN PROGRESS**
- CodeGenerator: Needs integration
- PRReviewer: Needs integration
- BotAgent: Needs MCP/API integration
- Test execution: Needs implementation
- Issue closing: Needs implementation

**Testing**: 📋 **PENDING**
- E2E tests defined (Issues #84, #85)
- Waiting for component integration
- Manual testing possible

**Estimated Timeline**: 4-6 hours to complete integration

## 🔒 Security

**Token Security**:
- Never commit tokens to git
- Use environment variables or systemd Environment= directive
- Prefer BOT_GITHUB_TOKEN for bot operations
- Rotate tokens regularly

**Safety Features**:
- Auto-merge disabled by default
- Tests required before PR creation
- Review before merge (configurable)
- Error recovery with retry logic
- Resource limits in systemd service

## 📚 Documentation

**Code**:
- `engine/core/pipeline_orchestrator.py` - Comprehensive docstrings
- `engine/runners/polling_service.py` - Updated with pipeline calls
- `systemd/agent-forge-polling.service` - Commented configuration

**Guides**:
- This file (PIPELINE_ARCHITECTURE.md)
- CHANGELOG.md - Feature documentation
- GitHub Issues #84, #85 - E2E test specs

## 🤝 Contributing

When extending the pipeline:

1. **Add phase** to PipelineOrchestrator._handle_new_issue()
2. **Implement method** (e.g., `_generate_implementation()`)
3. **Update progress tracking** (phase name, progress value)
4. **Add error handling** with try/except and logging
5. **Update CHANGELOG.md** with changes
6. **Test with E2E issues** (#84, #85)

**Code Style**:
- Use emoji prefixes in logs: 🚀 ✅ ❌ ⚠️ 🔍
- Comprehensive error messages
- Type hints for all methods
- Docstrings with Args/Returns

---

**Author**: Agent Forge  
**Date**: 2025-10-10  
**Version**: 1.0 (Infrastructure Complete)
