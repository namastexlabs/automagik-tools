# Multi-Tenant Architecture Documentation

## Overview

The Automagik Tools Hub implements a multi-tenant architecture that allows multiple users to use the same tool with their own configurations, credentials, and isolated execution environments.

## Architecture Components

### 1. Database Layer (`automagik_tools/hub/models.py`)

**ToolConfig Model**: Stores per-user tool configurations
```python
class ToolConfig(Base):
    user_id: str          # User identifier (email or ID)
    tool_name: str        # Name of the tool
    config: JSON          # User-specific configuration
    credentials: JSON     # Encrypted user credentials
```

**Key Features**:
- Per-user configuration storage
- Encrypted credentials
- JSON flexibility for tool-specific settings

### 2. Tool Lifecycle Management (`automagik_tools/hub/tool_instances.py`)

**ToolInstanceManager**: Manages running tool instances per user

```python
class ToolInstanceManager:
    async def start_tool(user_id, tool_name, config)
    async def stop_tool(user_id, tool_name)
    async def refresh_tool(user_id, tool_name, new_config)
    async def get_tool_status(user_id, tool_name)
```

**Features**:
- Per-user tool instances
- Lifecycle management (start/stop/refresh)
- Status monitoring
- Configuration hot-reload

### 3. Configuration Injection (`automagik_tools/hub/config_injection.py`)

**Runtime Configuration Loading**: Injects user-specific config at request time

```python
async def load_user_config_for_tool(user_id: str, tool_name: str) -> Optional[Dict[str, Any]]

def get_or_create_user_config(ctx: Optional[Context], config_class: type, tool_name: str) -> Any
```

**Methods**:
1. **Context Injection**: Configuration attached to FastMCP Context
2. **Environment Variables**: Temporary env var manipulation (transitional)
3. **Direct Config Objects**: Pydantic Settings instances

### 4. Tool Wrapper (`automagik_tools/hub/execution.py`)

**HubToolWrapper**: Intercepts tool function calls and injects user configuration

```python
class HubToolWrapper:
    @staticmethod
    def wrap(tool_name: str, tool_func: Callable) -> Callable:
        # Loads user config from database
        # Injects into Context
        # Calls original tool function
```

**Process**:
1. Extract user_id from FastMCP Context
2. Load user config from database
3. Attach config to Context as `ctx.tool_config`
4. Call original tool function
5. Tool accesses config via Context

### 5. Migration Helpers (`automagik_tools/hub/tool_migration_helpers.py`)

**Utilities for Tool Migration**:

```python
# Context-aware config loader
_get_config = make_context_aware_config_loader(ConfigClass, "tool_name")

# Context-aware client factory
_ensure_client = make_context_aware_client_factory(ClientClass, _get_config, "tool_name")

# Complete migration helper
helper = ToolMigrationHelper(
    tool_name="my_tool",
    config_class=MyToolConfig,
    client_class=MyToolClient
)
```

## User Flow

### 1. User Authentication
1. User visits Hub UI
2. Authenticates via WorkOS AuthKit
3. Receives JWT token with user_id

### 2. Tool Configuration
1. User selects tool from catalogue
2. Provides tool-specific configuration (API keys, endpoints, etc.)
3. Configuration saved to database (encrypted if credentials)

### 3. Tool Usage
1. User calls tool function via MCP
2. Hub middleware extracts user_id from token
3. HubToolWrapper loads user config from database
4. Config injected into FastMCP Context
5. Tool function executes with user config
6. Result returned to user

### 4. Tool Instance Management
1. User starts tool instance via API (`/api/user/tools/{tool_name}/start`)
2. ToolInstanceManager creates isolated instance with user config
3. Instance runs in dedicated environment
4. User can stop/refresh instance as needed

## API Endpoints

### Tool Catalogue (Public)
- `GET /api/tools/catalogue` - List all available tools
- `GET /api/tools/{tool_name}/metadata` - Get tool metadata
- `GET /api/tools/{tool_name}/schema` - Get configuration schema

### User Tool Management (Authenticated)
- `GET /api/user/tools` - List user's configured tools
- `POST /api/user/tools/{tool_name}` - Configure tool
- `GET /api/user/tools/{tool_name}` - Get tool configuration
- `PUT /api/user/tools/{tool_name}` - Update configuration
- `DELETE /api/user/tools/{tool_name}` - Remove tool

### Tool Lifecycle (Authenticated)
- `GET /api/user/tools/{tool_name}/status` - Get instance status
- `POST /api/user/tools/{tool_name}/start` - Start tool instance
- `POST /api/user/tools/{tool_name}/stop` - Stop instance
- `POST /api/user/tools/{tool_name}/refresh` - Reload configuration

### Authentication
- `GET /api/auth/authorize` - Get WorkOS authorization URL
- `POST /api/auth/callback` - Handle OAuth callback
- `GET /api/auth/user` - Get current user info

## Tool Migration Guide

### Making a Tool Multi-Tenant Compatible

#### Option 1: Quick Migration (Recommended)

Add Context parameter to tool initialization:

```python
# In your tool's __init__.py

from typing import Optional
from fastmcp import Context
from automagik_tools.hub.config_injection import get_or_create_user_config

# Original (single-tenant)
def _ensure_client() -> Client:
    global _config
    if not _config:
        _config = MyToolConfig()
    return Client(_config)

# Updated (multi-tenant compatible)
def _ensure_client(ctx: Optional[Context] = None) -> Client:
    config = get_or_create_user_config(ctx, MyToolConfig, "my_tool")
    return Client(config)

# Update all @mcp.tool() functions to accept Context
@mcp.tool()
async def my_function(param1: str, ctx: Context = None) -> str:
    client = _ensure_client(ctx)  # Pass context
    # ... rest of function
```

#### Option 2: Using Migration Helper

```python
# In your tool's __init__.py

from automagik_tools.hub.tool_migration_helpers import ToolMigrationHelper

# Create helper at module level
_mt_helper = ToolMigrationHelper(
    tool_name="my_tool",
    config_class=MyToolConfig,
    client_class=MyToolClient,
    singleton=True  # Use singleton for global client
)

# Replace _ensure_client
def _ensure_client(ctx: Optional[Context] = None) -> MyToolClient:
    return _mt_helper.get_client(ctx)

# Add ctx parameter to all tool functions
@mcp.tool()
async def my_function(param1: str, ctx: Context = None) -> str:
    client = _ensure_client(ctx)
    # ... rest of function
```

#### Option 3: Full Refactoring (Best Practice)

Implement `MultiTenantToolMixin`:

```python
from automagik_tools.hub.multi_tenant_tool import MultiTenantToolMixin

class MyTool(MultiTenantToolMixin[MyToolConfig]):
    tool_name = "my_tool"

    async def get_client(self, ctx: Context) -> MyToolClient:
        config = await self.get_user_config(ctx, MyToolConfig)
        return MyToolClient(config)

# Use in tool functions
_tool = MyTool()

@mcp.tool()
async def my_function(param1: str, ctx: Context = None) -> str:
    client = await _tool.get_client(ctx)
    # ... rest of function
```

### Configuration Schema

Each tool should define its configuration schema for the UI:

```python
def get_metadata() -> Dict[str, Any]:
    return {
        "name": "my_tool",
        "description": "My awesome tool",
        "config_schema": {
            "type": "object",
            "properties": {
                "api_key": {
                    "type": "string",
                    "description": "API key for authentication",
                    "secret": True  # Will be encrypted
                },
                "base_url": {
                    "type": "string",
                    "description": "Base URL for API",
                    "default": "https://api.example.com"
                },
                "timeout": {
                    "type": "integer",
                    "description": "Request timeout in seconds",
                    "default": 30
                }
            },
            "required": ["api_key"]
        },
        "auth_type": "api_key",  # or "oauth", "none"
    }
```

## Security Considerations

### 1. Credential Encryption
- All sensitive configuration (API keys, tokens) encrypted at rest
- Uses Fernet symmetric encryption
- Encryption key stored in environment variable `ENCRYPTION_KEY`

### 2. User Isolation
- Each user's configuration stored separately
- Tool instances isolated per user
- No data leakage between users

### 3. Authentication
- WorkOS AuthKit for OAuth
- JWT tokens for API access
- Token validation on every request

### 4. Authorization
- Users can only access their own configurations
- Users can only manage their own tool instances
- Admin functions require special permissions (future)

## Performance Considerations

### 1. Configuration Caching
- User configs cached in memory with TTL
- Reduces database queries
- Invalidated on configuration updates

### 2. Client Pooling
- Reuse client instances when possible
- Per-user client pools
- Automatic cleanup of idle clients

### 3. Instance Lifecycle
- Lazy instance creation (only when needed)
- Automatic shutdown of idle instances
- Resource limits per user

## Backward Compatibility

### Single-Tenant Mode (stdio)
Tools continue to work in single-tenant mode:
- No Context provided → Falls back to global config
- Environment variables used as before
- No database required

### Multi-Tenant Mode (HTTP)
Tools work in multi-tenant mode:
- Context provided with user_id
- User config loaded from database
- Isolated execution per user

## Testing Multi-Tenant Functionality

### Unit Tests
```python
import pytest
from fastmcp import Context
from automagik_tools.tools.my_tool import _ensure_client

async def test_multi_tenant_config():
    # Create mock context with user_id
    ctx = Context()
    ctx.set_state("user_id", "test_user@example.com")

    # Mock config in context
    ctx.tool_config = {"api_key": "test_key"}

    # Get client with user config
    client = _ensure_client(ctx)

    # Verify user config was used
    assert client.config.api_key == "test_key"
```

### Integration Tests
```python
async def test_tool_lifecycle():
    # Start tool
    result = await client.post(
        "/api/user/tools/my_tool/start",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert result.status_code == 200

    # Check status
    status = await client.get(
        "/api/user/tools/my_tool/status",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert status.json()["status"] == "running"

    # Stop tool
    result = await client.post(
        "/api/user/tools/my_tool/stop",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert result.status_code == 200
```

## Current Status

### Completed
✅ Database models for user configurations
✅ Tool lifecycle management system
✅ Configuration injection utilities
✅ Migration helper utilities
✅ Multi-tenant base classes
✅ API endpoints for tool management
✅ Authentication integration (WorkOS)
✅ Hub infrastructure

### In Progress
🔄 Tool wrapping in Hub server
🔄 Migrating individual tools
🔄 End-to-end testing

### Planned
📋 Configuration caching layer
📋 Client connection pooling
📋 Resource usage monitoring
📋 Admin dashboard
📋 Automated tool migration script

## Examples

### Example 1: OMNI Tool (Multi-Tenant Ready)
The OMNI tool supports multi-tenant operation:
- Per-user OMNI API credentials
- Isolated instances per user
- Dynamic configuration loading

### Example 2: Google Calendar (OAuth)
Google Calendar uses OAuth with per-user credentials:
- Each user authenticates their own Google account
- Credentials stored in database
- Automatic token refresh

### Example 3: Spark Workflows (Stateful)
Spark maintains per-user workflow state:
- Isolated workflow execution
- User-specific workflow definitions
- State persistence per user

## Troubleshooting

### Configuration Not Loading
**Problem**: Tool uses global config instead of user config
**Solution**: Ensure Context is passed to tool functions and HubToolWrapper is applied

### Authentication Errors
**Problem**: 401 Unauthorized errors
**Solution**: Check WorkOS configuration and token validity

### Tool Instance Won't Start
**Problem**: Tool instance fails to start
**Solution**: Check user configuration is valid and complete

### Database Connection Issues
**Problem**: Cannot load/save configurations
**Solution**: Verify DATABASE_URL environment variable and database is initialized

## References

- [FastMCP Documentation](https://github.com/jlowin/fastmcp)
- [WorkOS AuthKit](https://workos.com/docs/authkit)
- [Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
- [Tool Creation Guide](./TOOL_CREATION_GUIDE.md)
