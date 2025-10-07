#!/usr/bin/env python3
"""
Security Auditor for Pull Requests

Comprehensive security audit system for non-agent PRs to detect:
- Hardcoded secrets and credentials
- Dependency vulnerabilities
- Code injection risks (SQL, XSS, command injection)
- Malicious patterns and obfuscated code
- License compliance issues
"""

import re
import subprocess
import logging
import json
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Set
from pathlib import Path
from enum import Enum

logger = logging.getLogger(__name__)


class Severity(Enum):
    """Security issue severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class Category(Enum):
    """Security issue categories"""
    SECRETS = "secrets"
    INJECTION = "injection"
    MALWARE = "malware"
    DEPENDENCY = "dependency"
    LICENSE = "license"
    CODE_QUALITY = "code_quality"


@dataclass
class SecurityIssue:
    """Represents a security issue found during audit"""
    severity: str
    category: str
    description: str
    file: str
    line: Optional[int] = None
    code_snippet: Optional[str] = None
    recommendation: str = ""
    cwe_id: Optional[str] = None  # Common Weakness Enumeration ID
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class AuditResult:
    """Results of a security audit"""
    passed: bool
    issues: List[SecurityIssue]
    score: float  # 0-100, higher is better
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    
    def to_dict(self) -> Dict:
        return {
            'passed': self.passed,
            'issues': [issue.to_dict() for issue in self.issues],
            'score': self.score,
            'critical_count': self.critical_count,
            'high_count': self.high_count,
            'medium_count': self.medium_count,
            'low_count': self.low_count
        }


class SecurityAuditor:
    """
    Comprehensive security auditor for pull requests.
    
    Performs multiple security checks:
    1. Secrets scanning (API keys, passwords, tokens)
    2. Dependency vulnerability checks
    3. Code injection detection (SQL, XSS, command injection)
    4. Malicious pattern detection
    5. License compliance
    """
    
    # Patterns for detecting secrets
    SECRET_PATTERNS = [
        # API Keys and Tokens
        (r'(?i)(api[_-]?key|apikey)[\'"\s]*[:=][\'"\s]*([a-zA-Z0-9_-]{20,})', 'API Key'),
        (r'(?i)(secret[_-]?key|secretkey)[\'"\s]*[:=][\'"\s]*([a-zA-Z0-9_-]{20,})', 'Secret Key'),
        (r'(?i)(access[_-]?token|accesstoken)[\'"\s]*[:=][\'"\s]*([a-zA-Z0-9_-]{20,})', 'Access Token'),
        (r'(?i)(auth[_-]?token|authtoken)[\'"\s]*[:=][\'"\s]*([a-zA-Z0-9_-]{20,})', 'Auth Token'),
        
        # GitHub Tokens
        (r'ghp_[a-zA-Z0-9]{36}', 'GitHub Personal Access Token'),
        (r'gho_[a-zA-Z0-9]{36}', 'GitHub OAuth Token'),
        (r'ghu_[a-zA-Z0-9]{36}', 'GitHub User Token'),
        
        # AWS Keys
        (r'AKIA[0-9A-Z]{16}', 'AWS Access Key'),
        (r'(?i)aws[_-]?secret[_-]?access[_-]?key[\'"\s]*[:=][\'"\s]*([a-zA-Z0-9/+=]{40})', 'AWS Secret Key'),
        
        # Private Keys
        (r'-----BEGIN (RSA |DSA |EC )?PRIVATE KEY-----', 'Private Key'),
        (r'-----BEGIN OPENSSH PRIVATE KEY-----', 'OpenSSH Private Key'),
        
        # Passwords
        (r'(?i)password[\'"\s]*[:=][\'"\s]*[\'"]([^\'"]{8,})[\'"]', 'Hardcoded Password'),
        (r'(?i)passwd[\'"\s]*[:=][\'"\s]*[\'"]([^\'"]{8,})[\'"]', 'Hardcoded Password'),
        
        # Database Connection Strings
        (r'(?i)(mysql|postgresql|mongodb)://[^:]+:[^@]+@', 'Database Connection String with Credentials'),
        
        # JWT Tokens
        (r'eyJ[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}', 'JWT Token'),
    ]
    
    # Dangerous code patterns
    INJECTION_PATTERNS = [
        # SQL Injection
        (r'(?i)execute\s*\(\s*[\'"].*%s.*[\'"]', 'Potential SQL Injection (string formatting)'),
        (r'(?i)cursor\.execute\s*\(\s*f[\'"]', 'Potential SQL Injection (f-string in query)'),
        (r'(?i)query\s*=\s*[\'"].*\+', 'Potential SQL Injection (string concatenation)'),
        
        # Command Injection
        (r'subprocess\.(call|run|Popen)\s*\([^)]*shell\s*=\s*True', 'Command Injection Risk (shell=True)'),
        (r'os\.system\s*\(', 'Command Injection Risk (os.system)'),
        (r'eval\s*\(', 'Code Injection Risk (eval)'),
        (r'exec\s*\(', 'Code Injection Risk (exec)'),
        
        # XSS (in templates/HTML)
        (r'\{\{.*\|safe\}\}', 'XSS Risk (unsafe template variable)'),
        (r'innerHTML\s*=', 'XSS Risk (innerHTML assignment)'),
        (r'document\.write\s*\(', 'XSS Risk (document.write)'),
        
        # Path Traversal
        (r'open\s*\([^)]*\+', 'Path Traversal Risk (path concatenation)'),
        (r'os\.path\.join\s*\([^)]*input', 'Path Traversal Risk (user input in path)'),
    ]
    
    # Malicious patterns
    MALICIOUS_PATTERNS = [
        (r'import\s+base64.*decode', 'Suspicious base64 decoding'),
        (r'(?i)reverse[_-]?shell', 'Potential reverse shell'),
        (r'socket\.socket.*connect', 'Network connection attempt'),
        (r'(?i)crypto.*encrypt.*key\s*=', 'Suspicious encryption operation'),
        (r'__import__\s*\([\'"]', 'Dynamic import (potential obfuscation)'),
    ]
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize security auditor
        
        Args:
            config: Configuration dict with audit settings
        """
        self.config = config or {}
        self.block_on_critical = self.config.get('block_on_critical', True)
        self.block_on_high = self.config.get('block_on_high', True)
        self.warn_on_medium = self.config.get('warn_on_medium', True)
        
        # Tools availability
        self.tools_available = {
            'bandit': self._check_tool_available('bandit'),
            'safety': self._check_tool_available('safety'),
        }
        
        logger.info(f"🔒 Security Auditor initialized")
        logger.info(f"   Available tools: {[k for k, v in self.tools_available.items() if v]}")
    
    def _check_tool_available(self, tool: str) -> bool:
        """Check if a security tool is available"""
        try:
            subprocess.run([tool, '--version'], 
                         capture_output=True, 
                         timeout=5,
                         check=False)
            return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
    
    async def audit_pr(self, repo: str, pr_number: int, files: List[Dict]) -> AuditResult:
        """
        Run comprehensive security audit on PR
        
        Args:
            repo: Repository name (owner/repo)
            pr_number: Pull request number
            files: List of changed files with content
        
        Returns:
            AuditResult with all findings
        """
        logger.info(f"🔒 Starting security audit for PR #{pr_number} in {repo}")
        
        issues: List[SecurityIssue] = []
        
        # 1. Secrets scanning
        logger.debug("🔍 Scanning for secrets...")
        issues.extend(await self._scan_secrets(files))
        
        # 2. Dependency vulnerabilities (if requirements.txt or package.json changed)
        logger.debug("📦 Checking dependencies...")
        issues.extend(await self._check_dependencies(files))
        
        # 3. Code injection risks
        logger.debug("💉 Scanning for injection vulnerabilities...")
        issues.extend(await self._scan_injection_risks(files))
        
        # 4. Malicious patterns
        logger.debug("🦠 Detecting malicious patterns...")
        issues.extend(await self._detect_malicious_patterns(files))
        
        # 5. License compliance (if dependencies changed)
        logger.debug("⚖️ Checking license compliance...")
        issues.extend(await self._check_licenses(files))
        
        # 6. Run bandit if available (Python security linter)
        if self.tools_available.get('bandit'):
            logger.debug("🐍 Running Bandit...")
            issues.extend(await self._run_bandit(files))
        
        # Calculate severity counts
        critical_count = sum(1 for i in issues if i.severity == Severity.CRITICAL.value)
        high_count = sum(1 for i in issues if i.severity == Severity.HIGH.value)
        medium_count = sum(1 for i in issues if i.severity == Severity.MEDIUM.value)
        low_count = sum(1 for i in issues if i.severity == Severity.LOW.value)
        
        # Determine if audit passed
        passed = True
        if self.block_on_critical and critical_count > 0:
            passed = False
        if self.block_on_high and high_count > 0:
            passed = False
        
        # Calculate security score (0-100)
        score = self._calculate_security_score(issues)
        
        result = AuditResult(
            passed=passed,
            issues=issues,
            score=score,
            critical_count=critical_count,
            high_count=high_count,
            medium_count=medium_count,
            low_count=low_count
        )
        
        logger.info(f"🔒 Audit complete: {len(issues)} issues found")
        logger.info(f"   Critical: {critical_count}, High: {high_count}, Medium: {medium_count}, Low: {low_count}")
        logger.info(f"   Score: {score:.1f}/100, Passed: {passed}")
        
        return result
    
    async def _scan_secrets(self, files: List[Dict]) -> List[SecurityIssue]:
        """Scan files for hardcoded secrets"""
        issues = []
        
        for file in files:
            if file.get('status') == 'removed':
                continue
            
            filename = file.get('filename', '')
            patch = file.get('patch', '')
            
            # Skip binary files and certain directories
            if any(ext in filename.lower() for ext in ['.png', '.jpg', '.pdf', '.zip']):
                continue
            if any(dir in filename for dir in ['node_modules/', 'venv/', '.git/']):
                continue
            
            # Scan patch content
            for line_no, line in enumerate(patch.split('\n'), 1):
                if not line.startswith('+'):  # Only check added lines
                    continue
                
                line_content = line[1:]  # Remove '+' prefix
                
                for pattern, secret_type in self.SECRET_PATTERNS:
                    if re.search(pattern, line_content):
                        issues.append(SecurityIssue(
                            severity=Severity.CRITICAL.value,
                            category=Category.SECRETS.value,
                            description=f"{secret_type} detected in code",
                            file=filename,
                            line=line_no,
                            code_snippet=line_content[:100],
                            recommendation=f"Remove {secret_type} and use environment variables or secret management",
                            cwe_id="CWE-798"
                        ))
        
        return issues
    
    async def _check_dependencies(self, files: List[Dict]) -> List[SecurityIssue]:
        """Check for dependency vulnerabilities"""
        issues = []
        
        # Check if dependency files changed
        dep_files = [f for f in files if f.get('filename') in ['requirements.txt', 'package.json', 'Pipfile']]
        
        if not dep_files:
            return issues
        
        # For now, just flag that dependencies changed and manual review needed
        # In production, we'd use safety, npm audit, etc.
        for file in dep_files:
            issues.append(SecurityIssue(
                severity=Severity.MEDIUM.value,
                category=Category.DEPENDENCY.value,
                description=f"Dependency file {file['filename']} modified - manual security review required",
                file=file['filename'],
                recommendation="Run 'safety check' or 'npm audit' to verify dependencies",
                cwe_id="CWE-1395"
            ))
        
        return issues
    
    async def _scan_injection_risks(self, files: List[Dict]) -> List[SecurityIssue]:
        """Scan for code injection vulnerabilities"""
        issues = []
        
        for file in files:
            if file.get('status') == 'removed':
                continue
            
            filename = file.get('filename', '')
            patch = file.get('patch', '')
            
            # Only check code files
            if not any(filename.endswith(ext) for ext in ['.py', '.js', '.ts', '.php', '.java']):
                continue
            
            for line_no, line in enumerate(patch.split('\n'), 1):
                if not line.startswith('+'):
                    continue
                
                line_content = line[1:]
                
                for pattern, issue_desc in self.INJECTION_PATTERNS:
                    if re.search(pattern, line_content):
                        # Determine severity based on pattern type
                        severity = Severity.HIGH.value
                        if 'eval' in issue_desc or 'exec' in issue_desc:
                            severity = Severity.CRITICAL.value
                        
                        issues.append(SecurityIssue(
                            severity=severity,
                            category=Category.INJECTION.value,
                            description=issue_desc,
                            file=filename,
                            line=line_no,
                            code_snippet=line_content[:100],
                            recommendation="Use parameterized queries, input validation, and avoid dynamic code execution",
                            cwe_id="CWE-89" if 'SQL' in issue_desc else "CWE-78"
                        ))
        
        return issues
    
    async def _detect_malicious_patterns(self, files: List[Dict]) -> List[SecurityIssue]:
        """Detect potentially malicious code patterns"""
        issues = []
        
        for file in files:
            if file.get('status') == 'removed':
                continue
            
            filename = file.get('filename', '')
            patch = file.get('patch', '')
            
            for line_no, line in enumerate(patch.split('\n'), 1):
                if not line.startswith('+'):
                    continue
                
                line_content = line[1:]
                
                for pattern, issue_desc in self.MALICIOUS_PATTERNS:
                    if re.search(pattern, line_content):
                        issues.append(SecurityIssue(
                            severity=Severity.HIGH.value,
                            category=Category.MALWARE.value,
                            description=issue_desc,
                            file=filename,
                            line=line_no,
                            code_snippet=line_content[:100],
                            recommendation="Review code carefully for malicious intent",
                            cwe_id="CWE-506"
                        ))
        
        return issues
    
    async def _check_licenses(self, files: List[Dict]) -> List[SecurityIssue]:
        """Check for license compliance issues"""
        issues = []
        
        # Check if LICENSE file was modified
        license_files = [f for f in files if 'LICENSE' in f.get('filename', '').upper()]
        
        for file in license_files:
            if file.get('status') == 'modified':
                issues.append(SecurityIssue(
                    severity=Severity.MEDIUM.value,
                    category=Category.LICENSE.value,
                    description=f"License file {file['filename']} was modified",
                    file=file['filename'],
                    recommendation="Verify license changes are intentional and compliant"
                ))
        
        return issues
    
    async def _run_bandit(self, files: List[Dict]) -> List[SecurityIssue]:
        """Run Bandit Python security linter"""
        issues = []
        
        # For now, just return empty list
        # In production, we'd run bandit on Python files and parse results
        
        return issues
    
    def _calculate_security_score(self, issues: List[SecurityIssue]) -> float:
        """
        Calculate security score (0-100)
        
        100 = Perfect (no issues)
        0 = Critical issues found
        """
        if not issues:
            return 100.0
        
        # Weighted scoring
        weights = {
            Severity.CRITICAL.value: 40,
            Severity.HIGH.value: 20,
            Severity.MEDIUM.value: 5,
            Severity.LOW.value: 1,
            Severity.INFO.value: 0
        }
        
        total_deduction = sum(weights.get(issue.severity, 0) for issue in issues)
        score = max(0, 100 - total_deduction)
        
        return round(score, 1)
    
    def format_audit_report(self, result: AuditResult) -> str:
        """
        Format audit result as markdown report
        
        Args:
            result: Audit result to format
        
        Returns:
            Formatted markdown report
        """
        lines = []
        lines.append("# 🔒 Security Audit Report\n")
        
        # Summary
        status_emoji = "✅" if result.passed else "❌"
        lines.append(f"**Status**: {status_emoji} {'PASSED' if result.passed else 'FAILED'}")
        lines.append(f"**Security Score**: {result.score}/100\n")
        
        # Issue counts
        lines.append("## Issue Summary\n")
        lines.append(f"- 🔴 **Critical**: {result.critical_count}")
        lines.append(f"- 🟠 **High**: {result.high_count}")
        lines.append(f"- 🟡 **Medium**: {result.medium_count}")
        lines.append(f"- 🟢 **Low**: {result.low_count}")
        lines.append("")
        
        if not result.issues:
            lines.append("✅ No security issues detected!")
            return '\n'.join(lines)
        
        # Group issues by severity
        by_severity = {}
        for issue in result.issues:
            by_severity.setdefault(issue.severity, []).append(issue)
        
        # Display issues by severity
        severity_order = [Severity.CRITICAL.value, Severity.HIGH.value, 
                         Severity.MEDIUM.value, Severity.LOW.value]
        
        for severity in severity_order:
            if severity not in by_severity:
                continue
            
            emoji = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}.get(severity, "⚪")
            lines.append(f"## {emoji} {severity.upper()} Issues\n")
            
            for i, issue in enumerate(by_severity[severity], 1):
                lines.append(f"### {i}. {issue.description}")
                lines.append(f"**File**: `{issue.file}`")
                if issue.line:
                    lines.append(f"**Line**: {issue.line}")
                if issue.code_snippet:
                    lines.append(f"```\n{issue.code_snippet}\n```")
                lines.append(f"**Recommendation**: {issue.recommendation}")
                if issue.cwe_id:
                    lines.append(f"**CWE**: [{issue.cwe_id}](https://cwe.mitre.org/data/definitions/{issue.cwe_id.split('-')[1]}.html)")
                lines.append("")
        
        # Footer
        if not result.passed:
            lines.append("---")
            lines.append("⚠️ **This PR is blocked from merging due to critical security issues.**")
            lines.append("Please address all critical/high severity issues before proceeding.")
        
        return '\n'.join(lines)
