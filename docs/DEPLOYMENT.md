# Deployment Guide 🚀

Complete guide for deploying Agent-Forge in development and production environments.

> **⚠️ Important Path Changes (October 2025)**  
> The project structure has been refactored:
> - All Python modules are now in `engine/` (not `agents/`)
> - Configurations are hierarchically organized in `config/`
> - Secrets are stored in `secrets/agents/` with proper permissions
> - Service command: `python3 -m engine.core.service_manager`
>
> See [ARCHITECTURE.md](../ARCHITECTURE.md) for full directory structure.

---

## 📋 Table of Contents

- [Deployment Options](#deployment-options)
- [Prerequisites](#prerequisites)
- [Local Development](#local-development)
- [Production Deployment](#production-deployment)
- [Docker Deployment](#docker-deployment)
- [Systemd Service](#systemd-service)
- [Nginx Reverse Proxy](#nginx-reverse-proxy)
- [Environment Configuration](#environment-configuration)
- [Security Hardening](#security-hardening)
- [Monitoring Setup](#monitoring-setup)
- [Backup Strategy](#backup-strategy)
- [Troubleshooting](#troubleshooting)

---

## 🎯 Deployment Options

### Development (Local)

**Best for**: Local development, testing, prototyping

**Pros**:
- Quick setup
- Easy debugging
- No additional infrastructure

**Cons**:
- Not suitable for production
- No auto-restart on crashes
- Manual process management

### Systemd Service (Production)

**Best for**: Production Linux servers, VPS, dedicated machines

**Pros**:
- Automatic startup on boot
- Process monitoring and restart
- Systemd integration (logging, watchdog)
- Resource limits

**Cons**:
- Requires Linux with systemd
- Root access needed for setup

### Docker (Future)

**Best for**: Container-based deployments, cloud platforms

**Pros**:
- Consistent environment
- Easy scaling
- Portable across platforms
- Isolation

**Cons**:
- Not yet implemented
- Additional complexity

---

## 📦 Prerequisites

### System Requirements

**Minimum**:
- CPU: 2 cores
- RAM: 4 GB
- Disk: 20 GB free space
- OS: Ubuntu 20.04+ / Debian 11+

**Recommended**:
- CPU: 4+ cores
- RAM: 8+ GB
- Disk: 50 GB SSD
- OS: Ubuntu 24.04 LTS

### Software Requirements

```bash
# Python 3.12+
python3 --version

# Git
git --version

# Ollama (for local LLM)
ollama --version

# Optional: systemd (for service deployment)
systemctl --version

# Optional: nginx (for reverse proxy)
nginx -v
```

### Network Requirements

**Ports**:
- `8080`: Service Manager API
- `7997`: WebSocket monitoring
- `8897`: Frontend dashboard
- `11434`: Ollama (local only)

**Firewall Rules** (if deploying on server):

```bash
# Ubuntu/Debian
sudo ufw allow 8080/tcp
sudo ufw allow 7997/tcp
sudo ufw allow 8897/tcp

# Or allow specific IP range
sudo ufw allow from 192.168.1.0/24 to any port 8080
```

---

## 💻 Local Development

### Quick Start

1. **Clone Repository**:

```bash
git clone https://github.com/m0nk111/agent-forge.git
cd agent-forge
```

2. **Create Virtual Environment**:

```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows
```

3. **Install Dependencies**:

```bash
pip install -r requirements.txt
```

4. **Configure Environment**:

```bash
# Copy example config
cp config/agents.yaml.example config/agents.yaml
cp .env.example .env

# Edit .env with your tokens
nano .env
```

5. **Pull Ollama Model**:

```bash
# Ensure Ollama is running
ollama serve &

# Pull model
ollama pull qwen2.5-coder:7b
```

6. **Initialize Database** (if needed):

```bash
python -m agents.init_db
```

7. **Start Service**:

```bash
# Start service manager
python -m agents.service_manager

# Or with custom ports
python -m agents.service_manager \
    --service-port 8080 \
    --monitor-port 7997 \
    --web-port 8897
```

8. **Access Dashboard**:

```
http://localhost:8897/dashboard.html
```

### Development Mode

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Start with auto-reload (using nodemon or watchdog)
watchmedo auto-restart \
    --directory=./agents \
    --pattern="*.py" \
    --recursive \
    -- python -m agents.service_manager
```

---

## 🏭 Production Deployment

### 1. Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3.12 python3.12-venv python3-pip git

# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Enable Ollama service
sudo systemctl enable ollama
sudo systemctl start ollama

# Pull models
ollama pull qwen2.5-coder:7b
```

### 2. Create Dedicated User

```bash
# Create agent-forge user
sudo useradd -r -s /bin/bash -d /opt/agent-forge agent-forge

# Create home directory
sudo mkdir -p /opt/agent-forge
sudo chown agent-forge:agent-forge /opt/agent-forge
```

### 3. Deploy Application

```bash
# Switch to agent-forge user
sudo su - agent-forge

# Clone repository
cd /opt/agent-forge
git clone https://github.com/m0nk111/agent-forge.git .

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create directories
mkdir -p logs data config

# Copy configuration
cp config/agents.yaml.example config/agents.yaml
cp .env.example .env

# Edit configuration
nano .env
nano config/agents.yaml
```

### 4. Configure Environment

```bash
# /opt/agent-forge/.env
GITHUB_TOKEN=ghp_your_token_here
GITHUB_BOT_TOKEN=ghp_bot_token_here

# Service configuration
SERVICE_PORT=8080
WEBSOCKET_PORT=7997
FRONTEND_PORT=8897

# Logging
LOG_LEVEL=INFO
LOG_FILE=/opt/agent-forge/logs/agent-forge.log

# Database
DATABASE_PATH=/opt/agent-forge/data/agent-forge.db
```

### 5. Test Installation

```bash
# Run service manually
python -m agents.service_manager

# In another terminal, test endpoints
curl http://localhost:8080/health
curl http://localhost:8080/status
```

---

## 🐳 Docker Deployment

> **Note**: Docker deployment is planned for future release.

**Dockerfile** (example):

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Ollama
RUN curl -fsSL https://ollama.com/install.sh | sh

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create non-root user
RUN useradd -m -u 1000 agent-forge && \
    chown -R agent-forge:agent-forge /app

USER agent-forge

# Expose ports
EXPOSE 8080 7997 8897

# Start services
CMD ["python", "-m", "agents.service_manager"]
```

**docker-compose.yml** (example):

```yaml
version: '3.8'

services:
  agent-forge:
    build: .
    container_name: agent-forge
    restart: unless-stopped
    ports:
      - "8080:8080"
      - "7997:7997"
      - "8897:8897"
    environment:
      - GITHUB_TOKEN=${GITHUB_TOKEN}
      - GITHUB_BOT_TOKEN=${GITHUB_BOT_TOKEN}
      - LOG_LEVEL=INFO
    volumes:
      - ./config:/app/config
      - ./data:/app/data
      - ./logs:/app/logs
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

---

## 🔧 Systemd Service

### Installation

1. **Copy Service File**:

```bash
sudo cp systemd/agent-forge.service /etc/systemd/system/
```

2. **Edit Service File** (if needed):

```bash
sudo nano /etc/systemd/system/agent-forge.service
```

**Service File** (`/etc/systemd/system/agent-forge.service`):

```ini
[Unit]
Description=Agent-Forge Multi-Agent System
After=network.target ollama.service
Requires=ollama.service

[Service]
Type=notify
User=agent-forge
Group=agent-forge
WorkingDirectory=/opt/agent-forge
Environment="PATH=/opt/agent-forge/venv/bin:/usr/local/bin:/usr/bin"
EnvironmentFile=/opt/agent-forge/.env

# Start command
ExecStart=/opt/agent-forge/venv/bin/python -m agents.service_manager

# Restart policy
Restart=always
RestartSec=10
StartLimitBurst=5
StartLimitIntervalSec=300

# Resource limits
MemoryMax=2G
MemoryHigh=1.5G
CPUQuota=200%

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=agent-forge

# Security
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/agent-forge/logs /opt/agent-forge/data

# Watchdog
WatchdogSec=60

[Install]
WantedBy=multi-user.target
```

3. **Enable and Start Service**:

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable on boot
sudo systemctl enable agent-forge

# Start service
sudo systemctl start agent-forge

# Check status
sudo systemctl status agent-forge
```

### Service Management

```bash
# Start service
sudo systemctl start agent-forge

# Stop service
sudo systemctl stop agent-forge

# Restart service
sudo systemctl restart agent-forge

# Reload configuration
sudo systemctl reload agent-forge

# View logs
sudo journalctl -u agent-forge -f --no-pager

# View recent logs
sudo journalctl -u agent-forge -n 100 --no-pager

# View logs since boot
sudo journalctl -u agent-forge -b --no-pager
```

### Automatic Installation Script

**scripts/install-service.sh**:

```bash
#!/bin/bash
set -e

echo "Installing Agent-Forge systemd service..."

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root" 
   exit 1
fi

# Copy service file
cp systemd/agent-forge.service /etc/systemd/system/

# Reload systemd
systemctl daemon-reload

# Enable service
systemctl enable agent-forge

echo "Service installed successfully!"
echo ""
echo "To start the service:"
echo "  sudo systemctl start agent-forge"
echo ""
echo "To view logs:"
echo "  sudo journalctl -u agent-forge -f --no-pager"
```

---

## 🌐 Nginx Reverse Proxy

### Purpose

- HTTPS termination (SSL/TLS)
- Load balancing (future)
- Static file serving
- Security headers
- Rate limiting

### Installation

```bash
# Install nginx
sudo apt install nginx

# Enable and start
sudo systemctl enable nginx
sudo systemctl start nginx
```

### Configuration

**File**: `/etc/nginx/sites-available/agent-forge`

```nginx
# HTTP to HTTPS redirect
server {
    listen 80;
    listen [::]:80;
    server_name agent-forge.example.com;
    
    return 301 https://$server_name$request_uri;
}

# HTTPS server
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name agent-forge.example.com;
    
    # SSL configuration
    ssl_certificate /etc/letsencrypt/live/agent-forge.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/agent-forge.example.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    
    # API proxy
    location /api/ {
        proxy_pass http://localhost:8080/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # WebSocket proxy
    location /ws/ {
        proxy_pass http://localhost:7997/ws/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "Upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts for WebSocket
        proxy_connect_timeout 7d;
        proxy_send_timeout 7d;
        proxy_read_timeout 7d;
    }
    
    # Frontend static files
    location / {
        proxy_pass http://localhost:8897;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=60r/m;
    limit_req zone=api burst=20 nodelay;
    
    # Access logs
    access_log /var/log/nginx/agent-forge-access.log;
    error_log /var/log/nginx/agent-forge-error.log;
}
```

### Enable Configuration

```bash
# Create symlink
sudo ln -s /etc/nginx/sites-available/agent-forge /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Reload nginx
sudo systemctl reload nginx
```

### SSL Certificate (Let's Encrypt)

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d agent-forge.example.com

# Auto-renewal is set up automatically
# Test renewal
sudo certbot renew --dry-run
```

---

## ⚙️ Environment Configuration

### Production .env File

```bash
# /opt/agent-forge/.env

# GitHub Authentication
GITHUB_TOKEN=ghp_production_token
GITHUB_BOT_TOKEN=ghp_bot_production_token

# Service Ports
SERVICE_PORT=8080
WEBSOCKET_PORT=7997
FRONTEND_PORT=8897

# Logging
LOG_LEVEL=INFO
LOG_FILE=/opt/agent-forge/logs/agent-forge.log
LOG_MAX_SIZE=10485760  # 10 MB
LOG_BACKUP_COUNT=5

# Database
DATABASE_PATH=/opt/agent-forge/data/agent-forge.db

# Ollama
OLLAMA_HOST=http://localhost:11434

# Performance
MAX_WORKERS=4
REQUEST_TIMEOUT=300
MAX_CONCURRENT_TASKS=5

# Security
ALLOWED_HOSTS=agent-forge.example.com,localhost
CORS_ORIGINS=https://agent-forge.example.com
```

### Production config/system.yaml

```yaml
service_manager:
  enable_polling: true
  enable_monitoring: true
  enable_web_ui: true
  
  polling_interval: 300  # 5 minutes
  monitoring_port: 7997
  web_ui_port: 8897
  service_port: 8080
  
  polling_repos:
    - "m0nk111/agent-forge"
    - "m0nk111/stepperheightcontrol"
  
  # Resource limits
  max_concurrent_agents: 3
  max_memory_mb: 2048
  max_cpu_percent: 80

logging:
  level: INFO
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file: /opt/agent-forge/logs/agent-forge.log
  max_size_mb: 10
  backup_count: 5

database:
  path: /opt/agent-forge/data/agent-forge.db
  timeout: 30
  journal_mode: WAL

security:
  rate_limit:
    enabled: true
    requests_per_minute: 60
  
  cors:
    enabled: true
    allowed_origins:
      - "https://agent-forge.example.com"
```

---

## 🔒 Security Hardening

### 1. Firewall Configuration

```bash
# Allow SSH
sudo ufw allow 22/tcp

# Allow HTTPS only (nginx handles HTTP->HTTPS redirect)
sudo ufw allow 443/tcp

# Block direct access to application ports
sudo ufw deny 8080/tcp
sudo ufw deny 7997/tcp
sudo ufw deny 8897/tcp

# Enable firewall
sudo ufw enable
```

### 2. File Permissions

```bash
# Secure configuration files
chmod 600 /opt/agent-forge/.env
chmod 644 /opt/agent-forge/config/*.yaml

# Secure directories
chmod 755 /opt/agent-forge
chmod 700 /opt/agent-forge/data
chmod 755 /opt/agent-forge/logs

# Set ownership
chown -R agent-forge:agent-forge /opt/agent-forge
```

### 3. Environment Variables

```bash
# Never commit .env to Git
echo ".env" >> .gitignore

# Use secrets management (future)
# - HashiCorp Vault
# - AWS Secrets Manager
# - Azure Key Vault
```

### 4. Rate Limiting

Already configured in Nginx (see above).

### 5. Security Headers

Already configured in Nginx (see above).

---

## 📊 Monitoring Setup

### 1. Log Aggregation

```bash
# View live logs
sudo journalctl -u agent-forge -f --no-pager

# Export logs
sudo journalctl -u agent-forge --since "2025-10-06" > logs-2025-10-06.txt

# Rotate logs
sudo logrotate -f /etc/logrotate.d/agent-forge
```

### 2. Metrics Collection

Dashboard available at: `http://localhost:8897/dashboard.html`

### 3. Alerts (Future)

- Email notifications on errors
- Slack/Discord webhooks
- PagerDuty integration

---

## 💾 Backup Strategy

### Database Backup

```bash
#!/bin/bash
# /opt/agent-forge/scripts/backup-db.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/opt/agent-forge/backups"
DB_PATH="/opt/agent-forge/data/agent-forge.db"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Backup database
sqlite3 "$DB_PATH" ".backup '$BACKUP_DIR/agent-forge_$DATE.db'"

# Compress
gzip "$BACKUP_DIR/agent-forge_$DATE.db"

# Keep only last 30 days
find "$BACKUP_DIR" -name "agent-forge_*.db.gz" -mtime +30 -delete

echo "Backup completed: agent-forge_$DATE.db.gz"
```

### Automated Backups

```bash
# Add to crontab
crontab -e

# Daily backup at 3 AM
0 3 * * * /opt/agent-forge/scripts/backup-db.sh
```

---

## 🐛 Troubleshooting

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for detailed troubleshooting guide.

### Quick Checks

```bash
# Service status
sudo systemctl status agent-forge

# Recent logs
sudo journalctl -u agent-forge -n 50 --no-pager

# Check ports
sudo lsof -i:8080,7997,8897

# Test endpoints
curl http://localhost:8080/health
```

---

**Deployment Guide Version**: 1.0  
**Last Updated**: October 6, 2025

*For development setup, see [CONTRIBUTING.md](../CONTRIBUTING.md)*
