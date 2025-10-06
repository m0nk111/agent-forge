# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased] - 2025-01-06

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
