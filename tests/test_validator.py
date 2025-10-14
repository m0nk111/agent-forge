import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import subprocess

class WorkspaceManager:
    """Manages temporary workspaces for cross-repo operations."""

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
    def __init__(self, agent):
        self.agent = agent
    
    async def assign_to_issue(self, repo: str, issue_number: int):
        # Prepare workspace for target repository
        workspace = await WorkspaceManager().prepare_workspace(repo, issue_number)
        
        # Override agent's project_root temporarily
        original_root = self.agent.project_root
        self.agent.project_root = workspace
        
        try:
            # Execute workflow in target repository
            result = self._execute_workflow(issue_number)
        finally:
            # Restore original project_root
            self.agent.project_root = original_root
            await WorkspaceManager().cleanup_workspace(workspace)
    
    def _execute_workflow(self, issue_number: int):
        """Simulate workflow execution."""
        print(f"Executing workflow for issue {issue_number}")
        return "Workflow completed"

# Example usage:
class Agent:
    def __init__(self, project_root: Path):
        self.project_root = project_root

agent = Agent(Path("/opt/agent-forge"))
issue_handler = IssueHandler(agent)
await issue_handler.assign_to_issue("m0nk111/agent-forge-test", 3)

# Test file for validator.py
@pytest.fixture
def mock_subprocess_run():
    return patch('subprocess.run')

def test_prepare_workspace(mock_subprocess_run):
    workspace_manager = WorkspaceManager()
    repo = "m0nk111/agent-forge-test"
    issue_number = 3
    expected_path = Path("/tmp/agent-forge-workspaces/m0nk111-agent-forge-test-3")
    
    mock_subprocess_run.return_value = MagicMock(returncode=0)
    
    workspace = workspace_manager.prepare_workspace(repo, issue_number)
    
    assert workspace == expected_path
    mock_subprocess_run.assert_called_once_with(['git', 'clone', f'https://github.com/{repo}.git', str(expected_path)], check=True)

def test_prepare_workspace_existing_repo(mock_subprocess_run):
    workspace_manager = WorkspaceManager()
    repo = "m0nk111/agent-forge-test"
    issue_number = 3
    expected_path = Path("/tmp/agent-forge-workspaces/m0nk111-agent-forge-test-3")
    
    mock_subprocess_run.return_value = MagicMock(returncode=0)
    expected_path.mkdir(parents=True, exist_ok=True)
    
    workspace = workspace_manager.prepare_workspace(repo, issue_number)
    
    assert workspace == expected_path
    mock_subprocess_run.assert_not_called()

def test_cleanup_workspace(mock_subprocess_run):
    workspace_manager = WorkspaceManager()
    repo = "m0nk111/agent-forge-test"
    issue_number = 3
    expected_path = Path("/tmp/agent-forge-workspaces/m0nk111-agent-forge-test-3")
    
    mock_shutil_rmtree = patch('shutil.rmtree').start()
    
    workspace_manager.cleanup_workspace(expected_path)
    
    mock_shutil_rmtree.assert_called_once_with(expected_path, ignore_errors=True)

def test_assign_to_issue(mock_subprocess_run):
    issue_handler = IssueHandler(agent)
    repo = "m0nk111/agent-forge-test"
    issue_number = 3
    expected_result = "Workflow completed"
    
    mock_execute_workflow = patch.object(issue_handler, '_execute_workflow', return_value=expected_result).start()
    mock_subprocess_run.return_value = MagicMock(returncode=0)
    
    result = await issue_handler.assign_to_issue(repo, issue_number)
    
    assert result == expected_result
    mock_execute_workflow.assert_called_once_with(issue_number)

def test_assign_to_issue_existing_workspace(mock_subprocess_run):
    issue_handler = IssueHandler(agent)
    repo = "m0nk111/agent-forge-test"
    issue_number = 3
    expected_result = "Workflow completed"
    
    mock_execute_workflow = patch.object(issue_handler, '_execute_workflow', return_value=expected_result).start()
    mock_subprocess_run.return_value = MagicMock(returncode=0)
    
    with patch('pathlib.Path.mkdir') as mock_mkdir:
        mock_mkdir.side_effect = FileExistsError
        result = await issue_handler.assign_to_issue(repo, issue_number)
    
    assert result == expected_result
    mock_execute_workflow.assert_called_once_with(issue_number)

def test_assign_to_issue_cleanup_failure(mock_subprocess_run):
    issue_handler = IssueHandler(agent)
    repo = "m0nk111/agent-forge-test"
    issue_number = 3
    expected_result = "Workflow completed"
    
    mock_execute_workflow = patch.object(issue_handler, '_execute_workflow', return_value=expected_result).start()
    mock_subprocess_run.return_value = MagicMock(returncode=0)
    
    with patch('shutil.rmtree') as mock_rmtree:
        mock_rmtree.side_effect = Exception("Cleanup failed")
        result = await issue_handler.assign_to_issue(repo, issue_number)
    
    assert result == expected_result
    mock_execute_workflow.assert_called_once_with(issue_number)