# Agent Onboarding Guide

> **Purpose**: This document provides a structured checklist for AI agents to quickly understand the Agent-Forge project architecture, conventions, and workflows.

## 📋 Quick Start Checklist

### 1. Essential Reading (Read in this order!)

#### **MUST READ FIRST** ⚠️
- [ ] **README.md** (Root) - Complete architecture overview, service manager, quick start
- [ ] **ARCHITECTURE.md** (Root) - Deep technical architecture and system design
- [ ] **.github/copilot-instructions.md** - Agent-specific rules and conventions (auto-loaded)

#### **Core Documentation** 📚
- [ ] **docs/MULTI_AGENT_GITHUB_STRATEGY.md** - How agents collaborate on GitHub
- [ ] **docs/QWEN_MONITORING.md** - WebSocket monitoring and dashboard architecture
- [ ] **docs/BOT_USAGE_GUIDE.md** - Bot agent workflows and capabilities
- [ ] **docs/INSTRUCTION_VALIDATION_GUIDE.md** - Validation rules and patterns

#### **Visual Architecture** 🎨
- [ ] **docs/diagrams/architecture-overview.md** - System architecture diagram
- [ ] **docs/diagrams/data-flow.md** - Data flow through the system
- [ ] **docs/diagrams/component-interactions.md** - How components communicate
- [ ] **docs/PORT_REFERENCE.md** - Port allocation and conflicts

### 2. Key Architecture Concepts to Verify

#### **Service Manager** (Port 8080)
```
service_manager.py
├── Orchestrates all services
├── REST API on port 8080
└── Controls: monitor_service, websocket_handler, polling_service, code_agent
```

#### **Frontend Structure** (Port 8897) ⚠️ CRITICAL
```
frontend/
├── index.html              → Landing page (auto-redirects)
├── dashboard.html          → ⭐ DEFAULT DASHBOARD (main entry point)
├── unified_dashboard.html  → New unified dashboard (issues #27, #28, #65)
├── monitoring_dashboard.html → Classic monitoring view
└── config_ui.html          → Configuration interface
```

**🚨 IMPORTANT**: `dashboard.html` is the DEFAULT dashboard, NOT `monitoring_dashboard.html`!

#### **WebSocket Architecture** (Port 7997)
```
websocket_handler.py
├── WebSocket server on ws://host:7997/ws/monitor
├── Real-time agent state updates
├── Log streaming to dashboards
└── Connected to all frontend dashboards
```

#### **Port Allocation** 🔌
| Port | Service | Purpose |
|------|---------|---------|
| 8080 | Service Manager | REST API, service orchestration |
| 7997 | WebSocket Server | Real-time monitoring, log streaming |
| 8897 | Frontend HTTP | Dashboard hosting (dashboard.html) |
| 7996 | Other Services | Additional backend services |

### 3. Configuration Files

#### **Core Config Files**
- [ ] `config/system.yaml` - System-wide configuration
- [ ] `config/agents.yaml` - Agent definitions and capabilities
- [ ] `config/bot_config.yaml` - Bot-specific settings
- [ ] `config/coordinator_config.yaml` - Coordinator settings
- [ ] `config/repositories.yaml` - GitHub repository mappings
- [ ] `config/instruction_rules.yaml` - Validation rules

#### **Project Standards**
- [ ] `CHANGELOG.md` - All code changes must be documented here
- [ ] `DOCS_CHANGELOG.md` - Documentation changes tracked separately
- [ ] `BUGS_TRACKING.md` - Known issues and tracking

### 4. Development Workflows

#### **Deployment Commands**
```bash
# Start Service Manager (orchestrates everything)
./scripts/start-service.sh

# Start Frontend Dashboard
./scripts/launch_dashboard.sh
# → Serves frontend/ on http://0.0.0.0:8897
# → Access via: http://localhost:8897/dashboard.html

# Start Monitoring Dashboard
./scripts/launch_monitoring.sh
```

#### **Git Workflow**
- Read `.github/copilot-instructions.md` for commit message format
- **Conventional Commits**: `feat(scope): description`
- **Update CHANGELOG.md BEFORE committing**
- **Never commit in external-code/ directories**

#### **Testing**
```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_bot_agent.py

# Run with coverage
pytest --cov=agents --cov-report=html
```

### 5. Agent Roles and Responsibilities

#### **Bot Agent** (`agents/bot_agent.py`)
- Handles GitHub issue assignments
- Performs code modifications
- Creates branches and commits
- Manages pull requests

#### **Coordinator Agent** (`agents/coordinator_agent.py`)
- Orchestrates multi-agent workflows
- Task distribution and prioritization
- High-level decision making

#### **Qwen Agent** (`agents/qwen_agent.py`)
- Local LLM integration (Qwen 2.5 Coder)
- Code generation and review
- Works offline without API costs

### 6. Common Pitfalls to Avoid ⚠️

#### **Frontend Confusion**
❌ **WRONG**: Assuming `monitoring_dashboard.html` is the default  
✅ **CORRECT**: `dashboard.html` is the DEFAULT, accessed after `index.html` redirect

#### **Port Confusion**
❌ **WRONG**: Using port 8898 for frontend  
✅ **CORRECT**: Frontend is on port 8897 (see `scripts/launch_dashboard.sh`)

#### **Commit Workflow**
❌ **WRONG**: Commit first, update CHANGELOG later  
✅ **CORRECT**: Update CHANGELOG.md FIRST, then commit

#### **External Code**
❌ **WRONG**: Committing changes inside `external-code/` directories  
✅ **CORRECT**: External projects are READ-ONLY for git operations

### 7. Verification Steps

Before starting work, verify:

```bash
# 1. Check current branch
git branch --show-current

# 2. Verify services are running
lsof -i:8080  # Service Manager
lsof -i:7997  # WebSocket
lsof -i:8897  # Frontend

# 3. Test WebSocket connection
# Open dashboard: http://localhost:8897/dashboard.html
# Check connection status indicator (should be green)

# 4. Verify Python environment
source venv/bin/activate
python --version  # Should be 3.10+

# 5. Check configuration
cat config/system.yaml
cat config/agents.yaml
```

### 8. Quick Reference Links

#### **Documentation**
- Architecture: `/ARCHITECTURE.md`
- API Reference: `/docs/API_REFERENCE.md` (if exists)
- Troubleshooting: `/docs/TROUBLESHOOTING.md` (if exists)

#### **Diagrams**
- System Architecture: `/docs/diagrams/architecture-overview.md`
- Data Flow: `/docs/diagrams/data-flow.md`
- Components: `/docs/diagrams/component-interactions.md`

#### **Configuration**
- Port Reference: `/docs/PORT_REFERENCE.md`
- Agent Config: `/config/agents.yaml`
- System Config: `/config/system.yaml`

---

## 🎯 Final Checklist Before Starting Work

- [ ] Read all MUST READ documents
- [ ] Understand port allocation (8080, 7997, 8897)
- [ ] Know that `dashboard.html` is the DEFAULT frontend
- [ ] Reviewed relevant diagrams for task context
- [ ] Verified all services are running
- [ ] Understand commit workflow (CHANGELOG first!)
- [ ] Know which agent role is relevant to task

---

## 💡 Pro Tips

1. **Always check diagrams first** - A picture is worth 1000 lines of code
2. **When in doubt, check PORT_REFERENCE.md** - Port conflicts are common
3. **Update CHANGELOG.md immediately** - Don't let it pile up
4. **Test WebSocket connection** - Most dashboard issues are WebSocket-related
5. **Use structured logging with emojis** - `logger.debug("🔍 Context: {info}")`

---

**Last Updated**: 2025-10-06  
**Maintained by**: Agent-Forge Team  
**Feedback**: Create an issue with label `documentation`
