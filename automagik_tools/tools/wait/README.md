# Wait Utility MCP Tool

## Overview
Smart timing functions for agent workflows including delays, progress reporting, and timestamp waiting. Perfect for workflow polling, rate limiting, and scheduled operations in automated systems.

## Configuration
Set the following environment variables:

```bash
# Maximum wait duration (default: 3600 seconds = 1 hour)
WAIT_MAX_DURATION=3600

# Default progress reporting interval (default: 1.0 seconds)
WAIT_DEFAULT_PROGRESS_INTERVAL=1.0
```

## Usage

### Standalone
```bash
# Run with stdio transport (for Claude Desktop)
uvx automagik-tools tool wait

# Run with SSE transport
uvx automagik-tools tool wait --transport sse --port 8000
```

### Claude Desktop Configuration
```json
{
  "mcpServers": {
    "wait": {
      "command": "uvx",
      "args": ["automagik-tools", "serve", "wait"],
      "env": {
        "WAIT_MAX_DURATION": "7200"
      }
    }
  }
}
```

## Available Tools

### `wait_seconds(duration: float)`
Wait for a specified number of seconds with precise timing.

**Parameters:**
- `duration`: Number of seconds to wait (must be positive and within max_duration limit)

**Example:**
```python
# Wait for 5 seconds
result = await wait_seconds(5.0)
```

### `wait_minutes(duration: float)`
Wait for a specified number of minutes (converted to seconds internally).

**Parameters:**
- `duration`: Number of minutes to wait (must be positive)

**Example:**
```python
# Wait for 2.5 minutes
result = await wait_minutes(2.5)
```

### `wait_until_timestamp(timestamp: str)`
Wait until a specific ISO 8601 timestamp is reached.

**Parameters:**
- `timestamp`: Target timestamp in ISO 8601 format (e.g., "2024-01-01T12:00:00Z")

**Example:**
```python
# Wait until midnight UTC on New Year's Day
result = await wait_until_timestamp("2024-01-01T00:00:00Z")
```

### `wait_with_progress(duration: float, interval: float = 1.0)`
Wait with regular progress updates for long operations.

**Parameters:**
- `duration`: Total duration to wait in seconds
- `interval`: Progress reporting interval in seconds (default: 1.0)

**Example:**
```python
# Wait for 30 seconds with progress updates every 2 seconds
result = await wait_with_progress(30.0, 2.0)
```

## Use Cases

### Workflow Polling
```python
# Poll a workflow status every 10 seconds
while True:
    status = await check_workflow_status(run_id)
    if status == "completed":
        break
    await wait_seconds(10.0)  # Intelligent delay between polls
```

### Rate Limiting
```python
# Respect API rate limits
for item in items:
    await process_item(item)
    await wait_seconds(1.0)  # 1 second delay between API calls
```

### Scheduled Operations
```python
# Wait until a specific time to perform an action
await wait_until_timestamp("2024-01-01T09:00:00Z")
await perform_scheduled_task()
```

### Long Operations with Progress
```python
# Long wait with user-visible progress
await wait_with_progress(300.0, 5.0)  # 5 minute wait with updates every 5 seconds
```

## Features

- ✅ **Precise Timing**: Accurate delays using asyncio
- ✅ **Progress Reporting**: Real-time progress updates for long waits
- ✅ **Cancellation Support**: Proper handling of cancelled operations
- ✅ **Input Validation**: Duration limits and timestamp parsing
- ✅ **Multiple Formats**: Seconds, minutes, and timestamp-based waiting
- ✅ **Context Integration**: Rich logging and progress reporting
- ✅ **Error Handling**: Comprehensive error responses

## Safety Features

- **Maximum Duration Limits**: Prevents excessive waits (configurable, default 1 hour)
- **Input Validation**: Ensures positive durations and valid timestamps
- **Cancellation Handling**: Graceful handling of interrupted waits
- **Progress Tracking**: Visibility into long-running operations