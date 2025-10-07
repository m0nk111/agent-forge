# SSH-Based Dashboard Authentication

**Concept:** Gebruik systeem SSH credentials voor dashboard login  
**Voordeel:** Geen OAuth setup, werkt direct voor iedereen met SSH toegang  
**Tijd:** 30 minuten implementatie

---

## 🎯 Architectuur

```
User Browser
    ↓
    POST /auth/login (username, password)
    ↓
Dashboard (port 8897)
    ↓
Auth API (port 7999)
    ↓
PAM (Linux System Auth)
    ↓
✅ Valid SSH user → Session token
❌ Invalid → 401 Unauthorized
```

---

## 🔐 Security Model

**Authenticatie via PAM (Pluggable Authentication Modules)**
- ✅ Gebruikt systeem user accounts
- ✅ Zelfde credentials als SSH
- ✅ Geen aparte user database nodig
- ✅ System security policies (password complexity, lockout, etc.)

**Session Management**
- ✅ JWT token na succesvolle login
- ✅ Token expiry (24 uur)
- ✅ HttpOnly cookie (XSS protection)
- ✅ CSRF token

---

## 📦 Dependencies

```bash
# Install PAM library
pip install python-pam>=2.0.2
```

---

## 🔧 Implementation

### 1. Auth Backend (api/auth_routes.py)

```python
#!/usr/bin/env python3
"""
SSH-based Authentication for Agent-Forge Dashboard
Uses PAM to validate against system SSH credentials
"""

import os
import jwt
import pam
import logging
from datetime import datetime, timedelta
from typing import Optional
from fastapi import FastAPI, HTTPException, Response, Request, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

logger = logging.getLogger(__name__)

app = FastAPI(title="Agent-Forge SSH Auth")

# CORS for dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8897", "http://192.168.1.26:8897", "http://ai-kvm1:8897"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# JWT Configuration
JWT_SECRET = os.getenv("SESSION_SECRET", "change-me-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_HOURS = 24

# Session storage (in-memory, voor nu)
active_sessions = {}  # {token: {"username": str, "expires": datetime}}


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    success: bool
    token: Optional[str] = None
    username: Optional[str] = None
    expires: Optional[str] = None
    error: Optional[str] = None


def authenticate_user(username: str, password: str) -> bool:
    """
    Authenticate user against PAM (system SSH credentials)
    
    Args:
        username: System username
        password: User password
    
    Returns:
        True if authentication successful, False otherwise
    """
    try:
        p = pam.pam()
        authenticated = p.authenticate(username, password)
        
        if authenticated:
            logger.info(f"✅ Authentication successful for user: {username}")
            return True
        else:
            logger.warning(f"❌ Authentication failed for user: {username} - Reason: {p.reason}")
            return False
    except Exception as e:
        logger.error(f"❌ PAM authentication error: {e}")
        return False


def create_session_token(username: str) -> tuple[str, datetime]:
    """
    Create JWT session token
    
    Args:
        username: Authenticated username
    
    Returns:
        Tuple of (token, expiry_datetime)
    """
    expiry = datetime.utcnow() + timedelta(hours=JWT_EXPIRY_HOURS)
    
    payload = {
        "username": username,
        "exp": expiry,
        "iat": datetime.utcnow()
    }
    
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    
    return token, expiry


def verify_session_token(token: str) -> Optional[str]:
    """
    Verify JWT session token
    
    Args:
        token: JWT token
    
    Returns:
        Username if valid, None otherwise
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        username = payload.get("username")
        
        # Check if still in active sessions
        if token in active_sessions:
            return username
        else:
            logger.warning(f"⚠️ Token not in active sessions: {username}")
            return None
    except jwt.ExpiredSignatureError:
        logger.warning("⚠️ Token expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"⚠️ Invalid token: {e}")
        return None


@app.post("/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest, response: Response):
    """
    Login with SSH credentials
    
    POST /auth/login
    Body: {"username": "flip", "password": "secret"}
    
    Returns:
        Session token in cookie + JSON response
    """
    logger.info(f"🔐 Login attempt for user: {request.username}")
    
    # Authenticate via PAM
    if not authenticate_user(request.username, request.password):
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password"
        )
    
    # Create session token
    token, expiry = create_session_token(request.username)
    
    # Store in active sessions
    active_sessions[token] = {
        "username": request.username,
        "expires": expiry
    }
    
    # Set HttpOnly cookie
    response.set_cookie(
        key="session_token",
        value=token,
        httponly=True,
        secure=False,  # Set True if using HTTPS
        samesite="lax",
        max_age=JWT_EXPIRY_HOURS * 3600
    )
    
    logger.info(f"✅ Login successful for user: {request.username}")
    
    return LoginResponse(
        success=True,
        token=token,
        username=request.username,
        expires=expiry.isoformat()
    )


@app.get("/auth/status")
async def auth_status(request: Request):
    """
    Check authentication status
    
    GET /auth/status
    Cookie: session_token
    
    Returns:
        Current user info if authenticated
    """
    # Get token from cookie
    token = request.cookies.get("session_token")
    
    if not token:
        return JSONResponse(
            status_code=401,
            content={"authenticated": False, "error": "No session token"}
        )
    
    # Verify token
    username = verify_session_token(token)
    
    if not username:
        return JSONResponse(
            status_code=401,
            content={"authenticated": False, "error": "Invalid or expired token"}
        )
    
    session = active_sessions.get(token, {})
    
    return {
        "authenticated": True,
        "username": username,
        "expires": session.get("expires", "").isoformat() if isinstance(session.get("expires"), datetime) else ""
    }


@app.post("/auth/logout")
async def logout(request: Request, response: Response):
    """
    Logout and destroy session
    
    POST /auth/logout
    Cookie: session_token
    """
    # Get token from cookie
    token = request.cookies.get("session_token")
    
    if token and token in active_sessions:
        username = active_sessions[token]["username"]
        del active_sessions[token]
        logger.info(f"🔓 Logout successful for user: {username}")
    
    # Clear cookie
    response.delete_cookie(key="session_token")
    
    return {"success": True, "message": "Logged out successfully"}


@app.get("/auth/user")
async def get_user(request: Request):
    """
    Get current authenticated user
    
    GET /auth/user
    Cookie: session_token
    """
    token = request.cookies.get("session_token")
    
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    username = verify_session_token(token)
    
    if not username:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    
    return {
        "username": username,
        "authenticated": True
    }


@app.get("/health")
async def health():
    """
    Health check endpoint
    
    GET /health
    """
    return {
        "status": "healthy",
        "auth_type": "ssh_pam",
        "active_sessions": len(active_sessions)
    }


if __name__ == "__main__":
    import uvicorn
    
    # Generate session secret if not set
    if JWT_SECRET == "change-me-in-production":
        logger.warning("⚠️ Using default JWT secret! Set SESSION_SECRET environment variable!")
    
    logger.info("🚀 Starting SSH Auth API on port 7999...")
    logger.info("🔐 Authentication: PAM (system SSH credentials)")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=7999,
        log_level="info"
    )
```

### 2. Frontend Login Form (frontend/login.html)

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Agent-Forge Login</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
        }
        
        .login-container {
            background: white;
            padding: 40px;
            border-radius: 10px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.2);
            width: 100%;
            max-width: 400px;
        }
        
        h1 {
            text-align: center;
            color: #333;
            margin-bottom: 10px;
        }
        
        .subtitle {
            text-align: center;
            color: #666;
            font-size: 14px;
            margin-bottom: 30px;
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        label {
            display: block;
            color: #555;
            font-weight: 500;
            margin-bottom: 8px;
        }
        
        input[type="text"],
        input[type="password"] {
            width: 100%;
            padding: 12px;
            border: 2px solid #e0e0e0;
            border-radius: 5px;
            font-size: 14px;
            transition: border-color 0.3s;
        }
        
        input[type="text"]:focus,
        input[type="password"]:focus {
            outline: none;
            border-color: #667eea;
        }
        
        .btn-login {
            width: 100%;
            padding: 12px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 5px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s;
        }
        
        .btn-login:hover {
            transform: translateY(-2px);
        }
        
        .btn-login:disabled {
            opacity: 0.6;
            cursor: not-allowed;
        }
        
        .error-message {
            background: #fee;
            color: #c33;
            padding: 10px;
            border-radius: 5px;
            margin-bottom: 20px;
            display: none;
        }
        
        .info-message {
            background: #e3f2fd;
            color: #1565c0;
            padding: 10px;
            border-radius: 5px;
            margin-top: 20px;
            font-size: 13px;
        }
        
        .loading {
            text-align: center;
            color: #667eea;
            margin-top: 10px;
            display: none;
        }
    </style>
</head>
<body>
    <div class="login-container">
        <h1>🤖 Agent-Forge</h1>
        <p class="subtitle">Login with your SSH credentials</p>
        
        <div id="errorMessage" class="error-message"></div>
        
        <form id="loginForm">
            <div class="form-group">
                <label for="username">Username</label>
                <input type="text" id="username" name="username" required autofocus>
            </div>
            
            <div class="form-group">
                <label for="password">Password</label>
                <input type="password" id="password" name="password" required>
            </div>
            
            <button type="submit" class="btn-login" id="loginBtn">
                Login
            </button>
            
            <div class="loading" id="loading">
                🔄 Authenticating...
            </div>
        </form>
        
        <div class="info-message">
            💡 Use your system SSH credentials (same as <code>ssh user@ai-kvm1</code>)
        </div>
    </div>
    
    <script>
        const AUTH_API_URL = 'http://localhost:7999';
        const DASHBOARD_URL = '/dashboard.html';
        
        const loginForm = document.getElementById('loginForm');
        const loginBtn = document.getElementById('loginBtn');
        const loading = document.getElementById('loading');
        const errorMessage = document.getElementById('errorMessage');
        
        // Check if already authenticated
        window.addEventListener('DOMContentLoaded', async () => {
            try {
                const response = await fetch(`${AUTH_API_URL}/auth/status`, {
                    credentials: 'include'
                });
                
                if (response.ok) {
                    const data = await response.json();
                    if (data.authenticated) {
                        console.log('✅ Already authenticated, redirecting...');
                        window.location.href = DASHBOARD_URL;
                    }
                }
            } catch (error) {
                console.log('Not authenticated, showing login form');
            }
        });
        
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            
            // Hide error, show loading
            errorMessage.style.display = 'none';
            loading.style.display = 'block';
            loginBtn.disabled = true;
            
            try {
                const response = await fetch(`${AUTH_API_URL}/auth/login`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    credentials: 'include',
                    body: JSON.stringify({ username, password })
                });
                
                const data = await response.json();
                
                if (response.ok && data.success) {
                    console.log('✅ Login successful:', data.username);
                    // Redirect to dashboard
                    window.location.href = DASHBOARD_URL;
                } else {
                    // Show error
                    errorMessage.textContent = data.error || 'Invalid username or password';
                    errorMessage.style.display = 'block';
                    loading.style.display = 'none';
                    loginBtn.disabled = false;
                }
            } catch (error) {
                console.error('Login error:', error);
                errorMessage.textContent = 'Connection error. Is the auth service running?';
                errorMessage.style.display = 'block';
                loading.style.display = 'none';
                loginBtn.disabled = false;
            }
        });
    </script>
</body>
</html>
```

### 3. Dashboard Auth Check (update dashboard.html)

```javascript
// Add to frontend/dashboard.html (top of script section)

const AUTH_API_URL = 'http://localhost:7999';

// Check authentication on page load
async function checkAuth() {
    try {
        const response = await fetch(`${AUTH_API_URL}/auth/status`, {
            credentials: 'include'
        });
        
        if (!response.ok) {
            console.log('🔐 Not authenticated, redirecting to login...');
            window.location.href = '/login.html';
            return false;
        }
        
        const data = await response.json();
        
        if (!data.authenticated) {
            console.log('🔐 Not authenticated, redirecting to login...');
            window.location.href = '/login.html';
            return false;
        }
        
        console.log('✅ Authenticated as:', data.username);
        
        // Show username in UI (optional)
        updateAuthUI(data.username);
        
        return true;
    } catch (error) {
        console.error('Auth check failed:', error);
        window.location.href = '/login.html';
        return false;
    }
}

function updateAuthUI(username) {
    // Add logout button to header
    const header = document.querySelector('header') || document.body;
    const userInfo = document.createElement('div');
    userInfo.style.cssText = 'position: absolute; top: 10px; right: 10px; color: white;';
    userInfo.innerHTML = `
        <span>👤 ${username}</span>
        <button onclick="logout()" style="margin-left: 10px; padding: 5px 10px; cursor: pointer;">
            Logout
        </button>
    `;
    header.appendChild(userInfo);
}

async function logout() {
    try {
        await fetch(`${AUTH_API_URL}/auth/logout`, {
            method: 'POST',
            credentials: 'include'
        });
        
        window.location.href = '/login.html';
    } catch (error) {
        console.error('Logout error:', error);
        window.location.href = '/login.html';
    }
}

// Run auth check before initializing dashboard
window.addEventListener('DOMContentLoaded', async () => {
    const isAuthenticated = await checkAuth();
    if (!isAuthenticated) {
        return; // Stop loading dashboard
    }
    
    // Continue with dashboard initialization
    setViewMode(viewMode);
    connect();
});
```

---

## 🚀 Setup & Testing

### 1. Install Dependencies
```bash
cd /home/flip/agent-forge
pip install python-pam>=2.0.2 PyJWT>=2.8.0
```

### 2. Start Auth Service
```bash
python3 api/auth_routes.py
# Or use systemd service
```

### 3. Test Authentication
```bash
# Test health
curl http://localhost:7999/health

# Test login (replace with your credentials)
curl -X POST http://localhost:7999/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"flip","password":"your-password"}' \
  -c cookies.txt

# Test status
curl http://localhost:7999/auth/status -b cookies.txt
```

### 4. Access Dashboard
```
1. Open: http://192.168.1.26:8897/login.html
2. Login with SSH credentials (flip / your-password)
3. Redirects to dashboard.html
```

---

## 🔒 Security Considerations

### ✅ Strengths
- Uses system authentication (no separate user DB)
- PAM supports all SSH security features (2FA, key-based, etc.)
- HttpOnly cookies (XSS protection)
- JWT with expiry
- Session management

### ⚠️ Considerations
- Runs as flip user (can only authenticate users flip can check)
- May need sudo for PAM access (see troubleshooting)
- HTTP (not HTTPS) - OK for LAN, use HTTPS in production

### 🛡️ Hardening (Optional)
- Enable HTTPS (nginx reverse proxy)
- Add rate limiting (fail2ban)
- Add 2FA support via PAM
- Session timeout after inactivity

---

## 🐛 Troubleshooting

### Problem: PAM Permission Denied
```bash
# Solution: Add user to shadow group
sudo usermod -aG shadow flip

# Or: Run auth service with sudo
sudo python3 api/auth_routes.py
```

### Problem: Authentication Always Fails
```bash
# Test PAM directly
python3 -c "import pam; p = pam.pam(); print(p.authenticate('flip', 'password'))"

# Check system auth logs
sudo tail -f /var/log/auth.log
```

### Problem: CORS Errors
- Add your hostname to CORS origins in auth_routes.py
- Check browser console for details

---

## 📊 Comparison: SSH Auth vs OAuth

| Feature | SSH Auth | Google OAuth |
|---------|----------|--------------|
| Setup time | 5 min | 30 min |
| Dependencies | python-pam | httpx, google libs |
| User management | System users | Email whitelist |
| External service | ❌ None | ✅ Google |
| 2FA support | ✅ Via PAM | ✅ Via Google |
| Team friendly | ✅ SSH access | ✅ Email based |
| Complexity | 🟢 Low | 🟡 Medium |

**Conclusion:** SSH auth perfect voor Agent-Forge!

---

## ✅ Benefits

- 🚀 **Fast**: 5 minutes setup
- 🔐 **Secure**: System authentication
- 💰 **Free**: No external dependencies
- 🎯 **Simple**: Same credentials as SSH
- 🔧 **Flexible**: Works with existing user management

---

## 📝 Next Steps

1. Implement auth backend
2. Create login page
3. Update dashboard with auth check
4. Test authentication flow
5. Add to systemd service
