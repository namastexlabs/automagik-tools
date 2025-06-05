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
import uvicorn
from fastapi import FastAPI
from contextlib import asynccontextmanager

console = Console()
app = typer.Typer(name="automagik-tools", help="MCP Tools Framework")


def create_multi_mcp_lifespan(loaded_tools: Dict[str, FastMCP]):
    """Create a lifespan manager that properly coordinates multiple FastMCP apps

    According to FastMCP docs, when mounting FastMCP apps, you must pass the lifespan
    context from the FastMCP app to the parent FastAPI app for Streamable HTTP transport.
    """

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # Store all the individual MCP app lifespan contexts
        lifespan_contexts = {}

        # Initialize each MCP app's lifespan properly
        for tool_name, mcp_server in loaded_tools.items():
            try:
                # Get the HTTP app which includes the proper lifespan
                mcp_app = mcp_server.http_app()

                # The FastMCP http_app() returns a Starlette app with a lifespan
                # We need to start each MCP app's lifespan context manually
                if hasattr(mcp_app, "lifespan") and mcp_app.lifespan:
                    console.print(
                        f"[blue]🔄 Starting {tool_name} MCP lifespan...[/blue]"
                    )
                    # Create and enter the lifespan context
                    lifespan_context = mcp_app.lifespan(mcp_app)
                    await lifespan_context.__aenter__()
                    lifespan_contexts[tool_name] = lifespan_context
                    console.print(f"[green]✅ {tool_name} lifespan started[/green]")
                else:
                    console.print(
                        f"[yellow]⚠️  {tool_name} has no lifespan context[/yellow]"
                    )

            except Exception as e:
                console.print(
                    f"[red]❌ Failed to start {tool_name} lifespan: {e}[/red]"
                )
                import traceback

                console.print(f"[red]{traceback.format_exc()}[/red]")

        console.print(
            f"[green]🚀 Multi-tool server ready with {len(loaded_tools)} tools[/green]"
        )

        try:
            yield
        finally:
            # Cleanup all MCP app lifespans
            console.print("[blue]🔄 Shutting down MCP lifespans...[/blue]")
            for tool_name, lifespan_context in lifespan_contexts.items():
                try:
                    await lifespan_context.__aexit__(None, None, None)
                    console.print(f"[green]✅ {tool_name} lifespan stopped[/green]")
                except Exception as e:
                    console.print(
                        f"[red]❌ Error stopping {tool_name} lifespan: {e}[/red]"
                    )

    return lifespan


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
            console.print(
                f"[yellow]Warning: Failed to load config for '{tool_name}': {e}[/yellow]"
            )

    # Legacy support - return empty dict
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


@app.command()
def list():
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
def serve_all(
    host: Optional[str] = typer.Option(
        None, help="Host to bind to (overrides HOST env var)"
    ),
    port: Optional[int] = typer.Option(
        None, help="Port to bind to (overrides PORT env var)"
    ),
    tools: Optional[str] = typer.Option(
        None, help="Comma-separated list of tools to serve (default: all)"
    ),
):
    """Serve all tools (or specified tools) on a single server with path-based routing"""
    available_tools = discover_tools()

    if not available_tools:
        console.print("[red]No tools found[/red]")
        sys.exit(1)

    # Parse tool list or use all tools
    if tools:
        tool_names = [t.strip() for t in tools.split(",")]
        missing_tools = [t for t in tool_names if t not in available_tools]
        if missing_tools:
            console.print(f"[red]Tools not found: {', '.join(missing_tools)}[/red]")
            console.print(f"Available tools: {', '.join(available_tools.keys())}")
            sys.exit(1)
    else:
        tool_names = list(available_tools.keys())

    # Get host and port from environment variables or defaults
    serve_host = host or os.getenv("HOST", "127.0.0.1")
    serve_port = port or int(os.getenv("PORT", "8000"))

    console.print(f"Starting multi-tool server with: {', '.join(tool_names)}")
    console.print(f"[blue]Server config: HOST={serve_host}, PORT={serve_port}[/blue]")

    # Load all tools and create their HTTP apps
    loaded_tools = {}
    mcp_apps = {}

    for tool_name in tool_names:
        try:
            console.print(f"[blue]Loading tool: {tool_name}[/blue]")
            config = create_config_for_tool(tool_name)
            if tool_name == "evolution-api":
                console.print(
                    f"[blue]Config: URL={config.base_url}, API Key={'***' if config.api_key else 'Not set'}[/blue]"
                )

            mcp_server = load_tool(tool_name, available_tools)
            loaded_tools[tool_name] = mcp_server

            # Create the HTTP app for this tool
            # Use path="/mcp" to set the MCP endpoint path within each mounted app
            mcp_app = mcp_server.http_app(path="/mcp")
            mcp_apps[tool_name] = mcp_app

            console.print(f"[green]✅ Tool '{tool_name}' loaded successfully[/green]")
        except Exception as e:
            console.print(f"[red]❌ Failed to load tool {tool_name}: {e}[/red]")
            import traceback

            console.print(f"[red]{traceback.format_exc()}[/red]")

    if not loaded_tools:
        console.print("[red]No tools loaded successfully. Exiting.[/red]")
        sys.exit(1)

    # Create the main FastAPI app
    # According to FastMCP docs, we need to use the lifespan from one of the MCP apps
    # For multiple apps, we'll combine their lifespans manually

    @asynccontextmanager
    async def combined_lifespan(app: FastAPI):
        # Start all MCP app lifespans
        lifespan_contexts = {}

        for tool_name, mcp_app in mcp_apps.items():
            try:
                if hasattr(mcp_app, "lifespan") and mcp_app.lifespan:
                    console.print(
                        f"[blue]🔄 Starting {tool_name} MCP lifespan...[/blue]"
                    )
                    lifespan_context = mcp_app.lifespan(mcp_app)
                    await lifespan_context.__aenter__()
                    lifespan_contexts[tool_name] = lifespan_context
                    console.print(f"[green]✅ {tool_name} lifespan started[/green]")
            except Exception as e:
                console.print(
                    f"[red]❌ Failed to start {tool_name} lifespan: {e}[/red]"
                )
                import traceback

                console.print(f"[red]{traceback.format_exc()}[/red]")

        console.print(
            f"[green]🚀 Multi-tool server ready with {len(loaded_tools)} tools[/green]"
        )

        try:
            yield
        finally:
            # Stop all MCP app lifespans
            console.print("[blue]🔄 Shutting down MCP lifespans...[/blue]")
            for tool_name, lifespan_context in lifespan_contexts.items():
                try:
                    await lifespan_context.__aexit__(None, None, None)
                    console.print(f"[green]✅ {tool_name} lifespan stopped[/green]")
                except Exception as e:
                    console.print(
                        f"[red]❌ Error stopping {tool_name} lifespan: {e}[/red]"
                    )

    # Create FastAPI app with the combined lifespan
    fastapi_app = FastAPI(
        title="Automagik Tools Server", version="0.1.0", lifespan=combined_lifespan
    )

    # Add root endpoint that lists available tools
    @fastapi_app.get("/")
    async def root():
        return {
            "message": "Automagik Tools Server",
            "available_tools": list(loaded_tools.keys()),
            "endpoints": {tool: f"/{tool}/mcp" for tool in loaded_tools.keys()},
        }

    # Mount each tool's MCP app on its own path
    for tool_name in tool_names:
        if tool_name in mcp_apps:
            # Mount the MCP app under /{tool_name}
            fastapi_app.mount(f"/{tool_name}", mcp_apps[tool_name])
            console.print(
                f"[green]🔗 Tool '{tool_name}' available at: http://{serve_host}:{serve_port}/{tool_name}/mcp[/green]"
            )

    # Start the combined server
    console.print(
        f"[green]🚀 Starting multi-tool server on {serve_host}:{serve_port}[/green]"
    )
    uvicorn.run(fastapi_app, host=serve_host, port=serve_port)


@app.command()
def serve(
    tool: str = typer.Option(..., help="Tool name to serve"),
    host: Optional[str] = typer.Option(
        None, help="Host to bind to (overrides HOST env var)"
    ),
    port: Optional[int] = typer.Option(
        None, help="Port to bind to (overrides PORT env var)"
    ),
    transport: str = typer.Option("sse", help="Transport type (sse or stdio)"),
):
    """Serve a specific tool (legacy single-tool mode)"""
    tools = discover_tools()

    if tool not in tools:
        console.print(f"[red]Tool '{tool}' not found[/red]")
        console.print(f"Available tools: {', '.join(tools.keys())}")
        sys.exit(1)

    # Get host and port from environment variables or defaults
    # Command line options take precedence over environment variables
    serve_host = host or os.getenv("HOST", "127.0.0.1")
    serve_port = port or int(os.getenv("PORT", "8000"))

    # Only print to console for non-stdio transports
    if transport != "stdio":
        console.print(f"Starting server with tools: {tool}")
        console.print(f"[blue]Server config: HOST={serve_host}, PORT={serve_port}[/blue]")

    try:
        # Load the tool
        mcp_server = load_tool(tool, tools)
        config = create_config_for_tool(tool, tools)

        if transport != "stdio" and tool == "evolution-api":
            console.print(
                f"[blue]Config loaded: URL={config.base_url}, API Key={'***' if config.api_key else 'Not set'}[/blue]"
            )

        if transport != "stdio":
            console.print(f"[green]✅ Tool '{tool}' loaded successfully[/green]")

        # Start the server
        if transport == "sse":
            console.print(
                f"[green]🚀 Starting SSE server on {serve_host}:{serve_port}[/green]"
            )
            mcp_server.run(transport="sse", host=serve_host, port=serve_port)
        else:
            # No console output for stdio to avoid protocol interference
            mcp_server.run(transport="stdio")

    except Exception as e:
        console.print(f"[red]❌ Failed to load tool {tool}: {e}[/red]")
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


@app.command()
def run(
    tool_name: str,
    host: str = typer.Option("0.0.0.0", help="Host to bind to"),
    port: int = typer.Option(8000, help="Port to bind to"),
):
    """Run a tool standalone (if it supports it)"""
    tools = discover_tools()

    if tool_name not in tools:
        console.print(f"[red]Tool '{tool_name}' not found[/red]")
        console.print(f"Available tools: {', '.join(tools.keys())}")
        return

    tool_data = tools[tool_name]

    # Check if module is loaded
    if "module" not in tool_data:
        console.print(f"[red]Tool '{tool_name}' couldn't be loaded[/red]")
        return

    tool_module = tool_data["module"]

    # Check if tool supports standalone execution
    if hasattr(tool_module, "run_standalone"):
        console.print(f"[green]Running {tool_name} standalone on {host}:{port}[/green]")
        tool_module.run_standalone(host=host, port=port)
    else:
        # Fallback to create_server
        console.print(
            "[yellow]Tool doesn't have run_standalone, using create_server[/yellow]"
        )
        server = load_tool(tool_name, tools)
        server.run(transport="sse", host=host, port=port)


@app.command()
def tool(
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
def version():
    """Show version information"""
    from . import __version__

    console.print(f"automagik-tools v{__version__}")


def main():
    """Main entry point"""
    app()


if __name__ == "__main__":
    main()
