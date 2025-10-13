import pytest
from validator import WorkspaceManager, IssueHandler

# Test for WorkspaceManager.prepare_workspace
@pytest.mark.asyncio
async def test_prepare_workspace():
    repo = "user/repo"
    issue_number = 123
    workspace_path = Path(f"/tmp/agent-forge-workspaces/user-repo-123")
    
    # Mock subprocess.run to avoid actual git clone operation
    with patch('subprocess.run') as mock_run:
        await WorkspaceManager.prepare_workspace(repo, issue_number)
        
        mock_run.assert_called_once_with(['git', 'clone', f'https://github.com/{repo}.git', workspace_path])

@pytest.mark.asyncio
async def test_prepare_workspace_existing_workspace():
    repo = "user/repo"
    issue_number = 123
    workspace_path = Path(f"/tmp/agent-forge-workspaces/user-repo-123")
    
    # Mocking the workspace to exist
    workspace_path.mkdir(parents=True, exist_ok=True)
    
    with patch('subprocess.run') as mock_run:
        await WorkspaceManager.prepare_workspace(repo, issue_number)
        
        mock_run.assert_not_called()

@pytest.mark.asyncio
async def test_cleanup_workspace():
    workspace_path = Path("/tmp/agent-forge-workspaces/test_repo-123")
    
    # Mocking the workspace to exist
    workspace_path.mkdir(parents=True, exist_ok=True)
    
    await WorkspaceManager.cleanup_workspace(workspace_path)
    
    assert not workspace_path.exists()

# Test for IssueHandler.assign_to_issue
@pytest.mark.asyncio
async def test_assign_to_issue():
    class MockAgent:
        project_root = None

    agent = MockAgent()
    issue_handler = IssueHandler(agent)
    repo = "user/repo"
    issue_number = 123
    
    # Mocking the execute_workflow method to return a known result
    with patch.object(issue_handler, '_execute_workflow', return_value={"issue_number": issue_number, "status": "completed"}):
        await issue_handler.assign_to_issue(repo, issue_number)
        
        assert agent.project_root == Path("/tmp/agent-forge-workspaces/user-repo-123")

@pytest.mark.asyncio
async def test_assign_to_issue_cleanup():
    class MockAgent:
        project_root = None

    agent = MockAgent()
    issue_handler = IssueHandler(agent)
    repo = "user/repo"
    issue_number = 123
    
    # Mocking the execute_workflow method to return a known result
    with patch.object(issue_handler, '_execute_workflow', return_value={"issue_number": issue_number, "status": "completed"}):
        await issue_handler.assign_to_issue(repo, issue_number)
        
        assert not Path("/tmp/agent-forge-workspaces/user-repo-123").exists()

@pytest.mark.asyncio
async def test_assign_to_issue_exception():
    class MockAgent:
        project_root = None

    agent = MockAgent()
    issue_handler = IssueHandler(agent)
    repo = "user/repo"
    issue_number = 123
    
    # Mocking the execute_workflow method to raise an exception
    with patch.object(issue_handler, '_execute_workflow', side_effect=Exception("Simulated error")):
        with pytest.raises(Exception) as exc_info:
            await issue_handler.assign_to_issue(repo, issue_number)
            
        assert str(exc_info.value) == "Simulated error"
        assert agent.project_root is None