"""Discovery API routes for projects and agents.

Endpoints for:
- Base folder management
- Project listing and syncing
- Agent discovery
- Agent toolkit configuration (with frontmatter write-back!)
- Icon picker
"""
from typing import List, Optional, Dict, Any
from pathlib import Path
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from .database import get_db_session
from .models import UserBaseFolder, Project, Agent, User
from .discovery import (
    ProjectScanner,
    AgentParser,
    FrontmatterManager,
    get_discovery_service,
)
from .permissions import ThreeTierPermissionChecker, Permission

router = APIRouter(prefix="/discovery", tags=["discovery"])


# ==========================================
# Request/Response Models
# ==========================================

class BaseFolderRequest(BaseModel):
    """Base folder creation request."""
    path: str = Field(..., description="Absolute path to scan")
    label: Optional[str] = Field(None, description="Display name")


class BaseFolderResponse(BaseModel):
    """Base folder response."""
    id: str
    path: str
    label: Optional[str]
    is_active: bool
    last_scanned_at: Optional[str]


class ProjectResponse(BaseModel):
    """Project response."""
    id: str
    name: str
    path: str
    git_remote_url: Optional[str]
    has_genie_folder: bool
    agent_count: int
    is_active: bool
    discovered_at: str
    last_synced_at: Optional[str]


class AgentResponse(BaseModel):
    """Agent response."""
    id: str
    project_id: str
    filename: str
    relative_path: str
    title: str
    description: Optional[str]
    icon: str
    model: Optional[str]
    executor: Optional[str]
    has_toolkit: bool
    toolkit: Optional[Dict[str, Any]]


class AgentToolkitRequest(BaseModel):
    """Agent toolkit configuration request."""
    name: Optional[str] = Field(None, description="Toolkit display name")
    tools: List[Dict[str, Any]] = Field(..., description="List of tools with permissions")
    inherit_project_tools: bool = Field(False, description="Inherit project-level tools")


class AgentIconRequest(BaseModel):
    """Agent icon update request."""
    icon: str = Field(..., description="Lucide icon name", min_length=1)


# ==========================================
# Dependency Injection
# ==========================================

async def get_current_user_id() -> str:
    """Get current user ID from auth context.

    TODO: Implement proper auth context extraction
    For now, returns placeholder
    """
    # This should come from FastMCP Context or JWT
    return "placeholder-user-id"


async def get_permission_checker(
    session: AsyncSession = Depends(get_db_session)
) -> ThreeTierPermissionChecker:
    """Get permission checker."""
    return ThreeTierPermissionChecker(session)


# ==========================================
# Base Folder Endpoints
# ==========================================

@router.get("/base-folders", response_model=List[BaseFolderResponse])
async def list_base_folders(
    session: AsyncSession = Depends(get_db_session),
    user_id: str = Depends(get_current_user_id)
):
    """List user's base folders."""
    result = await session.execute(
        select(UserBaseFolder)
        .where(UserBaseFolder.user_id == user_id)
        .order_by(UserBaseFolder.created_at)
    )
    folders = result.scalars().all()

    return [
        BaseFolderResponse(
            id=f.id,
            path=f.path,
            label=f.label,
            is_active=f.is_active,
            last_scanned_at=f.last_scanned_at.isoformat() if f.last_scanned_at else None
        )
        for f in folders
    ]


@router.post("/base-folders", response_model=BaseFolderResponse)
async def create_base_folder(
    request: BaseFolderRequest,
    session: AsyncSession = Depends(get_db_session),
    user_id: str = Depends(get_current_user_id)
):
    """Create new base folder."""
    import uuid
    from datetime import datetime

    # Validate path exists
    path = Path(request.path)
    if not path.exists() or not path.is_dir():
        raise HTTPException(status_code=400, detail="Path does not exist or is not a directory")

    # Get user workspace
    result = await session.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Create base folder
    folder = UserBaseFolder(
        id=str(uuid.uuid4()),
        user_id=user_id,
        workspace_id=user.workspace_id,
        path=str(path.resolve()),
        label=request.label,
        is_active=True,
        last_scanned_at=None,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    session.add(folder)
    await session.commit()
    await session.refresh(folder)

    return BaseFolderResponse(
        id=folder.id,
        path=folder.path,
        label=folder.label,
        is_active=folder.is_active,
        last_scanned_at=None
    )


@router.post("/base-folders/{folder_id}/scan")
async def scan_base_folder(
    folder_id: str,
    session: AsyncSession = Depends(get_db_session),
    user_id: str = Depends(get_current_user_id),
    permissions: ThreeTierPermissionChecker = Depends(get_permission_checker)
):
    """Scan base folder for projects."""
    # Get folder
    result = await session.execute(
        select(UserBaseFolder).where(UserBaseFolder.id == folder_id)
    )
    folder = result.scalar_one_or_none()
    if not folder:
        raise HTTPException(status_code=404, detail="Base folder not found")

    # Check permission
    if folder.user_id != user_id:
        if not await permissions.is_platform_admin(user_id):
            raise HTTPException(status_code=403, detail="Not authorized")

    # Scan for projects
    scanner = ProjectScanner(session)
    projects = await scanner.scan_base_folder(folder_id, folder.workspace_id)

    return {
        "scanned": True,
        "projects_found": len(projects),
        "projects": [p.id for p in projects]
    }


# ==========================================
# Project Endpoints
# ==========================================

@router.get("/projects", response_model=List[ProjectResponse])
async def list_projects(
    session: AsyncSession = Depends(get_db_session),
    user_id: str = Depends(get_current_user_id),
    permissions: ThreeTierPermissionChecker = Depends(get_permission_checker)
):
    """List user's projects."""
    # Get user workspace
    result = await session.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Get projects
    scanner = ProjectScanner(session)
    projects = await scanner.get_projects(user.workspace_id, active_only=True)

    return [
        ProjectResponse(
            id=p.id,
            name=p.name,
            path=p.path,
            git_remote_url=p.git_remote_url,
            has_genie_folder=p.has_genie_folder,
            agent_count=p.agent_count,
            is_active=p.is_active,
            discovered_at=p.discovered_at.isoformat(),
            last_synced_at=p.last_synced_at.isoformat() if p.last_synced_at else None
        )
        for p in projects
    ]


@router.post("/projects/{project_id}/sync")
async def sync_project(
    project_id: str,
    session: AsyncSession = Depends(get_db_session),
    user_id: str = Depends(get_current_user_id),
    permissions: ThreeTierPermissionChecker = Depends(get_permission_checker)
):
    """Resync project and scan for agents."""
    # Check permission
    if not await permissions.check_project_access(user_id, project_id, Permission.PROJECT_WRITE):
        raise HTTPException(status_code=403, detail="Not authorized")

    # Rescan project
    scanner = ProjectScanner(session)
    project = await scanner.rescan_project(project_id)

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Scan for agents
    parser = AgentParser(session)
    agents = await parser.scan_project(project_id)

    return {
        "synced": True,
        "project_id": project_id,
        "agents_found": len(agents),
        "agents": [a.id for a in agents]
    }


# ==========================================
# Agent Endpoints
# ==========================================

@router.get("/projects/{project_id}/agents", response_model=List[AgentResponse])
async def list_agents(
    project_id: str,
    session: AsyncSession = Depends(get_db_session),
    user_id: str = Depends(get_current_user_id),
    permissions: ThreeTierPermissionChecker = Depends(get_permission_checker)
):
    """List agents in project."""
    # Check permission
    if not await permissions.check_project_access(user_id, project_id, Permission.PROJECT_READ):
        raise HTTPException(status_code=403, detail="Not authorized")

    # Get agents
    parser = AgentParser(session)
    agents = await parser.get_project_agents(project_id)

    return [
        AgentResponse(
            id=a.id,
            project_id=a.project_id,
            filename=a.filename,
            relative_path=a.relative_path,
            title=a.title,
            description=a.description,
            icon=a.icon,
            model=a.model,
            executor=a.executor,
            has_toolkit=bool(a.toolkit),
            toolkit=a.toolkit
        )
        for a in agents
    ]


# ==========================================
# Agent Toolkit Configuration (CRITICAL!)
# ==========================================

@router.put("/agents/{agent_id}/toolkit")
async def update_agent_toolkit(
    agent_id: str,
    request: AgentToolkitRequest,
    session: AsyncSession = Depends(get_db_session),
    user_id: str = Depends(get_current_user_id),
    permissions: ThreeTierPermissionChecker = Depends(get_permission_checker)
):
    """Update agent toolkit configuration.

    CRITICAL: This endpoint writes toolkit config back to .genie frontmatter!
    The config is version-controlled and persists across tool instances.
    """
    # Get agent
    result = await session.execute(
        select(Agent).where(Agent.id == agent_id)
    )
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    # Check permission
    if not await permissions.can_configure_agent(user_id, agent_id):
        raise HTTPException(status_code=403, detail="Not authorized to configure this agent")

    # Get user email for attribution
    result = await session.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    user_email = user.email if user else None

    # Update database
    toolkit_dict = request.dict()
    agent.toolkit = toolkit_dict
    await session.commit()

    # CRITICAL: Write back to .genie frontmatter
    file_path = Path(agent.file_path)
    frontmatter = FrontmatterManager()

    success = frontmatter.update_hub_toolkit(
        file_path,
        toolkit_dict,
        configured_by=user_email
    )

    if not success:
        # Rollback database change if frontmatter write failed
        agent.toolkit = None
        await session.commit()
        raise HTTPException(
            status_code=500,
            detail="Failed to write toolkit config to .genie file"
        )

    return {
        "success": True,
        "agent_id": agent_id,
        "toolkit": toolkit_dict,
        "persisted_to": str(file_path),
        "message": "Toolkit configuration saved to database and .genie frontmatter"
    }


@router.get("/agents/{agent_id}/toolkit")
async def get_agent_toolkit(
    agent_id: str,
    session: AsyncSession = Depends(get_db_session),
    user_id: str = Depends(get_current_user_id),
    permissions: ThreeTierPermissionChecker = Depends(get_permission_checker)
):
    """Get agent toolkit configuration."""
    # Get agent
    result = await session.execute(
        select(Agent).where(Agent.id == agent_id)
    )
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    # Check permission
    if not await permissions.check_project_access(user_id, agent.project_id, Permission.PROJECT_READ):
        raise HTTPException(status_code=403, detail="Not authorized")

    return {
        "agent_id": agent_id,
        "has_toolkit": bool(agent.toolkit),
        "toolkit": agent.toolkit or {}
    }


# ==========================================
# Agent Icon Picker
# ==========================================

@router.put("/agents/{agent_id}/icon")
async def update_agent_icon(
    agent_id: str,
    request: AgentIconRequest,
    session: AsyncSession = Depends(get_db_session),
    user_id: str = Depends(get_current_user_id),
    permissions: ThreeTierPermissionChecker = Depends(get_permission_checker)
):
    """Update agent icon (Lucide icon name)."""
    # Get agent
    result = await session.execute(
        select(Agent).where(Agent.id == agent_id)
    )
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    # Check permission
    if not await permissions.can_configure_agent(user_id, agent_id):
        raise HTTPException(status_code=403, detail="Not authorized")

    # Update database
    agent.icon = request.icon
    await session.commit()

    # Write back to frontmatter
    file_path = Path(agent.file_path)
    frontmatter = FrontmatterManager()

    success = frontmatter.update_hub_icon(file_path, request.icon)

    if not success:
        # Rollback if frontmatter write failed
        agent.icon = "bot"
        await session.commit()
        raise HTTPException(
            status_code=500,
            detail="Failed to write icon to .genie file"
        )

    return {
        "success": True,
        "agent_id": agent_id,
        "icon": request.icon,
        "persisted_to": str(file_path)
    }
