# Agent-Forge Installation Guide

Complete setup guide for Agent-Forge multi-agent platform.

## Prerequisites

- **OS**: Linux (Ubuntu 20.04+, Debian 11+)
- **Python**: 3.12 or higher
- **Ollama**: For local LLM models (optional but recommended)
- **Git**: Version control
- **systemd**: For service management

## Quick Install

```bash
# 1. Clone repository
git clone https://github.com/your-org/your-project.git
cd agent-forge

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Install Ollama (optional, for local LLMs)
curl -fsSL https://ollama.com/install.sh | sh

# 4. Pull a local model (optional)
ollama pull qwen2.5-coder:7b

# 5. Create secrets directory
mkdir -p secrets/agents secrets/keys
chmod 700 secrets

# 6. Configure your first agent
# Copy example config and customize
cp config/agents/your-agent.yaml.example config/agents/your-agent.yaml
# Edit config/agents/your-agent.yaml with your settings

# 7. Add GitHub token (if using GitHub integration)
echo "ghp_YOUR_TOKEN_HERE" > secrets/agents/your-agent-id.token
chmod 600 secrets/agents/your-agent-id.token

# 8. Install systemd services
sudo cp systemd/agent-forge.service /etc/systemd/system/
sudo cp systemd/agent-forge-auth.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable agent-forge agent-forge-auth
sudo systemctl start agent-forge agent-forge-auth

# 9. Access dashboard
# Open browser: http://YOUR_IP:8897/dashboard.html
# Login with your system SSH credentials
```

## Detailed Setup

### 1. Python Environment

```bash
# Check Python version
python3 --version  # Should be 3.12+

# Optional: Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Ollama Setup (Local LLMs)

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Start Ollama service
sudo systemctl start ollama
sudo systemctl enable ollama

# Pull recommended models
ollama pull qwen2.5-coder:7b        # 4.7GB - Good for coding
ollama pull qwen2.5-coder:14b       # 9GB - Better quality
ollama pull llama3.1:8b             # 4.7GB - General purpose
ollama pull deepseek-coder-v2:16b   # 9GB - Code specialist

# Verify installation
ollama list
```

### 3. Agent Configuration

```bash
# Create agent config
nano config/agents/your-agent.yaml
```

Example configuration:

```yaml
agents:
  - agent_id: my-code-agent
    name: My Code Agent
    agent_type: code
    llm_provider: local
    llm_model: qwen2.5-coder:7b
    enabled: true
    capabilities:
      - code_generation
      - code_review
      - issue_management
    github_token: null  # Stored in secrets/
    local_shell_enabled: true
```

### 4. GitHub Token Setup

```bash
# Generate token at: https://github.com/settings/tokens
# Required scopes: repo, workflow

# Save token securely
echo "ghp_YOUR_TOKEN" > secrets/agents/my-code-agent.token
chmod 600 secrets/agents/my-code-agent.token
```

### 5. Dashboard Authentication

The dashboard uses SSH/PAM authentication (your system login):

```bash
# Auth service starts automatically via systemd
sudo systemctl status agent-forge-auth

# Check auth service
curl http://localhost:7996/health
# Should return: {"status":"healthy","auth_type":"ssh_pam"}

# Access dashboard
# Browser: http://YOUR_IP:8897/dashboard.html
# Login: Use your system username/password
```

### 6. Systemd Services

```bash
# Install services
sudo cp systemd/*.service /etc/systemd/system/
sudo systemctl daemon-reload

# Enable services
sudo systemctl enable agent-forge
sudo systemctl enable agent-forge-auth

# Start services
sudo systemctl start agent-forge
sudo systemctl start agent-forge-auth

# Check status
sudo systemctl status agent-forge
sudo systemctl status agent-forge-auth

# View logs
sudo journalctl -u agent-forge -f --no-pager
sudo journalctl -u agent-forge-auth -f --no-pager
```

### 7. Passwordless Sudo (Optional)

For deployment operations without password prompts:

```bash
# Create sudoers file
sudo visudo -f /etc/sudoers.d/flip-nopasswd

# Add line:
flip ALL=(ALL) NOPASSWD: ALL

# Or command-specific:
flip ALL=(ALL) NOPASSWD: /bin/cp, /usr/bin/pkill, /bin/systemctl
```

## Verification

### Test Auth Service

```bash
# Health check
curl http://localhost:7996/health

# Login test
curl -X POST http://localhost:7996/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"YOUR_USER","password":"YOUR_PASS"}'

# Should return JWT token
```

### Test Agent Service

```bash
# Check service status
systemctl status agent-forge

# Check ports
ss -tlnp | grep ':7996\|:7997\|:7998\|:8897'

# Expected:
# 7996 - Auth service
# 7997 - WebSocket monitoring
# 7998 - Config API
# 8897 - Dashboard HTTP
```

### Test Dashboard

1. Open browser: `http://YOUR_IP:8897/dashboard.html`
2. Should redirect to login page
3. Login with system credentials
4. Dashboard should show active agents
5. Check agent status and logs

### Test Token Loading

```bash
# Test ConfigManager token loading
python3 -c "
from agents.config_manager import ConfigManager
cm = ConfigManager()
agent = cm.get_agent('my-code-agent')
if agent and agent.github_token:
    print('✅ Token loaded successfully')
    print(f'Token (masked): {agent.github_token[:10]}...')
else:
    print('❌ Token not loaded')
"
```

## Troubleshooting

### Auth Service Won't Start

```bash
# Check logs
sudo journalctl -u agent-forge-auth -n 50 --no-pager

# Common issues:
# 1. Port 7996 already in use
ss -tlnp | grep 7996
sudo pkill -f auth_routes

# 2. simplepam not installed
pip install simplepam PyJWT

# 3. PAM permissions
# User must have valid system login
```

### Dashboard Can't Connect

```bash
# Check all services
systemctl status agent-forge agent-forge-auth

# Check firewall
sudo ufw status
sudo ufw allow 7996/tcp
sudo ufw allow 7997/tcp
sudo ufw allow 8897/tcp

# Check CORS
# Edit api/auth_routes.py and add your IP:
# allow_origins=[
#     "http://YOUR_IP:8897",
#     ...
# ]
```

### Token Not Loading

```bash
# Check secrets directory
ls -la secrets/agents/

# Files should be:
# - Owned by your user
# - Permissions: 0600 (rw-------)
# - Contains valid GitHub token

# Fix permissions
chmod 700 secrets
chmod 600 secrets/agents/*.token
```

### Ollama Connection Issues

```bash
# Check Ollama service
systemctl status ollama

# Test Ollama
curl http://localhost:11434/api/version

# Restart if needed
sudo systemctl restart ollama

# Check models
ollama list
```

## Next Steps

1. **Configure Agents**: Edit agent config files in `config/agents/` with your project settings
2. **Add Repositories**: Edit `config/repositories.yaml` for GitHub monitoring
3. **Setup Agent GitHub Account**: See [GitHub Bot Account Setup](#github-bot-account-setup) below
4. **Configure Authentication**: See [Dashboard Authentication Setup](#dashboard-authentication-setup) below
5. **Review Docs**: 
   - [TOKEN_SECURITY.md](TOKEN_SECURITY.md) - Token security guide
   - [ARCHITECTURE.md](../ARCHITECTURE.md) - System architecture
   - [DEPLOYMENT.md](DEPLOYMENT.md) - Production deployment guide
6. **Test Agent**: Run a simple task to verify everything works
7. **Monitor**: Watch dashboard for agent activity

---

## GitHub Bot Account Setup

For automated GitHub operations, create a dedicated machine user account.

### Prerequisites

- Gmail account (or any email provider supporting `+` addressing)
- Access to GitHub.com
- Password manager (recommended)

### 1. Create Machine User Account

**1.1 Sign out of current GitHub account**

```bash
# Open browser in incognito/private mode
# Or sign out: https://github.com/logout
```

**1.2 Create new account**

Go to: https://github.com/signup

```
Username:   <your-username>-<agent-name>-agent
            Example: your-agent
Email:      <your-email>+<agent-name>@gmail.com
            Example: flip+qwen@gmail.com
Password:   <secure password - save in password manager>
```

**Important:**
- Username format: `<your-username>-<agent-name>-agent`
- Use `+` addressing so emails arrive in your main inbox
- Use strong, unique password (generate with password manager)

**1.3 Verify email**

1. GitHub sends verification email to `your-email+agent@gmail.com`
2. Email arrives in your main inbox: `your-email@gmail.com`
3. Click verification link
4. ✅ Account is verified

**1.4 Complete profile (optional but recommended)**

```
Name:        <Agent Name> Bot
             Example: Qwen Agent Bot
Bio:         Autonomous coding agent powered by <LLM>
             Managed by @<your-username>
Location:    localhost:11434
Website:     https://github.com/<your-username>/agent-forge
```

### 2. Generate Fine-Grained Personal Access Token

**2.1 Navigate to token settings**

1. Sign in as machine user account
2. Go to: Settings → Developer settings → Personal access tokens → Fine-grained tokens
3. Click: "Generate new token"

**2.2 Configure token**

```
Token name:     agent-forge-<agent-name>-token
Description:    Token for <agent> to commit/push to repositories
Expiration:     90 days (set calendar reminder to rotate)
```

**2.3 Repository access**

**Option A: Select repositories** (recommended)
- ✅ Select your target repositories
- Example: owner/agent-forge, owner/project1, owner/project2

**Option B: All repositories** (less secure, not recommended)

**2.4 Permissions**

Required permissions:

```
Repository permissions:
├── Contents:              Read and write
├── Commit statuses:       Read and write  
├── Pull requests:         Read and write
├── Issues:                Read and write (optional)
├── Workflows:             Read and write (if editing GitHub Actions)
└── Metadata:              Read-only (automatic)
```

**2.5 Generate and save token**

1. Click "Generate token"
2. **COPY TOKEN IMMEDIATELY** (shown only once!)
3. Save in Agent-Forge secrets:

```bash
# Save token in secrets directory
echo "github_pat_xxxxxxxxxxxxx" > secrets/agents/<agent-id>.token
chmod 600 secrets/agents/<agent-id>.token

# Verify token is saved
ls -la secrets/agents/<agent-id>.token
# Should show: -rw------- 1 user user 93 ... <agent-id>.token
```

Token format: `github_pat_11XXXXXXXXXXXXXXXXX_YYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYY`

**Optional: Save in environment** (for manual testing)

```bash
# Option 1: Password manager (recommended for humans)
# Save as: "GitHub PAT - <agent-account-name>"

# Option 2: Environment file (for testing)
echo "AGENT_GITHUB_TOKEN=github_pat_xxxxxxxxxxxxx" >> ~/.agent-forge.env
chmod 600 ~/.agent-forge.env
source ~/.agent-forge.env
```

### 3. Add as Collaborator to Repositories

**3.1 Add to target repositories**

**As your main account:**

1. Go to: `https://github.com/<owner>/<repo>/settings/access`
2. Click: "Add people"
3. Search: `<agent-username>` (e.g., `your-agent`)
4. Role: **Write** (can push to branches, create PRs)
5. Click: "Add to this repository"

**3.2 Accept invitation**

**As machine user:**

1. Check email: arrives in your main inbox
2. Click invitation link
3. Click: "Accept invitation"
4. ✅ Now collaborator on repository

**3.3 Repeat for all target repositories**

### 4. Configure Agent-Forge

**4.1 Update agent configuration**

Edit your agent config file (e.g., `config/agents/your-agent.yaml`):

```yaml
agents:
  - agent_id: my-bot-agent
    name: My Bot Agent
    agent_type: bot
    enabled: true
    
    # GitHub configuration
    github:
      username: your-agent  # Machine user username
      email: flip+qwen@gmail.com     # Machine user email
      token: null  # Loaded from secrets/agents/my-bot-agent.token
      
    # Capabilities
    capabilities:
      - git_commit
      - git_push
      - github_issues
      - github_prs
```

**4.2 Test token loading**

```bash
# Test ConfigManager token loading
python3 -c "
from agents.config_manager import ConfigManager
cm = ConfigManager()
agent = cm.get_agent('my-bot-agent')
if agent and agent.github_token:
    print('✅ Token loaded successfully')
    print(f'Token (masked): {agent.github_token[:10]}...')
else:
    print('❌ Token not loaded')
"
```

**4.3 Test GitHub connectivity**

```bash
# Test GitHub API with token
curl -H "Authorization: token $(cat secrets/agents/my-bot-agent.token)" \
  https://api.github.com/user

# Should return machine user details
```

### 5. Setup Gmail Filters (Optional)

**5.1 Create filter for agent notifications**

Gmail settings → Filters → Create new filter:

```
From:     notifications@github.com
To:       your-email+agent@gmail.com

Actions:
├── Apply label: "Agent: <Name>"
├── Skip inbox (Archive)
└── Mark as read
```

**5.2 Create filter for important agent notifications**

```
From:     notifications@github.com
To:       your-email+agent@gmail.com
Subject:  (failed|error|rejected)

Actions:
├── Apply label: "Agent: <Name> - ALERT"
├── Star
└── Keep in inbox
```

### Security Checklist

- [ ] Token saved in `secrets/agents/<agent-id>.token`
- [ ] Token file has 600 permissions: `chmod 600 secrets/agents/*.token`
- [ ] Secrets directory has 700 permissions: `chmod 700 secrets`
- [ ] Secrets directory in `.gitignore`
- [ ] Token has expiration date set (90 days)
- [ ] Calendar reminder set for token rotation
- [ ] Fine-grained permissions (only required repos)
- [ ] Machine user has Write (not Admin) access
- [ ] Test token before agent uses it

### Troubleshooting

**Email not arriving**

```bash
# Check spam folder
# Wait up to 5 minutes for delivery
# Try resending verification from GitHub settings
```

**Token authentication fails**

```bash
# Verify token is correct
cat secrets/agents/<agent-id>.token | wc -c  # Should be ~93 characters

# Test token manually
TOKEN=$(cat secrets/agents/<agent-id>.token)
curl -H "Authorization: Bearer $TOKEN" https://api.github.com/user
```

**Permission denied on push**

```bash
# Check collaborator status
# Visit: https://github.com/<owner>/<repo>/settings/access
# Ensure: Machine user has "Write" access

# Check token permissions
# Visit: https://github.com/settings/tokens
# Ensure: Contents: Read and write is enabled
```

---

## Dashboard Authentication Setup

Agent-Forge supports two authentication methods for the web dashboard.

### Option 1: SSH/PAM Authentication (Default)

Uses your system login credentials (simplest, no additional setup).

**Already configured if you followed Quick Install!**

```bash
# Verify auth service is running
sudo systemctl status agent-forge-auth

# Test health
curl http://localhost:7996/health
# Returns: {"status":"healthy","auth_type":"ssh_pam"}

# Test login
curl -X POST http://localhost:7996/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"YOUR_USER","password":"YOUR_PASS"}'
# Returns: JWT token if successful
```

**Troubleshooting SSH/PAM Auth:**

```bash
# Common issues:
# 1. simplepam not installed
pip install simplepam PyJWT

# 2. PAM permissions
# User must have valid system login

# 3. Port 7996 in use
ss -tlnp | grep 7996
sudo pkill -f auth_routes
sudo systemctl restart agent-forge-auth
```

### Option 2: Google OAuth (Optional)

Use Google accounts for authentication (multi-user setups).

**Step 1: Google Cloud Project**

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click project dropdown → "NEW PROJECT"
3. Project name: `agent-forge-auth`
4. Click "CREATE"

**Step 2: OAuth Consent Screen**

1. Sidebar: "APIs & Services" → "OAuth consent screen"
2. Choose "External" (for personal use)
3. Fill in:
   - **App name**: `Agent-Forge Dashboard`
   - **User support email**: Your email
   - **Developer contact**: Your email
4. Scopes: Add:
   - `.../auth/userinfo.email`
   - `.../auth/userinfo.profile`
   - `openid`
5. Test users: Add authorized Google emails
6. Click "SAVE AND CONTINUE"

**Step 3: OAuth Client Credentials**

1. Sidebar: "APIs & Services" → "Credentials"
2. Click "CREATE CREDENTIALS" → "OAuth client ID"
3. Application type: **Web application**
4. Name: `Agent-Forge Dashboard Client`
5. Authorized JavaScript origins:
   ```
   http://localhost:8897
   http://<YOUR_IP>:8897
   http://<YOUR_HOSTNAME>:8897
   ```
6. Authorized redirect URIs:
   ```
   http://localhost:8897/auth/callback
   http://<YOUR_IP>:8897/auth/callback
   http://<YOUR_HOSTNAME>:8897/auth/callback
   ```
7. Click "CREATE"
8. **Save Client ID and Client Secret**

**Step 4: Configure Agent-Forge**

Create `secrets/oauth/google.json`:

```json
{
  "client_id": "xxxxx.apps.googleusercontent.com",
  "client_secret": "GOCSPX-xxxxxxxxxxxxx",
  "redirect_uri": "http://<YOUR_IP>:8897/auth/callback"
}
```

Secure the file:

```bash
chmod 600 secrets/oauth/google.json
```

**Step 5: Update Auth Service**

Edit `api/auth_routes.py` to enable Google OAuth:

```python
# Add at top
import json

# Load OAuth config
with open('secrets/oauth/google.json') as f:
    OAUTH_CONFIG = json.load(f)

# Add OAuth routes (see full implementation in GOOGLE_OAUTH_SETUP.md)
```

Restart services:

```bash
sudo systemctl restart agent-forge-auth
```

**Step 6: Test OAuth Login**

1. Open: `http://<YOUR_IP>:8897/dashboard.html`
2. Click "Sign in with Google"
3. Authorize with Google account
4. Redirect back to dashboard
5. ✅ OAuth working!

**OAuth Costs:**

- **Free**: 10,000 requests/day (plenty for personal use)
- **Paid**: Only if you exceed quota (unlikely)

**OAuth Troubleshooting:**

```bash
# Invalid redirect URI
# Fix: Add exact URI to Google Console authorized redirects

# Unauthorized user
# Fix: Add user email to "Test users" in OAuth consent screen

# CORS errors
# Fix: Update CORS origins in auth_routes.py
```

---

## Next Steps

1. **Configure Agents**: Edit `config/agents/*.yaml` with your project settings
2. **Add Repositories**: Edit `config/repositories.yaml` for GitHub monitoring
3. **Review Docs**: 
   - [TOKEN_SECURITY.md](TOKEN_SECURITY.md) - Token security guide
   - [ARCHITECTURE.md](../ARCHITECTURE.md) - System architecture
   - [DEPLOYMENT.md](DEPLOYMENT.md) - Production deployment guide
4. **Test Agent**: Run a simple task to verify everything works
5. **Monitor**: Watch dashboard for agent activity

---

## Uninstall

```bash
# Stop and disable services
sudo systemctl stop agent-forge agent-forge-auth
sudo systemctl disable agent-forge agent-forge-auth

# Remove services
sudo rm /etc/systemd/system/agent-forge*.service
sudo systemctl daemon-reload

# Remove files
cd ~
rm -rf agent-forge

# Remove sudoers (if created)
sudo rm /etc/sudoers.d/flip-nopasswd
```

## Support

- **Issues**: https://github.com/your-org/your-project/issues
- **Docs**: See docs/ directory
- **Logs**: `sudo journalctl -u agent-forge -f --no-pager`
