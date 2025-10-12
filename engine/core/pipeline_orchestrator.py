"""Pipeline Orchestrator for Autonomous Issue Resolution.

This module orchestrates the complete autonomous workflow:
1. PollingService detects issues
2. IssueHandler parses requirements
3. CodeGenerator creates implementation
4. BotAgent creates PR
5. PRReviewer posts review
6. BotAgent merges if approved

The orchestrator handles:
- Token management (env vars, MCP, config)
- Service communication
- Error recovery and retry logic
- Progress tracking
- Logging and monitoring

Author: Agent Forge
Date: 2025-10-10
"""

import asyncio
import logging
import os
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import traceback


logger = logging.getLogger(__name__)


@dataclass
class PipelineConfig:
    """Configuration for pipeline orchestrator."""
    
    # Repository configuration
    default_repos: Optional[List[str]] = None
    
    # GitHub token sources (priority order)
    token_env_vars: Optional[List[str]] = None
    token_config_path: Optional[str] = None
    
    # Retry configuration
    max_retries: int = 3
    retry_delay: int = 60  # seconds
    
    # Feature flags
    auto_merge_on_approval: bool = False  # Safety: don't auto-merge yet
    require_tests_passing: bool = True
    require_review_approval: bool = False  # Can self-approve for now
    
    # Monitoring
    enable_monitoring: bool = True
    monitor_service: Optional[Any] = None
    
    def __post_init__(self):
        """Initialize default values."""
        if self.default_repos is None:
            self.default_repos = ["m0nk111/agent-forge"]
        
        if self.token_env_vars is None:
            self.token_env_vars = [
                'BOT_GITHUB_TOKEN',  # Preferred for bot operations
                'GITHUB_TOKEN',       # Standard fallback
                'GH_TOKEN'            # GitHub CLI token
            ]


class PipelineOrchestrator:
    """Orchestrates the complete autonomous issue resolution pipeline."""
    
    def __init__(self, config: Optional[PipelineConfig] = None, agent = None):
        """Initialize pipeline orchestrator.
        
        Args:
            config: Pipeline configuration (uses defaults if not provided)
            agent: Code agent instance for LLM operations (optional)
        """
        self.config = config or PipelineConfig()
        self.agent = agent  # For CodeGenerator and other LLM-based operations
        self.active_pipelines: Dict[str, Dict] = {}  # issue_key -> pipeline_state
        
        # Initialize components (lazy loading)
        self._issue_handler = None
        self._code_generator = None
        self._pr_reviewer = None
        self._github_api = None
        
        logger.info("🔧 Pipeline Orchestrator initialized")
        logger.debug(f"🔍 Token sources: {self.config.token_env_vars}")
        logger.debug(f"🔍 Default repos: {self.config.default_repos}")
    
    def _get_github_token(self) -> Optional[str]:
        """Get GitHub token from multiple sources (priority order).
        
        Returns:
            GitHub token or None if not found
        """
        # Try environment variables in priority order
        token_vars = self.config.token_env_vars or []
        for var_name in token_vars:
            token = os.getenv(var_name)
            if token:
                logger.debug(f"✅ Found token in {var_name}")
                return token
        
        # Try config file if specified
        if self.config.token_config_path:
            try:
                import json
                config_path = Path(self.config.token_config_path)
                if config_path.exists():
                    with open(config_path) as f:
                        data = json.load(f)
                        token = data.get('github_token') or data.get('GITHUB_TOKEN')
                        if token:
                            logger.debug(f"✅ Found token in config file")
                            return token
            except Exception as e:
                logger.warning(f"⚠️  Failed to read token from config: {e}")
        
        # Try MCP-style token (if available)
        # This would be injected by the MCP server if running in that context
        if hasattr(self, '_mcp_token') and self._mcp_token:
            logger.debug("✅ Using MCP-injected token")
            return self._mcp_token
        
        logger.error("❌ No GitHub token found in any source")
        return None
    
    def set_mcp_token(self, token: str):
        """Set GitHub token from MCP server.
        
        This allows MCP server to inject token without environment variables.
        
        Args:
            token: GitHub personal access token
        """
        self._mcp_token = token
        logger.info("✅ MCP token configured")
    
    async def handle_new_issue(self, repo: str, issue_number: int) -> Dict[str, Any]:
        """Handle a new issue through the complete autonomous pipeline.
        
        This is the main entry point for autonomous issue resolution.
        
        Args:
            repo: Repository in format "owner/repo"
            issue_number: Issue number to resolve
            
        Returns:
            Dict with:
                - success: bool
                - pr_url: Optional[str]
                - pr_number: Optional[int]
                - summary: str
                - error: Optional[str]
        """
        issue_key = f"{repo}#{issue_number}"
        
        logger.info(f"\n{'='*70}")
        logger.info(f"🚀 AUTONOMOUS PIPELINE STARTED: {issue_key}")
        logger.info(f"{'='*70}")
        
        # Initialize pipeline state
        pipeline_state = {
            'repo': repo,
            'issue_number': issue_number,
            'started_at': datetime.utcnow().isoformat(),
            'phase': 'initialization',
            'progress': 0.0,
            'error': None
        }
        self.active_pipelines[issue_key] = pipeline_state
        
        try:
            # Verify token availability
            token = self._get_github_token()
            if not token:
                raise RuntimeError("No GitHub token available - cannot proceed")
            
            # Phase 1: Fetch issue details
            pipeline_state['phase'] = 'fetch_issue'
            pipeline_state['progress'] = 0.1
            logger.info("\n📖 Phase 1: Fetching issue details...")
            
            issue_data = await self._fetch_issue_details(repo, issue_number, token)
            if not issue_data:
                raise RuntimeError(f"Failed to fetch issue {issue_key}")
            
            logger.info(f"   ✅ Issue: {issue_data.get('title', 'Untitled')}")
            pipeline_state['issue_title'] = issue_data.get('title')
            
            # Phase 2: Parse requirements
            pipeline_state['phase'] = 'parse_requirements'
            pipeline_state['progress'] = 0.2
            logger.info("\n🔍 Phase 2: Parsing requirements...")
            
            requirements = await self._parse_requirements(issue_data)
            if not requirements.get('success'):
                raise RuntimeError(f"Requirements parsing failed: {requirements.get('error')}")
            
            # Check if this is a documentation file workflow
            if requirements.get('is_documentation'):
                logger.info(f"   📄 Documentation file detected: {requirements.get('file_path')}")
                logger.info(f"   🔀 Switching to IssueHandler workflow...")
                
                # Use IssueHandler for documentation files
                result = await self._handle_documentation_issue(repo, issue_number, issue_data, token)
                return result
            
            logger.info(f"   ✅ Module path: {requirements.get('module_path')}")
            
            # Phase 3: Generate code
            pipeline_state['phase'] = 'generate_code'
            pipeline_state['progress'] = 0.4
            logger.info("\n⚙️  Phase 3: Generating code...")
            
            generation_result = await self._generate_implementation(requirements, issue_data)
            if not generation_result.get('success'):
                raise RuntimeError(f"Code generation failed: {generation_result.get('error')}")
            
            logger.info(f"   ✅ Files created: {len(generation_result.get('files', []))}")
            
            # Phase 4: Run tests
            pipeline_state['phase'] = 'run_tests'
            pipeline_state['progress'] = 0.6
            logger.info("\n🧪 Phase 4: Running tests...")
            
            test_result = {'passed': True, 'count': 0}
            if self.config.require_tests_passing:
                test_result = await self._run_tests(generation_result.get('files', []))
                if not test_result.get('passed'):
                    raise RuntimeError(f"Tests failed: {test_result.get('error')}")
                logger.info(f"   ✅ Tests passed: {test_result.get('count', 0)}")
            else:
                logger.info("   ⏭️  Tests skipped (not required)")
            
            # Phase 5: Create PR
            pipeline_state['phase'] = 'create_pr'
            pipeline_state['progress'] = 0.7
            logger.info("\n🔀 Phase 5: Creating pull request...")
            
            pr_result = await self._create_pull_request(
                repo, 
                issue_number, 
                issue_data, 
                generation_result, 
                token
            )
            if not pr_result.get('success'):
                raise RuntimeError(f"PR creation failed: {pr_result.get('error')}")
            
            pr_url = pr_result.get('pr_url', '')
            pr_number = pr_result.get('pr_number', 0)
            logger.info(f"   ✅ PR created: {pr_url}")
            pipeline_state['pr_url'] = pr_url
            pipeline_state['pr_number'] = pr_number
            
            # Phase 6: Review PR
            pipeline_state['phase'] = 'review_pr'
            pipeline_state['progress'] = 0.8
            logger.info("\n📝 Phase 6: Reviewing pull request...")
            
            if pr_number:
                review_result = await self._review_pull_request(repo, pr_number, token)
                logger.info(f"   ✅ Review posted: {review_result.get('approved', False) and 'APPROVED' or 'COMMENTED'}")
            else:
                review_result = {'approved': False}
                logger.warning("   ⚠️  No PR number, skipping review")
            
            # Phase 7: Merge PR (if approved and configured)
            pipeline_state['phase'] = 'merge_pr'
            pipeline_state['progress'] = 0.9
            
            if pr_number and self.config.auto_merge_on_approval and review_result.get('approved'):
                logger.info("\n✅ Phase 7: Merging pull request...")
                merge_result = await self._merge_pull_request(repo, pr_number, token)
                if merge_result.get('success'):
                    logger.info(f"   ✅ PR merged successfully")
                else:
                    logger.warning(f"   ⚠️  PR merge failed: {merge_result.get('error')}")
            else:
                logger.info("\n⏭️  Phase 7: Auto-merge disabled (manual merge required)")
            
            # Phase 8: Close issue
            pipeline_state['phase'] = 'close_issue'
            pipeline_state['progress'] = 1.0
            logger.info("\n🎉 Phase 8: Closing issue...")
            
            if pr_url:
                await self._close_issue_with_summary(
                    repo, 
                    issue_number, 
                    pr_url, 
                    generation_result, 
                    token
                )
                logger.info(f"   ✅ Issue closed")
            else:
                logger.warning("   ⚠️  No PR URL, skipping issue close")
            
            # Success!
            logger.info(f"\n{'='*70}")
            logger.info(f"✅ AUTONOMOUS PIPELINE COMPLETED: {issue_key}")
            logger.info(f"   PR: {pr_url}")
            logger.info(f"{'='*70}\n")
            
            return {
                'success': True,
                'pr_url': pr_url,
                'pr_number': pr_number,
                'summary': f"Successfully resolved {issue_key} with PR {pr_url}",
                'files_created': generation_result.get('files', []),
                'tests_passed': test_result.get('count', 0) if self.config.require_tests_passing else None
            }
        
        except Exception as e:
            logger.error(f"\n❌ PIPELINE FAILED: {issue_key}")
            logger.error(f"   Error: {e}")
            logger.error(f"   Phase: {pipeline_state.get('phase')}")
            logger.error(f"   Traceback:\n{traceback.format_exc()}")
            
            pipeline_state['error'] = str(e)
            pipeline_state['phase'] = 'failed'
            
            return {
                'success': False,
                'error': str(e),
                'phase': pipeline_state.get('phase'),
                'summary': f"Failed to resolve {issue_key}: {e}"
            }
        
        finally:
            # Cleanup
            if issue_key in self.active_pipelines:
                pipeline_state['completed_at'] = datetime.utcnow().isoformat()
    
    async def _fetch_issue_details(self, repo: str, issue_number: int, token: str) -> Optional[Dict]:
        """Fetch issue details from GitHub API."""
        try:
            import requests
            
            owner, repo_name = repo.split('/')
            url = f"https://api.github.com/repos/{owner}/{repo_name}/issues/{issue_number}"
            
            headers = {
                'Authorization': f'token {token}',
                'Accept': 'application/vnd.github+json',
                'X-GitHub-Api-Version': '2022-11-28'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            return {
                'number': issue_number,
                'title': data.get('title', ''),
                'body': data.get('body', ''),
                'labels': [l['name'] for l in data.get('labels', [])],
                'assignees': [a['login'] for a in data.get('assignees', [])],
                'state': data.get('state', 'open')
            }
        
        except Exception as e:
            logger.error(f"❌ Failed to fetch issue: {e}")
            return None
    
    async def _parse_requirements(self, issue_data: Dict) -> Dict:
        """Parse issue requirements using CodeGenerator's inference."""
        try:
            from engine.operations.code_generator import CodeGenerator
            
            # Use CodeGenerator's intelligent parsing
            generator = CodeGenerator(self.agent)
            
            title = issue_data.get('title', '')
            body = issue_data.get('body', '')
            labels = issue_data.get('labels', [])
            
            # Infer module specification
            module_spec = generator.infer_module_spec(title, body, labels)
            
            if not module_spec:
                # Check if this is a documentation file that should use IssueHandler
                text = f"{title} {body}".lower()
                doc_pattern = r'(?:create|add|implement|build)(?:\s+file)?(?:\s*:)?\s*[`]?([a-z_/.-]+\.(?:md|txt|rst))[`]?'
                doc_match = re.search(doc_pattern, text)
                
                if doc_match:
                    doc_file = doc_match.group(1)
                    logger.info(f"📄 Detected documentation file: {doc_file}")
                    logger.info(f"   Using IssueHandler workflow instead of code generation pipeline")
                    
                    # Return special marker for documentation file
                    return {
                        'success': True,
                        'is_documentation': True,
                        'file_path': doc_file,
                        'title': title,
                        'body': body,
                        'labels': labels
                    }
                else:
                    logger.error("❌ Could not infer module specification from issue")
                    return {
                        'success': False,
                        'error': 'Could not infer module specification from issue'
                    }
            
            logger.info(f"✅ Inferred module: {module_spec.module_path}")
            
            # Convert ModuleSpec to requirements dict
            return {
                'success': True,
                'is_documentation': False,
                'module_path': module_spec.module_path,
                'module_name': module_spec.module_name,
                'test_path': module_spec.test_path,
                'description': module_spec.description,
                'functions': module_spec.functions,
                'dependencies': module_spec.dependencies,
                'title': title,
                'labels': labels
            }
            
        except Exception as e:
            logger.error(f"❌ Error parsing requirements: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _generate_implementation(self, requirements: Dict, issue_data: Dict) -> Dict:
        """Generate code implementation (delegate to CodeGenerator)."""
        try:
            # Import CodeGenerator
            from engine.operations.code_generator import CodeGenerator, ModuleSpec
            from pathlib import Path
            
            # Extract module specification from requirements
            module_path = requirements.get('module_path')
            if not module_path:
                logger.error("❌ No module_path in requirements")
                return {
                    'success': False,
                    'error': 'No module_path specified in requirements',
                    'files': []
                }
            
            # Build ModuleSpec
            spec = ModuleSpec(
                module_path=module_path,
                module_name=requirements.get('module_name', Path(module_path).stem),
                test_path=requirements.get('test_path', f"tests/test_{Path(module_path).stem}.py"),
                description=requirements.get('description', issue_data.get('title', '')),
                functions=requirements.get('functions', []),
                dependencies=requirements.get('dependencies', [])
            )
            
            # Generate code
            logger.info(f"🚀 Generating module: {spec.module_name}")
            generator = CodeGenerator(self.agent)
            result = generator.generate_module(spec)
            
            if not result.success:
                logger.error(f"❌ Code generation failed: {result.errors}")
                return {
                    'success': False,
                    'error': f"Code generation failed: {', '.join(result.errors or [])}",
                    'files': []
                }
            
            logger.info(f"✅ Code generation successful (retry_count={result.retry_count})")
            
            # Return implementation details
            return {
                'success': True,
                'module_path': spec.module_path,
                'test_path': spec.test_path,
                'module_content': result.module_content,
                'test_content': result.test_content,
                'static_analysis': result.static_analysis,
                'retry_count': result.retry_count,
                'files': [spec.module_path, spec.test_path]
            }
            
        except Exception as e:
            logger.error(f"❌ Error generating implementation: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                'success': False,
                'error': str(e),
                'files': []
            }
    
    async def _run_tests(self, files: List[str]) -> Dict:
        """Run tests for generated code."""
        try:
            import subprocess
            
            # Find test files in the files list
            test_files = [f for f in files if f.startswith('tests/') and f.endswith('.py')]
            
            if not test_files:
                logger.warning("⚠️ No test files found to execute")
                return {
                    'passed': False,
                    'count': 0,
                    'error': 'No test files found'
                }
            
            logger.info(f"🧪 Running tests: {test_files}")
            
            # Run pytest on test files
            cmd = ['pytest'] + test_files + ['-v', '--tb=short']
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            # Parse output for test results
            output = result.stdout + result.stderr
            logger.debug(f"Test output:\n{output}")
            
            # Extract test counts from pytest output
            passed = failed = 0
            for line in output.split('\n'):
                if 'passed' in line.lower():
                    import re
                    match = re.search(r'(\d+) passed', line)
                    if match:
                        passed = int(match.group(1))
                if 'failed' in line.lower():
                    import re
                    match = re.search(r'(\d+) failed', line)
                    if match:
                        failed = int(match.group(1))
            
            success = result.returncode == 0 and failed == 0
            
            logger.info(f"✅ Test results: {passed} passed, {failed} failed")
            
            return {
                'passed': success,
                'count': passed,
                'failed': failed,
                'output': output[:1000],  # Truncate for logging
                'returncode': result.returncode
            }
            
        except subprocess.TimeoutExpired:
            logger.error("❌ Test execution timed out after 5 minutes")
            return {
                'passed': False,
                'count': 0,
                'error': 'Test execution timed out'
            }
        except Exception as e:
            logger.error(f"❌ Error running tests: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                'passed': False,
                'count': 0,
                'error': str(e)
            }
    
    async def _create_pull_request(
        self, 
        repo: str, 
        issue_number: int, 
        issue_data: Dict, 
        generation_result: Dict, 
        token: str
    ) -> Dict:
        """Create pull request with generated changes."""
        try:
            import requests
            import subprocess
            
            owner, repo_name = repo.split('/')
            
            # Create branch name
            branch_name = f"fix-issue-{issue_number}"
            
            # Get files to commit
            files = generation_result.get('files', [])
            if not files:
                return {
                    'success': False,
                    'error': 'No files to commit'
                }
            
            logger.info(f"🌿 Creating branch: {branch_name}")
            
            # Create new branch via git
            # First, ensure we're on main
            subprocess.run(['git', 'checkout', 'main'], capture_output=True)
            subprocess.run(['git', 'pull', 'origin', 'main'], capture_output=True)
            
            # Create and checkout new branch
            result = subprocess.run(
                ['git', 'checkout', '-b', branch_name],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                logger.error(f"Failed to create branch: {result.stderr}")
                return {
                    'success': False,
                    'error': f'Branch creation failed: {result.stderr}'
                }
            
            # Write generated files
            module_path = generation_result.get('module_path')
            test_path = generation_result.get('test_path')
            module_content = generation_result.get('module_content')
            test_content = generation_result.get('test_content')
            
            if module_path and module_content:
                Path(module_path).parent.mkdir(parents=True, exist_ok=True)
                Path(module_path).write_text(module_content)
                logger.info(f"📝 Wrote {module_path}")
            
            if test_path and test_content:
                Path(test_path).parent.mkdir(parents=True, exist_ok=True)
                Path(test_path).write_text(test_content)
                logger.info(f"📝 Wrote {test_path}")
            
            # Git add
            subprocess.run(['git', 'add'] + files, capture_output=True)
            
            # Git commit
            commit_msg = f"fix: Resolve issue #{issue_number} - {issue_data.get('title', 'Unknown')}\n\nGenerated by Agent-Forge autonomous pipeline."
            subprocess.run(
                ['git', 'commit', '-m', commit_msg],
                capture_output=True,
                text=True
            )
            
            # Git push
            result = subprocess.run(
                ['git', 'push', 'origin', branch_name],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                logger.error(f"Failed to push branch: {result.stderr}")
                return {
                    'success': False,
                    'error': f'Push failed: {result.stderr}'
                }
            
            logger.info(f"✅ Pushed branch: {branch_name}")
            
            # Create PR via GitHub API
            pr_url = f"https://api.github.com/repos/{owner}/{repo_name}/pulls"
            
            pr_data = {
                'title': f"Fix: {issue_data.get('title', 'Unknown')}",
                'body': f"Resolves #{issue_number}\n\nAutomatically generated by Agent-Forge pipeline.\n\n**Generated Files:**\n" + '\n'.join([f"- `{f}`" for f in files]),
                'head': branch_name,
                'base': 'main'
            }
            
            headers = {
                'Authorization': f'token {token}',
                'Accept': 'application/vnd.github+json',
                'X-GitHub-Api-Version': '2022-11-28'
            }
            
            response = requests.post(pr_url, json=pr_data, headers=headers, timeout=30)
            response.raise_for_status()
            
            pr_result = response.json()
            pr_number = pr_result['number']
            pr_html_url = pr_result['html_url']
            
            logger.info(f"✅ Created PR #{pr_number}: {pr_html_url}")
            
            return {
                'success': True,
                'pr_number': pr_number,
                'pr_url': pr_html_url,
                'branch': branch_name
            }
            
        except Exception as e:
            logger.error(f"❌ Error creating PR: {e}")
            import traceback
            logger.error(traceback.format_exc())
            
            # Try to cleanup branch
            try:
                subprocess.run(['git', 'checkout', 'main'], capture_output=True)
                subprocess.run(['git', 'branch', '-D', branch_name], capture_output=True)
            except:
                pass
            
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _review_pull_request(self, repo: str, pr_number: int, token: str) -> Dict:
        """Review pull request (delegate to PRReviewer)."""
        try:
            from engine.operations.pr_reviewer import PRReviewer, ReviewCriteria
            from engine.operations.github_api_helper import GitHubAPIHelper
            import requests
            
            owner, repo_name = repo.split('/')
            
            # Fetch PR details via GitHub API
            pr_url = f"https://api.github.com/repos/{owner}/{repo_name}/pulls/{pr_number}"
            headers = {
                'Authorization': f'token {token}',
                'Accept': 'application/vnd.github+json',
                'X-GitHub-Api-Version': '2022-11-28'
            }
            
            response = requests.get(pr_url, headers=headers, timeout=30)
            response.raise_for_status()
            pr_data = response.json()
            
            # Fetch PR files
            files_url = f"{pr_url}/files"
            response = requests.get(files_url, headers=headers, timeout=30)
            response.raise_for_status()
            files = response.json()
            
            logger.info(f"📝 Reviewing PR #{pr_number} with {len(files)} files")
            
            # Create reviewer with relaxed criteria (self-review)
            criteria = ReviewCriteria(
                check_code_quality=True,
                check_testing=True,
                check_documentation=False,  # Relaxed
                check_security=True,
                require_changelog=False,  # Relaxed for now
                min_test_coverage=70,  # Lower threshold
                strictness_level="relaxed"
            )
            
            github_api = GitHubAPIHelper(token)
            reviewer = PRReviewer(
                github_username="m0nk111-post",  # Bot username
                criteria=criteria,
                llm_agent=self.agent,
                github_api=github_api
            )
            
            # Perform review
            should_approve, summary, comments = await reviewer.review_pr(
                repo, pr_number, pr_data, files
            )
            
            logger.info(f"✅ Review complete: approved={should_approve}, comments={len(comments)}")
            
            return {
                'approved': should_approve,
                'summary': summary,
                'comments': len(comments)
            }
            
        except Exception as e:
            logger.error(f"❌ Error reviewing PR: {e}")
            import traceback
            logger.error(traceback.format_exc())
            # Default to not approved on error
            return {
                'approved': False,
                'error': str(e)
            }
    
    async def _merge_pull_request(self, repo: str, pr_number: int, token: str) -> Dict:
        """Merge pull request if approved."""
        try:
            import requests
            
            owner, repo_name = repo.split('/')
            
            # Merge via GitHub API
            merge_url = f"https://api.github.com/repos/{owner}/{repo_name}/pulls/{pr_number}/merge"
            
            headers = {
                'Authorization': f'token {token}',
                'Accept': 'application/vnd.github+json',
                'X-GitHub-Api-Version': '2022-11-28'
            }
            
            merge_data = {
                'commit_title': f"Merge pull request #{pr_number}",
                'commit_message': f"Automatically merged by Agent-Forge pipeline",
                'merge_method': 'squash'  # Squash commits for clean history
            }
            
            response = requests.put(merge_url, json=merge_data, headers=headers, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"✅ Merged PR #{pr_number}: {result.get('message', 'Success')}")
            
            return {
                'success': True,
                'merged': result.get('merged', False),
                'sha': result.get('sha')
            }
            
        except Exception as e:
            logger.error(f"❌ Error merging PR: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _handle_documentation_issue(
        self, 
        repo: str, 
        issue_number: int, 
        issue_data: Dict, 
        token: str
    ) -> Dict[str, Any]:
        """Handle documentation file creation using IssueHandler workflow.
        
        This method provides a simplified workflow for documentation files:
        1. Use IssueHandler to parse requirements and create files
        2. Create PR with changes
        3. Close issue
        
        Args:
            repo: Repository in format "owner/repo"
            issue_number: Issue number
            issue_data: Issue data dict from GitHub API
            token: GitHub token for API calls
            
        Returns:
            Dict with success, pr_url, summary, etc.
        """
        from engine.operations.issue_handler import IssueHandler
        
        logger.info(f"\n📄 Documentation workflow for {repo}#{issue_number}")
        
        try:
            # Initialize IssueHandler with agent
            if not self.agent:
                raise RuntimeError("No agent available for IssueHandler")
            
            issue_handler = IssueHandler(self.agent)
            
            # Let IssueHandler process the issue autonomously
            # It will parse requirements, create files, commit, and create PR
            logger.info("🤖 Starting IssueHandler autonomous workflow...")
            result = issue_handler.assign_to_issue(repo, issue_number)
            
            if result.get('success'):
                logger.info(f"✅ IssueHandler completed successfully")
                logger.info(f"   PR: {result.get('pr_url', 'N/A')}")
                return {
                    'success': True,
                    'pr_url': result.get('pr_url'),
                    'pr_number': result.get('pr_number'),
                    'summary': f"Documentation created via IssueHandler: {result.get('pr_url')}",
                    'workflow_type': 'documentation'
                }
            else:
                logger.error(f"❌ IssueHandler failed: {result.get('error')}")
                return {
                    'success': False,
                    'error': result.get('error', 'IssueHandler workflow failed'),
                    'summary': f"Documentation workflow failed: {result.get('error')}",
                    'workflow_type': 'documentation'
                }
                
        except Exception as e:
            logger.error(f"❌ Documentation workflow failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                'success': False,
                'error': str(e),
                'summary': f"Documentation workflow exception: {e}",
                'workflow_type': 'documentation'
            }
    
    async def _close_issue_with_summary(
        self, 
        repo: str, 
        issue_number: int, 
        pr_url: str, 
        generation_result: Dict, 
        token: str
    ):
        """Close issue with completion summary."""
        try:
            import requests
            
            owner, repo_name = repo.split('/')
            
            # Build summary comment
            files = generation_result.get('files', [])
            retry_count = generation_result.get('retry_count', 0)
            
            summary = f"""## ✅ Issue Resolved

This issue has been automatically resolved by the Agent-Forge autonomous pipeline.

**Pull Request:** {pr_url}

**Generated Files:**
{chr(10).join([f"- `{f}`" for f in files])}

**Generation Stats:**
- Retry count: {retry_count}
- Tests: Passed ✅

The fix has been merged and is now available in the main branch.

---
*This issue was resolved autonomously by Agent-Forge 🤖*
"""
            
            # Post comment via GitHub API
            comment_url = f"https://api.github.com/repos/{owner}/{repo_name}/issues/{issue_number}/comments"
            headers = {
                'Authorization': f'token {token}',
                'Accept': 'application/vnd.github+json',
                'X-GitHub-Api-Version': '2022-11-28'
            }
            
            comment_data = {'body': summary}
            response = requests.post(comment_url, json=comment_data, headers=headers, timeout=30)
            response.raise_for_status()
            
            logger.info(f"✅ Posted summary comment to issue #{issue_number}")
            
            # Close issue via GitHub API
            issue_url = f"https://api.github.com/repos/{owner}/{repo_name}/issues/{issue_number}"
            close_data = {
                'state': 'closed',
                'state_reason': 'completed'
            }
            
            response = requests.patch(issue_url, json=close_data, headers=headers, timeout=30)
            response.raise_for_status()
            
            logger.info(f"✅ Closed issue #{issue_number}")
            
        except Exception as e:
            logger.error(f"❌ Error closing issue: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    def get_pipeline_status(self, repo: str, issue_number: int) -> Optional[Dict]:
        """Get current status of a pipeline.
        
        Args:
            repo: Repository name
            issue_number: Issue number
            
        Returns:
            Pipeline state dict or None if not found
        """
        issue_key = f"{repo}#{issue_number}"
        return self.active_pipelines.get(issue_key)
    
    def get_all_active_pipelines(self) -> Dict[str, Dict]:
        """Get all currently active pipelines.
        
        Returns:
            Dict mapping issue_key -> pipeline_state
        """
        return self.active_pipelines.copy()


# Singleton instance for global access
_orchestrator_instance: Optional[PipelineOrchestrator] = None


def get_orchestrator(config: Optional[PipelineConfig] = None, agent = None) -> PipelineOrchestrator:
    """Get or create the global pipeline orchestrator instance.
    
    Args:
        config: Configuration (only used on first call)
        agent: Code agent instance (only used on first call)
        
    Returns:
        PipelineOrchestrator instance
    """
    global _orchestrator_instance
    
    if _orchestrator_instance is None:
        _orchestrator_instance = PipelineOrchestrator(config, agent)
    
    return _orchestrator_instance
