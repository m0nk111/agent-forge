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
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

app = FastAPI(title="Agent-Forge SSH Auth")

# CORS for dashboard - Allow all origins on port 8897 for development
# In production, lock this down to specific domains
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (for development/testing)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# JWT Configuration
JWT_SECRET = os.getenv("SESSION_SECRET", "change-me-in-production-" + os.urandom(16).hex())
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_HOURS = 24

# Session storage (in-memory)
active_sessions = {}  # {token: {"username": str, "expires": datetime}}


class LoginRequest(BaseModel):
    """Login request model"""
    username: str
    password: str


class LoginResponse(BaseModel):
    """Login response model"""
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
        authenticated = simplepam.authenticate(username, password)
        
        if authenticated:
            logger.info(f"✅ Authentication successful for user: {username}")
            return True
        else:
            logger.warning(f"❌ Authentication failed for user: {username}")
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
    expires = session.get("expires", "")
    
    return {
        "authenticated": True,
        "username": username,
        "expires": expires.isoformat() if isinstance(expires, datetime) else ""
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
    if "change-me-in-production" in JWT_SECRET:
        logger.warning("⚠️ Using generated JWT secret. Set SESSION_SECRET environment variable for production!")
    
    logger.info("🚀 Starting SSH Auth API on port 7996...")
    logger.info("🔐 Authentication: PAM (system SSH credentials)")
    logger.info(f"🔑 Active sessions: {len(active_sessions)}")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=7996,  # Changed from 7999
        log_level="info"
    )
