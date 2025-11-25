"""Three-tier permission system for Automagik Hub.

Permission Layers:
1. Platform Admin - Full organization administration
2. Organization Users - Project and tool management within workspace
3. Agent Toolkits - Minimal permissions per agent

Hierarchy:
  Platform Admin (Layer 1)
    └── Organization User (Layer 2)
          └── Agent Toolkit (Layer 3)
"""
from typing import Optional, List, Set
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import User, UserRole, Project, Agent, ProjectTool, UserTool


class Permission:
    """Permission definitions."""

    # Platform-level permissions (Layer 1: Platform Admin)
    PLATFORM_ADMIN = "platform:admin"
    MANAGE_ALL_WORKSPACES = "platform:manage_workspaces"
    VIEW_ALL_AUDIT_LOGS = "platform:view_all_logs"
    MANAGE_SYSTEM_CONFIG = "platform:manage_config"

    # Workspace-level permissions (Layer 2: Organization Users)
    WORKSPACE_OWNER = "workspace:owner"
    MANAGE_PROJECTS = "workspace:manage_projects"
    MANAGE_TOOLS = "workspace:manage_tools"
    CONFIGURE_AGENTS = "workspace:configure_agents"
    VIEW_WORKSPACE_LOGS = "workspace:view_logs"

    # Project-level permissions
    PROJECT_READ = "project:read"
    PROJECT_WRITE = "project:write"
    PROJECT_DELETE = "project:delete"
    PROJECT_SYNC = "project:sync"

    # Agent-level permissions
    AGENT_READ = "agent:read"
    AGENT_CONFIGURE = "agent:configure"
    AGENT_EXECUTE = "agent:execute"

    # Tool-level permissions (Layer 3: Agent Toolkits)
    TOOL_USE = "tool:use"
    TOOL_CONFIGURE = "tool:configure"


class ThreeTierPermissionChecker:
    """Permission checker implementing three-tier model."""

    def __init__(self, session: AsyncSession):
        """Initialize permission checker.

        Args:
            session: Async database session
        """
        self.session = session

    async def _get_user(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    # ==========================================
    # Layer 1: Platform Admin Permissions
    # ==========================================

    async def is_platform_admin(self, user_id: str) -> bool:
        """Check if user is a platform admin.

        Args:
            user_id: User ID to check

        Returns:
            True if user is platform admin
        """
        user = await self._get_user(user_id)
        if not user:
            return False
        return user.is_super_admin or user.role == UserRole.SUPER_ADMIN.value

    async def check_platform_permission(
        self,
        user_id: str,
        permission: str
    ) -> bool:
        """Check platform-level permission.

        Args:
            user_id: User ID to check
            permission: Permission to check (e.g., Permission.PLATFORM_ADMIN)

        Returns:
            True if user has permission
        """
        # Platform admins have all platform permissions
        if await self.is_platform_admin(user_id):
            return True

        return False

    # ==========================================
    # Layer 2: Organization User Permissions
    # ==========================================

    async def check_workspace_access(
        self,
        user_id: str,
        workspace_id: str
    ) -> bool:
        """Check if user has access to workspace.

        Args:
            user_id: User ID to check
            workspace_id: Workspace ID to check

        Returns:
            True if user has access
        """
        # Platform admins can access all workspaces
        if await self.is_platform_admin(user_id):
            return True

        user = await self._get_user(user_id)
        if not user:
            return False

        # Check if user belongs to workspace
        return user.workspace_id == workspace_id

    async def check_project_access(
        self,
        user_id: str,
        project_id: str,
        permission: str = Permission.PROJECT_READ
    ) -> bool:
        """Check if user has access to project with specific permission.

        Args:
            user_id: User ID to check
            project_id: Project ID to check
            permission: Required permission

        Returns:
            True if user has access
        """
        # Get project
        result = await self.session.execute(
            select(Project).where(Project.id == project_id)
        )
        project = result.scalar_one_or_none()
        if not project:
            return False

        # Check workspace access
        if not await self.check_workspace_access(user_id, project.workspace_id):
            return False

        # Platform admins and workspace owners have all project permissions
        user = await self._get_user(user_id)
        if not user:
            return False

        if user.is_super_admin or user.role == UserRole.WORKSPACE_OWNER.value:
            return True

        # Check specific permission
        # For now, workspace members have read-only access
        if permission == Permission.PROJECT_READ:
            return True

        return False

    async def get_user_projects(
        self,
        user_id: str,
        workspace_id: Optional[str] = None
    ) -> List[Project]:
        """Get projects accessible by user.

        Args:
            user_id: User ID
            workspace_id: Optional workspace filter

        Returns:
            List of accessible projects
        """
        user = await self._get_user(user_id)
        if not user:
            return []

        # Platform admins see all projects
        if user.is_super_admin:
            query = select(Project)
            if workspace_id:
                query = query.where(Project.workspace_id == workspace_id)
        else:
            # Regular users see their workspace projects
            query = select(Project).where(
                Project.workspace_id == user.workspace_id
            )

        result = await self.session.execute(query)
        return list(result.scalars().all())

    # ==========================================
    # Layer 3: Agent Toolkit Permissions
    # ==========================================

    async def check_agent_tool_permission(
        self,
        agent_id: str,
        tool_name: str,
        permission: str
    ) -> bool:
        """Check if agent has permission to use specific tool.

        Args:
            agent_id: Agent ID
            tool_name: Tool name (e.g., "gmail")
            permission: Required permission (e.g., "send_emails")

        Returns:
            True if agent has permission
        """
        # Get agent
        result = await self.session.execute(
            select(Agent).where(Agent.id == agent_id)
        )
        agent = result.scalar_one_or_none()
        if not agent:
            return False

        # Check if agent has toolkit configured
        if not agent.toolkit:
            return False

        toolkit = agent.toolkit
        tools = toolkit.get("tools", [])

        # Find tool in toolkit
        for tool in tools:
            if tool.get("name") == tool_name:
                # Check if permission is in tool's permissions list
                tool_permissions = tool.get("permissions", [])
                return permission in tool_permissions

        # Check if inheriting project-level tools
        if toolkit.get("inherit_project_tools", False):
            # Check project-level tool enablement
            result = await self.session.execute(
                select(ProjectTool).where(
                    ProjectTool.project_id == agent.project_id,
                    ProjectTool.tool_name == tool_name,
                    ProjectTool.enabled == True
                )
            )
            project_tool = result.scalar_one_or_none()
            if project_tool:
                # Project-level tool grants all permissions
                return True

        return False

    async def get_agent_tools(self, agent_id: str) -> List[str]:
        """Get list of tools available to agent.

        Args:
            agent_id: Agent ID

        Returns:
            List of tool names
        """
        result = await self.session.execute(
            select(Agent).where(Agent.id == agent_id)
        )
        agent = result.scalar_one_or_none()
        if not agent or not agent.toolkit:
            return []

        toolkit = agent.toolkit
        tools = toolkit.get("tools", [])
        tool_names = [tool.get("name") for tool in tools]

        # Add inherited project tools
        if toolkit.get("inherit_project_tools", False):
            result = await self.session.execute(
                select(ProjectTool.tool_name).where(
                    ProjectTool.project_id == agent.project_id,
                    ProjectTool.enabled == True
                )
            )
            project_tools = result.scalars().all()
            tool_names.extend(project_tools)

        return list(set(tool_names))  # Deduplicate

    async def get_agent_tool_permissions(
        self,
        agent_id: str,
        tool_name: str
    ) -> Set[str]:
        """Get all permissions agent has for a specific tool.

        Args:
            agent_id: Agent ID
            tool_name: Tool name

        Returns:
            Set of permissions
        """
        result = await self.session.execute(
            select(Agent).where(Agent.id == agent_id)
        )
        agent = result.scalar_one_or_none()
        if not agent or not agent.toolkit:
            return set()

        toolkit = agent.toolkit
        tools = toolkit.get("tools", [])

        # Find tool permissions
        for tool in tools:
            if tool.get("name") == tool_name:
                return set(tool.get("permissions", []))

        # Check inherited project tools (all permissions)
        if toolkit.get("inherit_project_tools", False):
            result = await self.session.execute(
                select(ProjectTool).where(
                    ProjectTool.project_id == agent.project_id,
                    ProjectTool.tool_name == tool_name,
                    ProjectTool.enabled == True
                )
            )
            if result.scalar_one_or_none():
                # Project-level tools grant all permissions
                # Return a wildcard or specific permission set
                return {"*"}  # Wildcard for all permissions

        return set()

    # ==========================================
    # Helper Methods
    # ==========================================

    async def can_configure_agent(self, user_id: str, agent_id: str) -> bool:
        """Check if user can configure agent toolkit.

        Args:
            user_id: User ID
            agent_id: Agent ID

        Returns:
            True if user can configure
        """
        # Get agent
        result = await self.session.execute(
            select(Agent).where(Agent.id == agent_id)
        )
        agent = result.scalar_one_or_none()
        if not agent:
            return False

        # Check project access with write permission
        return await self.check_project_access(
            user_id,
            agent.project_id,
            Permission.PROJECT_WRITE
        )


# Dependency injection helper
async def get_permission_checker(session: AsyncSession) -> ThreeTierPermissionChecker:
    """Get permission checker instance.

    Args:
        session: Database session

    Returns:
        ThreeTierPermissionChecker instance
    """
    return ThreeTierPermissionChecker(session)
