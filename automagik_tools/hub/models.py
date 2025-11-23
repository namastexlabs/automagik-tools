"""Database models for multi-tenant Hub."""
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import String, Boolean, Text, JSON, ForeignKey, Index, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


class User(Base):
    """User accounts authenticated via AuthKit."""
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)  # WorkOS User ID
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    first_name: Mapped[Optional[str]] = mapped_column(String(255))
    last_name: Mapped[Optional[str]] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    tools: Mapped[List["UserTool"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    configs: Mapped[List["ToolConfig"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class UserTool(Base):
    """Tools enabled for each user."""
    __tablename__ = "user_tools"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    tool_name: Mapped[str] = mapped_column(String(100), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="tools")

    __table_args__ = (
        Index("idx_user_tools_lookup", "user_id", "enabled"),
        Index("idx_user_tools_unique", "user_id", "tool_name", unique=True),
    )


class ToolConfig(Base):
    """Configuration key-value pairs for each user's tool."""
    __tablename__ = "tool_configs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    tool_name: Mapped[str] = mapped_column(String(100), nullable=False)
    config_key: Mapped[str] = mapped_column(String(100), nullable=False)
    config_value: Mapped[str] = mapped_column(Text, nullable=False)  # JSON string
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="configs")

    __table_args__ = (
        Index("idx_tool_configs_lookup", "user_id", "tool_name"),
        Index("idx_tool_configs_unique", "user_id", "tool_name", "config_key", unique=True),
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
    """Encrypted OAuth tokens for external tools (e.g., Google, GitHub)."""
    __tablename__ = "oauth_tokens"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    tool_name: Mapped[str] = mapped_column(String(100), nullable=False)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    access_token: Mapped[str] = mapped_column(Text, nullable=False)  # Encrypted
    refresh_token: Mapped[Optional[str]] = mapped_column(Text)       # Encrypted
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    scopes: Mapped[Optional[List[str]]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_oauth_tokens_lookup", "user_id", "tool_name"),
        Index("idx_oauth_tokens_unique", "user_id", "tool_name", "provider", unique=True),
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
