# Automagik Agents MCP Tool

Automagik agents templates and API

This tool was auto-generated from an OpenAPI specification.

## Features

- Full API integration with Automagik Agents
- Automatic authentication handling
- Comprehensive error handling
- Type-safe parameter validation
- Async/await support

## Configuration

### Required Environment Variables

```bash
# API authentication key
AUTOMAGIK_AGENTS_API_KEY=your-api-key-here

# Base URL for the API (optional, defaults to https://api.example.com)
AUTOMAGIK_AGENTS_BASE_URL=https://api.example.com

# Request timeout in seconds (optional, defaults to 30)
AUTOMAGIK_AGENTS_TIMEOUT=30
```

## Available Operations


### System

- **root_get**: Root Endpoint
  - Endpoint: `GET /`
- **health_check_health_get**: Health Check
  - Endpoint: `GET /health`

### Agents

- **list_agents_api_v1_agent_list_get**: List Registered Agents
  - Endpoint: `GET /api/v1/agent/list`
- **run_agent_api_v1_agent_agent_name_run_post**: Run Agent with Optional LangGraph Orchestration
  - Endpoint: `POST /api/v1/agent/{agent_name}/run`
- **run_agent_async_api_v1_agent_agent_name_run_async_post**: Run Agent Asynchronously
  - Endpoint: `POST /api/v1/agent/{agent_name}/run/async`
- **get_run_status_api_v1_run_run_id_status_get**: Get Async Run Status
  - Endpoint: `GET /api/v1/run/{run_id}/status`

### Prompts

- **list_prompts_api_v1_agent_agent_id_prompt_get**: List Prompts for Agent
  - Endpoint: `GET /api/v1/agent/{agent_id}/prompt`
- **create_prompt_api_v1_agent_agent_id_prompt_post**: Create New Prompt
  - Endpoint: `POST /api/v1/agent/{agent_id}/prompt`
- **get_prompt_api_v1_agent_agent_id_prompt_prompt_id_get**: Get Prompt by ID
  - Endpoint: `GET /api/v1/agent/{agent_id}/prompt/{prompt_id}`
- **update_prompt_api_v1_agent_agent_id_prompt_prompt_id_put**: Update Prompt
  - Endpoint: `PUT /api/v1/agent/{agent_id}/prompt/{prompt_id}`
- **delete_prompt_api_v1_agent_agent_id_prompt_prompt_id_delete**: Delete Prompt
  - Endpoint: `DELETE /api/v1/agent/{agent_id}/prompt/{prompt_id}`
- **activate_prompt_api_v1_agent_agent_id_prompt_prompt_id_activate_post**: Activate Prompt
  - Endpoint: `POST /api/v1/agent/{agent_id}/prompt/{prompt_id}/activate`
- **deactivate_prompt_api_v1_agent_agent_id_prompt_prompt_id_deactivate_post**: Deactivate Prompt
  - Endpoint: `POST /api/v1/agent/{agent_id}/prompt/{prompt_id}/deactivate`

### Sessions

- **list_sessions_route_api_v1_sessions_get**: List All Sessions
  - Endpoint: `GET /api/v1/sessions`
- **get_session_route_api_v1_sessions_session_id_or_name_get**: Get Session History
  - Endpoint: `GET /api/v1/sessions/{session_id_or_name}`
- **delete_session_route_api_v1_sessions_session_id_or_name_delete**: Delete Session
  - Endpoint: `DELETE /api/v1/sessions/{session_id_or_name}`

### Users

- **list_users_route_api_v1_users_get**: List Users
  - Endpoint: `GET /api/v1/users`
- **create_user_route_api_v1_users_post**: Create User
  - Endpoint: `POST /api/v1/users`
- **get_user_route_api_v1_users_user_identifier_get**: Get User
  - Endpoint: `GET /api/v1/users/{user_identifier}`
- **update_user_route_api_v1_users_user_identifier_put**: Update User
  - Endpoint: `PUT /api/v1/users/{user_identifier}`

... and 10 more operations

## Usage

### With automagik-tools CLI

```bash
# List available tools
automagik-tools list

# Serve this specific tool
automagik-tools serve automagik

# Serve all tools
automagik-tools serve-all
```

### In Python Code

```python
from automagik_tools.tools.automagik_agents import create_server

# Create and run server
server = create_server()
# Server is now ready to handle MCP requests
```

## Development

### Running Tests

```bash
pytest tests/tools/test_automagik_agents.py -v
```

### Testing with MCP Inspector

```bash
# Install MCP Inspector
npm install -g @anthropic/mcp-inspector

# Run the tool in one terminal
automagik-tools serve automagik

# In another terminal, connect with inspector
mcp-inspector stdio automagik-tools serve automagik
```

## API Reference

This tool was generated from an OpenAPI specification. For detailed API documentation, please refer to the original API documentation.

## Troubleshooting

### Authentication Issues

If you're getting authentication errors:
1. Verify your API key is correctly set in the environment
2. Check that the API key has the necessary permissions
3. Ensure the base URL is correct for your API instance

### Connection Issues

If you're having connection problems:
1. Check your internet connection
2. Verify the base URL is accessible
3. Check if you're behind a proxy or firewall

## Contributing

This tool was auto-generated. To update it:
1. Obtain the latest OpenAPI specification
2. Re-run the generation script
3. Test the updated tool
4. Submit a pull request
