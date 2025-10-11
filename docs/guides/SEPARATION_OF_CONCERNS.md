# Separation of Concerns Architecture

**Pattern**: Decision/Execution Separation  
**Updated**: October 11, 2025  
**Architecture**: Coordinator = Intelligence, Polling = Execution

---

## Architecture Philosophy

### Clean Separation

```
┌─────────────────────────────────────┐
│   COORDINATOR (Intelligence Layer)  │
│   - Analyzes complexity             │
│   - Makes decisions                 │
│   - Posts reasoning                 │
│   - Tags issues                     │
│   - Does NOT execute                │
└─────────────────────────────────────┘
              ↓ Decision
┌─────────────────────────────────────┐
│   POLLING (Execution Layer)         │
│   - Executes decisions              │
│   - Starts agents                   │
│   - Manages execution               │
│   - Does NOT decide                 │
└─────────────────────────────────────┘
```

### Why This Pattern?

**Separation of concerns:**
- ✅ Coordinator = Pure intelligence (no execution code)
- ✅ Polling = Pure execution (no decision logic)
- ✅ Clear boundaries
- ✅ Testable in isolation
- ✅ Replaceable components

---

## Complete Workflow

### Step 1: Polling Detects Issue

```python
class PollingService:
    def process_actionable_issues(self, issues):
        for issue in issues:
            # ALL issues with 'agent-ready' → coordinator
            decision = self.coordinator_gateway.process_issue(
                owner=self.owner,
                repo=self.repo,
                issue_number=issue['number'],
                issue_data=issue
            )
            
            # Execute decision
            self.execute_coordinator_decision(issue, decision)
```

### Step 2: Coordinator Analyzes & Decides

```python
class CoordinatorGateway:
    def process_issue(self, owner, repo, issue_number, issue_data):
        # INTELLIGENCE WORK ONLY
        
        # 1. Analyze with LLM + metrics
        analysis = self.coordinator.analyze_issue_complexity(
            title=issue_data['title'],
            body=issue_data['body'],
            labels=issue_labels
        )
        
        # 2. Make routing decision
        decision = self._make_routing_decision(analysis, issue_data)
        
        # 3. Post decision comment (explain to humans)
        self._post_decision_comment(owner, repo, issue_number, decision, analysis)
        
        # 4. Tag issue with decision (for tracking)
        self._tag_issue_with_decision(owner, repo, issue_number, decision)
        
        # 5. Return decision for polling to execute
        return {
            'status': 'decision_made',
            'decision': 'SIMPLE' | 'UNCERTAIN' | 'COMPLEX',
            'action': 'start_code_agent' | 'start_coordinator_orchestration',
            'escalation_enabled': True/False,
            'instructions': {
                'agent_type': 'code_agent',
                'enable_escalation': True/False,
                'priority': 'normal' | 'high'
            }
        }
```

### Step 3: Polling Executes Decision

```python
class PollingService:
    def execute_coordinator_decision(self, issue, decision):
        # EXECUTION WORK ONLY
        
        if decision['action'] == 'start_code_agent':
            # Execute: Start code agent
            escalation = decision['escalation_enabled']
            self.start_code_agent(
                issue=issue,
                enable_escalation=escalation
            )
        
        elif decision['action'] == 'start_coordinator_orchestration':
            # Execute: Trigger orchestration
            self.start_coordinator_orchestration(issue)
```

---

## Decision Types

### 1. SIMPLE Decision

**Coordinator Intelligence:**
```python
{
    'status': 'decision_made',
    'decision': 'SIMPLE',
    'action': 'start_code_agent',
    'escalation_enabled': False,
    'reasoning': 'Issue is straightforward - single agent can handle',
    'analysis': {
        'complexity': 'simple',
        'score': 5,
        'confidence': 0.90
    },
    'instructions': {
        'agent_type': 'code_agent',
        'enable_escalation': False,
        'priority': 'normal'
    }
}
```

**Polling Execution:**
```python
def execute_simple_decision(self, issue, decision):
    # Start code agent without escalation
    agent = self.get_code_agent()
    agent.execute_issue(
        issue=issue,
        escalation_enabled=False
    )
```

**GitHub Tags Added:**
- `coordinator-approved-simple`

**Comment Posted:**
```markdown
🎯 **Coordinator Decision: Simple Issue - Approved for Code Agent**

Analysis:
- Complexity: SIMPLE
- Score: 5 points (threshold: 10)
- Confidence: 90%

Decision:
✅ Issue approved for direct code agent execution
- No orchestration needed
- Escalation NOT enabled

Next Steps:
Polling service will start code agent.
```

### 2. UNCERTAIN Decision

**Coordinator Intelligence:**
```python
{
    'status': 'decision_made',
    'decision': 'UNCERTAIN',
    'action': 'start_code_agent',
    'escalation_enabled': True,  # ← KEY DIFFERENCE
    'reasoning': 'Complexity unclear - start with agent but enable escalation',
    'analysis': {
        'complexity': 'uncertain',
        'score': 18,
        'confidence': 0.60
    },
    'instructions': {
        'agent_type': 'code_agent',
        'enable_escalation': True,  # ← MONITOR MODE
        'priority': 'high'
    }
}
```

**Polling Execution:**
```python
def execute_uncertain_decision(self, issue, decision):
    # Start code agent WITH escalation capability
    agent = self.get_code_agent()
    agent.execute_issue(
        issue=issue,
        escalation_enabled=True  # ← Can escalate back to coordinator
    )
```

**GitHub Tags Added:**
- `coordinator-approved-uncertain`

**Comment Posted:**
```markdown
🎯 **Coordinator Decision: Uncertain Complexity - Monitored Execution**

Analysis:
- Complexity: UNCERTAIN
- Score: 18 points (threshold: 11-25)
- Confidence: 60%

Decision:
⚠️ Starting with code agent but ESCALATION ENABLED
- If complexity increases, agent can escalate back
- Coordinator ready to take over

Next Steps:
Polling service will start code agent with escalation.
```

### 3. COMPLEX Decision

**Coordinator Intelligence:**
```python
{
    'status': 'decision_made',
    'decision': 'COMPLEX',
    'action': 'start_coordinator_orchestration',  # ← Different action
    'reasoning': 'Issue is complex - requires coordinator orchestration',
    'analysis': {
        'complexity': 'complex',
        'score': 34,
        'confidence': 0.90
    },
    'instructions': {
        'create_sub_issues': True,
        'build_execution_plan': True,
        'assign_multiple_agents': True,
        'priority': 'high'
    }
}
```

**Polling Execution:**
```python
def execute_complex_decision(self, issue, decision):
    # Trigger coordinator orchestration
    plan = self.coordinator.create_execution_plan(issue)
    sub_issues = self.coordinator.create_sub_issues(plan)
    
    # Coordinator handles everything
    self.coordinator.orchestrate(plan)
```

**GitHub Tags Added:**
- `coordinator-approved-complex`

**Comment Posted:**
```markdown
🎯 **Coordinator Decision: Complex Issue - Orchestration Required**

Analysis:
- Complexity: COMPLEX
- Score: 34 points (threshold: >25)
- Confidence: 90%

Detected Signals:
- Files mentioned: 8
- Architecture changes detected
- Refactoring required

Decision:
🎼 Coordinator will orchestrate multi-agent workflow
1. Break down into sub-issues
2. Create execution plan
3. Assign specialized agents

Next Steps:
Polling service will trigger coordinator orchestration.
```

---

## Benefits of Separation

### 1. Testability ✅

**Mock coordinator decisions:**
```python
def test_polling_executes_simple_decision():
    # Mock coordinator decision
    mock_decision = {
        'decision': 'SIMPLE',
        'action': 'start_code_agent',
        'escalation_enabled': False
    }
    
    # Test polling execution
    polling.execute_coordinator_decision(issue, mock_decision)
    
    # Verify code_agent started without escalation
    assert code_agent.started
    assert not code_agent.escalation_enabled
```

**Mock polling execution:**
```python
def test_coordinator_makes_simple_decision():
    # Test coordinator intelligence
    decision = coordinator.process_issue(issue_data)
    
    # Verify decision logic (no execution)
    assert decision['decision'] == 'SIMPLE'
    assert not decision['escalation_enabled']
```

### 2. Replaceability ✅

**Swap coordinators:**
```python
# Original: Qwen-based coordinator
coordinator = CoordinatorAgent(llm='qwen2.5:72b')

# Swap: GPT-4 coordinator
coordinator = CoordinatorAgent(llm='gpt-4')

# Swap: Claude coordinator
coordinator = CoordinatorAgent(llm='claude-3')

# Polling doesn't care - just executes decisions
```

**Swap polling execution:**
```python
# Original: Direct execution
polling.execute_decision(decision)

# Swap: Queue-based execution
queue.enqueue(decision)

# Swap: Distributed execution
distribute_to_workers(decision)

# Coordinator doesn't care - just makes decisions
```

### 3. Clear Responsibilities ✅

**Coordinator:**
- ❌ Cannot start agents
- ❌ Cannot execute code
- ❌ Cannot manage processes
- ✅ Can analyze
- ✅ Can decide
- ✅ Can tag/comment

**Polling:**
- ❌ Cannot analyze complexity
- ❌ Cannot make routing decisions
- ❌ Cannot use LLM
- ✅ Can start agents
- ✅ Can execute workflows
- ✅ Can manage processes

### 4. Debugging ✅

**Coordinator logs:**
```
🎯 COORDINATOR: Analyzing issue #94
📊 Analysis: SIMPLE (score: 5, confidence: 90%)
🎯 Decision: start_code_agent (escalation: False)
✅ Posted decision comment
✅ Tagged with: coordinator-approved-simple
```

**Polling logs:**
```
🔄 POLLING: Received decision for issue #94
📋 Decision: SIMPLE (escalation: False)
👨‍💻 Starting code_agent
✅ Code agent started: agent-001
```

**Clear separation** - easy to see where issues occur!

---

## Labels Used

### Decision Labels (Added by Coordinator)

- `coordinator-approved-simple`: Direct code agent execution
- `coordinator-approved-uncertain`: Code agent with escalation
- `coordinator-approved-complex`: Coordinator orchestration

### Status Labels (Added by Polling)

- `agent-executing`: Code agent working
- `coordinator-orchestrating`: Multi-agent coordination
- `escalated-to-coordinator`: Agent escalated mid-flight

---

## Example Flow

### Complete Lifecycle of Simple Issue

```
1. Issue #94 created with label "agent-ready"
2. Polling detects: "Found 1 actionable issue"
3. Polling calls: coordinator_gateway.process_issue(94)

4. COORDINATOR INTELLIGENCE:
   - LLM analysis: "Typo fix in README"
   - Metrics: 1 file, simple keywords
   - Score: 3 points
   - Decision: SIMPLE
   - Tags issue: coordinator-approved-simple
   - Posts comment explaining decision
   - Returns: {decision: 'SIMPLE', action: 'start_code_agent'}

5. POLLING EXECUTION:
   - Receives decision
   - Logs: "Decision: SIMPLE (escalation: False)"
   - Starts code_agent without escalation
   - Tags issue: agent-executing
   - Monitors execution

6. Code agent completes
7. PR created
8. Issue closed
```

---

## Migration Guide

### Old Architecture (Direct Delegation)

```python
# Coordinator started agents directly
coordinator.process_issue(issue)
    → coordinator._delegate_to_code_agent()
        → code_agent.execute()
```

### New Architecture (Decision/Execution Separation)

```python
# Coordinator makes decision
decision = coordinator.process_issue(issue)

# Polling executes decision
polling.execute_coordinator_decision(issue, decision)
    → polling.start_code_agent()
        → code_agent.execute()
```

### Changes Required

**Polling Service:**
```python
# ADD: Execute coordinator decisions
def execute_coordinator_decision(self, issue, decision):
    if decision['action'] == 'start_code_agent':
        self.start_code_agent(issue, decision['escalation_enabled'])
    elif decision['action'] == 'start_coordinator_orchestration':
        self.start_coordinator_orchestration(issue)
```

**Coordinator Gateway:**
```python
# CHANGE: Return decision instead of executing
def process_issue(self, ...):
    analysis = self.analyze()
    decision = self.decide(analysis)
    
    # Tag and comment
    self._tag_issue_with_decision(decision)
    self._post_decision_comment(decision)
    
    # Return for polling to execute
    return decision  # ← Not executing!
```

---

## Conclusion

**Clean architecture through separation of concerns:**

- 🧠 **Coordinator** = Intelligence (analyze, decide, explain)
- ⚙️ **Polling** = Execution (start, manage, monitor)
- 🏷️ **Labels** = Communication (coordinator → polling)
- 💬 **Comments** = Transparency (explain to humans)

**Benefits:**
- Testable components
- Replaceable layers
- Clear responsibilities
- Easy debugging
- Maintainable code
