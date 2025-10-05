"""
Instruction Validator Module

Validates agent operations against parsed Copilot instruction rules.
Provides auto-fix capabilities and compliance reporting.
"""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import logging

from agents.instruction_parser import InstructionParser, Rule

logger = logging.getLogger(__name__)


@dataclass
class Violation:
    """Represents a rule violation."""
    rule_name: str
    severity: str
    message: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    suggestion: Optional[str] = None
    auto_fixable: bool = False


@dataclass
class ComplianceReport:
    """Compliance validation report."""
    timestamp: datetime
    operation: str
    total_checks: int
    violations: List[Violation]
    warnings: List[Violation]
    passed: bool
    
    def __str__(self) -> str:
        """Format report as readable string."""
        lines = [
            f"\n📊 Compliance Report - {self.operation}",
            f"🕐 {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
            f"✅ Checks: {self.total_checks}",
            f"❌ Violations: {len(self.violations)}",
            f"⚠️  Warnings: {len(self.warnings)}",
            f"{'🟢 PASSED' if self.passed else '🔴 FAILED'}",
            ""
        ]
        
        if self.violations:
            lines.append("🔴 Violations:")
            for v in self.violations:
                lines.append(f"  • {v.rule_name}: {v.message}")
                if v.suggestion:
                    lines.append(f"    💡 {v.suggestion}")
                    
        if self.warnings:
            lines.append("\n⚠️  Warnings:")
            for w in self.warnings:
                lines.append(f"  • {w.rule_name}: {w.message}")
                if w.suggestion:
                    lines.append(f"    💡 {w.suggestion}")
                    
        return "\n".join(lines)


class InstructionValidator:
    """
    Validates agent operations against Copilot instruction rules.
    
    Features:
    - File location validation
    - Commit message validation
    - Changelog requirement checking
    - Port/IP convention validation
    - Documentation standards validation
    - Auto-fix capabilities
    - Compliance reporting
    """
    
    def __init__(
        self,
        instructions_file: Path,
        workspace_path: Optional[Path] = None,
        auto_fix: bool = False
    ):
        """
        Initialize validator.
        
        Args:
            instructions_file: Path to copilot-instructions.md
            workspace_path: Workspace root (for workspace-specific rules)
            auto_fix: Enable automatic fixes for fixable violations
        """
        self.instructions_file = instructions_file
        self.workspace_path = workspace_path or instructions_file.parent.parent
        self.auto_fix = auto_fix
        
        # Parse instructions
        self.parser = InstructionParser()
        if workspace_path:
            self.rules = self.parser.parse_workspace(workspace_path)
        else:
            self.rules = self.parser.parse_file(instructions_file)
            
        logger.info(f"✅ Validator initialized with {len(self.parser.get_all_rules())} rules")
    
    def validate_file_location(self, file_path: str) -> Tuple[bool, Optional[Violation]]:
        """
        Validate file placement according to project structure rules.
        
        Args:
            file_path: Path to file being created/edited
            
        Returns:
            (is_valid, violation_or_none)
        """
        rules = self.parser.get_rules_by_category('project_structure')
        
        for rule in rules:
            if rule.name == 'root_directory_rule':
                # Check if file is in root (and not allowed)
                if rule.pattern and re.match(rule.pattern, file_path):
                    # Exception for README, CHANGELOG, LICENSE
                    allowed_root = ['README', 'CHANGELOG', 'LICENSE', '.git', '.github']
                    if not any(allowed in file_path.upper() for allowed in allowed_root):
                        return False, Violation(
                            rule_name=rule.name,
                            severity=rule.severity,
                            message=f"File '{file_path}' should be in subdirectory, not root",
                            file_path=file_path,
                            suggestion="Move file to appropriate subdirectory (e.g., agents/, config/, docs/)",
                            auto_fixable=False
                        )
                        
            elif rule.name == 'external_code_protection':
                # Check if trying to modify external code
                if rule.pattern and re.search(rule.pattern, file_path):
                    return False, Violation(
                        rule_name=rule.name,
                        severity=rule.severity,
                        message=f"Cannot modify external-code directory: {file_path}",
                        file_path=file_path,
                        suggestion="External projects are read-only. Create wrapper/integration in agents/ instead",
                        auto_fixable=False
                    )
        
        return True, None
    
    def validate_commit_message(self, message: str) -> Tuple[bool, Optional[Violation]]:
        """
        Validate commit message format.
        
        Args:
            message: Commit message to validate
            
        Returns:
            (is_valid, violation_or_none)
        """
        rules = self.parser.get_rules_by_category('git_standards')
        
        for rule in rules:
            if rule.name == 'conventional_commits':
                if rule.pattern and not re.match(rule.pattern, message):
                    # Try to suggest fix
                    suggestion = self._suggest_commit_format(message)
                    return False, Violation(
                        rule_name=rule.name,
                        severity=rule.severity,
                        message=f"Commit message doesn't follow conventional format",
                        suggestion=suggestion,
                        auto_fixable=rule.auto_fixable
                    )
                    
            elif rule.name == 'file_specific_commits':
                # Check if message describes specific changes
                if len(message) < 20 or not any(word in message.lower() for word in ['add', 'update', 'fix', 'remove', 'implement']):
                    return False, Violation(
                        rule_name=rule.name,
                        severity=rule.severity,
                        message="Commit message should describe specific file changes",
                        suggestion="Include what files were changed and why",
                        auto_fixable=False
                    )
        
        return True, None
    
    def validate_changelog_updated(
        self,
        changed_files: List[str],
        workspace_path: Optional[Path] = None
    ) -> Tuple[bool, Optional[Violation]]:
        """
        Check if CHANGELOG.md was updated.
        
        Args:
            changed_files: List of files being committed
            workspace_path: Path to workspace root
            
        Returns:
            (is_valid, violation_or_none)
        """
        rules = self.parser.get_rules_by_category('git_standards')
        
        for rule in rules:
            if rule.name == 'changelog_required':
                # Check if CHANGELOG.md is in changed files
                has_changelog = any('CHANGELOG.md' in f for f in changed_files)
                
                # Exclude trivial changes
                only_tests = all('test' in f.lower() for f in changed_files)
                only_docs = all(f.endswith(('.md', '.rst', '.txt')) for f in changed_files)
                
                if not has_changelog and not only_tests and not only_docs:
                    return False, Violation(
                        rule_name=rule.name,
                        severity=rule.severity,
                        message="CHANGELOG.md not updated",
                        suggestion="Add entry to CHANGELOG.md describing your changes",
                        auto_fixable=rule.auto_fixable
                    )
        
        return True, None
    
    def validate_port_usage(self, port: int, service_name: str = "") -> Tuple[bool, Optional[Violation]]:
        """
        Validate port number against conventions.
        
        Args:
            port: Port number to validate
            service_name: Name of service using port
            
        Returns:
            (is_valid, violation_or_none)
        """
        rules = self.parser.get_rules_by_category('infrastructure')
        
        for rule in rules:
            if rule.name == 'port_range':
                # Extract port range from rule description
                match = re.search(r'(\d+)-(\d+)', rule.description)
                if match:
                    start, end = map(int, match.groups())
                    if not (start <= port <= end):
                        return False, Violation(
                            rule_name=rule.name,
                            severity=rule.severity,
                            message=f"Port {port} outside allowed range {start}-{end}",
                            suggestion=f"Use port in range {start}-{end} for {service_name or 'this service'}",
                            auto_fixable=False
                        )
        
        return True, None
    
    def validate_documentation(self, content: str, file_path: str) -> Tuple[bool, List[Violation]]:
        """
        Validate documentation content.
        
        Args:
            content: Documentation content
            file_path: Path to documentation file
            
        Returns:
            (is_valid, list_of_violations)
        """
        violations = []
        rules = self.parser.get_rules_by_category('documentation')
        
        for rule in rules:
            if rule.name == 'english_only':
                # Simple heuristic: check for common non-English words
                non_english_patterns = [
                    r'\b(het|de|een|voor|van|met|dit|dat)\b',  # Dutch
                    r'\b(le|la|les|un|une|pour|avec|dans)\b',  # French
                    r'\b(der|die|das|ein|eine|für|mit|von)\b'  # German
                ]
                
                for pattern in non_english_patterns:
                    if re.search(pattern, content.lower()):
                        violations.append(Violation(
                            rule_name=rule.name,
                            severity=rule.severity,
                            message=f"Documentation may contain non-English text: {file_path}",
                            file_path=file_path,
                            suggestion="All project documentation must be in English",
                            auto_fixable=False
                        ))
                        break
        
        return len(violations) == 0, violations
    
    def validate_operation(
        self,
        operation: str,
        **kwargs
    ) -> ComplianceReport:
        """
        Validate a complete operation against all applicable rules.
        
        Args:
            operation: Type of operation (create_file, edit_file, commit, etc.)
            **kwargs: Operation-specific parameters
            
        Returns:
            ComplianceReport with violations and warnings
        """
        violations = []
        warnings = []
        checks = 0
        
        # File creation/edit validation
        if operation in ['create_file', 'edit_file']:
            file_path = kwargs.get('file_path', '')
            checks += 1
            is_valid, violation = self.validate_file_location(file_path)
            if not is_valid and violation:
                if violation.severity == 'error':
                    violations.append(violation)
                else:
                    warnings.append(violation)
                    
            # Documentation validation
            if file_path.endswith(('.md', '.rst', '.txt')):
                content = kwargs.get('content', '')
                checks += 1
                is_valid, doc_violations = self.validate_documentation(content, file_path)
                for v in doc_violations:
                    if v.severity == 'error':
                        violations.append(v)
                    else:
                        warnings.append(v)
        
        # Commit validation
        elif operation == 'commit':
            message = kwargs.get('message', '')
            changed_files = kwargs.get('changed_files', [])
            
            checks += 1
            is_valid, violation = self.validate_commit_message(message)
            if not is_valid and violation:
                if violation.severity == 'error':
                    violations.append(violation)
                else:
                    warnings.append(violation)
            
            checks += 1
            is_valid, violation = self.validate_changelog_updated(changed_files)
            if not is_valid and violation:
                if violation.severity == 'error':
                    violations.append(violation)
                else:
                    warnings.append(violation)
        
        # Port validation
        elif operation == 'configure_port':
            port = kwargs.get('port', 0)
            service_name = kwargs.get('service_name', '')
            
            checks += 1
            is_valid, violation = self.validate_port_usage(port, service_name)
            if not is_valid and violation:
                if violation.severity == 'error':
                    violations.append(violation)
                else:
                    warnings.append(violation)
        
        # Create report
        report = ComplianceReport(
            timestamp=datetime.now(),
            operation=operation,
            total_checks=checks,
            violations=violations,
            warnings=warnings,
            passed=len(violations) == 0
        )
        
        return report
    
    def _suggest_commit_format(self, message: str) -> str:
        """Generate suggestion for commit message format."""
        # Detect likely type
        message_lower = message.lower()
        if any(word in message_lower for word in ['add', 'implement', 'create']):
            type_hint = "feat"
        elif any(word in message_lower for word in ['fix', 'bug', 'resolve']):
            type_hint = "fix"
        elif any(word in message_lower for word in ['doc', 'readme', 'comment']):
            type_hint = "docs"
        elif any(word in message_lower for word in ['test']):
            type_hint = "test"
        elif any(word in message_lower for word in ['refactor', 'clean', 'improve']):
            type_hint = "refactor"
        else:
            type_hint = "chore"
        
        return f"Try: '{type_hint}: {message.capitalize()}'"
    
    def auto_fix_violation(self, violation: Violation, **kwargs) -> Optional[str]:
        """
        Attempt to automatically fix a violation.
        
        Args:
            violation: The violation to fix
            **kwargs: Context for fix (file_path, content, etc.)
            
        Returns:
            Fixed content or None if not fixable
        """
        if not violation.auto_fixable:
            return None
        
        if violation.rule_name == 'conventional_commits':
            message = kwargs.get('message', '')
            return self._suggest_commit_format(message).replace("Try: '", "").rstrip("'")
        
        elif violation.rule_name == 'changelog_required':
            # Generate changelog entry
            changed_files = kwargs.get('changed_files', [])
            commit_msg = kwargs.get('message', '')
            
            entry = f"\n## [{datetime.now().strftime('%Y-%m-%d')}]\n"
            entry += f"### Changed\n"
            entry += f"- {commit_msg}\n"
            entry += f"  Files: {', '.join(changed_files)}\n"
            
            return entry
        
        return None
    
    def generate_compliance_report(
        self,
        changed_files: List[str],
        commit_message: str = ""
    ) -> str:
        """
        Generate comprehensive compliance report for PR/commit.
        
        Args:
            changed_files: List of modified files
            commit_message: Commit message (optional)
            
        Returns:
            Formatted compliance report
        """
        report_lines = [
            "# 📊 Copilot Instructions Compliance Report",
            f"\n**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Files Changed**: {len(changed_files)}",
            "\n## Validation Results\n"
        ]
        
        all_passed = True
        
        # Validate each file
        for file_path in changed_files:
            is_valid, violation = self.validate_file_location(file_path)
            if not is_valid:
                all_passed = False
                report_lines.append(f"❌ **{file_path}**")
                report_lines.append(f"   - {violation.message}")
                if violation.suggestion:
                    report_lines.append(f"   - 💡 {violation.suggestion}")
        
        # Validate commit message
        if commit_message:
            is_valid, violation = self.validate_commit_message(commit_message)
            if not is_valid:
                all_passed = False
                report_lines.append(f"\n❌ **Commit Message**")
                report_lines.append(f"   - {violation.message}")
                if violation.suggestion:
                    report_lines.append(f"   - 💡 {violation.suggestion}")
        
        # Validate changelog
        is_valid, violation = self.validate_changelog_updated(changed_files)
        if not is_valid:
            all_passed = False
            report_lines.append(f"\n❌ **Changelog**")
            report_lines.append(f"   - {violation.message}")
            if violation.suggestion:
                report_lines.append(f"   - 💡 {violation.suggestion}")
        
        # Summary
        if all_passed:
            report_lines.insert(3, "\n✅ **Status**: PASSED - All checks successful\n")
        else:
            report_lines.insert(3, "\n🔴 **Status**: FAILED - Violations found\n")
        
        return "\n".join(report_lines)


def main():
    """CLI for testing validator."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate against Copilot instructions")
    parser.add_argument('instructions', type=Path, help="Path to copilot-instructions.md")
    parser.add_argument('--file', type=str, help="Validate file location")
    parser.add_argument('--commit', type=str, help="Validate commit message")
    parser.add_argument('--port', type=int, help="Validate port number")
    parser.add_argument('--verbose', action='store_true', help="Verbose output")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
    
    # Initialize validator
    validator = InstructionValidator(args.instructions)
    
    # Run validations
    if args.file:
        is_valid, violation = validator.validate_file_location(args.file)
        if is_valid:
            print(f"✅ File location valid: {args.file}")
        else:
            print(f"❌ {violation.message}")
            if violation.suggestion:
                print(f"💡 {violation.suggestion}")
    
    if args.commit:
        is_valid, violation = validator.validate_commit_message(args.commit)
        if is_valid:
            print(f"✅ Commit message valid")
        else:
            print(f"❌ {violation.message}")
            if violation.suggestion:
                print(f"💡 {violation.suggestion}")
    
    if args.port:
        is_valid, violation = validator.validate_port_usage(args.port)
        if is_valid:
            print(f"✅ Port {args.port} valid")
        else:
            print(f"❌ {violation.message}")
            if violation.suggestion:
                print(f"💡 {violation.suggestion}")


if __name__ == "__main__":
    main()
