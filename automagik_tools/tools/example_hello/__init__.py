"""
Example Hello Tool - A minimal MCP tool example

This tool demonstrates the simplest possible MCP tool implementation.
Use this as a starting point for creating your own tools.
"""

from typing import Optional, Dict, Any
from fastmcp import FastMCP
from .config import ExampleHelloConfig


def create_tool(config: Optional[dict] = None) -> FastMCP:
    """Create the Example Hello MCP tool"""
    mcp = FastMCP("Example Hello Tool")
    
    @mcp.tool()
    async def say_hello(name: str = "World") -> str:
        """Say hello to someone
        
        Args:
            name: The name to greet (default: World)
            
        Returns:
            A friendly greeting message
        """
        return f"Hello, {name}! Welcome to automagik-tools!"
    
    @mcp.tool()
    async def add_numbers(a: int, b: int) -> int:
        """Add two numbers together
        
        Args:
            a: First number
            b: Second number
            
        Returns:
            The sum of a and b
        """
        return a + b
    
    @mcp.resource("example://info")
    async def get_info() -> str:
        """Get information about this example tool"""
        return """This is a minimal example MCP tool that demonstrates:
        - Basic tool implementation
        - Multiple tool methods
        - Resource endpoints
        - Simple prompts
        
        Use this as a template for creating your own tools!"""
    
    @mcp.prompt()
    async def example_usage() -> str:
        """Show example usage of this tool"""
        return """Here are some examples of using the Example Hello tool:
        
        1. Say hello to someone:
           say_hello("Alice") -> "Hello, Alice! Welcome to automagik-tools!"
        
        2. Add two numbers:
           add_numbers(5, 3) -> 8
        
        3. Get tool information:
           Access the resource example://info for tool details
        """
    
    return mcp


def get_metadata() -> Dict[str, Any]:
    """Tool metadata for discovery"""
    return {
        "name": "example-hello",
        "version": "1.0.0",
        "description": "A minimal MCP tool example",
        "author": "Automagik Team",
        "category": "example",
        "tags": ["example", "hello", "minimal"],
        "config_env_prefix": "EXAMPLE_HELLO_"
    }


def get_config_class():
    """Return configuration class for introspection"""
    return ExampleHelloConfig


def create_server(config: Optional[ExampleHelloConfig] = None):
    """Create FastMCP server instance"""
    if config is None:
        config = ExampleHelloConfig()
    return create_tool(config)


def get_config_schema() -> Dict[str, Any]:
    """Return JSON schema of configuration"""
    return ExampleHelloConfig.model_json_schema()


def get_required_env_vars() -> Dict[str, str]:
    """Return required environment variables"""
    # Example Hello has no required config
    return {}


def run_standalone(host: str = "0.0.0.0", port: int = 8000):
    """Run tool as standalone service"""
    config = ExampleHelloConfig()
    server = create_server(config)
    
    print(f"Starting Example Hello MCP server on {host}:{port}")
    server.run(transport="sse", host=host, port=port)


__all__ = ["create_tool", "create_server", "get_metadata", "get_config_class", 
          "get_config_schema", "get_required_env_vars", "run_standalone"]