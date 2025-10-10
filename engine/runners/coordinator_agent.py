"""
Coordinator Agent for multi-agent task planning and orchestration.

This agent specializes in breaking down complex issues into manageable sub-tasks,
assigning work to appropriate agents, monitoring progress, and adapting plans
when blockers are encountered.

Example:
    coordinator = CoordinatorAgent()
    plan = await coordinator.analyze_issue("owner/repo", 42)
    assignments = await coordinator.assign_tasks(plan)
    status = await coordinator.monitor_progress(plan.plan_id)
"""

import os
import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
from enum import Enum
import json
import yaml
import re

logger = logging.getLogger(__name__)


class AgentRole(Enum):
    """Agent role types."""
    COORDINATOR = "coordinator"
    DEVELOPER = "developer"
    REVIEWER = "reviewer"
    TESTER = "tester"
    DOCUMENTER = "documenter"
    BOT = "bot"
    RESEARCHER = "researcher"


class TaskStatus(Enum):
    """Task status values."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    FAILED = "failed"


class PlanStatus(Enum):
    """Execution plan status."""
    PLANNING = "planning"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


@dataclass
class SubTask:
    """Individual sub-task in an execution plan."""
    id: str
    title: str
    description: str
    assigned_to: Optional[str] = None
    depends_on: List[str] = field(default_factory=list)
    estimated_effort: int = 60  # minutes
    status: str = TaskStatus.PENDING.value
    priority: int = 3  # 1-5, 5 is highest
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    blocker: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        # Convert datetime objects to ISO format
        for key in ['created_at', 'started_at', 'completed_at']:
            if data[key]:
                data[key] = data[key].isoformat() if isinstance(data[key], datetime) else data[key]
        return data


@dataclass
class ExecutionPlan:
    """Complete execution plan for an issue."""
    plan_id: str
    issue_number: int
    repository: str
    title: str
    sub_tasks: List[SubTask] = field(default_factory=list)
    total_estimated_effort: int = 0  # minutes
    dependencies_graph: Dict[str, List[str]] = field(default_factory=dict)
    required_roles: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    status: str = PlanStatus.PLANNING.value
    completion_percentage: float = 0.0
    plan_priority: int = 3  # 1-5, 5 is highest
    labels: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Detach from externally provided mutable objects.

        Tests may reuse fixtures (lists/dicts) across plans. We copy here to
        avoid aliasing so mutations to this plan do not affect caller-owned
        fixtures and vice versa.
        """
        # Ensure new list object for sub_tasks (elements remain the same)
        if isinstance(self.sub_tasks, list):
            self.sub_tasks = list(self.sub_tasks)
        else:
            self.sub_tasks = []

        # Shallow copy lists within dependencies_graph
        if isinstance(self.dependencies_graph, dict):
            self.dependencies_graph = {
                k: list(v) if isinstance(v, list) else []
                for k, v in self.dependencies_graph.items()
            }
        else:
            self.dependencies_graph = {}

        # Copy other list-type fields
        if isinstance(self.required_roles, list):
            self.required_roles = list(self.required_roles)
        else:
            self.required_roles = []

        if isinstance(self.labels, list):
            self.labels = list(self.labels)
        else:
            self.labels = []
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        data = {
            'plan_id': self.plan_id,
            'issue_number': self.issue_number,
            'repository': self.repository,
            'title': self.title,
            'sub_tasks': [task.to_dict() for task in self.sub_tasks],
            'total_estimated_effort': self.total_estimated_effort,
            'dependencies_graph': self.dependencies_graph,
            'required_roles': self.required_roles,
            'created_at': self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,
            'updated_at': self.updated_at.isoformat() if isinstance(self.updated_at, datetime) else self.updated_at,
            'status': self.status,
            'completion_percentage': self.completion_percentage
        }
        return data


@dataclass
class TaskAssignment:
    """Assignment of task to agent."""
    task_id: str
    agent_id: str
    assigned_at: datetime = field(default_factory=datetime.now)
    deadline: Optional[datetime] = None
    priority: int = 3
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'task_id': self.task_id,
            'agent_id': self.agent_id,
            'assigned_at': self.assigned_at.isoformat() if isinstance(self.assigned_at, datetime) else self.assigned_at,
            'deadline': self.deadline.isoformat() if self.deadline and isinstance(self.deadline, datetime) else self.deadline,
            'priority': self.priority
        }


@dataclass
class AgentCapability:
    """Agent capability definition."""
    agent_id: str
    role: str
    skills: List[str] = field(default_factory=list)
    max_concurrent_tasks: int = 3
    current_task_count: int = 0
    availability: bool = True


class CoordinatorAgent:
    """
    Coordinator agent for multi-agent task planning and orchestration.
    
    Uses LLM for intelligent planning, task breakdown, and decision making.
    Coordinates multiple agents working on complex issues.
    
    Attributes:
        agent_id: Unique coordinator identifier
        role: Agent role (COORDINATOR)
        llm_agent: LLM agent for planning
        bot_agent: Bot agent for notifications
        active_plans: Dictionary of active execution plans
        agent_registry: Registry of available agents
    """
    
    def __init__(
        self,
        agent_id: str = "coordinator",
        llm_agent: Optional[Any] = None,
        bot_agent: Optional[Any] = None,
        config_file: Optional[Path] = None,
        monitor: Optional[Any] = None
    ):
        """
        Initialize coordinator agent.
        
        Args:
            agent_id: Unique coordinator identifier
            llm_agent: LLM agent for planning (Qwen, Claude, etc.)
            bot_agent: Bot agent for notifications
            config_file: Path to coordinator configuration
            monitor: MonitorService instance
        """
        self.agent_id = agent_id
        self.role = AgentRole.COORDINATOR
        self.llm_agent = llm_agent
        self.bot_agent = bot_agent
        self.monitor = monitor
        
        # Load configuration
        self.config = self._load_config(config_file)
        
        # Active plans (plan_id -> ExecutionPlan)
        self.active_plans: Dict[str, ExecutionPlan] = {}
        
        # Agent registry (agent_id -> AgentCapability)
        self.agent_registry: Dict[str, AgentCapability] = {}
        
        # Planning parameters from config
        self.max_sub_tasks = self.config.get('planning', {}).get('max_sub_tasks', 20)
        self.default_task_effort = self.config.get('planning', {}).get('default_task_effort', 30)
        self.max_concurrent_tasks = self.config.get('planning', {}).get('max_concurrent_tasks', 5)
        
        # Monitoring parameters
        self.check_interval = self.config.get('monitoring', {}).get('check_interval', 300)
        self.blocker_threshold = self.config.get('monitoring', {}).get('blocker_threshold', 1800)
        
        logger.info(f"Coordinator agent initialized: {self.agent_id}")
    
    def _load_config(self, config_file: Optional[Path]) -> Dict:
        """Load coordinator configuration from YAML."""
        if config_file and config_file.exists():
            with open(config_file, 'r') as f:
                return yaml.safe_load(f).get('coordinator', {})
        
        # Default configuration
        return {
            'llm': {
                'model': 'qwen2.5:72b',
                'endpoint': 'http://localhost:11434',
                'temperature': 0.3,
                'max_tokens': 4096
            },
            'planning': {
                'max_sub_tasks': 20,
                'default_task_effort': 30,
                'max_concurrent_tasks': 5
            },
            'monitoring': {
                'check_interval': 300,
                'blocker_threshold': 1800
            }
        }
    
    def register_agent(
        self,
        agent_id: str,
        role: str,
        skills: List[str],
        max_concurrent_tasks: int = 3
    ):
        """
        Register an agent in the registry.
        
        Args:
            agent_id: Unique agent identifier
            role: Agent role (developer, reviewer, etc.)
            skills: List of agent skills/capabilities
            max_concurrent_tasks: Max concurrent tasks for agent
        """
        capability = AgentCapability(
            agent_id=agent_id,
            role=role,
            skills=skills,
            max_concurrent_tasks=max_concurrent_tasks
        )
        self.agent_registry[agent_id] = capability
        logger.info(f"Registered agent: {agent_id} ({role}) with skills: {skills}")
    
    async def analyze_issue(
        self,
        repo: str,
        issue_number: int,
        issue_data: Optional[Dict] = None
    ) -> ExecutionPlan:
        """
        Analyze issue and create execution plan.
        
        Args:
            repo: Repository name (owner/repo)
            issue_number: Issue number
            issue_data: Optional issue data (fetched if not provided)
        
        Returns:
            ExecutionPlan with sub-tasks and dependencies
        """
        logger.info(f"Analyzing issue {repo}#{issue_number}")
        
        # Fetch issue data if not provided
        if not issue_data:
            issue_data = await self._fetch_issue_data(repo, issue_number)
        
        # Create plan ID
        plan_id = f"plan-{issue_number}-{int(datetime.now().timestamp())}"
        
        # Analyze complexity and requirements
        analysis = await self._analyze_complexity(issue_data)
        
        # Break down into sub-tasks
        sub_tasks = await self._create_sub_tasks(issue_data, analysis)
        
        # Build dependency graph
        dependencies_graph = self._build_dependency_graph(sub_tasks)
        
    # Identify required roles
        required_roles = self._identify_required_roles(sub_tasks, analysis)
        
        # Calculate total effort
        total_effort = sum(task.estimated_effort for task in sub_tasks)
        
        # Determine labels and plan priority
        labels = issue_data.get('labels', []) if isinstance(issue_data.get('labels', []), list) else []
        plan_priority = self._compute_plan_priority(labels)

        # Create execution plan
        plan = ExecutionPlan(
            plan_id=plan_id,
            issue_number=issue_number,
            repository=repo,
            title=issue_data.get('title', ''),
            sub_tasks=sub_tasks,
            total_estimated_effort=total_effort,
            dependencies_graph=dependencies_graph,
            required_roles=required_roles,
            status=PlanStatus.PLANNING.value,
            plan_priority=plan_priority,
            labels=labels
        )
        
        # Store plan
        self.active_plans[plan_id] = plan
        
        # Notify via bot if available
        if self.bot_agent:
            await self._notify_plan_created(plan)
        
        logger.info(f"Created execution plan {plan_id} with {len(sub_tasks)} sub-tasks")
        return plan

    def _compute_plan_priority(self, labels: List[str]) -> int:
        """Compute plan priority (1-5) from issue labels.

        Mapping:
        - critical, security, p0, high-priority -> 5
        - bug, p1, urgent -> 4
        - enhancement, feature -> 3
        - documentation, chore -> 2
        - low-priority, nice-to-have -> 1
        """
        label_set = {str(l).lower() for l in labels}
        if any(k in label_set for k in ["critical", "security", "p0", "high-priority"]):
            logger.debug("🔍 Plan priority computed: 5 (critical/security)")
            return 5
        if any(k in label_set for k in ["bug", "p1", "urgent"]):
            logger.debug("🔍 Plan priority computed: 4 (bug/urgent)")
            return 4
        if any(k in label_set for k in ["enhancement", "feature"]):
            logger.debug("🔍 Plan priority computed: 3 (enhancement/feature)")
            return 3
        if any(k in label_set for k in ["documentation", "chore"]):
            logger.debug("🔍 Plan priority computed: 2 (docs/chore)")
            return 2
        logger.debug("🔍 Plan priority computed: 1 (default low)")
        return 1

    async def get_next_task_assignment(
        self,
        available_agents: Optional[List[str]] = None
    ) -> Optional[TaskAssignment]:
        """Select and assign the next highest-priority task across all active plans.

        Returns the TaskAssignment if assignment succeeded, else None.
        """
        if not self.active_plans:
            logger.debug("🐛 No active plans available for assignment")
            return None

        # Prepare agent capabilities
        if available_agents:
            agents = [self.agent_registry.get(aid) for aid in available_agents if aid in self.agent_registry]
        else:
            agents = list(self.agent_registry.values())
        agents = [a for a in agents if a and a.availability and a.current_task_count < a.max_concurrent_tasks]
        if not agents:
            logger.warning("⚠️ No available agents for assignment")
            return None

        # Rank plans by plan_priority desc, then by created_at asc
        plans = sorted(
            self.active_plans.values(),
            key=lambda p: (-int(getattr(p, 'plan_priority', 3)), getattr(p, 'created_at', datetime.now()))
        )

        for plan in plans:
            # Get next unassigned task according to topo order and task priority
            sorted_tasks = self._topological_sort(plan.sub_tasks, plan.dependencies_graph)
            next_task = next((t for t in sorted_tasks if not t.assigned_to and t.status == TaskStatus.PENDING.value), None)
            if not next_task:
                continue

            best_agent = self._find_best_agent(next_task, agents)
            if not best_agent:
                continue

            assignment = TaskAssignment(
                task_id=next_task.id,
                agent_id=best_agent.agent_id,
                priority=next_task.priority
            )
            next_task.assigned_to = best_agent.agent_id
            best_agent.current_task_count += 1
            plan.status = PlanStatus.EXECUTING.value
            plan.updated_at = datetime.now()
            logger.info(f"✅ Assigned {next_task.id} from plan {plan.plan_id} (prio {plan.plan_priority}) to {best_agent.agent_id}")
            return assignment

        logger.info("⚠️ No assignable tasks found across active plans")
        return None
    
    async def _fetch_issue_data(self, repo: str, issue_number: int) -> Dict:
        """Fetch issue data from GitHub."""
        # Simplified implementation - in production, use GitHub API
        return {
            'number': issue_number,
            'title': f'Issue #{issue_number}',
            'body': 'Issue description',
            'labels': []
        }
    
    async def _analyze_complexity(self, issue_data: Dict) -> Dict:
        """
        Analyze issue complexity using LLM.
        
        Args:
            issue_data: GitHub issue data
        
        Returns:
            Analysis dict with complexity, scope, risks
        """
        if not self.llm_agent:
            # Fallback to rule-based analysis
            return {
                'complexity': 'medium',
                'scope': 'feature',
                'estimated_hours': 4,
                'risks': []
            }
        
        # Use LLM for intelligent analysis
        prompt = f"""Analyze this GitHub issue and provide a JSON response:

Title: {issue_data.get('title', '')}
Description: {issue_data.get('body', '')}
Labels: {', '.join(issue_data.get('labels', []))}

Provide analysis in JSON format:
{{
    "complexity": "low|medium|high|very_high",
    "scope": "bugfix|feature|refactoring|documentation",
    "estimated_hours": <number>,
    "risks": ["risk1", "risk2"],
    "key_components": ["component1", "component2"]
}}

Only respond with valid JSON."""
        
        try:
            response = await self.llm_agent.query(prompt, max_tokens=500)
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))
        except Exception as e:
            logger.warning(f"LLM analysis failed: {e}")
        
        # Fallback
        return {
            'complexity': 'medium',
            'scope': 'feature',
            'estimated_hours': 4,
            'risks': []
        }
    
    async def _create_sub_tasks(
        self,
        issue_data: Dict,
        analysis: Dict
    ) -> List[SubTask]:
        """
        Create sub-tasks using LLM or rule-based breakdown.
        
        Args:
            issue_data: GitHub issue data
            analysis: Complexity analysis
        
        Returns:
            List of SubTask objects
        """
        if not self.llm_agent:
            # Fallback to simple breakdown
            return [
                SubTask(
                    id=f"task-{issue_data['number']}-1",
                    title="Implement solution",
                    description="Implement the requested feature",
                    priority=4,
                    estimated_effort=120
                ),
                SubTask(
                    id=f"task-{issue_data['number']}-2",
                    title="Write tests",
                    description="Add comprehensive tests",
                    depends_on=[f"task-{issue_data['number']}-1"],
                    priority=3,
                    estimated_effort=60
                ),
                SubTask(
                    id=f"task-{issue_data['number']}-3",
                    title="Update documentation",
                    description="Update README and docs",
                    depends_on=[f"task-{issue_data['number']}-1"],
                    priority=2,
                    estimated_effort=30
                )
            ]
        
        # Use LLM for intelligent task breakdown
        prompt = f"""Break down this GitHub issue into sub-tasks:

Title: {issue_data.get('title', '')}
Description: {issue_data.get('body', '')}
Complexity: {analysis.get('complexity', 'medium')}
Scope: {analysis.get('scope', 'feature')}

Create up to {self.max_sub_tasks} sub-tasks in JSON array format:
[
    {{
        "title": "Task title",
        "description": "Detailed description",
        "priority": 1-5,
        "estimated_effort": <minutes>,
        "depends_on": ["task-X-Y"],
        "required_skills": ["python", "testing"]
    }}
]

Guidelines:
- Priority: 5 (critical) to 1 (nice-to-have)
- Include dependencies using task IDs
- Estimated effort in minutes
- Consider: design, implementation, testing, documentation
- Order tasks logically

Only respond with valid JSON array."""
        
        try:
            response = await self.llm_agent.query(prompt, max_tokens=2000)
            # Extract JSON array
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                tasks_data = json.loads(json_match.group(0))
                
                sub_tasks = []
                for idx, task_data in enumerate(tasks_data[:self.max_sub_tasks]):
                    task_id = f"task-{issue_data['number']}-{idx+1}"
                    sub_task = SubTask(
                        id=task_id,
                        title=task_data.get('title', f'Task {idx+1}'),
                        description=task_data.get('description', ''),
                        priority=task_data.get('priority', 3),
                        estimated_effort=task_data.get('estimated_effort', self.default_task_effort),
                        depends_on=task_data.get('depends_on', [])
                    )
                    sub_tasks.append(sub_task)
                
                return sub_tasks
        except Exception as e:
            logger.warning(f"LLM task breakdown failed: {e}")
        
        # Fallback to simple breakdown
        return [
            SubTask(
                id=f"task-{issue_data['number']}-1",
                title="Implement solution",
                description="Implement the requested feature",
                priority=4,
                estimated_effort=120
            )
        ]
    
    def _build_dependency_graph(self, sub_tasks: List[SubTask]) -> Dict[str, List[str]]:
        """Build dependency graph from sub-tasks."""
        graph = {}
        for task in sub_tasks:
            graph[task.id] = task.depends_on
        return graph
    
    def _identify_required_roles(
        self,
        sub_tasks: List[SubTask],
        analysis: Dict
    ) -> List[str]:
        """Identify required agent roles for plan execution."""
        roles = set([AgentRole.COORDINATOR.value])
        
        # Add developer for implementation tasks
        if any('implement' in task.title.lower() for task in sub_tasks):
            roles.add(AgentRole.DEVELOPER.value)
        
        # Add tester if tests needed
        if any('test' in task.title.lower() for task in sub_tasks):
            roles.add(AgentRole.TESTER.value)
        
        # Add documenter if docs needed
        if any('doc' in task.title.lower() for task in sub_tasks):
            roles.add(AgentRole.DOCUMENTER.value)
        
        # Add reviewer for code review
        if analysis.get('complexity') in ['high', 'very_high']:
            roles.add(AgentRole.REVIEWER.value)
        
        return list(roles)
    
    async def assign_tasks(
        self,
        plan: ExecutionPlan,
        available_agents: Optional[List[str]] = None
    ) -> List[TaskAssignment]:
        """
        Assign tasks to appropriate agents.
        
        Args:
            plan: Execution plan with sub-tasks
            available_agents: Optional list of available agent IDs
        
        Returns:
            List of TaskAssignment objects
        """
        logger.info(f"Assigning tasks for plan {plan.plan_id}")
        
        assignments = []
        
        # Get available agents from registry or parameter
        if available_agents:
            agents = [self.agent_registry.get(aid) for aid in available_agents if aid in self.agent_registry]
        else:
            agents = list(self.agent_registry.values())
        
        # Filter available agents
        agents = [a for a in agents if a and a.availability and a.current_task_count < a.max_concurrent_tasks]
        
        # Sort tasks by priority (highest first) and dependencies
        sorted_tasks = self._topological_sort(plan.sub_tasks, plan.dependencies_graph)
        
        for task in sorted_tasks:
            # Skip if already assigned
            if task.assigned_to:
                continue
            
            # Find best agent for task
            best_agent = self._find_best_agent(task, agents)
            
            if best_agent:
                # Create assignment
                assignment = TaskAssignment(
                    task_id=task.id,
                    agent_id=best_agent.agent_id,
                    priority=task.priority
                )
                
                # Update task
                task.assigned_to = best_agent.agent_id
                
                # Update agent load
                best_agent.current_task_count += 1
                
                assignments.append(assignment)
                
                # Notify via bot
                if self.bot_agent:
                    await self._notify_task_assigned(plan, task, best_agent.agent_id)
                
                logger.info(f"Assigned task {task.id} to {best_agent.agent_id}")
            else:
                logger.warning(f"No available agent for task {task.id}")
        
        # Update plan status
        plan.status = PlanStatus.EXECUTING.value
        plan.updated_at = datetime.now()
        
        return assignments
    
    def _topological_sort(
        self,
        tasks: List[SubTask],
        dependencies: Dict[str, List[str]]
    ) -> List[SubTask]:
        """Sort tasks topologically based on dependencies."""
        # Create task lookup
        task_map = {task.id: task for task in tasks}
        
        # Calculate in-degrees
        in_degree = {task.id: len(dependencies.get(task.id, [])) for task in tasks}
        
        # Queue of tasks with no dependencies
        queue = [task for task in tasks if in_degree[task.id] == 0]
        
        # Sort by priority within same dependency level
        queue.sort(key=lambda t: -t.priority)
        
        result = []
        
        while queue:
            # Pop highest priority task
            current = queue.pop(0)
            result.append(current)
            
            # Reduce in-degree for dependent tasks
            for task in tasks:
                if current.id in dependencies.get(task.id, []):
                    in_degree[task.id] -= 1
                    if in_degree[task.id] == 0:
                        queue.append(task)
                        queue.sort(key=lambda t: -t.priority)
        
        return result
    
    def _find_best_agent(
        self,
        task: SubTask,
        available_agents: List[AgentCapability]
    ) -> Optional[AgentCapability]:
        """Find best agent for task based on skills and availability."""
        if not available_agents:
            return None
        
        # Score agents based on suitability
        scores = []
        for agent in available_agents:
            score = 0
            
            # Check role match
            task_lower = task.title.lower()
            if 'implement' in task_lower or 'create' in task_lower or 'add' in task_lower:
                if agent.role == AgentRole.DEVELOPER.value:
                    score += 10
            elif 'test' in task_lower:
                if agent.role in [AgentRole.TESTER.value, AgentRole.DEVELOPER.value]:
                    score += 10
            elif 'review' in task_lower:
                if agent.role == AgentRole.REVIEWER.value:
                    score += 10
            elif 'doc' in task_lower:
                if agent.role == AgentRole.DOCUMENTER.value:
                    score += 10
            
            # Check current load (prefer less loaded agents)
            load_factor = 1.0 - (agent.current_task_count / agent.max_concurrent_tasks)
            score += load_factor * 5
            
            scores.append((agent, score))
        
        # Return agent with highest score
        scores.sort(key=lambda x: -x[1])
        return scores[0][0] if scores else None
    
    async def monitor_progress(self, plan_id: str) -> Dict:
        """
        Monitor progress of active plan.
        
        Args:
            plan_id: Plan identifier
        
        Returns:
            Status dict with progress, blockers, completed tasks
        """
        if plan_id not in self.active_plans:
            return {'error': 'Plan not found'}
        
        plan = self.active_plans[plan_id]
        
        # Count task statuses
        status_counts = {
            'pending': 0,
            'in_progress': 0,
            'completed': 0,
            'blocked': 0,
            'failed': 0
        }
        
        blockers = []
        completed_tasks = []
        
        for task in plan.sub_tasks:
            status_counts[task.status] += 1
            
            if task.status == TaskStatus.COMPLETED.value:
                completed_tasks.append(task.id)
            elif task.status == TaskStatus.BLOCKED.value:
                blockers.append({
                    'task_id': task.id,
                    'blocker': task.blocker
                })
        
        # Calculate completion percentage
        total_tasks = len(plan.sub_tasks)
        completed_count = status_counts['completed']
        plan.completion_percentage = (completed_count / total_tasks * 100) if total_tasks > 0 else 0
        
        # Check if plan is complete
        if completed_count == total_tasks:
            plan.status = PlanStatus.COMPLETED.value
            logger.info(f"Plan {plan_id} completed!")
        
        return {
            'plan_id': plan_id,
            'status': plan.status,
            'completion_percentage': plan.completion_percentage,
            'status_counts': status_counts,
            'blockers': blockers,
            'completed_tasks': completed_tasks,
            'total_tasks': total_tasks
        }
    
    async def adapt_plan(
        self,
        plan_id: str,
        blockers: List[Dict]
    ) -> ExecutionPlan:
        """
        Adapt plan based on blockers or changes.
        
        Args:
            plan_id: Plan identifier
            blockers: List of blocker dicts with task_id, issue, solution
        
        Returns:
            Updated ExecutionPlan
        """
        if plan_id not in self.active_plans:
            raise ValueError(f"Plan {plan_id} not found")
        
        plan = self.active_plans[plan_id]
        
        logger.info(f"Adapting plan {plan_id} due to {len(blockers)} blocker(s)")
        
        for blocker in blockers:
            task_id = blocker.get('task_id')
            issue = blocker.get('issue')
            solution = blocker.get('solution')
            
            # Find blocked task
            blocked_task = next((t for t in plan.sub_tasks if t.id == task_id), None)
            if not blocked_task:
                continue
            
            # Create new task to resolve blocker
            new_task_id = f"{task_id}-fix"
            new_task = SubTask(
                id=new_task_id,
                title=f"Resolve blocker: {issue}",
                description=solution or f"Fix issue preventing {blocked_task.title}",
                priority=5,  # High priority
                estimated_effort=30
            )
            
            # Insert new task before blocked task
            plan.sub_tasks.insert(
                plan.sub_tasks.index(blocked_task),
                new_task
            )
            
            # Update dependencies
            blocked_task.depends_on.append(new_task_id)
            plan.dependencies_graph[blocked_task.id] = blocked_task.depends_on
            
            # Update blocked task status
            blocked_task.blocker = issue
            
            logger.info(f"Created task {new_task_id} to resolve blocker")
        
        plan.updated_at = datetime.now()
        
        # Notify via bot
        if self.bot_agent:
            await self._notify_plan_adapted(plan, blockers)
        
        return plan
    
    async def _notify_plan_created(self, plan: ExecutionPlan):
        """Notify via bot that plan was created."""
        if not self.bot_agent:
            return
        
        task_list = "\n".join([
            f"{idx+1}. {'✓' if task.status == TaskStatus.COMPLETED.value else '⏳'} {task.title} ({task.estimated_effort}m)"
            for idx, task in enumerate(plan.sub_tasks[:10])  # First 10 tasks
        ])
        
        timeline_hours = plan.total_estimated_effort / 60
        timeline_days = timeline_hours / 8  # Assuming 8 hour workdays
        
        body = f"""🎯 **Execution Plan Created**

**Feature**: {plan.title}
**Estimated Effort**: ~{timeline_hours:.1f} hours
**Sub-tasks**: {len(plan.sub_tasks)}

**Task Breakdown**:
{task_list}

**Timeline**: Estimated completion in {timeline_days:.1f} days with current resources.
"""
        
        try:
            await self.bot_agent.add_comment(
                repo=plan.repository,
                issue_number=plan.issue_number,
                body=body
            )
        except Exception as e:
            logger.error(f"Failed to notify plan creation: {e}")
    
    async def _notify_task_assigned(
        self,
        plan: ExecutionPlan,
        task: SubTask,
        agent_id: str
    ):
        """Notify via bot that task was assigned."""
        if not self.bot_agent:
            return
        
        body = f"""🤖 **Task Assigned**

@{agent_id} has been assigned to work on:

**Task**: {task.title}
**Description**: {task.description}
**Priority**: {task.priority}/5
**Estimated Effort**: {task.estimated_effort} minutes

Please update progress in the issue comments."""
        
        try:
            await self.bot_agent.add_comment(
                repo=plan.repository,
                issue_number=plan.issue_number,
                body=body
            )
        except Exception as e:
            logger.error(f"Failed to notify task assignment: {e}")
    
    async def _notify_plan_adapted(
        self,
        plan: ExecutionPlan,
        blockers: List[Dict]
    ):
        """Notify via bot that plan was adapted."""
        if not self.bot_agent:
            return
        
        blocker_list = "\n".join([
            f"- **{b.get('task_id')}**: {b.get('issue')}"
            for b in blockers
        ])
        
        body = f"""🔄 **Plan Adapted**

Plan has been updated due to blockers:

{blocker_list}

New tasks have been created to resolve these issues.
Execution will continue once blockers are cleared."""
        
        try:
            await self.bot_agent.add_comment(
                repo=plan.repository,
                issue_number=plan.issue_number,
                body=body
            )
        except Exception as e:
            logger.error(f"Failed to notify plan adaptation: {e}")
    
    def get_plan(self, plan_id: str) -> Optional[ExecutionPlan]:
        """Get execution plan by ID."""
        return self.active_plans.get(plan_id)
    
    def list_active_plans(self) -> List[ExecutionPlan]:
        """List all active plans."""
        return list(self.active_plans.values())
    
    def save_plan(self, plan: ExecutionPlan, filepath: Path):
        """Save plan to JSON file."""
        with open(filepath, 'w') as f:
            json.dump(plan.to_dict(), f, indent=2)
        logger.info(f"Saved plan {plan.plan_id} to {filepath}")
    
    def load_plan(self, filepath: Path) -> ExecutionPlan:
        """Load plan from JSON file."""
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        # Reconstruct plan (simplified - would need full reconstruction)
        plan = ExecutionPlan(
            plan_id=data['plan_id'],
            issue_number=data['issue_number'],
            repository=data['repository'],
            title=data['title'],
            status=data['status']
        )
        
        self.active_plans[plan.plan_id] = plan
        logger.info(f"Loaded plan {plan.plan_id} from {filepath}")
        return plan


async def main():
    """CLI interface for testing coordinator."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Coordinator Agent CLI")
    parser.add_argument("operation", choices=["analyze", "assign", "monitor", "status"])
    parser.add_argument("--repo", required=True, help="Repository (owner/repo)")
    parser.add_argument("--issue", type=int, help="Issue number")
    parser.add_argument("--plan-id", help="Plan ID")
    parser.add_argument("--config", type=Path, help="Config file")
    
    args = parser.parse_args()
    
    coordinator = CoordinatorAgent(config_file=args.config)
    
    try:
        if args.operation == "analyze":
            if not args.issue:
                print("Error: --issue required for analyze")
                return 1
            
            plan = await coordinator.analyze_issue(args.repo, args.issue)
            print(f"✅ Created plan {plan.plan_id} with {len(plan.sub_tasks)} tasks")
            print(f"Estimated effort: {plan.total_estimated_effort} minutes")
        
        elif args.operation == "status":
            plans = coordinator.list_active_plans()
            print(f"Active plans: {len(plans)}")
            for plan in plans:
                print(f"  - {plan.plan_id}: {plan.title} ({plan.status})")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main()))
