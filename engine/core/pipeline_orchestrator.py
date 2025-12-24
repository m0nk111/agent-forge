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
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import traceback


logger = logging.getLogger(__name__)


def _sanitize_patch(text: str) -> str:
    """Sanitize an LLM-produced patch into a plain unified diff.

    Keeps behavior minimal: strip markdown fences and any leading prose,
    then return only the content starting at the first `diff --git` header.
    """
    if not text:
        return ""

    cleaned = text.strip()

    # Strip common markdown code fences (```diff ... ``` or ``` ... ```)
    cleaned = cleaned.replace("```diff", "```")
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```[a-zA-Z0-9_-]*\n", "", cleaned)
        cleaned = re.sub(r"\n```\s*$", "", cleaned.strip())

    # Keep only the diff portion starting at the first diff header.
    idx = cleaned.find("diff --git")
    if idx != -1:
        cleaned = cleaned[idx:]

    cleaned = cleaned.strip()
    if not cleaned:
        return ""

    return cleaned + "\n"


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
    
    # Timeout configuration (prevent infinite loops)
    max_execution_time: int = 1800  # 30 minutes max per issue
    
    # Feature flags
    auto_merge_on_approval: bool = False  # Safety: don't auto-merge yet
    require_tests_passing: bool = True
    require_review_approval: bool = False  # Can self-approve for now
    enable_pr_review: bool = False  # Post automated PR reviews/comments
    
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


def _compose_pr_update_comment(
    *,
    event: str,
    repo: str,
    pr_number: int,
    fallback: str,
    extra_context: Optional[Dict[str, Any]] = None,
    must_include: Optional[List[str]] = None,
) -> str:
    """Best-effort helper to reduce scripted PR update comments."""
    try:
        from engine.operations.comment_composer import CommentComposer

        composer = CommentComposer()
        return composer.compose(
            event=event,
            context={
                "repo": repo,
                "pr_number": pr_number,
                **(extra_context or {}),
            },
            must_include_lines=must_include or [],
            fallback=fallback,
        )
    except Exception as e:
        logger.debug(f"🐛 PR update comment composer failed (event={event}): {e}")
        return fallback


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
        logger.info(f"   ⏱️  Max execution time: {self.config.max_execution_time}s")
        logger.info(f"{'='*70}")
        
        # Initialize pipeline state
        start_time = datetime.utcnow()
        pipeline_state = {
            'repo': repo,
            'issue_number': issue_number,
            'started_at': start_time.isoformat(),
            'phase': 'initialization',
            'progress': 0.0,
            'error': None
        }
        self.active_pipelines[issue_key] = pipeline_state
        
        # Helper function to check timeout
        def check_timeout():
            elapsed = (datetime.utcnow() - start_time).total_seconds()
            if elapsed > self.config.max_execution_time:
                raise TimeoutError(f"Pipeline exceeded max execution time of {self.config.max_execution_time}s (elapsed: {elapsed:.0f}s)")
        
        try:
            # Check timeout before each major phase
            check_timeout()
            
            # Verify token availability
            token = self._get_github_token()
            if not token:
                raise RuntimeError("No GitHub token available - cannot proceed")
            
            # Phase 1: Fetch issue details
            check_timeout()
            pipeline_state['phase'] = 'fetch_issue'
            pipeline_state['progress'] = 0.1
            logger.info("\n📖 Phase 1: Fetching issue details...")
            
            issue_data = await self._fetch_issue_details(repo, issue_number, token)
            if not issue_data:
                raise RuntimeError(f"Failed to fetch issue {issue_key}")
            
            logger.info(f"   ✅ Issue: {issue_data.get('title', 'Untitled')}")
            pipeline_state['issue_title'] = issue_data.get('title')
            
            # Phase 2: Parse requirements
            check_timeout()
            pipeline_state['phase'] = 'parse_requirements'
            pipeline_state['progress'] = 0.2
            logger.info("\n🔍 Phase 2: Parsing requirements...")
            
            requirements = await self._parse_requirements(issue_data)
            if not requirements.get('success'):
                raise RuntimeError(f"Requirements parsing failed: {requirements.get('error')}")
            
            # Check if this is a documentation file workflow
            # NOTE: Documentation issues MUST still go through the clone->branch->PR pipeline.
            # IssueHandler operates on the local workspace and can auto-close issues, which
            # violates the single-bot workflow contract.
            if requirements.get('is_documentation'):
                doc_path = requirements.get('file_path')
                logger.info(f"   📄 Documentation file detected: {doc_path}")
                logger.info("   🔀 Routing documentation issue through generic clone->PR workflow...")

                constraints = (
                    "DOCUMENTATION TASK CONSTRAINTS:\n"
                    f"- Only create/modify exactly ONE file: {doc_path}\n"
                    "- Do NOT create any other files\n"
                    "- Do NOT modify any non-doc files\n"
                    "- Keep changes minimal and directly tied to the issue\n"
                )

                result = await self._handle_generic_issue(
                    repo,
                    issue_number,
                    issue_data,
                    token,
                    extra_constraints=constraints,
                    require_tests=False,
                )
                return result

            # Generic workflow: issues that request changes across existing files
            # (e.g. UI tweaks, API endpoints, config updates) and cannot be mapped to
            # a single new module/test file.
            if requirements.get('is_generic_task'):
                logger.info("   🔁 Generic task detected (no module spec inferred)")
                result = await self._handle_generic_issue(repo, issue_number, issue_data, token)
                return result
            
            logger.info(f"   ✅ Module path: {requirements.get('module_path')}")
            
            # Phase 3: Generate code
            check_timeout()
            pipeline_state['phase'] = 'generate_code'
            pipeline_state['progress'] = 0.4
            logger.info("\n⚙️  Phase 3: Generating code...")
            
            generation_result = await self._generate_implementation(requirements, issue_data)
            if not generation_result.get('success'):
                raise RuntimeError(f"Code generation failed: {generation_result.get('error')}")
            
            logger.info(f"   ✅ Files created: {len(generation_result.get('files', []))}")
            
            # Phase 4: Run tests
            check_timeout()
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
            check_timeout()
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
            check_timeout()
            pipeline_state['phase'] = 'review_pr'
            pipeline_state['progress'] = 0.8
            logger.info("\n📝 Phase 6: Reviewing pull request...")

            review_result = {'approved': False}
            if not self.config.enable_pr_review:
                logger.info("   ⏭️  PR review disabled (enable_pr_review=false)")
            elif pr_number:
                review_result = await self._review_pull_request(repo, pr_number, token)
                logger.info(f"   ✅ Review posted: {review_result.get('approved', False) and 'APPROVED' or 'COMMENTED'}")
            else:
                logger.warning("   ⚠️  No PR number, skipping review")
            
            # Phase 7: Merge PR (if approved and configured)
            check_timeout()
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
            
            # Pipeline complete - issue will be closed automatically when PR is merged
            pipeline_state['phase'] = 'complete'
            pipeline_state['progress'] = 1.0
            logger.info("\n✅ Pipeline Complete!")
            logger.info(f"   📝 PR created: {pr_url}")
            logger.info(f"   ⏳ Issue #{issue_number} will close automatically after PR merge")
            
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
        
        except TimeoutError as e:
            logger.error(f"\n⏱️  PIPELINE TIMEOUT: {issue_key}")
            logger.error(f"   Error: {e}")
            logger.error(f"   Phase: {pipeline_state.get('phase')}")
            
            pipeline_state['error'] = str(e)
            pipeline_state['phase'] = 'timeout'
            
            # Post timeout comment to issue (if we have a token)
            try:
                token = self._get_github_token()
                if token:
                    from engine.operations.comment_composer import CommentComposer

                    composer = CommentComposer()
                    base = (
                        f"⏱️ **Pipeline Timeout**\n\n"
                        f"The autonomous pipeline exceeded the maximum execution time of {self.config.max_execution_time}s.\n\n"
                        f"**Last Phase:** {pipeline_state.get('phase')}\n\n"
                        "The issue will need to be reprocessed or handled manually."
                    )
                    body = composer.compose(
                        event="pipeline_timeout",
                        context={
                            "repo": repo,
                            "issue_number": issue_number,
                            "max_execution_time_seconds": self.config.max_execution_time,
                            "phase": pipeline_state.get('phase'),
                        },
                        must_include_lines=["⏱️ **Pipeline Timeout**"],
                        fallback=base,
                    )
                    await self._post_issue_comment(
                        repo, 
                        issue_number,
                        body,
                        token
                    )
            except Exception as comment_error:
                logger.warning(f"Failed to post timeout comment: {comment_error}")
            
            return {
                'success': False,
                'error': str(e),
                'phase': pipeline_state.get('phase'),
                'summary': f"Pipeline timeout for {issue_key} after {self.config.max_execution_time}s"
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

    async def _handle_generic_issue(
        self,
        repo: str,
        issue_number: int,
        issue_data: Dict,
        token: str,
        *,
        extra_constraints: Optional[str] = None,
        require_tests: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """Fallback handler for issues that require changes across existing files.

        Implementation strategy (optimized for local LLMs):
        - Clone repo to a temp workspace
        - Create a branch
        - PRIMARY: Ask LLM for JSON file operations (full file content)
        - FALLBACK: Ask for unified diff patch if JSON fails
        - Apply changes, run tests (optional), commit, push
        - Open PR
        """
        import subprocess
        import tempfile
        import shutil
        import requests
        from pathlib import Path

        owner, repo_name = repo.split('/')
        branch_name = f"fix-issue-{issue_number}"

        def _sanitize_patch(text: str) -> str:
            if not text:
                return ""
            # Strip common markdown fences
            cleaned = text.strip()
            cleaned = cleaned.replace("```diff", "```")
            if cleaned.startswith("```"):
                cleaned = cleaned.strip("`")
            # Keep only the diff portion starting at the first diff header
            idx = cleaned.find("diff --git")
            if idx != -1:
                cleaned = cleaned[idx:]
            return cleaned.strip() + "\n"

        def _extract_corrupt_line(err_text: str) -> Optional[int]:
            if not err_text:
                return None
            m = re.search(r"corrupt patch at line\s+(\d+)", err_text)
            if not m:
                return None
            try:
                return int(m.group(1))
            except Exception:
                return None

        def _patch_excerpt(text: str, around_line: Optional[int], radius: int = 12, max_lines: int = 120) -> str:
            lines = (text or "").splitlines()
            if not lines:
                return "(empty patch)"
            if not around_line or around_line <= 0:
                start = 0
                end = min(len(lines), max_lines)
            else:
                center = max(1, around_line) - 1
                start = max(0, center - radius)
                end = min(len(lines), center + radius + 1)
            excerpt_lines: List[str] = []
            for i in range(start, end):
                excerpt_lines.append(f"{i+1:04d}: {lines[i]}")
            if end - start > max_lines:
                excerpt_lines = excerpt_lines[:max_lines]
            return "\n".join(excerpt_lines)

        workspace = tempfile.mkdtemp(prefix=f"{repo_name}-generic-")
        logger.info(f"📁 Generic workspace: {workspace}")

        try:
            clone_url = f"https://{token}@github.com/{owner}/{repo_name}.git"
            clone_res = subprocess.run(
                ['git', 'clone', '--depth=1', clone_url, workspace],
                capture_output=True,
                text=True,
            )
            if clone_res.returncode != 0:
                return {'success': False, 'error': f"Clone failed: {clone_res.stderr.strip()}"}

            # Determine base branch (origin/HEAD)
            base_ref = 'main'
            head_ref_res = subprocess.run(
                ['git', 'symbolic-ref', 'refs/remotes/origin/HEAD'],
                cwd=workspace,
                capture_output=True,
                text=True,
            )
            if head_ref_res.returncode == 0:
                ref = (head_ref_res.stdout or '').strip()
                if ref.startswith('refs/remotes/origin/'):
                    base_ref = ref.split('refs/remotes/origin/', 1)[1]

            co_res = subprocess.run(
                ['git', 'checkout', '-b', branch_name],
                cwd=workspace,
                capture_output=True,
                text=True,
            )
            if co_res.returncode != 0:
                return {'success': False, 'error': f"Branch creation failed: {co_res.stderr.strip()}"}

            # Configure git identity (required for commits)
            subprocess.run(['git', 'config', 'user.email', 'agent-forge@example.com'], cwd=workspace, capture_output=True)
            subprocess.run(['git', 'config', 'user.name', 'Agent-Forge'], cwd=workspace, capture_output=True)

            # Build minimal context for LLM
            title = issue_data.get('title', '')
            body = issue_data.get('body', '')

            # Attempt to focus context on explicitly mentioned file paths
            text_blob = f"{title}\n\n{body}"
            mentioned_paths = set(re.findall(r"(?:^|[^A-Za-z0-9_])([A-Za-z0-9_./-]+\.(?:py|yml|yaml|md|html|js|ts|css|json|sh))(?:$|[^A-Za-z0-9_])", text_blob))
            mentioned_paths = {p.strip() for p in mentioned_paths if p.strip() and not p.strip().startswith('http')}

            # If the issue doesn't name any files, seed a small set of likely entrypoints.
            if not mentioned_paths:
                likely_paths = [
                    'README.md',
                    'frontend/index.html',
                    'frontend/config_ui.html',
                    'frontend/dashboard.html',
                    'api/config_routes.py',
                    'api/auth_routes.py',
                    'engine/runners/polling_service.py',
                    'engine/core/pipeline_orchestrator.py',
                    'config/agents/m0nk111-post.yaml',
                    'requirements.txt',
                ]
                for p in likely_paths:
                    full = Path(workspace) / p
                    if full.exists() and not full.is_dir():
                        mentioned_paths.add(p)

            file_snippets: List[str] = []
            for rel_path in list(mentioned_paths)[:10]:
                try:
                    full_path = Path(workspace) / rel_path
                    if not full_path.exists() or full_path.is_dir():
                        continue
                    content = full_path.read_text(errors='ignore')
                    if len(content) > 5000:
                        content = content[:5000] + "\n... (file truncated) ...\n"
                    file_snippets.append(f"FILE: {rel_path}\n" + content)
                except Exception:
                    continue

            # Provide a short file list to help navigation
            ls_res = subprocess.run(
                ['git', 'ls-files'],
                cwd=workspace,
                capture_output=True,
                text=True,
            )
            repo_files = (ls_res.stdout or '')
            repo_files_lines = repo_files.splitlines()
            if len(repo_files_lines) > 250:
                repo_files = "\n".join(repo_files_lines[:250]) + "\n... (file list truncated) ...\n"

            if not self.agent or not hasattr(self.agent, 'query_llm'):
                return {'success': False, 'error': 'No LLM agent available for generic issue handling'}

            # Helper: sanitize JSON from LLM output
            import json
            def _sanitize_json(text: str) -> str:
                cleaned = (text or '').strip()
                cleaned = cleaned.replace('```json', '```').replace('```', '')
                start = cleaned.find('[')
                if start == -1:
                    start = cleaned.find('{')
                if start != -1:
                    cleaned = cleaned[start:]
                return cleaned.strip()

            constraints_block = ""
            if extra_constraints:
                constraints_block = f"\n\n{extra_constraints.strip()}\n"

            file_context = "\n\n".join(file_snippets)
            apply_ok = False
            last_error = ""

            # ─────────────────────────────────────────────────────────────────────
            # PRIMARY STRATEGY: JSON file operations (more reliable for local LLMs)
            # ─────────────────────────────────────────────────────────────────────
            logger.info("🔧 Attempting JSON file operations (primary strategy)...")
            json_system = (
                "You are an autonomous coding assistant. Return ONLY valid JSON. No markdown fences. No explanation. "
                "Return a JSON array of file operations: "
                "[{\"action\":\"modify\"|\"create\"|\"delete\",\"path\":\"relative/path\",\"content\":\"...COMPLETE file content...\"}]. "
                "For 'modify' and 'create', include the ENTIRE file content, not just changes. "
                "For 'delete', omit content. "
                "Paths must be relative to repo root and must not contain '..'."
            )
            json_prompt = (
                f"Repository: {repo}\n"
                f"Issue #{issue_number}: {title}\n\n"
                "Issue body:\n"
                f"{body}\n\n"
                "Repository files (may be truncated):\n"
                f"{repo_files}\n\n"
                "Existing relevant files and contents:\n"
                f"{file_context}\n\n"
                "Create the minimal set of file operations to implement the issue. "
                "For any file you modify, include the COMPLETE updated file content."
                + constraints_block
            )
            raw_ops = self.agent.query_llm(json_prompt, system_prompt=json_system, stream=False) or ''
            ops_text = _sanitize_json(raw_ops)
            try:
                ops = json.loads(ops_text)
                if isinstance(ops, list) and ops and len(ops) <= 25:
                    for op in ops:
                        if not isinstance(op, dict):
                            continue
                        action = (op.get('action') or '').strip().lower()
                        rel_path = (op.get('path') or '').strip()
                        if not rel_path or rel_path.startswith('/') or '..' in rel_path:
                            continue
                        target = Path(workspace) / rel_path
                        if action in ('create', 'modify'):
                            content = op.get('content')
                            if not isinstance(content, str):
                                continue
                            target.parent.mkdir(parents=True, exist_ok=True)
                            target.write_text(content)
                            logger.info(f"📝 {action.title()}: {rel_path}")
                        elif action == 'delete':
                            try:
                                if target.exists() and not target.is_dir():
                                    target.unlink()
                                    logger.info(f"🗑️ Deleted: {rel_path}")
                            except Exception:
                                continue
                    # Check if changes were made
                    status_check = subprocess.run(['git', 'status', '--porcelain'], cwd=workspace, capture_output=True, text=True)
                    if (status_check.stdout or '').strip():
                        apply_ok = True
                        logger.info("✅ JSON file operations applied successfully")
                    else:
                        last_error = "JSON operations produced no changes"
                        logger.warning(f"⚠️ {last_error}")
                else:
                    last_error = f"Invalid JSON structure: got {'empty list' if not ops else f'{len(ops)} ops' if isinstance(ops, list) else type(ops).__name__}"
                    logger.warning(f"⚠️ {last_error}")
            except Exception as parse_error:
                last_error = f"JSON parse failed: {parse_error}"
                logger.warning(f"⚠️ {last_error}")

            # ─────────────────────────────────────────────────────────────────────
            # FALLBACK STRATEGY: Unified diff patch
            # ─────────────────────────────────────────────────────────────────────
            if not apply_ok:
                logger.info("🔧 Falling back to unified diff patch...")
                patch_system = (
                    "You are an autonomous coding assistant. Return ONLY a unified diff patch that can be applied with `git apply`. "
                    "Do not include explanations, markdown fences, or any text before/after the diff.\n\n"
                    "CORRECT FORMAT EXAMPLE:\n"
                    "diff --git a/path/to/file.py b/path/to/file.py\n"
                    "--- a/path/to/file.py\n"
                    "+++ b/path/to/file.py\n"
                    "@@ -10,3 +10,4 @@\n"
                    " existing line\n"
                    "-removed line\n"
                    "+added line\n"
                    " another existing line\n\n"
                    "CRITICAL RULES:\n"
                    "- Start with 'diff --git a/path b/path'\n"
                    "- Include '--- a/path' and '+++ b/path' headers\n"
                    "- Include @@ line number markers\n"
                    "- Lines starting with ' ' (space) are context (unchanged)\n"
                    "- Lines starting with '-' are removed\n"
                    "- Lines starting with '+' are added\n"
                    "- NO explanation text, NO markdown, ONLY the patch"
                )
                patch_prompt = (
                    f"Repository: {repo}\n"
                    f"Issue #{issue_number}: {title}\n\n"
                    "Issue body:\n"
                    f"{body}\n\n"
                    f"Base branch: {base_ref}\n"
                    f"Target branch: {branch_name}\n\n"
                    "Repository files (may be truncated):\n"
                    f"{repo_files}\n\n"
                    "Relevant file contents (may be truncated):\n"
                    + "\n\n".join(file_snippets)
                    + "\n\n"
                    "Produce a unified diff patch implementing the issue requirements."
                    + constraints_block
                )

                for attempt in range(3):  # 3 attempts for patch
                    raw_patch = self.agent.query_llm(patch_prompt, system_prompt=patch_system, stream=False) or ''
                    patch_text = _sanitize_patch(raw_patch)
                    if not patch_text or 'diff --git' not in patch_text:
                        last_error = "LLM did not return a valid unified diff patch"
                        logger.warning(f"⚠️ Patch attempt {attempt+1}/3: {last_error}")
                        continue

                    apply_res = subprocess.run(
                        ['git', 'apply', '--whitespace=nowarn', '-'],
                        cwd=workspace,
                        input=patch_text,
                        text=True,
                        capture_output=True,
                    )
                    if apply_res.returncode == 0:
                        apply_ok = True
                        logger.info("✅ Patch applied successfully")
                        break

                    err = (apply_res.stderr or '').strip()
                    last_error = err
                    logger.warning(f"⚠️ Patch attempt {attempt+1}/3 failed: {err}")
                    if attempt < 2:
                        corrupt_line = _extract_corrupt_line(err)
                        excerpt = _patch_excerpt(patch_text, corrupt_line)
                        patch_prompt = (
                            patch_prompt
                            + f"\n\nPrevious patch failed with error:\n{err}\n\n"
                            + f"Patch excerpt (with line numbers):\n{excerpt}\n\n"
                            + "Return a corrected unified diff patch ONLY."
                        )

            if not apply_ok:
                return {'success': False, 'error': f"Both strategies failed. Last error: {last_error}"}

            status_res = subprocess.run(['git', 'status', '--porcelain'], cwd=workspace, capture_output=True, text=True)
            if not (status_res.stdout or '').strip():
                return {'success': False, 'error': 'Changes applied but produced no git diff'}

            tests_required = self.config.require_tests_passing if require_tests is None else bool(require_tests)
            if tests_required:
                try:
                    # Install dependencies if requirements.txt exists
                    req_file = Path(workspace) / 'requirements.txt'
                    if req_file.exists():
                        logger.info("📦 Installing dependencies from requirements.txt...")
                        install_res = subprocess.run(
                            [sys.executable, '-m', 'pip', 'install', '-q', '-r', 'requirements.txt'],
                            cwd=workspace,
                            capture_output=True,
                            text=True,
                            timeout=300,
                        )
                        if install_res.returncode != 0:
                            logger.warning(f"⚠️ pip install failed: {install_res.stderr}")
                    test_res = subprocess.run(
                        [sys.executable, '-m', 'pytest', '-q'],
                        cwd=workspace,
                        capture_output=True,
                        text=True,
                        timeout=600,
                    )
                    # pytest returns 5 when no tests are collected; treat as pass
                    if test_res.returncode not in (0, 5):
                        out = (test_res.stdout or '') + (test_res.stderr or '')
                        out = out[-2000:]
                        return {'success': False, 'error': f'Tests failed (pytest -q):\n{out}'}
                except Exception as e:
                    return {'success': False, 'error': f'Test run failed: {e}'}

            subprocess.run(['git', 'add', '-A'], cwd=workspace, capture_output=True)
            commit_msg = f"fix: Resolve issue #{issue_number} - {title}\n\nGenerated by Agent-Forge autonomous pipeline."
            commit_res = subprocess.run(['git', 'commit', '-m', commit_msg], cwd=workspace, capture_output=True, text=True)
            if commit_res.returncode != 0:
                return {'success': False, 'error': f"Git commit failed: {(commit_res.stderr or '').strip()}"}

            push_res = subprocess.run(['git', 'push', 'origin', branch_name], cwd=workspace, capture_output=True, text=True)
            if push_res.returncode != 0:
                return {'success': False, 'error': f"Push failed: {(push_res.stderr or '').strip()}"}

            pr_url = f"https://api.github.com/repos/{owner}/{repo_name}/pulls"
            headers = {
                'Authorization': f'token {token}',
                'Accept': 'application/vnd.github+json',
                'X-GitHub-Api-Version': '2022-11-28'
            }
            pr_data = {
                'title': f"Fix: {title}",
                'body': f"Resolves #{issue_number}\n\nAutomatically generated by Agent-Forge pipeline.",
                'head': branch_name,
                'base': base_ref
            }

            response = requests.post(pr_url, headers=headers, json=pr_data, timeout=30)
            if response.status_code not in (200, 201):
                return {'success': False, 'error': f"PR creation failed: {response.status_code} {response.text}"}

            pr = response.json()
            return {
                'success': True,
                'pr_url': pr.get('html_url'),
                'pr_number': pr.get('number'),
                'summary': f"PR created: {pr.get('html_url')}"
            }

        finally:
            try:
                shutil.rmtree(workspace)
                logger.info(f"🧹 Cleaned up workspace: {workspace}")
            except Exception as cleanup_error:
                logger.warning(f"⚠️  Failed to cleanup workspace: {cleanup_error}")

    async def handle_pr_change_request(
        self,
        repo: str,
        pr_number: int,
        mention_instructions: str,
    ) -> Dict[str, Any]:
        """Handle a change request on an existing PR triggered by an @mention.

        This workflow updates the PR's existing head branch (commit + push),
        rather than creating a new PR.
        """
        pr_key = f"{repo}#PR{pr_number}"
        logger.info(f"\n{'='*70}")
        logger.info(f"🔁 PR CHANGE-REQUEST PIPELINE STARTED: {pr_key}")
        logger.info(f"{'='*70}")

        start_time = datetime.utcnow()

        token = self._get_github_token()
        if not token:
            return {'success': False, 'error': 'No GitHub token available - cannot proceed'}

        if not mention_instructions or not mention_instructions.strip():
            try:
                from engine.operations.comment_composer import CommentComposer

                composer = CommentComposer()
                fallback = "⚠️ I was mentioned, but the comment didn’t include any change request text. Please describe what you want changed."
                body = composer.compose(
                    event="pr_change_request_missing_instructions",
                    context={
                        "repo": repo,
                        "pr_number": pr_number,
                    },
                    must_include_lines=["⚠️"],
                    fallback=fallback,
                )
                await self._post_issue_comment(
                    repo,
                    pr_number,
                    body,
                    token,
                )
            except Exception:
                pass
            return {'success': False, 'error': 'Empty mention instructions'}

        try:
            pr_data = await self._fetch_pr_details(repo=repo, pr_number=pr_number, token=token)
            if not pr_data:
                raise RuntimeError('Failed to fetch PR details')

            head_ref = pr_data['head']['ref']
            head_repo_full_name = pr_data['head']['repo']['full_name']
            base_ref = pr_data['base']['ref']
            pr_title = pr_data.get('title', '')

            logger.info(f"📌 PR title: {pr_title}")
            logger.info(f"🌿 Head: {head_repo_full_name}:{head_ref}")
            logger.info(f"🌳 Base: {repo}:{base_ref}")

            await self._post_issue_comment(
                repo,
                pr_number,
                _compose_pr_update_comment(
                    event="pr_update_start",
                    repo=repo,
                    pr_number=pr_number,
                    fallback="🤖 Starting PR update based on your @mention change request. I’ll push commits to this PR branch if successful.",
                    extra_context={
                        "pr_title": pr_title,
                        "head_ref": head_ref,
                        "base_ref": base_ref,
                    },
                ),
                token,
            )

            result = await self._apply_change_request_to_pr_branch(
                base_repo=repo,
                head_repo_full_name=head_repo_full_name,
                head_ref=head_ref,
                base_ref=base_ref,
                pr_number=pr_number,
                mention_instructions=mention_instructions,
                token=token,
            )

            elapsed = (datetime.utcnow() - start_time).total_seconds()
            if result.get('success'):
                await self._post_issue_comment(
                    repo,
                    pr_number,
                    _compose_pr_update_comment(
                        event="pr_update_success",
                        repo=repo,
                        pr_number=pr_number,
                        fallback=f"✅ Pushed updates to this PR branch based on the change request. Elapsed: {elapsed:.0f}s.",
                        extra_context={"elapsed_seconds": elapsed},
                        must_include=["✅"],
                    ),
                    token,
                )
            else:
                await self._post_issue_comment(
                    repo,
                    pr_number,
                    _compose_pr_update_comment(
                        event="pr_update_failure",
                        repo=repo,
                        pr_number=pr_number,
                        fallback=(
                            "❌ I couldn’t apply the requested changes automatically.\n\n"
                            f"Error: {result.get('error', 'Unknown error')}"
                        ),
                        extra_context={"error": result.get('error', 'Unknown error')},
                        must_include=["❌"],
                    ),
                    token,
                )

            result['elapsed_seconds'] = elapsed
            return result

        except Exception as e:
            logger.error(f"❌ PR change-request workflow failed: {e}")
            logger.error(traceback.format_exc())
            try:
                await self._post_issue_comment(
                    repo,
                    pr_number,
                    _compose_pr_update_comment(
                        event="pr_update_exception",
                        repo=repo,
                        pr_number=pr_number,
                        fallback=f"❌ I hit an error while attempting to update this PR.\n\nError: {e}",
                        extra_context={"error": str(e)},
                        must_include=["❌"],
                    ),
                    token,
                )
            except Exception:
                pass
            return {'success': False, 'error': str(e)}

    async def _fetch_pr_details(self, repo: str, pr_number: int, token: str) -> Optional[Dict[str, Any]]:
        """Fetch PR details via GitHub API."""
        try:
            import requests

            owner, repo_name = repo.split('/')
            pr_url = f"https://api.github.com/repos/{owner}/{repo_name}/pulls/{pr_number}"
            headers = {
                'Authorization': f'token {token}',
                'Accept': 'application/vnd.github+json',
                'X-GitHub-Api-Version': '2022-11-28'
            }
            response = requests.get(pr_url, headers=headers, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"❌ Failed to fetch PR details for {repo}#{pr_number}: {e}")
            return None

    async def _apply_change_request_to_pr_branch(
        self,
        base_repo: str,
        head_repo_full_name: str,
        head_ref: str,
        base_ref: str,
        pr_number: int,
        mention_instructions: str,
        token: str,
    ) -> Dict[str, Any]:
        """Clone the PR head branch, generate/apply a patch, commit, and push."""
        import subprocess
        import tempfile
        import shutil

        workspace = tempfile.mkdtemp(prefix=f"pr-{pr_number}-")
        logger.info(f"📁 PR workspace: {workspace}")

        try:
            clone_url = f"https://{token}@github.com/{head_repo_full_name}.git"
            logger.info(f"📥 Cloning {head_repo_full_name}@{head_ref}")

            # NOTE: Avoid shallow clones here. We need sufficient history to compute
            # diffs against the base branch, otherwise changed-file detection can
            # incorrectly return 0 and starve the LLM of context.
            clone_res = subprocess.run(
                ['git', 'clone', '--branch', head_ref, clone_url, workspace],
                capture_output=True,
                text=True,
            )
            if clone_res.returncode != 0:
                logger.warning(f"⚠️  Branch clone failed, retrying full clone: {clone_res.stderr.strip()}")
                clone_res = subprocess.run(
                    ['git', 'clone', clone_url, workspace],
                    capture_output=True,
                    text=True,
                )
                if clone_res.returncode != 0:
                    raise RuntimeError(f"Clone failed: {clone_res.stderr.strip()}")
                co_res = subprocess.run(
                    ['git', 'checkout', head_ref],
                    capture_output=True,
                    text=True,
                    cwd=workspace,
                )
                if co_res.returncode != 0:
                    raise RuntimeError(f"Checkout failed: {co_res.stderr.strip()}")

            # Configure git identity (required for commits)
            subprocess.run(['git', 'config', 'user.email', 'agent-forge@example.com'], cwd=workspace, capture_output=True)
            subprocess.run(['git', 'config', 'user.name', 'Agent-Forge'], cwd=workspace, capture_output=True)

            # Fetch base ref for diff context
            subprocess.run(['git', 'fetch', 'origin', base_ref], cwd=workspace, capture_output=True)

            # Build context: changed files vs base
            name_only = subprocess.run(
                ['git', 'diff', '--name-only', f'origin/{base_ref}...HEAD'],
                cwd=workspace,
                capture_output=True,
                text=True,
            )
            changed_files = [ln.strip() for ln in (name_only.stdout or '').splitlines() if ln.strip()]

            # Fallback: if merge-base diff fails (e.g. odd histories), use last-commit files.
            if not changed_files:
                show_only = subprocess.run(
                    ['git', 'show', '--name-only', '--pretty=format:', 'HEAD'],
                    cwd=workspace,
                    capture_output=True,
                    text=True,
                )
                changed_files = [ln.strip() for ln in (show_only.stdout or '').splitlines() if ln.strip()]
            logger.info(f"📊 Changed files in PR: {len(changed_files)}")

            diff_res = subprocess.run(
                ['git', 'diff', f'origin/{base_ref}...HEAD'],
                cwd=workspace,
                capture_output=True,
                text=True,
            )
            pr_diff = (diff_res.stdout or '')
            if len(pr_diff) > 12000:
                pr_diff = pr_diff[:12000] + "\n\n... (diff truncated) ...\n"

            file_snippets: List[str] = []
            for path in changed_files[:8]:
                try:
                    full_path = Path(workspace) / path
                    if not full_path.exists() or full_path.is_dir():
                        continue
                    content = full_path.read_text(errors='ignore')
                    if len(content) > 3000:
                        content = content[:3000] + "\n... (file truncated) ...\n"
                    file_snippets.append(f"FILE: {path}\n" + content)
                except Exception:
                    continue

            # Deterministic fast-path: if the mention explicitly requests a file to be set to
            # EXACT content, apply it directly (avoids brittle patch generation/apply).
            try:
                instr_lower = (mention_instructions or '').lower()
                if 'exact content' in instr_lower and ':' in mention_instructions:
                    marker_idx = instr_lower.find('exact content')
                    before = mention_instructions[:marker_idx]
                    after = mention_instructions[marker_idx:]

                    # Try to find a relative file path near the request.
                    # Prefer backticked paths, fallback to plain paths.
                    m = re.search(r"`([^`]+\.(?:md|txt))`", before)
                    if not m:
                        m = re.search(r"([A-Za-z0-9_./-]+\.(?:md|txt))", before)
                    rel_path = (m.group(1).strip() if m else '')

                    # Extract everything after the first ':' following the marker.
                    content_part = after.split(':', 1)[1]
                    content_part = content_part.lstrip("\r\n ")
                    content_part = content_part.replace('```', '').strip("\r\n")
                    if content_part and not content_part.endswith("\n"):
                        content_part += "\n"

                    if rel_path and content_part and not rel_path.startswith('/') and '..' not in rel_path:
                        target = Path(workspace) / rel_path
                        target.parent.mkdir(parents=True, exist_ok=True)
                        target.write_text(content_part)
                        logger.info(f"📝 Applied exact-content update to {rel_path}")
            except Exception as e:
                logger.warning(f"⚠️  Failed exact-content fast-path parsing/apply: {e}")

            if not self.agent or not hasattr(self.agent, 'query_llm'):
                raise RuntimeError('No LLM agent available for PR change request')

            # Helper: sanitize JSON from LLM output
            import json
            def _sanitize_json(text: str) -> str:
                cleaned = (text or '').strip()
                cleaned = cleaned.replace('```json', '```').replace('```', '')
                start = cleaned.find('[')
                if start == -1:
                    start = cleaned.find('{')
                if start != -1:
                    cleaned = cleaned[start:]
                return cleaned.strip()

            file_context = "\n\n".join(file_snippets)
            apply_ok = False
            last_error = ""

            # ─────────────────────────────────────────────────────────────────────
            # PRIMARY STRATEGY: JSON file operations (more reliable for local LLMs)
            # ─────────────────────────────────────────────────────────────────────
            logger.info("🔧 PR change request: attempting JSON file operations (primary strategy)...")
            json_system = (
                "You are an autonomous coding assistant. Return ONLY valid JSON. No markdown fences. No explanation. "
                "Return a JSON array of file operations: "
                "[{\"action\":\"modify\"|\"create\"|\"delete\",\"path\":\"relative/path\",\"content\":\"...COMPLETE file content...\"}]. "
                "For 'modify' and 'create', include the ENTIRE file content, not just changes. "
                "For 'delete', omit content. "
                "Paths must be relative to repo root and must not contain '..'."
            )
            json_prompt = (
                f"Repository: {base_repo}\n"
                f"PR #{pr_number} head: {head_repo_full_name}:{head_ref}\n"
                f"Base ref: {base_ref}\n\n"
                "Change request (from @mention comment):\n"
                f"{mention_instructions}\n\n"
                "Current PR diff (may be truncated):\n"
                f"{pr_diff}\n\n"
                "Existing relevant files and contents:\n"
                f"{file_context}\n\n"
                "Create the minimal set of file operations to implement the change request. "
                "For any file you modify, include the COMPLETE updated file content."
            )
            raw_ops = self.agent.query_llm(json_prompt, system_prompt=json_system, stream=False) or ''
            ops_text = _sanitize_json(raw_ops)
            try:
                ops = json.loads(ops_text)
                if isinstance(ops, list) and ops and len(ops) <= 25:
                    for op in ops:
                        if not isinstance(op, dict):
                            continue
                        action = (op.get('action') or '').strip().lower()
                        rel_path = (op.get('path') or '').strip()
                        if not rel_path or rel_path.startswith('/') or '..' in rel_path:
                            continue
                        target = Path(workspace) / rel_path
                        if action in ('create', 'modify'):
                            content = op.get('content')
                            if not isinstance(content, str):
                                continue
                            target.parent.mkdir(parents=True, exist_ok=True)
                            target.write_text(content)
                            logger.info(f"📝 {action.title()}: {rel_path}")
                        elif action == 'delete':
                            try:
                                if target.exists() and not target.is_dir():
                                    target.unlink()
                                    logger.info(f"🗑️ Deleted: {rel_path}")
                            except Exception:
                                continue
                    # Check if changes were made
                    status_check = subprocess.run(['git', 'status', '--porcelain'], cwd=workspace, capture_output=True, text=True)
                    if (status_check.stdout or '').strip():
                        apply_ok = True
                        logger.info("✅ JSON file operations applied successfully")
                    else:
                        last_error = "JSON operations produced no changes"
                        logger.warning(f"⚠️ {last_error}")
                else:
                    last_error = f"Invalid JSON structure: got {'empty list' if not ops else f'{len(ops)} ops' if isinstance(ops, list) else type(ops).__name__}"
                    logger.warning(f"⚠️ {last_error}")
            except Exception as parse_error:
                last_error = f"JSON parse failed: {parse_error}"
                logger.warning(f"⚠️ {last_error}")

            # ─────────────────────────────────────────────────────────────────────
            # FALLBACK STRATEGY: Unified diff patch
            # ─────────────────────────────────────────────────────────────────────
            if not apply_ok:
                logger.info("🔧 Falling back to unified diff patch...")
                patch_system = (
                    "You are an autonomous coding assistant. Return ONLY a unified diff patch that can be applied with `git apply`. "
                    "Do not include explanations, markdown fences, or any text before/after the diff.\n\n"
                    "CORRECT FORMAT EXAMPLE:\n"
                    "diff --git a/path/to/file.py b/path/to/file.py\n"
                    "--- a/path/to/file.py\n"
                    "+++ b/path/to/file.py\n"
                    "@@ -10,3 +10,4 @@\n"
                    " existing line\n"
                    "-removed line\n"
                    "+added line\n"
                    " another existing line\n\n"
                    "CRITICAL RULES:\n"
                    "- Start with 'diff --git a/path b/path'\n"
                    "- Include '--- a/path' and '+++ b/path' headers\n"
                    "- Include @@ line number markers\n"
                    "- Lines starting with ' ' (space) are context (unchanged)\n"
                    "- Lines starting with '-' are removed\n"
                    "- Lines starting with '+' are added\n"
                    "- NO explanation text, NO markdown, ONLY the patch"
                )
                patch_prompt = (
                    f"Repository: {base_repo}\n"
                    f"PR #{pr_number} head: {head_repo_full_name}:{head_ref}\n"
                    f"Base ref: {base_ref}\n\n"
                    "Change request (from @mention comment):\n"
                    f"{mention_instructions}\n\n"
                    "Current PR diff (may be truncated):\n"
                    f"{pr_diff}\n\n"
                    "Relevant file contents (may be truncated):\n"
                    + "\n\n".join(file_snippets)
                    + "\n\n"
                    "Produce a unified diff patch implementing the change request."
                )

                for attempt in range(3):  # 3 attempts for patch
                    raw_patch = self.agent.query_llm(patch_prompt, system_prompt=patch_system, stream=False) or ''
                    patch_text = _sanitize_patch(raw_patch)
                    if not patch_text or 'diff --git' not in patch_text:
                        last_error = "LLM did not return a valid unified diff patch"
                        logger.warning(f"⚠️ Patch attempt {attempt+1}/3: {last_error}")
                        continue

                    apply_res = subprocess.run(
                        ['git', 'apply', '--whitespace=nowarn', '-'],
                        cwd=workspace,
                        input=patch_text,
                        text=True,
                        capture_output=True,
                    )
                    if apply_res.returncode == 0:
                        apply_ok = True
                        logger.info("✅ Patch applied successfully")
                        break

                    err = (apply_res.stderr or '').strip()
                    last_error = err
                    logger.warning(f"⚠️ Patch attempt {attempt+1}/3 failed: {err}")
                    if attempt < 2:
                        patch_prompt = (
                            patch_prompt
                            + f"\n\nPrevious patch failed with error:\n{err}\n\n"
                            + "Return a corrected unified diff patch ONLY."
                        )

            if not apply_ok:
                return {'success': False, 'error': f"Both strategies failed. Last error: {last_error}"}

            status_res = subprocess.run(
                ['git', 'status', '--porcelain'],
                cwd=workspace,
                capture_output=True,
                text=True,
            )
            if not (status_res.stdout or '').strip():
                return {'success': False, 'error': 'Changes applied but produced no git diff'}

            if self.config.require_tests_passing:
                try:
                    # Install dependencies if requirements.txt exists
                    req_file = Path(workspace) / 'requirements.txt'
                    if req_file.exists():
                        logger.info("📦 Installing dependencies from requirements.txt...")
                        install_res = subprocess.run(
                            [sys.executable, '-m', 'pip', 'install', '-q', '-r', 'requirements.txt'],
                            cwd=workspace,
                            capture_output=True,
                            text=True,
                            timeout=300,
                        )
                        if install_res.returncode != 0:
                            logger.warning(f"⚠️ pip install failed: {install_res.stderr}")
                    test_res = subprocess.run(
                        [sys.executable, '-m', 'pytest', '-q'],
                        cwd=workspace,
                        capture_output=True,
                        text=True,
                        timeout=600,
                    )
                    # pytest returns 5 when no tests are collected; treat as pass
                    if test_res.returncode not in (0, 5):
                        out = (test_res.stdout or '') + (test_res.stderr or '')
                        out = out[-2000:]
                        return {'success': False, 'error': f'Tests failed (pytest -q):\n{out}'}
                except Exception as e:
                    return {'success': False, 'error': f'Test run failed: {e}'}

            subprocess.run(['git', 'add', '-A'], cwd=workspace, capture_output=True)
            commit_msg = f"chore: address PR change request (#{pr_number})"
            commit_res = subprocess.run(
                ['git', 'commit', '-m', commit_msg],
                cwd=workspace,
                capture_output=True,
                text=True,
            )
            if commit_res.returncode != 0:
                raise RuntimeError(f"Git commit failed: {(commit_res.stderr or '').strip()}")

            push_res = subprocess.run(
                ['git', 'push', 'origin', head_ref],
                cwd=workspace,
                capture_output=True,
                text=True,
            )
            if push_res.returncode != 0:
                raise RuntimeError(f"Push failed: {(push_res.stderr or '').strip()}")

            return {'success': True, 'updated_pr': pr_number, 'branch': head_ref}

        except subprocess.TimeoutExpired:
            return {'success': False, 'error': 'Tests timed out'}
        finally:
            try:
                shutil.rmtree(workspace)
                logger.info(f"🧹 Cleaned up PR workspace: {workspace}")
            except Exception as cleanup_error:
                logger.warning(f"⚠️  Failed to cleanup workspace: {cleanup_error}")
    
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
            
            title = issue_data.get('title', '')
            body = issue_data.get('body', '')
            labels = issue_data.get('labels', [])
            
            # CRITICAL: Check for documentation files FIRST before CodeGenerator inference
            # This prevents CodeGenerator from inferring wrong Python modules for doc files
            text = f"{title} {body}".lower()
            # Pattern supports: lowercase, uppercase, digits, underscores, hyphens, dots, slashes
            doc_pattern = r'(?:create|add|implement|build)(?:\s+file)?(?:\s*:)?\s*[`]?([a-z0-9_/.-]+\.(?:md|txt|rst))[`]?'
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
            
            # Use CodeGenerator's intelligent parsing for code modules
            generator = CodeGenerator(self.agent)
            
            # Infer module specification
            module_spec = generator.infer_module_spec(title, body, labels)
            
            if not module_spec:
                logger.warning("⚠️  Could not infer module specification from issue; falling back to generic workflow")
                return {
                    'success': True,
                    'is_documentation': False,
                    'is_generic_task': True,
                    'title': title,
                    'body': body,
                    'labels': labels,
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
            import tempfile
            import shutil
            
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
            
            # Create temporary workspace for target repository
            workspace = tempfile.mkdtemp(prefix=f"{repo_name}-")
            logger.info(f"📁 Workspace: {workspace}")
            
            try:
                # Clone target repository with authentication
                clone_url = f"https://{token}@github.com/{owner}/{repo_name}.git"
                clone_result = subprocess.run(
                    ['git', 'clone', '--depth=1', clone_url, workspace],
                    capture_output=True,
                    text=True
                )
                
                if clone_result.returncode != 0:
                    logger.error(f"Failed to clone repository: {clone_result.stderr}")
                    return {
                        'success': False,
                        'error': f'Clone failed: {clone_result.stderr}'
                    }
                
                # Create and checkout new branch
                result = subprocess.run(
                    ['git', 'checkout', '-b', branch_name],
                    capture_output=True,
                    text=True,
                    cwd=workspace
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
                    full_module_path = Path(workspace) / module_path
                    full_module_path.parent.mkdir(parents=True, exist_ok=True)
                    full_module_path.write_text(module_content)
                    logger.info(f"📝 Wrote {module_path}")
                
                if test_path and test_content:
                    full_test_path = Path(workspace) / test_path
                    full_test_path.parent.mkdir(parents=True, exist_ok=True)
                    full_test_path.write_text(test_content)
                    logger.info(f"📝 Wrote {test_path}")
                
                # Git add
                add_result = subprocess.run(
                    ['git', 'add'] + files, 
                    capture_output=True, 
                    text=True,
                    cwd=workspace
                )
                
                if add_result.returncode != 0:
                    logger.error(f"Failed to git add files: {add_result.stderr}")
                    return {
                        'success': False,
                        'error': f'Git add failed: {add_result.stderr}'
                    }
                
                logger.info(f"✅ Added files to git: {', '.join(files)}")
                
                # Configure git user for this repo (required for commit)
                subprocess.run(
                    ['git', 'config', 'user.email', 'agent-forge@example.com'],
                    capture_output=True,
                    cwd=workspace
                )
                subprocess.run(
                    ['git', 'config', 'user.name', 'Agent-Forge'],
                    capture_output=True,
                    cwd=workspace
                )
                
                # Git commit
                commit_msg = f"fix: Resolve issue #{issue_number} - {issue_data.get('title', 'Unknown')}\n\nGenerated by Agent-Forge autonomous pipeline."
                commit_result = subprocess.run(
                    ['git', 'commit', '-m', commit_msg],
                    capture_output=True,
                    text=True,
                    cwd=workspace
                )
                
                if commit_result.returncode != 0:
                    logger.error(f"Failed to commit: {commit_result.stderr}")
                    return {
                        'success': False,
                        'error': f'Git commit failed: {commit_result.stderr}'
                    }
                
                logger.info(f"✅ Committed changes: {commit_msg.split(chr(10))[0]}")
                
                # Git push
                result = subprocess.run(
                    ['git', 'push', 'origin', branch_name],
                    capture_output=True,
                    text=True,
                    cwd=workspace
                )
                
                if result.returncode != 0:
                    logger.error(f"Failed to push branch: {result.stderr}")
                    return {
                        'success': False,
                        'error': f'Push failed: {result.stderr}'
                    }
                
                logger.info(f"✅ Pushed branch: {branch_name}")
                
            finally:
                # Cleanup workspace
                try:
                    shutil.rmtree(workspace)
                    logger.info(f"🧹 Cleaned up workspace: {workspace}")
                except Exception as cleanup_error:
                    logger.warning(f"⚠️  Failed to cleanup workspace: {cleanup_error}")
            
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
    
    async def _post_issue_comment(self, repo: str, issue_number: int, comment_body: str, token: str):
        """Post a comment to a GitHub issue.
        
        Args:
            repo: Repository in format "owner/repo"
            issue_number: Issue number
            comment_body: Comment text (markdown supported)
            token: GitHub token
        """
        try:
            import requests
            
            owner, repo_name = repo.split('/')
            comment_url = f"https://api.github.com/repos/{owner}/{repo_name}/issues/{issue_number}/comments"
            headers = {
                'Authorization': f'token {token}',
                'Accept': 'application/vnd.github+json',
                'X-GitHub-Api-Version': '2022-11-28'
            }
            
            response = requests.post(comment_url, json={'body': comment_body}, headers=headers, timeout=30)
            response.raise_for_status()
            logger.debug(f"Posted comment to {repo}#{issue_number}")
        except Exception as e:
            logger.error(f"Failed to post comment to {repo}#{issue_number}: {e}")
            raise
    
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
