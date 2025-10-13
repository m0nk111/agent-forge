import pytest
from pathlib import Path
from unittest.mock import Mock, patch
import subprocess

# Import the function to test
from engine.validation.validator import WorkspaceManager, IssueHandler

@pytest.fixture
def workspace_manager():
    return WorkspaceManager()

@pytest.fixture
def issue_handler(agent):
    return IssueHandler(agent)

@patch('subprocess.run')
def test_prepare_workspace(workspace_manager, mock_subprocess):
    repo = "m0nk111/agent-forge-test"
    issue_number = 3
    expected_path = Path("/tmp/agent-forge-workspaces/m0nk111-agent-forge-test-3")

    result = workspace_manager.prepare_workspace(repo, issue_number)
    
    mock_subprocess.assert_called_once_with(['git', 'clone', f'https://github.com/{repo}.git', expected_path], check=True)
    assert result == expected_path

@patch('shutil.rmtree')
def test_cleanup_workspace(workspace_manager, mock_rmtree):
    workspace = Path("/tmp/agent-forge-workspaces/m0nk111-agent-forge-test-3")
    
    workspace_manager.cleanup_workspace(workspace)
    
    mock_rmtree.assert_called_once_with(workspace, ignore_errors=True)

@pytest.fixture
def agent():
    return Mock(project_root="/opt/agent-forge")

@patch('engine.validation.validator.WorkspaceManager.prepare_workspace')
@patch('engine.validation.validator.IssueHandler._execute_workflow')
def test_assign_to_issue(issue_handler, mock_prepare_workspace, mock_execute_workflow):
    repo = "m0nk111/agent-forge-test"
    issue_number = 3
    expected_path = Path("/tmp/agent-forge-workspaces/m0nk111-agent-forge-test-3")
    
    mock_prepare_workspace.return_value = expected_path
    mock_execute_workflow.return_value = "Workflow completed successfully."
    
    result = issue_handler.assign_to_issue(repo, issue_number)
    
    assert result == "Workflow completed successfully."
    mock_prepare_workspace.assert_called_once_with(repo, issue_number)
    mock_execute_workflow.assert_called_once_with(issue_handler.agent)

@patch('engine.validation.validator.WorkspaceManager.prepare_workspace', side_effect=FileNotFoundError)
def test_assign_to_issue_with_error(workspace_manager, issue_handler):
    repo = "m0nk111/agent-forge-test"
    issue_number = 3
    
    with pytest.raises(FileNotFoundError):
        issue_handler.assign_to_issue(repo, issue_number)