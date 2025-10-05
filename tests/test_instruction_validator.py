"""
Tests for Instruction Validator

Tests validation of operations against parsed rules.
"""

import pytest
from pathlib import Path
from datetime import datetime
from agents.instruction_validator import InstructionValidator, Violation, ComplianceReport


@pytest.fixture
def sample_instructions(tmp_path):
    """Create sample instructions file."""
    content = """
# Copilot Instructions

## Root Directory Rule
Files should be in subdirectories, not root (except README/CHANGELOG).

## Git Commit Standards
- Conventional commit format: type(scope): description
- Update CHANGELOG.md for every change
- File-specific commits

## Language Convention
All documentation must be in English.

## Port Management
Services must use ports 7000-7999.

## External Projects
Never commit inside external-code directories.
"""
    
    instructions_file = tmp_path / ".github" / "copilot-instructions.md"
    instructions_file.parent.mkdir(parents=True)
    instructions_file.write_text(content)
    return instructions_file


@pytest.fixture
def validator(sample_instructions):
    """Create InstructionValidator instance."""
    return InstructionValidator(sample_instructions)


class TestInstructionValidator:
    """Test InstructionValidator class."""
    
    def test_validator_initialization(self, validator):
        """Test validator initializes correctly."""
        assert validator.parser is not None
        assert validator.rules is not None
        assert isinstance(validator.rules, dict)
    
    def test_validate_file_location_root_file(self, validator):
        """Test validation fails for root Python file."""
        is_valid, violation = validator.validate_file_location("test.py")
        
        assert is_valid is False
        assert violation is not None
        assert violation.rule_name == "root_directory_rule"
        assert violation.severity == "error"
        assert violation.suggestion is not None
    
    def test_validate_file_location_subdirectory(self, validator):
        """Test validation passes for file in subdirectory."""
        is_valid, violation = validator.validate_file_location("agents/test.py")
        
        assert is_valid is True
        assert violation is None
    
    def test_validate_file_location_readme_allowed(self, validator):
        """Test README.md is allowed in root."""
        is_valid, violation = validator.validate_file_location("README.md")
        
        assert is_valid is True
        assert violation is None
    
    def test_validate_file_location_changelog_allowed(self, validator):
        """Test CHANGELOG.md is allowed in root."""
        is_valid, violation = validator.validate_file_location("CHANGELOG.md")
        
        assert is_valid is True
        assert violation is None
    
    def test_validate_file_location_external_code(self, validator):
        """Test validation fails for external-code directory."""
        is_valid, violation = validator.validate_file_location("external-code/test.py")
        
        assert is_valid is False
        assert violation is not None
        assert violation.rule_name == "external_code_protection"
        assert "external-code" in violation.message.lower()
    
    def test_validate_commit_message_valid(self, validator):
        """Test validation passes for valid commit message."""
        message = "feat: Add new validation feature"
        is_valid, violation = validator.validate_commit_message(message)
        
        assert is_valid is True
        assert violation is None
    
    def test_validate_commit_message_invalid_format(self, validator):
        """Test validation fails for invalid format."""
        message = "Added some stuff"
        is_valid, violation = validator.validate_commit_message(message)
        
        assert is_valid is False
        assert violation is not None
        assert violation.rule_name == "conventional_commits"
        assert violation.suggestion is not None
    
    def test_validate_commit_message_too_short(self, validator):
        """Test validation fails for too short message."""
        message = "fix: bug"
        is_valid, violation = validator.validate_commit_message(message)
        
        # Should fail conventional commits pattern (requires 10+ chars after type)
        assert is_valid is False
    
    def test_validate_commit_message_types(self, validator):
        """Test various commit types are valid."""
        valid_types = ["feat", "fix", "docs", "style", "refactor", "test", "chore"]
        
        for commit_type in valid_types:
            message = f"{commit_type}: This is a valid commit message with details"
            is_valid, _ = validator.validate_commit_message(message)
            assert is_valid is True, f"{commit_type} should be valid"
    
    def test_validate_changelog_updated_with_changelog(self, validator):
        """Test validation passes when CHANGELOG.md is in changed files."""
        changed_files = ["agents/test.py", "CHANGELOG.md"]
        is_valid, violation = validator.validate_changelog_updated(changed_files)
        
        assert is_valid is True
        assert violation is None
    
    def test_validate_changelog_updated_without_changelog(self, validator):
        """Test validation fails when CHANGELOG.md not updated."""
        changed_files = ["agents/test.py", "config/test.yaml"]
        is_valid, violation = validator.validate_changelog_updated(changed_files)
        
        assert is_valid is False
        assert violation is not None
        assert violation.rule_name == "changelog_required"
        assert "CHANGELOG" in violation.message
    
    def test_validate_changelog_updated_tests_only(self, validator):
        """Test validation passes for test-only changes."""
        changed_files = ["tests/test_feature.py", "tests/test_another.py"]
        is_valid, violation = validator.validate_changelog_updated(changed_files)
        
        # Test-only changes should be exempt
        assert is_valid is True
        assert violation is None
    
    def test_validate_changelog_updated_docs_only(self, validator):
        """Test validation passes for docs-only changes."""
        changed_files = ["docs/guide.md", "docs/api.md"]
        is_valid, violation = validator.validate_changelog_updated(changed_files)
        
        # Docs-only changes should be exempt
        assert is_valid is True
        assert violation is None
    
    def test_validate_port_usage_valid(self, validator):
        """Test validation passes for port in valid range."""
        is_valid, violation = validator.validate_port_usage(7500, "test-service")
        
        assert is_valid is True
        assert violation is None
    
    def test_validate_port_usage_below_range(self, validator):
        """Test validation fails for port below range."""
        is_valid, violation = validator.validate_port_usage(6000, "test-service")
        
        assert is_valid is False
        assert violation is not None
        assert violation.rule_name == "port_range"
        assert "6000" in violation.message
    
    def test_validate_port_usage_above_range(self, validator):
        """Test validation fails for port above range."""
        is_valid, violation = validator.validate_port_usage(8500, "test-service")
        
        assert is_valid is False
        assert violation is not None
    
    def test_validate_documentation_english(self, validator):
        """Test validation passes for English documentation."""
        content = "This is a test document in English language."
        is_valid, violations = validator.validate_documentation(content, "test.md")
        
        assert is_valid is True
        assert len(violations) == 0
    
    def test_validate_documentation_non_english(self, validator):
        """Test validation fails for non-English documentation."""
        # Dutch content
        content = "Dit is een test document in het Nederlands."
        is_valid, violations = validator.validate_documentation(content, "test.md")
        
        assert is_valid is False
        assert len(violations) > 0
        assert violations[0].rule_name == "english_only"
    
    def test_validate_operation_create_file_valid(self, validator):
        """Test operation validation for valid file creation."""
        report = validator.validate_operation(
            operation="create_file",
            file_path="agents/new_feature.py",
            content="# Python code here"
        )
        
        assert isinstance(report, ComplianceReport)
        assert report.passed is True
        assert len(report.violations) == 0
    
    def test_validate_operation_create_file_invalid(self, validator):
        """Test operation validation for invalid file creation."""
        report = validator.validate_operation(
            operation="create_file",
            file_path="bad_file.py",  # Root file
            content="# Code"
        )
        
        assert isinstance(report, ComplianceReport)
        assert report.passed is False
        assert len(report.violations) > 0
    
    def test_validate_operation_commit_valid(self, validator):
        """Test operation validation for valid commit."""
        report = validator.validate_operation(
            operation="commit",
            message="feat: Add awesome new feature with lots of details",
            changed_files=["agents/feature.py", "CHANGELOG.md"]
        )
        
        assert report.passed is True
        assert len(report.violations) == 0
    
    def test_validate_operation_commit_invalid_message(self, validator):
        """Test operation validation for invalid commit message."""
        report = validator.validate_operation(
            operation="commit",
            message="Added stuff",  # Invalid format
            changed_files=["agents/feature.py", "CHANGELOG.md"]
        )
        
        assert report.passed is False
        assert len(report.violations) > 0
    
    def test_validate_operation_commit_no_changelog(self, validator):
        """Test operation validation for commit without changelog."""
        report = validator.validate_operation(
            operation="commit",
            message="feat: Add awesome feature with details",
            changed_files=["agents/feature.py"]  # No CHANGELOG.md
        )
        
        assert report.passed is False
        assert len(report.violations) > 0
    
    def test_validate_operation_configure_port_valid(self, validator):
        """Test port configuration validation."""
        report = validator.validate_operation(
            operation="configure_port",
            port=7500,
            service_name="test-service"
        )
        
        assert report.passed is True
        assert len(report.violations) == 0
    
    def test_validate_operation_configure_port_invalid(self, validator):
        """Test invalid port configuration."""
        report = validator.validate_operation(
            operation="configure_port",
            port=9000,  # Outside range
            service_name="test-service"
        )
        
        assert report.passed is False
        assert len(report.violations) > 0
    
    def test_suggest_commit_format_feat(self, validator):
        """Test commit format suggestion for feature."""
        suggestion = validator._suggest_commit_format("added new feature")
        
        assert "feat:" in suggestion.lower()
    
    def test_suggest_commit_format_fix(self, validator):
        """Test commit format suggestion for fix."""
        suggestion = validator._suggest_commit_format("fixed a bug")
        
        assert "fix:" in suggestion.lower()
    
    def test_suggest_commit_format_docs(self, validator):
        """Test commit format suggestion for docs."""
        suggestion = validator._suggest_commit_format("updated readme")
        
        assert "docs:" in suggestion.lower()
    
    def test_auto_fix_conventional_commits(self, validator):
        """Test auto-fix for commit messages."""
        violation = Violation(
            rule_name="conventional_commits",
            severity="error",
            message="Invalid format",
            auto_fixable=True
        )
        
        fixed = validator.auto_fix_violation(violation, message="added feature")
        
        assert fixed is not None
        assert "feat:" in fixed.lower()
    
    def test_auto_fix_changelog_entry(self, validator):
        """Test auto-fix for changelog entry generation."""
        violation = Violation(
            rule_name="changelog_required",
            severity="error",
            message="No changelog",
            auto_fixable=True
        )
        
        fixed = validator.auto_fix_violation(
            violation,
            changed_files=["agents/feature.py"],
            message="feat: Add feature"
        )
        
        assert fixed is not None
        assert "Changed" in fixed
        assert "feat: Add feature" in fixed
    
    def test_generate_compliance_report(self, validator):
        """Test compliance report generation."""
        report = validator.generate_compliance_report(
            changed_files=["agents/feature.py", "CHANGELOG.md"],
            commit_message="feat: Add awesome feature"
        )
        
        assert isinstance(report, str)
        assert "Compliance Report" in report
        assert "Files Changed: 2" in report
    
    def test_generate_compliance_report_with_violations(self, validator):
        """Test compliance report with violations."""
        report = validator.generate_compliance_report(
            changed_files=["bad_file.py"],  # Root file
            commit_message="bad message"  # Invalid format
        )
        
        assert "FAILED" in report
        assert "bad_file.py" in report


class TestViolation:
    """Test Violation dataclass."""
    
    def test_violation_creation(self):
        """Test creating Violation instance."""
        violation = Violation(
            rule_name="test_rule",
            severity="error",
            message="Test violation",
            file_path="test.py",
            line_number=42,
            suggestion="Fix it",
            auto_fixable=True
        )
        
        assert violation.rule_name == "test_rule"
        assert violation.severity == "error"
        assert violation.message == "Test violation"
        assert violation.file_path == "test.py"
        assert violation.line_number == 42
        assert violation.suggestion == "Fix it"
        assert violation.auto_fixable is True
    
    def test_violation_defaults(self):
        """Test Violation default values."""
        violation = Violation(
            rule_name="test_rule",
            severity="warning",
            message="Test"
        )
        
        assert violation.file_path is None
        assert violation.line_number is None
        assert violation.suggestion is None
        assert violation.auto_fixable is False


class TestComplianceReport:
    """Test ComplianceReport dataclass."""
    
    def test_report_creation(self):
        """Test creating ComplianceReport."""
        violations = [
            Violation("rule1", "error", "Error 1"),
            Violation("rule2", "error", "Error 2")
        ]
        warnings = [
            Violation("rule3", "warning", "Warning 1")
        ]
        
        report = ComplianceReport(
            timestamp=datetime.now(),
            operation="test",
            total_checks=10,
            violations=violations,
            warnings=warnings,
            passed=False
        )
        
        assert report.operation == "test"
        assert report.total_checks == 10
        assert len(report.violations) == 2
        assert len(report.warnings) == 1
        assert report.passed is False
    
    def test_report_str_failed(self):
        """Test string representation of failed report."""
        violations = [Violation("rule1", "error", "Error", suggestion="Fix it")]
        
        report = ComplianceReport(
            timestamp=datetime.now(),
            operation="test",
            total_checks=5,
            violations=violations,
            warnings=[],
            passed=False
        )
        
        report_str = str(report)
        
        assert "Compliance Report" in report_str
        assert "FAILED" in report_str
        assert "Violations: 1" in report_str
        assert "Error" in report_str
        assert "Fix it" in report_str
    
    def test_report_str_passed(self):
        """Test string representation of passed report."""
        report = ComplianceReport(
            timestamp=datetime.now(),
            operation="test",
            total_checks=5,
            violations=[],
            warnings=[],
            passed=True
        )
        
        report_str = str(report)
        
        assert "Compliance Report" in report_str
        assert "PASSED" in report_str
        assert "Violations: 0" in report_str
