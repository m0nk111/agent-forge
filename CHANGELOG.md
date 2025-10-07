# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased] - 2025-10-07

### Added

- **Agent configuration refactoring** - Moved to per-agent config files
  - Removed monolithic `config/agents.yaml` (backed up to backups/)
  - Created dedicated `config/qwen_main_agent.yaml` for qwen-main-agent
  - Existing configs: `bot_config.yaml` (m0nk111-bot), `coordinator_config.yaml`, `polling_config.yaml`
  - Benefits: Cleaner separation, easier maintenance, more flexible per-agent settings
  - Trusted agents: Separate `trusted_agents.yaml` for GitHub account credentials
  - Architecture: Each agent has its own config file with full settings

- **API-level service/agent separation** - Clean architectural separation of infrastructure and agents
  - New endpoint: `/api/services` - Returns only infrastructure services (polling-service)
  - Services API: Filters services by service_ids, separate from agent monitoring
  - Dashboard integration: Dashboard now fetches services from dedicated endpoint
  - Real-time updates: Services section updates from `/api/services` on WebSocket connect
  - Method fix: Corrected `monitor.get_agents()` → `monitor.get_all_agents()`
  - Production sync: Websocket handler updated in both dev and production (/opt/agent-forge)

- **Dashboard UI/UX improvements** - Separated infrastructure services from agents
  - New Services section: Infrastructure services (polling, monitoring, web_ui, code_agent) now displayed separately
  - Visual distinction: Purple border for services, blue border for agents
  - Compact service cards: Show service name, type, and health status (green/red dot)
  - Service status monitoring: Auto-updates when WebSocket connects
  - Layout reorganization: Left column now shows Services (top) and Agents (bottom)
  - Service labels: "GitHub Polling", "Monitoring API", "Web Dashboard", "Code Agent Runtime"

- **Authentication improvements** - Enhanced login debugging and user experience
  - Debug logging: Added console logging for auth API URL, request, and response
  - Better error messages: More specific connection error messages (includes port number)
  - Login flow tracking: Track authentication attempts step-by-step in console

- **Systemd service fixes** - Bot token integration and polling service activation
  - Bot token: Added BOT_GITHUB_TOKEN environment variable to systemd service
  - Polling service: Now starts successfully with bot credentials
  - Health monitoring: All 4 services (polling, monitoring, web_ui, code_agent) report healthy
  - Service file location: `/etc/systemd/system/agent-forge.service`

### Fixed

- **Dashboard launch script** - Fixed working directory issue
  - Path fix: `launch_dashboard.sh` now uses `cd "$(dirname "$0")/.."` to reach project root
  - Resolved 404 errors when accessing dashboard files

- **WebSocket handler** - Started monitoring service on port 7997
  - Service activation: WebSocket handler now runs via systemd service_manager
  - Port management: Properly handles port conflicts and cleanup

**Role system integration fixes** - Complete integration of role-based permissions and UI
  - Legacy config cleanup: Moved `config/agents.yaml` to `config/backups/agents.yaml.legacy` (avoid confusion)
  - Permission presets: Added 7 role-specific permission presets to `permissions.py`
    * COORDINATOR: Read-only files/terminal, full GitHub coordination, config access (10 permissions)
    * DEVELOPER: Full file/terminal access, no PR merge (13 permissions)
    * REVIEWER: Read-only, can create issues/PRs with feedback (7 permissions)
    * TESTER: File write (tests only), terminal execute, no merge (9 permissions)
    * DOCUMENTER: File write (docs only), no terminal execute (8 permissions)
    * BOT: Read-only files/terminal, issue management, NO merge (8 permissions)
    * RESEARCHER: Read-only, full API access for research (8 permissions)
  - Helper function: `get_preset_for_role()` maps agent role → permission preset
  - UI updates: Config UI now shows/edits role field with dropdown and badge
  - CSS updates: Added `.badge-info` and `.form-help` styles for role display
  - API updates: `config_routes.py` models support role field (AgentConfigModel, AgentUpdateModel)
  - Bot token setup: Created `secrets/agents/m0nk111-bot.token.example` with setup instructions
  - README update: Bot token setup documentation in Security section
  - Testing: Validated all 3 agents load with roles, permissions map correctly per role
  - Verified: BOT role has NO file write, NO terminal execute, NO merge permissions

- **Role-based agent system** - Enhanced agent configuration with specialized roles
  - New `role` field in AgentConfig: coordinator, developer, reviewer, tester, documenter, bot, researcher
  - New agent: `m0nk111-bot` with bot role for automated operations (posting, organizing, triage)
  - Bot agent features: 3 concurrent tasks, 30s polling, no shell access, lower temperature (0.3)
  - Bot capabilities: issue_management, posting, organization, notifications, automation
  - Updated existing agents with roles: m0nk111-qwen-agent (developer), qwen-main-agent (coordinator)
  - New documentation: `docs/AGENT_ROLES.md` - Complete guide to agent roles and usage (400+ lines)
  - Role-based task assignment in CoordinatorAgent using AgentRole enum
  - Benefits: Clear responsibilities, efficient task matching, security through role permissions

- **Directory refactor (Issue #69)** - Restructured codebase for better scalability
  - New structure: `engine/` package with subpackages (runners, core, operations, validation)
  - Moved all agent code from `agents/` to `engine/` with logical organization
  - Individual agent configs: `agents/*.yaml` files (one file per agent, hot-reload ready)
  - New trust list: `config/trusted_agents.yaml` separate from agent configs
  - ConfigManager enhancement: Load agents from individual YAML files in `agents/` directory
  - Import updates: All imports changed from `agents.*` to `engine.*` (55 files updated)
  - Script updates: `scripts/start-service.sh` uses `engine.core.service_manager`
  - Benefits: Hot-reload support, scalable to 100+ agents, clean separation of data vs code

- **Production deployment tools** - Complete deployment checklist and automation
  - New file: `docs/DEPLOYMENT_CHECKLIST.md` - Comprehensive pre-deployment checklist (300+ lines)
  - New script: `scripts/quick-deploy.sh` - Automated deployment verification (one-command deploy)
  - Checklist sections: Code Quality, Configuration, Documentation, Security, Services, Testing, Git, Deployment
  - Pre-production checks: Security hardening, performance tuning, monitoring, backup & recovery
  - Post-deployment verification: Service status, port availability, health checks, log monitoring
  - Rollback procedure: Step-by-step instructions for emergency rollback
  - Deployment notes template: Structured deployment documentation format

- **Complete installation documentation** - Full setup guide for new users
  - New file: `docs/INSTALLATION.md` - 340+ line comprehensive installation guide
  - Sections: Prerequisites, Quick Install, Detailed Setup (7 subsections), Verification (4 tests), Troubleshooting, Next Steps
  - Testing procedures: Auth service, agent service, dashboard, token loading
  - Troubleshooting guides: Auth issues, CORS problems, token loading, Ollama connectivity
  - Quick install: 9-step command sequence for rapid setup
  - Detailed setup: Python environment, Ollama, agent config, GitHub tokens, systemd services, passwordless sudo

- **Updated README with security documentation**
  - New section: "Security & Authentication" in README.md (50 lines)
  - Dashboard authentication instructions (SSH/PAM login, 24h JWT sessions)
  - Token security model explanation (secrets/ directory, 0600 permissions)
  - Setup instructions for new users
  - Links to comprehensive security documentation

- **SSH/PAM authentication system** - Simpler dashboard security using system credentials
  - New file: `api/auth_routes.py` - SSH authentication via PAM (replaces OAuth)
  - Endpoints: `/auth/login`, `/auth/logout`, `/auth/user`, `/auth/status`, `/health`
  - Session management with JWT tokens (24-hour expiry, HttpOnly cookies)
  - No external dependencies - works offline with system users
  - 5-minute setup vs 30-minute OAuth setup
  
- **Token security system** - Protected GitHub tokens outside git
  - New directory: `secrets/agents/` for sensitive tokens (0600 permissions)
  - ConfigManager enhancement: Automatic token loading from secrets directory
  - Updated `.gitignore`: Blocks `secrets/`, `*.token`, `*.key` files
  - Migration: Tokens removed from `config/agents.yaml`, stored in individual files
  - Protection: Tokens never committed to git, isolated per agent

- **Dashboard authentication integration**
  - Login page: Modern UI matching dashboard theme (slate/blue gradient)
  - Auth check on page load: Automatic redirect to login if not authenticated
  - Dynamic API URLs: Works with any IP address (not hardcoded localhost)
  - User display: Shows authenticated username with logout button
  - CORS configuration: Supports multiple dashboard IPs (192.168.1.26, 192.168.1.30)

### Changed

- **OAuth system archived** - Replaced by simpler SSH authentication
  - File renamed: `api/auth_routes.py` → `api/auth_routes_oauth.py.backup`
  - Reason: OAuth too complex for local development/testing
  - Preserved for future reference if public deployment needed
  
- **Login page styling** - Updated to match dashboard aesthetics
  - Background: Purple/violet gradient → Dark slate/blue gradient (#0f172a → #1e293b)
  - Container: White → Dark transparent with backdrop blur
  - Inputs: Light borders → Blue accent borders with dark background
  - Button: Purple gradient → Blue gradient (#3b82f6 → #2563eb)
  - Text colors: Dark → Light slate (#e2e8f0, #94a3b8)
- **Auth service startup script**
  - New file: `scripts/start-auth-service.sh`
  - Validates OAuth configuration
  - Generates session secrets
  - Starts auth API on port 7999

- **Complete passwordless sudo for user flip**
  - Added `/etc/sudoers.d/flip-nopasswd` with `flip ALL=(ALL) NOPASSWD: ALL`
  - No more password prompts for ANY sudo command
  - Resolves user request: "ik wil voor alle sudo commands geen passwd intikken"

### Changed

- **Config API PATCH endpoints made public for dashboard self-service**
  - Removed `Depends(verify_token)` from `PATCH /api/config/agents/{agent_id}` and `PATCH /api/config/agents/{agent_id}/permissions`
  - Enables dashboard to save agent configurations without authentication
  - Suitable for single-user local deployments
  - Users can now update GitHub tokens, LLM settings, and permissions via dashboard
  
- **qwen-main-agent configured with GitHub token**
  - Set `github_token` for qwen-main-agent using m0nk111-bot account
  - Agent can now authenticate with GitHub API for issue/PR operations

- **Sudoers configuration enhanced for passwordless operations**
  - Added NOPASSWD rules for `cp`, `kill`, `pkill` commands
  - File: `/etc/sudoers.d/agent-forge-extra` (mode 0440)
  - Eliminates password prompts for agent-forge deployment operations
  - Maintains security by limiting scope to agent-forge paths and specific commands

### Fixed

- **Dashboard config modal now loads complete agent settings** - Config API integration
  - `frontend/dashboard.html`: `openAgentConfigModal()` now fetches from Config API instead of WebSocket data
  - WebSocket data only contains runtime state, not full configuration
  - Config modal now correctly shows LLM provider, model, temperature, max_tokens, shell permissions
  - Resolves issue: "ik zie de locale llm niet geselecteerd, geen API token"
  - User reported: Config modal showed empty/default values instead of actual agent config
  
- **Config API Pydantic models updated with Issue #30 & #31 fields**
  - `api/config_routes.py`: Added missing fields to `AgentConfigModel` and `AgentUpdateModel`
  - Added: `model_provider`, `model_name`, `api_key_name`, `temperature`, `max_tokens`
  - Added: `local_shell_enabled`, `shell_working_dir`, `shell_timeout`, `shell_permissions`
  - GET endpoints now return complete agent configuration
  
- **Config API GET endpoints made public for dashboard access**
  - Removed `Depends(verify_token)` from `GET /api/config/agents` and `GET /api/config/agents/{agent_id}`
  - Read-only endpoints don't require authentication
  - Dashboard can now load agent configs without auth headers

### Added

- **Dashboard now shows configured-but-inactive agents** - Monitor service integration with ConfigManager
  - `agents/monitor_service.py`: Extended `get_all_agents()` to include config-only agents
  - Agents from `config/agents.yaml` without active instances now appear with status "OFFLINE"
  - Current task shows "Agent configured but not running" for inactive agents
  - Enables visibility of all configured agents without requiring them to be running
  - No service restart needed - dashboard automatically shows config changes on WebSocket reconnect
  - Example: `m0nk111-qwen-agent` now visible in dashboard despite not being started

- **New Agent: m0nk111-qwen-agent** - Second production agent configuration
  - Agent ID: `m0nk111-qwen-agent` (matches GitHub username from trusted_agents)
  - Model: Local Ollama `qwen2.5-coder:7b`
  - Full capabilities: code_generation, code_review, issue_management, pr_management, documentation
  - Developer shell permissions at `/opt/agent-forge`
  - Temperature: 0.7, Max tokens: 4096
  - GitHub token to be configured via dashboard UI
  - Complements existing `qwen-main-agent` for multi-agent workflows

- **Create Agent UI Modal with GitHub Integration** - Complete agent creation flow via dashboard
  - New "Create Agent ➕" button in dashboard header (green styling, positioned between view toggle and agent count)
  - Complete Create Agent modal form with fields:
    * Agent ID (required, validated: lowercase, numbers, hyphens only)
    * Agent Name (required, display name)
    * GitHub Token (required, password field with validation button)
    * GitHub Username (auto-detected readonly field)
    * LLM Provider dropdown (local, openai, anthropic, google)
    * Model dropdown (dynamic loading based on provider)
  - GitHub token validation with auto-username detection:
    * New backend endpoint: `POST /api/github/validate-token`
    * Accepts `github_token` in request body
    * Calls GitHub API: `GET https://api.github.com/user` with Bearer token
    * Returns: `{is_valid: bool, username: str, name: str, email: str, avatar_url: str}`
    * Error handling for 401 (invalid token), 403 (rate limit), 500 (network error)
    * 10 second timeout for API calls
  - JavaScript functions implemented:
    * `openCreateAgentModal()` - Show modal, reset form, load default models
    * `closeCreateAgentModal()` - Hide modal, restore body overflow
    * `validateGithubToken()` - Validate token and auto-populate username field
    * `updateNewAgentModels()` - Dynamic model loading from `/api/llm/providers/{provider}/models`
    * `createNewAgent()` - Create agent via `POST /api/config/agents` with full validation
  - Auto-refresh dashboard after successful agent creation
  - Complete validation: required fields, agent ID pattern, GitHub username detection
  - Integration with Issues #30 & #31: new agents get permissions and LLM provider config

- **Agent Permissions System UI (Issue #30 - Complete)** - Full UI integration for permissions management
  - Updated `frontend/dashboard.html` with comprehensive permissions section:
    * Permission preset selector (READ_ONLY 🔵, DEVELOPER 🟢, ADMIN 🔴, CUSTOM ⚙️)
    * 15+ categorized permission checkboxes (File System, Terminal, GitHub, API, System)
    * Danger level indicators (⚠️ Dangerous, 🚨 CRITICAL)
    * Auto-switch to "custom" preset when manually changing checkboxes
  - JavaScript functions implemented:
    * `applyPermissionPreset()` - Apply read_only/developer/admin presets
    * `loadAgentPermissions(agentId)` - Load from `/api/config/agents/{id}/permissions`
    * `saveAgentPermissions(agentId)` - Save via PATCH with preset and grant array
  - Integrated into agent config modal:
    * `openAgentConfigModal()` calls `loadAgentPermissions()` to load current settings
    * `saveAgentConfig()` calls `saveAgentPermissions()` to persist changes
  - Status: **COMPLETE** - Backend and UI fully integrated and tested

- **Multi-Provider LLM UI (Issue #31 - Complete)** - Full UI integration for LLM provider management
  - Updated `frontend/dashboard.html` with LLM provider section:
    * Provider dropdown (local 🏠, openai 🟢, anthropic 🟣, google 🔵)
    * Dynamic model dropdown (updates based on provider)
    * API key input field (password, hidden for local provider)
    * Test connection button with status display (✅/❌/🔄)
  - JavaScript functions implemented:
    * `updateProviderModels()` - Load models per provider, show/hide API key field
    * `testProviderConnection()` - Test API key via `/api/llm/test-connection`
  - Integrated into agent config modal:
    * `openAgentConfigModal()` loads `model_provider` and `model_name` fields
    * `saveAgentConfig()` saves provider settings to backend API
  - Status: **COMPLETE** - Backend and UI fully integrated and tested

- **Agent Permissions System API (Issue #30)** - Complete permissions management with API endpoints
  - Added permissions endpoints to `api/config_routes.py`:
    * `GET /api/config/agents/{id}/permissions` - Get agent permissions configuration
    * `PATCH /api/config/agents/{id}/permissions` - Update permissions (preset, grant, revoke)
    * `GET /api/permissions/metadata` - Get all permissions metadata with descriptions and warnings
  - API models:
    * `PermissionsModel`: preset (read_only/developer/admin), permissions dict
    * `PermissionsUpdateModel`: preset change, grant list, revoke list
  - Permission management features:
    * Set permission preset (READ_ONLY, DEVELOPER, ADMIN, CUSTOM)
    * Grant individual permissions
    * Revoke individual permissions
    * Get permissions metadata with danger warnings
    * List presets with emoji indicators (🔵🟢🔴)
  - Integration with existing permission framework from Issue #64

- **Multi-Provider LLM Support (Issue #31)** - Enable OpenAI, Anthropic, Google, and local LLMs
  - Created `agents/llm_providers.py` (500+ lines) - Unified LLM provider interface:
    * `LLMProvider` base class with chat_completion(), test_connection(), get_available_models()
    * `OpenAIProvider`: GPT-4, GPT-4 Turbo, GPT-3.5 support with org ID
    * `AnthropicProvider`: Claude 3.5 Sonnet, Claude 3 Opus/Haiku support
    * `GoogleProvider`: Gemini Pro, Gemini 1.5 Pro/Flash support
    * `LocalProvider`: Ollama, LM Studio support (no API key required)
    * `LLMMessage` and `LLMResponse` dataclasses for unified interface
    * Timeout handling (60s chat, 120s local)
    * Usage tracking (prompt_tokens, completion_tokens, total_tokens)
  - Created `agents/key_manager.py` (400+ lines) - Secure API key management:
    * `KeyManager` class with JSON file storage (keys.json)
    * Secure file permissions (0600 - owner read/write only)
    * Key masking for display (sk-...abc123)
    * Environment variable fallback
    * Provider key validation (format checking)
    * Connection testing per provider
    * 12 supported providers: OpenAI, Anthropic, Google, Groq, Replicate, Qwen, xAI, Mistral, DeepSeek, OpenRouter, Hugging Face, local
  - Extended `agents/config_manager.py` `AgentConfig` dataclass:
    * `model_provider: str` - Provider selection (openai, anthropic, google, local)
    * `model_name: str` - Specific model (gpt-4, claude-3-opus, gemini-pro, etc.)
    * `api_key_name: Optional[str]` - Reference to keys.json key name
    * `temperature: float` - Generation temperature (0.0-2.0, default 0.7)
    * `max_tokens: int` - Maximum tokens to generate (default 4096)
  - Added LLM API endpoints to `api/config_routes.py`:
    * `GET /api/llm/providers` - List all providers with configuration status
    * `GET /api/llm/providers/{provider}/models` - Get available models for provider
    * `POST /api/llm/test-connection` - Test API key validity
    * `GET /api/llm/keys` - List configured keys (masked)

### Fixed

- **Project Structure Cleanup** - Removed misplaced Caramba configuration file
  - Removed `configs/caramba_personality_ai.yaml` (belonged to Caramba project, not agent-forge)
  - File moved to `/home/flip/caramba/configs/` where it belongs
  - Removed empty `configs/` directory from agent-forge
  - Improves project separation and prevents confusion between agent-forge and Caramba

- **Agent Creation API Authentication** - Removed authentication requirements for agent creation flow
  - Removed `verify_token` dependency from `POST /api/config/agents` (allow unauthenticated agent creation)
  - Removed `verify_token` dependency from `POST /api/github/validate-token` (needed for new agent GitHub validation)
  - Removed `verify_token` dependency from `GET /api/llm/providers/{provider}/models` (needed for model selection during creation)
  - Fixed `local` provider validation in `get_provider_models`:
    - Now checks `PROVIDERS` dict instead of `PROVIDER_KEYS` (local provider has no API key)
    - Prevents "Unknown provider: local" error
  - Added `CONFIG_API_PORT` environment variable support (default: 7998)
  - Added `API_BASE_URL` auto-detection in frontend dashboard for cross-origin API calls
  - Updated critical frontend API calls to use `API_BASE_URL`:
    - GitHub token validation: `validateGithubToken()`
    - Model loading: `updateNewAgentModels()`
    - Agent creation: `createNewAgent()`
  - Rationale: New agents cannot authenticate before they exist, so creation endpoints must be public
  - Security note: Consider adding rate limiting or CAPTCHA for production deployments
    * `PATCH /api/llm/keys/{provider}` - Update API key with validation and connection test
    * `DELETE /api/llm/keys/{provider}` - Delete API key
  - Created `keys.example.json` - Template for API keys with all supported providers
  - Updated `.gitignore` - Exclude keys.json, *.key, *.pem, .env for security
  - Security features:
    * Keys never committed to git (keys.json gitignored)
    * File permissions enforced (chmod 600)
    * Key format validation before storage
    * Masked display in API responses (only last 6 chars visible)
    * Connection testing before accepting keys
    * Environment variable fallback for CI/CD
  - Feature capabilities:
    * Switch between commercial LLMs (OpenAI GPT-4, Anthropic Claude, Google Gemini)
    * Use local LLMs via Ollama/LM Studio (no API key needed)
    * Per-agent model configuration
    * Temperature and max_tokens tuning per agent
    * Multiple API key management
    * Test connections before deployment
  - Status: Backend complete, UI integration pending

- **Local Shell Access for Agent Testing (Issue #64)** - Enable agents to run tests on co-located repositories
  - Created `agents/permissions.py` (450 lines) - Granular permission system:
    * `Permission` enum with 20+ permissions across 5 categories (FILE_SYSTEM, TERMINAL, GITHUB, API, SYSTEM)
    * `PermissionMetadata` with danger warnings (🚨 CRITICAL for TERMINAL_EXECUTE, GITHUB_MERGE_PR, SYSTEM_RESTART)
    * `PermissionPreset` enum: READ_ONLY (safest), DEVELOPER (testing enabled), ADMIN (unrestricted)
    * `AgentPermissions` class with has_permission(), grant_permission(), get_dangerous_permissions()
    * `PermissionValidator` for operation authorization checks
    * DEVELOPER preset includes TERMINAL_EXECUTE for pytest/npm test/cargo test
  - Created `agents/shell_runner.py` (400 lines) - Safe shell command execution:
    * `ShellSafetyConfig`: 300s default timeout, blocked commands (rm -rf /, sudo, shutdown, fork bombs), blocked patterns (pipe to bash, writing to /dev/sd), allowed commands whitelist (pytest, npm, pip, git)
    * `CommandResult` dataclass: tracks command, status (SUCCESS/FAILURE/TIMEOUT/BLOCKED/ERROR), exit_code, stdout/stderr, execution_time
    * `ShellRunner.run_command()`: Validates working directory, checks blocked commands/patterns, enforces timeout, kills on timeout, truncates large output (10MB limit)
    * `ShellRunner.run_test_suite()`: Auto-detects test framework (pytest, npm, cargo, go, make) and runs with 600s timeout
    * `ShellRunner.kill_all_processes()`: Emergency process cleanup
    * Statistics tracking: success/failure/timeout/blocked counts, success rate calculation
  - Extended `agents/config_manager.py` `AgentConfig` dataclass:
    * `local_shell_enabled: bool` - Toggle shell access per agent
    * `shell_working_dir: Optional[str]` - Restrict execution directory
    * `shell_timeout: int` - Per-agent timeout (300s default)
    * `shell_permissions: str` - Permission preset ("read_only", "developer", "admin")
  - Created `docs/LOCAL_SHELL_ACCESS.md` (500+ lines) - Comprehensive documentation:
    * Security warnings and threat model
    * Architecture overview (Permission → ShellRunner → Audit)
    * Permission level comparison (Read-Only/Developer/Admin)
    * Configuration guide (YAML, Python API, Dashboard UI)
    * Safety guardrails (blocked commands, timeouts, working directory restrictions)
    * Usage examples (pytest, npm test, cargo test, build scripts)
    * Security best practices (least privilege, audit monitoring)
    * Troubleshooting guide (blocked commands, timeouts, permission errors)
    * Advanced topics (custom safety config, background processes, environment variables)
  - Feature capabilities:
    * Enable agents to validate code changes with pytest, npm test before committing
    * Auto-detect test framework from project structure (pytest.ini, package.json, Cargo.toml, go.mod, Makefile)
    * Block dangerous commands (rm -rf /, sudo, shutdown, piping to bash/sh)
    * Enforce timeouts to prevent infinite loops (default 5min, max 30min)
    * Restrict execution to allowed directories (/home/flip/agent-forge, /tmp/agent-*)
    * Log all commands with timestamp, agent_id, exit_code, execution_time
    * Track command history and statistics (success rate, failure analysis)
  - Security model:
    * Default: Locked down (READ_ONLY preset, no shell access)
    * Opt-in: DEVELOPER preset enables TERMINAL_EXECUTE for testing
    * Dangerous: ADMIN preset grants full access with explicit warnings
    * Multi-layer safety: permission check → command validation → working directory check → timeout enforcement
  - Testing workflow integration:
    * Agent generates code → writes files → runs tests → fixes failures → creates PR
    * Validation before PR creation reduces broken commits
    * Automated testing enables fully autonomous development loop
  - Status: Core implementation complete, pending API endpoints, UI integration, audit logging

## [Unreleased] - 2025-10-06

### Added

- **Security Audit System for External PRs (Issue #62)** - Mandatory security scanning for non-trusted contributors
  - Created `agents/security_auditor.py` (517 lines) with comprehensive scanning:
    * `SecurityIssue` dataclass: severity, category, description, file, line, recommendation, CWE ID
    * `AuditResult` dataclass: passed status, issues list, score (0-100), severity counts
    * 6 audit methods: secrets scanning, dependency checks, injection detection, malware patterns, license validation, code quality
  - Integrated security auditor into `agents/pr_reviewer.py`:
    * Loads trusted agents from `config/agents.yaml`
    * Non-trusted PR authors trigger mandatory security audit before review
    * PRs blocked on critical/high severity issues (cannot merge)
    * Trusted agents (m0nk111-bot, m0nk111-qwen-agent) bypass audit
    * Error handling: audit failures block PRs from untrusted authors for safety
    * Detailed security block message with issue breakdown, recommendations, CWE links
  - Updated `config/agents.yaml`: Added trusted_agents section with bot and qwen-agent accounts
  - Added security dependencies to `requirements.txt`: bandit>=1.7.5, safety>=3.0.0
  - Leverages existing `config/security_audit.yaml` (212 lines) with:
    * Severity thresholds (block on critical/high, warn on medium)
    * Blocked patterns (eval, exec, SQL injection, XSS, hardcoded secrets)
    * Tool configurations (bandit, safety, semgrep, npm audit)
    * License compliance rules (MIT/Apache/BSD allowed, AGPL/proprietary forbidden)
    * Performance settings (5min timeout, 1MB max file size, 100 files/PR limit)

- **Agent Configuration Modal** - Per-agent configuration interface integrated into default dashboard
  - Added gear icon (⚙️) button to each agent card
  - Full-featured modal with 8 configuration sections:
    * Basic Information (agent name, LLM model selection)
    * API Configuration (API tokens, GitHub PAT)
    * Model Parameters (temperature, max tokens)
    * Capabilities (code generation, review, issue/PR management, documentation)
    * Permissions (file read/write, terminal commands, PR operations)
    * Custom Instructions (agent-specific rules)
    * Rate Limits (API throttling)
  - Modal features:
    * Form validation for required fields
    * Reset to defaults button with confirmation
    * ESC key to close modal
    * Click-outside-to-close behavior
    * Smooth animations (slide-in effect)
    * Dark theme consistent with dashboard
  - Backend integration ready (TODO: connect to /api/config/agents/:id endpoint)
  - File size: dashboard.html grew from 1,341 lines to 1,808 lines (+467 lines, +35%)
  - Replaces need for separate unified_dashboard.html
  - Implements features from GitHub issues #27, #28, #65

- **Prominent Unified Dashboard Button** - Highly visible button in dashboard footer
  - Replaced small text link with styled green gradient button
  - Increased font size from 10px to 12px for better visibility
  - Added padding, border-radius, box shadow for button appearance
  - Implemented hover effect with transform and shadow animation
  - Used !important flags to override CSS cascade issues
  - Much more discoverable and clickable than previous text link

- **Auto-Deploy Frontend Script** - Automated deployment system for frontend changes
  - Created `/home/flip/agent-forge/scripts/auto_deploy_frontend.sh` (3.0K)
  - Systemd timer triggers every 60 seconds
  - Detects new commits on main branch via git fetch
  - Syncs frontend changes to production directory (/opt/agent-forge)
  - Restarts agent-forge.service when frontend files change
  - Lock file prevents concurrent deployments
  - Comprehensive logging to /var/log/agent-forge-deploy.log

- **Enterprise Visual Documentation Suite** - 13 comprehensive Mermaid diagrams covering all architectural aspects
  - `docs/diagrams/ENTERPRISE_DIAGRAMS.md` - 10 enterprise-level diagrams (~550 lines)
    * High-Level System Architecture (C4 Context model)
    * Deployment Architecture (Dev, Systemd, Docker scenarios)
    * Agent Lifecycle State Machine (complete state transitions)
    * Request Flow Sequences (issue processing, manual assignment)
    * WebSocket Communication Protocol (real-time updates, heartbeat)
    * Configuration Management Hierarchy (priority order, runtime updates)
    * Error Handling Flow (classification, retry logic, notifications)
    * Security Architecture (network/application/service/data layers)
    * Database Schema (ER diagram with all entities and relationships)
    * CI/CD Pipeline (complete GitHub Actions workflow)
  - `docs/diagrams/README.md` - Comprehensive diagram index (~800 lines)
    * Catalog of all 13 diagrams (architecture, deployment, communication, context)
    * Role-based navigation guides (Developer, DevOps, Contributor, Manager)
    * Viewing instructions (GitHub, VS Code, CLI export, online editor)
    * Diagram conventions, templates, and update procedures
    * Complete checklist for diagram maintenance
  - Total: ~2100 lines of visual documentation complementing 4,346 lines of text documentation

- **Workspace Identification** - Prominent header in `.github/copilot-instructions.md` to prevent agent confusion
  - Added clear "WORKSPACE-SPECIFIC" warning at top of instructions file
  - Identifies project as AGENT-FORGE to prevent mixing with other projects (Caramba, AudioTransfer, etc.)
  - Resolves issue where agents worked on wrong project's issues

- **Instruction Validation System** - Comprehensive validation of code changes against Copilot instructions (#63)
  - `agents/instruction_parser.py` - Parse `.github/copilot-instructions.md` files
  - `agents/instruction_validator.py` - Validate file locations, commit messages, changelog updates, port usage, and documentation language
  - `config/instruction_rules.yaml` - Configuration for validation rules and exemptions
  - Support for merging global and project-specific instructions
  - Auto-fix capabilities for commit messages and changelog entries
  - Compliance reporting with educational feedback
  - 30 comprehensive tests with 78% code coverage
  - Integration hooks in `IssueHandler`, `FileEditor`, `GitOperations`

- **Comprehensive Documentation Suite** - Complete architecture and onboarding documentation (#67)
  - **AGENT_ONBOARDING.md**: Structured checklist for AI agents to quickly understand the project
    - Must-read documents in priority order
    - Key architecture concepts to verify
    - Port overview (8080, 7997, 8897) with common pitfalls
    - Frontend structure clarification (dashboard.html is DEFAULT)
    - Deployment verification steps
    - Common mistakes and best practices
  - **ARCHITECTURE.md**: Complete system architecture documentation (root level)
    - Service Manager architecture and orchestration
    - Agent roles and responsibilities
    - WebSocket communication flow
    - Frontend file structure and relationships
    - Port allocation table with bind addresses
    - Configuration management hierarchy
    - Deployment architectures (local, systemd, future Docker)
    - Security considerations
  - **docs/diagrams/architecture-overview.md**: Visual system architecture (Mermaid)
    - Service Manager with all services and agents
    - Frontend structure (index→dashboard→unified→config→monitoring)
    - GitHub API integration
    - LLM connections (Ollama, OpenAI, Anthropic, Google)
    - Network topology diagram
  - **docs/diagrams/data-flow.md**: Complete data flow diagrams (Mermaid)
    - Issue processing lifecycle with sequence diagram
    - Monitoring data flow (agent → monitor → WebSocket → dashboards)
    - Configuration update flow with validation
    - WebSocket message types and patterns
    - Git operations flow (branch, commit, push, PR)
    - Rate limiting and caching strategies
  - **docs/diagrams/component-interactions.md**: Component communication patterns (Mermaid)
    - Service Manager orchestration lifecycle
    - Inter-agent communication via Message Bus
    - Configuration load and runtime update flows
    - Agent state tracking and metrics collection
    - Error handling and retry strategies
    - WebSocket connection management
    - API request lifecycle
  - **docs/PORT_REFERENCE.md**: Complete port allocation guide
    - Detailed port usage table (8080, 7997, 8897, 7996, 11434)
    - Configuration methods (env vars, config files, CLI)
    - Common port conflicts and resolutions
    - WebSocket troubleshooting
    - LAN access configuration
    - Firewall rules
    - Quick commands reference
    - Troubleshooting matrix
- **Documentation Cross-References**: Updated existing docs with diagram references
  - README.md: Added visual documentation link to Architecture section
  - QWEN_MONITORING.md: Added data flow diagram reference
  - MULTI_AGENT_GITHUB_STRATEGY.md: Added architecture and data flow references
- **Dashboard Footer Enhancement**: Link to unified dashboard from main dashboard
  - Added green "🚀 Try New Unified Dashboard" link in footer-left of dashboard.html
  - Added "✨ You are on the New Unified Dashboard" indicator in unified_dashboard.html footer

- **Agent Configuration Modal** - Direct agent configuration from dashboard (Issue #65)
  - **Configuration Button**: Added gear icon (⚙️) to top-right of each agent card
  - **Modal Design**: Clean overlay modal with organized sections for all config options
  - **Basic Information**: Agent name and LLM model selection (GPT-4, Claude 3, Qwen, Gemini, etc.)
  - **API Configuration**: Fields for API token and GitHub token (secure password inputs)
  - **Model Parameters**: Temperature (0-2) and max tokens controls with helpful descriptions
  - **Capabilities**: Checkboxes for code generation, code review, issue management, PR management, documentation
  - **Permissions**: Granular controls for file operations, terminal commands, PR creation/merging with warning labels
  - **Custom Instructions**: Textarea for additional agent-specific instructions
  - **Rate Limits**: API calls per minute control to prevent quota exhaustion
  - **Validation**: Required field validation and user-friendly error messages
  - **Accessibility**: Keyboard navigation (ESC to close), ARIA labels, hover effects
  - **Save/Cancel/Reset**: Three action buttons with clear labels and confirmation for destructive actions
  - **Smooth Animations**: Rotating gear icon on hover, modal fade-in with backdrop blur
  - **Responsive Design**: Works within fixed 1280x1024 dashboard layout
  - **Backend Ready**: Form collects all data for future API integration

- **Unified Dashboard** - New modern dashboard combining monitoring and configuration (Issues #27, #28)
  - **Fixed Layout**: 1280x1024 viewport with agent list (40%) + live logs (60%)
  - **Agent Cards**: Click-to-select agents with real-time status, model info, task progress
  - **Live Log Filtering**: View all logs or filter by selected agent
  - **Sliding Sidebar**: 400px configuration panel with smooth animations
  - **Agent Configuration**: Add/edit agents with model selection, permissions, capabilities
  - **Permission System**: Granular permissions (read files, write files, execute commands, GitHub ops, APIs)
  - **Model Selection**: Dropdown with GPT-4, Claude 3, Qwen 2.5 Coder, Gemini Pro options
  - **WebSocket Integration**: Real-time updates via existing monitoring infrastructure
  - **Dark Theme**: Consistent with existing Agent-Forge UI
  - **Footer Links**: Added navigation to unified dashboard from classic monitoring and config UI
  - **Backward Compatible**: Old dashboards remain default, new UI accessible via footer links

### Changed
- **BREAKING: Agent Refactoring** - Renamed `qwen_agent.py` to `code_agent.py` for generic LLM support (Issue #66)
  - **Class Rename**: `QwenAgent` → `CodeAgent` 
  - **File Rename**: `agents/qwen_agent.py` → `agents/code_agent.py`
  - **Service Manager**: Updated all service keys and methods (`enable_qwen_agent` → `enable_code_agent`)
  - **Configuration**: CLI flag `--no-qwen` kept for backward compatibility
  - **Documentation**: Updated all references in README, QWEN_MONITORING.md, MULTI_AGENT_GITHUB_STRATEGY.md, SETUP_QWEN_GITHUB_ACCOUNT.md
  - **Tests**: Updated imports in `test_issue_handler.py` and `test_qwen_monitoring.py`
  - **Migration Required**: Update any external code importing `QwenAgent` to use `CodeAgent`

### Added
- **API Test Endpoint** - Added `/api/hello` endpoint for API health verification (Issue #54)
  - Returns JSON with status, message, and UTC timestamp
  - No authentication required
  - Useful for testing and monitoring

### Changed
- **Project Structure Cleanup** - Reorganized root directory to comply with Copilot instructions
  - Moved all test scripts from root to `tests/` directory
  - Moved demo and utility scripts from root to `scripts/` directory
  - Moved YAML configuration files from root to `config/` directory
  - Moved documentation files (`BUGS_TRACKING.md`, `COMMERCIAL-LICENSE.md`) to `docs/` directory
  - Updated all references and import paths in documentation and scripts
  - Added dynamic sys.path fixes to standalone test scripts for proper imports
  - Root directory now only contains: README.md, CHANGELOG.md, LICENSE, .gitignore, requirements.txt, and standard config files
  - All functionality verified working after reorganization

### Added
## [Unreleased] - 2025-10-06

### Added

- **Comprehensive Documentation Suite** (commit `932580e`):
  - Created `CONTRIBUTING.md` (880 lines): Complete contributor guide with code of conduct, development workflow, coding standards, testing guidelines, PR process, issue templates, and agent development guide
  - Created `docs/TROUBLESHOOTING.md` (1017 lines): Exhaustive troubleshooting guide covering service issues, port conflicts, GitHub/Ollama problems, WebSocket issues, configuration errors, performance problems, and emergency recovery
  - Created `docs/TESTING.md` (786 lines): Complete testing guide with testing pyramid, unit/integration/E2E test examples, coverage requirements, mocking patterns, and CI/CD integration
  - Created `docs/API.md` (982 lines): Full REST API reference with all endpoints, authentication, error handling, rate limits, and code examples
  - Created `docs/DEPLOYMENT.md` (681 lines): Production deployment guide with systemd service, nginx reverse proxy, SSL setup, security hardening, monitoring, and backup strategies
  - **Total**: 4,346 lines of professional documentation covering all previously missing aspects
- **Documentation Enhancement** (commit `cb9ff1f`):
  - Created comprehensive `docs/LESSONS_LEARNED.md` (462 lines) documenting development insights, PR management, agent confusion prevention, testing strategies
  - Created `docs/SESSION_LOG_2025_10_06.md` documenting complete workflow of PR #63 and #67
  - Enhanced `README.md` with recent developments section and updated feature list
  - Enhanced `docs/AGENT_ONBOARDING.md` with workspace awareness warning and October 2025 updates
  - Updated `ARCHITECTURE.md` with recent changes context and refactoring details
  - Enhanced `.github/copilot-instructions.md` with agent naming conventions and PR references
- **Workspace Identification**: Added prominent header to `.github/copilot-instructions.md` to prevent agent confusion between projects (commit `cce8134`)
- **Instruction Validation System** (PR #63, commit `da7cb16`):

- **Integration Hooks** - Validation integrated into agent workflow
  - `IssueHandler` - Pre-commit validation of changed files and commit messages
  - `FileEditor` - Pre-edit validation of file locations
  - `GitOperations` - Commit message format validation with auto-fix
  - All integrations are optional and non-breaking

- **Sample Copilot Instructions** - `.github/copilot-instructions.md` with example rules
  - Project structure conventions (root directory rule)
  - Documentation standards (English language, changelog requirements)
  - Git standards (conventional commit format, file-specific commits)
  - Code quality standards (debug logging, error handling)
  - Infrastructure standards (port ranges, IP conventions)

### Changed
- Enhanced `IssueHandler` to validate changes before creating commits
- Enhanced `FileEditor` to check file locations before edits
- Enhanced `GitOperations` to validate and auto-fix commit messages

### Technical Details
- Validation system is modular and configurable
- All validations are optional and fail gracefully
- Backward compatible with existing code
- Educational feedback explains why rules exist
- Auto-fix reduces manual corrections
- Rule priority: Project-specific > Global > Defaults

### Testing
- 30 unit tests added for instruction validation
- All existing tests continue to pass
- Test coverage: 78% overall (82% validator, 72% parser)
- Comprehensive testing of all rule categories

## [0.1.0] - Previous Releases

### Added
- Initial agent framework
- Issue handling capabilities
- Git operations
- File editing
- PR review system
- Monitoring dashboard
- Polling service
- Bot operations

### Fixed

- **Agent configuration cleanup** - Removed duplicate offline agent
  - Removed `m0nk111-qwen-agent` from config (was duplicate, never started by service_manager)
  - Only `qwen-main-agent` remains as active code agent
  - Restored agents.yaml from backup (was empty: `agents: []`)
  - Trusted agents: m0nk111-bot configured for GitHub automation
  - Production config synced: /opt/agent-forge/config/agents.yaml
  - Service restarted: offline agent no longer appears in dashboard

