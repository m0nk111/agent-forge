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
    
    def __init__(self, config: Optional[PipelineConfig] = None):
        """Initialize pipeline orchestrator.
        
        Args:
            config: Pipeline configuration (uses defaults if not provided)
        """
        self.config = config or PipelineConfig()
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
            logger.info(f"   ✅ Tasks identified: {len(requirements.get('tasks', []))}")
            
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
        """Parse issue requirements (delegate to IssueHandler)."""
        # TODO: Implement smart parsing using LLM
        # For now, extract basic info
        return {
            'title': issue_data.get('title', ''),
            'description': issue_data.get('body', ''),
            'tasks': [],  # Will be populated by IssueHandler
            'labels': issue_data.get('labels', [])
        }
    
    async def _generate_implementation(self, requirements: Dict, issue_data: Dict) -> Dict:
        """Generate code implementation (delegate to CodeGenerator)."""
        # TODO: Integrate with actual CodeGenerator
        logger.warning("⚠️  Code generation not yet fully integrated - placeholder")
        return {
            'success': False,
            'error': 'Code generation integration pending',
            'files': []
        }
    
    async def _run_tests(self, files: List[str]) -> Dict:
        """Run tests for generated code."""
        # TODO: Implement test execution
        logger.warning("⚠️  Test execution not yet implemented - placeholder")
        return {
            'passed': True,
            'count': 0
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
        # TODO: Integrate with GitHubAPIHelper or MCP
        logger.warning("⚠️  PR creation not yet integrated - placeholder")
        return {
            'success': False,
            'error': 'PR creation integration pending'
        }
    
    async def _review_pull_request(self, repo: str, pr_number: int, token: str) -> Dict:
        """Review pull request (delegate to PRReviewer)."""
        # TODO: Integrate with PRReviewer
        logger.warning("⚠️  PR review not yet integrated - placeholder")
        return {
            'approved': False
        }
    
    async def _merge_pull_request(self, repo: str, pr_number: int, token: str) -> Dict:
        """Merge pull request if approved."""
        # TODO: Implement merge logic
        logger.warning("⚠️  PR merge not yet implemented - placeholder")
        return {
            'success': False,
            'error': 'Merge not yet implemented'
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
        # TODO: Integrate with GitHubAPIHelper
        logger.warning("⚠️  Issue closing not yet integrated - placeholder")
    
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


def get_orchestrator(config: Optional[PipelineConfig] = None) -> PipelineOrchestrator:
    """Get or create the global pipeline orchestrator instance.
    
    Args:
        config: Configuration (only used on first call)
        
    Returns:
        PipelineOrchestrator instance
    """
    global _orchestrator_instance
    
    if _orchestrator_instance is None:
        _orchestrator_instance = PipelineOrchestrator(config)
    
    return _orchestrator_instance
