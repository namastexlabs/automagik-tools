# Analysis: OMNI MCP Tool

## Overview
- **Name**: omni
- **Type**: Multi-tenant omnichannel messaging API client
- **Complexity**: High (30+ endpoints, requires intelligent aggregation)
- **Estimated Time**: 8-10 hours

## Requirements

### Functional Requirements
1. **Instance Management** (Critical)
   - CRUD operations for messaging instances
   - Multi-channel support (WhatsApp, Slack, Discord)
   - QR code generation and connection status
   - Instance restart/logout functionality

2. **Messaging Capabilities** (High Priority)
   - Send text, media, audio, stickers, contacts
   - Reaction management
   - Profile operations (fetch/update)
   - Generic enough for any instance type

3. **Trace Management** (Medium Priority)
   - List and filter message traces
   - Analytics and summaries
   - Payload inspection
   - Cleanup operations

4. **Webhook Management** (Low Priority)
   - Evolution webhook endpoints
   - Test capture functionality

### Technical Requirements
- **Authentication**: Bearer token (HTTP Bearer)
- **API Version**: v1
- **Base URL**: Configurable (default: http://localhost:8882)
- **Rate Limits**: Not specified (assume standard)
- **Dependencies**: FastMCP, httpx, pydantic

## Intelligent Endpoint Aggregation Strategy

### 1. **Instance Operations** (manage_instances)
Single tool combining:
- list_instances (GET /instances)
- get_instance (GET /instances/{name})
- create_instance (POST /instances)
- update_instance (PUT /instances/{name})
- delete_instance (DELETE /instances/{name})
- set_default_instance (POST /instances/{name}/set-default)
- get_instance_status (GET /instances/{name}/status)
- get_instance_qr (GET /instances/{name}/qr)
- restart_instance (POST /instances/{name}/restart)
- logout_instance (POST /instances/{name}/logout)

### 2. **Messaging Operations** (send_message)
Unified messaging interface with type parameter:
- send_text (POST /instance/{name}/send-text)
- send_media (POST /instance/{name}/send-media)
- send_audio (POST /instance/{name}/send-audio)
- send_sticker (POST /instance/{name}/send-sticker)
- send_contact (POST /instance/{name}/send-contact)
- send_reaction (POST /instance/{name}/send-reaction)

### 3. **Trace Operations** (manage_traces)
Combined trace management:
- list_traces (GET /traces with filters)
- get_trace (GET /traces/{id})
- get_trace_payloads (GET /traces/{id}/payloads)
- get_trace_analytics (GET /traces/analytics/summary)
- get_traces_by_phone (GET /traces/phone/{number})
- cleanup_traces (DELETE /traces/cleanup)

### 4. **Profile Operations** (manage_profiles)
Profile management:
- fetch_profile (POST /instance/{name}/fetch-profile)
- update_profile_picture (POST /instance/{name}/update-profile-picture)

## Similar Tools Analysis

### automagik_workflows_v2
- **Pattern**: FastMCP server with session management and streaming
- **Structure**: Separate client, models, session_manager
- **Config**: Pydantic v2 with model_config

### genie
- **Pattern**: Complex MCP orchestrator with multi-tool access
- **Structure**: MCP wrapper pattern for subprocess isolation
- **Config**: Environment-based with validation

### evolution_api
- **Pattern**: Direct API client with specific Evolution endpoints
- **Structure**: Simple client-based architecture
- **Config**: Basic Pydantic settings

## Implementation Plan

### File Structure
```
automagik_tools/tools/omni/
├── __init__.py       # FastMCP server with intelligent tool aggregation
├── __main__.py       # CLI entry point
├── config.py         # Pydantic settings with OMNI API config
├── client.py         # HTTP client for OMNI API
├── models.py         # Request/response models
└── README.md         # Tool documentation

tests/tools/
└── test_omni.py      # Comprehensive test suite
```

### Key Components

1. **Server Creation** (`__init__.py`):
   - 4 main FastMCP tools (manage_instances, send_message, manage_traces, manage_profiles)
   - Intelligent parameter handling for operation types
   - Context-aware responses

2. **Client Implementation** (`client.py`):
   - Async HTTP client using httpx
   - Bearer token authentication
   - Error handling and retries
   - Response validation

3. **Configuration** (`config.py`):
   - OMNI_API_URL (default: http://localhost:8882)
   - OMNI_API_KEY (required)
   - DEFAULT_INSTANCE (optional)
   - TIMEOUT settings

4. **Models** (`models.py`):
   - Pydantic models for all request/response types
   - Instance configurations
   - Message types union
   - Trace filters

5. **Entry Point Registration**:
   - Update pyproject.toml with omni entry point
   - Add to automagik_tools.plugins

## Risk Assessment

- **Complexity Risks**: 
  - Large number of endpoints requires careful aggregation
  - Multiple message types need unified interface
  - Instance management state tracking

- **Dependency Risks**: 
  - OMNI API availability and stability
  - Evolution API integration complexity

- **API Limitations**: 
  - No documented rate limits (need defensive coding)
  - Multi-tenant complexity with instance management

- **Testing Challenges**: 
  - Need to mock OMNI API responses
  - Complex state management for instances
  - Message type variations

## Testing Strategy

- **Unit Tests**: 
  - Client methods
  - Model validation
  - Tool parameter parsing

- **Integration Tests**: 
  - Hub mounting
  - Tool discovery
  - End-to-end workflows

- **MCP Compliance**: 
  - Protocol adherence
  - Error handling
  - Response formats

- **Mocking Strategy**: 
  - Mock httpx responses
  - Fixture-based test data
  - State simulation for instances

## Success Criteria

- [x] All major endpoint groups intelligently aggregated
- [x] Configuration working with environment variables
- [x] Tests created (35 tests covering all functionality)
- [x] Hub integration successful (tool is discoverable)
- [x] Documentation complete (comprehensive README with examples)
- [x] Error handling comprehensive (all error cases handled)
- [x] Generic messaging interface implemented (6 message types)
- [x] Trace analytics functional (full trace management)

## Implementation Notes

### Intelligent Design Decisions

1. **Aggregation Strategy**: Group by resource type (instances, messages, traces, profiles) rather than individual endpoints
2. **Message Abstraction**: Single `send_message` tool with type parameter for all message types
3. **Instance Context**: Optional default instance to simplify operations
4. **Filter Builder**: Smart trace filtering with multiple parameters
5. **Batch Operations**: Support bulk operations where applicable

### Reusable Patterns from Existing Tools

1. From `automagik_workflows_v2`:
   - Session management pattern
   - Streaming response handling
   - Progress tracking

2. From `genie`:
   - Complex configuration validation
   - Multi-server orchestration concepts

3. From `evolution_api`:
   - Direct API client pattern
   - Simple httpx usage

## Implementation Status (COMPLETED)

### ✅ BUILDER Phase Complete
1. ✅ Implemented core client with httpx (client.py)
2. ✅ Created Pydantic models for all operations (models.py)
3. ✅ Built 4 main FastMCP tools with intelligent routing
4. ✅ Added comprehensive error handling
5. ✅ Created detailed README with examples

### ✅ TESTER Phase Complete
1. ✅ Created comprehensive test suite (35 tests)
2. ✅ Tested all 4 main tools
3. ✅ Added error handling tests
4. ✅ Added edge case tests
5. ✅ Added MCP protocol compliance tests

### 📊 Final Statistics
- **Endpoints Aggregated**: 30+ → 4 tools
- **Message Types**: 6 (text, media, audio, sticker, contact, reaction)
- **Instance Operations**: 10 (CRUD + status, QR, restart, logout)
- **Trace Operations**: 6 (list, get, payloads, analytics, by_phone, cleanup)
- **Profile Operations**: 2 (fetch, update_picture)
- **Test Coverage**: 35 comprehensive tests
- **Documentation**: Complete with examples