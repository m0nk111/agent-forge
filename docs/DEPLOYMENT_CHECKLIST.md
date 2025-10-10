# Deployment Checklist

Pre-deployment checklist voor Agent-Forge updates.

## ✅ Voor Elke Deployment

### 1. Code Quality
- [ ] Alle tests passed: `pytest tests/ -v`
- [ ] Geen linting errors: `pylint agents/ api/`
- [ ] Type checking: `mypy agents/ api/` (optional)
- [ ] Code coverage > 70%: `pytest --cov=agents --cov-report=html`

### 2. Configuration
- [ ] `config/agents/*.yaml` updated (tokens removed)
- [ ] `config/repositories.yaml` configured
- [ ] `secrets/agents/*.token` files exist (0600 permissions)
- [ ] `.gitignore` blocks `secrets/` directory
- [ ] `requirements.txt` up-to-date

### 3. Documentation
- [ ] `CHANGELOG.md` updated with changes
- [ ] `README.md` reflects current features
- [ ] New features documented in `docs/`
- [ ] Architecture diagrams current
- [ ] API documentation updated

### 4. Security
- [ ] No tokens in git history: `git log --all -p | grep -i "ghp_"`
- [ ] Secrets directory permissions: `chmod 700 secrets/`
- [ ] Token files permissions: `chmod 600 secrets/agents/*.token`
- [ ] Auth service configured
- [ ] CORS origins updated in `api/auth_routes.py`

### 5. Services
- [ ] Systemd services updated: `systemd/*.service`
- [ ] Service files installed: `sudo cp systemd/*.service /etc/systemd/system/`
- [ ] Daemon reloaded: `sudo systemctl daemon-reload`
- [ ] Services enabled: `sudo systemctl enable agent-forge agent-forge-auth`
- [ ] Services started: `sudo systemctl start agent-forge agent-forge-auth`

### 6. Testing
- [ ] Auth service health: `curl http://localhost:7996/health`
- [ ] Config API health: `curl http://localhost:7998/api/config/health`
- [ ] Monitor WebSocket: `ws://localhost:7997/ws/monitor`
- [ ] Dashboard accessible: `http://YOUR_IP:8897/dashboard.html`
- [ ] Login flow works
- [ ] Agent status visible in dashboard
- [ ] Logs streaming correctly

### 7. Git
- [ ] All changes committed
- [ ] Commit message follows conventional commits
- [ ] CHANGELOG.md entry included in commit
- [ ] No sensitive data in commit
- [ ] Branch up-to-date with main
- [ ] Tests passed in CI/CD (if configured)

### 8. Deployment
- [ ] Services restarted: `sudo systemctl restart agent-forge agent-forge-auth`
- [ ] No errors in logs: `sudo journalctl -u agent-forge -n 50 --no-pager`
- [ ] Dashboard still accessible
- [ ] Agent operations working
- [ ] GitHub integration functional

## 🚨 Pre-Production Checklist

Additional checks voor production deployments:

### Security Hardening
- [ ] Session secret configured: `SESSION_SECRET` env var
- [ ] Token rotation policy documented
- [ ] Backup strategy for secrets/
- [ ] Firewall rules configured
- [ ] SSH keys configured for git operations
- [ ] User permissions reviewed

### Performance
- [ ] Resource limits configured in systemd
- [ ] Log rotation configured
- [ ] Disk space sufficient
- [ ] Memory limits appropriate
- [ ] CPU limits appropriate

### Monitoring
- [ ] Error alerting configured
- [ ] Performance metrics tracked
- [ ] Log aggregation setup
- [ ] Uptime monitoring active
- [ ] Backup verification automated

### Backup & Recovery
- [ ] Config files backed up
- [ ] Secrets backed up securely
- [ ] Database backup (if applicable)
- [ ] Rollback plan documented
- [ ] Recovery tested

## 📋 Post-Deployment Verification

Run these checks na deployment:

```bash
# 1. Service Status
sudo systemctl status agent-forge agent-forge-auth

# 2. Port Availability
ss -tlnp | grep ':7996\|:7997\|:7998\|:8897'

# 3. Auth Service
curl http://localhost:7996/health

# 4. Config API
curl http://localhost:7998/api/config/health

# 5. Dashboard Access
curl -I http://localhost:8897/dashboard.html

# 6. Monitor Logs (5 min)
sudo journalctl -u agent-forge -f --no-pager &
sudo journalctl -u agent-forge-auth -f --no-pager &

# Wait 5 minutes, check for errors
```

### Expected Results
- ✅ All services: `active (running)`
- ✅ All ports listening
- ✅ Health checks return 200 OK
- ✅ Dashboard returns 200 OK
- ✅ No errors in logs
- ✅ Auth redirects to login
- ✅ Login flow works
- ✅ Agents visible in dashboard

## 🔧 Rollback Procedure

### When to Rollback
- Critical bugs discovered within 1 hour of deployment
- Services fail to start after deployment
- Data corruption detected
- Security vulnerability introduced
- Performance degradation > 50%

### Rollback Steps

```bash
# 1. Stop all services immediately
sudo systemctl stop agent-forge agent-forge-auth agent-forge-monitor

# 2. Verify services stopped
sudo systemctl status agent-forge agent-forge-auth agent-forge-monitor

# 3. Backup current state (in case rollback fails)
BACKUP_DIR="/tmp/agent-forge-rollback-$(date +%Y%m%d-%H%M%S)"
mkdir -p $BACKUP_DIR
cp -r config/ $BACKUP_DIR/
cp -r secrets/ $BACKUP_DIR/
cp -r agents/ $BACKUP_DIR/
echo "Backup created: $BACKUP_DIR"

# 4. Identify previous working commit
git log --oneline -10  # Find last known good commit
PREVIOUS_COMMIT="abc1234"  # Replace with actual commit hash

# 5. Rollback code
git checkout $PREVIOUS_COMMIT

# 6. Restore previous configuration (if needed)
# Only restore config if new deployment changed it
# git checkout $PREVIOUS_COMMIT -- config/

# 7. Reinstall systemd services
sudo cp systemd/*.service /etc/systemd/system/
sudo systemctl daemon-reload

# 8. Restart services
sudo systemctl start agent-forge-auth  # Auth first
sleep 2
sudo systemctl start agent-forge       # Main service
sleep 2
sudo systemctl start agent-forge-monitor  # Monitor last

# 9. Verify rollback success
curl -f http://localhost:7996/health || echo "❌ Auth service failed"
curl -f http://localhost:7998/api/config/health || echo "❌ Config API failed"
curl -f http://localhost:7997/health || echo "❌ Monitor service failed"
curl -I http://localhost:8897/dashboard.html || echo "❌ Dashboard failed"

# 10. Check logs for errors
sudo journalctl -u agent-forge -n 50 --no-pager
sudo journalctl -u agent-forge-auth -n 50 --no-pager

# 11. Test critical functionality
# - Login to dashboard
# - Check agent status
# - Verify GitHub connectivity
# - Test issue handling (if safe)

# 12. Document rollback
echo "## Rollback $(date)" >> docs/DEPLOYMENT_HISTORY.md
echo "- From commit: $(git rev-parse HEAD)" >> docs/DEPLOYMENT_HISTORY.md
echo "- To commit: $PREVIOUS_COMMIT" >> docs/DEPLOYMENT_HISTORY.md
echo "- Reason: [FILL IN]" >> docs/DEPLOYMENT_HISTORY.md
echo "- Backup: $BACKUP_DIR" >> docs/DEPLOYMENT_HISTORY.md
```

### Rollback Verification Checklist
- [ ] All services running: `systemctl status agent-forge*`
- [ ] No errors in logs (last 100 lines)
- [ ] Dashboard accessible and functional
- [ ] Login flow works
- [ ] Agents visible and responding
- [ ] GitHub API connectivity confirmed
- [ ] No data loss verified
- [ ] Previous functionality restored

### If Rollback Fails
1. Check service logs: `sudo journalctl -u agent-forge -n 200 --no-pager`
2. Verify configuration files not corrupted
3. Check disk space: `df -h`
4. Check permissions: `ls -la config/ secrets/`
5. Try clean restart: `sudo systemctl restart agent-forge*`
6. Check for port conflicts: `ss -tlnp | grep ':7996\|:7997\|:7998\|:8897'`
7. Review recent commits: `git log --oneline -20`
8. Consider restoring from backup: `cp -r $BACKUP_DIR/* .`

## 🚨 Emergency Procedures

### Database Corruption
```bash
# 1. Stop service
sudo systemctl stop agent-forge

# 2. Backup corrupted database
cp data/agent_forge.db data/agent_forge.db.corrupted.$(date +%Y%m%d-%H%M%S)

# 3. Restore from backup
cp backups/latest/agent_forge.db data/

# 4. Verify database integrity
sqlite3 data/agent_forge.db "PRAGMA integrity_check;"

# 5. Restart service
sudo systemctl start agent-forge
```

### Disk Full
```bash
# 1. Check disk usage
df -h
du -sh /var/log/* | sort -h

# 2. Clean old logs
sudo journalctl --vacuum-time=7d
sudo find /var/log -name "*.log.gz" -mtime +30 -delete

# 3. Clean Python cache
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type f -name "*.pyc" -delete

# 4. Clean old backups
find backups/ -name "*.tar.gz" -mtime +30 -delete

# 5. Verify space freed
df -h

# 6. Restart services
sudo systemctl restart agent-forge
```

### Service Won't Start
```bash
# 1. Check service status
sudo systemctl status agent-forge

# 2. Check detailed logs
sudo journalctl -u agent-forge -n 200 --no-pager

# 3. Check for port conflicts
ss -tlnp | grep ':7996\|:7997\|:7998\|:8897'

# 4. Kill conflicting processes
sudo lsof -ti:7997 | xargs sudo kill -9

# 5. Check configuration
for config in config/agents/*.yaml; do
  python3 -c "import yaml; yaml.safe_load(open('$config'))"
done

# 6. Check permissions
ls -la config/ secrets/
sudo chown -R agent-forge:agent-forge /opt/agent-forge

# 7. Try manual start (debugging)
cd /opt/agent-forge
source venv/bin/activate
python3 agents/service_manager.py

# 8. Check dependencies
pip3 list | grep -E "flask|pyyaml|requests|anthropic|ollama"

# 9. Reinstall if needed
pip3 install -r requirements.txt

# 10. Restart systemd
sudo systemctl daemon-reload
sudo systemctl restart agent-forge
```

### Agent Stuck/Unresponsive
```bash
# 1. Check agent status via API
curl http://localhost:7998/api/agents/status

# 2. Check WebSocket connection
wscat -c ws://localhost:7997/ws/monitor

# 3. Check Ollama availability
curl http://localhost:11434/api/tags

# 4. Check GitHub API connectivity
curl -H "Authorization: token $(cat secrets/agents/bot.token)" \
  https://api.github.com/rate_limit

# 5. Force agent restart via API
curl -X POST http://localhost:7998/api/agents/bot/restart

# 6. If API unresponsive, restart service
sudo systemctl restart agent-forge

# 7. Check for deadlocks in logs
sudo journalctl -u agent-forge | grep -i "deadlock\|timeout\|hung"

# 8. Check resource usage
top -b -n 1 | grep python3
ps aux | grep agent-forge

# 9. Kill hung processes if needed
pkill -9 -f "agent-forge"
sudo systemctl restart agent-forge
```

### GitHub API Rate Limited
```bash
# 1. Check rate limit status
curl -H "Authorization: token $(cat secrets/agents/bot.token)" \
  https://api.github.com/rate_limit

# 2. Wait until reset time (shown in response)

# 3. Meanwhile, pause polling service
curl -X POST http://localhost:7998/api/services/polling/pause

# 4. Reduce polling frequency temporarily
# Edit config/services/polling.yaml:
# check_interval_seconds: 300  # 5 minutes instead of 60

# 5. Restart to apply changes
sudo systemctl restart agent-forge

# 6. Resume when rate limit resets
curl -X POST http://localhost:7998/api/services/polling/resume
```

## 📊 Monitoring After Deployment

### First Hour
Monitor these metrics every 5-10 minutes:

```bash
# Service health
watch -n 10 'curl -s http://localhost:7996/health && curl -s http://localhost:7997/health'

# CPU and memory
watch -n 10 'ps aux | grep -E "agent-forge|python3" | grep -v grep'

# Error logs
sudo journalctl -u agent-forge -f --no-pager | grep -i error

# GitHub API usage
watch -n 60 'curl -s -H "Authorization: token $(cat secrets/agents/bot.token)" \
  https://api.github.com/rate_limit | jq ".rate"'
```

**Red flags in first hour:**
- Memory usage > 1GB per agent
- CPU consistently > 80%
- Error rate > 5% in logs
- GitHub API calls > 4000/hour
- Service restarts > 2
- Response times > 5 seconds

### First Day
Check these metrics hourly:

- Service uptime: `systemctl status agent-forge`
- Completed tasks: Check dashboard
- Error count: `sudo journalctl -u agent-forge --since "1 hour ago" | grep -c ERROR`
- Disk space: `df -h`
- Database size: `du -sh data/agent_forge.db`
- Log size: `du -sh /var/log/agent-forge/`

**Red flags in first day:**
- Task completion rate < 80%
- Database growth > 100MB/day
- Log growth > 1GB/day
- Disk usage > 80%
- Memory leaks (steadily increasing)
- Repeated errors in logs

### First Week
Daily checks:

1. **Performance trends**: Are response times degrading?
2. **Resource usage**: Is memory/CPU usage stable?
3. **Error patterns**: Any recurring errors?
4. **GitHub usage**: Within API limits?
5. **Storage growth**: Sustainable rate?

**Rollback triggers after week:**
- Critical bug affecting > 50% of tasks
- Data loss incidents
- Security vulnerabilities
- Unfixable performance issues

## 🤖 Deployment Automation

### Automated Deployment Script

Create `scripts/automated-deploy.sh`:

```bash
#!/bin/bash
set -euo pipefail

# Configuration
REPO_DIR="/opt/agent-forge"
BACKUP_DIR="/opt/agent-forge-backups"
LOG_FILE="/var/log/agent-forge/deployment.log"
ROLLBACK_ON_FAILURE=true

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}" | tee -a "$LOG_FILE"
}

success() {
    echo -e "${GREEN}[SUCCESS] $1${NC}" | tee -a "$LOG_FILE"
}

warn() {
    echo -e "${YELLOW}[WARNING] $1${NC}" | tee -a "$LOG_FILE"
}

rollback() {
    error "Deployment failed. Rolling back..."
    cd "$REPO_DIR"
    git checkout "$PREVIOUS_COMMIT"
    sudo systemctl restart agent-forge agent-forge-auth
    error "Rolled back to commit $PREVIOUS_COMMIT"
    exit 1
}

# Trap errors for automatic rollback
if [ "$ROLLBACK_ON_FAILURE" = true ]; then
    trap rollback ERR
fi

log "========== Starting Deployment =========="

# 1. Pre-deployment backup
log "Creating backup..."
BACKUP_NAME="backup-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_DIR/$BACKUP_NAME"
cp -r "$REPO_DIR/config" "$BACKUP_DIR/$BACKUP_NAME/"
cp -r "$REPO_DIR/data" "$BACKUP_DIR/$BACKUP_NAME/" 2>/dev/null || true
cp -r "$REPO_DIR/secrets" "$BACKUP_DIR/$BACKUP_NAME/"
PREVIOUS_COMMIT=$(git -C "$REPO_DIR" rev-parse HEAD)
echo "$PREVIOUS_COMMIT" > "$BACKUP_DIR/$BACKUP_NAME/commit.txt"
success "Backup created: $BACKUP_NAME"

# 2. Pull latest changes
log "Pulling latest changes..."
cd "$REPO_DIR"
git pull origin main
success "Code updated"

# 3. Update dependencies
log "Updating dependencies..."
source venv/bin/activate
pip install -r requirements.txt --quiet
success "Dependencies updated"

# 4. Run tests
log "Running tests..."
pytest tests/ -v --tb=short || {
    error "Tests failed"
    [ "$ROLLBACK_ON_FAILURE" = true ] && rollback
}
success "All tests passed"

# 5. Update systemd services
log "Updating systemd services..."
sudo cp systemd/*.service /etc/systemd/system/
sudo systemctl daemon-reload
success "Systemd services updated"

# 6. Restart services with health checks
log "Restarting services..."
sudo systemctl restart agent-forge-auth
sleep 3
curl -f http://localhost:7996/health || {
    error "Auth service health check failed"
    [ "$ROLLBACK_ON_FAILURE" = true ] && rollback
}

sudo systemctl restart agent-forge
sleep 5
curl -f http://localhost:7998/api/config/health || {
    error "Main service health check failed"
    [ "$ROLLBACK_ON_FAILURE" = true ] && rollback
}

success "Services restarted successfully"

# 7. Post-deployment verification
log "Running post-deployment checks..."

# Check all services running
systemctl is-active --quiet agent-forge || error "agent-forge not running"
systemctl is-active --quiet agent-forge-auth || error "agent-forge-auth not running"

# Check dashboard accessible
curl -sf -I http://localhost:8897/dashboard.html > /dev/null || warn "Dashboard not accessible"

# Check logs for errors
ERROR_COUNT=$(sudo journalctl -u agent-forge --since "1 minute ago" | grep -c ERROR || true)
if [ "$ERROR_COUNT" -gt 5 ]; then
    error "Too many errors in logs: $ERROR_COUNT"
    [ "$ROLLBACK_ON_FAILURE" = true ] && rollback
fi

success "Post-deployment checks passed"

# 8. Summary
log "========== Deployment Complete =========="
log "Previous commit: $PREVIOUS_COMMIT"
log "Current commit: $(git rev-parse HEAD)"
log "Backup location: $BACKUP_DIR/$BACKUP_NAME"
log "Services status:"
systemctl status agent-forge --no-pager -l || true
log "Dashboard: http://$(hostname -I | cut -d' ' -f1):8897/dashboard.html"

success "🎉 Deployment successful!"
```

Make executable: `chmod +x scripts/automated-deploy.sh`

### Scheduled Deployments (Cron)

For automated nightly deployments:

```bash
# Edit crontab
sudo crontab -e

# Add line for 2 AM deployments:
0 2 * * * /opt/agent-forge/scripts/automated-deploy.sh >> /var/log/agent-forge/auto-deploy.log 2>&1
```

### CI/CD Integration

Example GitHub Actions workflow (`.github/workflows/deploy.yml`):

```yaml
name: Deploy to Production

on:
  push:
    branches: [ main ]
  workflow_dispatch:

jobs:
  deploy:
    runs-on: self-hosted
    steps:
      - name: Checkout code
        uses: actions/checkout@v3
      
      - name: Run deployment script
        run: |
          cd /opt/agent-forge
          sudo -u agent-forge ./scripts/automated-deploy.sh
      
      - name: Notify on failure
        if: failure()
        run: |
          curl -X POST https://your-notification-service.com/alert \
            -d "Deployment failed for commit ${{ github.sha }}"
```

## 📝 Deployment Notes Template

```markdown
## Deployment YYYY-MM-DD HH:MM

### Changes
- Feature/fix 1
- Feature/fix 2
- ...

### Commits
- abc1234: feat(feature): description
- def5678: fix(bug): description

### Tests
- ✅ All tests passed
- ✅ Manual testing completed
- ✅ Dashboard accessible
- ✅ Auth working

### Issues
- None

### Rollback
- Previous commit: abc1234
- Rollback tested: Yes/No
```

## 🎯 Quick Deployment Script

```bash
#!/bin/bash
# quick-deploy.sh - Run all deployment checks

echo "🔍 Running deployment checks..."

# Tests
echo "1️⃣ Running tests..."
pytest tests/ -v || exit 1

# Security check
echo "2️⃣ Checking for secrets in git..."
if git log --all -p | grep -qi "ghp_"; then
    echo "❌ Found potential secrets in git history!"
    exit 1
fi

# Update services
echo "3️⃣ Updating systemd services..."
sudo cp systemd/*.service /etc/systemd/system/
sudo systemctl daemon-reload

# Restart services
echo "4️⃣ Restarting services..."
sudo systemctl restart agent-forge agent-forge-auth

# Wait for services
echo "5️⃣ Waiting for services to start..."
sleep 5

# Verify
echo "6️⃣ Verifying services..."
systemctl is-active --quiet agent-forge || echo "❌ agent-forge not running"
systemctl is-active --quiet agent-forge-auth || echo "❌ agent-forge-auth not running"

# Health checks
echo "7️⃣ Health checks..."
curl -sf http://localhost:7996/health > /dev/null || echo "❌ Auth service unhealthy"
curl -sf http://localhost:7998/api/config/health > /dev/null || echo "❌ Config API unhealthy"

echo "✅ Deployment complete!"
echo "📊 Check dashboard: http://$(hostname -I | cut -d' ' -f1):8897/dashboard.html"
```

Maak executable: `chmod +x scripts/quick-deploy.sh`
