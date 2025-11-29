"""
Main hub server that composes all automagik tools using FastMCP mount pattern
with automatic discovery of all tools in the tools directory.

Supports mounting:
- Local tools from automagik_tools/tools/
- Remote stdio MCP servers
- Remote HTTP MCP servers
"""

from fastmcp import FastMCP, Client
from fastmcp.server.middleware import (
    ErrorHandlingMiddleware,
    LoggingMiddleware,
    RateLimitingMiddleware,
    TimingMiddleware,
)
import importlib
import importlib.metadata
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv
import os
import json

# Load environment variables from .env file
load_dotenv()


def discover_and_load_tools() -> Dict[str, Any]:
    """
    Automatically discover all tools in the tools directory.
    Each tool must have:
    - get_metadata() function
    - get_config_class() function
    - create_server() function
    """
    tools = {}

    # Find the tools directory
    tools_dir = Path(__file__).parent / "tools"

    # Discover tools via entry points first (installed tools)
    try:
        entry_points = importlib.metadata.entry_points()
        if hasattr(entry_points, "select"):
            tool_entry_points = entry_points.select(group="automagik_tools.plugins")
        else:
            tool_entry_points = entry_points.get("automagik_tools.plugins", [])

        for ep in tool_entry_points:
            try:
                # Get the module name from the entry point
                module_name = ep.value.split(":")[0]
                module = importlib.import_module(module_name)

                if hasattr(module, "get_metadata"):
                    metadata = module.get_metadata()
                    tools[metadata["name"]] = {
                        "module": module,
                        "metadata": metadata,
                        "source": "entry_point",
                    }
                    print(f"📦 Discovered {metadata['name']} via entry point")
            except Exception as e:
                print(f"⚠️  Failed to load entry point {ep.name}: {e}")
    except Exception as e:
        print(f"⚠️  Error discovering entry points: {e}")

    # Also scan the tools directory for any tools not in entry points
    if tools_dir.exists():
        for tool_path in tools_dir.iterdir():
            if tool_path.is_dir() and not tool_path.name.startswith("_"):
                tool_name = tool_path.name

                # Skip if already loaded via entry point
                if any(
                    t.get("metadata", {}).get("name") == tool_name
                    for t in tools.values()
                ):
                    continue

                try:
                    # Import the tool module
                    module_name = f"automagik_tools.tools.{tool_name}"
                    module = importlib.import_module(module_name)

                    # Check if it has required functions
                    if (
                        hasattr(module, "get_metadata")
                        and hasattr(module, "get_config_class")
                        and hasattr(module, "create_server")
                    ):

                        metadata = module.get_metadata()
                        tools[metadata["name"]] = {
                            "module": module,
                            "metadata": metadata,
                            "source": "directory",
                        }
                        print(f"📂 Discovered {metadata['name']} via directory scan")
                except Exception as e:
                    print(f"⚠️  Failed to load tool {tool_name}: {e}")

    return tools


def load_external_mcp_servers() -> Dict[str, Dict[str, Any]]:
    """
    Load external MCP server configurations from environment variables.

    Expects MCP_SERVERS_CONFIG environment variable with JSON format:
    {
        "server_name": {
            "type": "stdio",
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path"],
            "env": {"KEY": "value"}  # optional
        },
        "another_server": {
            "type": "http",
            "url": "http://localhost:8884/mcp"
        }
    }
    """
    external_servers = {}

    config_json = os.getenv("MCP_SERVERS_CONFIG")
    if not config_json:
        return external_servers

    try:
        config = json.loads(config_json)
        for server_name, server_config in config.items():
            external_servers[server_name] = {
                "config": server_config,
                "source": "external_mcp",
            }
            print(f"🌐 Discovered external MCP server: {server_name}")
    except json.JSONDecodeError as e:
        print(f"⚠️  Failed to parse MCP_SERVERS_CONFIG: {e}")
    except Exception as e:
        print(f"⚠️  Error loading external MCP servers: {e}")

    return external_servers


async def create_proxy_server(server_name: str, server_config: Dict[str, Any]) -> Optional[FastMCP]:
    """
    Create a proxy server for an external MCP server (stdio or HTTP).

    Args:
        server_name: Name for the mounted server
        server_config: Configuration dict with 'type' and connection details

    Returns:
        FastMCP proxy server or None if creation fails
    """
    try:
        server_type = server_config.get("type")

        if server_type == "stdio":
            # Create stdio client
            from mcp.client.stdio import StdioServerParameters, stdio_client

            command = server_config.get("command")
            args = server_config.get("args", [])
            env = server_config.get("env")

            if not command:
                print(f"⚠️  No command specified for stdio server {server_name}")
                return None

            # Create server parameters
            server_params = StdioServerParameters(
                command=command,
                args=args,
                env=env
            )

            # Create client and proxy
            read, write = await stdio_client(server_params)
            client = Client(read, write)

            proxy = FastMCP.as_proxy(client, name=server_name)
            return proxy

        elif server_type == "http":
            # Create HTTP client
            url = server_config.get("url")

            if not url:
                print(f"⚠️  No URL specified for HTTP server {server_name}")
                return None

            client = Client(url)
            proxy = FastMCP.as_proxy(client, name=server_name)
            return proxy

        else:
            print(f"⚠️  Unknown server type '{server_type}' for {server_name}")
            return None

    except Exception as e:
        print(f"❌ Failed to create proxy for {server_name}: {e}")
        return None


async def create_hub_server() -> FastMCP:
    """
    Create the main hub server that automatically discovers and mounts all tools.
    Supports:
    - Local tools from automagik_tools/tools/ directory
    - External stdio MCP servers via MCP_SERVERS_CONFIG
    - External HTTP MCP servers via MCP_SERVERS_CONFIG
    """
    # Discover local tools
    discovered_tools = discover_and_load_tools()

    # Discover external MCP servers
    external_servers = load_external_mcp_servers()

    # Build instructions dynamically
    tool_list = []
    for name, info in discovered_tools.items():
        desc = info["metadata"].get("description", "No description")
        mount_name = info["metadata"]["name"].replace("-", "_")
        tool_list.append(f"- {mount_name}_* - {desc}")

    for server_name in external_servers.keys():
        mount_name = server_name.replace("-", "_")
        tool_list.append(f"- {mount_name}_* - External MCP server")

    instructions = f"""
    This is the main hub for all Automagik tools. Each tool is mounted
    under its own prefix. Available tools:
    {chr(10).join(tool_list)}
    """

    # Create the main hub with recommended path format for resource prefixes
    hub = FastMCP(
        name="Automagik Tools Hub",
        instructions=instructions,
        resource_prefix_format="path",  # Use recommended path format
    )

    # Add production middleware for monitoring, error handling, and rate limiting
    hub.add_middleware(ErrorHandlingMiddleware(include_traceback=True))
    hub.add_middleware(RateLimitingMiddleware(max_requests_per_second=50))
    hub.add_middleware(TimingMiddleware())
    hub.add_middleware(LoggingMiddleware(include_payloads=False))  # Set True for debugging

    # Mount each discovered tool
    mounted_tools = []
    for tool_name, tool_info in discovered_tools.items():
        try:
            module = tool_info["module"]
            metadata = tool_info["metadata"]

            # Get the config class and create config
            config_class = module.get_config_class()
            config = config_class()

            # Check if tool is properly configured (optional)
            is_configured = True
            if hasattr(config, "api_key") and not config.api_key:
                print(f"⚠️  {tool_name} not configured (missing API key)")
                is_configured = False

            # Create and mount the server
            server = module.create_server(config)

            # Use the tool name from metadata as mount point (no leading slash)
            mount_name = metadata["name"].replace("-", "_")

            # Check if server has custom lifespan to determine proxy mounting
            has_custom_lifespan = (
                hasattr(server, "_lifespan") and server._lifespan is not None
            )

            # Mount with proper syntax and consider proxy mounting
            if has_custom_lifespan:
                hub.mount(server=server, prefix=mount_name, as_proxy=True)
            else:
                hub.mount(server=server, prefix=mount_name)

            status = "✅" if is_configured else "⚠️"
            mounted_tools.append(mount_name)
            print(f"{status} Mounted {metadata['name']} at prefix '{mount_name}'")

        except Exception as e:
            print(f"❌ Failed to mount {tool_name}: {e}")

    # Mount external MCP servers as proxies
    for server_name, server_info in external_servers.items():
        try:
            server_config = server_info["config"]
            proxy_server = await create_proxy_server(server_name, server_config)

            if proxy_server:
                mount_name = server_name.replace("-", "_")
                hub.mount(server=proxy_server, prefix=mount_name, as_proxy=True)
                mounted_tools.append(mount_name)
                print(f"🌐 Mounted external MCP server '{server_name}' at prefix '{mount_name}'")
            else:
                print(f"⚠️  Failed to create proxy for {server_name}")

        except Exception as e:
            print(f"❌ Failed to mount external server {server_name}: {e}")

    # Add hub-level tools
    @hub.tool()
    async def list_mounted_tools() -> str:
        """List all tools mounted in this hub"""
        lines = ["Available tools in this hub:"]
        for mount_name in mounted_tools:
            lines.append(f"- {mount_name}: Use tools with prefix '{mount_name}_'")
        lines.append(
            "\nExample: 'evolution_api_send_text_message' or 'example_hello_say_hello'"
        )
        return "\n".join(lines)

    @hub.tool()
    async def hub_info() -> Dict[str, Any]:
        """Get detailed information about the hub and available tools"""
        return {
            "hub_name": "Automagik Tools Hub",
            "mounted_tools": mounted_tools,
            "discovered_tools": len(discovered_tools),
            "tool_details": {
                name: {
                    "description": info["metadata"].get("description"),
                    "version": info["metadata"].get("version", "unknown"),
                    "author": info["metadata"].get("author", "unknown"),
                    "source": info["source"],
                }
                for name, info in discovered_tools.items()
            },
        }

    # Add hub-level resource
    @hub.resource("hub://status")
    async def hub_status() -> str:
        """Get the status of the hub and mounted tools"""
        status = ["Automagik Tools Hub Status", "=" * 40]
        status.append(f"Total tools discovered: {len(discovered_tools)}")
        status.append(f"Successfully mounted: {len(mounted_tools)}")
        status.append("")

        for tool_name, tool_info in discovered_tools.items():
            metadata = tool_info["metadata"]
            mount_name = metadata["name"].replace("-", "_")

            if mount_name in mounted_tools:
                # Check if configured
                try:
                    module = tool_info["module"]
                    config_class = module.get_config_class()
                    config = config_class()

                    if hasattr(config, "api_key") and config.api_key:
                        status.append(f"✅ {metadata['name']}: Configured and mounted")
                    elif hasattr(config, "api_key"):
                        status.append(
                            f"⚠️  {metadata['name']}: Mounted but not configured"
                        )
                    else:
                        status.append(
                            f"✅ {metadata['name']}: Mounted (no config needed)"
                        )
                except Exception:
                    status.append(f"⚠️  {metadata['name']}: Mounted with errors")
            else:
                status.append(f"❌ {metadata['name']}: Failed to mount")

        return "\n".join(status)

    @hub.resource("hub://tools")
    async def list_all_tools() -> str:
        """List all discovered tools with their metadata"""
        lines = ["Discovered Tools", "=" * 40]

        for tool_name, tool_info in discovered_tools.items():
            metadata = tool_info["metadata"]
            lines.append(f"\n{metadata['name']}:")
            lines.append(f"  Description: {metadata.get('description', 'N/A')}")
            lines.append(f"  Version: {metadata.get('version', 'N/A')}")
            lines.append(f"  Category: {metadata.get('category', 'N/A')}")
            lines.append(f"  Source: {tool_info['source']}")

            if "tags" in metadata:
                lines.append(f"  Tags: {', '.join(metadata['tags'])}")

        return "\n".join(lines)

    return hub


# Allow running directly with FastMCP
if __name__ == "__main__":
    import asyncio
    hub = asyncio.run(create_hub_server())
    hub.run(show_banner=False)
