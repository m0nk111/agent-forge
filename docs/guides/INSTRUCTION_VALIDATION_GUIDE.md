# Instruction Validation System - Usage Guide

This guide explains how to use the Copilot instructions validation system in agent-forge.

## Overview

The instruction validation system automatically enforces project standards defined in `.github/copilot-instructions.md`. It validates:

- **File locations** - Blocks files in root directory (except README, CHANGELOG, etc.)
- **Commit messages** - Enforces conventional commit format
- **Changelog updates** - Requires CHANGELOG.md updates for code changes
- **Port usage** - Validates ports are within assigned ranges
- **Documentation language** - Checks for English-only documentation

## Quick Start

### 1. Create Copilot Instructions

Create `.github/copilot-instructions.md` in your project:

```markdown
# GitHub Copilot Instructions

## Project Structure Conventions

### Root Directory Rule
- **Rule**: Only README.md, CHANGELOG.md, LICENSE allowed in root
- **Rationale**: Keep root clean for better navigation
- **Enforcement**: Block creation of other files in root directory

## Git Standards

### Commit Message Format
- **Rule**: Use conventional commits format
- **Format**: `type(scope): description`
- **Types**: feat, fix, docs, style, refactor, test, chore
```

### 2. Use Instruction Validator

```python
from agents.instruction_validator import InstructionValidator

# Initialize with project root
validator = InstructionValidator(project_root="/path/to/project")

# Validate file location
result = validator.validate_file_location("test.py")
if not result.valid:
    print(f"❌ {result.message}")
    for suggestion in result.suggestions:
        print(f"   💡 {suggestion}")

# Validate commit message
result = validator.validate_commit_message("update files")
if not result.valid:
    print(f"❌ {result.message}")
    
    # Try auto-fix
    fixed = validator.auto_fix_commit_message("update files")
    print(f"✅ Auto-fixed: {fixed}")

# Generate compliance report
report = validator.generate_compliance_report(
    changed_files=["engine/operations/test.py", "CHANGELOG.md"],
    commit_message="feat(validator): add validation"
)
print(report.get_summary())
# Output: ✅ COMPLIANT - 4/4 passed, 0 failed, 0 warnings
```

### 3. Integration with Agent Components

The validation system is automatically integrated into:

#### IssueHandler
```python
from agents.issue_handler import IssueHandler

# Validation happens automatically in _validate_changes()
handler = IssueHandler(agent)
handler.assign_to_issue("owner/repo", 42)
# Files are validated before commit
# Invalid locations are blocked
# Commit messages are auto-fixed
```

#### FileEditor
```python
from agents.file_editor import FileEditor

editor = FileEditor(project_root="/path/to/project")

# Validation happens automatically before edits
success = editor.replace_in_file(
    "invalid.py",  # File in root - will be blocked
    "old text",
    "new text"
)
# Output: ⚠️  File 'invalid.py' should not be in root directory
#         💡 Move to appropriate subdirectory
```

#### GitOperations
```python
from agents.git_operations import GitOperations

git = GitOperations()

# Commit message is validated and auto-fixed
git.commit(
    repo_path="/path/to/repo",
    message="update files"  # Invalid format
)
# Output: ⚠️  Invalid commit message format
#         🔧 Auto-fixed to: chore: update files
```

## Configuration

Edit `config/instruction_rules.yaml` to customize validation:

```yaml
validation:
  # Enable/disable specific validations
  enforce_root_files: true
  require_changelog: true
  validate_commit_format: true
  enforce_port_ranges: true
  
  # Port range for infrastructure validation
  port_range:
    min: 7000
    max: 7999

# Exemptions - files that bypass validation
exemptions:
  files:
    - .gitignore
    - .github/*
    - tests/*
  
  directories:
    - docs/*
    - examples/*

# Auto-fix capabilities
auto_fix:
  enabled: true
  commit_message_format: true
  changelog_generation: true
  safe_mode: true  # Ask before applying fixes

# Reporting
reporting:
  generate_reports: true
  format: markdown
  include_rationale: true  # Explain WHY rules exist
```

## Rule Categories

### 1. Project Structure
- **Root Directory Rule** - Only specific files allowed in root
- **Directory Organization** - Enforce narrow and deep structure
- **External Code Policy** - Block commits in external-code/

### 2. Documentation Standards
- **Language Convention** - All docs must be in English
- **CHANGELOG.md Requirements** - Update for every code change
- **DOCS_CHANGELOG.md** - Track documentation changes

### 3. Git Standards
- **Commit Message Format** - Conventional commits (feat, fix, docs, etc.)
- **File-Specific Commits** - Describe exact changes to files
- **Changelog Before Commit** - CHANGELOG.md must be updated first

### 4. Code Quality
- **Debug Logging** - Use emoji prefixes (🔍, ✅, ❌, ⚠️)
- **Global DEBUG Flag** - Control debug output
- **Error Handling** - Proper try-except with specific exceptions

### 5. Infrastructure
- **Port Management** - Ports within assigned ranges
- **IP Address Conventions** - Use environment variables
- **Docker/Compose Validation** - Validate config syntax

## Auto-Fix Capabilities

The validator can automatically fix common violations:

### Commit Messages
```python
# Invalid format
"update files"

# Auto-fixed to
"chore: update files"
```

### Changelog Entries
```python
# Generate changelog entry
entry = validator.generate_changelog_entry(
    "feat(validator): add port validation",
    ["engine/validation/validator.py"]
)
# Output:
# ## [Unreleased] - 2025-01-06
# ### Added
# - add port validation
```

## Compliance Reporting

Generate comprehensive compliance reports:

```python
report = validator.generate_compliance_report(
    changed_files=["engine/operations/test.py", "test.py"],
    commit_message="update stuff",
    file_contents={
        "config.py": "PORT = 5000"  # Invalid port
    }
)

print(report.get_summary())
# Output: ❌ NON-COMPLIANT - 2/5 passed, 3 failed, 0 warnings

for result in report.results:
    if not result.valid:
        print(f"❌ {result.rule_name}: {result.message}")
        for suggestion in result.suggestions:
            print(f"   💡 {suggestion}")
```

## Best Practices

1. **Start with warnings** - Set `block_on_errors: false` initially
2. **Educate team** - Use `include_rationale: true` to explain rules
3. **Gradual enforcement** - Enable `gradual_enforcement` for training period
4. **Track violations** - Use `track_violations: true` to identify problem areas
5. **Custom rules** - Add project-specific rules to copilot-instructions.md
6. **Test coverage** - Aim for 80%+ coverage on new code

## Troubleshooting

### Validation not working
- Check `.github/copilot-instructions.md` exists
- Verify YAML config is valid
- Ensure validator is initialized in components

### Too many false positives
- Adjust exemptions in `instruction_rules.yaml`
- Use `safe_mode: true` for manual control
- Fine-tune rules in copilot-instructions.md

### Auto-fix not working
- Enable in config: `auto_fix.enabled: true`
- Check specific auto-fix settings
- Verify rule is marked as `auto_fixable`

## Examples

See `test_integration_validator.py` for complete working examples.

## Support

- **Documentation**: This file and inline docstrings
- **Tests**: `tests/test_instruction_validator.py`
- **Integration**: `test_integration_validator.py`
- **Config**: `config/instruction_rules.yaml`
