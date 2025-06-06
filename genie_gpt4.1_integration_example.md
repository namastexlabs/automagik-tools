# Genie GPT-4.1 Integration Example

This document shows how to integrate the GPT-4.1 optimizations into the existing Genie implementation.

## Quick Integration Steps

### 1. Import the Optimized Configuration

Add to the top of `automagik_tools/tools/genie/__init__.py`:

```python
# Import GPT-4.1 optimizations
try:
    from genie_gpt4.1_optimized_prompt import (
        GENIE_DESCRIPTION_GPT41,
        GENIE_INSTRUCTIONS_GPT41,
        create_genie_query_gpt41,
        ERROR_RESPONSE_TEMPLATE_GPT41
    )
    GPT41_OPTIMIZED = True
except ImportError:
    GPT41_OPTIMIZED = False
    logger.warning("GPT-4.1 optimizations not found, using standard configuration")
```

### 2. Update the Agent Initialization

Replace the current agent initialization (around line 188) with:

```python
# Initialize the agent inside the MCP context
if GPT41_OPTIMIZED:
    agent = Agent(
        name="Genie",
        model=OpenAIChat(id=config.model, api_key=config.openai_api_key),
        description=GENIE_DESCRIPTION_GPT41,
        # Memory configuration
        memory=memory,
        enable_agentic_memory=True,
        enable_user_memories=True,
        # Storage configuration
        storage=storage,
        add_history_to_messages=True,
        num_history_runs=max(config.num_history_runs, 10),  # More context for GPT-4.1
        # Tool access
        tools=tools_for_agent,
        # Output configuration
        markdown=True,
        show_tool_calls=True,
        debug_mode=True,
        # Verbose logging configuration
        monitoring=True,
        # GPT-4.1 optimized instructions
        instructions=GENIE_INSTRUCTIONS_GPT41,
    )
else:
    # Original configuration
    agent = Agent(
        name="Genie",
        model=OpenAIChat(id=config.model, api_key=config.openai_api_key),
        description="""I am Genie, an intelligent agent...""",
        # ... rest of original configuration
    )
```

### 3. Update Query Formatting

Replace the query preparation (around line 370) with:

```python
# Prepare the full query with context using XML format for GPT-4.1
if GPT41_OPTIMIZED:
    full_query = create_genie_query_gpt41(query, context)
else:
    # Original query formatting
    full_query = query
    if context:
        full_query = f"Context: {context}\n\nQuery: {query}"
```

### 4. Update Error Handling

Replace the error handling (around line 414) with:

```python
except Exception as e:
    error_msg = f"Genie error: {str(e)}"
    logger.error(error_msg)
    logger.exception("Full traceback:")
    
    if GPT41_OPTIMIZED:
        # Search memories for similar errors
        memory_results = "No similar errors found"
        try:
            # Search for similar errors in memory
            error_memories = memory.search_memories(
                f"error {type(e).__name__}",
                user_id=session_id,
                limit=3
            )
            if error_memories:
                memory_results = "; ".join([m.content for m in error_memories[:2]])
        except:
            pass
        
        # Determine likely cause
        likely_cause = "Unknown"
        if "MCP" in str(e) or "server" in str(e):
            likely_cause = "MCP server connection or configuration issue"
        elif "timeout" in str(e).lower():
            likely_cause = "Operation timed out - server may be slow or unreachable"
        elif "api" in str(e).lower():
            likely_cause = "API call failed - check parameters or authentication"
        
        fallback_response = ERROR_RESPONSE_TEMPLATE_GPT41.format(
            error_type=type(e).__name__,
            error_message=str(e),
            likely_cause=likely_cause,
            memory_results=memory_results,
            step1="Check if all required environment variables are set correctly",
            step2="Verify MCP server configurations are valid and servers are running",
            step3="Try breaking down your request into simpler steps",
            suggestion1="Rephrase your request with more specific details",
            suggestion2="Mention the specific tool you want to use by name",
            suggestion3="Ask me to list available tools first"
        )
        return fallback_response
    else:
        # Original error handling
        return f"❌ {error_msg}"
```

## Configuration Recommendations

### 1. Environment Variables

Add these to your `.env` file for optimal GPT-4.1 performance:

```bash
# Genie GPT-4.1 Optimizations
GENIE_MODEL=gpt-4o  # or gpt-4.1-mini when available
GENIE_HISTORY_RUNS=15  # More context for better planning
GENIE_MAX_MEMORIES=50  # More memories for learning
GENIE_TIMEOUT=600  # Longer timeout for complex workflows
```

### 2. Memory Database Schema

Consider adding indices to improve memory search performance:

```sql
-- Add to your SQLite initialization
CREATE INDEX IF NOT EXISTS idx_memories_user_content 
ON genie_memories(user_id, content);

CREATE INDEX IF NOT EXISTS idx_memories_topics 
ON genie_memories(topics);
```

### 3. Testing the Integration

Run these test cases to verify GPT-4.1 optimizations are working:

```python
import asyncio
from automagik_tools.tools.genie import ask_genie

async def test_gpt41_genie():
    # Test 1: Ambiguous request (should ask for clarification)
    print("Test 1: Ambiguous request")
    response = await ask_genie("Send a message to John")
    print(response)
    print("-" * 50)
    
    # Test 2: Learning test (should create memory)
    print("Test 2: Preference learning")
    response = await ask_genie("Remember that I prefer detailed explanations")
    print(response)
    print("-" * 50)
    
    # Test 3: Error handling (with invalid tool)
    print("Test 3: Error handling")
    response = await ask_genie("Use the nonexistent_tool to do something")
    print(response)
    print("-" * 50)
    
    # Test 4: Natural language API call
    print("Test 4: Natural language to API")
    response = await ask_genie("List all available agents and show me only the active ones")
    print(response)

# Run the tests
asyncio.run(test_gpt41_genie())
```

## Performance Monitoring

Track these metrics to measure improvement:

1. **Success Rate**: Percentage of first-attempt successful tool calls
2. **Memory Utilization**: Number of memories created and retrieved per request
3. **Error Recovery**: Percentage of errors resolved without user intervention
4. **Response Time**: Average time to complete requests
5. **Learning Curve**: Improvement in handling similar requests over time

## Advanced Features

### 1. Batch Processing

Genie can now recognize and optimize batch operations:

```python
# Example: Genie will recognize this as a batch operation
await ask_genie("""
Send the following messages:
- "Hello" to channel general
- "Meeting at 3pm" to channel meetings  
- "Code review ready" to channel dev
""")
```

### 2. Complex Workflows

Genie can handle multi-step workflows with checkpoints:

```python
# Example: Complex workflow with progress tracking
await ask_genie("""
1. First, list all Python files in the project
2. Then find all files with TODO comments
3. Create a summary report of all TODOs grouped by file
4. Save the report as todos.md
""")
```

### 3. Learning from Failures

Genie now creates detailed error memories:

```python
# After a failure, Genie remembers:
# - Exact error message
# - What parameters caused it
# - What solution worked
# - How to avoid it next time
```

## Troubleshooting

### If memories aren't being created:
1. Check that `enable_agentic_memory=True`
2. Verify SQLite database is writable
3. Look for memory creation logs in debug output

### If tool calls are failing:
1. Enable `debug_mode=True` to see full CoT reasoning
2. Check MCP server logs for connection issues
3. Verify tool schemas are being loaded correctly

### If responses are too verbose:
1. Adjust the instruction emphasis on conciseness
2. Modify the output format templates
3. Set stricter token limits in the model configuration

## Migration Path

For existing Genie installations:

1. **Phase 1**: Add optimizations with feature flag (GPT41_OPTIMIZED)
2. **Phase 2**: Test with subset of users
3. **Phase 3**: Monitor metrics and iterate
4. **Phase 4**: Make GPT-4.1 optimizations default
5. **Phase 5**: Remove legacy code

## Conclusion

These GPT-4.1 optimizations transform Genie from a simple MCP orchestrator into an intelligent, self-improving API translator that:

- Learns from every interaction
- Handles errors gracefully
- Provides natural language interfaces to any API
- Gets better over time without manual updates

The key is letting GPT-4.1's strengths shine through:
- Persistence in problem-solving
- Literal instruction following  
- Extensive planning before action
- Learning from successes and failures