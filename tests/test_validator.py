import pytest
from validator import WorkspaceManager, IssueHandler

@pytest.fixture
def issue_handler():
    agent = Mock()
    agent.project_root = Path("/tmp/original_project_root")
    return IssueHandler(agent)

async def test_prepare_workspace_success(issue_handler):
    repo = "username/repo"
    issue_number = 123
    workspace = await WorkspaceManager.prepare_workspace(repo, issue_number)
    assert workspace.exists()
    assert isinstance(workspace, Path)
    assert str(workspace) == "/tmp/agent-forge-workspaces/username-repo-123"

async def test_prepare_workspace_already_exists(issue_handler):
    repo = "username/repo"
    issue_number = 123
    workspace = await WorkspaceManager.prepare_workspace(repo, issue_number)
    assert workspace.exists()
    
    # Prepare again should not recreate the workspace
    existing_workspace = await WorkspaceManager.prepare_workspace(repo, issue_number)
    assert existing_workspace == workspace

async def test_cleanup_workspace_success(issue_handler):
    repo = "username/repo"
    issue_number = 123
    workspace = await WorkspaceManager.prepare_workspace(repo, issue_number)
    await WorkspaceManager.cleanup_workspace(workspace)
    assert not workspace.exists()

async def test_assign_to_issue_success(issue_handler):
    repo = "username/repo"
    issue_number = 123
    result = await issue_handler.assign_to_issue(repo, issue_number)
    assert result == "Workflow executed for issue 123"

async def test_assign_to_issue_with_error(issue_handler):
    issue_handler.agent.project_root = Path("/nonexistent/path")
    repo = "username/repo"
    issue_number = 123
    with pytest.raises(FileNotFoundError):
        await issue_handler.assign_to_issue(repo, issue_number)

async def test_execute_workflow_success(issue_handler):
    issue_number = 123
    result = issue_handler._execute_workflow(issue_number)
    assert result == "Workflow executed for issue 123"