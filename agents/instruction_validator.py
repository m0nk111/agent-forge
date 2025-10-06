"""
Instruction Validator for Copilot Instructions.

Validates code changes against rules defined in copilot-instructions.md.
Provides validation for file locations, commit messages, changelog updates,
port usage, documentation language, and other project standards.

Author: Agent Forge
Date: 2025-01-06
"""

import re
import os
from pathlib import Path
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field

from agents.instruction_parser import InstructionParser, InstructionSet, Rule


@dataclass
class ValidationResult:
    """Result of a validation check."""
    valid: bool
    rule_name: str
    message: str
    severity: str = "error"  # error, warning, info
    suggestions: List[str] = field(default_factory=list)
    auto_fixable: bool = False


@dataclass
class ComplianceReport:
    """Comprehensive compliance report for all validations."""
    passed: int = 0
    failed: int = 0
    warnings: int = 0
    results: List[ValidationResult] = field(default_factory=list)
    
    def add_result(self, result: ValidationResult):
        """Add a validation result."""
        self.results.append(result)
        if result.severity == "error" and not result.valid:
            self.failed += 1
        elif result.severity == "warning":
            self.warnings += 1
        elif result.valid:
            self.passed += 1
    
    def is_compliant(self) -> bool:
        """Check if all validations passed (no errors)."""
        return self.failed == 0
    
    def get_summary(self) -> str:
        """Get human-readable summary."""
        total = len(self.results)
        status = "✅ COMPLIANT" if self.is_compliant() else "❌ NON-COMPLIANT"
        return f"{status} - {self.passed}/{total} passed, {self.failed} failed, {self.warnings} warnings"


class InstructionValidator:
    """
    Validate code changes against Copilot instructions.
    
    Provides comprehensive validation across multiple categories:
    - Project structure (file locations, root directory rules)
    - Documentation (language, changelog requirements)
    - Git standards (commit message format, file-specific commits)
    - Code quality (debug logging, error handling)
    - Infrastructure (port ranges, IP conventions)
    """
    
    def __init__(
        self,
        instructions_file: Optional[str] = None,
        project_root: Optional[str] = None,
        config: Optional[Dict] = None
    ):
        """
        Initialize instruction validator.
        
        Args:
            instructions_file: Path to copilot-instructions.md (optional)
            project_root: Project root directory (optional)
            config: Validation configuration dict (optional)
        """
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.config = config or self._default_config()
        
        # Parse instructions
        self.parser = InstructionParser(str(self.project_root))
        
        if instructions_file:
            self.instructions = self.parser.parse_file(instructions_file)
        else:
            # Auto-detect and merge global + project instructions
            global_path, project_path = self.parser.get_default_instruction_paths()
            self.instructions = self.parser.merge_instructions(global_path, project_path)
        
        # Root directory allowed files
        self.root_allowed_files = {
            'README.md', 'CHANGELOG.md', 'LICENSE', 'LICENSE.md',
            '.gitignore', '.gitattributes',
            'requirements.txt', 'package.json', 'pyproject.toml',
            'Makefile', 'Dockerfile', 'docker-compose.yml',
            'setup.py', 'setup.cfg', 'MANIFEST.in'
        }
        
        # Root allowed directories
        self.root_allowed_dirs = {'.github', '.vscode', '.git'}
    
    def _default_config(self) -> Dict:
        """Get default validation configuration."""
        return {
            'enforce_root_files': True,
            'require_changelog': True,
            'block_external_commits': True,
            'enforce_port_ranges': True,
            'require_debug_logging': False,  # Optional for now
            'validate_commit_format': True,
            'check_documentation_language': True,
            'port_range': (7000, 7999),  # Default range
            'exemptions': {
                'files': ['.gitignore', '.github/*', '.vscode/*'],
                'directories': ['tests/*', 'external-code/*']
            }
        }
    
    def validate_file_location(self, file_path: str) -> ValidationResult:
        """
        Validate file is in correct location according to project structure rules.
        
        Args:
            file_path: Relative path from project root
            
        Returns:
            ValidationResult indicating if location is valid
        """
        if not self.config.get('enforce_root_files', True):
            return ValidationResult(
                valid=True,
                rule_name="Root Directory Rule",
                message="File location validation disabled",
                severity="info"
            )
        
        path = Path(file_path)
        
        # Check if file is in root directory
        if len(path.parts) == 1:
            # File is in root
            filename = path.name
            
            # Check if allowed
            if filename not in self.root_allowed_files:
                # Check if it matches a pattern (e.g., .*)
                if not filename.startswith('.'):
                    return ValidationResult(
                        valid=False,
                        rule_name="Root Directory Rule",
                        message=f"File '{filename}' should not be in root directory",
                        severity="error",
                        suggestions=[
                            f"Move to appropriate subdirectory (e.g., agents/, config/, docs/)",
                            f"Only README.md, CHANGELOG.md, LICENSE, and configuration files allowed in root"
                        ],
                        auto_fixable=False
                    )
        
        # Check for external-code directory
        if 'external-code' in path.parts:
            return ValidationResult(
                valid=False,
                rule_name="External Code Policy",
                message=f"Cannot modify files in external-code directory: {file_path}",
                severity="error",
                suggestions=["Do not commit changes to external-code/ directories"],
                auto_fixable=False
            )
        
        return ValidationResult(
            valid=True,
            rule_name="Root Directory Rule",
            message=f"File location valid: {file_path}",
            severity="info"
        )
    
    def validate_commit_message(self, message: str) -> ValidationResult:
        """
        Validate commit message format against Git standards.
        
        Args:
            message: Commit message to validate
            
        Returns:
            ValidationResult indicating if format is valid
        """
        if not self.config.get('validate_commit_format', True):
            return ValidationResult(
                valid=True,
                rule_name="Commit Message Format",
                message="Commit validation disabled",
                severity="info"
            )
        
        # Conventional commit pattern: type(scope): description
        # Relaxed to .{3,} to allow short but valid commits like "fix: tests"
        pattern = r'^(feat|fix|docs|style|refactor|test|chore)(\([a-zA-Z0-9_-]+\))?: .{3,}$'
        
        # Extract first line
        first_line = message.split('\n')[0].strip()
        
        if not re.match(pattern, first_line):
            suggestions = [
                "Use conventional commit format: type(scope): description",
                "Valid types: feat, fix, docs, style, refactor, test, chore",
                "Example: feat(validator): add instruction parser",
                "Description should be at least 10 characters"
            ]
            
            # Provide specific suggestions based on error
            if ':' not in first_line:
                suggestions.insert(0, "Missing colon ':' after type/scope")
            elif not any(first_line.startswith(t) for t in ['feat', 'fix', 'docs', 'style', 'refactor', 'test', 'chore']):
                suggestions.insert(0, "Invalid commit type (must be feat, fix, docs, style, refactor, test, or chore)")
            
            return ValidationResult(
                valid=False,
                rule_name="Commit Message Format",
                message=f"Invalid commit message format: {first_line[:50]}...",
                severity="error",
                suggestions=suggestions,
                auto_fixable=True
            )
        
        return ValidationResult(
            valid=True,
            rule_name="Commit Message Format",
            message="Commit message format valid",
            severity="info"
        )
    
    def validate_changelog_updated(self, changed_files: List[str]) -> ValidationResult:
        """
        Check if CHANGELOG.md was updated for code changes.
        
        Args:
            changed_files: List of files that were changed
            
        Returns:
            ValidationResult indicating if changelog was updated
        """
        if not self.config.get('require_changelog', True):
            return ValidationResult(
                valid=True,
                rule_name="CHANGELOG.md Requirements",
                message="Changelog validation disabled",
                severity="info"
            )
        
        # Check if CHANGELOG.md is in changed files
        changelog_updated = any('CHANGELOG.md' in f for f in changed_files)
        
        # Check if any code files were changed (not just docs/tests)
        code_files_changed = any(
            f.endswith(('.py', '.js', '.ts', '.java', '.go', '.rs'))
            for f in changed_files
            if 'test' not in f.lower() and 'CHANGELOG' not in f
        )
        
        if code_files_changed and not changelog_updated:
            return ValidationResult(
                valid=False,
                rule_name="CHANGELOG.md Requirements",
                message="CHANGELOG.md must be updated for code changes",
                severity="error",
                suggestions=[
                    "Add entry to CHANGELOG.md describing your changes",
                    "Format: ## [Version] - YYYY-MM-DD\\n### Added/Changed/Fixed\\n- Description"
                ],
                auto_fixable=True
            )
        
        return ValidationResult(
            valid=True,
            rule_name="CHANGELOG.md Requirements",
            message="Changelog requirements satisfied",
            severity="info"
        )
    
    def validate_port_usage(self, port: int) -> ValidationResult:
        """
        Validate port number is within assigned range.
        
        Args:
            port: Port number to validate
            
        Returns:
            ValidationResult indicating if port is valid
        """
        if not self.config.get('enforce_port_ranges', True):
            return ValidationResult(
                valid=True,
                rule_name="Port Management",
                message="Port validation disabled",
                severity="info"
            )
        
        port_min, port_max = self.config.get('port_range', (7000, 7999))
        
        if not (port_min <= port <= port_max):
            return ValidationResult(
                valid=False,
                rule_name="Port Management",
                message=f"Port {port} outside assigned range {port_min}-{port_max}",
                severity="error",
                suggestions=[
                    f"Use ports within assigned range: {port_min}-{port_max}",
                    "Avoid port conflicts with other services"
                ],
                auto_fixable=False
            )
        
        return ValidationResult(
            valid=True,
            rule_name="Port Management",
            message=f"Port {port} within valid range",
            severity="info"
        )
    
    def validate_documentation(self, content: str, file_path: str) -> ValidationResult:
        """
        Validate documentation content (language, format).
        
        Args:
            content: File content to validate
            file_path: Path to file being validated
            
        Returns:
            ValidationResult indicating if documentation is valid
        """
        if not self.config.get('check_documentation_language', True):
            return ValidationResult(
                valid=True,
                rule_name="Language Convention",
                message="Documentation validation disabled",
                severity="info"
            )
        
        # Simple heuristic: check for common non-English words
        # This is a basic implementation; real implementation might use language detection
        non_english_patterns = [
            r'\b(het|de|een)\b',  # Dutch
            r'\b(le|la|les|un|une)\b',  # French
            r'\b(der|die|das|ein|eine)\b',  # German
            r'\b(el|la|los|las|un|una)\b',  # Spanish
        ]
        
        issues_found = []
        for pattern in non_english_patterns:
            matches = re.findall(pattern, content.lower(), re.IGNORECASE)
            if matches:
                issues_found.extend(matches[:3])  # Limit to first 3
        
        if issues_found:
            return ValidationResult(
                valid=False,
                rule_name="Language Convention",
                message=f"Non-English text detected in {file_path}",
                severity="warning",  # Warning not error, as detection is not perfect
                suggestions=[
                    "All documentation should be in English",
                    f"Possible non-English words found: {', '.join(set(issues_found))}"
                ],
                auto_fixable=False
            )
        
        return ValidationResult(
            valid=True,
            rule_name="Language Convention",
            message="Documentation language valid",
            severity="info"
        )
    
    def generate_compliance_report(
        self,
        changed_files: Optional[List[str]] = None,
        commit_message: Optional[str] = None,
        file_contents: Optional[Dict[str, str]] = None
    ) -> ComplianceReport:
        """
        Generate comprehensive compliance report for changes.
        
        Args:
            changed_files: List of files that were changed
            commit_message: Commit message to validate
            file_contents: Dict mapping file paths to their contents
            
        Returns:
            ComplianceReport with all validation results
        """
        report = ComplianceReport()
        
        # Validate commit message
        if commit_message:
            result = self.validate_commit_message(commit_message)
            report.add_result(result)
        
        # Validate file locations
        if changed_files:
            for file_path in changed_files:
                result = self.validate_file_location(file_path)
                report.add_result(result)
            
            # Validate changelog
            result = self.validate_changelog_updated(changed_files)
            report.add_result(result)
        
        # Validate file contents
        if file_contents:
            for file_path, content in file_contents.items():
                # Documentation validation
                if file_path.endswith(('.md', '.txt', '.rst')):
                    result = self.validate_documentation(content, file_path)
                    report.add_result(result)
                
                # Port usage validation
                if file_path.endswith(('.py', '.js', '.yml', '.yaml', '.json')):
                    # Look for port definitions
                    port_pattern = r'\bport[\'"]?\s*[:=]\s*(\d+)'
                    ports = re.findall(port_pattern, content, re.IGNORECASE)
                    for port_str in ports:
                        port = int(port_str)
                        result = self.validate_port_usage(port)
                        report.add_result(result)
        
        return report
    
    def suggest_commit_improvements(self, message: str) -> List[str]:
        """
        Suggest improvements for commit message.
        
        Args:
            message: Original commit message
            
        Returns:
            List of suggested improvements
        """
        suggestions = []
        
        first_line = message.split('\n')[0].strip()
        
        # Try to fix common issues
        if ':' not in first_line:
            # Suggest adding type and scope
            suggestions.append(f"feat: {first_line}")
            suggestions.append(f"fix: {first_line}")
        
        # Suggest making it more descriptive
        if len(first_line) < 10:
            suggestions.append("Make commit message more descriptive (at least 10 characters)")
        
        return suggestions
    
    def auto_fix_commit_message(self, message: str) -> Optional[str]:
        """
        Attempt to auto-fix commit message format.
        
        Args:
            message: Original commit message
            
        Returns:
            Fixed message or None if cannot auto-fix
        """
        first_line = message.split('\n')[0].strip()
        rest = '\n'.join(message.split('\n')[1:])
        
        # If no type prefix, try to infer
        if ':' not in first_line:
            # Default to 'chore' for generic commits
            fixed = f"chore: {first_line}"
            if rest:
                fixed += '\n' + rest
            return fixed
        
        return None
    
    def generate_changelog_entry(
        self,
        commit_message: str,
        changed_files: List[str]
    ) -> str:
        """
        Auto-generate CHANGELOG.md entry.
        
        Args:
            commit_message: Commit message
            changed_files: List of changed files
            
        Returns:
            Suggested changelog entry
        """
        from datetime import datetime
        
        # Parse commit type
        first_line = commit_message.split('\n')[0].strip()
        commit_type = 'Changed'
        
        if first_line.startswith('feat'):
            commit_type = 'Added'
        elif first_line.startswith('fix'):
            commit_type = 'Fixed'
        elif first_line.startswith('docs'):
            commit_type = 'Documentation'
        
        # Extract description
        if ':' in first_line:
            description = first_line.split(':', 1)[1].strip()
        else:
            description = first_line
        
        # Generate entry
        date_str = datetime.now().strftime('%Y-%m-%d')
        entry = f"## [Unreleased] - {date_str}\n"
        entry += f"### {commit_type}\n"
        entry += f"- {description}\n"
        
        return entry


# Example usage
if __name__ == "__main__":
    validator = InstructionValidator()
    
    print("🔍 Instruction Validator Test\n")
    
    # Test file location validation
    print("1. Testing file location validation:")
    result = validator.validate_file_location("test.py")
    print(f"   {result.message}")
    
    # Test commit message validation
    print("\n2. Testing commit message validation:")
    result = validator.validate_commit_message("feat(validator): add instruction validation")
    print(f"   {result.message}")
    
    result = validator.validate_commit_message("update files")
    print(f"   {result.message}")
    if not result.valid:
        print(f"   Suggestions: {result.suggestions[0]}")
    
    # Test changelog validation
    print("\n3. Testing changelog validation:")
    result = validator.validate_changelog_updated(["agents/test.py"])
    print(f"   {result.message}")
    
    # Generate compliance report
    print("\n4. Generating compliance report:")
    report = validator.generate_compliance_report(
        changed_files=["agents/instruction_validator.py", "CHANGELOG.md"],
        commit_message="feat(validator): add instruction validation system"
    )
    print(f"   {report.get_summary()}")
