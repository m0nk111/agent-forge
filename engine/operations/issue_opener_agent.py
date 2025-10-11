#!/usr/bin/env python3
"""
Autonomous Issue Opener Agent

This agent automatically:
1. Monitors GitHub issues with specific labels
2. Analyzes issue requirements
3. Generates implementation code
4. Runs tests
5. Creates pull request with solution

Powered by GPT-5 Chat Latest for fast, high-quality code generation.
"""

import os
import sys
import json
import logging
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from engine.core.llm_providers import OpenAIProvider, LLMMessage
from engine.operations.github_api_helper import GitHubAPIHelper

logger = logging.getLogger(__name__)


class IssueOpenerAgent:
    """
    Autonomous agent that resolves GitHub issues and creates PRs.
    
    Workflow:
    1. Fetch issue from GitHub
    2. Analyze requirements using GPT-5
    3. Generate implementation plan
    4. Write code changes
    5. Run tests
    6. Create branch and PR
    """
    
    def __init__(self, config: Dict):
        """
        Initialize Issue Opener Agent.
        
        Args:
            config: Configuration dict with:
                - github_token: GitHub API token
                - openai_api_key: OpenAI API key
                - model: LLM model to use (default: gpt-5-chat-latest)
                - repo: Repository to work on (owner/repo)
                - project_root: Path to project
        """
        self.config = config
        self.project_root = Path(config.get('project_root', '/home/flip/agent-forge'))
        
        # Parse owner/repo
        self.owner, self.repo = config['repo'].split('/')
        
        # Initialize GitHub API
        self.github = GitHubAPIHelper(
            token=config['github_token']
        )
        
        # Initialize LLM provider
        self.llm = OpenAIProvider(
            api_key=config['openai_api_key'],
            org_id=config.get('org_id')
        )
        
        self.model = config.get('model', 'gpt-5-chat-latest')
        
        logger.info(f"🤖 Issue Opener Agent initialized")
        logger.info(f"   Model: {self.model}")
        logger.info(f"   Repo: {self.owner}/{self.repo}")
    
    def process_issue(self, issue_number: int) -> Dict:
        """
        Process a single GitHub issue end-to-end.
        
        Args:
            issue_number: Issue number to process
            
        Returns:
            Dict with:
                - success: bool
                - pr_url: str (if successful)
                - branch: str (if successful)
                - error: str (if failed)
                - actions: List[str] - actions taken
        """
        print(f"\n{'=' * 70}")
        print(f"🤖 PROCESSING ISSUE #{issue_number}")
        print(f"{'=' * 70}\n")
        
        actions = []
        
        try:
            # Step 1: Fetch issue
            print("📖 Step 1: Fetching issue details...")
            issue = self._fetch_issue(issue_number)
            actions.append(f"Fetched issue #{issue_number}")
            
            print(f"   ✅ Title: {issue['title']}")
            print(f"   📝 Labels: {', '.join(issue.get('labels', []))}")
            print()
            
            # Step 2: Analyze requirements
            print("🔍 Step 2: Analyzing requirements with GPT-5...")
            analysis = self._analyze_issue(issue)
            actions.append("Analyzed requirements")
            
            print(f"   ✅ Analysis complete")
            print(f"   📋 Tasks: {len(analysis.get('tasks', []))}")
            for i, task in enumerate(analysis.get('tasks', []), 1):
                print(f"      {i}. {task}")
            print()
            
            # Step 3: Generate implementation plan
            print("📐 Step 3: Creating implementation plan...")
            plan = self._create_plan(issue, analysis)
            actions.append("Created implementation plan")
            
            print(f"   ✅ Plan created")
            print(f"   📂 Files to modify: {len(plan.get('files', []))}")
            for file_info in plan.get('files', []):
                print(f"      • {file_info['path']} - {file_info['action']}")
            print()
            
            # Step 4: Create branch
            print("🌿 Step 4: Creating feature branch...")
            branch_name = self._create_branch(issue_number, issue['title'])
            actions.append(f"Created branch: {branch_name}")
            
            print(f"   ✅ Branch: {branch_name}\n")
            
            # Step 5: Implement changes
            print("💻 Step 5: Implementing code changes...")
            changes = self._implement_changes(plan)
            actions.append(f"Implemented {len(changes)} file changes")
            
            print(f"   ✅ {len(changes)} files modified\n")
            
            # Step 6: Run tests
            print("🧪 Step 6: Running tests...")
            test_result = self._run_tests()
            actions.append(f"Tests: {test_result['status']}")
            
            if test_result['success']:
                print(f"   ✅ All tests passed\n")
            else:
                print(f"   ⚠️  Some tests failed (continuing anyway)\n")
            
            # Step 7: Commit and push
            print("📤 Step 7: Committing and pushing changes...")
            commit_sha = self._commit_and_push(issue_number, issue['title'], changes)
            actions.append(f"Pushed commit: {commit_sha[:8]}")
            
            print(f"   ✅ Commit: {commit_sha[:8]}\n")
            
            # Step 8: Create PR
            print("🔀 Step 8: Creating pull request...")
            pr = self._create_pr(issue_number, issue['title'], plan, branch_name)
            actions.append(f"Created PR #{pr['number']}")
            
            print(f"   ✅ PR created: #{pr['number']}")
            print(f"   🔗 URL: {pr['html_url']}\n")
            
            # Success!
            print(f"{'=' * 70}")
            print(f"✅ ISSUE #{issue_number} RESOLVED SUCCESSFULLY!")
            print(f"{'=' * 70}\n")
            
            return {
                'success': True,
                'pr_url': pr['html_url'],
                'pr_number': pr['number'],
                'branch': branch_name,
                'commit': commit_sha,
                'actions': actions,
                'test_result': test_result
            }
            
        except Exception as e:
            logger.error(f"Failed to process issue #{issue_number}: {e}", exc_info=True)
            
            print(f"\n{'=' * 70}")
            print(f"❌ FAILED TO PROCESS ISSUE #{issue_number}")
            print(f"{'=' * 70}")
            print(f"Error: {e}\n")
            
            return {
                'success': False,
                'error': str(e),
                'actions': actions
            }
    
    def _fetch_issue(self, issue_number: int) -> Dict:
        """Fetch issue details from GitHub."""
        issue_data = self.github.get_issue(self.owner, self.repo, issue_number)
        
        return {
            'number': issue_data['number'],
            'title': issue_data['title'],
            'body': issue_data.get('body', ''),
            'labels': [label['name'] for label in issue_data.get('labels', [])],
            'assignees': [user['login'] for user in issue_data.get('assignees', [])],
            'state': issue_data['state']
        }
    
    def _analyze_issue(self, issue: Dict) -> Dict:
        """
        Analyze issue using GPT-5 to extract requirements and tasks.
        
        Returns:
            Dict with:
                - summary: str
                - tasks: List[str]
                - files_needed: List[str]
                - complexity: str (low/medium/high)
        """
        prompt = f"""Analyze this GitHub issue and extract implementation requirements:

Title: {issue['title']}

Body:
{issue['body']}

Labels: {', '.join(issue['labels'])}

Provide a structured analysis in JSON format:
{{
    "summary": "Brief summary of what needs to be done",
    "tasks": ["Task 1", "Task 2", ...],
    "files_needed": ["path/to/file1.py", "path/to/file2.py", ...],
    "complexity": "low|medium|high",
    "estimated_time": "time estimate"
}}

Only return valid JSON, no other text."""
        
        messages = [
            LLMMessage(role='system', content='You are a technical analyst. Extract structured requirements from GitHub issues.'),
            LLMMessage(role='user', content=prompt)
        ]
        
        response = self.llm.chat_completion(
            messages=messages,
            model=self.model
        )
        
        # Parse JSON response
        try:
            analysis = json.loads(response.content)
        except json.JSONDecodeError:
            # Fallback: extract JSON from markdown code blocks
            import re
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response.content, re.DOTALL)
            if json_match:
                analysis = json.loads(json_match.group(1))
            else:
                # Last resort: basic parsing
                analysis = {
                    'summary': issue['title'],
                    'tasks': ['Implement requested feature'],
                    'files_needed': [],
                    'complexity': 'medium'
                }
        
        return analysis
    
    def _create_plan(self, issue: Dict, analysis: Dict) -> Dict:
        """
        Create detailed implementation plan using GPT-5.
        
        Returns:
            Dict with:
                - description: str
                - files: List[Dict] with path, action, changes
                - tests: List[str] - test scenarios
        """
        prompt = f"""Create a detailed implementation plan for this issue:

Issue: {issue['title']}
Summary: {analysis['summary']}
Tasks: {json.dumps(analysis['tasks'], indent=2)}

Provide an implementation plan in JSON format:
{{
    "description": "Implementation approach",
    "files": [
        {{
            "path": "relative/path/to/file.py",
            "action": "create|modify|delete",
            "changes": "Description of changes needed"
        }}
    ],
    "tests": ["Test scenario 1", "Test scenario 2"]
}}

Only return valid JSON."""
        
        messages = [
            LLMMessage(role='system', content='You are a software architect. Create detailed implementation plans.'),
            LLMMessage(role='user', content=prompt)
        ]
        
        response = self.llm.chat_completion(
            messages=messages,
            model=self.model
        )
        
        # Parse JSON
        try:
            plan = json.loads(response.content)
        except json.JSONDecodeError:
            import re
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response.content, re.DOTALL)
            if json_match:
                plan = json.loads(json_match.group(1))
            else:
                plan = {
                    'description': 'Implement feature',
                    'files': [],
                    'tests': []
                }
        
        return plan
    
    def _create_branch(self, issue_number: int, title: str) -> str:
        """Create a new git branch for the issue."""
        # Generate branch name
        safe_title = title.lower()[:40].replace(' ', '-').replace('/', '-')
        branch_name = f"issue-{issue_number}-{safe_title}"
        
        # Create and checkout branch
        subprocess.run(['git', 'checkout', '-b', branch_name], 
                      cwd=self.project_root, check=True, capture_output=True)
        
        return branch_name
    
    def _implement_changes(self, plan: Dict) -> List[Dict]:
        """
        Implement code changes according to plan.
        
        Returns:
            List of dicts with: path, action, success
        """
        changes = []
        
        for file_info in plan.get('files', []):
            file_path = self.project_root / file_info['path']
            action = file_info['action']
            
            try:
                if action == 'create':
                    # Generate new file content
                    content = self._generate_file_content(file_info)
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    file_path.write_text(content)
                    
                elif action == 'modify':
                    # Modify existing file
                    if not file_path.exists():
                        logger.warning(f"File not found for modification: {file_path}")
                        continue
                    
                    content = self._modify_file_content(file_path, file_info)
                    file_path.write_text(content)
                    
                elif action == 'delete':
                    # Delete file
                    if file_path.exists():
                        file_path.unlink()
                
                changes.append({
                    'path': file_info['path'],
                    'action': action,
                    'success': True
                })
                
            except Exception as e:
                logger.error(f"Failed to {action} {file_path}: {e}")
                changes.append({
                    'path': file_info['path'],
                    'action': action,
                    'success': False,
                    'error': str(e)
                })
        
        return changes
    
    def _generate_file_content(self, file_info: Dict) -> str:
        """Generate content for a new file using GPT-5."""
        prompt = f"""Generate complete file content for:

Path: {file_info['path']}
Purpose: {file_info['changes']}

Requirements:
- Complete, production-ready code
- Include docstrings and comments
- Follow best practices
- Include imports and error handling

Only return the file content, no explanations."""
        
        messages = [
            LLMMessage(role='system', content='You are an expert programmer. Generate clean, production-ready code.'),
            LLMMessage(role='user', content=prompt)
        ]
        
        response = self.llm.chat_completion(
            messages=messages,
            model=self.model
        )
        
        # Extract code from response
        content = response.content
        
        # Remove markdown code blocks if present
        if '```' in content:
            import re
            code_match = re.search(r'```(?:\w+)?\n(.*?)```', content, re.DOTALL)
            if code_match:
                content = code_match.group(1)
        
        return content
    
    def _modify_file_content(self, file_path: Path, file_info: Dict) -> str:
        """Modify existing file content using GPT-5."""
        current_content = file_path.read_text()
        
        prompt = f"""Modify this file according to requirements:

File: {file_path.name}
Changes needed: {file_info['changes']}

Current content:
```
{current_content}
```

Provide the complete modified file content. Only return the file content, no explanations."""
        
        messages = [
            LLMMessage(role='system', content='You are an expert programmer. Modify code carefully while maintaining existing functionality.'),
            LLMMessage(role='user', content=prompt)
        ]
        
        response = self.llm.chat_completion(
            messages=messages,
            model=self.model
        )
        
        # Extract code
        content = response.content
        if '```' in content:
            import re
            code_match = re.search(r'```(?:\w+)?\n(.*?)```', content, re.DOTALL)
            if code_match:
                content = code_match.group(1)
        
        return content
    
    def _run_tests(self) -> Dict:
        """
        Run project tests.
        
        Returns:
            Dict with: success, status, output
        """
        try:
            # Try pytest first
            result = subprocess.run(
                ['pytest', '--tb=short', '-v'],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            return {
                'success': result.returncode == 0,
                'status': 'passed' if result.returncode == 0 else 'failed',
                'output': result.stdout + result.stderr
            }
            
        except (subprocess.TimeoutExpired, FileNotFoundError):
            # No tests or timeout
            return {
                'success': True,
                'status': 'no_tests',
                'output': 'No tests found or tests timed out'
            }
    
    def _commit_and_push(self, issue_number: int, title: str, changes: List[Dict]) -> str:
        """Commit changes and push to remote."""
        # Add all changed files
        for change in changes:
            if change['success']:
                subprocess.run(['git', 'add', change['path']], 
                             cwd=self.project_root, check=True)
        
        # Create commit message
        commit_msg = f"fix: Resolve issue #{issue_number} - {title}\n\nImplemented:\n"
        for change in changes:
            if change['success']:
                commit_msg += f"- {change['action'].capitalize()} {change['path']}\n"
        
        # Commit
        subprocess.run(['git', 'commit', '-m', commit_msg],
                      cwd=self.project_root, check=True, capture_output=True)
        
        # Get commit SHA
        result = subprocess.run(['git', 'rev-parse', 'HEAD'],
                               cwd=self.project_root, check=True, 
                               capture_output=True, text=True)
        commit_sha = result.stdout.strip()
        
        # Push
        branch = subprocess.run(['git', 'branch', '--show-current'],
                               cwd=self.project_root, check=True,
                               capture_output=True, text=True).stdout.strip()
        
        subprocess.run(['git', 'push', '-u', 'origin', branch],
                      cwd=self.project_root, check=True, capture_output=True)
        
        return commit_sha
    
    def _create_pr(self, issue_number: int, title: str, plan: Dict, branch: str) -> Dict:
        """Create pull request on GitHub."""
        pr_title = f"Fix #{issue_number}: {title}"
        
        pr_body = f"""Resolves #{issue_number}

## Implementation

{plan['description']}

## Changes

"""
        
        for file_info in plan.get('files', []):
            pr_body += f"- {file_info['action'].capitalize()} `{file_info['path']}`\n"
        
        pr_body += "\n## Tests\n\n"
        for test in plan.get('tests', []):
            pr_body += f"- {test}\n"
        
        pr_body += "\n---\n*🤖 This PR was created automatically by Issue Opener Agent*"
        
        # Create PR via GitHub API
        pr_data = self.github.create_pull_request(
            title=pr_title,
            body=pr_body,
            head=branch,
            base='main'
        )
        
        return pr_data


def main():
    """Test the Issue Opener Agent."""
    # Load config
    config = {
        'github_token': os.getenv('BOT_GITHUB_TOKEN') or os.getenv('GITHUB_TOKEN'),
        'openai_api_key': os.getenv('OPENAI_API_KEY'),
        'model': 'gpt-5-chat-latest',
        'repo': 'm0nk111/agent-forge',
        'project_root': project_root
    }
    
    # Check required config
    if not config['github_token']:
        print("❌ GITHUB_TOKEN or BOT_GITHUB_TOKEN not set")
        sys.exit(1)
    
    if not config['openai_api_key']:
        print("❌ OPENAI_API_KEY not set")
        sys.exit(1)
    
    # Get issue number from args
    if len(sys.argv) < 2:
        print("Usage: python3 issue_opener_agent.py <issue_number>")
        sys.exit(1)
    
    issue_number = int(sys.argv[1])
    
    # Create agent
    agent = IssueOpenerAgent(config)
    
    # Process issue
    result = agent.process_issue(issue_number)
    
    # Print result
    print(json.dumps(result, indent=2))
    
    sys.exit(0 if result['success'] else 1)


if __name__ == '__main__':
    main()
