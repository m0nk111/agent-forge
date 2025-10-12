import os
from pathlib import Path
import subprocess
import shutil
from typing import Optional

class WorkspaceManager:
    """Class for managing repository workspaces."""

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
    """Class for handling issue resolution workflows."""

    def __init__(self, agent):
        self.agent = agent
        self.workspace_manager = WorkspaceManager()

    async def assign_to_issue(self, repo: str, issue_number: int):
        # Prepare workspace for target repository
        workspace = await self.workspace_manager.prepare_workspace(repo, issue_number)
        
        # Override agent's project_root temporarily
        original_root = self.agent.project_root
        self.agent.project_root = workspace
        
        try:
            # Execute workflow in target repository
            result = self._execute_workflow(issue_number)
        finally:
            # Restore original project_root
            self.agent.project_root = original_root

    def _execute_workflow(self, issue_number: int):
        """Execute the workflow within the agent's context."""
        # Placeholder for actual workflow logic
        print(f"Executing workflow for issue {issue_number} in workspace")
        return True  # Return result of workflow execution

# Example usage:
# from engine.core import Agent
# agent = Agent(project_root="/opt/agent-forge")
# handler = IssueHandler(agent)
# await handler.assign_to_issue("m0nk111/agent-forge-test", 3)