import pytest
from validator import WorkspaceManager, IssueHandler
from unittest.mock import Mock, patch, MagicMock

# Fixtures to create mock instances
@pytest.fixture
def workspace_manager():
    return WorkspaceManager()

@pytest.fixture
def issue_handler(agent):
    return IssueHandler(agent)

@pytest.fixture
def agent():
    return Mock(project_root=None)

# Test cases for WorkspaceManager.prepare_workspace
def test_prepare_workspace(workspace_manager, tmp_path):
    repo = "test/repo"
    issue_number = 123
    workspace = workspace_manager.prepare_workspace(repo, issue_number)
    
    assert workspace == Path(f"/tmp/agent-forge-workspaces/test-repo-123")
    assert workspace.exists()

def test_prepare_workspace_existing(workspace_manager, tmp_path):
    repo = "test/repo"
    issue_number = 123
    existing_workspace = Path("/tmp/agent-forge-workspaces/test-repo-123")
    existing_workspace.mkdir(parents=True)
    
    with patch('subprocess.run') as mock_run:
        workspace_manager.prepare_workspace(repo, issue_number)
    
    assert mock_run.call_count == 0

# Test cases for WorkspaceManager.cleanup_workspace
def test_cleanup_workspace(workspace_manager, tmp_path):
    repo = "test/repo"
    issue_number = 123
    workspace = workspace_manager.prepare_workspace(repo, issue_number)
    
    workspace_manager.cleanup_workspace(workspace)
    assert not workspace.exists()

# Test cases for IssueHandler.assign_to_issue
def test_assign_to_issue(issue_handler, agent, tmp_path):
    repo = "test/repo"
    issue_number = 123
    
    with patch.object(IssueHandler, '_execute_workflow') as mock_execute:
        issue_handler.assign_to_issue(repo, issue_number)
    
    assert agent.project_root == Path(f"/tmp/agent-forge-workspaces/test-repo-123")
    mock_execute.assert_called_once()

def test_assign_to_issue_cleanup(issue_handler, agent, tmp_path):
    repo = "test/repo"
    issue_number = 123
    
    with patch.object(IssueHandler, '_execute_workflow') as mock_execute:
        issue_handler.assign_to_issue(repo, issue_number)
    
    assert not Path(f"/tmp/agent-forge-workspaces/test-repo-123").exists()

# Test cases for IssueHandler._execute_workflow
def test_execute_workflow(issue_handler):
    issue = Mock()
    
    with patch.object(IssueHandler, '_execute_workflow', return_value="mocked_result") as mock_execute:
        result = issue_handler._execute_workflow(issue)
    
    assert result == "mocked_result"