"""
Google OAuth authentication routes for Agent-Forge dashboard.

Provides secure authentication using Google OAuth 2.0.
Sessions are stored in-memory (consider Redis for production).
"""

import os
import secrets
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from urllib.parse import urlencode

import httpx
from fastapi import FastAPI, Request, Response, HTTPException, Depends, Cookie
from fastapi.responses import RedirectResponse, JSONResponse
from starlette.middleware.sessions import SessionMiddleware

logger = logging.getLogger(__name__)

# OAuth Configuration
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8897/auth/callback")
SESSION_SECRET = os.getenv("SESSION_SECRET", secrets.token_hex(32))
ALLOWED_EMAILS_STR = os.getenv("ALLOWED_EMAILS", "")
ALLOWED_EMAILS = [email.strip() for email in ALLOWED_EMAILS_STR.split(",") if email.strip()]

# Google OAuth endpoints
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"

# Session storage (in-memory, use Redis for production)
sessions: Dict[str, Dict[str, Any]] = {}


def create_app() -> FastAPI:
    """Create FastAPI app with auth routes."""
    app = FastAPI(title="Agent-Forge Auth API")
    
    # Add session middleware
    app.add_middleware(
        SessionMiddleware,
        secret_key=SESSION_SECRET,
        max_age=86400,  # 24 hours
        same_site="lax",
        https_only=False  # Set to True if using HTTPS
    )
    
    return app


app = create_app()


async def get_current_user(request: Request) -> Optional[Dict[str, Any]]:
    """
    Get current authenticated user from session.
    
    Returns:
        User dict with email, name, picture if authenticated, None otherwise
    """
    session_id = request.cookies.get("session_id")
    if not session_id:
        return None
    
    session = sessions.get(session_id)
    if not session:
        return None
    
    # Check session expiry
    if datetime.now() > session.get("expires_at", datetime.min):
        del sessions[session_id]
        return None
    
    return session.get("user")


async def require_auth(request: Request) -> Dict[str, Any]:
    """
    Dependency to require authentication.
    
    Raises:
        HTTPException: 401 if not authenticated
    
    Returns:
        User dict
    """
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


@app.get("/auth/login")
async def login(request: Request):
    """
    Redirect to Google OAuth login page.
    
    Query params:
        redirect_to: URL to redirect after successful login (optional)
    """
    # Generate random state for CSRF protection
    state = secrets.token_urlsafe(32)
    request.session["oauth_state"] = state
    
    # Store redirect destination
    redirect_to = request.query_params.get("redirect_to", "/dashboard.html")
    request.session["redirect_to"] = redirect_to
    
    # Build Google OAuth URL
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "access_type": "online",
        "prompt": "select_account"
    }
    
    auth_url = f"{GOOGLE_AUTH_URL}?{urlencode(params)}"
    return RedirectResponse(auth_url)


@app.get("/auth/callback")
async def callback(request: Request):
    """
    OAuth callback endpoint.
    
    Google redirects here after user authentication.
    Exchanges code for token and creates session.
    """
    # Verify state (CSRF protection)
    state = request.query_params.get("state")
    session_state = request.session.get("oauth_state")
    
    if not state or state != session_state:
        raise HTTPException(status_code=400, detail="Invalid state parameter")
    
    # Get authorization code
    code = request.query_params.get("code")
    if not code:
        error = request.query_params.get("error", "unknown_error")
        raise HTTPException(status_code=400, detail=f"OAuth error: {error}")
    
    # Exchange code for access token
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": GOOGLE_REDIRECT_URI
            }
        )
        
        if token_response.status_code != 200:
            logger.error(f"Token exchange failed: {token_response.text}")
            raise HTTPException(status_code=400, detail="Failed to obtain access token")
        
        token_data = token_response.json()
        access_token = token_data.get("access_token")
        
        # Get user info
        userinfo_response = await client.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        if userinfo_response.status_code != 200:
            logger.error(f"Userinfo request failed: {userinfo_response.text}")
            raise HTTPException(status_code=400, detail="Failed to get user info")
        
        user_data = userinfo_response.json()
    
    # Check if user email is allowed
    user_email = user_data.get("email")
    if ALLOWED_EMAILS and user_email not in ALLOWED_EMAILS:
        logger.warning(f"Access denied for email: {user_email}")
        raise HTTPException(status_code=403, detail="Access denied. Email not in allowed list.")
    
    # Create session
    session_id = secrets.token_urlsafe(32)
    sessions[session_id] = {
        "user": {
            "email": user_email,
            "name": user_data.get("name"),
            "picture": user_data.get("picture"),
            "verified_email": user_data.get("verified_email", False)
        },
        "created_at": datetime.now(),
        "expires_at": datetime.now() + timedelta(hours=24)
    }
    
    logger.info(f"✅ User logged in: {user_email}")
    
    # Redirect to original destination
    redirect_to = request.session.get("redirect_to", "/dashboard.html")
    response = RedirectResponse(redirect_to)
    response.set_cookie(
        key="session_id",
        value=session_id,
        max_age=86400,  # 24 hours
        httponly=True,
        samesite="lax"
    )
    
    return response


@app.get("/auth/logout")
async def logout(request: Request):
    """Logout current user and destroy session."""
    session_id = request.cookies.get("session_id")
    if session_id and session_id in sessions:
        user_email = sessions[session_id].get("user", {}).get("email")
        del sessions[session_id]
        logger.info(f"🚪 User logged out: {user_email}")
    
    response = RedirectResponse("/")
    response.delete_cookie("session_id")
    return response


@app.get("/auth/user")
async def get_user(user: Dict[str, Any] = Depends(require_auth)):
    """
    Get current authenticated user info.
    
    Returns:
        User object with email, name, picture
    """
    return user


@app.get("/auth/status")
async def auth_status(request: Request):
    """
    Check authentication status.
    
    Returns:
        {authenticated: bool, user: {...} | null}
    """
    user = await get_current_user(request)
    return {
        "authenticated": user is not None,
        "user": user
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "oauth_configured": bool(GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET),
        "allowed_emails_count": len(ALLOWED_EMAILS)
    }


if __name__ == "__main__":
    import uvicorn
    
    # Check configuration
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        logger.warning("⚠️  Google OAuth not configured. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET env vars.")
    
    if not ALLOWED_EMAILS:
        logger.warning("⚠️  No email whitelist configured. Set ALLOWED_EMAILS env var (comma-separated).")
    
    logger.info("🔐 Starting Auth API on http://0.0.0.0:7999")
    logger.info(f"📧 Allowed emails: {ALLOWED_EMAILS}")
    
    uvicorn.run(app, host="0.0.0.0", port=7999, log_level="info")
