import pytest
from pathlib import Path
from unittest.mock import Mock, patch
from engine.core import Agent
from workspace_manager import WorkspaceManager
from issue_handler import IssueHandler

# Fixtures to simulate agent and workspace
@pytest.fixture
def mock_agent():
    return Mock(spec=Agent)

@pytest.fixture
def mock_workspace_manager():
    return Mock(spec=WorkspaceManager)

@pytest.fixture
def mock_issue_handler(mock_agent, mock_workspace_manager):
    handler = IssueHandler(mock_agent)
    handler.workspace_manager = mock_workspace_manager
    return handler

# Test cases for WorkspaceManager
def test_prepare_workspace_success(mock_workspace_manager):
    repo = "m0nk111/agent-forge-test"
    issue_number = 3
    workspace_path = Path("/tmp/agent-forge-workspaces/m0nk111-agent-forge-test-3")
    
    mock_agent.project_root = "/opt/agent-forge"

    # Mock git clone to avoid actual cloning
    with patch("subprocess.run") as mock_run:
        result = mock_workspace_manager.prepare_workspace(repo, issue_number)
        
        assert result == workspace_path
        mock_run.assert_called_once_with(['git', 'clone', f'https://github.com/{repo}.git', workspace_path])

def test_prepare_workspace_exists(mock_workspace_manager):
    repo = "m0nk111/agent-forge-test"
    issue_number = 3
    workspace_path = Path("/tmp/agent-forge-workspaces/m0nk111-agent-forge-test-3")
    
    mock_agent.project_root = "/opt/agent-forge"

    # Mock existing workspace
    workspace_path.mkdir(parents=True, exist_ok=True)
    
    with patch("subprocess.run") as mock_run:
        result = mock_workspace_manager.prepare_workspace(repo, issue_number)
        
        assert result == workspace_path
        mock_run.assert_not_called()

def test_cleanup_workspace_success(mock_workspace_manager):
    repo = "m0nk111/agent-forge-test"
    issue_number = 3
    workspace_path = Path("/tmp/agent-forge-workspaces/m0nk111-agent-forge-test-3")
    
    mock_agent.project_root = "/opt/agent-forge"

    # Mock existing workspace
    workspace_path.mkdir(parents=True, exist_ok=True)
    
    with patch("shutil.rmtree") as mock_rmtree:
        mock_workspace_manager.cleanup_workspace(workspace_path)
        
        assert not workspace_path.exists()
        mock_rmtree.assert_called_once_with(workspace_path, ignore_errors=True)

def test_cleanup_workspace_nonexistent(mock_workspace_manager):
    repo = "m0nk111/agent-forge-test"
    issue_number = 3
    workspace_path = Path("/tmp/agent-forge-workspaces/m0nk111-agent-forge-test-3")
    
    mock_agent.project_root = "/opt/agent-forge"

    # Mock non-existing workspace
    with patch("shutil.rmtree") as mock_rmtree:
        mock_workspace_manager.cleanup_workspace(workspace_path)
        
        assert not workspace_path.exists()
        mock_rmtree.assert_not_called()

# Test cases for IssueHandler
def test_assign_to_issue_success(mock_issue_handler):
    repo = "m0nk111/agent-forge-test"
    issue_number = 3
    
    # Mock prepare_workspace and cleanup_workspace
    with patch.object(mock_issue_handler.workspace_manager, 'prepare_workspace') as mock_prepare:
        with patch.object(mock_issue_handler.workspace_manager, 'cleanup_workspace') as mock_cleanup:
            result = mock_issue_handler.assign_to_issue(repo, issue_number)
            
            assert result is None
            mock_prepare.assert_called_once_with(repo, issue_number)
            mock_cleanup.assert_called_once_with(mock_prepare.return_value)

def test_assign_to_issue_cleanup_failure(mock_issue_handler):
    repo = "m0nk111/agent-forge-test"
    issue_number = 3
    
    # Mock prepare_workspace and cleanup_workspace
    with patch.object(mock_issue_handler.workspace_manager, 'prepare_workspace') as mock_prepare:
        mock_prepare.return_value = Path("/tmp/agent-forge-workspaces/m0nk111-agent-forge-test-3")
        
        with patch.object(mock_issue_handler.workspace_manager, 'cleanup_workspace') as mock_cleanup:
            mock_cleanup.side_effect = Exception("Cleanup failed")
            
            with pytest.raises(Exception) as exc_info:
                result = mock_issue_handler.assign_to_issue(repo, issue_number)
                
                assert str(exc_info.value) == "Cleanup failed"
                mock_prepare.assert_called_once_with(repo, issue_number)
                mock_cleanup.assert_called_once_with(mock_prepare.return_value)

def test_assign_to_issue_workspace_exists(mock_issue_handler):
    repo = "m0nk111/agent-forge-test"
    issue_number = 3
    
    # Mock prepare_workspace and cleanup_workspace
    with patch.object(mock_issue_handler.workspace_manager, 'prepare_workspace') as mock_prepare:
        mock_prepare.return_value = Path("/tmp/agent-forge-workspaces/m0nk111-agent-forge-test-3")
        
        with patch.object(mock_issue_handler.workspace_manager, 'cleanup_workspace') as mock_cleanup:
            # Mock existing workspace
            mock_prepare.return_value.mkdir(parents=True, exist_ok=True)
            
            result = mock_issue_handler.assign_to_issue(repo, issue_number)
            
            assert result is None
            mock_prepare.assert_called_once_with(repo, issue_number)
            mock_cleanup.assert_not_called()