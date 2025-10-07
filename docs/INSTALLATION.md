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
git clone https://github.com/m0nk111/agent-forge.git
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
cp config/agents.yaml.example config/agents.yaml
# Edit config/agents.yaml with your settings

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
nano config/agents.yaml
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
sudo journalctl -u agent-forge -f
sudo journalctl -u agent-forge-auth -f
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
sudo journalctl -u agent-forge-auth -n 50

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

1. **Configure Agents**: Edit `config/agents.yaml` with your project settings
2. **Add Repositories**: Edit `config/repositories.yaml` for GitHub monitoring
3. **Review Docs**: 
   - [TOKEN_SECURITY.md](docs/TOKEN_SECURITY.md) - Token security guide
   - [SSH_AUTH_DESIGN.md](docs/SSH_AUTH_DESIGN.md) - Auth architecture
   - [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture
   - [REFACTOR_PLAN.md](REFACTOR_PLAN.md) - Upcoming refactor (Issue #69)
4. **Test Agent**: Run a simple task to verify everything works
5. **Monitor**: Watch dashboard for agent activity

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

- **Issues**: https://github.com/m0nk111/agent-forge/issues
- **Docs**: See docs/ directory
- **Logs**: `sudo journalctl -u agent-forge -f`
