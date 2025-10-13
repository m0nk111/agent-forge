"""
Module for handling workspace management and issue validation across multiple repositories.
"""

import os
import shutil
from pathlib import Path
import subprocess
from typing import Optional, Dict

class WorkspaceManager:
    """Class to manage temporary workspaces for issues from different repositories."""

    @staticmethod
    async def prepare_workspace(repo: str, issue_number: int) -> Path:
        """Clone target repository to temporary workspace."""
        workspace = Path(f"/tmp/agent-forge-workspaces/{repo.replace('/', '-')}-{issue_number}")
        
        if not workspace.exists():
            # Clone repository
            subprocess.run(['git', 'clone', f'https://github.com/{repo}.git', workspace])
        
        return workspace

    @staticmethod
    async def cleanup_workspace(workspace: Path):
        """Remove temporary workspace after workflow completion."""
        shutil.rmtree(workspace, ignore_errors=True)

class IssueHandler:
    """Class to handle assignment and processing of issues across different repositories."""

    def __init__(self, agent):
        self.agent = agent

    async def assign_to_issue(self, repo: str, issue_number: int):
        # Prepare workspace for target repository
        workspace = await WorkspaceManager.prepare_workspace(repo, issue_number)
        
        # Override agent's project_root temporarily
        original_root = self.agent.project_root
        self.agent.project_root = workspace
        
        try:
            # Execute workflow in target repository
            result = self._execute_workflow(issue_number)
        finally:
            # Restore original project_root
            self.agent.project_root = original_root
            await WorkspaceManager.cleanup_workspace(workspace)

    def _execute_workflow(self, issue_number: int) -> Dict:
        """Simulate workflow execution."""
        return {
            "issue_number": issue_number,
            "status": "completed"
        }