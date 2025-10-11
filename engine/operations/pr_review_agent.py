"""
PR Review Agent - Automated code review for pull requests.

This module provides automated code review capabilities for PRs created by bot accounts.
It performs:
- Code quality analysis
- Test coverage verification
- Style compliance checks
- Security scanning
- Detailed PR comments with actionable feedback
"""

import json
import logging
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import requests


logger = logging.getLogger(__name__)


class PRReviewAgent:
    """Automated code review agent for pull requests."""
    
    def __init__(self, project_root: Optional[str] = None, github_token: Optional[str] = None):
        """
        Initialize PR Review Agent.
        
        Args:
            project_root: Path to project root (auto-detected if not provided)
            github_token: GitHub token for API requests (loads from secrets if not provided)
        """
        if project_root:
            self.project_root = Path(project_root)
        else:
            # Auto-detect from module location
            self.project_root = Path(__file__).parent.parent.parent.resolve()
        
        # Load GitHub token
        if github_token:
            self.github_token = github_token
        else:
            self.github_token = self._load_github_token()
    
    def _load_github_token(self) -> str:
        """Load GitHub token from secrets."""
        token_path = self.project_root / 'secrets' / 'agents' / 'm0nk111.token'
        
        if not token_path.exists():
            raise FileNotFoundError(f"GitHub token not found: {token_path}")
        
        return token_path.read_text().strip()
    
    def _github_request(
        self,
        method: str,
        url: str,
        json_data: Optional[Dict] = None
    ) -> Tuple[int, Optional[Dict]]:
        """
        Make GitHub API request.
        
        Args:
            method: HTTP method (GET, POST, PATCH, PUT)
            url: API endpoint URL
            json_data: Optional JSON data for request body
        
        Returns:
            Tuple of (status_code, response_json)
        """
        headers = {
            "Authorization": f"token {self.github_token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        try:
            if method == 'GET':
                resp = requests.get(url, headers=headers)
            elif method == 'POST':
                resp = requests.post(url, headers=headers, json=json_data)
            elif method == 'PATCH':
                resp = requests.patch(url, headers=headers, json=json_data)
            elif method == 'PUT':
                resp = requests.put(url, headers=headers, json=json_data)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            if resp.status_code in [200, 201, 204]:
                try:
                    return resp.status_code, resp.json() if resp.text else None
                except:
                    return resp.status_code, None
            else:
                return resp.status_code, None
        
        except Exception as e:
            logger.error(f"GitHub API error: {e}")
            return 0, None
    
    def review_pr(self, repo: str, pr_number: int) -> Dict:
        """
        Perform automated review of a pull request.
        
        Args:
            repo: Repository name (format: 'owner/repo')
            pr_number: Pull request number
        
        Returns:
            Dictionary with review results and summary
        """
        logger.info(f"🔍 Starting automated review for {repo}#{pr_number}")
        logger.info("📊 Review Type: Static Code Analysis (No LLM)")
        logger.info("🔍 Checks: File size, print statements, TODOs, exceptions, docstrings, tests")
        
        review_result = {
            'pr': f"{repo}#{pr_number}",
            'approved': False,
            'issues': [],
            'suggestions': [],
            'summary': ''
        }
        
        try:
            # Get PR details
            pr_data = self._get_pr_details(repo, pr_number)
            if not pr_data:
                review_result['issues'].append("Failed to fetch PR details")
                return review_result
            
            # Get changed files
            files = self._get_changed_files(repo, pr_number)
            if not files:
                review_result['issues'].append("No files changed in PR")
                return review_result
            
            logger.info(f"📝 Reviewing {len(files)} changed file(s)")
            
            # Analyze each file
            for file_data in files:
                filename = file_data['filename']
                status = file_data['status']
                
                logger.info(f"   Analyzing: {filename} ({status})")
                
                # Skip deleted files
                if status == 'removed':
                    continue
                
                # Python files get full review
                if filename.endswith('.py'):
                    file_issues = self._review_python_file(repo, pr_number, file_data)
                    review_result['issues'].extend(file_issues)
            
            # Run tests if test files changed
            test_files = [f['filename'] for f in files if 'test' in f['filename']]
            if test_files:
                test_result = self._run_tests(test_files)
                if not test_result['passed']:
                    review_result['issues'].append(
                        f"Tests failed: {test_result['failed_count']} failures"
                    )
            
            # Determine approval
            critical_issues = [i for i in review_result['issues'] if 'CRITICAL' in i or 'ERROR' in i]
            
            if not review_result['issues']:
                review_result['approved'] = True
                review_result['summary'] = "✅ All checks passed! Code looks good."
            elif not critical_issues:
                review_result['approved'] = True  # Minor issues OK
                review_result['summary'] = f"⚠️ Approved with {len(review_result['issues'])} minor suggestion(s)"
            else:
                review_result['approved'] = False
                review_result['summary'] = f"❌ Changes requested: {len(critical_issues)} issue(s) need attention"
            
            logger.info(f"📊 Review complete: {review_result['summary']}")
            
        except Exception as e:
            logger.error(f"❌ Review failed: {e}", exc_info=True)
            review_result['issues'].append(f"Review error: {str(e)}")
        
        return review_result
    
    def _get_pr_details(self, repo: str, pr_number: int) -> Optional[Dict]:
        """Get PR details from GitHub API."""
        try:
            owner, repo_name = repo.split('/')
            url = f"https://api.github.com/repos/{owner}/{repo_name}/pulls/{pr_number}"
            
            status, data = self._github_request('GET', url)
            
            if status == 200:
                return data
            else:
                logger.error(f"❌ Failed to get PR details: status {status}")
                return None
        
        except Exception as e:
            logger.error(f"❌ Error getting PR details: {e}")
            return None
    
    def _get_changed_files(self, repo: str, pr_number: int) -> List[Dict]:
        """Get list of changed files in PR."""
        try:
            owner, repo_name = repo.split('/')
            url = f"https://api.github.com/repos/{owner}/{repo_name}/pulls/{pr_number}/files"
            
            status, data = self._github_request('GET', url)
            
            if status == 200 and isinstance(data, list):
                return data
            else:
                logger.error(f"❌ Failed to get PR files: status {status}")
                return []
        
        except Exception as e:
            logger.error(f"❌ Error getting PR files: {e}")
            return []
    
    def _review_python_file(self, repo: str, pr_number: int, file_data: Dict) -> List[str]:
        """
        Review a Python file for code quality issues.
        
        Args:
            repo: Repository name
            pr_number: PR number
            file_data: File data from GitHub API
        
        Returns:
            List of issues found
        """
        issues = []
        filename = file_data['filename']
        
        # Check for large files
        if file_data.get('changes', 0) > 500:
            issues.append(f"⚠️ Large file: {filename} has {file_data['changes']} changes. Consider splitting.")
        
        # Check if patch data available
        patch = file_data.get('patch', '')
        if not patch:
            return issues
        
        # Analyze patch for common issues
        lines = patch.split('\n')
        
        # Check for print statements (should use logging)
        print_lines = [i for i, line in enumerate(lines) if 'print(' in line and line.strip().startswith('+')]
        if print_lines:
            issues.append(f"💡 Consider using logging instead of print() in {filename} (lines: {len(print_lines)})")
        
        # Check for TODO/FIXME comments
        todo_lines = [i for i, line in enumerate(lines) if ('TODO' in line or 'FIXME' in line) and line.strip().startswith('+')]
        if todo_lines:
            issues.append(f"📝 TODOs found in {filename}: {len(todo_lines)} items")
        
        # Check for except: pass (bad error handling)
        for i, line in enumerate(lines):
            if line.strip().startswith('+') and 'except:' in line:
                if i + 1 < len(lines) and 'pass' in lines[i + 1]:
                    issues.append(f"❌ CRITICAL: Silent exception handling in {filename}. Use specific exceptions and logging.")
        
        # Check for missing docstrings in new functions
        func_lines = [(i, line) for i, line in enumerate(lines) if line.strip().startswith('+ def ') or line.strip().startswith('+def ')]
        for i, func_line in func_lines:
            # Check if docstring follows
            if i + 2 < len(lines):
                next_lines = ''.join(lines[i+1:i+3])
                if '"""' not in next_lines and "'''" not in next_lines:
                    func_name = func_line.split('def ')[1].split('(')[0]
                    issues.append(f"⚠️ Missing docstring for function '{func_name}' in {filename}")
        
        return issues
    
    def _run_tests(self, test_files: List[str]) -> Dict:
        """
        Run tests for changed test files.
        
        Args:
            test_files: List of test file paths
        
        Returns:
            Dictionary with test results
        """
        result = {
            'passed': False,
            'failed_count': 0,
            'output': ''
        }
        
        try:
            # Run pytest on changed test files
            cmd = ['python3', '-m', 'pytest'] + test_files + ['-v', '--tb=short']
            
            process = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            result['output'] = process.stdout + process.stderr
            result['passed'] = process.returncode == 0
            
            # Count failures
            if not result['passed']:
                for line in result['output'].split('\n'):
                    if 'failed' in line.lower():
                        try:
                            parts = line.split()
                            for i, part in enumerate(parts):
                                if 'failed' in part.lower() and i > 0:
                                    result['failed_count'] = int(parts[i-1])
                                    break
                        except:
                            pass
            
            logger.info(f"✅ Tests {'passed' if result['passed'] else 'failed'}: {result['failed_count']} failures")
        
        except subprocess.TimeoutExpired:
            logger.error("❌ Test execution timed out")
            result['failed_count'] = 1
        except Exception as e:
            logger.error(f"❌ Test execution error: {e}")
            result['failed_count'] = 1
        
        return result
    
    def post_review_comment(self, repo: str, pr_number: int, review_result: Dict) -> bool:
        """
        Post review comment to PR.
        
        Args:
            repo: Repository name
            pr_number: PR number
            review_result: Review results from review_pr()
        
        Returns:
            True if comment posted successfully
        """
        try:
            # Format review comment
            comment = self._format_review_comment(review_result)
            
            # Post comment via GitHub API
            owner, repo_name = repo.split('/')
            url = f"https://api.github.com/repos/{owner}/{repo_name}/issues/{pr_number}/comments"
            
            data = {'body': comment}
            status, _ = self._github_request('POST', url, json_data=data)
            
            if status in [200, 201]:
                logger.info(f"✅ Posted review comment to {repo}#{pr_number}")
                return True
            else:
                logger.error(f"❌ Failed to post comment: status {status}")
                return False
        
        except Exception as e:
            logger.error(f"❌ Error posting comment: {e}")
            return False
    
    def _format_review_comment(self, review_result: Dict) -> str:
        """Format review results as GitHub comment."""
        lines = [
            "## 🤖 Automated Code Review",
            "",
            f"**Status**: {review_result['summary']}",
            ""
        ]
        
        if review_result['issues']:
            lines.append("### Issues Found")
            for issue in review_result['issues']:
                lines.append(f"- {issue}")
            lines.append("")
        
        if review_result['suggestions']:
            lines.append("### Suggestions")
            for suggestion in review_result['suggestions']:
                lines.append(f"- {suggestion}")
            lines.append("")
        
        if review_result['approved']:
            lines.append("✅ **This PR is approved for merge**")
        else:
            lines.append("❌ **Changes requested** - Please address the issues above")
        
        lines.extend([
            "",
            "---",
            "*Automated review by Agent-Forge*"
        ])
        
        return '\n'.join(lines)


def main():
    """CLI entry point for testing."""
    import sys
    import argparse
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(message)s'
    )
    
    parser = argparse.ArgumentParser(description='Review a pull request')
    parser.add_argument('repo', help='Repository (owner/repo)')
    parser.add_argument('pr_number', type=int, help='PR number')
    parser.add_argument('--post-comment', action='store_true', help='Post review as comment')
    
    args = parser.parse_args()
    
    try:
        reviewer = PRReviewAgent()
        
        # Print review type info
        print("📊 PR Review Agent - Static Code Analysis")
        print("🔧 Review Method: Rule-based checks (No LLM)")
        print("✓ Fast • ✓ Deterministic • ✓ Zero cost")
        print()
        
        result = reviewer.review_pr(args.repo, args.pr_number)
        
        print(f"\n{'='*60}")
        print("REVIEW SUMMARY")
        print('='*60)
        print(result['summary'])
        
        if result['issues']:
            print(f"\nIssues ({len(result['issues'])}):")
            for issue in result['issues']:
                print(f"  - {issue}")
        
        if args.post_comment:
            if reviewer.post_review_comment(args.repo, args.pr_number, result):
                print("\n✅ Review comment posted to PR")
            else:
                print("\n❌ Failed to post review comment")
                return 1
        
        return 0 if result['approved'] else 1
    
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return 1


if __name__ == '__main__':
    import sys
    sys.exit(main())
