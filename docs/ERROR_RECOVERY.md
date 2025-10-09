# Error Recovery & Resilience Strategy

> **Purpose**: Define how Agent-Forge handles failures, retries operations, and maintains system health during adverse conditions.

**Last Updated**: 2025-10-09

---

## 🎯 Overview

Agent-Forge uses a **layered resilience strategy** to handle failures gracefully:
1. **Retry with exponential backoff** for transient failures
2. **Circuit breakers** for external service protection
3. **Health checks** for proactive failure detection
4. **Graceful degradation** when services are unavailable

---

## 🔄 Retry Policies

### GitHub API Operations

**Strategy**: Exponential backoff with jitter

```python
MAX_RETRIES = 3
BASE_DELAY = 2  # seconds
MAX_DELAY = 60  # seconds

def retry_github_api(operation, *args, **kwargs):
    """Retry GitHub API calls with exponential backoff"""
    for attempt in range(MAX_RETRIES):
        try:
            return operation(*args, **kwargs)
        except requests.HTTPError as e:
            if e.response.status_code == 403:
                # Rate limit - check reset time
                reset_time = int(e.response.headers.get('X-RateLimit-Reset', 0))
                wait = max(reset_time - time.time(), 0)
                logger.warning(f"⚠️ Rate limited. Waiting {wait}s until reset")
                time.sleep(wait)
            elif e.response.status_code in [500, 502, 503, 504]:
                # Server error - retry with backoff
                delay = min(BASE_DELAY * (2 ** attempt) + random.uniform(0, 1), MAX_DELAY)
                logger.warning(f"⚠️ GitHub API error {e.response.status_code}. Retry {attempt+1}/{MAX_RETRIES} in {delay:.1f}s")
                time.sleep(delay)
            else:
                # Client error - don't retry
                raise
    
    raise Exception(f"Failed after {MAX_RETRIES} retries")
```

**Retry Conditions**:
- ✅ `403 Rate Limit` - Wait until reset time
- ✅ `500, 502, 503, 504` - Server errors (exponential backoff)
- ✅ `Connection timeout` - Network issues (exponential backoff)
- ❌ `401, 404, 422` - Client errors (no retry)

### Ollama LLM Inference

**Strategy**: Retry with health check

```python
OLLAMA_MAX_RETRIES = 2
OLLAMA_TIMEOUT = 300  # 5 minutes

def retry_ollama_generate(prompt, model="qwen2.5-coder:7b"):
    """Retry Ollama generation with health check"""
    for attempt in range(OLLAMA_MAX_RETRIES):
        try:
            # Health check first
            health = requests.get("http://localhost:11434/api/version", timeout=5)
            if health.status_code != 200:
                raise Exception(f"Ollama unhealthy: {health.status_code}")
            
            # Generate
            response = requests.post(
                "http://localhost:11434/api/chat",
                json={"model": model, "messages": [{"role": "user", "content": prompt}]},
                timeout=OLLAMA_TIMEOUT
            )
            response.raise_for_status()
            return response.json()["message"]["content"]
            
        except (requests.Timeout, requests.ConnectionError) as e:
            logger.warning(f"⚠️ Ollama connection failed: {e}. Retry {attempt+1}/{OLLAMA_MAX_RETRIES}")
            time.sleep(5)  # Wait for Ollama to restart
    
    raise Exception("Ollama unavailable after retries")
```

**Retry Conditions**:
- ✅ `Connection refused` - Ollama not running (retry after 5s)
- ✅ `Timeout` - Long generation (retry with same prompt)
- ❌ `Invalid model` - Model not available (no retry, log error)

### Database Operations

**Strategy**: Retry with lock timeout increase

```python
DB_MAX_RETRIES = 5
DB_BASE_TIMEOUT = 5  # seconds

def retry_db_operation(operation, *args, **kwargs):
    """Retry database operations with increasing timeout"""
    for attempt in range(DB_MAX_RETRIES):
        try:
            timeout = DB_BASE_TIMEOUT * (attempt + 1)
            conn = sqlite3.connect('data/agent-forge.db', timeout=timeout)
            conn.execute('PRAGMA journal_mode=WAL')  # Enable WAL mode
            return operation(conn, *args, **kwargs)
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e):
                logger.warning(f"⚠️ Database locked. Retry {attempt+1}/{DB_MAX_RETRIES}")
                time.sleep(1)
            else:
                raise
        finally:
            if 'conn' in locals():
                conn.close()
    
    raise Exception("Database locked after retries")
```

**Retry Conditions**:
- ✅ `Database locked` - Concurrent access (increase timeout)
- ✅ `Disk I/O error` - Transient disk issues (retry)
- ❌ `Corrupt database` - Data integrity (no retry, restore backup)

---

## 🔌 Circuit Breakers

### Pattern

Circuit breaker prevents cascading failures by **failing fast** when external service is down.

**States**:
- **CLOSED** (normal): Requests pass through
- **OPEN** (failed): Requests fail immediately (no external call)
- **HALF_OPEN** (testing): Single test request to check recovery

```python
from enum import Enum
import time

class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class CircuitBreaker:
    def __init__(self, failure_threshold=5, timeout=60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
    
    def call(self, func, *args, **kwargs):
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time > self.timeout:
                logger.info("🔧 Circuit breaker entering HALF_OPEN state")
                self.state = CircuitState.HALF_OPEN
            else:
                raise Exception(f"Circuit breaker OPEN. Retry after {self.timeout}s")
        
        try:
            result = func(*args, **kwargs)
            if self.state == CircuitState.HALF_OPEN:
                logger.info("✅ Circuit breaker recovered. Entering CLOSED state")
                self.state = CircuitState.CLOSED
                self.failure_count = 0
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.failure_threshold:
                logger.error(f"❌ Circuit breaker OPEN after {self.failure_count} failures")
                self.state = CircuitState.OPEN
            
            raise

# Usage
github_circuit = CircuitBreaker(failure_threshold=5, timeout=60)
ollama_circuit = CircuitBreaker(failure_threshold=3, timeout=30)

def safe_github_call(operation, *args, **kwargs):
    return github_circuit.call(retry_github_api, operation, *args, **kwargs)
```

### Configuration

| Service | Failure Threshold | Timeout | Rationale |
|---------|-------------------|---------|-----------|
| **GitHub API** | 5 failures | 60s | Transient network issues |
| **Ollama** | 3 failures | 30s | May need restart |
| **Database** | 10 failures | 120s | WAL mode reduces locks |

---

## 🏥 Health Checks

### Agent Health Check

Agents report health every **60 seconds** via heartbeat.

```python
def agent_health_check(agent_id):
    """Check if agent is healthy"""
    agent = get_agent_status(agent_id)
    
    # Unhealthy conditions
    if agent.status == "working" and agent.last_update < time.time() - 1800:
        # Working for 30+ min without update
        logger.error(f"❌ Agent {agent_id} stuck. No update for 30 min")
        return False, "Stuck - no progress update"
    
    if agent.error_message and agent.error_count > 3:
        # Multiple consecutive errors
        logger.error(f"❌ Agent {agent_id} failing. {agent.error_count} consecutive errors")
        return False, f"Error loop: {agent.error_message}"
    
    if agent.status == "offline":
        logger.warning(f"⚠️ Agent {agent_id} offline")
        return False, "Offline"
    
    return True, "Healthy"
```

**Auto-Recovery Actions**:
- **Stuck agent** (no progress > 30 min): Send SIGINT, wait 10s, SIGKILL if needed
- **Error loop** (>3 consecutive errors): Stop agent, log full context, alert admin
- **Offline agent** (expected to be always-on): Attempt restart via systemd

### Service Health Check

Services expose `/health` endpoint.

```python
@app.route('/health')
def health_check():
    """Service health check"""
    checks = {
        'ollama': check_ollama_health(),
        'github': check_github_health(),
        'database': check_database_health(),
        'disk_space': check_disk_space()
    }
    
    all_healthy = all(c['healthy'] for c in checks.values())
    status_code = 200 if all_healthy else 503
    
    return jsonify({
        'status': 'healthy' if all_healthy else 'degraded',
        'checks': checks,
        'timestamp': time.time()
    }), status_code

def check_ollama_health():
    try:
        r = requests.get('http://localhost:11434/api/version', timeout=5)
        return {'healthy': r.status_code == 200, 'latency_ms': r.elapsed.total_seconds() * 1000}
    except:
        return {'healthy': False, 'error': 'Connection failed'}
```

**Health Check Frequency**:
- **External monitoring** (Nagios, Prometheus): Every 60s
- **Internal monitoring** (agent watchdog): Every 30s
- **Load balancer** (if deployed): Every 10s

---

## 🎭 Graceful Degradation

### Scenario 1: Ollama Unavailable

**Impact**: Code generation unavailable  
**Degradation Strategy**:

1. **Detect**: Circuit breaker opens after 3 failures
2. **Fallback**: Use template-based generation (no LLM)
3. **Communicate**: Update agent status to "degraded - LLM unavailable"
4. **Queue**: Store tasks for later execution
5. **Recover**: Retry Ollama connection every 60s

```python
def generate_code_with_fallback(prompt):
    try:
        return ollama_circuit.call(ollama_generate, prompt)
    except:
        logger.warning("⚠️ Ollama unavailable. Using template fallback")
        return generate_from_template(prompt)  # Simple templates
```

### Scenario 2: GitHub API Rate Limited

**Impact**: Cannot create PRs, issues, comments  
**Degradation Strategy**:

1. **Detect**: 403 with `X-RateLimit-Remaining: 0`
2. **Calculate**: Time until rate limit reset
3. **Queue**: Store operations in local queue
4. **Schedule**: Execute queue after reset time
5. **Notify**: Dashboard shows "rate limited - resuming at HH:MM"

```python
def handle_rate_limit(response):
    reset_time = int(response.headers.get('X-RateLimit-Reset', 0))
    wait_seconds = max(reset_time - time.time(), 0)
    
    logger.warning(f"⚠️ GitHub rate limited. Reset in {wait_seconds//60} min")
    
    # Queue operation for later
    operation_queue.append({
        'operation': current_operation,
        'retry_after': reset_time
    })
    
    # Update dashboard
    broadcast_status({
        'type': 'rate_limit',
        'message': f'Rate limited. Resuming at {time.strftime("%H:%M", time.localtime(reset_time))}'
    })
```

### Scenario 3: Database Locked

**Impact**: Cannot save agent state  
**Degradation Strategy**:

1. **Detect**: `sqlite3.OperationalError: database is locked`
2. **Retry**: Increase timeout with each retry (5s → 10s → 15s → 20s → 25s)
3. **WAL Mode**: Enable Write-Ahead Logging (reduces locks)
4. **Fallback**: Store state in memory temporarily
5. **Persist**: Flush to database when lock clears

### Scenario 4: Disk Full

**Impact**: Cannot write files, logs, database  
**Degradation Strategy**:

1. **Detect**: `OSError: [Errno 28] No space left on device`
2. **Alert**: Send critical alert (email, Slack, PagerDuty)
3. **Cleanup**: Delete old logs, temp files, backups (keep last 7 days)
4. **Pause**: Stop accepting new tasks until space available
5. **Readonly**: Continue read operations (status checks, monitoring)

```python
def check_disk_space():
    """Check available disk space"""
    stat = os.statvfs('/home/flip/agent-forge')
    free_gb = (stat.f_bavail * stat.f_frsize) / (1024**3)
    
    if free_gb < 1:
        logger.critical(f"🚨 CRITICAL: Only {free_gb:.1f}GB free. Cleanup required!")
        cleanup_old_files()
        pause_task_acceptance()
        return False
    elif free_gb < 5:
        logger.warning(f"⚠️ Low disk space: {free_gb:.1f}GB free")
        return True
    
    return True
```

---

## 🚨 Alert Thresholds

| Condition | Severity | Action | Alert Channel |
|-----------|----------|--------|---------------|
| Agent stuck > 30 min | **CRITICAL** | Auto-restart | Email + Slack |
| Ollama down > 5 min | **HIGH** | Manual restart | Slack |
| GitHub rate limited | **MEDIUM** | Queue operations | Dashboard |
| Database locked > 30s | **MEDIUM** | Increase timeout | Log |
| Disk < 1GB free | **CRITICAL** | Cleanup + pause | Email + SMS |
| Disk < 5GB free | **MEDIUM** | Cleanup | Dashboard |
| Error rate > 10% | **HIGH** | Investigate | Slack |
| Response time > 10s | **MEDIUM** | Performance review | Dashboard |

---

## 🔧 Recovery Procedures

### Agent Stuck Recovery

```bash
# 1. Identify stuck agent
curl http://localhost:7997/api/agents | jq '.agents[] | select(.status=="working" and .last_update < (now - 1800))'

# 2. Check agent logs
curl http://localhost:7997/api/agents/AGENT_ID/logs?limit=50

# 3. Attempt graceful stop
curl -X POST http://localhost:8080/agents/AGENT_ID/stop

# 4. Wait 10 seconds
sleep 10

# 5. Force kill if needed
pkill -9 -f "agent_id=AGENT_ID"

# 6. Restart agent
curl -X POST http://localhost:8080/agents/AGENT_ID/start

# 7. Monitor recovery
watch -n 5 'curl -s http://localhost:7997/api/agents/AGENT_ID/status | jq'
```

### Ollama Restart Recovery

```bash
# 1. Check Ollama status
systemctl status ollama

# 2. Restart Ollama
sudo systemctl restart ollama

# 3. Verify models loaded
ollama list

# 4. Test inference
ollama run qwen2.5-coder:7b "Write hello world"

# 5. Reset circuit breaker (if implemented)
curl -X POST http://localhost:8080/admin/circuit-breaker/ollama/reset
```

### Database Recovery

```bash
# 1. Check database integrity
sqlite3 data/agent-forge.db "PRAGMA integrity_check"

# 2. If corrupt, restore from backup
cp data/backups/agent-forge-$(date +%Y%m%d).db.gz /tmp/
gunzip /tmp/agent-forge-*.db.gz
mv data/agent-forge.db data/agent-forge.db.corrupt
mv /tmp/agent-forge-*.db data/agent-forge.db

# 3. Verify restoration
sqlite3 data/agent-forge.db "SELECT COUNT(*) FROM agents"

# 4. Restart service
sudo systemctl restart agent-forge
```

---

## 📚 Related Documentation

- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Common issues and solutions
- [MONITORING_API.md](MONITORING_API.md) - Health check endpoints
- [DEPLOYMENT.md](DEPLOYMENT.md) - Production deployment guide
- [ARCHITECTURE.md](../ARCHITECTURE.md) - System architecture

---

**Maintained by**: Agent Forge Operations Team  
**Questions?**: Create issue with label `operations`
