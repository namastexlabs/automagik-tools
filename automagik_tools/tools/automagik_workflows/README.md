# AutoMagik Workflows - Smart Claude Workflow Orchestration

## Overview

AutoMagik Workflows provides intelligent MCP integration for Claude Code workflow API with real-time progress tracking. This tool enables seamless execution, monitoring, and management of Claude Code workflows through a humanized interface.

## Configuration

The tool uses environment variables with the `AUTOMAGIK_WORKFLOWS_` prefix:

```bash
# Required
AUTOMAGIK_WORKFLOWS_API_KEY=your-api-key

# Optional (with defaults)
AUTOMAGIK_WORKFLOWS_BASE_URL=http://localhost:28881  # Claude Code API endpoint
AUTOMAGIK_WORKFLOWS_TIMEOUT=7200                     # 2 hours timeout
AUTOMAGIK_WORKFLOWS_POLLING_INTERVAL=8               # 8 seconds between status checks
AUTOMAGIK_WORKFLOWS_MAX_RETRIES=3                    # HTTP retry attempts
```

## Usage

### CLI Integration

```bash
# Serve the tool via automagik-tools
uvx automagik-tools serve automagik_workflows --transport stdio

# List all available tools (includes automagik_workflows)
uvx automagik-tools list
```

### Direct Usage

```bash
# Run the tool directly
cd automagik_tools/tools/automagik_workflows
python -m automagik_tools.tools.automagik_workflows
```

## Available Tools

### 🚀 run_workflow
Execute a Claude Code workflow with intelligent progress tracking.

**Parameters:**
- `workflow_name`: Workflow type (test, pr, fix, refactor, implement, review, document, architect)
- `message`: Task description for the workflow
- `max_turns`: Maximum conversation turns (1-100, default: 30)
- `session_name`: Optional session identifier
- `git_branch`: Git branch for the workflow
- `repository_url`: Repository URL if applicable
- `timeout`: Workflow timeout in seconds (default: 2 hours)

**Returns:** Complete workflow results with metrics and execution details

### 📋 list_workflows
Discover all available Claude workflows with descriptions.

**Returns:** List of available workflows with their capabilities

### 📊 list_recent_runs
View workflow execution history with optional filtering.

**Parameters:**
- `workflow_name`: Filter by specific workflow type
- `status`: Filter by status (pending, running, completed, failed)
- `limit`: Maximum number of runs to return (default: 10)
- `sort_by`: Sort field (started_at, workflow_name, status)
- `sort_order`: Sort order (asc, desc)

**Returns:** Paginated list of recent workflow runs

### 📈 get_workflow_status
Get detailed status of a specific workflow run.

**Parameters:**
- `run_id`: Unique identifier for the workflow run

**Returns:** Real-time status, progress, metrics, and results

## Examples

### Basic Workflow Execution

```python
# Execute a test workflow
result = await run_workflow(
    workflow_name="test",
    message="Run comprehensive tests on the codebase",
    max_turns=20
)

print(f"Status: {result['status']}")
print(f"Turns used: {result['turns_used']}/{result['max_turns']}")
```

### List Available Workflows

```python
# Discover what workflows are available
workflows = await list_workflows()
for workflow in workflows:
    print(f"- {workflow['name']}: {workflow['description']}")
```

### Monitor Workflow Progress

```python
# Start a workflow and monitor progress
result = await run_workflow(
    workflow_name="implement",
    message="Add user authentication feature",
    max_turns=50
)

if result['status'] == 'completed':
    print(f"✅ Completed in {result['execution_time']:.1f}s")
    print(f"📊 Used {result['turns_used']} turns")
else:
    print(f"❌ Failed: {result.get('error', 'Unknown error')}")
```

### Check Recent Activity

```python
# View recent workflow runs
recent_runs = await list_recent_runs(
    status="completed",
    limit=5
)

for run in recent_runs:
    print(f"Run {run['run_id']}: {run['workflow_name']} - {run['status']}")
```

## Features

### Real-Time Progress Tracking
- Uses `Context.report_progress()` with turns/max_turns ratio
- 8-second polling intervals for optimal responsiveness
- Visual progress indicators with emoji feedback

### Intelligent Error Handling
- Comprehensive retry logic with exponential backoff
- Graceful timeout management
- Detailed error reporting with context

### MCP Protocol Compliance
- Full FastMCP integration
- Proper Context logging (info, error, warn)
- Standard MCP tool registration and discovery

### Performance Optimized
- Async/await throughout for non-blocking operations
- Connection pooling with httpx.AsyncClient
- Configurable timeouts and retry strategies

## Integration

This tool follows the automagik-tools standard pattern:

- **Self-contained**: All functionality in `automagik_tools/tools/automagik_workflows/`
- **Auto-discovery**: Registered in `pyproject.toml` entry points
- **Hub-compatible**: Mounts seamlessly in automagik hub
- **CLI-ready**: Works with `uvx automagik-tools` commands

## Development

### Running Tests

```bash
# Run all tests
pytest tests/tools/test_automagik_workflows.py -v

# Run with coverage
pytest tests/tools/test_automagik_workflows.py --cov=automagik_tools.tools.automagik_workflows
```

### Code Quality

```bash
# Format code
black automagik_tools/tools/automagik_workflows/

# Lint code
ruff check automagik_tools/tools/automagik_workflows/
```

## License

Part of the automagik-tools project by Namastex Labs.