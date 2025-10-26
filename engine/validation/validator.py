"""
Module for validating and processing issues across multiple repositories.

This module provides a workspace management system to handle issues from external repositories.
It clones target repositories to temporary workspaces, overrides the agent's project_root,
executes workflows, and cleans up after completion.
"""

import os
from pathlib import Path
import subprocess
import shutil
from typing import Optional

class WorkspaceManager:
    """
    Class for managing temporary workspaces for processing issues from external repositories.
    
    Args:
        repo (str): The repository name in the format 'owner/repo'.
        issue_number (int): The issue number.
        
    Returns:
        Path: The path to the created workspace.
    """
    async def prepare_workspace(self, repo: str, issue_number: int) -> Path:
        """Clone target repository to temporary workspace."""
        workspace = Path(f"/tmp/agent-forge-workspaces/{repo.replace('/', '-')}-{issue_number}")
        
        if not workspace.exists():
            # Clone repository
            subprocess.run(['git', 'clone', f'https://github.com/{repo}.git', workspace])
        
        return workspace

    async def cleanup_workspace(self, workspace: Path):
        """Remove temporary workspace after workflow completion."""
        shutil.rmtree(workspace, ignore_errors=True)

class IssueHandler:
    """
    Class for handling issues and executing workflows in a temporary workspace.
    
    Args:
        agent (Agent): The agent instance with project_root attribute.
        
    Returns:
        None
    """
    def __init__(self, agent):
        self.agent = agent

    async def assign_to_issue(self, repo: str, issue_number: int):
        """Prepare workspace for target repository and override project_root."""
        workspace = await self.prepare_workspace(repo, issue_number)
        
        # Override agent's project_root temporarily
        original_root = self.agent.project_root
        self.agent.project_root = workspace
        
        try:
            # Execute workflow in target repository
            result = self._execute_workflow(issue)
            return result
        finally:
            # Restore original project_root
            self.agent.project_root = original_root

    def _execute_workflow(self, issue):
        """Execute the workflow for the given issue."""
        # Placeholder for actual workflow execution logic
        logging.info(f"Executing workflow for issue {issue}")
        return "Workflow completed successfully"

# Example usage:
# agent = Agent(project_root="/opt/agent-forge")
# validator = IssueHandler(agent)
# result = await validator.assign_to_issue("m0nk111/agent-forge-test", 3)
# print(result)