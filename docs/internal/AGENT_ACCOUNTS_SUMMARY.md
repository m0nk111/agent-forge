# Agent Accounts Summary - Agent Forge

## ✅ Active GitHub Accounts (6 total)

> **Note**: All account configurations are centralized in `config/system/github_accounts.yaml`  
> Use `AccountManager` from `engine.core.account_manager` for programmatic access.

### 1. m0nk111 (Admin)
- **Role**: Human admin, manual interventions
- **Email**: Personal account
- **Token**: Not automated (personal use)
- **Usage**: Manual approvals, emergency interventions

### 2. m0nk111-post (Bot Agent)
- **Role**: Bot operations, orchestration
- **Email**: aicodingtime+post@gmail.com
- **Token**: BOT_GITHUB_TOKEN
- **Location**: secrets/agents/m0nk111-post.token
- **Scopes**: repo, admin:org, workflow, write:discussion
- **Usage**: Issue monitoring, PR creation, notifications, repository creation
- **Can Review**: NO (dedicated bot, not coder)
- **Replaces**: m0nk111-bot (suspended)

### 3. m0nk111-coder1 (Primary GPT-5 Coder) ⭐
- **Role**: Code development (GPT-5 Chat Latest)
- **Email**: aicodingtime+coder1@gmail.com
- **Token**: CODER1_GITHUB_TOKEN
- **Location**: secrets/agents/m0nk111-coder1.token
- **Scopes**: repo, workflow, write:discussion, gist
- **LLM**: GPT-5 Chat Latest (gpt-5-chat-latest)
- **Usage**: Code generation, commits, PRs
- **Can Review**: YES (round-robin, peer review)
- **Status**: ✅ Active and verified
- **Priority**: PRIMARY

### 4. m0nk111-coder2 (Primary GPT-4o Coder) ⭐
- **Role**: Code development (GPT-4o)
- **Email**: aicodingtime+coder2@gmail.com
- **Token**: CODER2_GITHUB_TOKEN
- **Location**: secrets/agents/m0nk111-coder2.token
- **Scopes**: repo, workflow, write:discussion
- **LLM**: GPT-4o
- **Usage**: Code generation, commits, PRs
- **Can Review**: YES (round-robin)
- **Status**: ✅ Active and verified

---

## 📊 Account Distribution

- **LLM**: GPT-4o (gpt-4o)
- **Usage**: Code generation, commits, PRs
- **Can Review**: YES (round-robin, peer review)
- **Status**: ✅ Active and verified
- **Priority**: PRIMARY

### 5. m0nk111-reviewer (Dedicated Reviewer) ⭐
- **Role**: PR reviews and approvals
- **Email**: aicodingtime+reviewer@gmail.com
- **Token**: REVIEWER_GITHUB_TOKEN
- **Location**: secrets/agents/m0nk111-reviewer.token
- **Scopes**: repo, write:discussion, read:org
- **LLM**: GPT-5 Chat Latest (gpt-5-chat-latest)
- **Usage**: Review PRs from ALL coders, approve/reject
- **Can Review**: YES (dedicated reviewer, always available)
- **Status**: ✅ Active and verified

### 6. m0nk111-qwen-agent (Reserve Coder)
- **Role**: Code development (Qwen 2.5 Coder 32B - local)
- **Email**: aicodingtime+qwen@gmail.com
- **Token**: CODEAGENT_GITHUB_TOKEN
- **Location**: secrets/agents/m0nk111-qwen-agent.token
- **Scopes**: repo, workflow, write:discussion
- **LLM**: Qwen 2.5 Coder 32B (local model)
- **Usage**: Code generation, commits, PRs
- **Can Review**: YES (round-robin)
- **Status**: ✅ Active
- **Priority**: RESERVE/FALLBACK

---

## 📊 Account Statistics

### By Role
```
Bot:        1 account  (m0nk111-post)
Coders:     3 accounts (coder1, coder2, qwen-agent)
  Primary:  2 accounts (coder1, coder2)
  Reserve:  1 account  (qwen-agent)
Reviewer:   1 account  (reviewer)
Admin:      1 account  (m0nk111)
---
Total:      6 accounts
```

### By LLM
```
GPT-5:      2 accounts (reviewer, coder1)
GPT-4o:     1 account  (coder2)
Qwen 2.5:   1 account  (qwen-agent)
Human:      1 account  (m0nk111)
Local Bot:  1 account  (post - uses Qwen for orchestration)
```

### By Priority
```
PRIMARY:    3 accounts (coder1, coder2, reviewer)
RESERVE:    1 account  (qwen-agent)
BOT:        1 account  (post)
ADMIN:      1 account  (m0nk111)
```

---

## 🔄 Workflow Example

### Scenario: Issue #100 needs implementation

**Step 1: Issue Detection**
- `m0nk111-post` detects issue with "auto-resolve" label

**Step 2: Assignment**
- Coordinator assigns to available primary coder (coder1 or coder2)
- Options: coder1 (GPT-5), coder2 (GPT-4o), qwen-agent (Qwen)

**Step 3: Implementation**
- Selected coder (e.g., `m0nk111-coder1`) generates code
- Creates branch: `issue-100-implement-feature`
- Commits changes with GPT-5

**Step 4: PR Creation**
- Coder creates PR with implementation
- PR author: `m0nk111-coder1`

**Step 5: Review Assignment (Round-Robin)**
- System checks available reviewers:
  - ✅ m0nk111-reviewer (not author, can review)
  - ✅ m0nk111-coder2 (not author, can review)
  - ✅ m0nk111-qwen-agent (not author, can review)
  - ❌ m0nk111-coder1 (is author, cannot review own PR)

- Round-robin selects: `m0nk111-reviewer`

**Step 6: Code Review**
- `m0nk111-reviewer` reviews PR with GPT-5
- Security audit: 100%
- Code quality: 95%
- Decision: APPROVE ✅

**Step 7: Merge**
- Admin or automated system merges PR
- Issue #100 automatically closed

---

## 🎯 Review Strategy

**Current Strategy:** round-robin

### How It Works
1. When PR is created, get PR author
2. Filter out author from reviewer list
3. Select next reviewer in rotation
4. Assign review to selected agent
5. Rotate index for next PR

### Available Reviewers
```yaml
- m0nk111-reviewer (GPT-5)    # Dedicated, always available, highest priority
- m0nk111-coder1 (GPT-5)      # Primary coder, can review if not author
- m0nk111-coder2 (GPT-4o)     # Primary coder, can review if not author
- m0nk111-qwen-agent (Qwen)   # Reserve coder, can review if not author
```

### Reviewer Priority
1. **m0nk111-reviewer** - Dedicated reviewer (no conflicts)
2. **m0nk111-coder1** - Primary GPT-5 coder (peer review)
3. **m0nk111-coder2** - Primary GPT-4o coder (peer review)
4. **m0nk111-qwen-agent** - Reserve coder (fallback reviewer)

### Review Distribution
With 4 reviewers and round-robin:
- Each gets ~25% of reviews
- Self-review automatically prevented
- Multiple perspectives on code
- Can compare review quality by LLM model

---

## 🔐 Token Security

### Centralized Configuration
All account details managed in `config/system/github_accounts.yaml`:
- Single source of truth for all accounts
- Email addresses: `aicodingtime+<suffix>@gmail.com`
- Token locations and environment variable names
- Account roles, capabilities, and groups

### Programmatic Access
```python
from engine.core.account_manager import get_account, get_bot_account

# Get specific account
account = get_account('m0nk111-coder1')
print(account.email)    # aicodingtime+coder1@gmail.com
print(account.token)    # Automatically loaded from file/env

# Get default bot
bot = get_bot_account()
```

### Token Storage
All tokens stored in `secrets/agents/` with permissions `600`:
```
secrets/agents/
├── m0nk111-post.token         (600) ✅ Bot orchestrator
├── m0nk111-reviewer.token     (600) ✅ Dedicated reviewer
├── m0nk111-coder1.token       (600) ✅ Primary GPT-5
├── m0nk111-coder2.token       (600) ✅ Primary GPT-4o
└── m0nk111-qwen-agent.token   (600) ✅ Reserve coder
```

### Token Scopes Summary
```
Reviewer:  repo + write:discussion + read:org
Coder1:    repo + workflow + write:discussion + gist
Coder2:    repo + workflow + write:discussion
Qwen:      repo + workflow + write:discussion
Bot:       repo + admin:org + workflow + write:discussion
```

---

## 🚀 Benefits of Current Setup

### 1. Centralized Account Management
- ✅ Single YAML file for all account details
- ✅ No hardcoded usernames/emails in code
- ✅ Easy to add new accounts
- ✅ Type-safe access via AccountManager

### 2. Dedicated Reviewer
- ✅ Can approve PRs from ALL coders
- ✅ No "cannot approve own PR" errors
- ✅ Consistent review quality (GPT-5)

### 3. Multiple Primary Coders
- ✅ Parallel development possible
- ✅ Can compare LLM performance (GPT-5 vs GPT-4o vs Qwen)
- ✅ Load balancing across agents

### 3. Clean Separation
- ✅ Bot = orchestration only
- ✅ Coders = code only
- ✅ Reviewer = reviews only
- ✅ No mixed responsibilities

### 4. Peer Review
- ✅ Coders can review each other
- ✅ Multiple perspectives
- ✅ Quality assurance

### 5. Scalability
- ✅ Easy to add more coders
- ✅ Easy to add more reviewers
- ✅ Round-robin auto-balances load

---

## 📈 Next Steps

### Immediate (Ready Now)
- ✅ All tokens configured and verified
- ✅ All accounts active
- ✅ Polling service ready
- ✅ Ready for production use

### Testing
1. Create test issue with "auto-resolve" label
2. Watch coder pick it up and implement
3. Watch reviewer automatically review
4. Verify approval works
5. Merge and close

### Future Enhancements
1. Add more coder accounts for parallel work
2. Add specialized agents (docs, tests)
3. Implement "all" review strategy (multiple reviews per PR)
4. Add metrics dashboard (which LLM codes/reviews best)

---

## 🎉 Summary

**You now have a COMPLETE multi-agent system with:**
- ✅ 3 independent coders (GPT-5, GPT-4o, Qwen)
- ✅ 1 dedicated reviewer (GPT-5)
- ✅ 1 orchestration bot
- ✅ All tokens configured and verified
- ✅ Round-robin review distribution
- ✅ Self-review prevention
- ✅ Ready for full automation

**Status: PRODUCTION READY** 🚀

Time to test the complete flow! 🎊
