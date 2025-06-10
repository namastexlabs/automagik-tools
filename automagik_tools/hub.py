"""
Main hub server that composes all automagik tools using FastMCP mount pattern
with automatic discovery of all tools in the tools directory.
"""

from fastmcp import FastMCP
import importlib
import importlib.metadata
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv

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


def create_hub_server() -> FastMCP:
    """
    Create the main hub server that automatically discovers and mounts all tools.
    No manual configuration needed - just add a tool to the tools directory!
    """
    # Discover all available tools
    discovered_tools = discover_and_load_tools()

    # Build instructions dynamically
    tool_list = []
    for name, info in discovered_tools.items():
        desc = info["metadata"].get("description", "No description")
        # Use correct prefix format without leading slash
        mount_name = info["metadata"]["name"].replace("-", "_")
        tool_list.append(f"- {mount_name}_* - {desc}")

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
                hub.mount(mount_name, server, as_proxy=True)
            else:
                hub.mount(mount_name, server)

            status = "✅" if is_configured else "⚠️"
            mounted_tools.append(mount_name)
            print(f"{status} Mounted {metadata['name']} at prefix '{mount_name}'")

        except Exception as e:
            print(f"❌ Failed to mount {tool_name}: {e}")

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
    hub = create_hub_server()
    hub.run()
