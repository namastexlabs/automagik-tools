# AI-Powered JSON-to-Markdown Processing Guide

## Overview

The automagik-tools project now includes an intelligent AI processing system that converts noisy JSON tool outputs into clean, structured Markdown for better human readability. This system uses GPT-4o-mini to interpret API responses and generate context-aware, formatted documentation.

## Features

### 🤖 **AI-Powered Processing**
- Uses GPT-4o-mini for intelligent JSON interpretation
- Context-aware formatting based on tool type
- Error explanation and solution suggestions
- Progress tracking for async operations

### 📝 **Dynamic Markdown Generation**
- Clean, structured tables for data listings
- Status indicators and progress displays
- Code blocks for technical content
- Error handling with actionable solutions

### 🔧 **Enhanced Tool Integration**
- `automagik-enhanced` - Enhanced version with AI processing
- Backward compatibility with raw JSON access
- Configurable processing options
- Development and production modes

## Quick Start

### 1. Configuration

The AI processor is configured via environment variables:

```bash
# Enable AI processing (default: true)
ENABLE_JSON_PROCESSING=true

# OpenAI configuration
OPENAI_API_KEY=your-openai-api-key

# Processing settings
JSON_PROCESSOR_MODEL=gpt-4o-mini
JSON_PROCESSOR_MAX_TOKENS=2000
JSON_PROCESSOR_TEMPERATURE=0.1
JSON_PROCESSOR_DEBUG=false
```

### 2. Using the Enhanced Tool

#### List Agents with Enhanced Formatting
```python
from automagik_tools.tools.automagik_agents_enhanced import list_agents_enhanced

# Returns beautiful Markdown table instead of raw JSON
result = await list_agents_enhanced()
print(result)
```

**Output:**
```markdown
# Available AI Agents

| Name | ID | Description | Best Use Cases |
|------|----|-----------  |----------------|
| simple | 20 | Ultra-simplified SimpleAgent | Quick setups, minimal configurations |
| claude_code | 10 | Docker-based code analysis | Long-running workflows, git integration |
| genie | 17 | Workflow orchestrator | Complex multi-step processes |
```

#### Enhanced Agent Execution
```python
from automagik_tools.tools.automagik_agents_enhanced import run_agent_enhanced

# Get clean, conversational response
result = await run_agent_enhanced(
    "simple", 
    "Help me understand asynchronous programming"
)
print(result)
```

**Output:**
```markdown
# AI Agent Response Summary

## Overview
The operation was **successful**! The agent provided comprehensive guidance.

## Agent's Response
> Asynchronous programming allows your code to handle multiple tasks concurrently...

## Next Steps
- Try implementing async/await in your code
- Consider using asyncio for I/O operations
```

### 3. Advanced Usage

#### Custom Processing
```python
from automagik_tools.ai_processors.json_markdown_processor import process_tool_output

# Process any JSON response
result = await process_tool_output(
    json_data=api_response,
    tool_name="custom_operation",
    context="User is a beginner developer"
)

print(result.markdown)  # AI-generated Markdown
print(result.raw_json)  # Original JSON data
```

#### Raw Data Access
```python
from automagik_tools.tools.automagik_agents_enhanced import get_raw_response

# Get original JSON when needed
raw_data = await get_raw_response("/api/v1/agent/list")
print(raw_data)  # Pure JSON response
```

## Architecture

### Components

1. **JSON Processor** (`json_markdown_processor.py`)
   - Core AI processing engine
   - Tool-specific prompt customization
   - Error handling and fallbacks

2. **Enhanced Response** (`enhanced_response.py`)
   - Response wrapper with both raw and processed data
   - Formatting utilities (Slack, Discord, HTML)
   - Validation and error handling

3. **Enhanced Tools** (`automagik_agents_enhanced/`)
   - Drop-in replacement for standard tools
   - AI-enhanced function variants
   - Backward compatibility options

### Processing Flow

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   MCP Tool      │ -> │  AI Processor    │ -> │  Enhanced       │
│   Raw JSON      │    │  (GPT-4o-mini)   │    │  Markdown       │
│   Response      │    │                  │    │  Output         │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## Tool-Specific Processing

The AI processor uses specialized prompts for different tool types:

### Agent Operations
- **list_agents**: Creates organized tables with capabilities
- **run_agent**: Highlights conversations and responses  
- **run_agent_async**: Explains tracking and monitoring
- **get_run_status**: Shows progress with status indicators

### Memory Management
- **create_memories_batch**: Summarizes created records in tables
- **list_memories**: Organizes by type and importance

### Workflow Operations
- **run_claude_code_workflow**: Explains workflow purpose and tracking
- **get_claude_code_run_status**: Shows detailed progress with artifacts

### Error Responses
- Clear error explanations
- Potential causes and solutions
- Step-by-step resolution guidance

## Configuration Options

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ENABLE_JSON_PROCESSING` | `true` | Enable/disable AI processing |
| `JSON_PROCESSOR_MODEL` | `gpt-4o-mini` | OpenAI model to use |
| `JSON_PROCESSOR_MAX_TOKENS` | `2000` | Maximum response tokens |
| `JSON_PROCESSOR_TEMPERATURE` | `0.1` | AI creativity (0=focused, 1=creative) |
| `JSON_PROCESSOR_DEBUG` | `false` | Include debug information |

### Debug Mode

When `JSON_PROCESSOR_DEBUG=true`, responses include:

- Processing time and model used
- Raw JSON data in collapsible sections
- Timestamp and metadata

## Examples

### Error Processing
**Input JSON:**
```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "message_content"],
      "msg": "Field required"
    }
  ]
}
```

**AI-Generated Output:**
```markdown
## ⚠️ Validation Error

### Problem
The API request is missing a required field: `message_content`

### Solution
Add the missing field to your request:
```json
{
  "message_content": "Your message here"
}
```

### Next Steps
1. Update your request to include the required field
2. Retry the API call
3. Verify the request format matches the API documentation
```

### Success Processing
**Input JSON:**
```json
{
  "run_id": "abc-123",
  "status": "completed", 
  "result": {"content": "Task completed successfully"}
}
```

**AI-Generated Output:**
```markdown
## ✅ Task Completed Successfully

**Run ID:** `abc-123`  
**Status:** Completed  

### Results
Task completed successfully

### Summary
Your asynchronous operation has finished. The results are ready for review.
```

## Best Practices

### 1. Use Enhanced Functions for User-Facing Output
```python
# ✅ Good - Clean, readable output
result = await list_agents_enhanced()
display_to_user(result)

# ❌ Avoid - Raw JSON for user display  
result = await get_raw_response("/api/v1/agent/list")
display_to_user(result)  # Users see raw JSON
```

### 2. Use Raw Access for Programmatic Processing
```python
# ✅ Good - Raw data for logic
agents = await get_raw_response("/api/v1/agent/list")
for agent in agents:
    if agent["name"] == "target_agent":
        process_agent(agent)
```

### 3. Handle Both Success and Error Cases
```python
result = await run_agent_enhanced("simple", "Hello")
if "error" in result.lower():
    # AI will explain the error clearly
    show_error_to_user(result)
else:
    # AI will format the success nicely
    show_success_to_user(result)
```

### 4. Customize Context for Better Results
```python
result = await process_tool_output(
    json_data=response,
    tool_name="create_user",
    context="User is setting up their first account"
)
```

## Troubleshooting

### Common Issues

1. **No AI Processing**
   - Check `OPENAI_API_KEY` is set
   - Verify `ENABLE_JSON_PROCESSING=true`
   - Check network connectivity

2. **Poor Quality Output**
   - Increase `JSON_PROCESSOR_MAX_TOKENS`
   - Adjust `JSON_PROCESSOR_TEMPERATURE`
   - Add more context to requests

3. **Slow Processing**
   - Use raw access for high-frequency calls
   - Cache results when appropriate
   - Consider async processing for batch operations

### Debug Mode

Enable debug mode to see processing details:

```bash
JSON_PROCESSOR_DEBUG=true
```

This adds debug sections to all outputs showing:
- Processing time
- Model used  
- Raw JSON data
- Timestamps

## Migration Guide

### From Standard to Enhanced Tools

**Before:**
```python
from automagik_tools.tools.automagik_agents import list_agents
agents = await list_agents()  # Returns raw JSON
```

**After:**
```python
from automagik_tools.tools.automagik_agents_enhanced import list_agents_enhanced
agents = await list_agents_enhanced()  # Returns formatted Markdown
```

### Gradual Migration

1. **Start with user-facing functions** - Replace display logic first
2. **Keep raw access for backends** - Use `get_raw_response()` when needed
3. **Test thoroughly** - Verify outputs meet user expectations
4. **Monitor performance** - Watch API usage and response times

## Performance Considerations

- **AI processing adds ~1-3 seconds** per request
- **Use raw access for high-frequency operations**
- **Cache enhanced responses** when displaying the same data multiple times
- **Batch processing available** for multiple requests

## Future Enhancements

- Streaming responses for large outputs
- Custom prompt templates per user/organization
- Integration with more AI models
- Caching and performance optimizations
- Custom formatting rules and templates