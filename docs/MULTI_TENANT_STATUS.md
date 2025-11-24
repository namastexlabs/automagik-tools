# Multi-Tenant Hub - Tool Compatibility Status

## Overview

The Automagik Tools Hub uses WorkOS AuthKit for multi-tenant user authentication. Each tool must be adapted to work with **per-user credentials** rather than global configuration.

## Authentication Architecture

```
User → WorkOS AuthKit → Hub (FastMCP) → Tool (with user_id in Context)
                                        ↓
                                  Database (per-user credentials)
```

## Tool Status

### ✅ Multi-Tenant Ready

**Google Workspace Tools** (9 tools)
- ✅ google_gmail - Uses `user_google_email` parameter
- ✅ google_calendar - Uses `user_google_email` parameter
- ✅ google_drive - Uses `user_google_email` parameter
- ✅ google_docs - Uses `user_google_email` parameter
- ✅ google_sheets - Uses `user_google_email` parameter
- ✅ google_slides - Uses `user_google_email` parameter
- ✅ google_forms - Uses `user_google_email` parameter
- ✅ google_tasks - Uses `user_google_email` parameter
- ✅ google_chat - Uses `user_google_email` parameter

**Pattern**: All Google tools use `@require_google_service()` decorator which extracts `user_google_email` from Context and loads per-user OAuth credentials from database.

### ⚠️ Needs Adaptation for Multi-Tenant

**WhatsApp Tools**
- ❌ **evolution_api** - Uses global `client` object
  - **Issue**: Single shared API key and instance
  - **Fix Needed**: Accept `user_id` from Context, load per-user Evolution credentials
  - **Impact**: Medium - Each user needs their own Evolution instance

- ❌ **omni** - Uses global `client` object
  - **Issue**: Single shared OMNI API connection
  - **Fix Needed**: Accept `user_id` from Context, support per-user OMNI instances
  - **Impact**: High - Core WhatsApp functionality

- ❌ **genie-omni** - Same as `omni`
  - **Issue**: Agent-first wrapper around `omni`, inherits same limitation
  - **Fix Needed**: Same as `omni` tool
  - **Impact**: High - Agent workflows depend on this

**AI Tools**
- ❌ **gemini_assistant** - Global session storage
  - **Issue**: Session IDs are global, no user isolation
  - **Fix Needed**: Prefix session IDs with `user_id`, isolate file uploads
  - **Impact**: High - Session leakage between users

- ❌ **genie_tool** - Global OpenAI client and memory
  - **Issue**: Single shared OpenAI API key, shared memory database
  - **Fix Needed**: Support per-user OpenAI keys, isolate memory by user_id
  - **Impact**: High - Agent orchestration core

**Workflow Tools**
- ❌ **spark** - Global API client
  - **Issue**: Single shared Spark API connection
  - **Fix Needed**: Support per-user Spark instances or API keys
  - **Impact**: Medium - Workflow orchestration

- ❌ **automagik_hive** - Global API client
  - **Issue**: Single shared Hive API connection
  - **Fix Needed**: Support per-user Hive instances
  - **Impact**: Medium - Agent coordination

**Other Tools**
- ⚠️ **json_to_google_docs** - Service account auth (different model)
  - **Issue**: Uses service account, not user OAuth
  - **Status**: May not need multi-tenant (service account is already isolated)
  - **Impact**: Low - Specialized use case

- ✅ **wait** - No authentication needed
  - **Status**: Utility tool, no credentials
  - **Impact**: None

## Required Changes

### Pattern: Context-Aware Tool Design

**Current (Single-Tenant)**:
```python
# Global config and client
config = EvolutionAPIConfig()
client = EvolutionAPIClient(config)

@mcp.tool()
async def send_message(message: str):
    # Uses global client
    return await client.send_text_message(instance, message, number)
```

**Required (Multi-Tenant)**:
```python
# Config factory function
def get_user_config(user_id: str) -> EvolutionAPIConfig:
    # Load from database
    credentials = await db.get_credentials(user_id, "evolution_api")
    return EvolutionAPIConfig(**credentials)

@mcp.tool()
async def send_message(message: str, ctx: Context):
    # Extract user from context
    user_id = ctx.get_state("user_id")

    # Get user-specific config
    config = await get_user_config(user_id)
    client = EvolutionAPIClient(config)

    # Use per-user client
    return await client.send_text_message(instance, message, number)
```

### Database Schema for Per-User Credentials

Already implemented in Hub:

```python
class Credential(Base):
    id: int
    user_id: str  # From WorkOS AuthKit
    tool_name: str  # e.g., "evolution_api"
    provider: str  # e.g., "evolution"
    encrypted_secrets: str  # JSON with API keys, URLs, etc.
```

## Implementation Priority

### Phase 1: Critical (Block Hub Launch)
1. **gemini_assistant** - Session isolation
2. **genie_tool** - Memory/API key isolation
3. **omni / genie-omni** - WhatsApp core functionality

### Phase 2: High Priority
4. **evolution_api** - Alternative WhatsApp tool
5. **spark** - Workflow orchestration
6. **automagik_hive** - Agent coordination

### Phase 3: Low Priority
7. **json_to_google_docs** - Evaluate if service account model is acceptable

## Testing Multi-Tenant Tools

Each adapted tool must pass:

1. **Isolation Test**: Two users cannot access each other's data
2. **Context Test**: Tool correctly extracts `user_id` from Context
3. **Credential Test**: Tool loads correct per-user credentials from database
4. **Failure Test**: Tool fails gracefully when user has no credentials

## Migration Strategy

1. **Add Context parameter**: `async def tool_func(param: str, ctx: Context)`
2. **Extract user_id**: `user_id = ctx.get_state("user_id")`
3. **Load credentials**: `creds = await db.get_credentials(user_id, tool_name)`
4. **Create client**: `client = ToolClient(creds)`
5. **Execute operation**: `return await client.operation()`
6. **Update tests**: Add multi-user test cases

## Resources

- **Hub Implementation**: `automagik_tools/hub_http.py`
- **Credential Store**: `automagik_tools/hub/credentials.py`
- **Database Models**: `automagik_tools/hub/models.py`
- **Google Tools Example**: `automagik_tools/tools/google_workspace/`
