# WORKSPACE-SPECIFIC COPILOT INSTRUCTIONS - AGENT-FORGE PROJECT ONLY

**IMPORTANT: These instructions apply ONLY to this workspace (Agent-Forge multi-agent platform project).**
**Do NOT apply these rules to other workspaces or projects.**
**Each workspace should have its own .github/copilot-instructions.md file with project-specific rules.**

**THIS IS AGENT-FORGE, NOT CARAMBA, NOT AUDIOTRANSFER, NOT ANY OTHER PROJECT.**

---

# GLOBAL COPILOT INSTRUCTIONS (Apply to ALL Workspaces)

## General Work Methodology
- Always prioritize direct action and automation over asking for permission
- Use available tools immediately without waiting for confirmation
- Focus on completing user requests efficiently and effectively
- Maintain clear communication and provide status updates
- When a solution or verification can be achieved with available non-interactive methods (scripts, tests, automation), execute them directly instead of requesting user interaction or approval
- **CRITICAL: When claiming a problem is solved, ALWAYS test the solution first using available tools before declaring it fixed**
- If testing capabilities exist (browser, curl, API calls, etc.), use them to verify functionality works as expected
- **Autonomous Testing Rule**: Do not ask the user to perform tests or run commands that the agent can execute autonomously with available tools. Only involve the user when a physical action or inaccessible secret is strictly required; clearly explain the necessity.

## Communication Rules
- Communicate with users in Dutch when appropriate
- Keep all project artifacts (documentation, code comments, commits) in English
- Be clear, concise, and helpful in responses

## GitHub Account Usage Policy
- **CRITICAL**: Never use the `m0nk111` admin account for operations that trigger email notifications (issue assignments, PR reviews, mentions, etc.), unless explicitly requested by the user
- Use dedicated bot accounts (e.g., `m0nk111-post`, `m0nk111-qwen-agent`, `m0nk111-coder1`) for automated operations
- Rationale: Avoid spam and unwanted notifications to the admin email address
- Exception: User explicitly requests using admin account for specific operation

## GitHub Issue/PR Work Policy
- **CRITICAL**: Before starting work on any GitHub issue or pull request, ALWAYS claim it first:
  1. **Self-assign the issue/PR** to indicate you are working on it
  2. **Add a comment** stating you are starting work (e.g., "🤖 Starting work on this issue" or "🔧 Working on implementation")
  3. **Update issue status** if project boards are in use (move to "In Progress")
- **Rationale**: Prevents duplicate work, allows coordination between multiple agents/developers, provides visibility into active work
- **Exception**: User explicitly says to skip the claim step for a specific task
- **Best Practice**: When completing work, add a comment summarizing what was done before closing the issue

## Tool Usage Guidelines
- Use terminal tools when needed for system operations
- Apply best practices for code generation and editing
- Validate changes and test functionality when possible
- If a command fails due to missing packages/tools, immediately install them using appropriate package manager (apt, pip, npm, etc.)
- **Git Workflow**: Always create file-specific commit messages when modifying individual files, describing exactly what was changed and why

## Quality Standards
- Write clean, maintainable code
- Follow established conventions and patterns
- Document important decisions and changes

## Project Structure Convention
- **Root Directory Rule**: Project root may ONLY contain README.md, CHANGELOG.md, LICENSE, and standard config files (.gitignore, .github/, .vscode/)
- **All other files must be organized in subdirectories** with a narrow and deep tree structure
- **Rationale**: Keep root clean, promote organization, easier navigation, clear project structure
- **Examples**:
  - ✅ GOOD: `/docs/ARCHITECTURE.md`, `/engine/core/main.py`, `/scripts/deploy.sh`
  - ❌ BAD: `/ARCHITECTURE.md`, `/main.py`, `/deploy.sh` (all should be in subdirectories)
- **When creating new files**: Always place them in appropriate subdirectory, create new subdirs if needed

## Debug Code Requirements

When implementing any feature or component:

1. **Always Include Debug Logging**: Add comprehensive debug output throughout all code
2. **Global Debug Control**: Implement a DEBUG flag (config variable or environment variable) that controls debug output
3. **Persistence**: Debug flag state should be configurable via environment or config files
4. **Granular Output**: Include debug information for:
   - Function entry/exit points
   - Key variable values and state changes
   - Error conditions and exceptions
   - Performance metrics (timing, resource usage)
   - State transitions
   - Network operations
5. **Clear Formatting**: Use emoji prefixes for easy scanning:
   - 🐛 General debug information
   - 🔍 Detailed inspection/analysis
   - ⚠️ Warnings or edge cases
   - ❌ Errors
   - ✅ Success confirmations
   - 📊 Statistics/metrics
   - 🔧 Configuration changes
6. **Performance Impact**: Ensure debug code has minimal overhead when disabled

---

# AGENT-FORGE SPECIFIC INSTRUCTIONS

## Recent Changes & Context

### October 2025 Updates
- **Smart Task Recognition**: Implemented intelligent task inference from descriptive issue requirements
- **YAML Config Loading**: Polling service now loads configuration from `config/services/polling.yaml`
- **Claim Management**: Fixed claim timeout and username configuration issues
- **Agent Refactoring**: `qwen_agent.py` → `code_agent.py` (generic LLM support)
- **Workspace Identification**: This header added to prevent agent confusion between projects
- **Bug Fixes**: GitHub CLI replaced with REST API (systemd compatibility)

### Agent Naming Convention
- **Code Agent**: `engine/operations/code_agent.py` (generic LLM, not Qwen-specific)
- **Bot Agent**: `engine/operations/bot_agent.py` (GitHub operations, no email spam)
- **Coordinator Agent**: `engine/core/coordinator_agent.py` (task orchestration)
- **Polling Service**: `engine/runners/polling_service.py` (GitHub issue monitoring)
- **Issue Handler**: `engine/operations/issue_handler.py` (autonomous issue resolution)

## Project Structure Conventions

### Root Directory Rule
- **Rule**: Only README.md, CHANGELOG.md, LICENSE, ARCHITECTURE.md, and configuration files allowed in root
- **Rationale**: Keep root clean for better navigation (cleanup completed October 2025)
- **Enforcement**: Block creation of other files in root directory
- **Exceptions**: .gitignore, .github/*, .vscode/*, requirements.txt, setup.py
- **Recent Cleanup**: All test/demo scripts moved to tests/ and scripts/ directories

### Directory Organization
- **Rule**: Use narrow and deep directory structure
- **Engine Structure**: 
  - `engine/core/` - Core services (service_manager, agent_registry)
  - `engine/operations/` - Operational modules (issue_handler, github_api_helper, file_editor)
  - `engine/runners/` - Long-running services (polling_service, monitor_service)
  - `engine/validation/` - Validation modules (instruction_validator, instruction_parser)
- **Example**: `engine/operations/validators/` not `validators/` in root
- **Rationale**: Better scalability and organization

## Documentation Standards

### Language Convention
- **Rule**: All documentation, comments, and code must be in English
- **Rationale**: International collaboration and consistency
- **Applies to**: Code comments, docstrings, README files, commit messages

### CHANGELOG.md Requirements
- **Rule**: Every code change must have CHANGELOG.md entry
- **Format**: `## [Version] - YYYY-MM-DD\n### Added/Changed/Fixed\n- Description`
- **Rationale**: Track all changes for users and maintainers

### DOCS_CHANGELOG.md Requirements
- **Rule**: Documentation changes require DOCS_CHANGELOG.md entry
- **Rationale**: Track documentation evolution separately

## Git Standards

### Commit Message Format
- **Rule**: Use conventional commits format
- **Format**: `type(scope): description`
- **Types**: feat, fix, docs, style, refactor, test, chore
- **Example**: `feat(validator): add instruction parser`

### File-Specific Commits
- **Rule**: Commit message must describe exact changes to specific files
- **Bad**: "Update files"
- **Good**: "feat(parser): add YAML rule parsing to instruction_parser.py"

### External Code Policy
- **Rule**: No commits allowed in external-code/ directories
- **Rationale**: Preserve third-party code integrity

### Changelog Before Commit
- **Rule**: CHANGELOG.md must be updated before creating commit
- **Enforcement**: Pre-commit validation checks for changelog entry

## Code Quality Standards

### Debug Logging Requirements
- **Rule**: All debug logs must use emoji prefixes
- **Format**: `logger.debug("🔍 Parsing rule: {rule_name}")`
- **Emojis**: 🔍 (inspect), ✅ (success), ❌ (error), ⚠️ (warning), 🐛 (debug)

### Global DEBUG Flag
- **Rule**: Use global DEBUG flag for debug logging
- **Example**: `if DEBUG: logger.debug(...)`
- **Rationale**: Easy debugging control

### Error Handling
- **Rule**: All functions must have proper error handling
- **Pattern**: Try-except with specific exceptions, log errors

### Test Coverage
- **Rule**: Minimum 80% test coverage for new code
- **Rationale**: Ensure code quality and reliability

## Infrastructure Standards

### Port Management
- **Rule**: Port usage within assigned ranges
- **Range**: 7000-7999 for this project
- **Assigned Ports**:
  - 7997: Monitoring & WebSocket service
  - 8897: Web UI dashboard
  - 7996: SSH Auth API (optional)
- **Rationale**: Avoid port conflicts with other services

### IP Address Conventions
- **Rule**: Use environment variables for IP addresses
- **Example**: `HOST = os.getenv('HOST', '0.0.0.0')`
- **Rationale**: Deployment flexibility

### Docker/Compose Validation
- **Rule**: Validate docker-compose.yml syntax before commit
- **Tools**: docker-compose config

## Testing Standards

### Test Organization
- **Rule**: Tests in tests/ directory, mirror source structure
- **Example**: `tests/test_instruction_validator.py` for `engine/validation/instruction_validator.py`

### Test Naming
- **Rule**: Test functions start with `test_`
- **Pattern**: `test_<function>_<scenario>`
- **Example**: `test_validate_commit_message_invalid_format`

## Configuration Management

### YAML Config Files
- **Location**: `config/services/` for service configs
- **Validation**: All YAML files must be valid and loadable
- **Loading**: Services should load config from YAML, not hardcode values
- **Example**: Polling service loads from `config/services/polling.yaml`

### Environment Variables
- **Location**: `.env` file in project root (not committed)
- **Required Variables**:
  - `GITHUB_TOKEN`: GitHub API token for bot operations
  - `BOT_GITHUB_TOKEN`: Bot-specific GitHub token
- **Loading**: Use `python-dotenv` for loading

## Smart Task Recognition System

### Task Inference
- **Feature**: Automatically infer file creation from descriptive requirements
- **Keywords**: create, add, new, generate, make
- **Fallback**: Check issue body and title for filenames
- **Example**: Issue "Create welcome document" → infers "Create docs/welcome.md" if mentioned in body

### Task Synthesis
- **Feature**: Generate explicit tasks from implicit requirements
- **Location**: `issue_handler.py:_parse_issue_requirements()`
- **Priority**: Body first (more common), then title
- **Pattern**: Extract filename with regex `[\`]?([\w/.-]+\.\w+)`

## Lessons Learned & Best Practices

### Smart Task Recognition Implementation (October 2025)
**What Could Have Been Avoided:**
- **Hardcoded configuration**: Polling service had hardcoded config values instead of reading from YAML
- **Username mismatch**: Config specified wrong GitHub username causing issues not to be found
- **High claim timeout**: 60-minute timeout prevented testing of expired claims
- **Multiple restarts**: Had to restart service many times to test config changes

**Lessons Learned:**
- **YAML-first configuration**: Always load config from YAML files, never hardcode
- **Config validation**: Validate config values at startup and log them
- **Username consistency**: Ensure usernames match across all systems (GitHub, config, assignments)
- **Reasonable timeouts**: Use shorter timeouts during development for faster iteration
- **Debug logging**: Comprehensive debug logs saved hours of debugging time
- **Test in isolation**: Test config loading separately before integration

### Configuration Management Best Practices
- **Centralized config**: Keep all config in `config/` directory
- **Environment separation**: Use different configs for dev/staging/production
- **Validation**: Validate all config at application startup
- **Logging**: Log loaded config values (sanitize secrets)
- **Hot reload**: Support config reload without restart when possible
- **Defaults**: Provide sensible defaults for all config values
