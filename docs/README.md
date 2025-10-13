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

## � Technical Deep-Dives

**Recent Additions** (2025-10-13):

### BM25 Hybrid Search Documentation

**[BM25_HYBRID_SEARCH.md](BM25_HYBRID_SEARCH.md)** - Complete technical guide
- 📖 BM25 algorithm explanation with formulas
- 🔧 Client-side implementation details
- 🏗️ Architecture diagrams and data flows
- 💻 Code examples (TypeScript + Python)
- ⚡ Performance benchmarks
- 🔍 Troubleshooting guide

**[CLAUDE_CONTEXT_STATUS.md](CLAUDE_CONTEXT_STATUS.md)** - Current integration status
- ✅ Production ready status with hybrid search
- 🎯 BM25 encoder implementation overview
- 🚀 Auto-fit feature explanation
- 📊 Test results and benchmarks

**[CLAUDE_CONTEXT_INTEGRATION.md](CLAUDE_CONTEXT_INTEGRATION.md)** - Integration guide
- 🔄 Updated architecture for hybrid search
- 📝 Why client-side BM25 (vs server-side)
- 🛠️ Installation and configuration
- 🧪 Usage examples

**Key Innovation**: Client-side BM25 sparse vector generation
- Milvus server-side BM25 functions don't auto-execute
- Implemented custom BM25 encoder in TypeScript
- Hybrid search: Dense (OpenAI) + Sparse (BM25) + RRF reranking
- Auto-fit encoder from collection data on first search
- **Status**: Fully operational in production 🎉

## �🔒 Internal Documentation (Project-Specific, DO NOT RELEASE)

**Location**: `docs/internal/`

**Purpose**: Specific implementation details for THIS project.

**Characteristics**:
- ⚠️ Contains actual account names (your specific bot/coder accounts)
- ⚠️ Real email addresses
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
- Replace specific account names with generic placeholders (`your-bot-account`, `your-coder-1`)
- Replace real email addresses with template emails (`your-email+suffix@domain.com`)
- Replace project-specific repo names with generic examples (`your-org/your-project`)
- Replace specific paths with template paths (`<project-root>`, `<user-bin-path>`)

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
This document contains project-specific details for this project.
See docs/guides/INSTALLATION.md for generic setup instructions.
```

### Template Variables

Use template syntax in generic docs:
```markdown
# Generic
export BOT_GITHUB_TOKEN="<your-token>"
export BOT_GITHUB_USERNAME="<your-bot-username>"

# Internal (docs/internal/)
export BOT_GITHUB_TOKEN="ghp_ActualTokenHere123"
export BOT_GITHUB_USERNAME="your-actual-bot-username"
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
   grep -r "your-org-name" docs/guides/
   grep -r "your-email-domain" docs/guides/
   # Should return no results (replace with your actual sensitive keywords)
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

