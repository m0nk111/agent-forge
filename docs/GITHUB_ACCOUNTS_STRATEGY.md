# GitHub Accounts Strategy - Agent Forge

## Current Situation Analysis

### Existing Accounts
1. **m0nk111** (admin) - ✅ Working
   - Personal account, manual interventions
   - Should NOT be used for automation (email spam)

2. **m0nk111-post** (bot agent) - ✅ Working
   - Token: BOT_GITHUB_TOKEN
   - Current use: Issue detection, PR creation, comments
   - Problem: Used for BOTH bot operations AND code reviews
   - Issue: Mixing responsibilities = confusion

3. **m0nk111-qwen-agent** (code agent) - ✅ Working
   - Token: CODEAGENT_GITHUB_TOKEN
   - Current use: Git commits, code changes
   - Can also review (but shouldn't review own code)

4. **m0nk111-bot** - ❌ SUSPENDED (ignore)

## Agent Roles & Required Accounts

### Core Functional Roles

#### 1. **Coordinator Role** 
- **Function**: Task planning, orchestration, breakdown
- **GitHub Needed**: NO (local only, no commits)
- **Account**: None needed
- **Why**: Coordinators don't commit, they just plan

#### 2. **Developer/Code Agent Role**
- **Function**: Write code, implement features, fix bugs
- **GitHub Needed**: YES (commits, pushes, branches)
- **Account**: ✅ m0nk111-qwen-agent (existing)
- **Token**: CODEAGENT_GITHUB_TOKEN

#### 3. **Reviewer Role**
- **Function**: Review PRs, approve/request changes
- **GitHub Needed**: YES (PR reviews, comments)
- **Account**: ❌ MISSING - Need dedicated account
- **Recommended**: **m0nk111-reviewer**
- **Token**: REVIEWER_GITHUB_TOKEN
- **Why**: Cannot approve own PRs, needs separate identity

#### 4. **Bot/Automation Role**
- **Function**: Issue monitoring, PR creation, status updates
- **GitHub Needed**: YES (API calls, issue comments)
- **Account**: ✅ m0nk111-post (existing)
- **Token**: BOT_GITHUB_TOKEN
- **Clarification**: Should NOT be used for reviews

#### 5. **Tester Role**
- **Function**: Run tests, validate code
- **GitHub Needed**: NO (local only, posts results via bot)
- **Account**: None needed (can use bot account for posting)

#### 6. **Documenter Role**
- **Function**: Write documentation, update READMEs
- **GitHub Needed**: Optional (can commit via code agent)
- **Account**: Can reuse m0nk111-qwen-agent OR m0nk111-post
- **Decision**: Use code agent if docs with code, bot if standalone

#### 7. **Researcher Role**
- **Function**: Information gathering, analysis
- **GitHub Needed**: NO (local only)
- **Account**: None needed

#### 8. **Issue Opener Agent**
- **Function**: Autonomous issue resolution (create code + PR)
- **GitHub Needed**: YES (commits, PR creation)
- **Account**: Can reuse m0nk111-qwen-agent OR create dedicated
- **Current**: Uses m0nk111-post (suboptimal)
- **Recommendation**: Use m0nk111-qwen-agent or create m0nk111-coder

#### 9. **Bootstrap Agent**
- **Function**: Create repositories, setup projects
- **GitHub Needed**: YES (repo creation, team management)
- **Account**: Needs admin-level token
- **Current**: Uses m0nk111-post token
- **OK**: Can stay with post account (admin operations)

## Recommended Account Structure

### Minimum Viable Setup (2-3 accounts)

```
✅ m0nk111-post (BOT_GITHUB_TOKEN)
   └─ Bot operations, monitoring, PR creation, repo management
   
✅ m0nk111-qwen-agent (CODEAGENT_GITHUB_TOKEN)
   └─ Code development, commits, Issue Opener coding
   
❌ m0nk111-reviewer (REVIEWER_GITHUB_TOKEN) - CREATE THIS
   └─ PR reviews, approvals (can review m0nk111-qwen-agent PRs)
```

### Optimal Setup (3-4 accounts)

```
✅ m0nk111-post (BOT_GITHUB_TOKEN)
   └─ Bot operations ONLY: monitoring, status updates, notifications
   
✅ m0nk111-qwen-agent (CODEAGENT_GITHUB_TOKEN)
   └─ Code development: commits, pushes, Issue Opener
   
❌ m0nk111-reviewer (REVIEWER_GITHUB_TOKEN) - CREATE THIS
   └─ PR reviews: code review, approval/rejection
   
Optional:
❌ m0nk111-gpt5-coder (GPT5_GITHUB_TOKEN) - CREATE IF NEEDED
   └─ Alternative coder (GPT-5 vs Qwen separation)
```

### Future-Proof Setup (4-5 accounts)

```
✅ m0nk111-post (BOT_GITHUB_TOKEN)
   └─ Bot operations: monitoring, orchestration
   
✅ m0nk111-qwen-agent (QWEN_GITHUB_TOKEN)
   └─ Qwen-based coding agent
   
❌ m0nk111-gpt5-coder (GPT5_GITHUB_TOKEN)
   └─ GPT-5 based coding agent (different LLM)
   
❌ m0nk111-reviewer (REVIEWER_GITHUB_TOKEN)
   └─ Dedicated PR reviewer
   
Optional:
❌ m0nk111-docs (DOCS_GITHUB_TOKEN)
   └─ Documentation-only commits (keeps history clean)
```

## Required Actions

### Priority 1 - CRITICAL (Do This Now)
**Create m0nk111-reviewer account**
- Needed for: PR approval automation
- Without: Bots cannot approve their own PRs
- Setup time: 5 minutes

Steps:
1. Go to https://github.com/signup
2. Username: m0nk111-reviewer
3. Email: m0nk111-reviewer@users.noreply.github.com
4. Create token at https://github.com/settings/tokens
5. Scopes: repo, workflow, write:discussion, read:org
6. Add to keys.json as REVIEWER_GITHUB_TOKEN
7. Update polling.yaml reviewer_agents list

### Priority 2 - RECOMMENDED (Nice to Have)
**Separate Issue Opener from bot account**
- Currently: m0nk111-post does both bot work AND coding (Issue Opener)
- Better: m0nk111-qwen-agent handles all coding (including Issue Opener)
- Benefit: Clearer separation of concerns

Update issue-opener-agent.yaml:
```yaml
github:
  username: "m0nk111-qwen-agent"  # Change from m0nk111-post
  token_env: "CODEAGENT_GITHUB_TOKEN"  # Change from BOT_GITHUB_TOKEN
```

### Priority 3 - FUTURE (If Scaling)
**Create dedicated coder accounts per LLM**
- m0nk111-qwen-agent (Qwen 2.5 Coder)
- m0nk111-gpt5-coder (GPT-5 Chat)
- m0nk111-claude-coder (Claude 3.5 Sonnet)
- Benefit: Can compare which LLM writes better code
- Benefit: Multiple coders can work in parallel

## Token Management

### Current Tokens in keys.json
```json
{
  "OPENAI_API_KEY": "...",
  "BOT_GITHUB_TOKEN": "ghp_..."
}
```

### After Creating Reviewer Account
```json
{
  "OPENAI_API_KEY": "...",
  "BOT_GITHUB_TOKEN": "ghp_...",
  "REVIEWER_GITHUB_TOKEN": "ghp_..."
}
```

### Future Token Structure
```json
{
  "OPENAI_API_KEY": "...",
  "BOT_GITHUB_TOKEN": "ghp_...",
  "CODEAGENT_GITHUB_TOKEN": "ghp_...",  # If separated from BOT
  "REVIEWER_GITHUB_TOKEN": "ghp_...",
  "GPT5_CODER_GITHUB_TOKEN": "ghp_..."  # If adding GPT-5 coder
}
```

## Configuration Updates Needed

### 1. polling.yaml - After Creating Reviewer
```yaml
reviewer_agents:
  - agent_id: "code-agent-qwen"
    username: "m0nk111-qwen-agent"
    llm_model: "qwen-2.5-coder-32b"
  - agent_id: "reviewer-agent"
    username: "m0nk111-reviewer"  # NEW ACCOUNT
    llm_model: "gpt-5-chat-latest"
```

### 2. reviewer-agent.yaml
```yaml
github:
  username: "m0nk111-reviewer"  # Change from qwen-agent
  token_env: "REVIEWER_GITHUB_TOKEN"  # NEW TOKEN
```

### 3. issue-opener-agent.yaml (recommended)
```yaml
github:
  username: "m0nk111-qwen-agent"  # Change from m0nk111-post
  token_env: "CODEAGENT_GITHUB_TOKEN"  # Change from BOT_GITHUB_TOKEN
```

## Summary

**What You NEED:**
1. ✅ m0nk111-post (have) - Bot operations
2. ✅ m0nk111-qwen-agent (have) - Code development
3. ❌ m0nk111-reviewer (create) - PR reviews

**What You DON'T NEED:**
- ❌ Coordinator account (local only)
- ❌ Tester account (local only)
- ❌ Researcher account (local only)
- ❌ Documenter account (can reuse coder)

**Minimum to be fully functional:**
- Create 1 account: m0nk111-reviewer
- Add 1 token: REVIEWER_GITHUB_TOKEN
- Update 2 config files: polling.yaml, reviewer-agent.yaml
- Time: 10 minutes total

**Current blocker:**
- m0nk111-post is doing TOO MUCH (bot + reviews)
- m0nk111-qwen-agent could handle Issue Opener better
- Missing dedicated reviewer = can't approve own PRs

**After reviewer account:**
- ✅ Full automation possible
- ✅ Clean separation of concerns
- ✅ Bots can review each other's work
- ✅ No more email spam to admin

Ready to proceed? 🚀
