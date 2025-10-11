## 2025-10-11 - Documentation Architecture Overhaul

### Major Reorganization
- **Separated generic documentation from project-specific details**
  - Created `docs/guides/` for generic, reusable framework documentation (17 files)
  - Created `docs/internal/` for project-specific implementation documentation (30 files)
  - Created `docs/README.md` explaining documentation structure, migration strategy, and best practices

### Documentation Migration
**Moved to `docs/internal/` (30 files):**
- Account & Authentication (9): AGENT_ACCOUNTS_SUMMARY, GITHUB_ACCOUNTS_STRATEGY, GITHUB_TOKEN_SCOPES, MULTI_AGENT_GITHUB_STRATEGY, BOT_USAGE_GUIDE, SSH_AUTHENTICATION, TOKEN_SECURITY, LOCAL_SHELL_ACCESS, GITHUB_SUPPORT_REQUEST
- Configuration & Deployment (5): AGENT_ROLE_CONFIGS, DEPLOYMENT, DEPLOYMENT_CHECKLIST, PORT_REFERENCE, SECURITY_AUDIT
- Project History (10): LESSONS_LEARNED, DOCS_CHANGELOG, PERFORMANCE_BENCHMARKS, LLM_TEST_RESULTS, QWEN_MONITORING, TROUBLESHOOTING, OUTDATED_DOCS_AUDIT, BUGS_TRACKING, ERROR_RECOVERY, PROVISIONAL_GOALS
- Bootstrap & Specialized (4): PROJECT_BOOTSTRAP_AGENT, BOOTSTRAP_QUICK_START, ISSUE_OPENER_AGENT, GPT4_AGENT_GUIDE
- Other (2): ascii-art-demo, MIGRATION_PLAN

**Moved to `docs/guides/` (17 files):**
- Core Framework (8): AGENT_DEVELOPMENT_GUIDE, AGENT_LAUNCHER_GUIDE, AGENT_ONBOARDING, AGENT_ROLES, INSTRUCTION_VALIDATION_GUIDE, COORDINATOR_MODEL_COMPARISON, GPT5_QUICK_REFERENCE, ASCII_AUTOMATION_WORKFLOW
- API & Architecture (4): API, MONITORING_API, PIPELINE_ARCHITECTURE, ANTI_SPAM_PROTECTION
- Development (5): INSTALLATION, CONTRIBUTING, TESTING, LICENSING, COMMERCIAL-LICENSE

### Genericization of Guides
**Replaced specific references with generic placeholders:**
- Account names: `m0nk111-post` → `your-bot-account`, `m0nk111-coder1` → `your-coder-1`, etc.
- Emails: `aicodingtime+*@gmail.com` → `your-email+suffix@domain.com`
- Repositories: `m0nk111/agent-forge` → `your-org/your-project`
- Paths: `/home/flip/agent-forge` → `<project-root>`
- **Preserved**: Copyright and licensing information (m0nk111 references in licenses are intentional)

### Documentation Structure
**New structure:**
```
docs/
├── README.md (structure guide, 5.9 KB)
├── guides/ (17 generic docs)
│   ├── API.md, MONITORING_API.md
│   ├── AGENT_*.md (development, roles, launcher, onboarding)
│   ├── INSTALLATION.md, CONTRIBUTING.md, TESTING.md
│   └── LICENSING.md, COMMERCIAL-LICENSE.md
└── internal/ (30 project-specific docs)
    ├── AGENT_ACCOUNTS_SUMMARY.md, GITHUB_ACCOUNTS_STRATEGY.md
    ├── DEPLOYMENT*.md, PORT_REFERENCE.md
    ├── LESSONS_LEARNED.md, TROUBLESHOOTING.md
    └── MIGRATION_PLAN.md
```

### Rationale
- **Separation of concerns**: Generic framework documentation can be shared/released without exposing internal implementation details
- **Reusability**: Guide documentation can be used by other projects or in product releases
- **Security**: Internal docs containing sensitive information (accounts, emails, tokens, deployment details) are segregated
- **Clarity**: Clear distinction between "how to use the framework" (guides) vs "how we use it" (internal)

### Files Modified
- All 17 files in `docs/guides/` genericized
- `CHANGELOG.md` updated with documentation reorganization entry

### Verification Results
- ✅ 30 files in `docs/internal/`
- ✅ 17 files in `docs/guides/`
- ✅ 1 file in `docs/` root (README.md)
- ✅ 0 `aicodingtime` references in guides (excluding internal)
- ✅ Only copyright/licensing m0nk111 references in guides (intentional)
- ✅ No tokens or sensitive paths in guides

---

# Docs Changelog

All notable documentation-only changes are tracked here. Newest first.

## 2025-10-11

### Added

- **Centralized GitHub Account Configuration**: New `config/system/github_accounts.yaml` as single source of truth
- **AccountManager Documentation**: Usage examples for programmatic account access
- **Email Pattern Documentation**: All accounts use `aicodingtime+<suffix>@gmail.com`

### Changed

- **AGENT_ACCOUNTS_SUMMARY.md**: Updated all accounts with emails, priorities, and AccountManager reference
- **GITHUB_ACCOUNTS_STRATEGY.md**: Complete rewrite with current 6-account implementation
- **README.md**: Updated directory trees with all 5 agent configs and tokens
- **ARCHITECTURE.md**: Updated agents list and directory structure
- **API.md**: Replaced m0nk111-bot examples with m0nk111-post
- **MONITORING_API.md**: Replaced m0nk111-bot examples with m0nk111-post
- **AGENT_LAUNCHER_GUIDE.md**: Replaced m0nk111-bot references with m0nk111-post
- **AGENT_ROLES.md**: Replaced m0nk111-bot examples with m0nk111-post

### Removed

- **m0nk111-bot References**: Eliminated suspended account from all documentation
- **Outdated Account Info**: Removed references to deprecated bot token files

## 2025-10-10

### Fixed

- **Archived misleading planning docs**: Moved REFACTOR_PLAN.md → archive/REFACTOR_PLAN_COMPLETED.md (refactor already done), CONSOLIDATION_PLAN.md → archive/CONSOLIDATION_PLAN_UNEXECUTED.md (plan never executed), README.old.md → archive/README.old.md
- **Fixed config/agents.yaml references** (27+ occurrences): Updated to `config/agents/*.yaml` or `config/agents/` directory in PROVISIONAL_GOALS.md, ARCHITECTURE.md, CHANGELOG.md, CONTRIBUTING.md, DEPLOYMENT_CHECKLIST.md, AGENT_DEVELOPMENT_GUIDE.md, INSTALLATION.md, AGENT_ONBOARDING.md, DEPLOYMENT.md, LOCAL_SHELL_ACCESS.md
- **Fixed code path examples in QWEN_MONITORING.md**: Updated `agents/code_agent.py` → `engine/runners/code_agent.py`, `from agents.qwen_agent` → `from engine.runners.code_agent`
- **Removed REFACTOR_PLAN references**: Deleted references to archived plan in PROVISIONAL_GOALS.md, marked directory structure as COMPLETED

### Added

- OUTDATED_DOCS_AUDIT.md: Comprehensive audit report of misleading/outdated documentation

### Notes

- Directory refactor (Issue #69) was already completed but docs still referenced it as future work
- File `config/agents.yaml` no longer exists, replaced by individual files in `config/agents/` directory
- All code examples now use correct `engine/` paths instead of old `agents/` paths

## 2025-10-09

### Fixed

- PROVISIONAL_GOALS.md: Removed duplicated footer block and stray checklist line; ensured single, clean document footer.
- TOKEN_SECURITY.md: Replaced stray non-ASCII character in "Quick Start" heading; normalized to ASCII heading text.

### Notes

- These were formatting-only fixes; no content semantics changed.
