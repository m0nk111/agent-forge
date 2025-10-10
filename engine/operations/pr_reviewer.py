"""
PR Reviewer Module

Automatically review pull requests created by other agents or contributors.
Provides comprehensive code reviews with feedback, suggestions, and approval/change requests.
Includes mandatory security audits for PRs from non-trusted accounts.
"""

import asyncio
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import logging
import yaml

logger = logging.getLogger(__name__)

# Import security auditor for external PR scanning
try:
    from engine.validation.security_auditor import SecurityAuditor
    SECURITY_AUDITOR_AVAILABLE = True
except ImportError:
    logger.warning("⚠️ SecurityAuditor not available - external PRs will not be scanned")
    SECURITY_AUDITOR_AVAILABLE = False


@dataclass
class ReviewComment:
    """Represents a line-specific review comment."""
    path: str
    line: int
    side: str = "RIGHT"  # RIGHT for new code, LEFT for old code
    body: str = ""
    severity: str = "suggestion"  # suggestion, warning, error


@dataclass
class ReviewCriteria:
    """Review criteria configuration."""
    check_code_quality: bool = True
    check_testing: bool = True
    check_documentation: bool = True
    check_security: bool = True
    require_changelog: bool = True
    min_test_coverage: int = 80
    strictness_level: str = "normal"  # relaxed, normal, strict


class PRReviewer:
    """
    Automated PR reviewer for agent-created pull requests.
    
    Features:
    - Comprehensive code quality analysis
    - Test coverage verification
    - Documentation completeness check
    - Security vulnerability detection
    - Line-specific feedback
    - Approval/change request decisions
    """
    
    def __init__(
        self,
        github_username: str,
        criteria: Optional[ReviewCriteria] = None,
        llm_agent = None,
        github_api = None
    ):
        """
        Initialize PR reviewer.
        
        Args:
            github_username: Username of this agent (to skip own PRs)
            criteria: Review criteria configuration
            llm_agent: LLM agent for intelligent code analysis
            github_api: GitHubAPIHelper instance for posting reviews
        """
        self.github_username = github_username
        self.criteria = criteria or ReviewCriteria()
        self.llm_agent = llm_agent
        self.github_api = github_api
        
        # Review templates
        self.review_templates = self._load_review_templates()
        
        # Reviewed PRs cache (to avoid duplicate reviews)
        self.reviewed_prs: Dict[str, datetime] = {}
        
        logger.info(f"🤖 PR Reviewer initialized for {github_username}")
    
    async def review_pr(
        self,
        repo: str,
        pr_number: int,
        pr_data: Dict,
        files: List[Dict]
    ) -> Tuple[bool, str, List[ReviewComment]]:
        """
        Perform comprehensive PR review.
        
        Args:
            repo: Repository name (owner/repo)
            pr_number: PR number
            pr_data: PR metadata (title, description, author, etc.)
            files: List of changed files with diffs
            
        Returns:
            (should_approve, summary, comments)
        """
        pr_key = f"{repo}#{pr_number}"
        
        # Skip if PR created by self
        if pr_data.get('user', {}).get('login') == self.github_username:
            logger.info(f"⏭️  Skipping own PR: {pr_key}")
            return True, "", []
        
        # Load trusted agents list
        try:
            with open('config/agents.yaml', 'r') as f:
                agents_config = yaml.safe_load(f)
                trusted_agents = [
                    agent['username'] 
                    for agent in agents_config.get('trusted_agents', [])
                    if agent.get('trusted', False)
                ]
        except Exception as e:
            logger.error(f"❌ Failed to load trusted agents: {e}")
            trusted_agents = []
        
        # Check if PR author is trusted - if not, run mandatory security audit
        pr_author = pr_data.get('user', {}).get('login', '')
        is_trusted = pr_author in trusted_agents
        
        if not is_trusted and SECURITY_AUDITOR_AVAILABLE:
            logger.warning(f"🔐 PR from non-trusted author '{pr_author}' - running mandatory security audit")
            
            try:
                from engine.validation.security_auditor import SecurityAuditor
                auditor = SecurityAuditor()
                audit_result = await auditor.audit_pr(repo, pr_number, files)
                
                if not audit_result.passed:
                    # Security audit failed - block PR
                    critical_issues = [
                        issue for issue in audit_result.issues
                        if issue.severity in ['critical', 'high']
                    ]
                    
                    # Format security block message
                    summary = self._format_security_block_message(audit_result, critical_issues)
                    
                    logger.error(f"🚨 Security audit FAILED for {pr_key}: {len(critical_issues)} critical/high issues")
                    return False, summary, []
                else:
                    logger.info(f"✅ Security audit PASSED for {pr_key}: {audit_result.score:.1f}/100")
                    
            except Exception as e:
                logger.error(f"❌ Security audit error for {pr_key}: {e}")
                # On audit error, block PR from untrusted author for safety
                summary = (
                    f"## 🚨 Security Audit Error\n\n"
                    f"The mandatory security audit for this PR from non-trusted author failed to execute:\n"
                    f"```\n{str(e)}\n```\n\n"
                    f"**This PR cannot be merged until the security audit completes successfully.**\n\n"
                    f"Please contact a maintainer to investigate the audit system."
                )
                return False, summary, []
        elif not is_trusted and not SECURITY_AUDITOR_AVAILABLE:
            logger.warning(f"⚠️ PR from non-trusted author '{pr_author}' but SecurityAuditor unavailable")
            # Continue with review but log warning
        else:
            logger.info(f"✅ PR from trusted author '{pr_author}' - skipping security audit")
        
        # Skip if already reviewed recently
        if pr_key in self.reviewed_prs:
            last_review = self.reviewed_prs[pr_key]
            age = (datetime.now() - last_review).total_seconds() / 3600
            if age < 24:  # Skip if reviewed in last 24 hours
                logger.info(f"⏭️  PR recently reviewed ({age:.1f}h ago): {pr_key}")
                return True, "", []
        
        logger.info(f"🔍 Reviewing PR {pr_key}: {pr_data.get('title', 'Untitled')}")
        
        # Check if [skip-review] in description
        if '[skip-review]' in pr_data.get('body', '').lower():
            logger.info(f"⏭️  PR has [skip-review] tag: {pr_key}")
            return True, "", []
        
        # Analyze PR metadata
        pr_analysis = self._analyze_pr_metadata(pr_data)
        
        # Review each file
        all_comments = []
        file_scores = []
        
        for file_data in files:
            comments, score = await self._review_file(file_data)
            all_comments.extend(comments)
            file_scores.append(score)
        
        # Check documentation and tests
        doc_score = self._check_documentation(files, pr_data)
        test_score = self._check_testing(files)
        
        # Check changelog requirement
        changelog_present = any('CHANGELOG' in f['filename'].upper() for f in files)
        
        # Generate overall review summary
        avg_score = sum(file_scores) / len(file_scores) if file_scores else 0.5
        overall_score = (avg_score + doc_score + test_score) / 3
        
        should_approve = self._should_approve(
            overall_score,
            all_comments,
            changelog_present
        )
        
        summary = self._generate_review_summary(
            pr_data=pr_data,
            files=files,
            comments=all_comments,
            scores={
                'code_quality': avg_score,
                'documentation': doc_score,
                'testing': test_score,
                'overall': overall_score
            },
            changelog_present=changelog_present,
            should_approve=should_approve
        )
        
        # Cache review
        self.reviewed_prs[pr_key] = datetime.now()
        
        logger.info(f"✅ Review complete: {pr_key} - {'APPROVE' if should_approve else 'REQUEST_CHANGES'}")
        
        return should_approve, summary, all_comments
    
    async def post_review_to_github(
        self,
        repo: str,
        pr_number: int,
        should_approve: bool,
        summary: str,
        comments: List[ReviewComment],
        pr_head_sha: Optional[str] = None
    ) -> bool:
        """
        Post review to GitHub PR.
        
        Args:
            repo: Repository (owner/repo)
            pr_number: PR number
            should_approve: Whether to approve or request changes
            summary: Review summary text
            comments: List of line-specific comments
            pr_head_sha: SHA of PR head commit (fetched if not provided)
            
        Returns:
            True if successfully posted
        """
        if not self.github_api:
            logger.warning("No GitHub API client configured - cannot post review")
            return False
        
        try:
            owner, repo_name = repo.split('/')
            
            # Get PR head SHA if not provided
            if not pr_head_sha:
                pr_data = self.github_api.get_pull_request(owner, repo_name, pr_number)
                pr_head_sha = pr_data['head']['sha']
            
            # Determine review event type
            event = "APPROVE" if should_approve else "REQUEST_CHANGES"
            
            # Format line comments for GitHub API
            github_comments = []
            for comment in comments[:10]:  # Limit to 10 comments per review
                github_comments.append({
                    'path': comment.path,
                    'line': comment.line,
                    'side': comment.side,
                    'body': comment.body
                })
            
            # Post review
            self.github_api.create_pull_request_review(
                owner=owner,
                repo=repo_name,
                pr_number=pr_number,
                body=summary,
                event=event,
                comments=github_comments if github_comments else None
            )
            
            logger.info(f"✅ Posted {event} review to {repo}#{pr_number}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to post review to {repo}#{pr_number}: {e}")
            return False
    
    async def _review_file(self, file_data: Dict) -> Tuple[List[ReviewComment], float]:
        """
        Review individual file changes.
        
        Args:
            file_data: File metadata and diff
            
        Returns:
            (comments, quality_score)
        """
        filename = file_data['filename']
        patch = file_data.get('patch', '')
        
        if not patch:
            return [], 1.0
        
        comments = []
        issues_found = 0
        total_checks = 0
        
        # Determine file type
        file_ext = Path(filename).suffix
        
        # Code quality checks
        if file_ext in ['.py', '.js', '.ts', '.java', '.go']:
            quality_comments = self._check_code_quality(filename, patch)
            comments.extend(quality_comments)
            issues_found += len([c for c in quality_comments if c.severity in ['warning', 'error']])
            total_checks += 5
        
        # Security checks
        if self.criteria.check_security:
            security_comments = self._check_security(filename, patch)
            comments.extend(security_comments)
            issues_found += len([c for c in security_comments if c.severity == 'error'])
            total_checks += 3
        
        # LLM-powered analysis (if available)
        if self.llm_agent and len(patch) < 2000:  # Reasonable size for LLM
            llm_comments = await self._llm_review_file(filename, patch)
            comments.extend(llm_comments)
            total_checks += 2
        
        # Calculate quality score
        score = 1.0 - (issues_found / max(total_checks, 1))
        score = max(0.0, min(1.0, score))
        
        return comments, score
    
    def _check_code_quality(self, filename: str, patch: str) -> List[ReviewComment]:
        """Check code quality issues."""
        comments = []
        lines = patch.split('\n')
        current_line = 0
        
        for i, line in enumerate(lines):
            # Track line numbers (handle diff format)
            if line.startswith('@@'):
                match = re.search(r'\+(\d+)', line)
                if match:
                    current_line = int(match.group(1))
                continue
            
            if not line.startswith('+'):
                continue
            
            current_line += 1
            code = line[1:]  # Remove '+' prefix
            
            # Check for common issues
            
            # 1. Hardcoded credentials
            if re.search(r'(password|secret|api_key|token)\s*=\s*["\']', code.lower()):
                comments.append(ReviewComment(
                    path=filename,
                    line=current_line,
                    body="⚠️ Possible hardcoded credential detected. Use environment variables instead.",
                    severity="error"
                ))
            
            # 2. Print statements (should use logging)
            if 'print(' in code and not filename.endswith(('.md', '.txt')):
                comments.append(ReviewComment(
                    path=filename,
                    line=current_line,
                    body="💡 Consider using logging instead of print() for better control.",
                    severity="suggestion"
                ))
            
            # 3. Long lines
            if len(code) > 120:
                comments.append(ReviewComment(
                    path=filename,
                    line=current_line,
                    body=f"📏 Line exceeds 120 characters ({len(code)} chars). Consider breaking it up.",
                    severity="suggestion"
                ))
            
            # 4. TODO/FIXME comments
            if re.search(r'\b(TODO|FIXME|XXX|HACK)\b', code):
                comments.append(ReviewComment(
                    path=filename,
                    line=current_line,
                    body="📝 TODO/FIXME comment found. Consider creating an issue to track this.",
                    severity="suggestion"
                ))
            
            # 5. Bare except clauses
            if re.search(r'except\s*:', code):
                comments.append(ReviewComment(
                    path=filename,
                    line=current_line,
                    body="⚠️ Bare 'except:' clause catches all exceptions, including KeyboardInterrupt. Specify exception types.",
                    severity="warning"
                ))
        
        return comments
    
    def _check_security(self, filename: str, patch: str) -> List[ReviewComment]:
        """Check for security vulnerabilities."""
        comments = []
        lines = patch.split('\n')
        current_line = 0
        
        for i, line in enumerate(lines):
            if line.startswith('@@'):
                match = re.search(r'\+(\d+)', line)
                if match:
                    current_line = int(match.group(1))
                continue
            
            if not line.startswith('+'):
                continue
            
            current_line += 1
            code = line[1:]
            
            # SQL injection risks
            if re.search(r'execute\s*\([^)]*%[^)]*\)', code):
                comments.append(ReviewComment(
                    path=filename,
                    line=current_line,
                    body="🔒 Possible SQL injection risk. Use parameterized queries.",
                    severity="error"
                ))
            
            # eval() usage
            if 'eval(' in code:
                comments.append(ReviewComment(
                    path=filename,
                    line=current_line,
                    body="🔒 eval() is dangerous and should be avoided. Consider safer alternatives.",
                    severity="error"
                ))
            
            # shell=True in subprocess
            if 'shell=True' in code:
                comments.append(ReviewComment(
                    path=filename,
                    line=current_line,
                    body="🔒 shell=True in subprocess can be dangerous. Ensure input is sanitized.",
                    severity="warning"
                ))
        
        return comments
    
    async def _llm_review_file(self, filename: str, patch: str) -> List[ReviewComment]:
        """Use LLM for intelligent code review."""
        if not self.llm_agent:
            return []
        
        # Create comprehensive review prompt
        prompt = self._generate_review_prompt(filename, patch)
        
        try:
            response = await self.llm_agent.generate(prompt)
            return self._parse_llm_comments(response, filename)
        except Exception as e:
            logger.warning(f"LLM review failed: {e}")
            return []
    
    def _generate_review_prompt(self, filename: str, patch: str) -> str:
        """Generate comprehensive LLM review prompt."""
        file_ext = Path(filename).suffix
        language = self._guess_language(file_ext)
        
        prompt = f"""You are an expert code reviewer. Review the following {language} code changes.

📁 **File**: `{filename}`

**Diff**:
```diff
{patch}
```

**Review Guidelines**:
1. **Logic & Correctness**: Identify bugs, edge cases, or incorrect logic
2. **Security**: Flag potential security vulnerabilities or unsafe patterns
3. **Performance**: Point out inefficiencies or performance concerns
4. **Best Practices**: Suggest better patterns, idioms, or approaches specific to {language}
5. **Maintainability**: Comment on readability, naming, and code organization

**Output Format**:
Provide 0-3 actionable suggestions. For each suggestion, use this exact format:
```
Line <number>: <clear, specific suggestion with reasoning>
```

**Important**:
- Only comment on NEW lines (lines starting with '+' in diff)
- Be specific and actionable - explain WHY and HOW to fix
- Focus on high-impact issues, not nitpicks
- If code looks good, return empty response

**Examples**:
```
Line 42: This function doesn't handle None values. Add a null check before accessing `.items()` to prevent AttributeError.
Line 58: Using string concatenation in a loop is inefficient. Consider using `''.join()` or a list comprehension instead.
```

Now review the code:
"""
        return prompt
    
    def _guess_language(self, ext: str) -> str:
        """Guess programming language from file extension."""
        lang_map = {
            '.py': 'Python',
            '.js': 'JavaScript',
            '.ts': 'TypeScript',
            '.java': 'Java',
            '.cpp': 'C++',
            '.c': 'C',
            '.go': 'Go',
            '.rs': 'Rust',
            '.rb': 'Ruby',
            '.php': 'PHP',
            '.sh': 'Shell',
            '.yaml': 'YAML',
            '.yml': 'YAML',
            '.json': 'JSON',
            '.md': 'Markdown',
            '.html': 'HTML',
            '.css': 'CSS',
        }
        return lang_map.get(ext.lower(), 'code')
    
    def _parse_llm_comments(self, response: str, filename: str) -> List[ReviewComment]:
        """Parse LLM response into review comments."""
        comments = []
        
        # Extract "Line X: comment" patterns
        pattern = r'Line\s+(\d+):\s*(.+?)(?=Line\s+\d+:|$)'
        matches = re.finditer(pattern, response, re.IGNORECASE | re.DOTALL)
        
        for match in matches:
            line_num = int(match.group(1))
            comment_text = match.group(2).strip()
            
            comments.append(ReviewComment(
                path=filename,
                line=line_num,
                body=f"🤖 {comment_text}",
                severity="suggestion"
            ))
        
        return comments[:3]  # Max 3 LLM comments per file
    
    def _check_documentation(self, files: List[Dict], pr_data: Dict) -> float:
        """Check documentation completeness."""
        if not self.criteria.check_documentation:
            return 1.0
        
        score = 1.0
        
        # Check if README updated for significant changes
        has_code_changes = any(
            f['filename'].endswith(('.py', '.js', '.ts'))
            for f in files
        )
        has_readme_update = any(
            'README' in f['filename'].upper()
            for f in files
        )
        
        if has_code_changes and not has_readme_update and len(files) > 3:
            score -= 0.2
        
        # Check for CHANGELOG entry
        has_changelog = any(
            'CHANGELOG' in f['filename'].upper()
            for f in files
        )
        
        if self.criteria.require_changelog and not has_changelog and len(files) > 1:
            score -= 0.3
        
        return max(0.0, score)
    
    def _check_testing(self, files: List[Dict]) -> float:
        """Check test coverage."""
        if not self.criteria.check_testing:
            return 1.0
        
        # Count code files vs test files
        code_files = [f for f in files if f['filename'].endswith(('.py', '.js', '.ts')) 
                     and 'test' not in f['filename'].lower()]
        test_files = [f for f in files if 'test' in f['filename'].lower()]
        
        if not code_files:
            return 1.0
        
        # Calculate test ratio
        test_ratio = len(test_files) / len(code_files)
        
        # Score based on ratio
        if test_ratio >= 1.0:
            return 1.0
        elif test_ratio >= 0.5:
            return 0.8
        elif test_ratio > 0:
            return 0.6
        else:
            return 0.4
    
    def _should_approve(
        self,
        overall_score: float,
        comments: List[ReviewComment],
        changelog_present: bool
    ) -> bool:
        """Determine if PR should be approved."""
        # Count critical issues
        errors = len([c for c in comments if c.severity == 'error'])
        warnings = len([c for c in comments if c.severity == 'warning'])
        
        # Strict mode
        if self.criteria.strictness_level == 'strict':
            return errors == 0 and warnings == 0 and overall_score >= 0.8
        
        # Normal mode
        elif self.criteria.strictness_level == 'normal':
            return errors == 0 and overall_score >= 0.6
        
        # Relaxed mode
        else:
            return errors <= 1 and overall_score >= 0.5
    
    def _format_security_block_message(self, audit_result, critical_issues: List) -> str:
        """
        Format a security audit failure message for blocking PR merge.
        
        Args:
            audit_result: AuditResult from SecurityAuditor
            critical_issues: List of critical/high severity SecurityIssue objects
            
        Returns:
            Formatted markdown message explaining why PR is blocked
        """
        from engine.validation.security_auditor import SecurityIssue
        
        lines = []
        lines.append("## 🚨 SECURITY AUDIT FAILED - PR BLOCKED\n")
        lines.append(f"**Security Score:** {audit_result.score:.1f}/100 (threshold: 70.0)\n")
        lines.append("This pull request from a non-trusted account has **failed mandatory security checks**.")
        lines.append("The PR cannot be merged until all critical and high-severity issues are resolved.\n")
        
        # Issue summary
        lines.append("### 📊 Issue Summary\n")
        lines.append(f"- 🔴 **Critical:** {audit_result.critical_count}")
        lines.append(f"- 🟠 **High:** {audit_result.high_count}")
        lines.append(f"- 🟡 **Medium:** {audit_result.medium_count}")
        lines.append(f"- 🔵 **Low:** {audit_result.low_count}\n")
        
        # Critical/high issues detail
        if critical_issues:
            lines.append("### 🚨 Critical & High Severity Issues\n")
            
            # Group by category
            by_category = {}
            for issue in critical_issues:
                cat = issue.category
                if cat not in by_category:
                    by_category[cat] = []
                by_category[cat].append(issue)
            
            for category, issues in sorted(by_category.items()):
                emoji = {
                    'secrets': '🔑',
                    'injection': '💉',
                    'malware': '🦠',
                    'dependency': '📦',
                    'license': '⚖️',
                    'code_quality': '🔍'
                }.get(category, '⚠️')
                
                lines.append(f"#### {emoji} {category.upper()}\n")
                
                for issue in issues[:5]:  # Show max 5 per category
                    severity_emoji = '🔴' if issue.severity == 'critical' else '🟠'
                    lines.append(f"**{severity_emoji} {issue.severity.upper()}** - `{issue.file}`")
                    if issue.line:
                        lines.append(f"  - Line {issue.line}")
                    lines.append(f"  - {issue.description}")
                    if issue.recommendation:
                        lines.append(f"  - ✅ **Fix:** {issue.recommendation}")
                    if issue.cwe_id:
                        lines.append(f"  - 🔗 [CWE-{issue.cwe_id}](https://cwe.mitre.org/data/definitions/{issue.cwe_id}.html)")
                    lines.append("")
                
                if len(issues) > 5:
                    lines.append(f"*... and {len(issues) - 5} more {category} issues*\n")
        
        # Instructions
        lines.append("### 🔧 Next Steps\n")
        lines.append("1. **Review and fix** all critical and high severity issues listed above")
        lines.append("2. **Test your changes** thoroughly to ensure fixes don't break functionality")
        lines.append("3. **Push updated code** - the security audit will automatically re-run")
        lines.append("4. **Contact a maintainer** if you believe any issues are false positives\n")
        
        # Footer
        lines.append("---")
        lines.append(f"*🤖 Automated Security Audit by {self.github_username} • Agent Forge Security System v1.0*")
        lines.append(f"*Audit configuration: `config/security_audit.yaml` • Trusted agents: `config/agents.yaml`*")
        
        return "\n".join(lines)
    
    def _generate_review_summary(
        self,
        pr_data: Dict,
        files: List[Dict],
        comments: List[ReviewComment],
        scores: Dict[str, float],
        changelog_present: bool,
        should_approve: bool
    ) -> str:
        """Generate comprehensive review summary."""
        lines = [
            "## 🤖 Automated Code Review\n",
            f"**PR**: {pr_data.get('title', 'Untitled')}",
            f"**Author**: @{pr_data.get('user', {}).get('login', 'unknown')}",
            f"**Files Changed**: {len(files)}",
            f"**Review Date**: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}\n",
            "---\n",
            "### 📊 Quality Scores\n"
        ]
        
        # Score bars
        def score_bar(score: float) -> str:
            filled = int(score * 10)
            return f"{'█' * filled}{'░' * (10 - filled)} {score * 100:.0f}%"
        
        lines.append(f"**Code Quality**: {score_bar(scores['code_quality'])}")
        lines.append(f"**Documentation**: {score_bar(scores['documentation'])}")
        lines.append(f"**Testing**: {score_bar(scores['testing'])}")
        lines.append(f"**Overall**: {score_bar(scores['overall'])}\n")
        
        # Strengths
        strengths = []
        if scores['code_quality'] >= 0.8:
            strengths.append("✅ High code quality with minimal issues")
        if scores['testing'] >= 0.8:
            strengths.append("✅ Good test coverage")
        if scores['documentation'] >= 0.8:
            strengths.append("✅ Well-documented changes")
        if changelog_present:
            strengths.append("✅ CHANGELOG.md updated")
        
        if strengths:
            lines.append("### 💪 Strengths\n")
            lines.extend(strengths)
            lines.append("")
        
        # Issues/Suggestions
        errors = [c for c in comments if c.severity == 'error']
        warnings = [c for c in comments if c.severity == 'warning']
        suggestions = [c for c in comments if c.severity == 'suggestion']
        
        if errors:
            lines.append("### 🔴 Critical Issues\n")
            for comment in errors[:5]:  # Max 5 in summary
                lines.append(f"- `{comment.path}:{comment.line}`: {comment.body}")
            lines.append("")
        
        if warnings:
            lines.append("### ⚠️ Warnings\n")
            for comment in warnings[:5]:
                lines.append(f"- `{comment.path}:{comment.line}`: {comment.body}")
            lines.append("")
        
        if suggestions:
            lines.append("### 💡 Suggestions\n")
            for comment in suggestions[:3]:
                lines.append(f"- `{comment.path}:{comment.line}`: {comment.body}")
            lines.append("")
        
        # Checklist
        lines.append("### ✅ Review Checklist\n")
        lines.append(f"- [{'x' if scores['code_quality'] >= 0.6 else ' '}] Code quality acceptable")
        lines.append(f"- [{'x' if scores['testing'] >= 0.5 else ' '}] Tests included")
        lines.append(f"- [{'x' if scores['documentation'] >= 0.6 else ' '}] Documentation updated")
        lines.append(f"- [{'x' if changelog_present else ' '}] CHANGELOG entry present")
        lines.append(f"- [{'x' if len(errors) == 0 else ' '}] No critical issues\n")
        
        # Decision
        lines.append("### 🎯 Review Decision\n")
        if should_approve:
            lines.append("✅ **APPROVED** - Changes look good!")
            if suggestions:
                lines.append("\n*Minor suggestions provided for optional improvements.*")
        else:
            lines.append("🔄 **CHANGES REQUESTED**")
            lines.append("\nPlease address the issues mentioned above before merging.")
        
        lines.append("\n---")
        lines.append(f"*Automated review by {self.github_username} • Agent Forge PR Reviewer v1.0*")
        
        return "\n".join(lines)
    
    def _analyze_pr_metadata(self, pr_data: Dict) -> Dict:
        """Analyze PR metadata for insights."""
        return {
            'has_description': len(pr_data.get('body', '')) > 50,
            'is_draft': pr_data.get('draft', False),
            'labels': pr_data.get('labels', []),
            'requested_reviewers': pr_data.get('requested_reviewers', [])
        }
    
    def _load_review_templates(self) -> Dict[str, str]:
        """Load review message templates."""
        return {
            'approve': "Great work! Changes look good. ✅",
            'request_changes': "Please address the issues mentioned in the review comments. 🔄",
            'comment': "Some suggestions for improvement. 💡"
        }
    
    @staticmethod
    def load_criteria_from_yaml(config_file: Path) -> ReviewCriteria:
        """Load review criteria from YAML config."""
        try:
            with open(config_file) as f:
                config = yaml.safe_load(f)
            
            return ReviewCriteria(
                check_code_quality=config.get('check_code_quality', True),
                check_testing=config.get('check_testing', True),
                check_documentation=config.get('check_documentation', True),
                check_security=config.get('check_security', True),
                require_changelog=config.get('require_changelog', True),
                min_test_coverage=config.get('min_test_coverage', 80),
                strictness_level=config.get('strictness_level', 'normal')
            )
        except Exception as e:
            logger.warning(f"Failed to load review criteria: {e}")
            return ReviewCriteria()


async def main():
    """CLI for testing PR reviewer."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Review a GitHub PR")
    parser.add_argument('repo', help="Repository (owner/repo)")
    parser.add_argument('pr_number', type=int, help="PR number")
    parser.add_argument('--username', default='agent-bot', help="Agent username")
    parser.add_argument('--config', type=Path, help="Review criteria config")
    
    args = parser.parse_args()
    
    # Load criteria
    if args.config:
        criteria = PRReviewer.load_criteria_from_yaml(args.config)
    else:
        criteria = ReviewCriteria()
    
    # Initialize reviewer
    reviewer = PRReviewer(
        github_username=args.username,
        criteria=criteria
    )
    
    # Mock PR data (in real usage, fetch from GitHub API)
    pr_data = {
        'title': 'Test PR',
        'body': 'Test description',
        'user': {'login': 'test-user'}
    }
    
    files = [
        {
            'filename': 'test.py',
            'patch': '+def test():\n+    print("test")\n'
        }
    ]
    
    # Review PR
    should_approve, summary, comments = await reviewer.review_pr(
        repo=args.repo,
        pr_number=args.pr_number,
        pr_data=pr_data,
        files=files
    )
    
    print(summary)
    print(f"\n{'APPROVE' if should_approve else 'REQUEST_CHANGES'}")
    print(f"{len(comments)} comments generated")


if __name__ == "__main__":
    asyncio.run(main())
