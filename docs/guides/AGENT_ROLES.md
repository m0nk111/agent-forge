# Agent Roles and Task Assignment

Agent-Forge uses a role-based system for task assignment and specialization. Each agent can have one or more roles that define their responsibilities and capabilities.

## Available Roles

### 1. **Coordinator**
- **Purpose**: Task planning, breakdown, and orchestration
- **Responsibilities**:
  - Analyze complex issues and break them into subtasks
  - Assign tasks to appropriate agents based on roles
  - Monitor progress and adapt plans
  - Handle blockers and dependencies
- **Typical Agent**: `qwen-main-agent`
- **Best For**: Complex multi-step projects, issue triage
- **Permissions**: Full access (read, write, coordinate)

### 2. **Developer**
- **Purpose**: Code generation, implementation, and bug fixes
- **Responsibilities**:
  - Write and modify code
  - Implement features from specifications
  - Fix bugs and issues
  - Refactor and optimize code
- **Typical Agent**: `your-agent`
- **Best For**: Feature development, bug fixes, refactoring
- **Permissions**: Code write access, terminal, file system

### 3. **Reviewer**
- **Purpose**: Code review and quality assurance
- **Responsibilities**:
  - Review pull requests
  - Check code quality and standards
  - Security auditing
  - Suggest improvements
- **Best For**: PR reviews, security checks, quality gates
- **Permissions**: Read access, comment on PRs, request changes

### 4. **Tester**
- **Purpose**: Testing and validation
- **Responsibilities**:
  - Write and run tests
  - Validate functionality
  - Check for regressions
  - Report test results
- **Best For**: Test automation, CI/CD validation
- **Permissions**: Read access, write tests, run test suites

### 5. **Documenter**
- **Purpose**: Documentation creation and maintenance
- **Responsibilities**:
  - Write documentation
  - Update README files
  - Create guides and tutorials
  - Maintain changelogs
- **Best For**: Documentation tasks, knowledge base updates
- **Permissions**: Read access, write docs, update wikis

### 6. **Bot** ⭐
- **Purpose**: Automated operations, posting, and organization
- **Responsibilities**:
  - Issue triage and labeling
  - Automated responses and notifications
  - Project board management
  - Status updates and summaries
  - Scheduled maintenance tasks
- **Typical Agent**: `your-bot-agent`
- **Best For**: Automation, notifications, organization, posting updates
- **Permissions**: Read-only (no code changes), issue management, project boards
- **Special Features**:
  - Higher concurrent task limit (can handle multiple operations)
  - More frequent polling (faster response times)
  - Lower temperature (consistent responses)
  - No shell access (security)

### 7. **Researcher**
- **Purpose**: Information gathering and analysis
- **Responsibilities**:
  - Research best practices
  - Analyze codebases
  - Find solutions to problems
  - Investigate issues
- **Best For**: Problem investigation, technology research
- **Permissions**: Read access, web search, codebase analysis

## Agent Configuration

### Single Role Agent (Specialized)
```yaml
agent_id: your-bot-agent
name: M0nk111 Bot
role: bot  # Single specialized role
capabilities:
  - issue_management
  - posting
  - organization
```

### Multi-Capability Agent (Flexible)
```yaml
agent_id: your-agent
name: M0nk111 Qwen Agent
role: developer  # Primary role
capabilities:
  - code_generation    # Can also do these
  - code_review
  - documentation
```

## Role-Based Task Assignment

The Coordinator Agent uses roles to assign tasks:

```python
# Example from coordinator_agent.py
class AgentRole(Enum):
    COORDINATOR = "coordinator"
    DEVELOPER = "developer"
    REVIEWER = "reviewer"
    TESTER = "tester"
    DOCUMENTER = "documenter"
    BOT = "bot"
    RESEARCHER = "researcher"
```

### Task Assignment Logic

1. **Issue Analysis**: Coordinator analyzes the issue
2. **Task Breakdown**: Split into subtasks
3. **Role Matching**: Each subtask assigned a required role
4. **Agent Selection**: Choose agent with matching role
5. **Execution**: Agent executes based on their permissions

### Example Task Flow

```
Issue: "Add user authentication"

Coordinator breaks down:
  1. Research authentication methods → RESEARCHER
  2. Implement auth backend → DEVELOPER
  3. Write tests → TESTER
  4. Review code → REVIEWER
  5. Update documentation → DOCUMENTER
  6. Post status update → BOT
```

## Bot Role Deep Dive

The **bot** role is special because it's designed for automation without code modification:

### Bot Capabilities
- ✅ **Issue Management**: Label, triage, close, comment
- ✅ **PR Management**: Review, request changes, merge (with approval)
- ✅ **Posting**: Status updates, summaries, notifications
- ✅ **Organization**: Project boards, milestones, labels
- ✅ **Automation**: Scheduled tasks, workflows
- ❌ **Code Changes**: Cannot directly modify code
- ❌ **Shell Access**: No terminal access

### Bot Use Cases

1. **Automated Triage**
   ```yaml
   # Bot receives new issue
   # - Auto-labels based on content
   # - Assigns to project board
   # - Notifies relevant team members
   ```

2. **Status Posting**
   ```yaml
   # Bot posts daily summaries
   # - Open issues count
   # - PR status
   # - Build status
   # - Deployment status
   ```

3. **Project Organization**
   ```yaml
   # Bot manages project boards
   # - Moves cards based on status
   # - Creates milestones
   # - Tracks progress
   ```

4. **Notifications**
   ```yaml
   # Bot sends notifications
   # - PR ready for review
   # - Build failures
   # - Deployment complete
   ```

### Bot Configuration Best Practices

```yaml
# Recommended bot settings
max_concurrent_tasks: 3-5      # Handle multiple operations
polling_interval: 30-60        # Faster response times
temperature: 0.2-0.4           # Consistent responses
local_shell_enabled: false     # Security: no shell access
shell_permissions: read_only   # Security: read-only
auto_merge: false              # Require human approval
```

## Multiple Agents with Same Role

You can have multiple agents with the same role for:
- **Load Balancing**: Distribute work across agents
- **Specialization**: Different models or configurations
- **Redundancy**: Backup if one agent is busy

### Example: Multiple Bots

```yaml
# Primary bot - fast responses
agent_id: your-bot-agent-fast
role: bot
model: qwen2.5-coder:7b
temperature: 0.3

# Secondary bot - detailed analysis
agent_id: your-bot-agent-analyzer
role: bot
model: qwen2.5:32b
temperature: 0.5
```

## Role Assignment in Code

### Coordinator Agent Example

```python
# From coordinator_agent.py
def assign_tasks(self, plan: ExecutionPlan) -> Dict[str, List[str]]:
    """Assign tasks to agents based on roles"""
    assignments = {}
    
    for task in plan.tasks:
        # Find agents with required role
        matching_agents = [
            agent for agent in self.available_agents
            if agent.role in task.required_roles
        ]
        
        # Assign to best available agent
        best_agent = self._select_best_agent(matching_agents, task)
        assignments[task.id] = best_agent.agent_id
    
    return assignments
```

## Benefits of Role-Based System

1. **Clear Responsibilities**: Each agent knows their purpose
2. **Efficient Task Assignment**: Automatic matching of tasks to capabilities
3. **Scalability**: Easy to add specialized agents
4. **Security**: Role-based permissions prevent unauthorized actions
5. **Flexibility**: Agents can have multiple capabilities within their role
6. **Organization**: Clear separation of concerns

## Future Enhancements

- **Dynamic Role Assignment**: Agents learn and adapt roles
- **Role Hierarchies**: Senior/junior roles with different permissions
- **Role-Based Metrics**: Track performance per role
- **Custom Roles**: Define your own specialized roles
- **Role Combinations**: Agents with multiple primary roles

## Summary

- **Roles define purpose** and responsibilities
- **Bot role** is special for automation without code changes
- **One agent, one primary role** for clarity
- **Multiple capabilities** within that role for flexibility
- **Role-based assignment** ensures right agent for right task
- **Permissions tied to roles** for security

Choose roles based on:
- Agent's strengths (model capabilities)
- Security requirements (permissions needed)
- Task frequency (bot for high-frequency automation)
- Complexity (coordinator for complex planning)
