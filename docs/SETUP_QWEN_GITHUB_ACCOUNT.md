# Setup Guide: Qwen Agent GitHub Account

## Prerequisites

- Gmail account (recommended): `flip@gmail.com`
- Or any email provider that supports `+` addressing
- Access to GitHub.com

## Step 1: Create Machine User Account

### 1.1 Sign out of current GitHub account

```bash
# Open browser in incognito/private mode
# Or sign out: https://github.com/logout
```

### 1.2 Create new account

Go to: https://github.com/signup

```
Username:   m0nk111-qwen-agent
Email:      flip+qwen@gmail.com
Password:   <secure password - save in password manager>
```

**Important:**
- Username format: `<your-username>-<agent-name>-agent`
- Use `+` addressing so emails arrive in your main inbox
- Use strong, unique password (generate with password manager)

### 1.3 Verify email

1. GitHub sends verification email to `flip+qwen@gmail.com`
2. Email arrives in your main inbox: `flip@gmail.com`
3. Click verification link
4. ✅ Account is verified

### 1.4 Complete profile (optional but recommended)

```
Name:        Qwen Agent Bot
Bio:         Autonomous coding agent powered by Qwen2.5-Coder 7B
             Managed by @m0nk111
Location:    localhost:11434
Website:     https://github.com/m0nk111/agent-forge
```

## Step 2: Generate Fine-Grained Personal Access Token

### 2.1 Navigate to token settings

1. Sign in as `m0nk111-qwen-agent`
2. Go to: Settings → Developer settings → Personal access tokens → Fine-grained tokens
3. Click: "Generate new token"

### 2.2 Configure token

```
Token name:     agent-forge-qwen-token
Description:    Token for Qwen agent to commit/push to agent-forge and caramba repos
Expiration:     90 days (set calendar reminder to rotate)
```

### 2.3 Repository access

**Option A: Select repositories**
- ✅ m0nk111/agent-forge
- ✅ m0nk111/caramba
- ✅ m0nk111/HiDream-I1 (if needed)

**Option B: All repositories** (less secure, not recommended)

### 2.4 Permissions

Required permissions:

```
Repository permissions:
├── Contents:              Read and write
├── Commit statuses:       Read and write
├── Pull requests:         Read and write
├── Issues:                Read and write (optional)
└── Metadata:              Read-only (automatic)
```

### 2.5 Generate and save token

1. Click "Generate token"
2. **COPY TOKEN IMMEDIATELY** (shown only once!)
3. Save in secure location:

```bash
# Option 1: Password manager (recommended)
# Save as: "GitHub PAT - m0nk111-qwen-agent"

# Option 2: System keyring (Linux)
secret-tool store --label='GitHub Qwen Agent Token' \
  service github \
  username m0nk111-qwen-agent

# Option 3: Environment file (NEVER COMMIT!)
echo "QWEN_GITHUB_TOKEN=github_pat_xxxxxxxxxxxxx" >> ~/.agent-forge.env
chmod 600 ~/.agent-forge.env
```

Token format: `github_pat_11XXXXXXXXXXXXXXXXX_YYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYY`

## Step 3: Add as Collaborator to Repositories

### 3.1 Add to agent-forge

**As your main account (m0nk111):**

1. Go to: https://github.com/m0nk111/agent-forge/settings/access
2. Click: "Add people"
3. Search: `m0nk111-qwen-agent`
4. Role: **Write** (can push to branches, create PRs)
5. Click: "Add m0nk111-qwen-agent to this repository"

### 3.2 Accept invitation

**As machine user (m0nk111-qwen-agent):**

1. Check email: `flip+qwen@gmail.com` (arrives in flip@gmail.com)
2. Click invitation link
3. Click: "Accept invitation"
4. ✅ Now collaborator on agent-forge

### 3.3 Repeat for caramba repository

```
Repository: https://github.com/m0nk111/caramba/settings/access
Add:        m0nk111-qwen-agent
Role:       Write
```

## Step 4: Configure Local Git with Agent Identity

### 4.1 Create environment file

```bash
# Create agent environment file
cat > ~/.agent-forge.env << 'EOF'
# Qwen Agent GitHub Credentials
export QWEN_GITHUB_TOKEN="github_pat_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
export QWEN_GITHUB_USERNAME="m0nk111-qwen-agent"
export QWEN_GITHUB_EMAIL="flip+qwen@gmail.com"
EOF

# Secure the file
chmod 600 ~/.agent-forge.env

# Load in shell (add to ~/.bashrc for persistence)
echo "source ~/.agent-forge.env" >> ~/.bashrc
source ~/.agent-forge.env
```

### 4.2 Test git credentials

```bash
# Test git config
git config user.name "$QWEN_GITHUB_USERNAME"
git config user.email "$QWEN_GITHUB_EMAIL"

# Test authentication (don't commit yet!)
cd /home/flip/agent-forge
git config user.name "m0nk111-qwen-agent"
git config user.email "flip+qwen@gmail.com"

# Test token (this should work without password prompt)
git ls-remote https://${QWEN_GITHUB_TOKEN}@github.com/m0nk111/agent-forge.git
```

Expected output:
```
From https://github.com/m0nk111/agent-forge
xxxxxxxxx	HEAD
xxxxxxxxx	refs/heads/main
```

## Step 5: Update Agent Code to Use Identity

### 5.1 Add Git functionality to agent

Create new module: `agents/git_operations.py`

```python
import os
import subprocess
from typing import Optional

class GitOperations:
    """Handle Git operations with agent identity"""
    
    def __init__(self):
        self.username = os.getenv('QWEN_GITHUB_USERNAME', 'm0nk111-qwen-agent')
        self.email = os.getenv('QWEN_GITHUB_EMAIL', 'flip+qwen@gmail.com')
        self.token = os.getenv('QWEN_GITHUB_TOKEN')
        
        if not self.token:
            raise ValueError("QWEN_GITHUB_TOKEN not set in environment")
    
    def configure_identity(self, repo_path: str):
        """Configure git identity for repository"""
        subprocess.run(['git', 'config', 'user.name', self.username], cwd=repo_path)
        subprocess.run(['git', 'config', 'user.email', self.email], cwd=repo_path)
    
    def commit(self, repo_path: str, message: str, phase: Optional[int] = None) -> bool:
        """Commit changes with agent signature"""
        # Add agent signature to commit message
        signature = f"\n\nAgent: Qwen2.5-Coder 7B"
        if phase:
            signature += f"\nPhase: {phase}"
        
        full_message = message + signature
        
        try:
            # Configure identity
            self.configure_identity(repo_path)
            
            # Stage all changes
            subprocess.run(['git', 'add', '-A'], cwd=repo_path, check=True)
            
            # Commit
            result = subprocess.run(
                ['git', 'commit', '-m', full_message],
                cwd=repo_path,
                check=True,
                capture_output=True,
                text=True
            )
            
            print(f"✅ Committed: {message}")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Commit failed: {e.stderr}")
            return False
    
    def push(self, repo_path: str, branch: str = 'main') -> bool:
        """Push changes to remote"""
        try:
            # Get remote URL
            result = subprocess.run(
                ['git', 'remote', 'get-url', 'origin'],
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            remote_url = result.stdout.strip()
            
            # Replace URL with authenticated version
            if remote_url.startswith('https://github.com/'):
                auth_url = remote_url.replace(
                    'https://github.com/',
                    f'https://{self.token}@github.com/'
                )
            else:
                print(f"⚠️  Non-HTTPS remote: {remote_url}")
                auth_url = remote_url
            
            # Push
            subprocess.run(
                ['git', 'push', auth_url, branch],
                cwd=repo_path,
                check=True,
                capture_output=True,
                text=True
            )
            
            print(f"✅ Pushed to {branch}")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Push failed: {e.stderr}")
            return False
    
    def create_branch(self, repo_path: str, branch_name: str) -> bool:
        """Create and checkout new branch"""
        try:
            subprocess.run(
                ['git', 'checkout', '-b', branch_name],
                cwd=repo_path,
                check=True
            )
            print(f"✅ Created branch: {branch_name}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Branch creation failed: {e}")
            return False
```

### 5.2 Integrate with QwenAgent

Update `agents/qwen_agent.py`:

```python
from git_operations import GitOperations

class QwenAgent:
    def __init__(self, config_path: str):
        # ... existing code ...
        self.git = GitOperations()  # Add git operations
    
    def execute_phase(self, phase_num: int, dry_run: bool = False) -> bool:
        """Execute phase and commit results"""
        # ... existing execution code ...
        
        if not dry_run and success_count > 0:
            # Commit phase results
            commit_message = f"[QWEN] Complete Phase {phase_num}: {phase['name']}"
            
            if self.git.commit(self.project_root, commit_message, phase=phase_num):
                print(f"\n✅ Committed Phase {phase_num} results")
                
                # Optionally push (can be disabled)
                if os.getenv('QWEN_AUTO_PUSH', 'false').lower() == 'true':
                    self.git.push(self.project_root)
        
        return success_count == len(phase['tasks'])
```

## Step 6: Test Complete Workflow

### 6.1 Dry run test

```bash
# Ensure environment is loaded
source ~/.agent-forge.env

# Test with dry run (no commits)
cd /home/flip/agent-forge
python3 agents/qwen_agent.py \
  --config configs/caramba_personality_ai.yaml \
  --phase 2 \
  --dry-run
```

### 6.2 Real execution test (Phase 2)

```bash
# Execute Phase 2 with agent identity
python3 agents/qwen_agent.py \
  --config configs/caramba_personality_ai.yaml \
  --phase 2

# Check commit author
cd /home/flip/caramba
git log --oneline -1
git show --format=full HEAD | head -20
```

Expected output:
```
commit xxxxxxxxx
Author: m0nk111-qwen-agent <flip+qwen@gmail.com>
Date:   ...

    [QWEN] Complete Phase 2: LLM Integration
    
    Agent: Qwen2.5-Coder 7B
    Phase: 2
```

### 6.3 Verify on GitHub

1. Go to: https://github.com/m0nk111/caramba/commits/main
2. Check latest commit
3. Author should show: **m0nk111-qwen-agent**
4. ✅ Agent identity verified!

## Step 7: Setup Gmail Filters (Optional)

### 7.1 Create filter for agent notifications

Gmail settings → Filters → Create new filter:

```
From:     notifications@github.com
To:       flip+qwen@gmail.com

Actions:
├── Apply label: "Agent: Qwen"
├── Skip inbox (Archive)
└── Mark as read
```

### 7.2 Create filter for important agent notifications

```
From:     notifications@github.com
To:       flip+qwen@gmail.com
Subject:  (failed|error|rejected)

Actions:
├── Apply label: "Agent: Qwen - ALERT"
├── Star
└── Keep in inbox
```

## Security Checklist

- [ ] Token saved in secure location (password manager or keyring)
- [ ] Environment file has 600 permissions: `chmod 600 ~/.agent-forge.env`
- [ ] Environment file NOT committed: `.env` in `.gitignore`
- [ ] Token has expiration date set (90 days)
- [ ] Calendar reminder set for token rotation
- [ ] Fine-grained permissions (only required repos)
- [ ] Test token works before trusting agent with it
- [ ] Backup token in case of emergency (separate secure storage)

## Troubleshooting

### Email not arriving

```bash
# Check spam folder in Gmail
# Wait up to 5 minutes for delivery
# Try resending verification from GitHub settings
```

### Token authentication fails

```bash
# Verify token is correct
echo $QWEN_GITHUB_TOKEN | wc -c  # Should be ~93 characters

# Test token manually
curl -H "Authorization: Bearer $QWEN_GITHUB_TOKEN" \
  https://api.github.com/user
```

### Commits show wrong author

```bash
# Check git config
cd /home/flip/caramba
git config user.name    # Should be: m0nk111-qwen-agent
git config user.email   # Should be: flip+qwen@gmail.com

# Reconfigure
git config user.name "m0nk111-qwen-agent"
git config user.email "flip+qwen@gmail.com"
```

### Permission denied on push

```bash
# Check collaborator status
# Visit: https://github.com/m0nk111/caramba/settings/access
# Ensure: m0nk111-qwen-agent has "Write" access

# Check token permissions
# Visit: https://github.com/settings/tokens
# Ensure: Contents: Read and write is enabled
```

## Next Steps

After successful setup:

1. Execute Phase 2 with agent identity
2. Verify commits appear with agent author
3. Monitor agent activity via GitHub commit history
4. Consider creating additional agent accounts (DeepSeek, etc.)
5. Implement branch-per-phase workflow

## References

- [GitHub Machine Users](https://docs.github.com/en/developers/overview/managing-deploy-keys#machine-users)
- [Fine-grained PAT](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens#creating-a-fine-grained-personal-access-token)
- [Gmail Plus Addressing](https://gmail.googleblog.com/2008/03/2-hidden-ways-to-get-more-from-your.html)
