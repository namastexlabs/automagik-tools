"""
Tool Activation Logic.

Handles the "App Store" logic:
- Listing available tools with their installation status for a specific user.
- Determining what is needed to activate a tool (OAuth, API Key, etc.).
- Handling the activation process.
"""
from typing import List, Dict, Any, Optional
from sqlalchemy import select
from .database import get_db_session
from .models import ToolRegistry, UserTool, ToolConfig, OAuthToken
from .registry import list_available_tools, get_tool_metadata
from .auth.google.oauth_config import get_auth_url as get_google_auth_url

class ToolActivator:
    @staticmethod
    async def get_catalog(user_id: str) -> List[Dict[str, Any]]:
        """
        Get the full tool catalog with status for a specific user.
        
        Returns:
            List of tools with 'status': 'active', 'missing_config', 'not_installed'
        """
        # Get all available tools from registry
        available_tools = await list_available_tools()
        
        async with get_db_session() as session:
            # Get user's installed tools
            result = await session.execute(
                select(UserTool).where(UserTool.user_id == user_id)
            )
            user_tools = {ut.tool_name: ut for ut in result.scalars().all()}
            
            # Get user's configs to check for missing keys
            result = await session.execute(
                select(ToolConfig).where(ToolConfig.user_id == user_id)
            )
            user_configs = {}
            for config in result.scalars().all():
                if config.tool_name not in user_configs:
                    user_configs[config.tool_name] = set()
                user_configs[config.tool_name].add(config.config_key)
                
            # Get user's oauth tokens
            result = await session.execute(
                select(OAuthToken).where(OAuthToken.user_id == user_id)
            )
            user_tokens = {ot.tool_name: ot for ot in result.scalars().all()}

        catalog = []
        for tool in available_tools:
            tool_name = tool["tool_name"]
            status = "not_installed"
            missing_requirements = []
            
            is_installed = tool_name in user_tools and user_tools[tool_name].enabled
            
            if is_installed:
                # Check if config is complete
                required_config = tool.get("required_config", [])
                existing_config_keys = user_configs.get(tool_name, set())
                missing_config = [k for k in required_config if k not in existing_config_keys]
                
                # Check if oauth is complete
                # For now, we assume if auth_type is oauth, we need a token
                # But registry might not have auth_type populated for all yet if we didn't re-run discovery
                # We rely on the new auth_type field
                auth_type = tool.get("auth_type", "none")
                missing_oauth = False
                if auth_type == "oauth":
                    if tool_name not in user_tokens:
                        missing_oauth = True
                
                if missing_config or missing_oauth:
                    status = "missing_config"
                    if missing_config:
                        missing_requirements.append({"type": "config", "keys": missing_config})
                    if missing_oauth:
                        missing_requirements.append({"type": "oauth", "provider": "google"}) # TODO: Dynamic provider
                else:
                    status = "active"
            
            catalog_item = {
                **tool,
                "status": status,
                "missing_requirements": missing_requirements
            }
            catalog.append(catalog_item)
            
        return catalog

    @staticmethod
    async def get_activation_requirements(tool_name: str) -> Dict[str, Any]:
        """
        Get requirements to activate a tool.
        """
        metadata = await get_tool_metadata(tool_name)
        if not metadata:
            raise ValueError(f"Tool {tool_name} not found")
            
        auth_type = metadata.get("auth_type", "none")
        config_schema = metadata.get("config_schema", {})
        
        requirements = {
            "tool_name": tool_name,
            "auth_type": auth_type,
            "config_schema": config_schema
        }
        
        if auth_type == "oauth":
            # TODO: Support multiple providers. For now, hardcode Google for PoC if it looks like google
            # Or use metadata to determine provider
            if "google" in tool_name or "calendar" in tool_name:
                requirements["oauth_url"] = get_google_auth_url()
                requirements["oauth_provider"] = "google"
        
        return requirements

    @staticmethod
    async def complete_activation(user_id: str, tool_name: str, config_data: Dict[str, Any]) -> str:
        """
        Complete activation by saving config and enabling tool.
        """
        from .tools import update_tool_config, add_tool
        from fastmcp import Context # Mock context or create a minimal one
        
        # We need to call add_tool to ensure UserTool record exists
        # But add_tool requires Context. We might need to refactor add_tool or create a context.
        # For now, let's use the DB directly or refactor tools.py to separate logic from Context.
        # Actually, tools.py functions expect Context mainly for user_id.
        # If we refactor tools.py to accept user_id optionally, we can reuse them.
        
        # Let's assume we can use internal helpers if we move logic out of tools.py
        # But for now, I'll duplicate the DB logic here or use a helper if available.
        
        async with get_db_session() as session:
            # 1. Ensure UserTool exists
            result = await session.execute(
                select(UserTool).where(UserTool.user_id == user_id, UserTool.tool_name == tool_name)
            )
            user_tool = result.scalar_one_or_none()
            
            if not user_tool:
                user_tool = UserTool(user_id=user_id, tool_name=tool_name, enabled=True)
                session.add(user_tool)
            else:
                user_tool.enabled = True
            
            # 2. Save Config
            # Remove existing configs for this tool to avoid duplicates/stale data? 
            # Or just upsert.
            # Let's upsert provided keys.
            for key, value in config_data.items():
                # Check existing
                result = await session.execute(
                    select(ToolConfig).where(
                        ToolConfig.user_id == user_id,
                        ToolConfig.tool_name == tool_name,
                        ToolConfig.config_key == key
                    )
                )
                existing_config = result.scalar_one_or_none()
                
                if existing_config:
                    existing_config.config_value = str(value) # Store as string/JSON
                else:
                    new_config = ToolConfig(
                        user_id=user_id,
                        tool_name=tool_name,
                        config_key=key,
                        config_value=str(value)
                    )
                    session.add(new_config)
            
            await session.commit()
            
        return "Activation successful"
