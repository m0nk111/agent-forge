# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased] - 2025-01-06

### Added
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
- **Instruction Validation System** - Comprehensive validation of code changes against Copilot instructions
  - `agents/instruction_parser.py` - Parse `.github/copilot-instructions.md` files
  - `agents/instruction_validator.py` - Validate file locations, commit messages, changelog updates, port usage, and documentation language
  - `config/instruction_rules.yaml` - Configuration for validation rules and exemptions
  - Support for merging global and project-specific instructions
  - Auto-fix capabilities for commit messages and changelog entries
  - Compliance reporting with educational feedback
  - 30 comprehensive tests with 78% code coverage

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
