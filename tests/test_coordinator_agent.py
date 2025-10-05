"""
Tests for Coordinator Agent.

Tests planning, task assignment, progress monitoring, and plan adaptation.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
from pathlib import Path

from agents.coordinator_agent import (
    CoordinatorAgent, SubTask, ExecutionPlan, TaskAssignment,
    AgentCapability, AgentRole, TaskStatus, PlanStatus
)


@pytest.fixture
def coordinator():
    """Create CoordinatorAgent instance for testing."""
    return CoordinatorAgent(agent_id="test-coordinator")


@pytest.fixture
def mock_llm_agent():
    """Mock LLM agent for testing."""
    llm = Mock()
    llm.query = AsyncMock()
    return llm


@pytest.fixture
def mock_bot_agent():
    """Mock bot agent for testing."""
    bot = Mock()
    bot.add_comment = AsyncMock()
    return bot


@pytest.fixture
def sample_issue_data():
    """Sample GitHub issue data."""
    return {
        'number': 42,
        'title': 'Add user authentication system',
        'body': 'Implement JWT authentication with role-based permissions',
        'labels': ['enhancement', 'high-priority']
    }


@pytest.fixture
def sample_subtasks():
    """Sample sub-tasks for testing."""
    return [
        SubTask(
            id="task-42-1",
            title="Design authentication architecture",
            description="Plan the auth system design",
            priority=5,
            estimated_effort=60
        ),
        SubTask(
            id="task-42-2",
            title="Implement JWT token generation",
            description="Create JWT token functions",
            depends_on=["task-42-1"],
            priority=4,
            estimated_effort=120
        ),
        SubTask(
            id="task-42-3",
            title="Write authentication tests",
            description="Add comprehensive tests",
            depends_on=["task-42-2"],
            priority=3,
            estimated_effort=90
        )
    ]


class TestCoordinatorAgent:
    """Test CoordinatorAgent functionality."""
    
    def test_coordinator_initialization(self, coordinator):
        """Test coordinator initialization."""
        assert coordinator.agent_id == "test-coordinator"
        assert coordinator.role == AgentRole.COORDINATOR
        assert len(coordinator.active_plans) == 0
        assert len(coordinator.agent_registry) == 0
    
    def test_load_default_config(self, coordinator):
        """Test loading default configuration."""
        assert 'llm' in coordinator.config
        assert 'planning' in coordinator.config
        assert 'monitoring' in coordinator.config
        assert coordinator.max_sub_tasks == 20
        assert coordinator.default_task_effort == 30
    
    def test_load_config_from_file(self, tmp_path):
        """Test loading configuration from YAML file."""
        config_file = tmp_path / "test_coordinator_config.yaml"
        config_file.write_text("""
coordinator:
  planning:
    max_sub_tasks: 15
    default_task_effort: 45
""")
        
        coordinator = CoordinatorAgent(config_file=config_file)
        assert coordinator.max_sub_tasks == 15
        assert coordinator.default_task_effort == 45
    
    def test_register_agent(self, coordinator):
        """Test agent registration."""
        coordinator.register_agent(
            agent_id="dev-1",
            role="developer",
            skills=["python", "testing"],
            max_concurrent_tasks=3
        )
        
        assert "dev-1" in coordinator.agent_registry
        agent = coordinator.agent_registry["dev-1"]
        assert agent.role == "developer"
        assert "python" in agent.skills
        assert agent.max_concurrent_tasks == 3
    
    @pytest.mark.asyncio
    async def test_analyze_issue_without_llm(self, coordinator, sample_issue_data):
        """Test issue analysis without LLM (fallback mode)."""
        with patch.object(coordinator, '_fetch_issue_data', return_value=sample_issue_data):
            plan = await coordinator.analyze_issue("owner/repo", 42)
        
        assert plan.issue_number == 42
        assert plan.repository == "owner/repo"
        assert len(plan.sub_tasks) > 0
        assert plan.status == PlanStatus.PLANNING.value
        assert plan.plan_id in coordinator.active_plans
    
    @pytest.mark.asyncio
    async def test_analyze_issue_with_llm(self, mock_llm_agent, sample_issue_data):
        """Test issue analysis with LLM."""
        # Mock LLM responses
        complexity_response = '{"complexity": "high", "scope": "feature", "estimated_hours": 8, "risks": [], "key_components": ["auth", "jwt"]}'
        tasks_response = '''[
            {"title": "Design auth", "description": "Plan design", "priority": 5, "estimated_effort": 60, "depends_on": [], "required_skills": ["architecture"]},
            {"title": "Implement JWT", "description": "Create JWT functions", "priority": 4, "estimated_effort": 120, "depends_on": ["task-42-1"], "required_skills": ["python"]}
        ]'''
        
        mock_llm_agent.query = AsyncMock(side_effect=[complexity_response, tasks_response])
        
        coordinator = CoordinatorAgent(llm_agent=mock_llm_agent)
        
        with patch.object(coordinator, '_fetch_issue_data', return_value=sample_issue_data):
            plan = await coordinator.analyze_issue("owner/repo", 42)
        
        assert plan.issue_number == 42
        assert len(plan.sub_tasks) == 2
        assert plan.sub_tasks[0].title == "Design auth"
        assert plan.sub_tasks[1].depends_on == ["task-42-1"]
    
    def test_build_dependency_graph(self, coordinator, sample_subtasks):
        """Test dependency graph building."""
        graph = coordinator._build_dependency_graph(sample_subtasks)
        
        assert graph["task-42-1"] == []
        assert graph["task-42-2"] == ["task-42-1"]
        assert graph["task-42-3"] == ["task-42-2"]
    
    def test_identify_required_roles(self, coordinator, sample_subtasks):
        """Test role identification."""
        analysis = {'complexity': 'medium', 'scope': 'feature'}
        roles = coordinator._identify_required_roles(sample_subtasks, analysis)
        
        assert AgentRole.COORDINATOR.value in roles
        assert AgentRole.DEVELOPER.value in roles
        assert AgentRole.TESTER.value in roles
    
    def test_topological_sort(self, coordinator, sample_subtasks):
        """Test topological sort of tasks."""
        dependencies = {
            "task-42-1": [],
            "task-42-2": ["task-42-1"],
            "task-42-3": ["task-42-2"]
        }
        
        sorted_tasks = coordinator._topological_sort(sample_subtasks, dependencies)
        
        # Task 1 should be first (no dependencies)
        assert sorted_tasks[0].id == "task-42-1"
        # Task 2 should be second
        assert sorted_tasks[1].id == "task-42-2"
        # Task 3 should be last
        assert sorted_tasks[2].id == "task-42-3"
    
    def test_find_best_agent_for_implementation(self, coordinator):
        """Test finding best agent for implementation task."""
        # Register agents
        dev_agent = AgentCapability(
            agent_id="dev-1",
            role=AgentRole.DEVELOPER.value,
            skills=["python"],
            current_task_count=0
        )
        tester_agent = AgentCapability(
            agent_id="tester-1",
            role=AgentRole.TESTER.value,
            skills=["testing"],
            current_task_count=0
        )
        
        task = SubTask(
            id="task-1",
            title="Implement feature X",
            description="Create new feature",
            priority=4
        )
        
        best_agent = coordinator._find_best_agent(task, [dev_agent, tester_agent])
        
        # Should prefer developer for implementation
        assert best_agent.agent_id == "dev-1"
    
    def test_find_best_agent_prefers_less_loaded(self, coordinator):
        """Test that agent selection prefers less loaded agents."""
        dev1 = AgentCapability(
            agent_id="dev-1",
            role=AgentRole.DEVELOPER.value,
            skills=["python"],
            current_task_count=2,
            max_concurrent_tasks=3
        )
        dev2 = AgentCapability(
            agent_id="dev-2",
            role=AgentRole.DEVELOPER.value,
            skills=["python"],
            current_task_count=0,
            max_concurrent_tasks=3
        )
        
        task = SubTask(
            id="task-1",
            title="Implement feature",
            description="Create feature",
            priority=4
        )
        
        best_agent = coordinator._find_best_agent(task, [dev1, dev2])
        
        # Should prefer dev-2 (less loaded)
        assert best_agent.agent_id == "dev-2"
    
    @pytest.mark.asyncio
    async def test_assign_tasks(self, coordinator, sample_subtasks):
        """Test task assignment."""
        # Create plan
        plan = ExecutionPlan(
            plan_id="plan-1",
            issue_number=42,
            repository="owner/repo",
            title="Test plan",
            sub_tasks=sample_subtasks,
            dependencies_graph={
                "task-42-1": [],
                "task-42-2": ["task-42-1"],
                "task-42-3": ["task-42-2"]
            }
        )
        
        # Register agents
        coordinator.register_agent("dev-1", "developer", ["python"])
        coordinator.register_agent("tester-1", "tester", ["testing"])
        
        assignments = await coordinator.assign_tasks(plan)
        
        assert len(assignments) > 0
        assert plan.status == PlanStatus.EXECUTING.value
        
        # Check that tasks were assigned
        for task in plan.sub_tasks:
            assert task.assigned_to is not None
    
    @pytest.mark.asyncio
    async def test_monitor_progress(self, coordinator, sample_subtasks):
        """Test progress monitoring."""
        plan = ExecutionPlan(
            plan_id="plan-1",
            issue_number=42,
            repository="owner/repo",
            title="Test plan",
            sub_tasks=sample_subtasks
        )
        
        coordinator.active_plans[plan.plan_id] = plan
        
        # Complete first task
        plan.sub_tasks[0].status = TaskStatus.COMPLETED.value
        
        status = await coordinator.monitor_progress(plan.plan_id)
        
        assert status['plan_id'] == plan.plan_id
        assert status['status_counts']['completed'] == 1
        assert status['status_counts']['pending'] == 2
        assert status['completion_percentage'] == pytest.approx(33.33, rel=0.1)
    
    @pytest.mark.asyncio
    async def test_monitor_progress_completion(self, coordinator, sample_subtasks):
        """Test that plan is marked complete when all tasks done."""
        plan = ExecutionPlan(
            plan_id="plan-1",
            issue_number=42,
            repository="owner/repo",
            title="Test plan",
            sub_tasks=sample_subtasks
        )
        
        coordinator.active_plans[plan.plan_id] = plan
        
        # Complete all tasks
        for task in plan.sub_tasks:
            task.status = TaskStatus.COMPLETED.value
        
        status = await coordinator.monitor_progress(plan.plan_id)
        
        assert status['completion_percentage'] == 100.0
        assert plan.status == PlanStatus.COMPLETED.value
    
    @pytest.mark.asyncio
    async def test_adapt_plan_with_blocker(self, coordinator, sample_subtasks):
        """Test plan adaptation when blocker is encountered."""
        plan = ExecutionPlan(
            plan_id="plan-1",
            issue_number=42,
            repository="owner/repo",
            title="Test plan",
            sub_tasks=sample_subtasks,
            dependencies_graph={
                "task-42-1": [],
                "task-42-2": ["task-42-1"],
                "task-42-3": ["task-42-2"]
            }
        )
        
        coordinator.active_plans[plan.plan_id] = plan
        
        blockers = [
            {
                'task_id': 'task-42-2',
                'issue': 'Missing dependency library',
                'solution': 'Install required library'
            }
        ]
        
        updated_plan = await coordinator.adapt_plan(plan.plan_id, blockers)
        
        # Should have created new task to resolve blocker
        assert len(updated_plan.sub_tasks) > len(sample_subtasks)
        
        # Blocked task should have blocker recorded
        blocked_task = next(t for t in updated_plan.sub_tasks if t.id == 'task-42-2')
        assert blocked_task.blocker is not None
    
    def test_get_plan(self, coordinator):
        """Test getting plan by ID."""
        plan = ExecutionPlan(
            plan_id="plan-1",
            issue_number=42,
            repository="owner/repo",
            title="Test plan"
        )
        
        coordinator.active_plans[plan.plan_id] = plan
        
        retrieved = coordinator.get_plan("plan-1")
        assert retrieved is not None
        assert retrieved.plan_id == "plan-1"
    
    def test_list_active_plans(self, coordinator):
        """Test listing active plans."""
        plan1 = ExecutionPlan(plan_id="plan-1", issue_number=1, repository="r1", title="Plan 1")
        plan2 = ExecutionPlan(plan_id="plan-2", issue_number=2, repository="r2", title="Plan 2")
        
        coordinator.active_plans["plan-1"] = plan1
        coordinator.active_plans["plan-2"] = plan2
        
        plans = coordinator.list_active_plans()
        
        assert len(plans) == 2
        assert any(p.plan_id == "plan-1" for p in plans)
        assert any(p.plan_id == "plan-2" for p in plans)
    
    def test_save_and_load_plan(self, coordinator, tmp_path):
        """Test saving and loading plan to/from file."""
        plan = ExecutionPlan(
            plan_id="plan-1",
            issue_number=42,
            repository="owner/repo",
            title="Test plan"
        )
        
        filepath = tmp_path / "plan.json"
        
        # Save plan
        coordinator.save_plan(plan, filepath)
        assert filepath.exists()
        
        # Load plan
        loaded_plan = coordinator.load_plan(filepath)
        assert loaded_plan.plan_id == "plan-1"
        assert loaded_plan.issue_number == 42


class TestSubTask:
    """Test SubTask dataclass."""
    
    def test_subtask_creation(self):
        """Test creating SubTask."""
        task = SubTask(
            id="task-1",
            title="Test task",
            description="Test description",
            priority=4,
            estimated_effort=60
        )
        
        assert task.id == "task-1"
        assert task.title == "Test task"
        assert task.status == TaskStatus.PENDING.value
        assert task.priority == 4
    
    def test_subtask_to_dict(self):
        """Test converting SubTask to dict."""
        task = SubTask(
            id="task-1",
            title="Test task",
            description="Test description"
        )
        
        data = task.to_dict()
        
        assert data['id'] == "task-1"
        assert data['title'] == "Test task"
        assert 'created_at' in data


class TestExecutionPlan:
    """Test ExecutionPlan dataclass."""
    
    def test_execution_plan_creation(self):
        """Test creating ExecutionPlan."""
        plan = ExecutionPlan(
            plan_id="plan-1",
            issue_number=42,
            repository="owner/repo",
            title="Test plan"
        )
        
        assert plan.plan_id == "plan-1"
        assert plan.issue_number == 42
        assert plan.status == PlanStatus.PLANNING.value
        assert plan.completion_percentage == 0.0
    
    def test_execution_plan_to_dict(self):
        """Test converting ExecutionPlan to dict."""
        task = SubTask(id="task-1", title="Task", description="Desc")
        plan = ExecutionPlan(
            plan_id="plan-1",
            issue_number=42,
            repository="owner/repo",
            title="Test plan",
            sub_tasks=[task]
        )
        
        data = plan.to_dict()
        
        assert data['plan_id'] == "plan-1"
        assert len(data['sub_tasks']) == 1
        assert data['sub_tasks'][0]['id'] == "task-1"


class TestTaskAssignment:
    """Test TaskAssignment dataclass."""
    
    def test_task_assignment_creation(self):
        """Test creating TaskAssignment."""
        assignment = TaskAssignment(
            task_id="task-1",
            agent_id="dev-1",
            priority=4
        )
        
        assert assignment.task_id == "task-1"
        assert assignment.agent_id == "dev-1"
        assert assignment.priority == 4
    
    def test_task_assignment_to_dict(self):
        """Test converting TaskAssignment to dict."""
        assignment = TaskAssignment(
            task_id="task-1",
            agent_id="dev-1"
        )
        
        data = assignment.to_dict()
        
        assert data['task_id'] == "task-1"
        assert data['agent_id'] == "dev-1"


class TestAgentCapability:
    """Test AgentCapability dataclass."""
    
    def test_agent_capability_creation(self):
        """Test creating AgentCapability."""
        capability = AgentCapability(
            agent_id="dev-1",
            role="developer",
            skills=["python", "testing"]
        )
        
        assert capability.agent_id == "dev-1"
        assert capability.role == "developer"
        assert "python" in capability.skills
        assert capability.availability is True
        assert capability.current_task_count == 0
