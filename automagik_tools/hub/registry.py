"""Tool registry for discovering and managing available tools."""
import importlib
import json
from pathlib import Path
from typing import Any, List, Dict, Optional
from sqlalchemy import select
from .database import get_db_session
from .models import ToolRegistry


async def discover_tools() -> List[Dict[str, Any]]:
    """
    Discover all available tools by scanning tools/ directory.

    Returns:
        List of tool metadata dictionaries
    """
    tools = []
    # Go up two levels from automagik_tools/hub/registry.py to automagik_tools/
    tools_dir = Path(__file__).parent.parent / "tools"

    if not tools_dir.exists():
        print(f"Warning: Tools directory not found at {tools_dir}")
        return []

    for tool_path in tools_dir.iterdir():
        if not tool_path.is_dir() or tool_path.name.startswith("_"):
            continue

        try:
            # Import tool module
            module_name = f"automagik_tools.tools.{tool_path.name}"
            tool_module = importlib.import_module(module_name)

            # Get metadata
            if hasattr(tool_module, "get_metadata"):
                metadata = tool_module.get_metadata()
                tools.append({
                    "tool_name": tool_path.name,
                    "display_name": metadata.get("name", tool_path.name),
                    "description": metadata.get("description", ""),
                    "category": metadata.get("category", "general"),
                    "auth_type": metadata.get("auth_type", "none"),
                    "config_schema": metadata.get("config_schema", {}),
                    "required_oauth": metadata.get("required_oauth", []),
                    "icon_url": metadata.get("icon_url"),
                })
        except Exception as e:
            print(f"Warning: Could not load tool {tool_path.name}: {e}")
            continue

    return tools


async def populate_tool_registry():
    """Populate tool registry table with discovered tools."""
    tools = await discover_tools()

    async with get_db_session() as session:
        for tool_data in tools:
            # Check if tool already exists
            result = await session.execute(
                select(ToolRegistry).where(ToolRegistry.tool_name == tool_data["tool_name"])
            )
            existing = result.scalar_one_or_none()

            if existing:
                # Update existing
                for key, value in tool_data.items():
                    setattr(existing, key, value)
            else:
                # Create new
                session.add(ToolRegistry(**tool_data))

        await session.commit()

    print(f"✅ Tool registry populated with {len(tools)} tools")


async def get_tool_metadata(tool_name: str) -> Optional[Dict[str, Any]]:
    """
    Get metadata for a specific tool from registry.

    Args:
        tool_name: Name of the tool

    Returns:
        Tool metadata dictionary or None if not found
    """
    async with get_db_session() as session:
        result = await session.execute(
            select(ToolRegistry).where(ToolRegistry.tool_name == tool_name)
        )
        tool = result.scalar_one_or_none()

        if not tool:
            return None

        return {
            "tool_name": tool.tool_name,
            "display_name": tool.display_name,
            "description": tool.description,
            "category": tool.category,
            "auth_type": tool.auth_type,
            "config_schema": tool.config_schema,
            "required_oauth": tool.required_oauth,
            "icon_url": tool.icon_url,
        }


async def list_available_tools() -> List[Dict[str, Any]]:
    """
    List all tools available in the registry.

    Returns:
        List of tool metadata dictionaries
    """
    async with get_db_session() as session:
        result = await session.execute(select(ToolRegistry))
        tools = result.scalars().all()

        return [
            {
                "tool_name": tool.tool_name,
                "display_name": tool.display_name,
                "description": tool.description,
                "category": tool.category,
                "auth_type": tool.auth_type,
                "required_config": list(tool.config_schema.get("required", [])) if isinstance(tool.config_schema, dict) else [],
            }
            for tool in tools
        ]
