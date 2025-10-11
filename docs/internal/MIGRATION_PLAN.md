# Documentation Migration Plan

**Date**: 2025-10-11  
**Purpose**: Reorganize documentation to separate generic (releasable) from specific (internal)

---

## 🔒 Move to `docs/internal/` (Project-Specific)

### Account & Authentication (9 files)
- ✅ AGENT_ACCOUNTS_SUMMARY.md - Lists m0nk111-* accounts with emails
- ✅ GITHUB_ACCOUNTS_STRATEGY.md - Our multi-account strategy
- ✅ GITHUB_TOKEN_SCOPES.md - Our token configurations
- ✅ MULTI_AGENT_GITHUB_STRATEGY.md - Our GitHub setup
- ✅ BOT_USAGE_GUIDE.md - m0nk111-post specific usage
- ✅ SSH_AUTHENTICATION.md - Our SSH setup
- ✅ TOKEN_SECURITY.md - Our token management
- ✅ LOCAL_SHELL_ACCESS.md - Our shell access
- ✅ GITHUB_SUPPORT_REQUEST.md - Our support requests

### Configuration & Deployment (5 files)
- ✅ AGENT_ROLE_CONFIGS.md - Our specific configs
- ✅ DEPLOYMENT.md - Our deployment specifics
- ✅ DEPLOYMENT_CHECKLIST.md - Our checklist
- ✅ PORT_REFERENCE.md - Our port assignments (7000-7999)
- ✅ SECURITY_AUDIT.md - Our audit config

### Project History & Operations (10 files)
- ✅ LESSONS_LEARNED.md - Our experiences
- ✅ DOCS_CHANGELOG.md - Our doc history
- ✅ PERFORMANCE_BENCHMARKS.md - Our benchmarks
- ✅ LLM_TEST_RESULTS.md - Our LLM tests
- ✅ QWEN_MONITORING.md - Our Qwen setup
- ✅ TROUBLESHOOTING.md - Our specific issues
- ✅ OUTDATED_DOCS_AUDIT.md - Our audit
- ✅ BUGS_TRACKING.md - Our bug tracking
- ✅ ERROR_RECOVERY.md - Our error handling
- ✅ PROVISIONAL_GOALS.md - Our goals

### Bootstrap & Specialized Agents (4 files)
- ✅ PROJECT_BOOTSTRAP_AGENT.md - Our bootstrap impl
- ✅ BOOTSTRAP_QUICK_START.md - Our bootstrap guide
- ✅ ISSUE_OPENER_AGENT.md - Our issue opener
- ✅ GPT4_AGENT_GUIDE.md - Our GPT-4 setup

**Total: 28 files → `docs/internal/`**

---

## 📚 Keep/Move to `docs/guides/` (Generic, Releasable)

### Core Framework (8 files)
- ✅ AGENT_DEVELOPMENT_GUIDE.md - Generic agent development
- ✅ AGENT_LAUNCHER_GUIDE.md - Generic launcher patterns
- ✅ AGENT_ONBOARDING.md - Generic onboarding process
- ✅ AGENT_ROLES.md - Generic role patterns
- ✅ INSTRUCTION_VALIDATION_GUIDE.md - Generic validation
- ✅ COORDINATOR_MODEL_COMPARISON.md - Generic comparison
- ✅ GPT5_QUICK_REFERENCE.md - Generic GPT-5 reference
- ✅ ASCII_AUTOMATION_WORKFLOW.md - Generic workflow

### API & Architecture (4 files)
- ✅ API.md - Generic API reference
- ✅ MONITORING_API.md - Generic monitoring API
- ✅ PIPELINE_ARCHITECTURE.md - Generic pipeline design
- ✅ ANTI_SPAM_PROTECTION.md - Generic spam protection

### Development Guides (4 files)
- ✅ INSTALLATION.md - Generic installation
- ✅ CONTRIBUTING.md - Generic contribution guide
- ✅ TESTING.md - Generic testing guide
- ✅ LICENSING.md - Generic licensing info
- ✅ COMMERCIAL-LICENSE.md - Commercial option

**Total: 16 files → `docs/guides/` (or stay in root)**

---

## 🔀 Needs Genericizing (Mixed Content)

These files currently have specific references that need to be replaced:

### Files with m0nk111-* References
```bash
grep -l "m0nk111" docs/*.md | grep -v internal | head -20
```

**Action**: Replace with placeholders:
- `m0nk111-post` → `your-bot-account`
- `m0nk111-coder1` → `your-coder-1`
- `aicodingtime+*@gmail.com` → `your-email+suffix@domain.com`
- `agent-forge` repo → `your-org/your-project`

### Files with Specific Paths
**Action**: Replace with template paths:
- `/home/flip/agent-forge` → `<project-root>`
- `/home/flip/.local/bin` → `<user-bin-path>`
- Specific ports → `<port-7xxx>` or environment variable references

---

## 📋 Migration Steps

### Step 1: Move Internal Docs (28 files)
```bash
# Account & Auth (9 files)
mv docs/AGENT_ACCOUNTS_SUMMARY.md docs/internal/
mv docs/GITHUB_ACCOUNTS_STRATEGY.md docs/internal/
mv docs/GITHUB_TOKEN_SCOPES.md docs/internal/
mv docs/MULTI_AGENT_GITHUB_STRATEGY.md docs/internal/
mv docs/BOT_USAGE_GUIDE.md docs/internal/
mv docs/SSH_AUTHENTICATION.md docs/internal/
mv docs/TOKEN_SECURITY.md docs/internal/
mv docs/LOCAL_SHELL_ACCESS.md docs/internal/
mv docs/GITHUB_SUPPORT_REQUEST.md docs/internal/

# Configuration & Deployment (5 files)
mv docs/AGENT_ROLE_CONFIGS.md docs/internal/
mv docs/DEPLOYMENT.md docs/internal/
mv docs/DEPLOYMENT_CHECKLIST.md docs/internal/
mv docs/PORT_REFERENCE.md docs/internal/
mv docs/SECURITY_AUDIT.md docs/internal/

# Project History (10 files)
mv docs/LESSONS_LEARNED.md docs/internal/
mv docs/DOCS_CHANGELOG.md docs/internal/
mv docs/PERFORMANCE_BENCHMARKS.md docs/internal/
mv docs/LLM_TEST_RESULTS.md docs/internal/
mv docs/QWEN_MONITORING.md docs/internal/
mv docs/TROUBLESHOOTING.md docs/internal/
mv docs/OUTDATED_DOCS_AUDIT.md docs/internal/
mv docs/BUGS_TRACKING.md docs/internal/
mv docs/ERROR_RECOVERY.md docs/internal/
mv docs/PROVISIONAL_GOALS.md docs/internal/

# Bootstrap (4 files)
mv docs/PROJECT_BOOTSTRAP_AGENT.md docs/internal/
mv docs/BOOTSTRAP_QUICK_START.md docs/internal/
mv docs/ISSUE_OPENER_AGENT.md docs/internal/
mv docs/GPT4_AGENT_GUIDE.md docs/internal/
```

### Step 2: Move Generic Docs (16 files)
```bash
# Core Framework (8 files)
mv docs/AGENT_DEVELOPMENT_GUIDE.md docs/guides/
mv docs/AGENT_LAUNCHER_GUIDE.md docs/guides/
mv docs/AGENT_ONBOARDING.md docs/guides/
mv docs/AGENT_ROLES.md docs/guides/
mv docs/INSTRUCTION_VALIDATION_GUIDE.md docs/guides/
mv docs/COORDINATOR_MODEL_COMPARISON.md docs/guides/
mv docs/GPT5_QUICK_REFERENCE.md docs/guides/
mv docs/ASCII_AUTOMATION_WORKFLOW.md docs/guides/

# API & Architecture (4 files)
mv docs/API.md docs/guides/
mv docs/MONITORING_API.md docs/guides/
mv docs/PIPELINE_ARCHITECTURE.md docs/guides/
mv docs/ANTI_SPAM_PROTECTION.md docs/guides/

# Development (4 files)
mv docs/INSTALLATION.md docs/guides/
mv docs/CONTRIBUTING.md docs/guides/
mv docs/TESTING.md docs/guides/
mv docs/LICENSING.md docs/guides/
mv docs/COMMERCIAL-LICENSE.md docs/guides/
```

### Step 3: Genericize Files
For each file in `docs/guides/`, run:
```bash
# Replace specific account names
sed -i 's/m0nk111-post/your-bot-account/g' docs/guides/*.md
sed -i 's/m0nk111-coder1/your-coder-1/g' docs/guides/*.md
sed -i 's/m0nk111-coder2/your-coder-2/g' docs/guides/*.md
sed -i 's/m0nk111-reviewer/your-reviewer/g' docs/guides/*.md
sed -i 's/m0nk111-qwen-agent/your-agent/g' docs/guides/*.md

# Replace specific emails
sed -i 's/aicodingtime+[a-z]*@gmail\.com/your-email+suffix@domain.com/g' docs/guides/*.md

# Replace specific repo
sed -i 's/m0nk111\/agent-forge/your-org\/your-project/g' docs/guides/*.md

# Replace specific paths
sed -i 's/\/home\/flip\/agent-forge/<project-root>/g' docs/guides/*.md
```

### Step 4: Add Headers
Add to top of each internal doc:
```markdown
# [INTERNAL] Document Title

**⚠️ PROJECT-SPECIFIC DOCUMENTATION - DO NOT RELEASE**

This document contains implementation details specific to the agent-forge project.
For generic documentation, see `docs/guides/`.

---
```

Add to top of each guide:
```markdown
# Document Title

**📚 GENERIC FRAMEWORK DOCUMENTATION**

This is generic, reusable documentation. For project-specific details, 
see your internal documentation.

---
```

### Step 5: Update Cross-References
Update all `[Link](../FILE.md)` references to point to new locations.

### Step 6: Verification
```bash
# Check no sensitive info in guides
grep -r "m0nk111" docs/guides/
grep -r "aicodingtime" docs/guides/
grep -r "ghp_" docs/guides/

# Should return no results

# Check internal docs exist
ls docs/internal/ | wc -l  # Should be 28
ls docs/guides/ | wc -l    # Should be 16
```

---

## 🎯 Success Criteria

- ✅ 28 files in `docs/internal/` with [INTERNAL] prefix
- ✅ 16 files in `docs/guides/` with generic content
- ✅ No `m0nk111-*` references in `docs/guides/`
- ✅ No `aicodingtime` emails in `docs/guides/`
- ✅ No token examples in `docs/guides/`
- ✅ All cross-references updated
- ✅ `docs/README.md` explains structure
- ✅ `.gitignore` configured for releases

---

## 📝 Commit Plan

```bash
git add docs/README.md
git commit -m "docs: Add documentation structure guide"

git add docs/internal/ docs/guides/
git commit -m "docs: Reorganize documentation (generic vs internal)"

git add docs/*.md
git commit -m "docs: Update cross-references after reorganization"

git add CHANGELOG.md docs/internal/DOCS_CHANGELOG.md
git commit -m "docs: Update changelogs for documentation reorganization"
```

---

## ⏭️ Future Enhancements

1. Create `docs/examples/` with code samples using placeholders
2. Add CI check to verify no sensitive info in `docs/guides/`
3. Create release script that excludes `docs/internal/`
4. Add `docs/templates/` with config file templates
5. Consider renaming `docs/guides/` → `docs/` for simpler structure

