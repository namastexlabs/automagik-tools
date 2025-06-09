# FastMCP Composition Compliance Update

## Task Summary
Updated the automagik-tools hub implementation to comply with FastMCP composition best practices based on the official documentation.

## Changes Made

### 1. Fixed Mount Syntax (hub.py and cli.py)
- **Before**: `hub.mount(f"/{tool_name}", server)` - Incorrect path prefix
- **After**: `hub.mount(mount_prefix, server)` - Correct prefix without leading slash
- Prefixes are now clean identifiers (e.g., "evolution_api" instead of "/evolution-api")

### 2. Added Proxy Mounting Support
- Detects servers with custom lifespan handlers
- Uses `as_proxy=True` for servers that need full lifecycle management
- Ensures proper client lifecycle events for mounted servers

### 3. Configured Resource Prefix Format
- Set global default to "path" format (recommended by FastMCP 2.4+)
- Added configuration in `__init__.py` to set `FASTMCP_RESOURCE_PREFIX_FORMAT=path`
- Applied to both hub.py and cli.py FastMCP instances
- Avoids legacy "protocol" format issues with underscores

### 4. Updated Documentation Strings
- Fixed tool list formatting to show correct prefix usage
- Updated mount success messages to clarify prefix-based access

## Key Improvements
1. **Correct Mounting**: Tools are now mounted with proper prefix syntax
2. **Resource URIs**: Will use path format (e.g., `resource://prefix/path`) instead of protocol format
3. **Lifecycle Management**: Proxy mounting ensures proper initialization of tools with custom lifespans
4. **Standards Compliance**: Follows FastMCP 2.2.0+ composition patterns

## Testing Recommendations
1. Run `make http-start` to test HTTP server with mounted tools
2. Verify tool prefixes work correctly (e.g., `evolution_api_send_message`)
3. Check resource URIs are properly prefixed in path format
4. Test tools with custom lifespans to ensure proxy mounting works

## Example Usage
Tools mounted with prefix "evolution_api" will have:
- Tools: `evolution_api_send_text_message`, `evolution_api_get_instance_status`
- Resources: `data://evolution_api/instances/list` (path format)