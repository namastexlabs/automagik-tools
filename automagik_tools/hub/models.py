"""Database models for multi-tenant Hub.

Multi-Tenancy Model:
- Each User owns exactly one Workspace (created on signup)
- All tools, configs, and credentials are scoped to the Workspace
- Super admins can access all workspaces
- WorkOS Organization ID maps 1:1 with Workspace

Hierarchy:
  Platform (Super Admin only)
    └── Workspace (per user)
         ├── Tools
         ├── Configs
         └── Credentials
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import String, Boolean, Text, JSON, ForeignKey, Index, DateTime, Enum
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
import enum


class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


class UserRole(str, enum.Enum):
    """User roles for authorization."""
    SUPER_ADMIN = "super_admin"      # Platform-level admin (only you)
    WORKSPACE_OWNER = "workspace_owner"  # Default for all users
    WORKSPACE_MEMBER = "workspace_member"  # Future: invited team members
    WORKSPACE_VIEWER = "workspace_viewer"  # Future: read-only access


class ProvisioningMethod(str, enum.Enum):
    """How the user was created."""
    MANUAL = "manual"           # Self-signup via AuthKit
    DIRECTORY_SYNC = "directory_sync"  # Auto-provisioned from Google Workspace
    INVITATION = "invitation"   # Invited by another user


class Workspace(Base):
    """Workspace - tenant isolation unit.

    Each user gets their own workspace on signup.
    All tools and credentials are scoped to the workspace.
    Maps 1:1 with WorkOS Organization.
    """
    __tablename__ = "workspaces"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)  # URL-safe identifier
    owner_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)  # Nullable for initial creation
    workos_org_id: Mapped[Optional[str]] = mapped_column(String(100), unique=True)  # WorkOS Organization ID
    settings: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    owner: Mapped[Optional["User"]] = relationship(back_populates="owned_workspace", foreign_keys="Workspace.owner_id")
    members: Mapped[List["User"]] = relationship(
        back_populates="workspace",
        foreign_keys="User.workspace_id",
        cascade="all, delete-orphan"
    )
    tools: Mapped[List["UserTool"]] = relationship(back_populates="workspace", cascade="all, delete-orphan")
    configs: Mapped[List["ToolConfig"]] = relationship(back_populates="workspace", cascade="all, delete-orphan")
    oauth_tokens: Mapped[List["OAuthToken"]] = relationship(back_populates="workspace", cascade="all, delete-orphan")
    audit_logs: Mapped[List["AuditLog"]] = relationship(back_populates="workspace", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_workspaces_owner", "owner_id"),
        Index("idx_workspaces_workos_org", "workos_org_id"),
    )


class User(Base):
    """User accounts authenticated via AuthKit.

    Users are members of exactly one workspace (their own by default).
    Super admins can access all workspaces.
    """
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)  # WorkOS User ID
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    first_name: Mapped[Optional[str]] = mapped_column(String(255))
    last_name: Mapped[Optional[str]] = mapped_column(String(255))

    # Multi-tenancy fields
    workspace_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("workspaces.id", ondelete="SET NULL"))
    role: Mapped[str] = mapped_column(String(50), default=UserRole.WORKSPACE_OWNER.value)
    is_super_admin: Mapped[bool] = mapped_column(Boolean, default=False)

    # Directory Sync fields
    directory_sync_id: Mapped[Optional[str]] = mapped_column(String(100))  # WorkOS Directory Sync User ID
    idp_id: Mapped[Optional[str]] = mapped_column(String(255))  # Identity Provider ID (e.g., Google user ID)
    provisioned_via: Mapped[str] = mapped_column(String(50), default=ProvisioningMethod.MANUAL.value)

    # MFA status
    mfa_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    mfa_grace_period_end: Mapped[Optional[datetime]] = mapped_column(DateTime)  # 7-day grace period

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    workspace: Mapped[Optional["Workspace"]] = relationship(
        back_populates="members",
        foreign_keys=[workspace_id]
    )
    owned_workspace: Mapped[Optional["Workspace"]] = relationship(
        back_populates="owner",
        foreign_keys="Workspace.owner_id"
    )
    tools: Mapped[List["UserTool"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    configs: Mapped[List["ToolConfig"]] = relationship(back_populates="user", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_users_workspace", "workspace_id"),
        Index("idx_users_directory_sync", "directory_sync_id"),
        Index("idx_users_idp", "idp_id"),
    )


class UserTool(Base):
    """Tools enabled for each user, scoped to workspace."""
    __tablename__ = "user_tools"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    workspace_id: Mapped[str] = mapped_column(String(36), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    tool_name: Mapped[str] = mapped_column(String(100), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="tools")
    workspace: Mapped["Workspace"] = relationship(back_populates="tools")

    __table_args__ = (
        Index("idx_user_tools_lookup", "user_id", "enabled"),
        Index("idx_user_tools_workspace", "workspace_id", "tool_name"),
        Index("idx_user_tools_unique", "workspace_id", "tool_name", unique=True),
    )


class ToolConfig(Base):
    """Configuration key-value pairs for each user's tool, scoped to workspace."""
    __tablename__ = "tool_configs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    workspace_id: Mapped[str] = mapped_column(String(36), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    tool_name: Mapped[str] = mapped_column(String(100), nullable=False)
    config_key: Mapped[str] = mapped_column(String(100), nullable=False)
    config_value: Mapped[str] = mapped_column(Text, nullable=False)  # JSON string
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="configs")
    workspace: Mapped["Workspace"] = relationship(back_populates="configs")

    __table_args__ = (
        Index("idx_tool_configs_lookup", "user_id", "tool_name"),
        Index("idx_tool_configs_workspace", "workspace_id", "tool_name"),
        Index("idx_tool_configs_unique", "workspace_id", "tool_name", "config_key", unique=True),
    )


class ToolRegistry(Base):
    """Metadata about available tools in the repository."""
    __tablename__ = "tool_registry"

    tool_name: Mapped[str] = mapped_column(String(100), primary_key=True)
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    auth_type: Mapped[str] = mapped_column(String(20), default="none") # oauth, key, none
    config_schema: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    required_oauth: Mapped[Optional[List[str]]] = mapped_column(JSON)
    icon_url: Mapped[Optional[str]] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class OAuthToken(Base):
    """Encrypted OAuth tokens for external tools (e.g., Google, GitHub), scoped to workspace."""
    __tablename__ = "oauth_tokens"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    workspace_id: Mapped[str] = mapped_column(String(36), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    tool_name: Mapped[str] = mapped_column(String(100), nullable=False)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    access_token: Mapped[str] = mapped_column(Text, nullable=False)  # Encrypted
    refresh_token: Mapped[Optional[str]] = mapped_column(Text)       # Encrypted
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    scopes: Mapped[Optional[List[str]]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    workspace: Mapped["Workspace"] = relationship(back_populates="oauth_tokens")

    __table_args__ = (
        Index("idx_oauth_tokens_lookup", "user_id", "tool_name"),
        Index("idx_oauth_tokens_workspace", "workspace_id", "tool_name"),
        Index("idx_oauth_tokens_unique", "workspace_id", "tool_name", "provider", unique=True),
    )


class ToolPreset(Base):
    """Pre-configured tool bundles."""
    __tablename__ = "tool_presets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    preset_name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    tools: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, nullable=False)  # List of {tool_name, config}
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


# ===================================
# Directory Sync Models (Week 3)
# ===================================

class DirectorySyncUser(Base):
    """Users synced from Google Workspace via WorkOS Directory Sync."""
    __tablename__ = "directory_sync_users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)  # WorkOS Directory User ID
    directory_id: Mapped[str] = mapped_column(String(100), nullable=False)  # WorkOS Directory ID
    user_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"))
    idp_id: Mapped[str] = mapped_column(String(255), nullable=False)  # Google Workspace user ID
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    first_name: Mapped[Optional[str]] = mapped_column(String(255))
    last_name: Mapped[Optional[str]] = mapped_column(String(255))
    state: Mapped[str] = mapped_column(String(50), default="active")  # active, suspended, deleted
    raw_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)  # Full WorkOS response
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_dsync_users_directory", "directory_id"),
        Index("idx_dsync_users_email", "email"),
        Index("idx_dsync_users_idp", "idp_id"),
        Index("idx_dsync_users_state", "state"),
    )


class DirectoryGroup(Base):
    """Groups synced from Google Workspace, mapped to roles."""
    __tablename__ = "directory_groups"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)  # WorkOS Directory Group ID
    directory_id: Mapped[str] = mapped_column(String(100), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    idp_id: Mapped[Optional[str]] = mapped_column(String(255))  # Google Workspace group ID
    mapped_role: Mapped[Optional[str]] = mapped_column(String(50))  # Maps to UserRole
    raw_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_directory_groups_directory", "directory_id"),
        Index("idx_directory_groups_name", "name"),
    )


class DirectoryGroupMembership(Base):
    """Tracks which users belong to which directory groups."""
    __tablename__ = "directory_group_memberships"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    group_id: Mapped[str] = mapped_column(String(36), ForeignKey("directory_groups.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("directory_sync_users.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_dgm_group", "group_id"),
        Index("idx_dgm_user", "user_id"),
        Index("idx_dgm_unique", "group_id", "user_id", unique=True),
    )


# ===================================
# Audit Log Models (Week 4)
# ===================================

class AuditEventCategory(str, enum.Enum):
    """Categories of audit events."""
    AUTH = "auth"           # Login, logout, MFA
    TOOL = "tool"           # Tool add, remove, configure, execute
    CREDENTIAL = "credential"  # Credential create, access, delete
    ADMIN = "admin"         # User management, settings changes
    WORKSPACE = "workspace"  # Workspace settings changes


class AuditLog(Base):
    """Compliance audit log for all security-relevant events.

    Logs are scoped to workspace but can also be queried globally by super admins.
    Follows WorkOS Audit Logs event schema for potential future integration.
    """
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    workspace_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("workspaces.id", ondelete="SET NULL"))

    # Event details
    action: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g., "tool.added", "auth.login_succeeded"
    category: Mapped[str] = mapped_column(String(50), nullable=False)  # AuditEventCategory value

    # Actor (who performed the action)
    actor_id: Mapped[Optional[str]] = mapped_column(String(36))  # User ID
    actor_email: Mapped[Optional[str]] = mapped_column(String(255))
    actor_type: Mapped[str] = mapped_column(String(50), default="user")  # user, system, api_key

    # Target (what was affected)
    target_type: Mapped[Optional[str]] = mapped_column(String(50))  # user, tool, credential, workspace
    target_id: Mapped[Optional[str]] = mapped_column(String(255))
    target_name: Mapped[Optional[str]] = mapped_column(String(255))

    # Context
    ip_address: Mapped[Optional[str]] = mapped_column(String(45))  # IPv4 or IPv6
    user_agent: Mapped[Optional[str]] = mapped_column(Text)
    request_id: Mapped[Optional[str]] = mapped_column(String(36))  # X-Request-ID for correlation
    event_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)  # Additional event-specific data

    # Status
    success: Mapped[bool] = mapped_column(Boolean, default=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text)

    # Timestamps
    occurred_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    workspace: Mapped[Optional["Workspace"]] = relationship(back_populates="audit_logs")

    __table_args__ = (
        Index("idx_audit_workspace", "workspace_id"),
        Index("idx_audit_action", "action"),
        Index("idx_audit_category", "category"),
        Index("idx_audit_actor", "actor_id"),
        Index("idx_audit_target", "target_type", "target_id"),
        Index("idx_audit_occurred", "occurred_at"),
        Index("idx_audit_request", "request_id"),
    )
