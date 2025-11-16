# Spark MCP Tool

## Overview

The Spark MCP tool provides comprehensive workflow orchestration and AI agent management capabilities through the AutoMagik Spark API. It enables you to execute, schedule, and manage AI workflows including single agents, multi-agent teams, and structured processes.

## Features

- **Workflow Management**: Execute and manage AI workflows (agents, teams, structured processes)
- **Task Monitoring**: Track task execution status and results
- **Schedule Automation**: Create cron and interval-based schedules for automated runs
- **Source Integration**: Connect to multiple AutoMagik Agents and Hive instances
- **Remote Discovery**: Browse and sync workflows from remote sources

## Configuration

Set the following environment variables:

```bash
export SPARK_API_KEY="namastex888"  # Your Spark API key
export SPARK_BASE_URL="http://localhost:8883"  # Spark API URL (optional)
export SPARK_TIMEOUT="30"  # Request timeout in seconds (optional)
```

Or create a `.env` file:

```env
SPARK_API_KEY=namastex888
SPARK_BASE_URL=http://localhost:8883
SPARK_TIMEOUT=30
```

## Installation

### As a standalone tool

```bash
# Run with uvx
uvx automagik-tools tool spark

# Or run directly
python -m automagik_tools.tools.spark
```

### In Claude Desktop or Cursor

Add to your MCP configuration:

```json
{
  "mcpServers": {
    "spark": {
      "command": "uvx",
      "args": ["automagik-tools", "tool", "spark"],
      "env": {
        "SPARK_API_KEY": "namastex888",
        "SPARK_BASE_URL": "http://localhost:8883"
      }
    }
  }
}
```

## Available Tools

### Health & Status
- `get_health()` - Get API and service health status

### Workflow Management
- `list_workflows(source?, limit?)` - List all synchronized workflows
- `get_workflow(workflow_id)` - Get specific workflow details
- `run_workflow(workflow_id, input_text)` - Execute a workflow
- `delete_workflow(workflow_id)` - Delete a workflow

### Remote Discovery
- `list_remote_workflows(source_url)` - List workflows from remote source
- `sync_workflow(workflow_id, input_component?, output_component?)` - Sync remote workflow

### Task Management
- `list_tasks(workflow_id?, status?, limit?)` - List task executions
- `get_task(task_id)` - Get task details

### Schedule Management
- `list_schedules(workflow_id?)` - List active schedules
- `create_schedule(workflow_id, schedule_type, schedule_expr, input_value?)` - Create schedule
- `delete_schedule(schedule_id)` - Delete schedule
- `enable_schedule(schedule_id)` - Enable schedule
- `disable_schedule(schedule_id)` - Disable schedule

### Source Management
- `list_sources()` - List configured sources
- `add_source(name, source_type, url, api_key?)` - Add workflow source
- `delete_source(source_id)` - Delete source

## Usage Examples

### Execute a Workflow

```python
# List available workflows
workflows = await list_workflows()

# Run a specific workflow
result = await run_workflow(
    workflow_id="f9c38d51-56a4-42e8-8b0f-10b180345468",
    input_text="What is the best practice for error handling in Python?"
)
```

### Schedule Automated Runs

```python
# Create a daily schedule
schedule = await create_schedule(
    workflow_id="f9c38d51-56a4-42e8-8b0f-10b180345468",
    schedule_type="cron",
    schedule_expr="0 9 * * *",  # Daily at 9 AM
    input_value="Generate a daily development tip"
)

# Create an interval schedule
schedule = await create_schedule(
    workflow_id="a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    schedule_type="interval",
    schedule_expr="30m",  # Every 30 minutes
    input_value="Check system health"
)
```

### Add Workflow Sources

```python
# Add AutoMagik Agents source
source = await add_source(
    name="Local Agents",
    source_type="automagik-agents",
    url="http://localhost:8881",
    api_key="namastex888"
)

# Add AutoMagik Hive source
source = await add_source(
    name="Hive Instance",
    source_type="automagik-hive",
    url="http://localhost:8886",
    api_key="hive_namastex888"
)
```

### Monitor Tasks

```python
# List recent tasks
tasks = await list_tasks(status="completed", limit=10)

# Get specific task details
task = await get_task(task_id="07412ae1-6ff2-46e5-ab47-9dd38a1c5da9")
```

## Workflow Types

The tool supports three types of workflows:

### 1. Agents (`hive_agent`)
Single AI agent execution with:
- Direct conversational input
- Memory and storage capabilities
- Tool integrations
- Session continuity

### 2. Teams (`hive_team`)
Multi-agent coordination with:
- Coordinator agent managing team members
- Domain-specific specialists
- Complex task decomposition
- Collaborative problem solving

### 3. Structured Workflows (`hive_workflow`)
Multi-step orchestrated processes with:
- Step-by-step execution
- Process automation
- Workflow-specific input/output
- Progress tracking

## Schedule Expressions

### Interval Format
- `5m` - Every 5 minutes
- `1h` - Every hour
- `30s` - Every 30 seconds
- `2d` - Every 2 days

### Cron Format
- `0 9 * * *` - Daily at 9 AM
- `*/15 * * * *` - Every 15 minutes
- `0 0 * * 0` - Weekly on Sunday at midnight
- `0 8-17 * * 1-5` - Hourly on weekdays 8 AM to 5 PM

## Error Handling

The tool provides detailed error messages for common issues:
- `401 Unauthorized` - Invalid or missing API key
- `404 Not Found` - Resource not found
- `422 Validation Error` - Invalid request parameters
- `500 Internal Server Error` - Server-side error

All errors include detailed messages to help diagnose issues.

## Support

For issues or questions about the Spark MCP tool, please refer to the [AutoMagik Tools documentation](https://github.com/namastexlabs/automagik-tools) or contact support.