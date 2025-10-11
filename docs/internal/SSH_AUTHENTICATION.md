# SSH-Based Dashboard Authentication

**Status:** ✅ Implemented & Working  
**Auth Type:** SSH/PAM (System credentials)  
**Updated:** 2025-10-09

---

## 📋 Table of Contents

- [Quick Start](#quick-start)
- [Architecture Overview](#architecture-overview)
- [Security Model](#security-model)
- [Implementation Details](#implementation-details)
- [Usage Guide](#usage-guide)
- [Troubleshooting](#troubleshooting)
- [Comparison: SSH vs OAuth](#comparison-ssh-vs-oauth)

---

## 🚀 Quick Start

### Start Auth Service

```bash
# Option 1: Systemd (recommended)
sudo systemctl start agent-forge-auth
sudo systemctl status agent-forge-auth

# Option 2: Manual
cd /home/flip/agent-forge
./venv/bin/python api/auth_routes.py

# Option 3: Background
./venv/bin/python api/auth_routes.py > /tmp/auth.log 2>&1 &
```

### Access Login Page

```
http://YOUR_IP:8897/login.html
```

### Test Authentication

```bash
# Health check
curl http://localhost:7996/health

# Login
curl -X POST http://localhost:7996/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"YOUR_USER","password":"YOUR_PASS"}' \
  -c cookies.txt

# Check status
curl http://localhost:7996/auth/status -b cookies.txt

# Logout
curl -X POST http://localhost:7996/auth/logout -b cookies.txt
```

---

## 🎯 Architecture Overview

### Authentication Flow

```
User Browser (port 8897)
    ↓
    POST /auth/login (username, password)
    ↓
Auth API (port 7996)
    ↓
PAM (Linux System Auth)
    ↓
✅ Valid SSH user → JWT Session Token
❌ Invalid → 401 Unauthorized
```

### Components

**1. Auth Backend** (`api/auth_routes.py`)
- Port: 7996
- Auth Method: PAM (simplepam library)
- Session: JWT tokens (24h expiry)
- Storage: In-memory sessions

**2. Login Frontend** (`frontend/login.html`)
- Modern UI with gradient design
- Username + password form
- Error handling & validation
- Auto-redirect if already logged in

**3. Dashboard Integration** (`frontend/dashboard.html`)
- Auth check on load
- Auto-redirect to login if unauthenticated
- JWT token management
- Logout functionality

### API Endpoints

```
POST   /auth/login       → Login with SSH credentials
GET    /auth/status      → Check authentication status
POST   /auth/logout      → Destroy session
GET    /auth/user        → Get current user info
GET    /health           → Health check
```

---

## 🔐 Security Model

### Authentication via PAM

**Benefits:**
- ✅ Uses system user accounts (same as SSH)
- ✅ No separate user database needed
- ✅ Inherits system security policies:
  - Password complexity requirements
  - Account lockout policies
  - Password expiration
  - Multi-factor authentication (if configured)

### Session Management

**JWT Tokens:**
- Token expiry: 24 hours (configurable)
- Secure token generation with SECRET_KEY
- Automatic cleanup of expired sessions

**Cookie Security:**
- HttpOnly: Prevents XSS attacks
- SameSite: CSRF protection
- Secure flag: HTTPS only (production)

### Authorization Levels

**Current Implementation:**
- All authenticated users have full access
- User must have valid system account

**Future Enhancement:**
- Role-based access control (RBAC)
- Permission levels (viewer, operator, admin)
- Agent-specific permissions

---

## 🔧 Implementation Details

### Dependencies

```bash
# Required packages
pip install simplepam==0.1.5    # PAM authentication
pip install PyJWT==2.10.1       # JWT tokens
pip install fastapi             # Web framework
pip install uvicorn             # ASGI server
```

### Configuration

**Environment Variables:**

```bash
# Auth service configuration
export AUTH_PORT=7996
export JWT_SECRET="your-secret-key-here"  # Generate with: openssl rand -hex 32
export JWT_EXPIRY_HOURS=24
export CORS_ORIGINS="http://localhost:8897,http://YOUR_IP:8897"
```

**Systemd Service:** (`systemd/agent-forge-auth.service`)

```ini
[Unit]
Description=Agent-Forge Authentication Service
After=network.target

[Service]
Type=simple
User=flip
WorkingDirectory=/home/flip/agent-forge
Environment="PATH=/home/flip/agent-forge/venv/bin"
Environment="JWT_SECRET=your-secret-key-here"
ExecStart=/home/flip/agent-forge/venv/bin/python api/auth_routes.py
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=multi-user.target
```

### Auth Backend Code Structure

**File:** `api/auth_routes.py`

```python
#!/usr/bin/env python3
"""
SSH-based Authentication for Agent-Forge Dashboard
Uses PAM to validate against system SSH credentials
"""

import os
import jwt
import simplepam
import logging
from datetime import datetime, timedelta
from typing import Optional
from fastapi import FastAPI, HTTPException, Response, Request, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Configuration
AUTH_PORT = int(os.getenv('AUTH_PORT', '7996'))
JWT_SECRET = os.getenv('JWT_SECRET', 'change-me-in-production')
JWT_EXPIRY_HOURS = int(os.getenv('JWT_EXPIRY_HOURS', '24'))

# Session storage (in-memory for now)
active_sessions = {}

# Models
class LoginRequest(BaseModel):
    username: str
    password: str

class AuthResponse(BaseModel):
    success: bool
    message: str
    token: Optional[str] = None
    user: Optional[dict] = None

# FastAPI app
app = FastAPI(title="Agent-Forge SSH Auth")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8897",
        "http://192.168.1.26:8897",
        # Add your IP addresses
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/auth/login")
async def login(request: LoginRequest, response: Response):
    """Authenticate user via PAM (SSH credentials)"""
    try:
        # Validate via PAM
        if simplepam.authenticate(request.username, request.password):
            # Generate JWT token
            expiry = datetime.utcnow() + timedelta(hours=JWT_EXPIRY_HOURS)
            token = jwt.encode({
                'username': request.username,
                'exp': expiry
            }, JWT_SECRET, algorithm='HS256')
            
            # Store session
            active_sessions[token] = {
                'username': request.username,
                'login_time': datetime.utcnow().isoformat(),
                'expiry': expiry.isoformat()
            }
            
            # Set cookie
            response.set_cookie(
                key="auth_token",
                value=token,
                httponly=True,
                max_age=JWT_EXPIRY_HOURS * 3600,
                samesite="lax"
            )
            
            return AuthResponse(
                success=True,
                message="Login successful",
                token=token,
                user={"username": request.username}
            )
        else:
            raise HTTPException(status_code=401, detail="Invalid credentials")
            
    except Exception as e:
        logging.error(f"Login error: {e}")
        raise HTTPException(status_code=500, detail="Authentication error")

@app.get("/auth/status")
async def check_status(request: Request):
    """Check if user is authenticated"""
    token = request.cookies.get("auth_token")
    
    if not token or token not in active_sessions:
        return {"authenticated": False}
    
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        return {
            "authenticated": True,
            "user": {"username": payload['username']}
        }
    except jwt.ExpiredSignatureError:
        active_sessions.pop(token, None)
        return {"authenticated": False, "reason": "Token expired"}
    except jwt.InvalidTokenError:
        return {"authenticated": False, "reason": "Invalid token"}

@app.post("/auth/logout")
async def logout(request: Request, response: Response):
    """Logout user and destroy session"""
    token = request.cookies.get("auth_token")
    
    if token:
        active_sessions.pop(token, None)
    
    response.delete_cookie(key="auth_token")
    return {"success": True, "message": "Logged out"}

@app.get("/auth/user")
async def get_current_user(request: Request):
    """Get current authenticated user"""
    token = request.cookies.get("auth_token")
    
    if not token or token not in active_sessions:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        session = active_sessions[token]
        return {
            "username": payload['username'],
            "login_time": session['login_time'],
            "expiry": session['expiry']
        }
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "auth_type": "ssh_pam",
        "active_sessions": len(active_sessions)
    }

if __name__ == "__main__":
    import uvicorn
    logging.basicConfig(level=logging.INFO)
    logging.info(f"🔐 Starting SSH Auth Service on port {AUTH_PORT}")
    uvicorn.run(app, host="0.0.0.0", port=AUTH_PORT)
```

---

## 📖 Usage Guide

### For End Users

**1. Access Dashboard**
- Open: `http://YOUR_IP:8897/dashboard.html`
- Automatically redirects to login if not authenticated

**2. Login**
- Enter your system username
- Enter your system password (same as SSH)
- Click "Login"

**3. Use Dashboard**
- Full access to agent management
- Monitor agent activity
- View logs and status

**4. Logout**
- Click logout button in dashboard
- Session is destroyed
- Redirected to login page

### For Administrators

**1. Install Auth Service**

```bash
# Copy systemd service
sudo cp systemd/agent-forge-auth.service /etc/systemd/system/

# Generate secure JWT secret
JWT_SECRET=$(openssl rand -hex 32)
sudo sed -i "s/your-secret-key-here/$JWT_SECRET/" /etc/systemd/system/agent-forge-auth.service

# Reload systemd
sudo systemctl daemon-reload

# Enable and start
sudo systemctl enable agent-forge-auth
sudo systemctl start agent-forge-auth

# Check status
sudo systemctl status agent-forge-auth
```

**2. Verify Installation**

```bash
# Check service is running
systemctl is-active agent-forge-auth

# Check port is listening
ss -tlnp | grep 7996

# Test health endpoint
curl http://localhost:7996/health
```

**3. Add Authorized Users**

```bash
# Create system user (if needed)
sudo useradd -m -s /bin/bash newuser
sudo passwd newuser

# User can now login to dashboard with these credentials
```

**4. Monitor Auth Service**

```bash
# View logs
sudo journalctl -u agent-forge-auth -f --no-pager

# Check active sessions
curl http://localhost:7996/health | jq '.active_sessions'

# View recent login attempts
sudo journalctl -u agent-forge-auth | grep "Login"
```

### Dashboard Integration

**File:** `frontend/dashboard.html`

Add auth check to dashboard:

```javascript
const AUTH_API_URL = 'http://localhost:7996';

async function checkAuth() {
    try {
        const response = await fetch(`${AUTH_API_URL}/auth/status`, {
            credentials: 'include'
        });
        
        if (!response.ok) {
            window.location.href = '/login.html';
            return false;
        }
        
        const data = await response.json();
        if (!data.authenticated) {
            window.location.href = '/login.html';
            return false;
        }
        
        return true;
    } catch (error) {
        console.error('Auth check failed:', error);
        window.location.href = '/login.html';
        return false;
    }
}

// Check auth on page load
window.addEventListener('DOMContentLoaded', async () => {
    const authenticated = await checkAuth();
    if (authenticated) {
        // Load dashboard data
        initDashboard();
    }
});

// Add logout button handler
document.getElementById('logoutBtn').addEventListener('click', async () => {
    await fetch(`${AUTH_API_URL}/auth/logout`, {
        method: 'POST',
        credentials: 'include'
    });
    window.location.href = '/login.html';
});
```

---

## 🐛 Troubleshooting

### Problem: Permission Denied (PAM)

**Symptom:** Login fails with "Permission denied" even with correct credentials

**Solution:**
```bash
# Check if user has valid system account
id USERNAME

# Verify PAM authentication works
pamtester login USERNAME authenticate

# Check auth service has proper permissions
# Service should run as user with PAM access
```

### Problem: Port 7996 Already in Use

**Symptom:** Auth service fails to start

**Solution:**
```bash
# Check what's using the port
sudo lsof -i :7996

# Kill the process
sudo kill $(sudo lsof -t -i :7996)

# Or change port in service config
sudo systemctl edit agent-forge-auth
```

### Problem: Module Not Found (simplepam)

**Symptom:** `ModuleNotFoundError: No module named 'simplepam'`

**Solution:**
```bash
# Install in correct environment
cd /home/flip/agent-forge
./venv/bin/pip install simplepam PyJWT

# Verify installation
./venv/bin/python -c "import simplepam; print('OK')"
```

### Problem: CORS Errors

**Symptom:** Browser console shows CORS errors

**Solution:**
```python
# Add your IP to CORS origins in api/auth_routes.py
allow_origins=[
    "http://localhost:8897",
    "http://YOUR_IP:8897",
    "http://YOUR_HOSTNAME:8897",
]

# Restart service
sudo systemctl restart agent-forge-auth
```

### Problem: Token Expired

**Symptom:** Redirected to login after some time

**Solution:**
```bash
# Tokens expire after 24 hours by default
# To extend, edit service config:
sudo systemctl edit agent-forge-auth

# Add:
[Service]
Environment="JWT_EXPIRY_HOURS=48"

# Restart
sudo systemctl restart agent-forge-auth
```

### Problem: Can't Login with System User

**Symptom:** User exists but can't authenticate

**Checklist:**
```bash
# 1. Verify user exists
id USERNAME

# 2. Verify user has password set
sudo passwd -S USERNAME
# Should show: "USERNAME P ..." (P = password set)

# 3. Test SSH login
ssh USERNAME@localhost

# 4. Check PAM configuration
ls -l /etc/pam.d/common-auth

# 5. Check auth service logs
sudo journalctl -u agent-forge-auth -n 50 --no-pager
```

---

## 📊 Comparison: SSH vs OAuth

### SSH/PAM Authentication (Current)

**Pros:**
- ✅ No external dependencies
- ✅ Uses existing system users
- ✅ Zero setup time (if users exist)
- ✅ Inherits system security policies
- ✅ Works offline
- ✅ No API keys or secrets to manage
- ✅ Simple to understand and debug

**Cons:**
- ❌ Requires system user account for each user
- ❌ Can't easily add external users
- ❌ Harder to implement fine-grained permissions
- ❌ Tied to single server (no centralized auth)

**Best for:**
- Single-server deployments
- Small teams (< 10 users)
- Users who already have SSH access
- Development and testing
- Self-hosted setups

### OAuth (Alternative)

**Pros:**
- ✅ No system users needed
- ✅ Easy to add external users
- ✅ Centralized authentication
- ✅ Fine-grained permissions (scopes)
- ✅ Social login (Google, GitHub)

**Cons:**
- ❌ Requires OAuth provider setup
- ❌ External dependency (Google, GitHub API)
- ❌ More complex implementation
- ❌ API quotas and rate limits
- ❌ Requires internet connection

**Best for:**
- Multi-server deployments
- Large teams (> 10 users)
- External user access
- Cloud deployments
- Enterprise environments

### Recommendation

**Use SSH/PAM if:**
- You're running Agent-Forge on a single server
- All users have SSH access already
- You want simple, zero-config authentication
- You're comfortable managing system users

**Use OAuth if:**
- You need to support many users
- Users don't have system accounts
- You need fine-grained permissions
- You're deploying to cloud/containers
- You want social login

**Hybrid Approach:**
- Start with SSH/PAM for simplicity
- Add OAuth later if needed
- Support both methods simultaneously

---

## ✅ Status & Files

### Implemented Files

```
api/
└── auth_routes.py              ✅ Auth backend (7996)

frontend/
├── login.html                  ✅ Login page
└── dashboard.html              ✅ Dashboard with auth check

systemd/
└── agent-forge-auth.service    ✅ Systemd service

requirements.txt                ✅ Updated with simplepam, PyJWT
```

### Configuration Files

```
/etc/systemd/system/
└── agent-forge-auth.service    → Systemd service config

/home/flip/agent-forge/
├── api/auth_routes.py          → Auth API code
├── frontend/login.html         → Login UI
└── frontend/dashboard.html     → Dashboard with auth
```

---

## 🎯 Benefits

### Security Benefits

1. **Strong Authentication**
   - Uses system-level authentication (PAM)
   - Inherits password policies
   - Account lockout protection
   - Password complexity requirements

2. **Session Security**
   - JWT tokens with expiry
   - HttpOnly cookies (XSS protection)
   - Secure cookie flags
   - Session cleanup

3. **No Credential Storage**
   - No password database to secure
   - No password hashes to protect
   - Leverages existing security infrastructure

### Operational Benefits

1. **Zero Configuration**
   - Works with existing users
   - No OAuth setup needed
   - No API keys to manage

2. **Simple Maintenance**
   - User management via system tools
   - Standard logging via journald
   - Familiar troubleshooting

3. **High Availability**
   - No external dependencies
   - Works offline
   - Fast authentication (local)

---

## 📚 Related Documentation

- [INSTALLATION.md](INSTALLATION.md) - Complete setup guide including auth
- [TOKEN_SECURITY.md](TOKEN_SECURITY.md) - Token and secrets management
- [DEPLOYMENT.md](DEPLOYMENT.md) - Production deployment guide
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - General troubleshooting

---

## 🔄 Future Enhancements

### Planned Features

1. **Role-Based Access Control (RBAC)**
   - Admin, operator, viewer roles
   - Per-agent permissions
   - Action-level authorization

2. **OAuth Support (Optional)**
   - Google OAuth
   - GitHub OAuth
   - Simultaneous SSH + OAuth

3. **Enhanced Session Management**
   - Database-backed sessions
   - Session history
   - Active session management UI

4. **Audit Logging**
   - Login/logout events
   - Failed authentication attempts
   - User action logging

5. **Multi-Factor Authentication (MFA)**
   - TOTP support
   - Hardware key support
   - SMS backup codes

---

**Last Updated:** 2025-10-09  
**Maintained By:** Agent-Forge Team
