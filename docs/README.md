# Documentation Structure

This directory contains two types of documentation:

## 📚 Generic Documentation (For Product/Open Source Release)

**Location**: `docs/guides/` and root `docs/*.md` (select files)

**Purpose**: Reusable documentation that can be shared publicly or in product releases.

**Characteristics**:
- ✅ Generic examples (e.g., `your-org/your-repo`, `your-bot-account`)
- ✅ Framework/architecture explanations
- ✅ API references without specific credentials
- ✅ Installation and setup guides (template-style)
- ✅ Best practices and patterns
- ✅ No hardcoded usernames, emails, or tokens

**Files that should be generic**:
- Architecture documentation
- API references
- Setup/installation guides
- Framework guides
- Best practices

## 🔒 Internal Documentation (Project-Specific, DO NOT RELEASE)

**Location**: `docs/internal/`

**Purpose**: Specific implementation details for THIS project (agent-forge for m0nk111).

**Characteristics**:
- ⚠️ Contains actual account names (m0nk111-post, m0nk111-coder1, etc.)
- ⚠️ Real email addresses (aicodingtime+*)
- ⚠️ Project-specific decisions and configurations
- ⚠️ Token locations and environment variable names
- ⚠️ Actual repository references
- ⚠️ Internal workflows and processes

**Files that should be internal**:
- Account summaries with real names
- GitHub accounts strategy with actual accounts
- Token management details
- Project-specific configurations
- Deployment details with real servers
- Internal troubleshooting guides

---

## 📋 File Classification Guide

### ✅ Generic (Releasable)

**Core Documentation**:
- `ARCHITECTURE.md` (make generic)
- `CONTRIBUTING.md`
- `LICENSE`

**Guides** (in `docs/guides/`):
- `INSTALLATION.md` (generic setup)
- `AGENT_DEVELOPMENT_GUIDE.md` (generic agent dev)
- `AGENT_LAUNCHER_GUIDE.md` (generic launcher)
- `AGENT_ROLES.md` (generic role patterns)
- `API.md` (generic API reference)
- `TESTING.md` (generic test patterns)
- `MONITORING_API.md` (generic monitoring)

**Architecture**:
- `PIPELINE_ARCHITECTURE.md`
- `COORDINATOR_MODEL_COMPARISON.md`

### 🔒 Internal (DO NOT RELEASE)

**Account Management** (in `docs/internal/`):
- `AGENT_ACCOUNTS_SUMMARY.md` - Our actual 6 accounts
- `GITHUB_ACCOUNTS_STRATEGY.md` - Our account decisions
- `GITHUB_TOKEN_SCOPES.md` - Our token configurations
- `MULTI_AGENT_GITHUB_STRATEGY.md` - Our GitHub setup

**Configuration** (in `docs/internal/`):
- `AGENT_ROLE_CONFIGS.md` - Our specific configs
- `BOT_USAGE_GUIDE.md` - Our bot account usage
- `PORT_REFERENCE.md` - Our port assignments
- `SSH_AUTHENTICATION.md` - Our SSH setup

**Deployment** (in `docs/internal/`):
- `DEPLOYMENT.md` - Our deployment specifics
- `DEPLOYMENT_CHECKLIST.md` - Our checklist
- `LOCAL_SHELL_ACCESS.md` - Our shell setup

**Project History** (in `docs/internal/`):
- `LESSONS_LEARNED.md` - Our experiences
- `DOCS_CHANGELOG.md` - Our doc history
- `PERFORMANCE_BENCHMARKS.md` - Our benchmarks
- `QWEN_MONITORING.md` - Our Qwen setup
- `TROUBLESHOOTING.md` - Our specific issues
- `OUTDATED_DOCS_AUDIT.md` - Our audit

**Bootstrap** (in `docs/internal/`):
- `PROJECT_BOOTSTRAP_AGENT.md` - Our bootstrap impl
- `BOOTSTRAP_QUICK_START.md` - Our bootstrap guide
- `ISSUE_OPENER_AGENT.md` - Our issue opener

---

## 🔄 Migration Strategy

### Phase 1: Move Internal Docs
```bash
mv docs/AGENT_ACCOUNTS_SUMMARY.md docs/internal/
mv docs/GITHUB_ACCOUNTS_STRATEGY.md docs/internal/
mv docs/GITHUB_TOKEN_SCOPES.md docs/internal/
# ... etc for all internal docs
```

### Phase 2: Genericize Releasable Docs
- Replace `m0nk111-*` with `your-bot-account`, `your-coder-1`
- Replace `aicodingtime+*` with `your-email+bot@domain.com`
- Replace `agent-forge` with `your-project`
- Replace specific paths with template paths

### Phase 3: Update References
- Update all internal doc cross-references
- Add note in generic docs: "See docs/internal/ for project-specific details"

### Phase 4: .gitignore for Releases
Add to `.gitignore` for product releases:
```
docs/internal/
config/system/github_accounts.yaml
secrets/
keys.json
```

---

## 🎯 Best Practices

### When Writing New Documentation

**Ask yourself**: 
- Will this doc contain our specific account names? → `docs/internal/`
- Is this a generic pattern/framework? → `docs/guides/` or root `docs/`

### Cross-References

**In generic docs**:
```markdown
For project-specific account setup, see your internal documentation.
```

**In internal docs**:
```markdown
This document contains project-specific details for agent-forge.
See docs/guides/INSTALLATION.md for generic setup instructions.
```

### Template Variables

Use template syntax in generic docs:
```markdown
# Generic
export BOT_GITHUB_TOKEN="<your-token>"
export BOT_GITHUB_USERNAME="<your-bot-username>"

# Internal (docs/internal/)
export BOT_GITHUB_TOKEN="ghp_..."
export BOT_GITHUB_USERNAME="m0nk111-post"
```

---

## 📦 Release Preparation

When preparing a release:

1. **Verify internal docs are excluded**:
   ```bash
   ls docs/internal/ | wc -l  # Should be > 0
   ```

2. **Check generic docs have no sensitive info**:
   ```bash
   grep -r "m0nk111" docs/guides/
   grep -r "aicodingtime" docs/guides/
   # Should return no results
   ```

3. **Update package/release script** to exclude `docs/internal/`

4. **Create README with setup instructions** referring to templates

---

## 🔍 Quick Reference

| Document Type | Location | Contains | For Release? |
|--------------|----------|----------|--------------|
| Generic guides | `docs/guides/` | Templates, patterns | ✅ Yes |
| Internal config | `docs/internal/` | Real accounts, tokens | ❌ No |
| Architecture | `docs/*.md` (select) | Framework design | ✅ Yes (after genericizing) |
| Configuration | `config/` | Real settings | ⚠️ Sanitize first |
| Secrets | `secrets/` | Tokens | ❌ Never |

