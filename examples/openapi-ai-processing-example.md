# OpenAPI AI Processing Example

This example demonstrates the dramatic improvement in code quality when using AI to process OpenAPI specifications for static tool generation.

## Original OpenAPI Specification

```json
{
  "paths": {
    "/api/v1/users/{user_id}/sessions/{session_id}/messages": {
      "get": {
        "operationId": "get_user_session_messages_api_v1_users__user_id__sessions__session_id__messages_get",
        "summary": "Get messages for a user session",
        "parameters": [
          {
            "name": "user_id",
            "in": "path",
            "required": true,
            "schema": {"type": "string"},
            "description": "User identifier"
          },
          {
            "name": "session_id", 
            "in": "path",
            "required": true,
            "schema": {"type": "string"},
            "description": "Session identifier"
          },
          {
            "name": "limit",
            "in": "query",
            "required": false,
            "schema": {"type": "integer", "default": 100},
            "description": "Maximum number of messages to return"
          }
        ]
      }
    },
    "/api/v1/agent/claude-code/{workflow_name}/run": {
      "post": {
        "operationId": "run_claude_code_workflow_api_v1_agent_claude_code__workflow_name__run_post",
        "summary": "Run a Claude Code workflow",
        "parameters": [
          {
            "name": "workflow_name",
            "in": "path",
            "required": true,
            "schema": {"type": "string"}
          }
        ],
        "requestBody": {
          "content": {
            "application/json": {
              "schema": {
                "type": "object",
                "properties": {
                  "parameters": {"type": "object"},
                  "timeout": {"type": "integer"}
                }
              }
            }
          }
        }
      }
    }
  }
}
```

## Without AI Processing (Standard Generation)

```python
@mcp.tool()
async def get_user_session_messages_api_v1_users__user_id__sessions__session_id__messages_get(
    user_id: str, 
    session_id: str, 
    limit: Optional[int] = None,
    ctx: Optional[Context] = None
) -> Dict[str, Any]:
    """
    Get messages for a user session
    
    Endpoint: GET /api/v1/users/{user_id}/sessions/{session_id}/messages
    
    Args:
        user_id: User identifier
        session_id: Session identifier  
        limit: Maximum number of messages to return
    """
    # ... implementation ...

@mcp.tool()
async def run_claude_code_workflow_api_v1_agent_claude_code__workflow_name__run_post(
    workflow_name: str,
    data: Optional[Dict[str, Any]] = None,
    ctx: Optional[Context] = None
) -> Dict[str, Any]:
    """
    Run a Claude Code workflow
    
    Endpoint: POST /api/v1/agent/claude-code/{workflow_name}/run
    
    Args:
        workflow_name: 
        data: Request body data
    """
    # ... implementation ...
```

## With AI Processing

```python
@mcp.tool()
async def get_messages(
    user_id: str,
    session_id: str, 
    limit: Optional[int] = None,
    ctx: Optional[Context] = None
) -> Dict[str, Any]:
    """
    Retrieve messages from a specific user session
    
    Endpoint: GET /api/v1/users/{user_id}/sessions/{session_id}/messages
    
    Args:
        user_id: Unique identifier for the user
        session_id: Unique identifier for the conversation session
        limit: Maximum number of messages to retrieve (default: 100, max: 1000)
    
    Returns:
        Dict containing a list of messages with timestamps and metadata
    
    Example:
        messages = await get_messages("user123", "session456", limit=50)
    """
    # ... implementation ...

@mcp.tool()
async def run_workflow(
    workflow_name: str,
    data: Optional[Dict[str, Any]] = None,
    ctx: Optional[Context] = None
) -> Dict[str, Any]:
    """
    Execute a Claude Code workflow with optional parameters
    
    Endpoint: POST /api/v1/agent/claude-code/{workflow_name}/run
    
    Args:
        workflow_name: Name of the workflow to execute (e.g., "data-analysis", "code-review")
        data: Workflow configuration containing:
            - parameters: Dict of workflow-specific parameters
            - timeout: Maximum execution time in seconds (optional)
    
    Returns:
        Dict with workflow execution ID and status
    
    Example:
        result = await run_workflow(
            "code-review",
            data={"parameters": {"branch": "main"}, "timeout": 300}
        )
    """
    # ... implementation ...
```

## Key Improvements with AI Processing

### 1. Function Names
- **Before**: `get_user_session_messages_api_v1_users__user_id__sessions__session_id__messages_get` (78 chars)
- **After**: `get_messages` (12 chars)
- **Improvement**: 85% shorter, instantly understandable

### 2. Tool Descriptions
- **Before**: Generic copy of the summary
- **After**: Specific, action-oriented descriptions that explain the business value

### 3. Parameter Documentation
- **Before**: Basic descriptions copied from OpenAPI
- **After**: Enhanced with:
  - Valid value ranges
  - Default values
  - Format specifications
  - Practical examples

### 4. Docstrings
- **Before**: Minimal documentation
- **After**: Comprehensive Google-style docstrings with:
  - Clear descriptions
  - Detailed parameter docs
  - Return value specifications
  - Usage examples

### 5. Organization
- Functions are automatically categorized (e.g., "messaging", "workflow_execution")
- Related operations are grouped together
- Consistent naming patterns across the entire API

## How to Use AI Processing

### Command Line

```bash
# Basic usage with AI
python scripts/create_tool_from_openapi.py \
  --url https://api.example.com/openapi.json \
  --name "My API" \
  --use-ai

# Specify AI model
python scripts/create_tool_from_openapi.py \
  --url https://api.example.com/openapi.json \
  --name "My API" \
  --use-ai \
  --ai-model gpt-3.5-turbo  # Faster and cheaper

# Provide API key directly
python scripts/create_tool_from_openapi.py \
  --url https://api.example.com/openapi.json \
  --name "My API" \
  --use-ai \
  --openai-key sk-...
```

### Environment Setup

```bash
# Set OpenAI API key
export OPENAI_API_KEY=sk-...

# Install required packages
pip install agno openai
```

## Performance Considerations

- **Processing Time**: AI processing adds 10-30 seconds to generation time
- **Cost**: Approximately $0.01-0.05 per API depending on size
- **Quality**: Dramatically improved code readability and documentation
- **One-Time Process**: AI runs only during initial generation, not at runtime

## Best Practices

1. **Review Generated Code**: AI suggestions should be reviewed for accuracy
2. **Provide Good Descriptions**: Better OpenAPI descriptions lead to better AI output
3. **Use Meaningful Operation IDs**: Even though AI will rename them, good IDs help
4. **Cache Results**: The processor caches results to avoid repeated API calls

## Conclusion

AI processing transforms verbose, auto-generated API integrations into clean, professional Python code that developers will actually enjoy using. The small upfront cost in time and API usage pays massive dividends in code quality and developer experience.