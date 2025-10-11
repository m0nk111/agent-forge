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
