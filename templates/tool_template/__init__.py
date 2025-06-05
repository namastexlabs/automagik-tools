"""
{TOOL_NAME} Tool - {TOOL_DESCRIPTION}

Replace this with a detailed description of your tool.
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from fastmcp import FastMCP, Context
import httpx  # Remove if not needed


# Request/Response models
class YourRequestModel(BaseModel):
    """Model for your tool's input"""
    required_field: str = Field(description="A required field")
    optional_field: Optional[int] = Field(default=None, description="An optional field")


class YourResponseModel(BaseModel):
    """Model for your tool's output"""
    status: str = Field(description="Operation status")
    data: Dict[str, Any] = Field(description="Response data")


# Helper functions
async def make_api_request(
    endpoint: str,
    method: str = "GET",
    data: Optional[Dict] = None,
    config: Optional[Any] = None,
    ctx: Optional[Context] = None
) -> Dict[str, Any]:
    """Make an API request (example helper)"""
    if not config or not hasattr(config, 'api_key'):
        raise ValueError("{TOOL_NAME} API key is required but not configured")
    
    headers = {
        "Authorization": f"Bearer {config.api_key}",
        "Content-Type": "application/json"
    }
    
    url = f"{config.base_url}/{endpoint}"
    
    if ctx:
        await ctx.info(f"Making {method} request to {url}")
    
    async with httpx.AsyncClient(timeout=config.timeout) as client:
        try:
            response = await client.request(
                method=method,
                url=url,
                headers=headers,
                json=data
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            error_msg = f"{TOOL_NAME} API error: {e.response.status_code} - {e.response.text}"
            if ctx:
                await ctx.error(error_msg)
            raise ValueError(error_msg)
        except Exception as e:
            error_msg = f"Request failed: {str(e)}"
            if ctx:
                await ctx.error(error_msg)
            raise ValueError(error_msg)


def create_tool(config: Any) -> FastMCP:
    """Create the {TOOL_NAME} MCP tool"""
    mcp = FastMCP("{TOOL_NAME}")
    
    # Tool: Main functionality
    @mcp.tool()
    async def your_main_action(
        required_param: str,
        optional_param: Optional[str] = None,
        ctx: Optional[Context] = None
    ) -> Dict[str, Any]:
        """Brief description of what this tool does
        
        Args:
            required_param: Description of this parameter
            optional_param: Description of this optional parameter
            ctx: MCP context for logging
            
        Returns:
            Dictionary containing the operation result
        """
        # Your implementation here
        if ctx:
            await ctx.info(f"Starting operation with param: {required_param}")
        
        try:
            # Example: Make an API call
            # result = await make_api_request(
            #     endpoint="your/endpoint",
            #     method="POST",
            #     data={"param": required_param},
            #     config=config,
            #     ctx=ctx
            # )
            
            # For now, return a simple response
            result = {
                "status": "success",
                "message": f"Processed: {required_param}",
                "optional": optional_param
            }
            
            if ctx:
                await ctx.info("Operation completed successfully")
            
            return result
            
        except Exception as e:
            if ctx:
                await ctx.error(f"Operation failed: {str(e)}")
            raise ValueError(f"Failed to complete operation: {str(e)}")
    
    # Tool: Additional action
    @mcp.tool()
    async def your_secondary_action(
        param1: str,
        param2: int = 10
    ) -> str:
        """Another tool action
        
        Args:
            param1: First parameter
            param2: Second parameter with default
            
        Returns:
            A string result
        """
        return f"Processed {param1} with value {param2}"
    
    # Resource: Status endpoint
    @mcp.resource("{TOOL_NAME_LOWER}://status")
    async def get_status() -> Dict[str, Any]:
        """Get current tool status"""
        return {
            "tool": "{TOOL_NAME}",
            "version": "1.0.0",
            "status": "operational",
            "configured": bool(config and hasattr(config, 'api_key') and config.api_key)
        }
    
    # Resource: Configuration info
    @mcp.resource("{TOOL_NAME_LOWER}://config")
    async def get_config() -> Dict[str, Any]:
        """Get tool configuration (non-sensitive)"""
        return {
            "base_url": getattr(config, 'base_url', 'Not configured'),
            "timeout": getattr(config, 'timeout', 30),
            "has_api_key": bool(config and hasattr(config, 'api_key') and config.api_key)
        }
    
    # Prompt: Setup guide
    @mcp.prompt()
    async def setup_guide() -> str:
        """Guide for setting up {TOOL_NAME}"""
        return """To set up {TOOL_NAME}:
        
        1. Get your API key from https://example.com/api-keys
        2. Add to your .env file:
           {TOOL_NAME_UPPER}_API_KEY=your-api-key-here
           {TOOL_NAME_UPPER}_BASE_URL=https://api.example.com
        3. Restart the automagik-tools server
        4. Verify setup with: automagik-tools list
        
        For more help, see the documentation.
        """
    
    # Prompt: Usage examples
    @mcp.prompt()
    async def usage_examples() -> str:
        """Show example usage of {TOOL_NAME}"""
        return """Here are some examples of using {TOOL_NAME}:
        
        1. Basic usage:
           your_main_action("test") -> {"status": "success", "message": "Processed: test"}
        
        2. With optional parameters:
           your_main_action("test", "optional_value")
        
        3. Secondary action:
           your_secondary_action("hello", 42) -> "Processed hello with value 42"
        
        4. Check status:
           Access resource {TOOL_NAME_LOWER}://status
        """
    
    return mcp