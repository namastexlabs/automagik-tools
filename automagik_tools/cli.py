"""
CLI for automagik-tools
"""

import os
import sys
from typing import Dict, Any, Optional, List
import importlib.metadata
import typer
from rich.console import Console
from rich.table import Table
from fastmcp import FastMCP
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
import uvicorn
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from contextlib import asynccontextmanager
import asyncio

console = Console()
app = typer.Typer(name="automagik-tools", help="MCP Tools Framework")


class EvolutionAPIConfig(BaseSettings):
    """Configuration for Evolution API"""
    base_url: str = Field(default="https://your-evolution-api-server.com", alias="evolution_api_base_url")
    api_key: str = Field(default="", alias="evolution_api_key")
    timeout: int = Field(default=30, alias="evolution_api_timeout")

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore"  # Allow extra fields
    }


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
                if hasattr(mcp_app, 'lifespan') and mcp_app.lifespan:
                    console.print(f"[blue]🔄 Starting {tool_name} MCP lifespan...[/blue]")
                    # Create and enter the lifespan context
                    lifespan_context = mcp_app.lifespan(mcp_app)
                    await lifespan_context.__aenter__()
                    lifespan_contexts[tool_name] = lifespan_context
                    console.print(f"[green]✅ {tool_name} lifespan started[/green]")
                else:
                    console.print(f"[yellow]⚠️  {tool_name} has no lifespan context[/yellow]")
                    
            except Exception as e:
                console.print(f"[red]❌ Failed to start {tool_name} lifespan: {e}[/red]")
                import traceback
                console.print(f"[red]{traceback.format_exc()}[/red]")
        
        console.print(f"[green]🚀 Multi-tool server ready with {len(loaded_tools)} tools[/green]")
        
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
                    console.print(f"[red]❌ Error stopping {tool_name} lifespan: {e}[/red]")
    
    return lifespan


def discover_tools() -> Dict[str, Any]:
    """Discover tools from entry points"""
    tools = {}
    
    try:
        entry_points = importlib.metadata.entry_points()
        if hasattr(entry_points, 'select'):
            # Python 3.10+
            tool_entry_points = entry_points.select(group='automagik_tools.plugins')
        else:
            # Python 3.9 and earlier
            tool_entry_points = entry_points.get('automagik_tools.plugins', [])
        
        for ep in tool_entry_points:
            tools[ep.name] = {
                'name': ep.name,
                'type': 'Static',
                'status': '⚪ Available',
                'description': _get_tool_description(ep.name),
                'entry_point': ep
            }
    except Exception as e:
        console.print(f"[red]Error discovering tools: {e}[/red]")
    
    return tools


def _get_tool_description(tool_name: str) -> str:
    """Get description for a tool"""
    descriptions = {
        'evolution-api': 'WhatsApp messaging via Evolution API',
        'discord': 'Discord bot integration',
        'notion': 'Notion workspace integration', 
        'github': 'GitHub repository management',
    }
    return descriptions.get(tool_name, f'{tool_name} tool')


def create_config_for_tool(tool_name: str) -> Any:
    """Create configuration for a specific tool"""
    if tool_name == 'evolution-api':
        return EvolutionAPIConfig()
    else:
        # For other tools, return empty config for now
        return {}


def load_tool(tool_name: str, tools: Dict[str, Any]) -> FastMCP:
    """Load a specific tool and return the MCP server"""
    if tool_name not in tools:
        raise ValueError(f"Tool '{tool_name}' not found")
    
    entry_point = tools[tool_name]['entry_point']
    create_tool_func = entry_point.load()
    config = create_config_for_tool(tool_name)
    
    return create_tool_func(config)


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
            tool_info['name'],
            tool_info['type'],
            tool_info['status'],
            tool_info['description']
        )
    
    console.print(table)


@app.command()
def serve_all(
    host: Optional[str] = typer.Option(None, help="Host to bind to (overrides HOST env var)"),
    port: Optional[int] = typer.Option(None, help="Port to bind to (overrides PORT env var)"),
    tools: Optional[str] = typer.Option(None, help="Comma-separated list of tools to serve (default: all)")
):
    """Serve all tools (or specified tools) on a single server with path-based routing"""
    available_tools = discover_tools()
    
    if not available_tools:
        console.print("[red]No tools found[/red]")
        sys.exit(1)
    
    # Parse tool list or use all tools
    if tools:
        tool_names = [t.strip() for t in tools.split(',')]
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
            if tool_name == 'evolution-api':
                console.print(f"[blue]Config: URL={config.base_url}, API Key={'***' if config.api_key else 'Not set'}[/blue]")
            
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
                if hasattr(mcp_app, 'lifespan') and mcp_app.lifespan:
                    console.print(f"[blue]🔄 Starting {tool_name} MCP lifespan...[/blue]")
                    lifespan_context = mcp_app.lifespan(mcp_app)
                    await lifespan_context.__aenter__()
                    lifespan_contexts[tool_name] = lifespan_context
                    console.print(f"[green]✅ {tool_name} lifespan started[/green]")
            except Exception as e:
                console.print(f"[red]❌ Failed to start {tool_name} lifespan: {e}[/red]")
                import traceback
                console.print(f"[red]{traceback.format_exc()}[/red]")
        
        console.print(f"[green]🚀 Multi-tool server ready with {len(loaded_tools)} tools[/green]")
        
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
                    console.print(f"[red]❌ Error stopping {tool_name} lifespan: {e}[/red]")
    
    # Create FastAPI app with the combined lifespan
    fastapi_app = FastAPI(
        title="Automagik Tools Server", 
        version="0.1.0",
        lifespan=combined_lifespan
    )

    # Add root endpoint that lists available tools
    @fastapi_app.get("/")
    async def root():
        return {
            "message": "Automagik Tools Server",
            "available_tools": list(loaded_tools.keys()),
            "endpoints": {tool: f"/{tool}/mcp" for tool in loaded_tools.keys()}
        }

    # Mount each tool's MCP app on its own path
    for tool_name in tool_names:
        if tool_name in mcp_apps:
            # Mount the MCP app under /{tool_name}
            fastapi_app.mount(f"/{tool_name}", mcp_apps[tool_name])
            console.print(f"[green]🔗 Tool '{tool_name}' available at: http://{serve_host}:{serve_port}/{tool_name}/mcp[/green]")
    
    # Start the combined server
    console.print(f"[green]🚀 Starting multi-tool server on {serve_host}:{serve_port}[/green]")
    uvicorn.run(fastapi_app, host=serve_host, port=serve_port)


@app.command()
def serve(
    tool: str = typer.Option(..., help="Tool name to serve"),
    host: Optional[str] = typer.Option(None, help="Host to bind to (overrides HOST env var)"),
    port: Optional[int] = typer.Option(None, help="Port to bind to (overrides PORT env var)"),
    transport: str = typer.Option("sse", help="Transport type (sse or stdio)")
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
    
    console.print(f"Starting server with tools: {tool}")
    console.print(f"[blue]Server config: HOST={serve_host}, PORT={serve_port}[/blue]")
    
    try:
        # Load the tool
        mcp_server = load_tool(tool, tools)
        config = create_config_for_tool(tool)
        
        if tool == 'evolution-api':
            console.print(f"[blue]Config loaded: URL={config.base_url}, API Key={'***' if config.api_key else 'Not set'}[/blue]")
        
        console.print(f"[green]✅ Tool '{tool}' loaded successfully[/green]")
        
        # Start the server
        if transport == "sse":
            console.print(f"[green]🚀 Starting SSE server on {serve_host}:{serve_port}[/green]")
            mcp_server.run(transport="sse", host=serve_host, port=serve_port)
        else:
            console.print(f"[green]🚀 Starting STDIO server[/green]")
            mcp_server.run(transport="stdio")
            
    except Exception as e:
        console.print(f"[red]❌ Failed to load tool {tool}: {e}[/red]")
        import traceback
        console.print(f"[red]{traceback.format_exc()}[/red]")
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