"""
CLI for automagik-tools
"""

import os
import sys
from typing import Dict, Any, Optional
from pathlib import Path
import importlib
import importlib.metadata
import typer
from rich.console import Console
from rich.table import Table
from fastmcp import FastMCP
import httpx
from .hub import create_hub_server

console = Console()
# For stdio transport, we need to use stderr to avoid polluting JSON-RPC
stderr_console = Console(stderr=True)
app = typer.Typer(name="automagik-tools", help="MCP Tools Framework")


def create_dynamic_openapi_tool(
    openapi_url: str,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    transport: str = "stdio",
) -> FastMCP:
    """Create a dynamic MCP tool from an OpenAPI specification URL"""

    # Only print to console for non-stdio transports
    if transport != "stdio":
        console.print(f"[blue]Fetching OpenAPI spec from: {openapi_url}[/blue]")

    # Fetch the OpenAPI spec
    try:
        response = httpx.get(openapi_url, timeout=30)
        response.raise_for_status()
        openapi_spec = response.json()
    except Exception as e:
        raise ValueError(f"Failed to fetch OpenAPI spec: {e}")

    # Extract info from OpenAPI spec
    api_info = openapi_spec.get("info", {})
    api_title = api_info.get("title", "Dynamic API")
    api_description = api_info.get("description", "API loaded from OpenAPI spec")

    # Determine base URL
    if not base_url:
        # Try to get from OpenAPI spec servers
        servers = openapi_spec.get("servers", [])
        if servers:
            base_url = servers[0].get("url", "")
        else:
            # Try to extract from the OpenAPI URL
            from urllib.parse import urlparse

            parsed = urlparse(openapi_url)
            base_url = f"{parsed.scheme}://{parsed.netloc}"

    if transport != "stdio":
        console.print(f"[blue]API Title: {api_title}[/blue]")
        console.print(f"[blue]Base URL: {base_url}[/blue]")

    # Create HTTP client with authentication
    headers = {}
    if api_key:
        # Try common auth header patterns
        headers["X-API-Key"] = api_key
        headers["Authorization"] = f"Bearer {api_key}"
        if transport != "stdio":
            console.print("[blue]Authentication headers configured[/blue]")

    client = httpx.AsyncClient(base_url=base_url, headers=headers, timeout=30.0)

    # Create MCP server from OpenAPI spec
    try:
        mcp_server = FastMCP.from_openapi(
            openapi_spec=openapi_spec,
            client=client,
            name=api_title,
            instructions=api_description,
        )

        if transport != "stdio":
            console.print(
                f"[green]✅ Successfully created MCP server for {api_title}[/green]"
            )

        return mcp_server

    except Exception as e:
        raise ValueError(f"Failed to create MCP server from OpenAPI spec: {e}")


# Removed create_multi_mcp_lifespan function as it's no longer needed with hub approach


def discover_tools() -> Dict[str, Any]:
    """Discover tools from the tools directory"""
    tools = {}

    # Get the tools directory
    tools_dir = Path(__file__).parent / "tools"

    if tools_dir.exists():
        for tool_path in tools_dir.iterdir():
            if tool_path.is_dir() and not tool_path.name.startswith("_"):
                tool_name_snake = tool_path.name
                # Convert snake_case to kebab-case for the tool name
                tool_name = tool_name_snake.replace("_", "-")

                try:
                    # Import the tool module
                    module_name = f"automagik_tools.tools.{tool_name_snake}"
                    module = importlib.import_module(module_name)

                    # Get metadata if available
                    metadata = (
                        module.get_metadata() if hasattr(module, "get_metadata") else {}
                    )

                    # Create a fake entry point for compatibility
                    class FakeEntryPoint:
                        def __init__(self, name, value):
                            self.name = name
                            self.value = value

                        def load(self):
                            # Return the module itself, not a specific function
                            return module

                    tools[tool_name] = {
                        "name": tool_name,
                        "module": module,
                        "entry_point": FakeEntryPoint(
                            tool_name, f"{module_name}:create_tool"
                        ),
                        "metadata": metadata,
                        "type": "Auto-discovered",
                        "status": "⚪ Available",
                        "description": metadata.get("description", f"{tool_name} tool"),
                    }
                except Exception as e:
                    # Use stderr for stdio transport to avoid polluting JSON-RPC
                    if os.environ.get("MCP_TRANSPORT") == "stdio":
                        stderr_console.print(
                            f"[yellow]Warning: Failed to load {tool_name}: {e}[/yellow]"
                        )
                    else:
                        console.print(
                            f"[yellow]Warning: Failed to load {tool_name}: {e}[/yellow]"
                        )
    else:
        console.print(f"[red]Tools directory not found: {tools_dir}[/red]")

    return tools


def create_config_for_tool(tool_name: str, tools: Dict[str, Any]) -> Any:
    """Create configuration by asking the tool itself"""
    if tool_name not in tools:
        raise ValueError(f"Tool '{tool_name}' not found")

    tool_data = tools[tool_name]

    # Try to get module from tool data
    if "module" in tool_data:
        tool_module = tool_data["module"]

        # Check if tool exports get_config_class
        if hasattr(tool_module, "get_config_class"):
            config_class = tool_module.get_config_class()
            return config_class()

    # Fallback for tools not yet loaded
    if "entry_point" in tool_data:
        try:
            tool_module = tool_data["entry_point"].load()
            if hasattr(tool_module, "get_config_class"):
                config_class = tool_module.get_config_class()
                return config_class()
        except Exception as e:
            # Use stderr for stdio transport to avoid polluting JSON-RPC
            if os.environ.get("MCP_TRANSPORT") == "stdio":
                stderr_console.print(
                    f"[yellow]Warning: Failed to load config for '{tool_name}': {e}[/yellow]"
                )
            else:
                console.print(
                    f"[yellow]Warning: Failed to load config for '{tool_name}': {e}[/yellow]"
                )

    # Legacy support - return empty dict
    if os.environ.get("MCP_TRANSPORT") == "stdio":
        stderr_console.print(
            f"[yellow]Warning: Tool '{tool_name}' doesn't export get_config_class[/yellow]"
        )
    else:
        console.print(
            f"[yellow]Warning: Tool '{tool_name}' doesn't export get_config_class[/yellow]"
        )
    return {}


def load_tool(tool_name: str, tools: Dict[str, Any]) -> FastMCP:
    """Load a specific tool and return the MCP server"""
    if tool_name not in tools:
        raise ValueError(f"Tool '{tool_name}' not found")

    tool_data = tools[tool_name]
    config = create_config_for_tool(tool_name, tools)

    # Try to use module if already loaded
    if "module" in tool_data:
        tool_module = tool_data["module"]

        # Use the tool's create function
        if hasattr(tool_module, "create_server"):
            return tool_module.create_server(config)
        elif hasattr(tool_module, "create_tool"):
            # Legacy support
            return tool_module.create_tool(config)

    # Fallback to loading via entry point
    if "entry_point" in tool_data:
        loaded_module = tool_data["entry_point"].load()

        # Check if it's a module or a function
        if hasattr(loaded_module, "create_server"):
            return loaded_module.create_server(config)
        elif hasattr(loaded_module, "create_tool"):
            return loaded_module.create_tool(config)
        else:
            # Direct function call for legacy
            return loaded_module(config)

    raise ValueError(f"Tool '{tool_name}' doesn't export create_server or create_tool")


@app.command("list")
def list_tools():
    """List all available tools"""
    tools = discover_tools()

    if not tools:
        console.print("[yellow]No tools found[/yellow]")
        return

    table = Table(title="Available Tools")
    table.add_column("Tool Name", style="cyan")
    table.add_column("Type", style="green")
    table.add_column("Status", style="yellow")
    table.add_column("Description", style="white")

    for tool_info in tools.values():
        table.add_row(
            tool_info["name"],
            tool_info["type"],
            tool_info["status"],
            tool_info["description"],
        )

    console.print(table)


@app.command()
def hub(
    host: Optional[str] = typer.Option(
        None, help="Host to bind to (overrides HOST env var)"
    ),
    port: Optional[int] = typer.Option(
        None, help="Port to bind to (overrides PORT env var)"
    ),
    transport: str = typer.Option(
        "stdio", "--transport", "-t", help="Transport type: stdio (default), http, sse"
    ),
):
    """Serve all tools on a single server with path-based routing using the hub"""
    # Get host and port from environment variables or defaults
    serve_host = host or os.getenv("AUTOMAGIK_TOOLS_HOST", "127.0.0.1")
    serve_port = port or int(os.getenv("AUTOMAGIK_TOOLS_SSE_PORT", "8884"))

    # For stdio transport, we can't serve multiple tools
    if transport == "stdio":
        console.print("[red]❌ stdio transport cannot serve multiple tools[/red]")
        console.print(
            "[yellow]💡 Use 'serve --tool <tool-name> --transport stdio' for a single tool[/yellow]"
        )
        sys.exit(1)

    if transport != "stdio":
        console.print("[blue]Starting Automagik Tools Hub...[/blue]")
        console.print(
            f"[blue]Server config: HOST={serve_host}, PORT={serve_port}, Transport={transport}[/blue]"
        )

    try:
        # Create the hub server using the unified implementation from hub.py
        hub_server = create_hub_server()

        # Set environment variable
        os.environ["MCP_TRANSPORT"] = transport

        # Run the hub server
        if transport == "stdio":
            hub_server.run(transport="stdio")
        elif transport == "http":
            console.print(
                f"[green]🚀 Starting HTTP hub server on {serve_host}:{serve_port}[/green]"
            )
            hub_server.run(transport="http", host=serve_host, port=serve_port)
        elif transport == "sse":
            console.print(
                f"[green]🚀 Starting SSE hub server on {serve_host}:{serve_port}[/green]"
            )
            hub_server.run(transport="sse", host=serve_host, port=serve_port)
        else:
            console.print(f"[red]❌ Unsupported transport: {transport}[/red]")
            sys.exit(1)

    except Exception as e:
        console.print(f"[red]❌ Failed to start hub server: {e}[/red]")
        import traceback

        console.print(f"[red]{traceback.format_exc()}[/red]")
        sys.exit(1)


@app.command()
def tool(
    tool_name: str = typer.Argument(..., help="Tool name to serve"),
    host: Optional[str] = typer.Option(
        None, help="Host to bind to (overrides HOST env var)"
    ),
    port: Optional[int] = typer.Option(
        None, help="Port to bind to (overrides PORT env var)"
    ),
    transport: str = typer.Option(
        "stdio", "--transport", "-t", help="Transport type: stdio (default), http, sse"
    ),
):
    """Serve a specific tool"""
    # Set transport early so discover_tools can use it
    os.environ["MCP_TRANSPORT"] = transport

    tools = discover_tools()

    if tool_name not in tools:
        if transport == "stdio":
            stderr_console.print(f"[red]Tool '{tool_name}' not found[/red]")
            stderr_console.print(f"Available tools: {', '.join(tools.keys())}")
        else:
            console.print(f"[red]Tool '{tool_name}' not found[/red]")
            console.print(f"Available tools: {', '.join(tools.keys())}")
        sys.exit(1)

    # Get host and port from environment variables or defaults
    serve_host = host or os.getenv("AUTOMAGIK_TOOLS_HOST", "127.0.0.1")
    serve_port = port or int(os.getenv("AUTOMAGIK_TOOLS_SSE_PORT", "8884"))

    # Only print to console for non-stdio transports
    if transport != "stdio":
        console.print(f"Starting tool: {tool_name}")
        console.print(
            f"[blue]Server config: HOST={serve_host}, PORT={serve_port}[/blue]"
        )

    try:
        # Load the tool
        mcp_server = load_tool(tool_name, tools)

        if transport != "stdio":
            console.print(f"[green]✅ Tool '{tool_name}' loaded successfully[/green]")

        # Start the server
        os.environ["MCP_TRANSPORT"] = transport

        if transport == "stdio":
            mcp_server.run(transport="stdio")
        elif transport == "sse":
            console.print(
                f"[green]🚀 Starting SSE server on {serve_host}:{serve_port}[/green]"
            )
            mcp_server.run(transport="sse", host=serve_host, port=serve_port)
        elif transport == "http":
            console.print(
                f"[green]🚀 Starting HTTP server on {serve_host}:{serve_port}[/green]"
            )
            mcp_server.run(transport="http", host=serve_host, port=serve_port)
        else:
            console.print(f"[red]❌ Unsupported transport: {transport}[/red]")
            sys.exit(1)

    except Exception as e:
        console.print(f"[red]❌ Failed to load tool {tool_name}: {e}[/red]")
        import traceback

        console.print(f"[red]{traceback.format_exc()}[/red]")
        sys.exit(1)


@app.command()
def openapi(
    url: str = typer.Argument(..., help="OpenAPI specification URL"),
    host: Optional[str] = typer.Option(
        None, help="Host to bind to (overrides AUTOMAGIK_TOOLS_HOST env var)"
    ),
    port: Optional[int] = typer.Option(
        None, help="Port to bind to (overrides AUTOMAGIK_TOOLS_SSE_PORT env var)"
    ),
    transport: str = typer.Option(
        "stdio", "--transport", "-t", help="Transport type: stdio (default), http, sse"
    ),
    api_key: Optional[str] = typer.Option(None, help="API key for authentication"),
    base_url: Optional[str] = typer.Option(
        None, help="Base URL for the API (if different from OpenAPI spec)"
    ),
):
    """Serve a tool directly from an OpenAPI specification URL"""
    if transport != "stdio":
        console.print(f"[blue]Creating tool from OpenAPI spec: {url}[/blue]")

    try:
        mcp_server = create_dynamic_openapi_tool(
            openapi_url=url,
            api_key=api_key,
            base_url=base_url,
            transport=transport,
        )

        # Get host and port
        serve_host = host or os.getenv("AUTOMAGIK_TOOLS_HOST", "127.0.0.1")
        serve_port = port or int(os.getenv("AUTOMAGIK_TOOLS_SSE_PORT", "8884"))

        # Start the server
        os.environ["MCP_TRANSPORT"] = transport

        if transport == "stdio":
            mcp_server.run(transport="stdio")
        elif transport == "sse":
            console.print(
                f"[green]🚀 Starting SSE server on {serve_host}:{serve_port}[/green]"
            )
            mcp_server.run(transport="sse", host=serve_host, port=serve_port)
        elif transport == "http":
            console.print(
                f"[green]🚀 Starting HTTP server on {serve_host}:{serve_port}[/green]"
            )
            mcp_server.run(transport="http", host=serve_host, port=serve_port)
        else:
            console.print(f"[red]❌ Unsupported transport: {transport}[/red]")
            sys.exit(1)

    except Exception as e:
        console.print(f"[red]❌ Failed to create OpenAPI tool: {e}[/red]")
        import traceback

        console.print(f"[red]{traceback.format_exc()}[/red]")
        sys.exit(1)


@app.command()
def info(tool_name: str):
    """Show detailed information about a tool"""
    tools = discover_tools()

    if tool_name not in tools:
        console.print(f"[red]Tool '{tool_name}' not found[/red]")
        console.print(f"Available tools: {', '.join(tools.keys())}")
        return

    tool_data = tools[tool_name]

    # Display basic info
    console.print(f"\n[bold cyan]Tool: {tool_name}[/bold cyan]")

    if "metadata" in tool_data and tool_data["metadata"]:
        metadata = tool_data["metadata"]
        console.print(f"Version: {metadata.get('version', 'Unknown')}")
        console.print(f"Description: {metadata.get('description', 'No description')}")
        console.print(f"Category: {metadata.get('category', 'Uncategorized')}")
        console.print(f"Author: {metadata.get('author', 'Unknown')}")

        if "tags" in metadata and metadata["tags"]:
            console.print(f"Tags: {', '.join(metadata['tags'])}")

        if "config_env_prefix" in metadata:
            console.print(f"\nEnvironment Prefix: {metadata['config_env_prefix']}")

    # Display configuration info
    if "module" in tool_data and hasattr(tool_data["module"], "get_required_env_vars"):
        console.print("\n[bold]Required Environment Variables:[/bold]")
        env_vars = tool_data["module"].get_required_env_vars()
        if env_vars:
            for var, desc in env_vars.items():
                console.print(f"  {var}: {desc}")
        else:
            console.print("  No required environment variables")

    # Display config schema if available
    if "module" in tool_data and hasattr(tool_data["module"], "get_config_schema"):
        console.print("\n[bold]Configuration Schema:[/bold]")
        schema = tool_data["module"].get_config_schema()
        for prop, details in schema.get("properties", {}).items():
            required = prop in schema.get("required", [])
            prop_type = details.get("type", "unknown")
            desc = details.get("description", "")
            console.print(
                f"  {prop}: {prop_type} {'(required)' if required else '(optional)'}"
            )
            if desc:
                console.print(f"    Description: {desc}")


# Removed run command - use 'tool' command instead


@app.command("create-tool")
def create_tool(
    url: str = typer.Option(..., "--url", "-u", help="OpenAPI specification URL"),
    name: Optional[str] = typer.Option(
        None, "--name", "-n", help="Tool name (optional)"
    ),
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite existing tool"),
):
    """Create a new MCP tool from an OpenAPI specification"""
    import subprocess

    console.print("[blue]Creating tool from OpenAPI specification...[/blue]")
    console.print(f"URL: {url}")

    # Build the command
    cmd = ["python", "scripts/create_tool_from_openapi_v2.py", "--url", url]
    if name:
        cmd.extend(["--name", name])
    if force:
        cmd.append("--force")

    try:
        # Run the script
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            console.print("[green]✅ Tool created successfully![/green]")
            if result.stdout:
                console.print(result.stdout)
        else:
            console.print("[red]❌ Failed to create tool[/red]")
            if result.stderr:
                console.print(f"[red]{result.stderr}[/red]")
            sys.exit(1)

    except FileNotFoundError:
        console.print("[red]❌ OpenAPI tool creation script not found[/red]")
        console.print(
            "[yellow]Make sure you're running from the automagik-tools repository root[/yellow]"
        )
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]❌ Error creating tool: {e}[/red]")
        sys.exit(1)


@app.command()
def mcp_config(
    tool_name: str = typer.Argument(..., help="Tool name to generate config for"),
    format: str = typer.Option("cursor", help="Output format: cursor or claude"),
):
    """Generate MCP configuration for a tool to use in Cursor or Claude"""
    import json

    # Special handling for hub
    if tool_name == "hub":
        config = {
            "automagik-hub": {
                "command": "uvx",
                "args": ["automagik-tools@latest", "hub"],
                "env": {
                    "AUTOMAGIK_API_KEY": "YOUR_API_KEY_HERE",
                    "AUTOMAGIK_BASE_URL": "http://localhost:28881",
                    "OPENAI_API_KEY": "YOUR_OPENAI_API_KEY_HERE",
                    "GENIE_MODEL": "gpt-4.1",
                },
            }
        }
        console.print(
            "[yellow]⚠️  Hub serves all tools - configure environment variables as needed[/yellow]"
        )
        console.print("\n[green]MCP Configuration for Cursor:[/green]")
        console.print(json.dumps(config, indent=2))
        return

    # Special handling for dynamic OpenAPI tools
    if tool_name == "discord-api":
        config = {
            "discord-api": {
                "command": "uvx",
                "args": [
                    "automagik-tools@latest",
                    "openapi",
                    "https://raw.githubusercontent.com/discord/discord-api-spec/refs/heads/main/specs/openapi.json",
                ],
                "env": {"DISCORD_TOKEN": "YOUR_DISCORD_TOKEN_HERE"},
            }
        }
        console.print(
            "[yellow]⚠️  Discord API tool uses dynamic OpenAPI - requires latest automagik-tools[/yellow]"
        )
        console.print(
            "[yellow]   Replace YOUR_DISCORD_TOKEN_HERE with your actual Discord token[/yellow]"
        )
        console.print("\n[green]MCP Configuration for Cursor:[/green]")
        console.print(json.dumps(config, indent=2))
        return

    # Check if tool exists
    tools = discover_tools()

    if tool_name not in tools:
        console.print(f"[red]Tool '{tool_name}' not found[/red]")
        console.print(f"Available tools: {', '.join(tools.keys())}")

        # Suggest discord-api for common mistakes
        if "discord" in tool_name.lower():
            console.print("\n[yellow]💡 Did you mean 'discord-api'? Try:[/yellow]")
            console.print("[blue]automagik-tools mcp-config discord-api[/blue]")
        return

    # Load tool to get its configuration requirements
    tool_data = tools[tool_name]

    # Basic MCP configuration
    config = {
        tool_name: {
            "command": "uvx",
            "args": [
                "automagik-tools@latest",
                "tool",
                tool_name,
            ],
        }
    }

    # Add environment variables if tool has config requirements
    if "module" in tool_data:
        try:
            schema = tool_data["module"].get_config_schema()
            env_vars = {}

            # Map configuration properties to environment variables
            for prop, details in schema.get("properties", {}).items():
                env_var = f"{tool_name.upper().replace('-', '_')}_{prop.upper()}"
                required = prop in schema.get("required", [])

                # Set example values based on property type
                if details.get("type") == "string":
                    if "url" in prop.lower():
                        value = "YOUR_API_URL_HERE"
                    elif "key" in prop.lower() or "token" in prop.lower():
                        value = "YOUR_API_KEY_HERE"
                    else:
                        value = "YOUR_VALUE_HERE"
                elif details.get("type") == "integer":
                    value = "30"  # Default timeout value
                else:
                    value = "YOUR_VALUE_HERE"

                env_vars[env_var] = value

                if required:
                    console.print(
                        f"[yellow]⚠️  {env_var} is required - replace {value} with actual value[/yellow]"
                    )

            if env_vars:
                config[tool_name]["env"] = env_vars
        except Exception:
            # If we can't get config schema, just continue without env vars
            pass

    # Special configurations for known tools
    if tool_name == "automagik":
        config[tool_name]["env"] = {
            "AUTOMAGIK_AGENTS_API_KEY": "YOUR_API_KEY_HERE",
            "AUTOMAGIK_AGENTS_BASE_URL": "http://localhost:8881",
            "AUTOMAGIK_AGENTS_OPENAPI_URL": "http://localhost:8881/api/v1/openapi.json",
            "AUTOMAGIK_AGENTS_TIMEOUT": "1000",
        }
        console.print(
            "[yellow]⚠️  Configure the environment variables above with your Automagik Agents instance[/yellow]"
        )
    elif tool_name == "evolution-api":
        config[tool_name]["env"] = {
            "EVOLUTION_API_BASE_URL": "http://localhost:8080",
            "EVOLUTION_API_API_KEY": "YOUR_API_KEY_HERE",
        }
        console.print(
            "[yellow]⚠️  Configure the environment variables above with your Evolution API instance[/yellow]"
        )
    elif tool_name == "evolution-api-v2":
        config[tool_name]["env"] = {
            "EVOLUTION_API_V2_BASE_URL": "http://localhost:8080",
            "EVOLUTION_API_V2_API_KEY": "YOUR_API_KEY_HERE",
        }
        console.print(
            "[yellow]⚠️  Configure the environment variables above with your Evolution API v2 instance[/yellow]"
        )

    # Output the configuration
    console.print(f"\n[green]MCP Configuration for {format.capitalize()}:[/green]")
    console.print(json.dumps(config, indent=2))

    console.print("\n[blue]To use this configuration:[/blue]")
    if format == "cursor":
        console.print("1. Copy the JSON above")
        console.print("2. Open ~/.cursor/mcp.json (or create it)")
        console.print("3. Add this configuration to the 'mcpServers' section")
        console.print("4. Restart Cursor")
    else:
        console.print("1. Copy the JSON above")
        console.print("2. Open Claude Desktop settings")
        console.print("3. Go to Developer > Edit Config")
        console.print("4. Add this configuration to the 'mcpServers' section")
        console.print("5. Restart Claude Desktop")

    console.print("\n[green]✅ Configuration generated successfully![/green]")


# Removed duplicate tool command - keeping the original OpenAPI tool creator


@app.command()
def version():
    """Show version information"""
    from . import __version__

    console.print(f"automagik-tools v{__version__}")


def main():
    """Main entry point"""
    app()


if __name__ == "__main__":
    main()
