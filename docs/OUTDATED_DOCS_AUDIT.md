# Outdated Documentation Audit Report

**Date**: 2025-10-10  
**Purpose**: Identify misleading, outdated, or redundant documentation  
**Status**: 🔴 ACTION REQUIRED

---

## 🚨 Critical Issues - MISLEADING CONTENT

### 1. **REFACTOR_PLAN.md** ⚠️ MISLEADING
- **Status**: ✅ **Already Executed** (refactor is complete)
- **Problem**: Doc beschrijft plan als toekomst, maar werk is al gedaan
- **Evidence**:
  - Plan zegt: "Move `agents/` → `engine/runners/`" → ✅ **DONE** (checked)
  - Plan zegt: "Create `engine/core/`" → ✅ **DONE** (9 modules aanwezig)
  - Plan zegt: "Create `engine/operations/`" → ✅ **DONE** (18 modules aanwezig)
  - Plan zegt: "Create `engine/validation/`" → ✅ **DONE** (4 modules aanwezig)
  - Plan zegt: "Split `config/agents.yaml`" → ✅ **DONE** (`config/agents/*.yaml`)
- **Action**: **DELETE** or move to `docs/archive/REFACTOR_PLAN_COMPLETED.md`
- **References to remove**:
  - `PROVISIONAL_GOALS.md` line 664: "26. **[REFACTOR_PLAN.md](REFACTOR_PLAN.md)** - Directory refactor plan (Issue #69)"
  - `PROVISIONAL_GOALS.md` line 728: "See **[REFACTOR_PLAN.md](REFACTOR_PLAN.md)** for detailed technical debt tracking."
  - `CONSOLIDATION_PLAN.md` line 142: "`REFACTOR_PLAN.md` - Planning document"

### 2. **config/agents.yaml** ⚠️ MISSING FILE, MANY REFERENCES
- **Status**: ❌ **File does not exist** (replaced by `config/agents/*.yaml`)
- **Problem**: 27+ references in docs point to non-existent file
- **Evidence**: File check confirms `config/agents.yaml` does not exist
- **Current Reality**: Individual YAML files in `config/agents/` (m0nk111-bot.yaml, m0nk111-qwen-agent.yaml)
- **Action**: **UPDATE ALL REFERENCES** to `config/agents/*.yaml` or `config/agents/`
- **Files with references**:
  - `CHANGELOG.md` (3 references)
  - `PROVISIONAL_GOALS.md` (3 references)
  - `ARCHITECTURE.md` (3 references)
  - `CONTRIBUTING.md` (3 references)
  - `DEPLOYMENT_CHECKLIST.md` (2 references)
  - `AGENT_DEVELOPMENT_GUIDE.md` (1 reference)
  - `INSTALLATION.md` (3 references)
  - `README.old.md` (2 references)

### 3. **QWEN_MONITORING.md** ⚠️ INCORRECT PATHS
- **Status**: 🔴 **Contains outdated code examples**
- **Problem**: References `agents/code_agent.py` and `engine/runners/code_agent.py` (wrong paths)
- **Evidence**:
  - Line 26: `python3 agents/code_agent.py` → Should be `python3 engine/runners/code_agent.py`
  - Line 34: `python3 agents/code_agent.py` → Should be `python3 engine/runners/code_agent.py`
  - Line 54: `from agents.qwen_agent import CodeAgent` → Should be `from engine.runners.code_agent import CodeAgent`
- **Action**: **UPDATE** all code examples with correct paths

### 4. **CONSOLIDATION_PLAN.md** ⚠️ OUTDATED PLANNING DOC
- **Status**: 📅 **Created 2025-01-XX** (placeholder date, likely old)
- **Problem**: 
  - References SETUP_QWEN_GITHUB_ACCOUNT.md (doesn't exist)
  - References GOOGLE_OAUTH_SETUP.md (doesn't exist)
  - References OAUTH_ACTIVATIE.md (doesn't exist)
  - Claims "38 markdown files" but we have 41 files
  - Plan to merge docs has not been executed
- **Action**: **DELETE** or move to archive (plan was never executed)

---

## ⚠️ Medium Priority - OUTDATED REFERENCES

### 5. **README.old.md** ⚠️ OLD VERSION
- **Status**: Filename indicates it's superseded
- **Problem**: Contains outdated `config/agents.yaml` references
- **Action**: **DELETE** or move to `docs/archive/`

### 6. **docs/archive/** SESSION LOGS ⚠️ HISTORICAL REFACTOR CONTEXT
- **Files**:
  - `SESSION_LOG_2025_10_06.md` - References qwen_agent.py → code_agent.py refactor
  - `SESSION_SUMMARY_2025-10-07.md` - References REFACTOR_PLAN.md creation
- **Status**: 📦 Already archived (correct location)
- **Problem**: References completed refactor as future work
- **Action**: **UPDATE** with completion notes or keep as historical record

---

## 📊 Misleading Documentation Statistics

| Issue Type | Count | Action Required |
|------------|-------|-----------------|
| Completed plans still listed as TODO | 1 | Delete/Archive REFACTOR_PLAN.md |
| Missing file references | 27+ | Update config/agents.yaml → config/agents/*.yaml |
| Incorrect code paths | 3+ | Update agents/ → engine/runners/ |
| Outdated planning docs | 1 | Delete/Archive CONSOLIDATION_PLAN.md |
| Old README versions | 1 | Delete/Archive README.old.md |

**Total Files Requiring Updates**: ~15 files  
**Estimated Time**: 1-2 hours

---

## ✅ Recommended Actions (Priority Order)

### Priority 1: Remove Misleading Plans (10 min)
```bash
# Move completed plans to archive
mv docs/REFACTOR_PLAN.md docs/archive/REFACTOR_PLAN_COMPLETED.md
mv docs/CONSOLIDATION_PLAN.md docs/archive/CONSOLIDATION_PLAN_UNEXECUTED.md
mv README.old.md docs/archive/README.old.md

# Add completion notes
echo "**Status**: ✅ COMPLETED on 2025-10-XX" >> docs/archive/REFACTOR_PLAN_COMPLETED.md
```

### Priority 2: Fix config/agents.yaml References (20 min)
Update all references from `config/agents.yaml` to `config/agents/*.yaml`:
- CHANGELOG.md
- PROVISIONAL_GOALS.md  
- ARCHITECTURE.md
- CONTRIBUTING.md
- DEPLOYMENT_CHECKLIST.md
- AGENT_DEVELOPMENT_GUIDE.md
- INSTALLATION.md

Search pattern: `config/agents.yaml`  
Replace with: `config/agents/*.yaml` or `config/agents/` (context dependent)

### Priority 3: Fix Code Path Examples (15 min)
Update QWEN_MONITORING.md:
- `agents/code_agent.py` → `engine/runners/code_agent.py`
- `from agents.qwen_agent` → `from engine.runners.code_agent`

### Priority 4: Update PROVISIONAL_GOALS.md (10 min)
Remove references to:
- REFACTOR_PLAN.md (line 664, 728)
- "Issue #69" (was internal reference to refactor)

---

## 📝 Documentation Accuracy Check Passed ✅

The following docs were checked and are **accurate**:
- AGENT_DEVELOPMENT_GUIDE.md (minor updates needed for config/agents.yaml)
- AGENT_ONBOARDING.md
- AGENT_ROLES.md
- ANTI_SPAM_PROTECTION.md
- API.md
- DEPLOYMENT.md
- ERROR_RECOVERY.md
- INSTALLATION.md (needs config/agents.yaml fix)
- LESSONS_LEARNED.md
- MONITORING_API.md
- PERFORMANCE_BENCHMARKS.md
- PORT_REFERENCE.md
- SECURITY_AUDIT.md
- TESTING.md
- TROUBLESHOOTING.md

---

## 🎯 Next Steps

1. **Approve audit findings** with user
2. **Execute Priority 1-4 actions** (automated via script)
3. **Validate all changes** (grep search for old references)
4. **Update DOCS_CHANGELOG.md** with cleanup actions
5. **Commit changes** with message: `docs: remove misleading refactor plans and fix outdated references`

---

**Created by**: GitHub Copilot Agent  
**Review Status**: 🟡 Pending user approval
