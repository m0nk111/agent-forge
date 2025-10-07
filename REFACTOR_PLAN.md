# Directory Refactor Plan - Agent-Forge

**Datum:** 2025-10-07  
**Doel:** Scheiden van agents (data) en engine (code)  
**Impact:** Hoog (alle imports, paths, configs)

---

## 🎯 Architectuur Filosofie

**Agents** = Data (YAML configuraties)
- Elk agent is een losse YAML file
- Agents zijn **declaratief** (beschrijven wat ze doen)
- Agents zijn **hot-swappable** (geen code restart)

**Engine** = Code (Python modules)
- Runners voeren agents uit
- Core modules bieden infrastructuur
- Operations bieden tools

---

## 📁 Nieuwe Directory Structuur

```
agent-forge/
├── agents/                           # ✨ NIEUW: Agent definitions
│   ├── qwen-main-agent.yaml         # Was: config/agents.yaml entry
│   ├── m0nk111-qwen-agent.yaml      # Was: config/agents.yaml entry
│   ├── polling-service.yaml         # Was: config/agents.yaml entry
│   ├── .gitignore                   # Ignore sensitive data
│   └── README.md                    # Agent creation guide
│
├── engine/                           # ✨ NIEUW: Execution engine
│   ├── runners/                     # Agent type runners
│   │   ├── __init__.py
│   │   ├── code_runner.py          # Was: agents/code_agent.py
│   │   ├── bot_runner.py           # Was: agents/bot_agent.py
│   │   ├── coordinator_runner.py   # Was: agents/coordinator_agent.py
│   │   ├── polling_runner.py       # Was: agents/polling_service.py
│   │   ├── monitor_runner.py       # Was: agents/monitor_service.py
│   │   └── pr_review_runner.py     # Was: agents/pr_reviewer.py
│   │
│   ├── core/                        # Core infrastructure
│   │   ├── __init__.py
│   │   ├── config_manager.py       # Was: agents/config_manager.py
│   │   ├── service_manager.py      # Was: agents/service_manager.py
│   │   ├── context_manager.py      # Was: agents/context_manager.py
│   │   ├── permissions.py          # Was: agents/permissions.py
│   │   ├── security_auditor.py     # Was: agents/security_auditor.py
│   │   ├── llm_providers.py        # Was: agents/llm_providers.py
│   │   └── key_manager.py          # Was: agents/key_manager.py
│   │
│   ├── operations/                  # Tools & operations
│   │   ├── __init__.py
│   │   ├── bot_operations.py       # Was: agents/bot_operations.py
│   │   ├── git_operations.py       # Was: agents/git_operations.py
│   │   ├── github_api_helper.py    # Was: agents/github_api_helper.py
│   │   ├── terminal_operations.py  # Was: agents/terminal_operations.py
│   │   ├── file_editor.py          # Was: agents/file_editor.py
│   │   ├── codebase_search.py      # Was: agents/codebase_search.py
│   │   ├── workspace_tools.py      # Was: agents/workspace_tools.py
│   │   ├── error_checker.py        # Was: agents/error_checker.py
│   │   ├── test_runner.py          # Was: agents/test_runner.py
│   │   ├── web_fetcher.py          # Was: agents/web_fetcher.py
│   │   ├── mcp_client.py           # Was: agents/mcp_client.py
│   │   └── shell_runner.py         # Was: agents/shell_runner.py
│   │
│   └── validation/                  # Validation modules
│       ├── __init__.py
│       ├── instruction_parser.py   # Was: agents/instruction_parser.py
│       ├── instruction_validator.py # Was: agents/instruction_validator.py
│       ├── issue_handler.py        # Was: agents/issue_handler.py
│       └── websocket_handler.py    # Was: agents/websocket_handler.py
│
├── config/                           # System config (not agents!)
│   ├── system.yaml
│   ├── repositories.yaml
│   ├── review_criteria.yaml
│   ├── instruction_rules.yaml
│   └── backups/
│
├── api/                              # REST API
│   ├── config_routes.py             # Update imports
│   └── auth_routes.py
│
├── frontend/                         # Web UI
│   ├── dashboard.html
│   └── ...
│
├── scripts/                          # Utility scripts
│   ├── start-auth-service.sh        # Update paths
│   └── ...
│
├── systemd/                          # Systemd services
│   └── agent-forge.service          # Update paths
│
└── tests/                            # Tests
    ├── test_config_manager.py       # Update imports
    └── ...
```

---

## 📋 Migration Steps

### Phase 1: Setup New Directories (5 min)
```bash
# Create new directory structure
mkdir -p engine/runners
mkdir -p engine/core
mkdir -p engine/operations
mkdir -p engine/validation
mkdir -p agents

# Create __init__.py files
touch engine/__init__.py
touch engine/runners/__init__.py
touch engine/core/__init__.py
touch engine/operations/__init__.py
touch engine/validation/__init__.py
```

### Phase 2: Move Files (10 min)

**Runners:**
```bash
mv agents/code_agent.py engine/runners/code_runner.py
mv agents/bot_agent.py engine/runners/bot_runner.py
mv agents/coordinator_agent.py engine/runners/coordinator_runner.py
mv agents/polling_service.py engine/runners/polling_runner.py
mv agents/monitor_service.py engine/runners/monitor_runner.py
mv agents/pr_reviewer.py engine/runners/pr_review_runner.py
```

**Core:**
```bash
mv agents/config_manager.py engine/core/
mv agents/service_manager.py engine/core/
mv agents/context_manager.py engine/core/
mv agents/permissions.py engine/core/
mv agents/security_auditor.py engine/core/
mv agents/llm_providers.py engine/core/
mv agents/key_manager.py engine/core/
```

**Operations:**
```bash
mv agents/bot_operations.py engine/operations/
mv agents/git_operations.py engine/operations/
mv agents/github_api_helper.py engine/operations/
mv agents/terminal_operations.py engine/operations/
mv agents/file_editor.py engine/operations/
mv agents/codebase_search.py engine/operations/
mv agents/workspace_tools.py engine/operations/
mv agents/error_checker.py engine/operations/
mv agents/test_runner.py engine/operations/
mv agents/web_fetcher.py engine/operations/
mv agents/mcp_client.py engine/operations/
mv agents/shell_runner.py engine/operations/
```

**Validation:**
```bash
mv agents/instruction_parser.py engine/validation/
mv agents/instruction_validator.py engine/validation/
mv agents/issue_handler.py engine/validation/
mv agents/websocket_handler.py engine/validation/
```

### Phase 3: Split agents.yaml (15 min)

**Convert:**
```bash
# Read config/agents.yaml
# Create agents/qwen-main-agent.yaml
# Create agents/m0nk111-qwen-agent.yaml
# Create agents/polling-service.yaml
```

**New agent YAML format:**
```yaml
# agents/qwen-main-agent.yaml
name: qwen-main-agent
type: code_generation
version: "1.0.0"
enabled: true

runtime:
  runner: code_runner
  auto_start: true

llm:
  provider: local
  model: qwen2.5-coder:7b
  temperature: 0.7
  max_tokens: 4096

github:
  token: null
  username: qwen-agent
  email: qwen@agent-forge.local

permissions:
  read_code: true
  write_code: true
  execute_commands: true
  create_commits: true
  create_pull_requests: true
  review_pull_requests: false
  manage_issues: true

monitoring:
  health_check_interval: 60
  log_level: INFO
```

### Phase 4: Update Imports (20 min)

**Pattern:**
```python
# OLD
from agents.config_manager import ConfigManager
from agents.git_operations import GitOperations

# NEW
from engine.core.config_manager import ConfigManager
from engine.operations.git_operations import GitOperations
```

**Files to update:**
- All files in `engine/`
- `api/config_routes.py`
- `api/auth_routes.py`
- All test files in `tests/`
- All root-level test files

### Phase 5: Update ConfigManager (30 min)

**Changes needed in `engine/core/config_manager.py`:**
1. Load agents from `agents/*.yaml` instead of `config/agents.yaml`
2. Support hot-reload (watch directory for changes)
3. Update `save_agent_config()` to write individual YAML files
4. Add `create_agent_config()` for new agents
5. Add `delete_agent_config()` for removing agents

### Phase 6: Update Scripts & Services (10 min)

**scripts/start-auth-service.sh:**
```bash
# OLD
python3 -m api.auth_routes

# NEW
python3 -m api.auth_routes  # (no change, but validate paths)
```

**systemd/agent-forge.service:**
```ini
# OLD
WorkingDirectory=/home/flip/agent-forge
ExecStart=/opt/agent-forge/venv/bin/python3 agents/monitor_service.py

# NEW
WorkingDirectory=/home/flip/agent-forge
ExecStart=/opt/agent-forge/venv/bin/python3 engine/runners/monitor_runner.py
```

### Phase 7: Update API Routes (10 min)

**api/config_routes.py:**
- Update imports
- Change `GET /api/config/agents` to list `agents/*.yaml`
- Change `PATCH /api/config/agents/{id}` to update individual YAML

### Phase 8: Update Tests (15 min)

**All test files:**
- Update imports to use `engine.*`
- Update test data paths

### Phase 9: Update Documentation (10 min)

**Update:**
- README.md
- ARCHITECTURE.md
- docs/BOT_USAGE_GUIDE.md
- docs/INSTRUCTION_VALIDATION_GUIDE.md
- .github/copilot-instructions.md

---

## 🔍 Import Change Examples

### ConfigManager
```python
# Files to update: ~15 files
from agents.config_manager import ConfigManager
↓
from engine.core.config_manager import ConfigManager
```

### GitOperations
```python
# Files to update: ~8 files
from agents.git_operations import GitOperations
↓
from engine.operations.git_operations import GitOperations
```

### ServiceManager
```python
# Files to update: ~5 files
from agents.service_manager import ServiceManager
↓
from engine.core.service_manager import ServiceManager
```

---

## 🧪 Testing Checklist

After refactor, test:

- [ ] Dashboard loads agents from `agents/*.yaml`
- [ ] Create new agent via UI
- [ ] Update agent config via UI
- [ ] Delete agent via UI
- [ ] Start/stop agents
- [ ] Monitor service shows all agents
- [ ] Config API endpoints work
- [ ] Auth service still works
- [ ] All tests pass: `pytest tests/`
- [ ] systemd service starts correctly
- [ ] Scripts work with new paths

---

## 📊 Impact Analysis

**Files to modify:** ~50-60 files
- Python files with imports: ~40
- Config files: ~5
- Test files: ~10
- Documentation: ~5

**Time estimate:** 2-3 hours
- Automated (search/replace): 30 min
- Manual (testing): 90-120 min

**Risk:** Medium
- High number of files
- Critical infrastructure (ConfigManager)
- Production services running

---

## 🚨 Rollback Plan

**If refactor fails:**
```bash
# Revert git commit
git reset --hard HEAD~1

# Or restore from backup
cp -r /tmp/agent-forge-backup/* /home/flip/agent-forge/

# Restart services
sudo systemctl restart agent-forge
```

---

## 🎯 Benefits

**After refactor:**
✅ Clear separation: data (agents) vs code (engine)
✅ Hot-reload agents without code restart
✅ Easy to add new agents (just drop YAML file)
✅ Better scalability (100s of agents possible)
✅ Cleaner imports (`engine.core`, `engine.operations`)
✅ Easier testing (mock individual agents)
✅ Better security (agents/*.yaml in .gitignore)

---

## 📝 Next Steps

**Option A: Refactor Now**
- Branch: `feature/engine-refactor`
- Commit: Small incremental commits
- Test: After each phase
- Merge: After full testing

**Option B: Refactor Later**
- Create issue: #XX "Directory refactor: agents/ → engine/"
- Priority: Medium
- Do after: OAuth is stable

**Option C: Hybrid Approach**
- Phase 1-2: Create structure, move files (low risk)
- Test: Ensure nothing breaks
- Phase 3-9: Later when time permits

---

## 🤔 Decision Point

**Question for you:**
1. Do we refactor NOW or LATER?
2. If now: Do we do it all at once or in phases?
3. If later: When? (after OAuth? after testing?)

**My recommendation:**
- Later (after OAuth is stable)
- Create detailed issue with this plan
- Do in phases (runners first, then core, then operations)
- Test extensively after each phase
