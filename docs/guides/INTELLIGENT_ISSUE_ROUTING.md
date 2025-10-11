# Intelligent Issue Routing & Agent Escalation Architecture

**Status**: Design Complete, Ready for Integration  
**Created**: October 11, 2025  
**Updated**: October 11, 2025 - **CRITICAL ARCHITECTURE CHANGE**  
**Purpose**: Coordinator as mandatory gateway for ALL issues

---

## CRITICAL UPDATE: Coordinator-First Architecture

### ⚠️ Architecture Change

**PREVIOUS DESIGN** (Discarded):
```
Polling → Quick pre-check → Route decision → Code agent or Coordinator
```

**NEW DESIGN** (Mandatory):
```
Polling → ALWAYS Coordinator → Coordinator decides → Delegate or Orchestrate
```

### Why This Change?

**The coordinator MUST be the intelligence hub:**
- ✅ Coordinator has LLM for semantic analysis
- ✅ Coordinator makes ALL routing decisions
- ✅ No "dumb" pre-filtering by polling service
- ✅ Coordinator can delegate OR orchestrate
- ✅ Single point of intelligent decision-making

**Polling service role:**
- Detect issues with `agent-ready` label
- Call coordinator gateway
- **NEVER** decide routing itself

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│              MANDATORY COORDINATOR GATEWAY                   │
└─────────────────────────────────────────────────────────────┘
                             
Issue with "agent-ready" label
         ↓
Polling Service detects
         ↓
    ┌────────────────────────────────┐
    │ ALWAYS → Coordinator Gateway   │
    │ (CoordinatorGateway)           │
    │ - LLM-powered analysis         │
    │ - IssueComplexityAnalyzer      │
    │ - Makes routing decision       │
    └────────────────────────────────┘
         ↓
    ┌───┴───┬───────────┬────────────┐
    │       │           │            │
   SIMPLE  UNCERTAIN  COMPLEX       │
         │           │            │
    ↓       ↓           ↓            │
  Delegate Delegate+  Orchestrate  │
  to Code  Escalation  Sub-Issues  │
  Agent    Enabled                  │
    │       │           │            │
    └───────┴───────────┴────────────┘
                             
┌─────────────────────────────────────────────────────────────┐
│                  STAGE 2: ESCALATION                        │
└─────────────────────────────────────────────────────────────┘

Code agent executes
         ↓
Monitors complexity signals:
  - Files affected (>5?)
  - Components touched (>3?)
  - Time stuck (>30 min?)
  - Failed attempts (≥2?)
  - Architecture changes?
         ↓
    ┌────────────────────────┐
    │ AgentEscalator         │
    │ - Detects triggers     │
    │ - Posts comment        │
    │ - Calls coordinator    │
    └────────────────────────┘
         ↓
Coordinator takes over:
  - Creates sub-issues
  - Builds execution plan
  - Assigns multiple agents
  - Monitors progress
```

---

## Component 1: IssueComplexityAnalyzer

**File**: `engine/operations/issue_complexity_analyzer.py`  
**Purpose**: Pre-flight complexity analysis for intelligent routing

### Complexity Signals (9 metrics)

| Signal | Weight | Thresholds |
|--------|--------|------------|
| Description length | 0-5 pts | >2000 chars = 5 pts |
| Task count | 0-10 pts | ≥10 tasks = 10 pts |
| File mentions | 0-8 pts | ≥8 files = 8 pts |
| Code blocks | 0-3 pts | ≥6 blocks = 3 pts |
| Dependencies | 0-5 pts | Each mention = 2 pts |
| Refactor keywords | 0-8 pts | Present = 8 pts |
| Architecture keywords | 0-10 pts | Present = 10 pts |
| Multi-component keywords | 0-6 pts | Present = 6 pts |
| Complex labels | 0-10 pts | Present = 10 pts |

**Total Score**: 0-65 points

### Keywords Detected

**Refactor**: refactor, redesign, rewrite, restructure, migrate, upgrade, modernize

**Architecture**: architecture, system design, infrastructure, framework, platform, integration

**Multi-component**: multiple, several, across, throughout, coordinate, orchestrate, synchronize

**Complex Labels**: refactor, architecture, multi-agent, infrastructure, breaking-change, epic

### Routing Logic

```python
if score <= 10:      # SIMPLE
    routing = 'code_agent'
    escalation = False
    
elif score <= 25:    # UNCERTAIN
    routing = 'code_agent_with_escalation'
    escalation = True
    
else:                # COMPLEX (>25)
    routing = 'coordinator'
    escalation = N/A (already at coordinator)
```

### Usage Example

```python
from engine.operations.issue_complexity_analyzer import IssueComplexityAnalyzer

analyzer = IssueComplexityAnalyzer(llm_agent=None)

result = analyzer.analyze_issue(
    title="Refactor authentication system",
    body="""Need to redesign auth to support:
    - OAuth2 providers
    - Multi-factor authentication  
    - Session management across 6 microservices
    
    Files affected:
    - auth_service.py
    - user_manager.py
    - session_store.py
    - api_gateway.py
    - frontend_auth.js
    - token_validator.py
    """,
    labels=["refactor", "architecture"]
)

print(result)
# {
#   'complexity': 'complex',
#   'score': 34,
#   'routing': 'coordinator',
#   'confidence': 0.90,
#   'reasoning': 'Issue is complex - requires coordinator orchestration',
#   'escalation_enabled': False
# }
```

---

## Component 2: AgentEscalator

**File**: `engine/operations/agent_escalator.py`  
**Purpose**: Mid-execution escalation when complexity emerges

### Escalation Triggers

| Trigger | Threshold | Reasoning |
|---------|-----------|-----------|
| Files affected | >5 | Beyond single-agent scope |
| Components touched | >3 | Multi-component coordination needed |
| Failed attempts | ≥2 | Approach not working |
| Stuck time | >30 min | Agent blocked |
| Architecture changes | Boolean | Structural impact |
| Requires coordination | Boolean | Multi-agent needed |

### Escalation Workflow

```python
# In code_agent execution loop

escalator = AgentEscalator(
    agent_id="code_agent_1",
    github_token=token,
    coordinator_agent=coordinator
)

# Build escalation context
context = EscalationContext(
    files_affected=len(changed_files),
    components_touched=["auth", "api", "db", "frontend"],
    time_spent_minutes=35.5,
    architecture_changes_needed=True
)

# Check if should escalate
if escalator.should_escalate(context):
    result = escalator.escalate_to_coordinator(
        owner="m0nk111",
        repo="agent-forge",
        issue_number=94,
        issue_data=issue,
        progress_so_far={
            'files_analyzed': ['auth.py', 'session.py', ...],
            'research_findings': ['OAuth2 integration needed', ...],
            'attempted_solutions': 1
        },
        reason="Architecture refactor required across 4 components"
    )
    
    if result.escalated:
        logger.info(f"✅ Escalated to coordinator: {result.coordinator_plan_id}")
        logger.info(f"   Sub-issues created: {result.sub_issues_created}")
        return  # Exit agent, let coordinator take over
```

### Escalation Comment Posted

When escalating, agent posts:

```markdown
🚨 **Agent Escalation - Coordinator Needed**

Agent `code_agent_1` has escalated this issue to the coordinator for multi-agent orchestration.

**Escalation Reason:**
Too many files affected (8 > 5); Architecture changes required

**Progress So Far:**
- Files analyzed: 8
- Research findings: 3 items
- Attempted solutions: 1

**Next Steps:**
The coordinator agent will:
1. Break down this issue into sub-issues
2. Create an execution plan
3. Assign specialized agents to each sub-issue
4. Monitor progress and coordinate work

⏳ Estimated coordination setup time: 2-5 minutes
```

---

## Integration Points

### 1. Polling Service Integration

**File**: `engine/runners/polling_service.py`

**Current workflow**:
```python
def process_issues(self, issues):
    for issue in issues:
        # Claim issue
        # Start code_agent
        pass
```

**New workflow**:
```python
def process_issues(self, issues):
    for issue in issues:
        # TRIAGE STEP (NEW)
        analysis = self.triage_issue(issue)
        
        if analysis['routing'] == 'code_agent':
            self.start_code_agent(issue, escalation=False)
        elif analysis['routing'] == 'code_agent_with_escalation':
            self.start_code_agent(issue, escalation=True)
        elif analysis['routing'] == 'coordinator':
            self.start_coordinator(issue)

def triage_issue(self, issue):
    """Quick complexity analysis before routing."""
    from engine.operations.issue_complexity_analyzer import IssueComplexityAnalyzer
    
    analyzer = IssueComplexityAnalyzer()
    return analyzer.analyze_issue(
        title=issue['title'],
        body=issue['body'],
        labels=[l['name'] for l in issue['labels']]
    )
```

### 2. Code Agent Integration

**File**: `engine/runners/code_agent.py`

**Add escalation capability**:
```python
class CodeAgent:
    def __init__(self, ..., enable_escalation=False):
        self.enable_escalation = enable_escalation
        self.escalator = AgentEscalator(
            agent_id=self.agent_id,
            coordinator_agent=self.get_coordinator()
        ) if enable_escalation else None
    
    def execute_issue(self, issue):
        start_time = time.time()
        files_changed = []
        
        # Work on issue...
        
        # Check escalation triggers periodically
        if self.escalator:
            elapsed = (time.time() - start_time) / 60
            context = EscalationContext(
                files_affected=len(files_changed),
                time_spent_minutes=elapsed
            )
            
            if self.escalator.should_escalate(context):
                result = self.escalator.escalate_to_coordinator(...)
                if result.escalated:
                    return  # Exit, coordinator takes over
```

### 3. Coordinator Agent Integration

**File**: `engine/runners/coordinator_agent.py`

**Enable takeover from escalated agents**:
```python
class CoordinatorAgent:
    def handle_escalation(self, issue_data, agent_progress):
        """Handle mid-execution escalation from agent."""
        
        # Parse agent's progress
        existing_work = self._parse_agent_progress(agent_progress)
        
        # Analyze full complexity
        plan = self.analyze_issue(
            owner=issue_data['owner'],
            repo=issue_data['repo'],
            issue_number=issue_data['number'],
            existing_progress=existing_work
        )
        
        # Create sub-issues
        sub_issues = self.create_sub_issues(plan)
        
        # Build execution plan
        execution_plan = self.create_execution_plan(plan)
        
        # Assign agents to sub-issues
        assignments = self.assign_tasks(execution_plan)
        
        return {
            'plan_id': execution_plan.plan_id,
            'sub_issues': sub_issues,
            'status': 'coordinating'
        }
```

---

## Configuration

### Thresholds (Tunable)

**IssueComplexityAnalyzer**:
```python
SIMPLE_THRESHOLD = 10      # 0-10: Single agent
COMPLEX_THRESHOLD = 25     # >25: Coordinator
```

**AgentEscalator**:
```python
MAX_FILES_SIMPLE = 5           # >5 files → escalate
MAX_COMPONENTS_SIMPLE = 3      # >3 components → escalate
MAX_FAILED_ATTEMPTS = 2        # ≥2 failures → escalate
MAX_STUCK_TIME_MINUTES = 30    # >30 min → escalate
```

### Labels

**New labels to create**:
- `needs-coordination`: Added when escalation happens but coordinator unavailable
- `coordinator-processing`: Added when coordinator takes over
- `escalated-from-agent`: Track escalation history

---

## Benefits

### 1. Efficient Resource Usage
- Simple issues → Fast single-agent execution
- Complex issues → Proper orchestration from start
- No wasted cycles on mismatched assignments

### 2. Dynamic Adaptation
- "Looks simple but actually complex" → Escalate mid-flight
- Handles unexpected complexity discovered during work
- Agent can request help instead of failing

### 3. Scalable Decision Making
- Objective metrics (not subjective judgment)
- Tunable thresholds
- Clear escalation criteria

### 4. Better Outcomes
- Complex issues get proper sub-task breakdown
- Multiple agents can work in parallel
- Coordinator monitors dependencies

### 5. Transparency
- Clear escalation comments
- Reasoning documented
- Progress preserved during handoff

---

## Example Scenarios

### Scenario 1: Obviously Complex (Pre-Flight Detection)

**Issue**: "Redesign authentication system architecture"
- **Signals**: Keywords "redesign", "architecture", "system"; label "architecture"
- **Score**: 34 points
- **Routing**: `coordinator` (immediate)
- **Result**: Coordinator breaks into sub-issues from start

### Scenario 2: Uncertain (Start Simple, Allow Escalation)

**Issue**: "Fix user login validation"
- **Signals**: Moderate description, 2 files mentioned
- **Score**: 18 points
- **Routing**: `code_agent_with_escalation`
- **Result**: Agent starts work, escalates if discovers more complexity

### Scenario 3: Mid-Flight Escalation

**Issue**: "Update API response format"
- **Initial Score**: 8 points (appears simple)
- **Routing**: `code_agent` (no escalation)
- **During Work**: Agent discovers 7 files affected across 3 services
- **Escalation Triggered**: Files (7>5) + Components (3=threshold)
- **Result**: Agent escalates, coordinator creates sub-issues

### Scenario 4: Simple Issue (Fast Path)

**Issue**: "Fix typo in README.md"
- **Signals**: Short description, 1 file, label "documentation"
- **Score**: 3 points
- **Routing**: `code_agent` (direct)
- **Result**: Agent completes quickly, no coordination needed

---

## Testing Strategy

### Unit Tests

**IssueComplexityAnalyzer**:
```python
def test_simple_issue():
    analyzer = IssueComplexityAnalyzer()
    result = analyzer.analyze_issue(
        title="Fix typo",
        body="Change 'teh' to 'the' in README.md",
        labels=["documentation"]
    )
    assert result['complexity'] == 'simple'
    assert result['score'] <= 10

def test_complex_issue():
    analyzer = IssueComplexityAnalyzer()
    result = analyzer.analyze_issue(
        title="Refactor architecture",
        body="Redesign system across 8 components...",
        labels=["refactor", "architecture"]
    )
    assert result['complexity'] == 'complex'
    assert result['score'] > 25
```

**AgentEscalator**:
```python
def test_escalation_trigger_files():
    escalator = AgentEscalator("test_agent")
    context = EscalationContext(files_affected=6)
    assert escalator.should_escalate(context)

def test_no_escalation_simple():
    escalator = AgentEscalator("test_agent")
    context = EscalationContext(files_affected=2, time_spent_minutes=10)
    assert not escalator.should_escalate(context)
```

### Integration Tests

**End-to-End Triage**:
```python
def test_triage_to_coordinator():
    """Test complex issue routes to coordinator."""
    polling = PollingService()
    issue = create_test_issue(complexity='complex')
    
    # Should route to coordinator
    routing = polling.triage_issue(issue)
    assert routing['routing'] == 'coordinator'

def test_escalation_workflow():
    """Test agent escalation during execution."""
    agent = CodeAgent(enable_escalation=True)
    issue = create_test_issue(complexity='simple')
    
    # Start execution
    agent.execute_issue(issue)
    
    # Simulate complexity discovery
    agent.escalator.escalate_to_coordinator(...)
    
    # Verify coordinator takeover
    assert coordinator.has_active_plan(issue['number'])
```

---

## Implementation Checklist

- [x] Design architecture
- [x] Create IssueComplexityAnalyzer
- [x] Create AgentEscalator
- [ ] Integrate with polling service (triage step)
- [ ] Add escalation to code_agent
- [ ] Implement coordinator takeover handling
- [ ] Create `needs-coordination` label
- [ ] Write unit tests
- [ ] Write integration tests
- [ ] Update documentation
- [ ] Deploy and monitor

---

## Future Enhancements

### 1. LLM-Enhanced Triage
- Use LLM for semantic analysis
- Better understanding of issue context
- More accurate complexity prediction

### 2. Machine Learning
- Learn from past escalations
- Improve threshold tuning
- Predict escalation probability

### 3. Agent Collaboration
- Multiple agents on same issue (not just escalation)
- Real-time coordination
- Shared context

### 4. Escalation Analytics
- Track escalation frequency
- Measure accuracy of pre-flight triage
- Optimize thresholds based on data

---

## Monitoring & Metrics

### Key Metrics to Track

1. **Triage Accuracy**
   - How often does "simple" stay simple?
   - How often does "complex" actually need coordinator?
   - False positive/negative rates

2. **Escalation Rate**
   - % of issues escalated mid-flight
   - Time to escalation detection
   - Success rate after escalation

3. **Performance Impact**
   - Triage overhead (target: <10 sec)
   - Escalation overhead (target: <2 min)
   - Overall completion time improvement

4. **Coordinator Utilization**
   - % issues routed to coordinator
   - Average sub-issues per coordinated issue
   - Coordinator success rate

---

## Conclusion

This two-stage architecture solves the fundamental "looks simple but actually complex" problem by:

1. ✅ **Pre-flight triage** - Catch obvious complexity early
2. ✅ **Dynamic escalation** - Adapt when complexity emerges
3. ✅ **Objective criteria** - Scalable decision-making
4. ✅ **Coordinator integration** - Proper multi-agent orchestration

**Status**: Architecture complete, ready for integration into polling service and code agent.

**Next Steps**: 
1. Integrate triage into polling service
2. Add escalation to code_agent
3. Test with real issues
4. Monitor and tune thresholds
