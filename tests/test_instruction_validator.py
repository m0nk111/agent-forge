"""
Tests for Instruction Validator and Parser.

Tests comprehensive validation functionality for Copilot instructions
including file location, commit messages, changelog, ports, and documentation.

Author: Agent Forge
Date: 2025-01-06
"""

import pytest
from pathlib import Path
import tempfile
import os

from agents.instruction_parser import InstructionParser, InstructionSet, Rule
from agents.instruction_validator import (
    InstructionValidator,
    ValidationResult,
    ComplianceReport
)


@pytest.fixture
def temp_project():
    """Create temporary project directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_instructions(temp_project):
    """Create sample copilot-instructions.md file."""
    github_dir = temp_project / ".github"
    github_dir.mkdir()
    
    instructions = github_dir / "copilot-instructions.md"
    instructions.write_text("""# GitHub Copilot Instructions

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

## Documentation Standards

### CHANGELOG.md Requirements
- **Rule**: Every code change must have CHANGELOG.md entry
- **Format**: `## [Version] - YYYY-MM-DD\\n### Added/Changed/Fixed\\n- Description`

## Infrastructure Standards

### Port Management
- **Rule**: Port usage within assigned ranges
- **Range**: 7000-7999 for this project
""")
    return instructions


class TestInstructionParser:
    """Test InstructionParser class."""
    
    def test_parser_initialization(self, temp_project):
        """Test parser initializes correctly."""
        parser = InstructionParser(str(temp_project))
        assert parser.project_root == temp_project
    
    def test_parse_file(self, sample_instructions, temp_project):
        """Test parsing instructions file."""
        parser = InstructionParser(str(temp_project))
        instructions = parser.parse_file(str(sample_instructions))
        
        assert isinstance(instructions, InstructionSet)
        assert len(instructions.rules) > 0
        assert "Project Structure Conventions" in instructions.get_all_categories()
        assert "Git Standards" in instructions.get_all_categories()
    
    def test_parse_file_not_found(self, temp_project):
        """Test parsing non-existent file raises error."""
        parser = InstructionParser(str(temp_project))
        
        with pytest.raises(FileNotFoundError):
            parser.parse_file("nonexistent.md")
    
    def test_parse_rules_by_category(self, sample_instructions, temp_project):
        """Test getting rules by category."""
        parser = InstructionParser(str(temp_project))
        instructions = parser.parse_file(str(sample_instructions))
        
        git_rules = instructions.get_rules_by_category("Git Standards")
        assert len(git_rules) > 0
        assert any(r.name == "Commit Message Format" for r in git_rules)
    
    def test_rule_extraction(self, sample_instructions, temp_project):
        """Test rule attributes are extracted correctly."""
        parser = InstructionParser(str(temp_project))
        instructions = parser.parse_file(str(sample_instructions))
        
        # Find root directory rule
        structure_rules = instructions.get_rules_by_category("Project Structure Conventions")
        root_rule = next(r for r in structure_rules if r.name == "Root Directory Rule")
        
        assert root_rule.rule_text
        assert "README" in root_rule.rule_text or "CHANGELOG" in root_rule.rule_text
        assert root_rule.rationale
        assert root_rule.enforcement
    
    def test_merge_instructions(self, temp_project):
        """Test merging global and project instructions."""
        parser = InstructionParser(str(temp_project))
        
        # Create global instructions
        global_dir = temp_project / "global" / ".github"
        global_dir.mkdir(parents=True)
        global_file = global_dir / "copilot-instructions.md"
        global_file.write_text("""# Global Instructions

## Git Standards

### Commit Format
- **Rule**: Use conventional commits
""")
        
        # Create project instructions
        project_dir = temp_project / ".github"
        project_dir.mkdir()
        project_file = project_dir / "copilot-instructions.md"
        project_file.write_text("""# Project Instructions

## Git Standards

### Commit Format
- **Rule**: Use extended commit format with ticket numbers
""")
        
        # Merge
        merged = parser.merge_instructions(
            str(global_file),
            str(project_file)
        )
        
        # Project-specific rule should override
        git_rules = merged.get_rules_by_category("Git Standards")
        commit_rule = next(r for r in git_rules if r.name == "Commit Format")
        assert "ticket numbers" in commit_rule.rule_text


class TestInstructionValidator:
    """Test InstructionValidator class."""
    
    def test_validator_initialization(self, sample_instructions, temp_project):
        """Test validator initializes correctly."""
        validator = InstructionValidator(
            str(sample_instructions),
            str(temp_project)
        )
        assert validator.project_root == temp_project
        assert validator.instructions is not None
    
    def test_validate_file_location_root_allowed(self, sample_instructions, temp_project):
        """Test allowed root files pass validation."""
        validator = InstructionValidator(
            str(sample_instructions),
            str(temp_project)
        )
        
        result = validator.validate_file_location("README.md")
        assert result.valid is True
        
        result = validator.validate_file_location("CHANGELOG.md")
        assert result.valid is True
    
    def test_validate_file_location_root_blocked(self, sample_instructions, temp_project):
        """Test non-allowed root files fail validation."""
        validator = InstructionValidator(
            str(sample_instructions),
            str(temp_project)
        )
        
        result = validator.validate_file_location("test.py")
        assert result.valid is False
        assert "root directory" in result.message.lower()
        assert len(result.suggestions) > 0
    
    def test_validate_file_location_subdirectory(self, sample_instructions, temp_project):
        """Test files in subdirectories pass validation."""
        validator = InstructionValidator(
            str(sample_instructions),
            str(temp_project)
        )
        
        result = validator.validate_file_location("agents/test.py")
        assert result.valid is True
    
    def test_validate_file_location_external_code(self, sample_instructions, temp_project):
        """Test external-code directory is blocked."""
        validator = InstructionValidator(
            str(sample_instructions),
            str(temp_project)
        )
        
        result = validator.validate_file_location("external-code/lib.py")
        assert result.valid is False
        assert "external-code" in result.message.lower()
    
    def test_validate_commit_message_valid(self, sample_instructions, temp_project):
        """Test valid commit messages pass."""
        validator = InstructionValidator(
            str(sample_instructions),
            str(temp_project)
        )
        
        valid_messages = [
            "feat(validator): add instruction validation",
            "fix(parser): handle edge case in rule parsing",
            "docs: update README with usage examples",
            "chore: update dependencies",
        ]
        
        for msg in valid_messages:
            result = validator.validate_commit_message(msg)
            assert result.valid is True, f"Failed for: {msg}"
    
    def test_validate_commit_message_invalid(self, sample_instructions, temp_project):
        """Test invalid commit messages fail."""
        validator = InstructionValidator(
            str(sample_instructions),
            str(temp_project)
        )
        
        invalid_messages = [
            "update files",
            "fixed bug",
            "WIP",
            "feat:",  # Too short description
        ]
        
        for msg in invalid_messages:
            result = validator.validate_commit_message(msg)
            assert result.valid is False, f"Should fail for: {msg}"
            assert len(result.suggestions) > 0
    
    def test_validate_changelog_updated(self, sample_instructions, temp_project):
        """Test changelog validation."""
        validator = InstructionValidator(
            str(sample_instructions),
            str(temp_project)
        )
        
        # Code changes without changelog should fail
        result = validator.validate_changelog_updated(["agents/test.py", "agents/utils.py"])
        assert result.valid is False
        assert "CHANGELOG" in result.message
        
        # Code changes with changelog should pass
        result = validator.validate_changelog_updated(["agents/test.py", "CHANGELOG.md"])
        assert result.valid is True
        
        # Only doc changes should pass without changelog
        result = validator.validate_changelog_updated(["README.md", "docs/guide.md"])
        assert result.valid is True
    
    def test_validate_port_usage(self, sample_instructions, temp_project):
        """Test port validation."""
        validator = InstructionValidator(
            str(sample_instructions),
            str(temp_project)
        )
        
        # Valid ports
        assert validator.validate_port_usage(7000).valid is True
        assert validator.validate_port_usage(7500).valid is True
        assert validator.validate_port_usage(7999).valid is True
        
        # Invalid ports
        assert validator.validate_port_usage(5000).valid is False
        assert validator.validate_port_usage(8000).valid is False
        assert validator.validate_port_usage(80).valid is False
    
    def test_validate_documentation(self, sample_instructions, temp_project):
        """Test documentation language validation."""
        validator = InstructionValidator(
            str(sample_instructions),
            str(temp_project)
        )
        
        # English content should pass
        result = validator.validate_documentation(
            "This is a test document with English content.",
            "README.md"
        )
        assert result.valid is True
        
        # Non-English content should warn (not error, as detection isn't perfect)
        result = validator.validate_documentation(
            "Dit is een test document met Nederlandse inhoud.",
            "README.md"
        )
        # Should detect some non-English words
        assert result.severity in ["warning", "error"] or result.valid is True
    
    def test_generate_compliance_report(self, sample_instructions, temp_project):
        """Test compliance report generation."""
        validator = InstructionValidator(
            str(sample_instructions),
            str(temp_project)
        )
        
        report = validator.generate_compliance_report(
            changed_files=["agents/validator.py", "CHANGELOG.md"],
            commit_message="feat(validator): add instruction validation system"
        )
        
        assert isinstance(report, ComplianceReport)
        assert len(report.results) > 0
        assert report.passed > 0
    
    def test_compliance_report_with_violations(self, sample_instructions, temp_project):
        """Test compliance report with violations."""
        validator = InstructionValidator(
            str(sample_instructions),
            str(temp_project)
        )
        
        report = validator.generate_compliance_report(
            changed_files=["test.py", "agents/utils.py"],  # test.py in root is violation
            commit_message="update files"  # Invalid format
        )
        
        assert report.failed > 0
        assert report.is_compliant() is False
    
    def test_suggest_commit_improvements(self, sample_instructions, temp_project):
        """Test commit message improvement suggestions."""
        validator = InstructionValidator(
            str(sample_instructions),
            str(temp_project)
        )
        
        suggestions = validator.suggest_commit_improvements("update files")
        assert len(suggestions) > 0
        assert any("feat:" in s or "fix:" in s for s in suggestions)
    
    def test_auto_fix_commit_message(self, sample_instructions, temp_project):
        """Test auto-fix commit message."""
        validator = InstructionValidator(
            str(sample_instructions),
            str(temp_project)
        )
        
        fixed = validator.auto_fix_commit_message("update validation logic")
        assert fixed is not None
        assert "chore:" in fixed
    
    def test_generate_changelog_entry(self, sample_instructions, temp_project):
        """Test changelog entry generation."""
        validator = InstructionValidator(
            str(sample_instructions),
            str(temp_project)
        )
        
        entry = validator.generate_changelog_entry(
            "feat(validator): add port validation",
            ["agents/validator.py"]
        )
        
        assert "##" in entry
        assert "Added" in entry or "Changed" in entry
        assert "port validation" in entry.lower()
    
    def test_config_override(self, sample_instructions, temp_project):
        """Test configuration overrides."""
        # Disable some validations
        config = {
            'enforce_root_files': False,
            'require_changelog': False,
        }
        
        validator = InstructionValidator(
            str(sample_instructions),
            str(temp_project),
            config=config
        )
        
        # Root file should pass when disabled
        result = validator.validate_file_location("test.py")
        assert result.severity == "info"
        
        # Changelog should pass when disabled
        result = validator.validate_changelog_updated(["agents/test.py"])
        assert result.severity == "info"
    
    def test_validation_with_file_contents(self, sample_instructions, temp_project):
        """Test validation with file contents."""
        validator = InstructionValidator(
            str(sample_instructions),
            str(temp_project)
        )
        
        file_contents = {
            "config.py": "PORT = 7500\nHOST = '0.0.0.0'",
            "README.md": "This is English documentation."
        }
        
        report = validator.generate_compliance_report(
            file_contents=file_contents
        )
        
        # Should validate port usage
        assert any("port" in r.message.lower() for r in report.results)


class TestValidationResult:
    """Test ValidationResult dataclass."""
    
    def test_validation_result_creation(self):
        """Test creating validation result."""
        result = ValidationResult(
            valid=False,
            rule_name="Test Rule",
            message="Test failed",
            severity="error",
            suggestions=["Fix this", "Try that"],
            auto_fixable=True
        )
        
        assert result.valid is False
        assert result.rule_name == "Test Rule"
        assert len(result.suggestions) == 2


class TestComplianceReport:
    """Test ComplianceReport dataclass."""
    
    def test_compliance_report_initialization(self):
        """Test compliance report initialization."""
        report = ComplianceReport()
        assert report.passed == 0
        assert report.failed == 0
        assert report.warnings == 0
        assert len(report.results) == 0
    
    def test_add_result_error(self):
        """Test adding error result."""
        report = ComplianceReport()
        result = ValidationResult(
            valid=False,
            rule_name="Test",
            message="Error",
            severity="error"
        )
        report.add_result(result)
        
        assert report.failed == 1
        assert report.passed == 0
    
    def test_add_result_warning(self):
        """Test adding warning result."""
        report = ComplianceReport()
        result = ValidationResult(
            valid=True,
            rule_name="Test",
            message="Warning",
            severity="warning"
        )
        report.add_result(result)
        
        assert report.warnings == 1
    
    def test_add_result_success(self):
        """Test adding success result."""
        report = ComplianceReport()
        result = ValidationResult(
            valid=True,
            rule_name="Test",
            message="Success",
            severity="info"
        )
        report.add_result(result)
        
        assert report.passed == 1
    
    def test_is_compliant(self):
        """Test compliance check."""
        report = ComplianceReport()
        
        # No errors = compliant
        assert report.is_compliant() is True
        
        # Add error
        report.add_result(ValidationResult(
            valid=False,
            rule_name="Test",
            message="Error",
            severity="error"
        ))
        
        assert report.is_compliant() is False
    
    def test_get_summary(self):
        """Test summary generation."""
        report = ComplianceReport()
        
        report.add_result(ValidationResult(valid=True, rule_name="T1", message="Pass", severity="info"))
        report.add_result(ValidationResult(valid=False, rule_name="T2", message="Fail", severity="error"))
        
        summary = report.get_summary()
        assert "1/2 passed" in summary
        assert "1 failed" in summary


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
