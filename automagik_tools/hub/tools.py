"""Hub management tools for users to add/remove/configure tools."""
import json
import uuid
from typing import Any, Dict, List
from fastmcp import Context
from fastmcp.exceptions import ToolError
from sqlalchemy import select
from .database import get_db_session
from .models import UserTool, ToolConfig, ToolRegistry


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
    Add a tool to your personal collection.

    Args:
        tool_name: Name of the tool to add
        config: Configuration dictionary for the tool
        ctx: FastMCP context (provides user_id)

    Returns:
        Success message
    """
    # In a real scenario, we'd get the user from the context
    # For now, we'll assume a default user or extract from context if available
    # user_id = ctx.request.state.user["id"] if hasattr(ctx.request.state, "user") else "default_user"
    
    # Since FastMCP context might not have user state directly accessible in the same way as FastAPI request
    # We might need to rely on the dependency injection in the HTTP layer to pass user info
    # But for this tool function signature, we'll assume the user_id is passed or available
    
    # TODO: Proper user extraction from context
    user_id = "default_user" 
    if ctx and hasattr(ctx, "session") and ctx.session.get("user_id"):
         user_id = ctx.session.get("user_id")

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

        # Add or enable tool for user
        result = await session.execute(
            select(UserTool).where(
                UserTool.user_id == user_id,
                UserTool.tool_name == tool_name
            )
        )
        user_tool = result.scalar_one_or_none()

        if user_tool:
            user_tool.enabled = True
        else:
            user_tool = UserTool(
                id=str(uuid.uuid4()),
                user_id=user_id,
                tool_name=tool_name,
                enabled=True
            )
            session.add(user_tool)

        # Store configuration
        for key, value in config.items():
            result = await session.execute(
                select(ToolConfig).where(
                    ToolConfig.user_id == user_id,
                    ToolConfig.tool_name == tool_name,
                    ToolConfig.config_key == key
                )
            )
            config_entry = result.scalar_one_or_none()

            if config_entry:
                config_entry.config_value = json.dumps(value)
            else:
                config_entry = ToolConfig(
                    id=str(uuid.uuid4()),
                    user_id=user_id,
                    tool_name=tool_name,
                    config_key=key,
                    config_value=json.dumps(value)
                )
                session.add(config_entry)

        await session.commit()

    return f"✅ Tool '{tool_name}' added successfully! It's now available for use."


async def remove_tool(tool_name: str, ctx: Context) -> str:
    """
    Remove a tool from your personal collection.

    Args:
        tool_name: Name of the tool to remove
        ctx: FastMCP context (provides user_id)

    Returns:
        Success message
    """
    # TODO: Proper user extraction
    user_id = "default_user"
    if ctx and hasattr(ctx, "session") and ctx.session.get("user_id"):
         user_id = ctx.session.get("user_id")

    async with get_db_session() as session:
        # Disable tool (soft delete)
        result = await session.execute(
            select(UserTool).where(
                UserTool.user_id == user_id,
                UserTool.tool_name == tool_name
            )
        )
        user_tool = result.scalar_one_or_none()

        if not user_tool:
            raise ToolError(f"Tool '{tool_name}' not found in your collection")

        user_tool.enabled = False
        await session.commit()

    return f"✅ Tool '{tool_name}' removed from your collection."


async def list_my_tools(ctx: Context) -> List[Dict[str, Any]]:
    """
    List all tools in your personal collection.

    Args:
        ctx: FastMCP context (provides user_id)

    Returns:
        List of enabled tools
    """
    # TODO: Proper user extraction
    user_id = "default_user"
    if ctx and hasattr(ctx, "session") and ctx.session.get("user_id"):
         user_id = ctx.session.get("user_id")

    async with get_db_session() as session:
        result = await session.execute(
            select(UserTool, ToolRegistry)
            .join(ToolRegistry, UserTool.tool_name == ToolRegistry.tool_name)
            .where(UserTool.user_id == user_id, UserTool.enabled == True)
        )

        tools = []
        for user_tool, registry_entry in result:
            tools.append({
                "name": user_tool.tool_name,
                "display_name": registry_entry.display_name,
                "description": registry_entry.description,
                "category": registry_entry.category,
                "added_at": user_tool.created_at.isoformat(),
            })

        return tools


async def get_tool_config(tool_name: str, ctx: Context) -> Dict[str, Any]:
    """
    Get current configuration for a tool in your collection.

    Args:
        tool_name: Name of the tool
        ctx: FastMCP context (provides user_id)

    Returns:
        Configuration dictionary
    """
    # TODO: Proper user extraction
    user_id = "default_user"
    if ctx and hasattr(ctx, "session") and ctx.session.get("user_id"):
         user_id = ctx.session.get("user_id")

    async with get_db_session() as session:
        result = await session.execute(
            select(ToolConfig).where(
                ToolConfig.user_id == user_id,
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
    Update configuration for a tool in your collection.

    Args:
        tool_name: Name of the tool
        config: New configuration dictionary (partial updates allowed)
        ctx: FastMCP context (provides user_id)

    Returns:
        Success message
    """
    # TODO: Proper user extraction
    user_id = "default_user"
    if ctx and hasattr(ctx, "session") and ctx.session.get("user_id"):
         user_id = ctx.session.get("user_id")

    async with get_db_session() as session:
        # Verify tool is enabled for user
        result = await session.execute(
            select(UserTool).where(
                UserTool.user_id == user_id,
                UserTool.tool_name == tool_name,
                UserTool.enabled == True
            )
        )
        if not result.scalar_one_or_none():
            raise ToolError(f"Tool '{tool_name}' not found in your collection")

        # Update configuration
        for key, value in config.items():
            result = await session.execute(
                select(ToolConfig).where(
                    ToolConfig.user_id == user_id,
                    ToolConfig.tool_name == tool_name,
                    ToolConfig.config_key == key
                )
            )
            config_entry = result.scalar_one_or_none()

            if config_entry:
                config_entry.config_value = json.dumps(value)
            else:
                config_entry = ToolConfig(
                    id=str(uuid.uuid4()),
                    user_id=user_id,
                    tool_name=tool_name,
                    config_key=key,
                    config_value=json.dumps(value)
                )
                session.add(config_entry)

        await session.commit()

    return f"✅ Configuration for '{tool_name}' updated successfully."


async def get_missing_config(tool_name: str, ctx: Context) -> List[str]:
    """
    Identify missing required configuration keys for a tool.
    
    Args:
        tool_name: Name of the tool
        ctx: FastMCP context (provides user_id)
        
    Returns:
        List of missing configuration keys
    """
    # TODO: Proper user extraction
    user_id = "default_user"
    if ctx and hasattr(ctx, "session") and ctx.session.get("user_id"):
         user_id = ctx.session.get("user_id")

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
            
        # Get current config
        result = await session.execute(
            select(ToolConfig).where(
                ToolConfig.user_id == user_id,
                ToolConfig.tool_name == tool_name
            )
        )
        configs = result.scalars().all()
        existing_keys = {config.config_key for config in configs}
        
        missing = [key for key in required_keys if key not in existing_keys]
        return missing
