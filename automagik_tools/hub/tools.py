"""Hub management tools for users to add/remove/configure tools.

All tools are scoped to the user's workspace for multi-tenant isolation.
"""
import json
import uuid
from typing import Any, Dict, List
from fastmcp import Context
from fastmcp.exceptions import ToolError
from sqlalchemy import select
from .database import get_db_session
from .models import UserTool, ToolConfig, ToolRegistry


def _get_user_workspace(ctx: Context) -> tuple[str, str]:
    """Extract user_id and workspace_id from context.

    Args:
        ctx: FastMCP context

    Returns:
        Tuple of (user_id, workspace_id)

    Raises:
        ToolError: If user is not authenticated
    """
    user_id = None
    workspace_id = None

    if ctx:
        # Try state (set by middleware)
        user_id = ctx.get_state("user_id")
        workspace_id = ctx.get_state("workspace_id")

        # Legacy: try session
        if not user_id and hasattr(ctx, "session"):
            user_id = ctx.session.get("user_id")
            workspace_id = ctx.session.get("workspace_id")

    if not user_id:
        raise ToolError("Authentication required. Please log in first.")

    if not workspace_id:
        raise ToolError("No workspace found. Please contact support.")

    return user_id, workspace_id


async def get_available_tools() -> List[Dict[str, Any]]:
    """
    List all tools available in the repository.

    Returns a list of tools with basic metadata that users can add to their collection.
    """
    from .registry import list_available_tools
    return await list_available_tools()


async def get_tool_metadata(tool_name: str) -> Dict[str, Any]:
    """
    Get detailed metadata and configuration schema for a specific tool.

    Args:
        tool_name: Name of the tool

    Returns:
        Tool metadata including configuration schema
    """
    from .registry import get_tool_metadata as get_meta

    metadata = await get_meta(tool_name)
    if not metadata:
        raise ToolError(f"Tool '{tool_name}' not found in registry")

    return metadata


async def add_tool(
    tool_name: str,
    config: Dict[str, Any],
    ctx: Context
) -> str:
    """
    Add a tool to your workspace.

    Args:
        tool_name: Name of the tool to add
        config: Configuration dictionary for the tool
        ctx: FastMCP context (provides user_id and workspace_id)

    Returns:
        Success message
    """
    user_id, workspace_id = _get_user_workspace(ctx)

    async with get_db_session() as session:
        # Verify tool exists in registry
        result = await session.execute(
            select(ToolRegistry).where(ToolRegistry.tool_name == tool_name)
        )
        tool_meta = result.scalar_one_or_none()
        if not tool_meta:
            raise ToolError(f"Tool '{tool_name}' not found in registry")

        # Validate config against schema (basic validation)
        required_keys = tool_meta.config_schema.get("required", [])
        for key in required_keys:
            if key not in config:
                raise ToolError(f"Missing required config key: {key}")

        # Add or enable tool for workspace
        result = await session.execute(
            select(UserTool).where(
                UserTool.workspace_id == workspace_id,
                UserTool.tool_name == tool_name
            )
        )
        user_tool = result.scalar_one_or_none()

        if user_tool:
            user_tool.enabled = True
            user_tool.user_id = user_id  # Update who last enabled it
        else:
            user_tool = UserTool(
                id=str(uuid.uuid4()),
                user_id=user_id,
                workspace_id=workspace_id,
                tool_name=tool_name,
                enabled=True
            )
            session.add(user_tool)

        # Store configuration (workspace-scoped)
        for key, value in config.items():
            result = await session.execute(
                select(ToolConfig).where(
                    ToolConfig.workspace_id == workspace_id,
                    ToolConfig.tool_name == tool_name,
                    ToolConfig.config_key == key
                )
            )
            config_entry = result.scalar_one_or_none()

            if config_entry:
                config_entry.config_value = json.dumps(value)
                config_entry.user_id = user_id  # Track who last modified
            else:
                config_entry = ToolConfig(
                    id=str(uuid.uuid4()),
                    user_id=user_id,
                    workspace_id=workspace_id,
                    tool_name=tool_name,
                    config_key=key,
                    config_value=json.dumps(value)
                )
                session.add(config_entry)

        await session.commit()

    return f"Tool '{tool_name}' added to your workspace successfully."


async def remove_tool(tool_name: str, ctx: Context) -> str:
    """
    Remove a tool from your workspace.

    Args:
        tool_name: Name of the tool to remove
        ctx: FastMCP context (provides user_id and workspace_id)

    Returns:
        Success message
    """
    user_id, workspace_id = _get_user_workspace(ctx)

    async with get_db_session() as session:
        # Disable tool (soft delete)
        result = await session.execute(
            select(UserTool).where(
                UserTool.workspace_id == workspace_id,
                UserTool.tool_name == tool_name
            )
        )
        user_tool = result.scalar_one_or_none()

        if not user_tool:
            raise ToolError(f"Tool '{tool_name}' not found in your workspace")

        user_tool.enabled = False
        await session.commit()

    return f"Tool '{tool_name}' removed from your workspace."


async def list_my_tools(ctx: Context) -> List[Dict[str, Any]]:
    """
    List all tools in your workspace.

    Args:
        ctx: FastMCP context (provides user_id and workspace_id)

    Returns:
        List of enabled tools
    """
    user_id, workspace_id = _get_user_workspace(ctx)

    async with get_db_session() as session:
        result = await session.execute(
            select(UserTool, ToolRegistry)
            .join(ToolRegistry, UserTool.tool_name == ToolRegistry.tool_name)
            .where(UserTool.workspace_id == workspace_id, UserTool.enabled == True)
        )

        tools = []
        for user_tool, registry_entry in result:
            tools.append({
                "name": user_tool.tool_name,
                "display_name": registry_entry.display_name,
                "description": registry_entry.description,
                "category": registry_entry.category,
                "added_at": user_tool.created_at.isoformat() if user_tool.created_at else None,
            })

        return tools


async def get_tool_config(tool_name: str, ctx: Context) -> Dict[str, Any]:
    """
    Get current configuration for a tool in your workspace.

    Args:
        tool_name: Name of the tool
        ctx: FastMCP context (provides user_id and workspace_id)

    Returns:
        Configuration dictionary
    """
    user_id, workspace_id = _get_user_workspace(ctx)

    async with get_db_session() as session:
        result = await session.execute(
            select(ToolConfig).where(
                ToolConfig.workspace_id == workspace_id,
                ToolConfig.tool_name == tool_name
            )
        )

        configs = result.scalars().all()
        return {
            config.config_key: json.loads(config.config_value)
            for config in configs
        }


async def update_tool_config(
    tool_name: str,
    config: Dict[str, Any],
    ctx: Context
) -> str:
    """
    Update configuration for a tool in your workspace.

    Args:
        tool_name: Name of the tool
        config: New configuration dictionary (partial updates allowed)
        ctx: FastMCP context (provides user_id and workspace_id)

    Returns:
        Success message
    """
    user_id, workspace_id = _get_user_workspace(ctx)

    async with get_db_session() as session:
        # Verify tool is enabled for workspace
        result = await session.execute(
            select(UserTool).where(
                UserTool.workspace_id == workspace_id,
                UserTool.tool_name == tool_name,
                UserTool.enabled == True
            )
        )
        if not result.scalar_one_or_none():
            raise ToolError(f"Tool '{tool_name}' not found in your workspace")

        # Update configuration
        for key, value in config.items():
            result = await session.execute(
                select(ToolConfig).where(
                    ToolConfig.workspace_id == workspace_id,
                    ToolConfig.tool_name == tool_name,
                    ToolConfig.config_key == key
                )
            )
            config_entry = result.scalar_one_or_none()

            if config_entry:
                config_entry.config_value = json.dumps(value)
                config_entry.user_id = user_id  # Track who modified
            else:
                config_entry = ToolConfig(
                    id=str(uuid.uuid4()),
                    user_id=user_id,
                    workspace_id=workspace_id,
                    tool_name=tool_name,
                    config_key=key,
                    config_value=json.dumps(value)
                )
                session.add(config_entry)

        await session.commit()

    return f"Configuration for '{tool_name}' updated successfully."


async def get_missing_config(tool_name: str, ctx: Context) -> List[str]:
    """
    Identify missing required configuration keys for a tool.

    Args:
        tool_name: Name of the tool
        ctx: FastMCP context (provides user_id and workspace_id)

    Returns:
        List of missing configuration keys
    """
    user_id, workspace_id = _get_user_workspace(ctx)

    async with get_db_session() as session:
        # Get tool metadata for schema
        result = await session.execute(
            select(ToolRegistry).where(ToolRegistry.tool_name == tool_name)
        )
        tool_meta = result.scalar_one_or_none()
        if not tool_meta:
            raise ToolError(f"Tool '{tool_name}' not found in registry")

        required_keys = tool_meta.config_schema.get("required", [])
        if not required_keys:
            return []

        # Get current config (workspace-scoped)
        result = await session.execute(
            select(ToolConfig).where(
                ToolConfig.workspace_id == workspace_id,
                ToolConfig.tool_name == tool_name
            )
        )
        configs = result.scalars().all()
        existing_keys = {config.config_key for config in configs}

        missing = [key for key in required_keys if key not in existing_keys]
        return missing
