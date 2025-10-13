"""
Module for handling workspace operations and issue resolution across multiple repositories.

This module provides functionality to prepare a temporary workspace for an issue in a different repository,
execute the workflow, and then clean up the workspace.
"""

import os
import subprocess
import shutil
from pathlib import Path
from typing import Optional

class WorkspaceManager:
    """Class for managing temporary workspaces."""
    
    @staticmethod
    async def prepare_workspace(repo: str, issue_number: int) -> Path:
        """
        Clone target repository to a temporary workspace.
        
        Args:
            repo (str): The GitHub repository in the format 'username/repo'.
            issue_number (int): The number of the issue.
            
        Returns:
            Path: The path to the temporary workspace.
        """
        workspace = Path(f"/tmp/agent-forge-workspaces/{repo.replace('/', '-')}-{issue_number}")
        
        if not workspace.exists():
            # Clone repository
            subprocess.run(['git', 'clone', f'https://github.com/{repo}.git', workspace])
        
        return workspace
    
    @staticmethod
    async def cleanup_workspace(workspace: Path):
        """
        Remove temporary workspace after workflow completion.
        
        Args:
            workspace (Path): The path to the temporary workspace.
        """
        shutil.rmtree(workspace, ignore_errors=True)

class IssueHandler:
    """Class for handling issues across multiple repositories."""
    
    def __init__(self, agent):
        self.agent = agent
    
    async def assign_to_issue(self, repo: str, issue_number: int):
        """
        Assign and resolve an issue in a different repository.
        
        Args:
            repo (str): The GitHub repository in the format 'username/repo'.
            issue_number (int): The number of the issue.
        """
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
            
        # Cleanup workspace
        await WorkspaceManager.cleanup_workspace(workspace)
    
    def _execute_workflow(self, issue_number: int):
        """
        Simulate workflow execution.
        
        Args:
            issue_number (int): The number of the issue.
            
        Returns:
            str: Result of the workflow.
        """
        # Placeholder for actual workflow logic
        return f"Workflow executed for issue {issue_number}"