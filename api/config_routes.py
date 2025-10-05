#!/usr/bin/env python3
"""
Configuration API Routes for Agent-Forge
FastAPI endpoints for managing agents, repositories, and system configuration.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from agents.config_manager import (
    get_config_manager,
    ConfigManager,
    AgentConfig,
    RepositoryConfig,
    SystemConfig
)

logger = logging.getLogger(__name__)

# Security scheme (JWT bearer tokens)
security = HTTPBearer()

# Pydantic models for API requests/responses
class AgentConfigModel(BaseModel):
    agent_id: str
    name: str
    model: str
    enabled: bool = True
    max_concurrent_tasks: int = Field(default=1, ge=1, le=10)
    polling_interval: int = Field(default=60, ge=10, le=3600)
    capabilities: List[str] = Field(default_factory=list)
    github_token: Optional[str] = None
    api_base_url: Optional[str] = None
    custom_settings: Dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class AgentUpdateModel(BaseModel):
    name: Optional[str] = None
    model: Optional[str] = None
    enabled: Optional[bool] = None
    max_concurrent_tasks: Optional[int] = Field(default=None, ge=1, le=10)
    polling_interval: Optional[int] = Field(default=None, ge=10, le=3600)
    capabilities: Optional[List[str]] = None
    github_token: Optional[str] = None
    api_base_url: Optional[str] = None
    custom_settings: Optional[Dict[str, Any]] = None


class RepositoryConfigModel(BaseModel):
    repo_id: str
    owner: str
    name: str
    enabled: bool = True
    auto_assign_issues: bool = True
    issue_labels: List[str] = Field(default_factory=list)
    branch_prefix: str = "feature"
    require_review: bool = True
    auto_merge: bool = False
    webhook_url: Optional[str] = None
    custom_settings: Dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class RepositoryUpdateModel(BaseModel):
    owner: Optional[str] = None
    name: Optional[str] = None
    enabled: Optional[bool] = None
    auto_assign_issues: Optional[bool] = None
    issue_labels: Optional[List[str]] = None
    branch_prefix: Optional[str] = None
    require_review: Optional[bool] = None
    auto_merge: Optional[bool] = None
    webhook_url: Optional[str] = None
    custom_settings: Optional[Dict[str, Any]] = None


class SystemConfigModel(BaseModel):
    monitoring_enabled: bool = True
    monitoring_port: int = Field(default=7997, ge=1024, le=65535)
    log_level: str = Field(default="INFO", pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")
    max_log_size: int = Field(default=10000, ge=100, le=100000)
    backup_enabled: bool = True
    backup_interval: int = Field(default=86400, ge=3600, le=604800)
    notification_email: Optional[str] = None
    slack_webhook: Optional[str] = None
    custom_settings: Dict[str, Any] = Field(default_factory=dict)
    updated_at: Optional[str] = None


class SystemUpdateModel(BaseModel):
    monitoring_enabled: Optional[bool] = None
    monitoring_port: Optional[int] = Field(default=None, ge=1024, le=65535)
    log_level: Optional[str] = Field(default=None, pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")
    max_log_size: Optional[int] = Field(default=None, ge=100, le=100000)
    backup_enabled: Optional[bool] = None
    backup_interval: Optional[int] = Field(default=None, ge=3600, le=604800)
    notification_email: Optional[str] = None
    slack_webhook: Optional[str] = None
    custom_settings: Optional[Dict[str, Any]] = None


# Dependency for authentication (placeholder - implement JWT validation)
async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify JWT token (placeholder implementation)"""
    # TODO: Implement actual JWT validation
    # For now, accept any token for development
    token = credentials.credentials
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    return {"user_id": "admin", "role": "admin"}  # Placeholder


# Create FastAPI app
app = FastAPI(
    title="Agent-Forge Configuration API",
    description="REST API for managing Agent-Forge configuration",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== AGENT ENDPOINTS ====================

@app.get("/api/config/agents", response_model=List[AgentConfigModel])
async def get_agents(
    enabled_only: bool = False,
    user: dict = Depends(verify_token)
):
    """Get all agent configurations"""
    try:
        manager = get_config_manager()
        agents = manager.get_agents()
        
        if enabled_only:
            agents = [a for a in agents if a.enabled]
        
        return agents
    except Exception as e:
        logger.error(f"Failed to get agents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/config/agents/{agent_id}", response_model=AgentConfigModel)
async def get_agent(
    agent_id: str,
    user: dict = Depends(verify_token)
):
    """Get specific agent configuration"""
    try:
        manager = get_config_manager()
        agent = manager.get_agent(agent_id)
        
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
        
        return agent
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/config/agents", response_model=AgentConfigModel, status_code=status.HTTP_201_CREATED)
async def create_agent(
    agent: AgentConfigModel,
    user: dict = Depends(verify_token)
):
    """Create new agent configuration"""
    try:
        manager = get_config_manager()
        agent_config = AgentConfig(**agent.model_dump())
        
        if not manager.add_agent(agent_config):
            raise HTTPException(
                status_code=400,
                detail=f"Agent {agent.agent_id} already exists"
            )
        
        return agent_config
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.patch("/api/config/agents/{agent_id}", response_model=AgentConfigModel)
async def update_agent(
    agent_id: str,
    updates: AgentUpdateModel,
    user: dict = Depends(verify_token)
):
    """Update agent configuration"""
    try:
        manager = get_config_manager()
        
        # Get current agent
        agent = manager.get_agent(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
        
        # Apply updates
        update_dict = {k: v for k, v in updates.model_dump().items() if v is not None}
        if not manager.update_agent(agent_id, update_dict):
            raise HTTPException(status_code=500, detail="Failed to update agent")
        
        # Return updated agent
        updated_agent = manager.get_agent(agent_id)
        return updated_agent
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/config/agents/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(
    agent_id: str,
    user: dict = Depends(verify_token)
):
    """Delete agent configuration"""
    try:
        manager = get_config_manager()
        
        if not manager.delete_agent(agent_id):
            raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
        
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== REPOSITORY ENDPOINTS ====================

@app.get("/api/config/repositories", response_model=List[RepositoryConfigModel])
async def get_repositories(
    enabled_only: bool = False,
    user: dict = Depends(verify_token)
):
    """Get all repository configurations"""
    try:
        manager = get_config_manager()
        repos = manager.get_repositories()
        
        if enabled_only:
            repos = [r for r in repos if r.enabled]
        
        return repos
    except Exception as e:
        logger.error(f"Failed to get repositories: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/config/repositories/{repo_id}", response_model=RepositoryConfigModel)
async def get_repository(
    repo_id: str,
    user: dict = Depends(verify_token)
):
    """Get specific repository configuration"""
    try:
        manager = get_config_manager()
        repo = manager.get_repository(repo_id)
        
        if not repo:
            raise HTTPException(status_code=404, detail=f"Repository {repo_id} not found")
        
        return repo
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get repository: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/config/repositories", response_model=RepositoryConfigModel, status_code=status.HTTP_201_CREATED)
async def create_repository(
    repo: RepositoryConfigModel,
    user: dict = Depends(verify_token)
):
    """Create new repository configuration"""
    try:
        manager = get_config_manager()
        repo_config = RepositoryConfig(**repo.model_dump())
        
        if not manager.add_repository(repo_config):
            raise HTTPException(
                status_code=400,
                detail=f"Repository {repo.repo_id} already exists"
            )
        
        return repo_config
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create repository: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.patch("/api/config/repositories/{repo_id}", response_model=RepositoryConfigModel)
async def update_repository(
    repo_id: str,
    updates: RepositoryUpdateModel,
    user: dict = Depends(verify_token)
):
    """Update repository configuration"""
    try:
        manager = get_config_manager()
        
        # Get current repository
        repo = manager.get_repository(repo_id)
        if not repo:
            raise HTTPException(status_code=404, detail=f"Repository {repo_id} not found")
        
        # Apply updates
        update_dict = {k: v for k, v in updates.model_dump().items() if v is not None}
        if not manager.update_repository(repo_id, update_dict):
            raise HTTPException(status_code=500, detail="Failed to update repository")
        
        # Return updated repository
        updated_repo = manager.get_repository(repo_id)
        return updated_repo
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update repository: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/config/repositories/{repo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_repository(
    repo_id: str,
    user: dict = Depends(verify_token)
):
    """Delete repository configuration"""
    try:
        manager = get_config_manager()
        
        if not manager.delete_repository(repo_id):
            raise HTTPException(status_code=404, detail=f"Repository {repo_id} not found")
        
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete repository: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== SYSTEM CONFIGURATION ENDPOINTS ====================

@app.get("/api/config/system", response_model=SystemConfigModel)
async def get_system_config(
    user: dict = Depends(verify_token)
):
    """Get system configuration"""
    try:
        manager = get_config_manager()
        return manager.get_system_config()
    except Exception as e:
        logger.error(f"Failed to get system config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.patch("/api/config/system", response_model=SystemConfigModel)
async def update_system_config(
    updates: SystemUpdateModel,
    user: dict = Depends(verify_token)
):
    """Update system configuration"""
    try:
        manager = get_config_manager()
        
        # Apply updates
        update_dict = {k: v for k, v in updates.model_dump().items() if v is not None}
        if not manager.update_system_config(update_dict):
            raise HTTPException(status_code=500, detail="Failed to update system config")
        
        # Return updated config
        return manager.get_system_config()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update system config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== UTILITY ENDPOINTS ====================

@app.get("/api/config/health")
async def health_check():
    """Health check endpoint (no authentication required)"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }


@app.post("/api/config/backup/cleanup")
async def cleanup_backups(
    keep_days: int = 7,
    user: dict = Depends(verify_token)
):
    """Cleanup old backup files"""
    try:
        manager = get_config_manager()
        manager.cleanup_old_backups(keep_days)
        return {"message": f"Cleaned up backups older than {keep_days} days"}
    except Exception as e:
        logger.error(f"Failed to cleanup backups: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("Starting Configuration API server on http://localhost:7996")
    print("API docs: http://localhost:7996/docs")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=7996,
        log_level="info"
    )
