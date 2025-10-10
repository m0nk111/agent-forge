# Port Allocation Reference

> **Complete guide to port usage in Agent-Forge to prevent conflicts and ensure proper configuration**

## 📋 Port Overview Table

| Port | Service | Protocol | Bind Address | Purpose | Status | Configurable |
|------|---------|----------|--------------|---------|--------|--------------|
| **8080** | Service Manager | HTTP/REST | `0.0.0.0` | Service orchestration, REST API | 🟢 Active | ✅ Yes |
| **7997** | WebSocket Server | WebSocket | `0.0.0.0` | Real-time monitoring, log streaming | 🟢 Active | ✅ Yes |
| **8897** | Frontend HTTP | HTTP | `0.0.0.0` | Dashboard hosting | 🟢 Active | ✅ Yes |
| 7996 | Code Agent (optional) | HTTP | `127.0.0.1` | Code generation API | 🟡 Optional | ✅ Yes |
| 11434 | Ollama | HTTP | `127.0.0.1` | Local LLM inference | 🟢 Active | ⚠️ External |

### Legend

- 🟢 **Active**: Required for normal operation
- 🟡 **Optional**: Used for specific features
- ⚠️ **External**: Managed by external service (Ollama)

---

## 🔌 Detailed Port Information

### Port 8080: Service Manager REST API

**Purpose**: Central REST API for service control and monitoring

**Service**: `engine/core/service_manager.py`

**Bind Address**: `0.0.0.0` (all interfaces, LAN accessible)

**Configuration**:

```yaml
# config/system.yaml
service_manager:
  web_ui_port: 8080  # Change here
```

```bash
# Environment variable
export SERVICE_MANAGER_PORT=8080

# Command line
python -m agents.service_manager --web-port 8080
```

**Endpoints**:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Health check |
| `/status` | GET | Service status |
| `/agents` | GET | List agents |
| `/agents/{id}/start` | POST | Start agent |
| `/agents/{id}/stop` | POST | Stop agent |
| `/config` | GET | Get config |
| `/config` | PUT | Update config |

**Common Conflicts**:

- Other web servers (Apache, Nginx on default ports)
- Development servers (Flask, Django)
- Proxy services

**Conflict Resolution**:

```bash
# Check if port is in use
lsof -i:8080

# Find process using port
sudo netstat -tlnp | grep :8080

# Kill process
lsof -ti:8080 | xargs kill -9

# Or change port in config
```

---

### Port 7997: WebSocket Server

**Purpose**: Real-time bidirectional communication for monitoring

**Service**: `engine/operations/websocket_handler.py`

**Bind Address**: `0.0.0.0` (all interfaces, LAN accessible)

**Protocol**: WebSocket (`ws://`)

**Configuration**:

```yaml
# config/system.yaml
service_manager:
  monitoring_port: 7997  # Change here
```

```bash
# Environment variable
export WEBSOCKET_PORT=7997

# Command line
python -m agents.service_manager --monitor-port 7997
```

**Connection URLs**:

```javascript
// Local
ws://localhost:7997/ws/monitor

// LAN
ws://192.168.1.26:7997/ws/monitor

// Auto-detect (recommended)
const host = window.location.hostname;
const ws = new WebSocket(`ws://${host}:7997/ws/monitor`);
```

**Message Types**:

```typescript
{
  type: "agent_state" | "log" | "system" | "heartbeat",
  data: {...}
}
```

**Common Conflicts**:

- Other WebSocket servers
- Development tools (Hot Module Replacement)
- Reverse proxies not configured for WebSocket

**Troubleshooting**:

```bash
# Check WebSocket connection
websocat ws://localhost:7997/ws/monitor

# Or with curl (HTTP upgrade)
curl --include \
     --no-buffer \
     --header "Connection: Upgrade" \
     --header "Upgrade: websocket" \
     --header "Sec-WebSocket-Key: SGVsbG8sIHdvcmxkIQ==" \
     --header "Sec-WebSocket-Version: 13" \
     http://localhost:7997/ws/monitor
```

**Performance Considerations**:

- **Max Connections**: ~1000 (configurable)
- **Message Rate**: ~100/sec per connection
- **Heartbeat Interval**: 30 seconds
- **Reconnect Delay**: 5 seconds

---

### Port 8897: Frontend HTTP Server

**Purpose**: Serve dashboard HTML/CSS/JS files

**Service**: Python HTTP server (`http.server` module)

**Bind Address**: `0.0.0.0` (all interfaces, LAN accessible)

**Configuration**:

```bash
# scripts/launch_dashboard.sh
PORT=8897  # Change here
python3 -m http.server $PORT --directory frontend --bind 0.0.0.0
```

```yaml
# config/system.yaml
service_manager:
  web_ui_port: 8897  # Also update here
```

**Access URLs**:

```
Local:    http://localhost:8897/dashboard.html
LAN:      http://192.168.1.26:8897/dashboard.html
          http://your-ip:8897/dashboard.html
```

**Files Served**:

```
frontend/
├── index.html                  # Landing (auto-redirects)
├── dashboard.html              # ⭐ DEFAULT
├── unified_dashboard.html      # New unified UI
├── monitoring_dashboard.html   # Classic monitoring
└── config_ui.html             # Configuration
```

**Common Confusion** ⚠️:

- **WRONG**: Port 8898
- **CORRECT**: Port 8897

**Common Conflicts**:

- Other HTTP servers on nearby ports
- Previous dashboard instances still running
- Port already bound by crashed process

**Conflict Resolution**:

```bash
# Check port
lsof -i:8897

# Kill all Python HTTP servers on this port
lsof -ti:8897 | xargs kill -9

# Wait a moment for port to be released
sleep 1

# Restart dashboard
./scripts/launch_dashboard.sh
```

**Production Deployment**:

```bash
# Use Nginx as reverse proxy (recommended)
server {
    listen 80;
    server_name agent-forge.local;
    
    location / {
        proxy_pass http://localhost:8897;
    }
    
    location /ws/ {
        proxy_pass http://localhost:7997;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

---

### Port 7996: Code Agent API (Optional)

**Purpose**: Optional HTTP API for direct code generation requests

**Service**: `engine/runners/code_agent.py` (when run as API server)

**Bind Address**: `127.0.0.1` (localhost only, not exposed to LAN)

**Status**: 🟡 Optional (not always running)

**Configuration**:

```bash
# Run code agent as API server
python -m agents.code_agent --api-mode --port 7996
```

**Endpoints**:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/generate` | POST | Generate code |
| `/analyze` | POST | Analyze code |
| `/refactor` | POST | Refactor code |
| `/health` | GET | Health check |

**Use Cases**:

- Direct code generation without issue workflow
- Testing and development
- External tool integration
- CI/CD pipelines

---

### Port 11434: Ollama (External)

**Purpose**: Local LLM inference server (Qwen 2.5 Coder)

**Service**: Ollama (external application)

**Bind Address**: `127.0.0.1` (localhost only)

**Configuration**:

```bash
# Ollama configuration (if needed)
export OLLAMA_HOST=127.0.0.1:11434

# Agent-Forge configuration
# config/agents/your-agent.yaml
code_agent:
  model: "qwen2.5-coder:32b"
  base_url: "http://localhost:11434"  # Change port here if needed
```

**Management**:

```bash
# Check Ollama status
ollama list

# Check if Ollama is running
curl http://localhost:11434/api/version

# Start Ollama (if not running)
ollama serve

# Pull model
ollama pull qwen2.5-coder:32b
```

**Common Issues**:

- Ollama not running
- Model not pulled
- Port conflict (rare)
- Firewall blocking localhost

**Performance**:

- **GPU Required**: For 32B models
- **RAM**: ~20GB for 32B, ~8GB for 7B
- **Response Time**: 2-10 seconds depending on model size

---

## 🔧 Port Configuration Guide

### Changing Ports

#### Method 1: Environment Variables

```bash
export SERVICE_MANAGER_PORT=8080
export WEBSOCKET_PORT=7997
export FRONTEND_PORT=8897

python -m agents.service_manager
```

#### Method 2: Configuration File

```yaml
# config/system.yaml
service_manager:
  web_ui_port: 8080
  monitoring_port: 7997
  frontend_port: 8897
```

#### Method 3: Command Line

```bash
python -m agents.service_manager \
    --web-port 8080 \
    --monitor-port 7997 \
    --frontend-port 8897
```

### Port Range Recommendations

**Production**:

- Service Manager: 8000-8099
- WebSocket: 7000-7999
- Frontend: 8800-8899

**Development**:

- Service Manager: 8080
- WebSocket: 7997
- Frontend: 8897

**CI/CD**:

- Use ephemeral ports (high numbers)
- Check availability before starting

---

## 🚨 Common Port Conflicts

### Problem: Port Already in Use

**Symptoms**:

```
OSError: [Errno 98] Address already in use
```

**Diagnosis**:

```bash
# Find what's using the port
lsof -i:8897

# Example output:
COMMAND   PID USER   FD   TYPE  DEVICE SIZE/OFF NODE NAME
python  12345 user    3u  IPv4 1234567      0t0  TCP *:8897 (LISTEN)
```

**Solutions**:

```bash
# Solution 1: Kill the process
kill -9 12345

# Solution 2: Kill all processes on port
lsof -ti:8897 | xargs kill -9

# Solution 3: Change port in config
# Edit config/system.yaml and use different port

# Solution 4: Wait for port to be released
# Sometimes takes 30-60 seconds after process stops
```

### Problem: WebSocket Connection Failed

**Symptoms**:

- Dashboard shows "Disconnected"
- Browser console: `WebSocket connection failed`

**Diagnosis**:

```bash
# Check if WebSocket server is running
lsof -i:7997

# Check if firewall is blocking
sudo iptables -L -n | grep 7997

# Test connection
curl http://localhost:7997/health
```

**Solutions**:

```bash
# Solution 1: Restart WebSocket server
systemctl restart agent-forge

# Solution 2: Check bind address
# Ensure bind is 0.0.0.0, not 127.0.0.1

# Solution 3: Allow through firewall
sudo ufw allow 7997/tcp
```

### Problem: LAN Access Not Working

**Symptoms**:

- Works on localhost
- Doesn't work from other devices on LAN

**Diagnosis**:

```bash
# Check bind address
netstat -tlnp | grep 8897

# Should show 0.0.0.0:8897, not 127.0.0.1:8897
```

**Solutions**:

```bash
# Ensure binding to all interfaces
python3 -m http.server 8897 --bind 0.0.0.0

# Check firewall
sudo ufw status
sudo ufw allow 8897/tcp
sudo ufw allow 7997/tcp

# Get your LAN IP
ip addr show | grep "inet "
# Or
hostname -I
```

---

## 📝 Port Usage Checklist

Before starting Agent-Forge:

- [ ] Verify port 8080 is available
- [ ] Verify port 7997 is available
- [ ] Verify port 8897 is available
- [ ] Check Ollama is running on 11434
- [ ] Ensure firewall allows ports (if LAN access needed)
- [ ] Verify no conflicting services

After starting:

- [ ] Verify Service Manager responds: `curl http://localhost:8080/health`
- [ ] Verify WebSocket server: `curl http://localhost:7997/health`
- [ ] Verify Frontend loads: Open `http://localhost:8897/dashboard.html`
- [ ] Check dashboard shows "Connected" status
- [ ] Verify Ollama: `curl http://localhost:11434/api/version`

---

## 🔗 Quick Commands Reference

```bash
# Check all Agent-Forge ports
lsof -i:8080,7997,8897,7996

# Kill all Agent-Forge services
lsof -ti:8080,7997,8897 | xargs kill -9

# Check firewall status
sudo ufw status | grep -E '8080|7997|8897'

# Allow all Agent-Forge ports
sudo ufw allow 8080/tcp
sudo ufw allow 7997/tcp
sudo ufw allow 8897/tcp

# Get LAN IP address
hostname -I | awk '{print $1}'

# Test WebSocket from command line
websocat ws://localhost:7997/ws/monitor

# Monitor port connections in real-time
watch -n 1 'lsof -i:7997 | tail -n +2'
```

---

## 📚 Related Documentation

- [ARCHITECTURE.md](../ARCHITECTURE.md) - Complete architecture guide
- [AGENT_ONBOARDING.md](AGENT_ONBOARDING.md) - Quick start guide
- [Architecture Diagram](diagrams/architecture-overview.md) - Visual port mapping

---

## 🐛 Troubleshooting Matrix

| Problem | Symptom | Solution |
|---------|---------|----------|
| Port in use | `Address already in use` | Kill process: `lsof -ti:PORT \| xargs kill -9` |
| WebSocket failed | Dashboard disconnected | Check port 7997, restart service |
| LAN access blocked | Works locally, not from LAN | Check bind address (`0.0.0.0`), check firewall |
| Ollama not found | Code generation fails | Start Ollama: `ollama serve` |
| Port confusion | Wrong port numbers | Use 8897 (not 8898) for frontend |
| Firewall blocking | Connection timeout | Allow ports: `sudo ufw allow PORT/tcp` |

---

**Last Updated**: 2025-10-06  
**Maintained by**: Agent-Forge Team  
**Questions?**: Create issue with label `documentation`
