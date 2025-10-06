# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased] - 2025-10-06

### Added

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
