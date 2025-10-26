import pytest
from pathlib import Path
import subprocess
import shutil
from unittest.mock import patch, MagicMock

# Mocking the Agent class for testing purposes
class MockAgent:
    def __init__(self):
        self.project_root = "/opt/agent-forge"

@pytest.fixture
async def workspace_manager():
    return WorkspaceManager()

@pytest.fixture
async def issue_handler(agent):
    return IssueHandler(agent)

@pytest.fixture
def agent():
    return MockAgent()

@pytest.mark.asyncio
@patch('subprocess.run')
async def test_prepare_workspace(subprocess_run_mock, workspace_manager, repo="m0nk111/agent-forge-test", issue_number=3):
    """Test the prepare_workspace method."""
    # Arrange
    expected_path = Path("/tmp/agent-forge-workspaces/m0nk111-agent-forge-test-3")
    
    # Act
    result = await workspace_manager.prepare_workspace(repo, issue_number)
    
    # Assert
    assert result == expected_path
    subprocess_run_mock.assert_called_once_with(['git', 'clone', f'https://github.com/{repo}.git', expected_path], check=True)

@pytest.mark.asyncio
@patch('shutil.rmtree')
async def test_cleanup_workspace(shutil_rmtree_mock, workspace_manager, repo="m0nk111/agent-forge-test", issue_number=3):
    """Test the cleanup_workspace method."""
    # Arrange
    workspace = Path("/tmp/agent-forge-workspaces/m0nk111-agent-forge-test-3")
    
    # Act
    await workspace_manager.cleanup_workspace(workspace)
    
    # Assert
    shutil_rmtree_mock.assert_called_once_with(workspace, ignore_errors=True)

@pytest.mark.asyncio
@patch('os.path.exists')
async def test_prepare_workspace_repo_exists(subprocess_run_mock, exists_mock, workspace_manager):
    """Test the prepare_workspace method when repo already exists."""
    # Arrange
    repo = "m0nk111/agent-forge-test"
    issue_number = 3
    expected_path = Path("/tmp/agent-forge-workspaces/m0nk111-agent-forge-test-3")
    
    exists_mock.return_value = True
    
    # Act
    result = await workspace_manager.prepare_workspace(repo, issue_number)
    
    # Assert
    assert result == expected_path
    subprocess_run_mock.assert_not_called()

@pytest.mark.asyncio
@patch('os.path.exists')
async def test_cleanup_workspace_repo_empty(shutil_rmtree_mock, exists_mock, workspace_manager):
    """Test the cleanup_workspace method when repo is empty."""
    # Arrange
    workspace = Path("/tmp/agent-forge-workspaces/m0nk111-agent-forge-test-3")
    
    exists_mock.return_value = True
    
    # Act
    await workspace_manager.cleanup_workspace(workspace)
    
    # Assert
    shutil_rmtree_mock.assert_called_once_with(workspace, ignore_errors=True)

@pytest.mark.asyncio
@patch('subprocess.run', side_effect=subprocess.CalledProcessError(1, 'git clone'))
async def test_prepare_workspace_repo_clone_fail(subprocess_run_mock, workspace_manager):
    """Test the prepare_workspace method when git clone fails."""
    # Arrange
    repo = "m0nk111/agent-forge-test"
    issue_number = 3
    
    with pytest.raises(subprocess.CalledProcessError) as e:
        await workspace_manager.prepare_workspace(repo, issue_number)
    
    # Assert
    assert isinstance(e.value, subprocess.CalledProcessError)
    assert e.value.returncode == 1
    subprocess_run_mock.assert_called_once_with(['git', 'clone', f'https://github.com/{repo}.git', Path("/tmp/agent-forge-workspaces/m0nk111-agent-forge-test-3")], check=True)

@pytest.mark.asyncio
@patch('shutil.rmtree', side_effect=PermissionError)
async def test_cleanup_workspace_repo_permission_error(shutil_rmtree_mock, workspace_manager):
    """Test the cleanup_workspace method when PermissionError occurs."""
    # Arrange
    workspace = Path("/tmp/agent-forge-workspaces/m0nk111-agent-forge-test-3")
    
    with pytest.raises(PermissionError) as e:
        await workspace_manager.cleanup_workspace(workspace)
    
    # Assert
    assert isinstance(e.value, PermissionError)
    shutil_rmtree_mock.assert_called_once_with(workspace, ignore_errors=True)

@pytest.mark.asyncio
async def test_assign_to_issue_positive(agent, issue_handler):
    """Test the assign_to_issue method with positive scenario."""
    # Arrange
    repo = "m0nk111/agent-forge-test"
    issue_number = 3
    
    # Mocking the prepare_workspace and cleanup_workspace methods
    workspace_manager = MagicMock()
    issue_handler.prepare_workspace.return_value = Path("/tmp/agent-forge-workspaces/m0nk111-agent-forge-test-3")
    
    # Act
    result = await issue_handler.assign_to_issue(repo, issue_number)
    
    # Assert
    assert result == "Workflow completed successfully"
    issue_handler.prepare_workspace.assert_called_once_with(repo, issue_number)
    agent.project_root.assert_set_to("/tmp/agent-forge-workspaces/m0nk111-agent-forge-test-3")
    issue_handler.cleanup_workspace.assert_called_once_with(Path("/tmp/agent-forge-workspaces/m0nk111-agent-forge-test-3"))

@pytest.mark.asyncio
async def test_assign_to_issue_negative(agent, issue_handler):
    """Test the assign_to_issue method with negative scenario."""
    # Arrange
    repo = "m0nk111/agent-forge-test"
    issue_number = 3
    
    # Mocking the prepare_workspace and cleanup_workspace methods to fail
    workspace_manager = MagicMock()
    issue_handler.prepare_workspace.side_effect = subprocess.CalledProcessError(1, 'git clone')
    
    with pytest.raises(subprocess.CalledProcessError) as e:
        await issue_handler.assign_to_issue(repo, issue_number)
    
    # Assert
    assert isinstance(e.value, subprocess.CalledProcessError)
    issue_handler.prepare_workspace.assert_called_once_with(repo, issue_number)
    agent.project_root.assert_not_called()
    issue_handler.cleanup_workspace.assert_not_called()

@pytest.mark.asyncio
async def test_assign_to_issue_cleanup_error(agent, issue_handler):
    """Test the assign_to_issue method with cleanup error."""
    # Arrange
    repo = "m0nk111/agent-forge-test"
    issue_number = 3
    
    # Mocking the prepare_workspace and cleanup_workspace methods
    workspace_manager = MagicMock()
    issue_handler.prepare_workspace.return_value = Path("/tmp/agent-forge-workspaces/m0nk111-agent-forge-test-3")
    issue_handler.cleanup_workspace.side_effect = PermissionError
    
    with pytest.raises(PermissionError) as e:
        await issue_handler.assign_to_issue(repo, issue_number)
    
    # Assert
    assert isinstance(e.value, PermissionError)
    issue_handler.prepare_workspace.assert_called_once_with(repo, issue_number)
    agent.project_root.assert_set_to("/tmp/agent-forge-workspaces/m0nk111-agent-forge-test-3")
    issue_handler.cleanup_workspace.assert_called_once_with(Path("/tmp/agent-forge-workspaces/m0nk111-agent-forge-test-3"))