import os
import shutil
from pathlib import Path
from typing import Optional

class WorkspaceManager:
    """
    Class to manage workspace for cross-repository issue resolution.
    """

    async def prepare_workspace(self, repo: str, issue_number: int) -> Path:
        """
        Clone target repository to temporary workspace.

        Args:
            repo (str): The GitHub repository in the format 'owner/repository'.
            issue_number (int): The issue number.

        Returns:
            Path: The path to the temporary workspace.
        """
        workspace = Path(f"/tmp/agent-forge-workspaces/{repo.replace('/', '-')}-{issue_number}")
        
        if not workspace.exists():
            # Clone repository
            subprocess.run(['git', 'clone', f'https://github.com/{repo}.git', workspace])
        
        return workspace

    async def cleanup_workspace(self, workspace: Path):
        """
        Remove temporary workspace after workflow completion.

        Args:
            workspace (Path): The path to the temporary workspace.
        """
        shutil.rmtree(workspace, ignore_errors=True)

class IssueHandler:
    """
    Class to handle issues and execute workflows in a temporary workspace.
    """

    def __init__(self, agent):
        self.agent = agent

    async def assign_to_issue(self, repo: str, issue_number: int):
        """
        Assign an issue to the workflow in the target repository.

        Args:
            repo (str): The GitHub repository in the format 'owner/repository'.
            issue_number (int): The issue number.
        """
        # Prepare workspace for target repository
        workspace = await self.prepare_workspace(repo, issue_number)
        
        # Override agent's project_root temporarily
        original_root = self.agent.project_root
        self.agent.project_root = workspace
        
        try:
            # Execute workflow in target repository
            result = self._execute_workflow(issue)
        finally:
            # Restore original project_root
            self.agent.project_root = original_root

    def _execute_workflow(self, issue):
        """
        Placeholder method to simulate workflow execution.

        Args:
            issue (dict): The issue details.
        
        Returns:
            str: Result of the workflow.
        """
        return "Workflow completed successfully."

# Example usage
if __name__ == "__main__":
    from engine.core import Agent

    agent = Agent(project_root="/opt/agent-forge")
    handler = IssueHandler(agent)

    # Prepare workspace and execute workflow for a test issue
    repo = "m0nk111/agent-forge-test"
    issue_number = 3
    result = handler.assign_to_issue(repo, issue_number)
    print(result)