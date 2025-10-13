import pytest
from validator import WorkspaceManager, IssueHandler
from unittest.mock import Mock, patch

# Test cases for WorkspaceManager.prepare_workspace
def test_prepare_workspace_creates_directory(tmp_path):
    repo = "user/repo"
    issue_number = 123
    workspace = WorkspaceManager.prepare_workspace(repo, issue_number)
    assert workspace.exists()
    assert str(workspace).startswith(f"/tmp/agent-forge-workspaces/{repo.replace('/', '-')}-{issue_number}")

@patch('subprocess.run')
def test_prepare_workspace_clones_repository(mock_run):
    repo = "user/repo"
    issue_number = 123
    WorkspaceManager.prepare_workspace(repo, issue_number)
    mock_run.assert_called_once_with(['git', 'clone', f'https://github.com/{repo}.git', '/tmp/agent-forge-workspaces/user-repo-123'])

def test_prepare_workspace_existing_directory(tmp_path):
    repo = "user/repo"
    issue_number = 123
    workspace = Path(f"/tmp/agent-forge-workspaces/{repo.replace('/', '-')}-{issue_number}")
    workspace.mkdir(parents=True, exist_ok=True)
    result = WorkspaceManager.prepare_workspace(repo, issue_number)
    assert result == workspace

@patch('shutil.rmtree')
def test_cleanup_workspace_removes_directory(mock_rmtree):
    workspace = Path("/tmp/agent-forge-workspaces/user-repo-123")
    workspace.mkdir(parents=True, exist_ok=True)
    WorkspaceManager.cleanup_workspace(workspace)
    mock_rmtree.assert_called_once_with(workspace, ignore_errors=True)

# Test cases for IssueHandler.assign_to_issue
def test_assign_to_issue_prepares_and_cleanup_workspace(mocker):
    agent = Mock()
    handler = IssueHandler(agent)
    repo = "user/repo"
    issue_number = 123
    with patch.object(WorkspaceManager, 'prepare_workspace', return_value=Mock()):
        with patch.object(WorkspaceManager, 'cleanup_workspace'):
            with patch.object(handler, '_execute_workflow', return_value="Workflow completed successfully"):
                result = handler.assign_to_issue(repo, issue_number)
                assert result == "Workflow completed successfully"
                agent.project_root.assert_called_once_with(None)

@patch('shutil.rmtree')
def test_assign_to_issue_exception_handling(mocker):
    agent = Mock()
    handler = IssueHandler(agent)
    repo = "user/repo"
    issue_number = 123
    with patch.object(WorkspaceManager, 'prepare_workspace', return_value=Mock()):
        with patch.object(WorkspaceManager, 'cleanup_workspace'):
            with patch.object(handler, '_execute_workflow') as mock_execute:
                mock_execute.side_effect = Exception("Test exception")
                result = handler.assign_to_issue(repo, issue_number)
                assert result is None
                agent.project_root.assert_called_once_with(None)

def test_assign_to_issue_no_cleanup_on_exception(mocker):
    agent = Mock()
    handler = IssueHandler(agent)
    repo = "user/repo"
    issue_number = 123
    with patch.object(WorkspaceManager, 'prepare_workspace', return_value=Mock()):
        with patch.object(WorkspaceManager, 'cleanup_workspace') as mock_cleanup:
            with patch.object(handler, '_execute_workflow') as mock_execute:
                mock_execute.side_effect = Exception("Test exception")
                result = handler.assign_to_issue(repo, issue_number)
                assert result is None
                agent.project_root.assert_called_once_with(None)
                mock_cleanup.assert_not_called()