# Troubleshooting Guide 🔧

Common issues and solutions for Agent-Forge development and deployment.

---

## 📋 Table of Contents

- [Service Issues](#service-issues)
- [Port Conflicts](#port-conflicts)
- [GitHub Integration](#github-integration)
- [Ollama Issues](#ollama-issues)
- [WebSocket Problems](#websocket-problems)
- [Agent Issues](#agent-issues)
- [Configuration Errors](#configuration-errors)
- [Performance Problems](#performance-problems)
- [Database Issues](#database-issues)
- [Logging and Debugging](#logging-and-debugging)

---

## 🚨 Service Issues

### Service Won't Start

**Symptom**: `python -m agents.service_manager` fails to start

**Common Causes & Solutions**:

1. **Missing Dependencies**:
   ```bash
   # Install all requirements
   pip install -r requirements.txt
   
   # Verify installation
   python -c "import flask, requests, yaml; print('OK')"
   ```

2. **Python Version**:
   ```bash
   # Check Python version (need 3.12+)
   python --version
   
   # If too old, use pyenv or update
   pyenv install 3.12.0
   pyenv local 3.12.0
   ```

3. **Port Already in Use**:
   ```bash
   # Check what's using ports
   lsof -i:8080  # Service Manager
   lsof -i:7997  # WebSocket
   lsof -i:8897  # Frontend
   
   # Kill processes
   lsof -ti:8080 | xargs kill -9
   ```

4. **Permission Issues**:
   ```bash
   # Check file permissions
   ls -la agents/
   
   # Fix if needed
   chmod +x scripts/*.sh
   chmod 644 config/*.yaml
   ```

### Service Crashes Immediately

**Check logs**:
```bash
# View recent logs
tail -50 logs/agent-forge.log

# Watch logs in real-time
tail -f logs/agent-forge.log

# Check systemd logs (if using systemd)
sudo journalctl -u agent-forge -n 50 --no-pager
```

**Common Crashes**:

1. **Configuration Error**:
   ```bash
   # Validate configuration
   python -c "import yaml; yaml.safe_load(open('config/system.yaml'))"
   
   # Check for typos
   yamllint config/*.yaml
   ```

2. **Missing Environment Variables**:
   ```bash
   # Check required variables
   echo $GITHUB_TOKEN
   echo $GITHUB_BOT_TOKEN
   
   # Set if missing
   export GITHUB_TOKEN="ghp_your_token"
   export GITHUB_BOT_TOKEN="ghp_bot_token"
   
   # Or use .env file
   cp .env.example .env
   # Edit .env with your tokens
   ```

3. **Database Connection**:
   ```bash
   # Check if database file exists
   ls -la data/agent-forge.db
   
   # Initialize if missing
   python -m agents.init_db
   ```

---

## 🔌 Port Conflicts

### Port Already in Use

**Error**: `Address already in use: 8080` (or 7997, 8897)

**Diagnosis**:
```bash
# Comprehensive port check
for port in 8080 7997 8897; do
    echo "=== Port $port ==="
    lsof -i:$port
done

# Alternative (if lsof not available)
netstat -tulpn | grep -E '8080|7997|8897'
```

**Solutions**:

1. **Kill Conflicting Process**:
   ```bash
   # Find process ID
   lsof -ti:8080
   
   # Kill process
   kill -9 $(lsof -ti:8080)
   
   # Kill all agent-forge processes
   pkill -f "python.*service_manager"
   ```

2. **Use Different Ports**:
   ```bash
   # Start with custom ports
   python -m agents.service_manager \
       --service-port 8081 \
       --monitor-port 7998 \
       --web-port 8898
   ```

3. **Update Configuration**:
   ```yaml
   # config/system.yaml
   service_manager:
     service_port: 8081  # Change from 8080
     monitoring_port: 7998  # Change from 7997
     web_ui_port: 8898  # Change from 8897
   ```

### Frontend Can't Connect to Backend

**Symptom**: Dashboard loads but shows "Connection failed"

**Check**:
```bash
# Test service manager API
curl http://localhost:8080/health

# Test WebSocket
curl -i -N \
    -H "Connection: Upgrade" \
    -H "Upgrade: websocket" \
    -H "Sec-WebSocket-Key: test" \
    -H "Sec-WebSocket-Version: 13" \
    http://localhost:7997/ws/monitor
```

**Solutions**:

1. **Update Frontend URLs**:
   ```javascript
   // frontend/dashboard.html
   const API_BASE = 'http://localhost:8081';  // Match your port
   const WS_URL = 'ws://localhost:7998/ws/monitor';
   ```

2. **Check Firewall**:
   ```bash
   # Ubuntu/Debian
   sudo ufw status
   sudo ufw allow 8080,7997,8897/tcp
   
   # Check iptables
   sudo iptables -L -n | grep -E '8080|7997|8897'
   ```

---

## 🐙 GitHub Integration

### Authentication Failed

**Error**: `401 Unauthorized` or `Bad credentials`

**Diagnosis**:
```bash
# Test token manually
curl -H "Authorization: Bearer $GITHUB_TOKEN" \
    https://api.github.com/user

# Check token scopes
curl -I -H "Authorization: Bearer $GITHUB_TOKEN" \
    https://api.github.com/user \
    | grep x-oauth-scopes
```

**Solutions**:

1. **Verify Token**:
   - Go to GitHub → Settings → Developer settings → Personal access tokens
   - Check token is not expired
   - Required scopes: `repo`, `workflow`, `admin:org` (for bot operations)

2. **Update Token**:
   ```bash
   # Update environment variable
   export GITHUB_TOKEN="ghp_new_token"
   
   # Or update .env file
   echo "GITHUB_TOKEN=ghp_new_token" > .env
   
   # Restart service
   sudo systemctl restart agent-forge
   ```

3. **Token Permissions**:
   ```bash
   # Check what your token can access
   curl -H "Authorization: Bearer $GITHUB_TOKEN" \
       https://api.github.com/user/repos | jq '.[].full_name'
   ```

### Rate Limit Exceeded

**Error**: `403 Forbidden - API rate limit exceeded`

**Check Limits**:
```bash
# Check current rate limit
curl -H "Authorization: Bearer $GITHUB_TOKEN" \
    https://api.github.com/rate_limit

# Example response:
# {
#   "resources": {
#     "core": {
#       "limit": 5000,
#       "remaining": 0,
#       "reset": 1728234567
#     }
#   }
# }
```

**Solutions**:

1. **Wait for Reset**:
   ```bash
   # Check reset time
   date -d @1728234567  # Replace with reset timestamp
   
   # Wait until reset time
   ```

2. **Reduce Polling Frequency**:
   ```yaml
   # config/system.yaml
   service_manager:
     polling_interval: 600  # Change from 300 to 600 seconds (10 min)
   ```

3. **Use Multiple Tokens** (for high-volume):
   ```yaml
   # config/system.yaml
   github:
     tokens:
       - "ghp_token1"
       - "ghp_token2"
       - "ghp_token3"
     rotation: "round-robin"  # Rotate between tokens
   ```

### Can't Create Pull Request

**Error**: `422 Unprocessable Entity - Validation Failed`

**Common Causes**:

1. **No Changes to Commit**:
   ```bash
   # Check if branch has commits
   git log main..feat/your-branch
   
   # Should show at least one commit
   ```

2. **Branch Already Has PR**:
   ```bash
   # Check existing PRs
   gh pr list --head feat/your-branch
   ```

3. **Invalid Base/Head Branch**:
   ```bash
   # Verify branches exist
   gh api repos/m0nk111/agent-forge/branches
   
   # Use correct base branch
   gh pr create --base main --head feat/your-branch
   ```

---

## 🦙 Ollama Issues

### Ollama Not Running

**Error**: `Connection refused: http://localhost:11434`

**Check Status**:
```bash
# Check if Ollama is running
systemctl status ollama

# Or check process
ps aux | grep ollama

# Check if port is listening
lsof -i:11434
```

**Solutions**:

1. **Start Ollama**:
   ```bash
   # Start Ollama service
   systemctl start ollama
   
   # Or run manually
   ollama serve
   ```

2. **Enable Auto-Start**:
   ```bash
   # Enable on boot
   systemctl enable ollama
   
   # Verify
   systemctl is-enabled ollama
   ```

3. **Check Ollama Version**:
   ```bash
   # Version should be 0.1.30+
   ollama --version
   
   # Update if needed
   curl -fsSL https://ollama.com/install.sh | sh
   ```

### Model Not Found

**Error**: `model 'qwen2.5-coder:7b' not found`

**List Models**:
```bash
# See installed models
ollama list

# Expected output should include:
# qwen2.5-coder:7b
```

**Solutions**:

1. **Pull Model**:
   ```bash
   # Pull required model
   ollama pull qwen2.5-coder:7b
   
   # Verify it's available
   ollama list | grep qwen2.5-coder
   ```

2. **Use Alternative Model**:
   ```yaml
   # config/agents.yaml
   code_agent:
     model: "qwen2.5-coder:14b"  # Or other available model
   ```

3. **Check Model Name**:
   ```bash
   # Exact name must match
   ollama list
   
   # Use exact name from list
   # e.g., "qwen2.5-coder:7b" not "qwen2.5-coder"
   ```

### Slow Model Inference

**Symptom**: Responses take > 30 seconds

**Diagnosis**:
```bash
# Test model speed
time ollama run qwen2.5-coder:7b "Write a hello world in Python"

# Check system resources
htop
nvidia-smi  # If using GPU
```

**Solutions**:

1. **Use Smaller Model**:
   ```yaml
   # config/agents.yaml
   code_agent:
     model: "qwen2.5-coder:7b"  # Instead of 32b
   ```

2. **Enable GPU** (if available):
   ```bash
   # Check NVIDIA drivers
   nvidia-smi
   
   # Ollama uses GPU automatically if available
   # Verify GPU is being used
   nvidia-smi dmon
   # Run agent, watch GPU utilization
   ```

3. **Increase Context Window**:
   ```yaml
   # config/agents.yaml
   code_agent:
     model: "qwen2.5-coder:7b"
     num_ctx: 4096  # Reduce from 8192 for faster inference
   ```

4. **Adjust Temperature**:
   ```yaml
   code_agent:
     temperature: 0.1  # Lower = faster, more deterministic
   ```

---

## 🔌 WebSocket Problems

### WebSocket Connection Failed

**Error in browser console**: `WebSocket connection failed`

**Diagnosis**:
```bash
# Check WebSocket server is running
curl -i -N \
    -H "Connection: Upgrade" \
    -H "Upgrade: websocket" \
    http://localhost:7997/ws/monitor

# Check logs
grep -i websocket logs/agent-forge.log
```

**Solutions**:

1. **Verify URL**:
   ```javascript
   // frontend/dashboard.html
   // Should be ws:// not wss:// for local
   const ws = new WebSocket('ws://localhost:7997/ws/monitor');
   ```

2. **Check Port**:
   ```bash
   # WebSocket should be on 7997
   lsof -i:7997
   
   # If not, check config
   grep monitoring_port config/system.yaml
   ```

3. **Check Browser**:
   - Open Browser DevTools → Network → WS tab
   - Check for connection attempt
   - Look at error messages

### WebSocket Disconnects Frequently

**Symptom**: Connection drops every few seconds

**Check Logs**:
```bash
# Watch WebSocket logs
tail -f logs/agent-forge.log | grep -i websocket
```

**Solutions**:

1. **Increase Timeout**:
   ```python
   # agents/websocket_handler.py
   # Adjust ping/pong timeout
   WEBSOCKET_PING_INTERVAL = 30  # seconds
   WEBSOCKET_PING_TIMEOUT = 60
   ```

2. **Check Reverse Proxy** (if using nginx):
   ```nginx
   # /etc/nginx/sites-available/agent-forge
   location /ws/ {
       proxy_pass http://localhost:7997;
       proxy_http_version 1.1;
       proxy_set_header Upgrade $http_upgrade;
       proxy_set_header Connection "Upgrade";
       proxy_read_timeout 86400;  # 24 hours
   }
   ```

3. **Browser Keep-Alive**:
   ```javascript
   // frontend/dashboard.html
   // Add heartbeat
   setInterval(() => {
       if (ws.readyState === WebSocket.OPEN) {
           ws.send(JSON.stringify({type: 'ping'}));
       }
   }, 30000);  // Every 30 seconds
   ```

---

## 🤖 Agent Issues

### Agent Stuck in "Working" State

**Symptom**: Agent status shows "working" indefinitely

**Diagnosis**:
```bash
# Check agent process
ps aux | grep "bot_agent\|code_agent"

# Check agent logs
tail -100 logs/agent-forge.log | grep -A 10 "agent_id"

# Check API status
curl http://localhost:8080/agents
```

**Solutions**:

1. **Restart Agent**:
   ```bash
   # Via API
   curl -X POST http://localhost:8080/agents/bot-1/stop
   curl -X POST http://localhost:8080/agents/bot-1/start
   
   # Or restart service
   sudo systemctl restart agent-forge
   ```

2. **Check for Deadlock**:
   ```bash
   # Get stack trace
   kill -USR1 $(pgrep -f service_manager)
   
   # Check logs for traceback
   tail -50 logs/agent-forge.log
   ```

3. **Increase Timeout**:
   ```yaml
   # config/agents.yaml
   bot_agent:
     task_timeout: 1800  # 30 minutes (increase from default)
   ```

### Agent Not Processing Issues

**Symptom**: New issues assigned but not picked up

**Check**:
```bash
# Verify polling is enabled
grep enable_polling config/system.yaml

# Check polling logs
tail -f logs/agent-forge.log | grep -i polling

# Test GitHub API
curl -H "Authorization: Bearer $GITHUB_TOKEN" \
    "https://api.github.com/repos/m0nk111/agent-forge/issues?state=open&assignee=m0nk111-bot"
```

**Solutions**:

1. **Enable Polling**:
   ```yaml
   # config/system.yaml
   service_manager:
     enable_polling: true  # Ensure this is true
   ```

2. **Check Issue Assignment**:
   - Issue must be assigned to bot account
   - Bot account must have write access to repo
   - Issue must not have `wontfix` or `duplicate` labels

3. **Reduce Polling Interval** (for testing):
   ```yaml
   service_manager:
     polling_interval: 60  # 1 minute (for testing)
   ```

### Agent Returns Empty Responses

**Symptom**: Agent processes task but returns empty solution

**Check**:
```bash
# Test Ollama directly
ollama run qwen2.5-coder:7b "Write a hello world function"

# Check agent config
cat config/agents.yaml | grep -A 10 code_agent
```

**Solutions**:

1. **Check Model Context**:
   ```yaml
   # config/agents.yaml
   code_agent:
     num_ctx: 8192  # Increase if truncated
     max_tokens: 4096  # Increase max response length
   ```

2. **Improve Prompt**:
   ```python
   # agents/code_agent.py
   # Add more context to prompt
   prompt = f"""
   Project: {repo_name}
   Issue: #{issue_number}
   Title: {issue_title}
   Description: {issue_body}
   
   Generate a complete solution with:
   1. Code implementation
   2. Tests
   3. Documentation
   """
   ```

3. **Check Temperature**:
   ```yaml
   code_agent:
     temperature: 0.7  # 0 = deterministic, 1 = creative
   ```

---

## ⚙️ Configuration Errors

### Invalid YAML Syntax

**Error**: `yaml.scanner.ScannerError: while scanning a simple key`

**Validate YAML**:
```bash
# Check syntax
python -c "import yaml; yaml.safe_load(open('config/system.yaml'))"

# Or use yamllint
yamllint config/*.yaml

# Find specific error
yaml-validator config/system.yaml
```

**Common Mistakes**:

```yaml
# ❌ BAD: Inconsistent indentation
service_manager:
  enable_polling: true
   polling_interval: 300  # Wrong indent!

# ✅ GOOD: Consistent indentation (2 spaces)
service_manager:
  enable_polling: true
  polling_interval: 300

# ❌ BAD: Missing space after colon
service_manager:
  enable_polling:true  # No space!

# ✅ GOOD: Space after colon
service_manager:
  enable_polling: true

# ❌ BAD: Unquoted special characters
repo: m0nk111/agent-forge:latest  # Colon is special!

# ✅ GOOD: Quote strings with special chars
repo: "m0nk111/agent-forge:latest"
```

### Configuration Not Loading

**Symptom**: Changes to config files not reflected

**Solutions**:

1. **Verify File Path**:
   ```bash
   # Check if file exists
   ls -la config/system.yaml
   
   # Check permissions
   ls -l config/system.yaml
   # Should show: -rw-r--r--
   ```

2. **Restart Service**:
   ```bash
   # Config only loads at startup
   sudo systemctl restart agent-forge
   
   # Or if running manually
   # Ctrl+C to stop, then restart
   python -m agents.service_manager
   ```

3. **Check Config Priority**:
   ```bash
   # Environment variables override config files
   env | grep AGENT_FORGE
   
   # Unset if needed
   unset AGENT_FORGE_POLLING_INTERVAL
   ```

---

## 🐌 Performance Problems

### High CPU Usage

**Diagnosis**:
```bash
# Check CPU usage
top -p $(pgrep -f service_manager)

# Profile with py-spy (if installed)
py-spy top --pid $(pgrep -f service_manager)
```

**Solutions**:

1. **Reduce Polling Frequency**:
   ```yaml
   service_manager:
     polling_interval: 600  # Increase from 300
   ```

2. **Limit Concurrent Agents**:
   ```yaml
   service_manager:
     max_concurrent_agents: 2  # Reduce from 5
   ```

3. **Use Smaller Model**:
   ```yaml
   code_agent:
     model: "qwen2.5-coder:7b"  # Instead of 32b
   ```

### High Memory Usage

**Diagnosis**:
```bash
# Check memory
ps aux | grep service_manager

# Detailed memory info
pmap $(pgrep -f service_manager)
```

**Solutions**:

1. **Reduce Model Context**:
   ```yaml
   code_agent:
     num_ctx: 4096  # Reduce from 8192
   ```

2. **Enable Memory Limits** (systemd):
   ```ini
   # /etc/systemd/system/agent-forge.service
   [Service]
   MemoryMax=2G
   MemoryHigh=1.5G
   ```

3. **Restart Periodically**:
   ```bash
   # Add to crontab
   0 3 * * * systemctl restart agent-forge
   ```

---

## 🗄️ Database Issues

### Database Locked

**Error**: `database is locked`

**Solutions**:

1. **Check for Concurrent Access**:
   ```bash
   # Find processes accessing database
   lsof data/agent-forge.db
   
   # Kill if needed
   kill -9 <PID>
   ```

2. **Increase Timeout**:
   ```python
   # agents/database.py
   conn = sqlite3.connect('data/agent-forge.db', timeout=30)
   ```

3. **Use WAL Mode**:
   ```python
   # agents/database.py
   conn.execute('PRAGMA journal_mode=WAL')
   ```

### Database Corruption

**Error**: `database disk image is malformed`

**Solutions**:

1. **Try Repair**:
   ```bash
   # Backup first!
   cp data/agent-forge.db data/agent-forge.db.backup
   
   # Try to recover
   sqlite3 data/agent-forge.db "PRAGMA integrity_check"
   
   # If recoverable
   sqlite3 data/agent-forge.db ".dump" | sqlite3 data/agent-forge-fixed.db
   mv data/agent-forge-fixed.db data/agent-forge.db
   ```

2. **Restore from Backup**:
   ```bash
   # Use latest backup
   cp data/backups/agent-forge-YYYY-MM-DD.db data/agent-forge.db
   ```

3. **Reinitialize** (data loss!):
   ```bash
   # Remove corrupted database
   rm data/agent-forge.db
   
   # Reinitialize
   python -m agents.init_db
   ```

---

## 📊 Logging and Debugging

### Enable Debug Logging

**Temporary** (for current session):
```bash
# Set debug level
export LOG_LEVEL=DEBUG

# Start service
python -m agents.service_manager --debug
```

**Permanent**:
```yaml
# config/system.yaml
logging:
  level: DEBUG  # Change from INFO
  file: logs/agent-forge.log
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
```

### View Logs

```bash
# Tail logs
tail -f logs/agent-forge.log

# Search logs
grep -i error logs/agent-forge.log

# Filter by timestamp
awk '/2025-10-06 14:30:00/,/2025-10-06 14:35:00/' logs/agent-forge.log

# View systemd logs
sudo journalctl -u agent-forge -f --no-pager --since "1 hour ago"

# Export logs
sudo journalctl -u agent-forge --since today > today-logs.txt
```

### Debug Specific Component

```bash
# Debug agent only
python -c "
import logging
logging.basicConfig(level=logging.DEBUG)
from agents.bot_agent import BotAgent
agent = BotAgent('test', 'qwen2.5-coder:7b')
# ... test code ...
"

# Debug WebSocket
python -m agents.websocket_handler --debug --port 7997

# Debug GitHub API
curl -v -H "Authorization: Bearer $GITHUB_TOKEN" \
    https://api.github.com/repos/m0nk111/agent-forge/issues
```

---

## 🆘 Getting Help

### Before Asking for Help

1. **Check logs** (see above)
2. **Search existing issues**: [GitHub Issues](https://github.com/m0nk111/agent-forge/issues)
3. **Review documentation**: [docs/](.)
4. **Try troubleshooting steps** (this document)

### Reporting Issues

Include in bug report:

```bash
# System info
uname -a
python --version
ollama --version

# Service status
systemctl status agent-forge

# Recent logs
tail -50 logs/agent-forge.log

# Configuration (redact tokens!)
cat config/system.yaml | sed 's/ghp_.*/ghp_REDACTED/g'

# Port status
lsof -i:8080,7997,8897
```

### Emergency Recovery

If everything is broken:

```bash
# Nuclear option: full reset
sudo systemctl stop agent-forge
pkill -f service_manager
rm -rf logs/*
rm data/agent-forge.db
git reset --hard HEAD
pip install -r requirements.txt --force-reinstall
python -m agents.init_db
sudo systemctl start agent-forge
```

---

**Need more help?** Open an issue: [GitHub Issues](https://github.com/m0nk111/agent-forge/issues)

*Last updated: October 6, 2025*
