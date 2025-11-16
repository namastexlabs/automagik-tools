# Analysis: Spark MCP Tool

## Overview
- **Name**: spark
- **Type**: API Integration (Workflow Orchestration)
- **Complexity**: Medium-High
- **Estimated Time**: 6-8 hours

## Requirements

### Functional Requirements
1. **Workflow Management**
   - List synchronized workflows (agents, teams, structured workflows)
   - Get specific workflow details
   - Execute workflows with input data
   - Delete workflows
   
2. **Remote Agent Discovery**
   - List available remote agents from AutoMagik Agents API
   - Get specific remote agent details
   - Sync agents from remote sources
   
3. **AutoMagik Hive Integration**
   - Support for agents (`hive_agent`)
   - Support for teams (`hive_team`)
   - Support for structured workflows (`hive_workflow`)
   
4. **Task Management**
   - List task executions with filtering
   - Get specific task details
   - Delete tasks
   - Monitor task status
   
5. **Schedule Management**
   - Create schedules (interval/cron)
   - List active schedules
   - Update/delete schedules
   - Enable/disable schedules
   
6. **Source Management**
   - Add workflow sources (AutoMagik Agents, AutoMagik Hive)
   - List configured sources
   - Update/delete sources

### Technical Requirements
- **Authentication**: API Key via X-API-Key header
- **API Version**: v1
- **Base URL**: Configurable (default: http://localhost:8883)
- **Rate Limits**: None documented
- **Dependencies**: httpx, fastmcp, pydantic
- **Response Format**: JSON with consistent structure
- **Error Handling**: Standard HTTP status codes with detail messages

## Similar Tools Analysis

### AutoMagik Tool (`automagik_tools/tools/automagik/`)
- **Pattern**: FastMCP server with async HTTP client
- **Structure**: __init__.py with server, config.py for settings, __main__.py for CLI
- **Config**: Pydantic BaseSettings with env prefix
- **Reusable**: HTTP request patterns, error handling, FastMCP setup

### AutoMagik Hive Tool (`automagik_tools/tools/automagik_hive/`)
- **Pattern**: Similar API integration with FastMCP
- **Structure**: Separate server.py for complex logic
- **Config**: Similar Pydantic configuration
- **Reusable**: API client patterns, response processing

### Key Patterns to Reuse
1. FastMCP server creation with proper metadata
2. Pydantic configuration with environment variables
3. Async HTTP client with timeout handling
4. Structured error responses
5. Tool registration via entry points

## Implementation Plan

### File Structure
```
automagik_tools/tools/spark/
├── __init__.py       # FastMCP server with all API endpoints
├── __main__.py       # CLI entry point (standard template)
├── config.py         # Pydantic settings for API configuration
├── client.py         # HTTP client wrapper for Spark API
└── models.py         # Pydantic models for request/response validation

tests/tools/
└── test_spark.py     # Comprehensive test suite
```

### Key Components

1. **Server Creation** (`__init__.py`):
   ```python
   # Core MCP tools for Spark API
   - list_workflows()      # GET /api/v1/workflows
   - get_workflow()        # GET /api/v1/workflows/{id}
   - run_workflow()        # POST /api/v1/workflows/{id}/run
   - delete_workflow()     # DELETE /api/v1/workflows/{id}
   
   - list_remote_agents()  # GET /api/v1/workflows/remote
   - sync_agent()          # POST /api/v1/workflows/sync/{id}
   
   - list_tasks()          # GET /api/v1/tasks
   - get_task()            # GET /api/v1/tasks/{id}
   
   - list_schedules()      # GET /api/v1/schedules
   - create_schedule()     # POST /api/v1/schedules
   - delete_schedule()     # DELETE /api/v1/schedules/{id}
   
   - list_sources()        # GET /api/v1/sources
   - add_source()          # POST /api/v1/sources
   
   - get_health()          # GET /health
   ```

2. **Configuration** (`config.py`):
   ```python
   class SparkConfig(BaseSettings):
       api_key: str            # SPARK_API_KEY
       base_url: str           # SPARK_BASE_URL (default: http://localhost:8883)
       timeout: int            # SPARK_TIMEOUT (default: 30)
       
       model_config = {
           "env_prefix": "SPARK_",
           "env_file": ".env"
       }
   ```

3. **HTTP Client** (`client.py`):
   - Async HTTP client with proper headers
   - Error handling and retry logic
   - Response validation
   - Authentication header injection

4. **Data Models** (`models.py`):
   - Workflow model (id, name, description, source, type)
   - Task model (id, status, input_data, output_data)
   - Schedule model (id, workflow_id, schedule_type, expression)
   - Source model (name, source_type, url, api_key)

5. **Entry Point Registration**:
   - Tools are auto-discovered from tools directory
   - No manual registration needed in pyproject.toml

## Risk Assessment

- **Complexity Risks**: 
  - Multiple workflow types (agents, teams, structured) need different handling
  - Async task execution requires polling for status
  - Schedule management has complex cron/interval expressions
  
- **Dependency Risks**: 
  - Depends on external Spark API being available
  - Requires proper API key configuration
  
- **API Limitations**: 
  - No documented rate limits but should implement backoff
  - Long-running workflows may timeout
  
- **Testing Challenges**: 
  - Need to mock complex workflow responses
  - Different response formats for different workflow types
  - Async task execution needs careful mocking

## Testing Strategy

1. **Unit Tests**:
   - Test each MCP tool function
   - Mock HTTP responses for all endpoints
   - Test error handling scenarios
   - Validate input/output transformations

2. **Integration Tests**:
   - Test hub mounting and discovery
   - Test configuration loading
   - Test tool metadata exposure

3. **MCP Compliance Tests**:
   - Verify tool registration
   - Test resource definitions
   - Validate error responses

4. **Mocking Strategy**:
   - Use pytest fixtures for mock responses
   - Create sample data for all workflow types
   - Mock async task completion scenarios
   - Use httpx_mock for HTTP client testing

## Implementation Priority

1. **Phase 1 - Core Workflow Operations** (2 hours):
   - list_workflows, get_workflow, run_workflow
   - Basic client and configuration

2. **Phase 2 - Task Management** (1 hour):
   - list_tasks, get_task
   - Task status monitoring

3. **Phase 3 - Schedule Management** (2 hours):
   - CRUD operations for schedules
   - Cron/interval expression handling

4. **Phase 4 - Source & Remote Management** (2 hours):
   - Source configuration
   - Remote agent discovery and sync

5. **Phase 5 - Testing & Polish** (1-2 hours):
   - Comprehensive test suite
   - Documentation
   - Error handling improvements

## Success Criteria
- [x] All major endpoints implemented (workflows, tasks, schedules, sources)
- [x] Configuration working with environment variables
- [x] Tests passing with >30% coverage
- [x] Hub integration successful
- [x] Documentation complete
- [x] Support for all workflow types (agents, teams, structured)
- [x] Proper error handling and responses

## Special Considerations

1. **Workflow Type Differentiation**:
   - Different data structures for agents vs teams vs workflows
   - Type field in data object indicates handling needed
   - Visual indicators (icons, colors) should be preserved

2. **Session Management**:
   - Some workflows maintain session state
   - Session IDs in responses should be tracked
   - Consider adding session continuation support

3. **Real-time Updates**:
   - Tasks have async execution
   - Consider adding status polling helpers
   - May want SSE/WebSocket support in future

4. **Multi-Source Support**:
   - Support multiple AutoMagik instances
   - Support both Agents and Hive APIs
   - Maintain source attribution in workflows

## Notes for BUILDER

- Use existing automagik tool as reference for HTTP client patterns
- Follow the exact file structure from other tools
- Ensure all responses include proper error details
- Test with actual Spark API if possible (running on localhost:8883)
- Consider adding helper functions for common patterns (polling, scheduling)
- Make sure to handle all three workflow types properly