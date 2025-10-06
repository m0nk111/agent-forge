# WORKSPACE-SPECIFIC COPILOT INSTRUCTIONS - AGENT-FORGE PROJECT ONLY

**IMPORTANT: These instructions apply ONLY to this workspace (Agent-Forge multi-agent platform project).**
**Do NOT apply these rules to other workspaces or projects.**
**Each workspace should have its own .github/copilot-instructions.md file with project-specific rules.**

**THIS IS AGENT-FORGE, NOT CARAMBA, NOT AUDIOTRANSFER, NOT ANY OTHER PROJECT.**

---

# GitHub Copilot Instructions

## Project Structure Conventions

### Root Directory Rule
- **Rule**: Only README.md, CHANGELOG.md, LICENSE, and configuration files allowed in root
- **Rationale**: Keep root clean for better navigation
- **Enforcement**: Block creation of other files in root directory
- **Exceptions**: .gitignore, .github/*, .vscode/*, package.json, requirements.txt

### Directory Organization
- **Rule**: Use narrow and deep directory structure
- **Example**: `agents/validators/` not `validators/` in root
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
- **Emojis**: 🔍 (inspect), ✅ (success), ❌ (error), ⚠️ (warning)

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
- **Example**: `tests/test_instruction_validator.py` for `agents/instruction_validator.py`

### Test Naming
- **Rule**: Test functions start with `test_`
- **Pattern**: `test_<function>_<scenario>`
- **Example**: `test_validate_commit_message_invalid_format`
