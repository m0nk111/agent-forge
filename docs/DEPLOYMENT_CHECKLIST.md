# Deployment Checklist

Pre-deployment checklist voor Agent-Forge updates.

## ✅ Voor Elke Deployment

### 1. Code Quality
- [ ] Alle tests passed: `pytest tests/ -v`
- [ ] Geen linting errors: `pylint agents/ api/`
- [ ] Type checking: `mypy agents/ api/` (optional)
- [ ] Code coverage > 70%: `pytest --cov=agents --cov-report=html`

### 2. Configuration
- [ ] `config/agents.yaml` updated (tokens removed)
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

If issues detected:

```bash
# 1. Stop services
sudo systemctl stop agent-forge agent-forge-auth

# 2. Rollback git
git log --oneline -5  # Find previous commit
git checkout PREVIOUS_COMMIT_HASH

# 3. Reinstall services
sudo cp systemd/*.service /etc/systemd/system/
sudo systemctl daemon-reload

# 4. Restart services
sudo systemctl start agent-forge agent-forge-auth

# 5. Verify
curl http://localhost:7996/health
curl http://localhost:8897/dashboard.html

# 6. Check logs
sudo journalctl -u agent-forge -n 50 --no-pager
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
