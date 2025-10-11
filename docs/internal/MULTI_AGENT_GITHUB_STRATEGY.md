# Multi-Agent GitHub Strategy

> **📊 Visual Documentation**: See [Architecture Diagram](diagrams/architecture-overview.md) for agent communication patterns and [Data Flow](diagrams/data-flow.md#issue-processing-flow) for GitHub integration flow.

## Problem

Using a single GitHub account for multiple AI agents makes it impossible to:
- Track which agent made which changes
- Apply different permissions per agent
- Audit agent behavior independently
- Collaborate when multiple agents work simultaneously

## Solution: Machine User Accounts

### GitHub Machine Users (Official)
GitHub allows creating **machine user accounts** for automation:
- https://docs.github.com/en/developers/overview/managing-deploy-keys#machine-users

**Benefits:**
- ✅ Official GitHub support
- ✅ Each agent has separate identity
- ✅ Individual access tokens per agent
- ✅ Clear audit trail
- ✅ Can be added as collaborators with specific permissions

**Requirements:**
- Each machine user needs unique email address
- Free accounts work fine for public repos
- For private repos: counts toward organization seats

### Recommended Setup

#### Agent Accounts
```
m0nk111-qwen-agent       # Qwen2.5-Coder agent
m0nk111-copilot-agent    # GitHub Copilot (if needed)
m0nk111-deepseek-agent   # Future: DeepSeek agent
m0nk111-builder-bot      # CI/CD automation
```

#### Email Strategy
Use email aliases:
```
flip+qwen@yourdomain.com
flip+copilot@yourdomain.com
flip+deepseek@yourdomain.com
```

Or use temporary email services for machine accounts.

### Implementation Steps

#### 1. Create Machine User Account
```bash
# On GitHub.com:
1. Sign out
2. Create new account: m0nk111-qwen-agent
3. Use unique email: flip+qwen@domain.com
4. Verify email
```

#### 2. Generate Personal Access Token (PAT)
```bash
# Settings → Developer settings → Personal access tokens → Fine-grained tokens
# Permissions needed:
- Repository access: Read and Write for specific repos
- Commit statuses: Read and Write
- Pull requests: Read and Write
- Issues: Read and Write (optional)
```

#### 3. Add as Collaborator
```bash
# Repository → Settings → Collaborators
# Add: m0nk111-qwen-agent
# Role: Write (can push commits, create branches)
```

#### 4. Configure Agent
```python
# engine/runners/code_agent.py
class CodeAgent:
    def __init__(self, config_path: str):
        # Load GitHub token from environment
        self.github_token = os.getenv('CODEAGENT_GITHUB_TOKEN')
        self.github_username = 'm0nk111-qwen-agent'
    
    def commit_and_push(self, message: str):
        """Commit with agent identity"""
        subprocess.run([
            'git', 'config', 'user.name', self.github_username
        ])
        subprocess.run([
            'git', 'config', 'user.email', 'flip+qwen@domain.com'
        ])
        subprocess.run(['git', 'commit', '-m', message])
        # Use token for authentication
        subprocess.run([
            'git', 'push', 
            f'https://{self.github_token}@github.com/m0nk111/repo.git'
        ])
```

#### 5. Environment Configuration
```bash
# ~/.bashrc or per-project .env
export CODEAGENT_GITHUB_TOKEN="ghp_xxxxxxxxxxxxxxxxxxxx"
export CODEAGENT_GITHUB_USERNAME="m0nk111-qwen-agent"
export CODEAGENT_GITHUB_EMAIL="flip+qwen@domain.com"
```

### Commit Signatures

**Option 1: Agent signature in commit messages**
```
[QWEN] Implement LLM client with retry logic

- Added exponential backoff
- Implemented connection pooling
- Added health checks

Agent: Qwen2.5-Coder 7B
Phase: 2 (LLM Integration)
Task: 1/4
```

**Option 2: Git trailers**
```bash
git commit -m "Implement LLM client" -m "Agent: qwen2.5-coder" -m "Phase: 2"
```

**Option 3: Signed commits**
```bash
# Generate GPG key for agent
gpg --gen-key
git config user.signingkey <key-id>
git commit -S -m "message"
```

### Collaboration Workflow

When multiple agents work simultaneously:

```yaml
# .github/agent-assignments.yml
agents:
  - name: qwen-agent
    github_user: m0nk111-qwen-agent
    assigned_phases: [1, 2, 3, 4]
    branch_prefix: "qwen/"
  
  - name: deepseek-agent
    github_user: m0nk111-deepseek-agent
    assigned_phases: [5, 6, 7]
    branch_prefix: "deepseek/"
```

Each agent:
1. Creates branch with prefix: `qwen/phase-2-llm-integration`
2. Commits with agent identity
3. Opens PR with `[QWEN]` prefix
4. Another agent or human reviews

### Security Considerations

**Token Storage:**
```bash
# NEVER commit tokens to repos
# Use environment variables or secret managers

# Option 1: Environment file (gitignored)
echo "CODEAGENT_GITHUB_TOKEN=ghp_xxx" >> .env
echo ".env" >> .gitignore

# Option 2: System keyring
pip install keyring
python -c "import keyring; keyring.set_password('github', 'qwen-agent', 'ghp_xxx')"
```

**Token Permissions:**
- Use **fine-grained tokens** (not classic PAT)
- Limit to specific repositories
- Set expiration dates (90 days)
- Rotate tokens regularly

**Audit Trail:**
```bash
# Track agent activity
git log --author="m0nk111-qwen-agent" --oneline
git log --grep="\[QWEN\]" --oneline

# Review agent PRs
gh pr list --author m0nk111-qwen-agent
```

### Alternative: Bot Apps

For more advanced setups, create a **GitHub App**:
- https://docs.github.com/en/apps/creating-github-apps

**Benefits:**
- More granular permissions
- Webhook integrations
- Better rate limits
- Official "bot" badge on commits

**Setup:**
```bash
# Create GitHub App
1. Settings → Developer settings → GitHub Apps → New
2. Name: Qwen Agent Bot
3. Webhook: Optional
4. Permissions: Contents (R/W), Pull Requests (R/W)
5. Install on repositories
```

## Recommended Approach for agent-forge

**Short-term (Now):**
1. Create `m0nk111-qwen-agent` machine user
2. Add as collaborator to agent-forge and caramba
3. Generate fine-grained PAT
4. Update agent to use agent identity for commits

**Medium-term (After Phase 2-3):**
1. Add more machine users for different agents
2. Implement branch-based workflow per agent
3. Add agent signatures to commit messages

**Long-term (If scaling):**
1. Create GitHub App for agent-forge
2. Implement proper webhook integrations
3. Build agent coordination system

## Implementation Priority

**Priority 1 (Now):**
- [x] Document strategy (this file)
- [ ] Create m0nk111-qwen-agent account
- [ ] Generate PAT and add to environment
- [ ] Update code_agent.py to use agent identity

**Priority 2 (Phase 2):**
- [ ] Add git commit functionality to agent
- [ ] Implement commit message formatting
- [ ] Test agent commits with machine user

**Priority 3 (Phase 3+):**
- [ ] Add branch creation per phase
- [ ] Implement PR creation
- [ ] Add agent coordination

## References
- [GitHub Machine Users](https://docs.github.com/en/developers/overview/managing-deploy-keys#machine-users)
- [Fine-grained Personal Access Tokens](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token)
- [GitHub Apps](https://docs.github.com/en/apps/creating-github-apps/about-creating-github-apps/about-creating-github-apps)
