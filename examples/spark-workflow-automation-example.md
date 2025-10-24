# Spark Workflow Automation Example

This example demonstrates how to use the Spark MCP tool to orchestrate AI workflows, schedule automated tasks, and manage multi-agent systems through the AutoMagik Spark API.

## Use Case Description

Use Spark to:
- Execute AI workflows (agents, teams, structured processes) on demand
- Schedule recurring tasks with cron or interval-based automation
- Monitor task execution status and results in real-time
- Connect to multiple AutoMagik Agents and Hive instances
- Discover and sync workflows from remote sources
- Build automated AI-powered business processes

Perfect for automating repetitive AI tasks, scheduling reports, orchestrating multi-step workflows, and building production AI systems.

## Setup

### Prerequisites

1. **Spark Instance**: Running Spark server
2. **API Credentials**: Spark API key
3. **Workflow Sources**: AutoMagik Agents or Hive instances (optional)
4. **Python 3.12+**: For running automagik-tools

### Environment Configuration

Create a `.env` file or set environment variables:

```bash
# Required
SPARK_API_KEY=namastex888

# Optional
SPARK_BASE_URL=http://localhost:8883  # Spark API URL
SPARK_TIMEOUT=30                       # Request timeout in seconds
```

## CLI Commands

### Direct Command Line Usage

```bash
# Run with stdio transport (for Claude/Cursor)
uvx automagik-tools tool spark --transport stdio

# Run with SSE transport
uvx automagik-tools tool spark --transport sse --port 8000

# Run with HTTP transport
uvx automagik-tools tool spark --transport http --port 8001
```

### Check Spark Status

```bash
# Check API health
curl http://localhost:8883/health \
  -H "X-API-Key: namastex888"

# List workflows
curl http://localhost:8883/api/workflows \
  -H "X-API-Key: namastex888"
```

## MCP Configuration

### For Claude Desktop

Add this to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "spark": {
      "command": "uvx",
      "args": [
        "automagik-tools",
        "tool",
        "spark",
        "--transport",
        "stdio"
      ],
      "env": {
        "SPARK_API_KEY": "namastex888",
        "SPARK_BASE_URL": "http://localhost:8883",
        "SPARK_TIMEOUT": "30"
      }
    }
  }
}
```

### For Cursor

Add this to your Cursor MCP configuration (`~/.cursor/mcp.json`):

```json
{
  "mcpServers": {
    "spark": {
      "command": "uvx",
      "args": [
        "automagik-tools",
        "tool",
        "spark",
        "--transport",
        "stdio"
      ],
      "env": {
        "SPARK_API_KEY": "namastex888",
        "SPARK_BASE_URL": "http://localhost:8883"
      }
    }
  }
}
```

## Expected Output

### 1. Check Health Status

**Command:**
```python
get_health()
```

**Expected Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "api_status": "operational",
  "database_status": "connected",
  "scheduler_status": "running",
  "active_schedules": 5,
  "total_workflows": 12,
  "uptime": "3 days, 12 hours"
}
```

### 2. List Available Workflows

**Command:**
```python
list_workflows(limit=10)
```

**Expected Response:**
```json
{
  "workflows": [
    {
      "id": "f9c38d51-56a4-42e8-8b0f-10b180345468",
      "name": "Python Expert Agent",
      "type": "hive_agent",
      "description": "Expert Python developer agent",
      "source": "local-agents",
      "created_at": "2024-01-10T10:00:00Z",
      "last_run": "2024-01-15T14:30:00Z",
      "total_runs": 45
    },
    {
      "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "name": "Data Analysis Workflow",
      "type": "hive_workflow",
      "description": "Multi-step data analysis pipeline",
      "source": "hive-instance",
      "created_at": "2024-01-12T09:00:00Z",
      "last_run": "2024-01-15T08:00:00Z",
      "total_runs": 120
    }
  ],
  "total_count": 2,
  "page": 1,
  "limit": 10
}
```

### 3. Run a Workflow

**Command:**
```python
run_workflow(
    workflow_id="f9c38d51-56a4-42e8-8b0f-10b180345468",
    input_text="What are the best practices for error handling in Python async functions?"
)
```

**Expected Response:**
```json
{
  "status": "success",
  "task_id": "task_abc123def456",
  "workflow_id": "f9c38d51-56a4-42e8-8b0f-10b180345468",
  "workflow_name": "Python Expert Agent",
  "result": {
    "response": "Here are the best practices for error handling in Python async functions:\n\n1. **Use try-except blocks**:\n```python\nasync def fetch_data():\n    try:\n        result = await api_call()\n        return result\n    except aiohttp.ClientError as e:\n        logger.error(f'API call failed: {e}')\n        raise\n```\n\n2. **Handle specific exceptions first**:\n- Catch specific exceptions before generic ones\n- Use asyncio.TimeoutError for timeouts\n- Handle asyncio.CancelledError for task cancellation\n\n3. **Use asyncio.gather with return_exceptions**:\n```python\nresults = await asyncio.gather(\n    task1(), task2(), task3(),\n    return_exceptions=True\n)\n```\n\n4. **Implement retry logic with exponential backoff**\n5. **Use context managers for resource cleanup**\n6. **Log errors appropriately**\n7. **Propagate errors when necessary**",
        "tokens_used": 245,
        "execution_time": "3.2s"
    },
    "started_at": "2024-01-15T15:00:00Z",
    "completed_at": "2024-01-15T15:00:03Z",
    "execution_time": "3.2 seconds"
}
```

### 4. Create a Schedule

**Command:**
```python
create_schedule(
    workflow_id="a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    schedule_type="cron",
    schedule_expr="0 9 * * *",  # Daily at 9 AM
    input_value="Generate daily sales report for yesterday"
)
```

**Expected Response:**
```json
{
  "status": "success",
  "schedule_id": "sched_xyz789abc123",
  "workflow_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "workflow_name": "Data Analysis Workflow",
  "schedule_type": "cron",
  "schedule_expression": "0 9 * * *",
  "next_run": "2024-01-16T09:00:00Z",
  "is_enabled": true,
  "created_at": "2024-01-15T15:05:00Z",
  "message": "Schedule created successfully. Next run: Tomorrow at 9:00 AM"
}
```

### 5. List Active Schedules

**Command:**
```python
list_schedules()
```

**Expected Response:**
```json
{
  "schedules": [
    {
      "id": "sched_xyz789abc123",
      "workflow_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "workflow_name": "Data Analysis Workflow",
      "schedule_type": "cron",
      "schedule_expression": "0 9 * * *",
      "description": "Daily sales report at 9 AM",
      "is_enabled": true,
      "next_run": "2024-01-16T09:00:00Z",
      "last_run": "2024-01-15T09:00:00Z",
      "total_runs": 30,
      "success_rate": "96.7%"
    },
    {
      "id": "sched_interval_456",
      "workflow_id": "f9c38d51-56a4-42e8-8b0f-10b180345468",
      "workflow_name": "System Health Check",
      "schedule_type": "interval",
      "schedule_expression": "30m",
      "description": "Check system health every 30 minutes",
      "is_enabled": true,
      "next_run": "2024-01-15T15:30:00Z",
      "last_run": "2024-01-15T15:00:00Z",
      "total_runs": 1440,
      "success_rate": "99.9%"
    }
  ],
  "total_count": 2
}
```

### 6. Add Workflow Source

**Command:**
```python
add_source(
    name="Production Agents",
    source_type="automagik-agents",
    url="http://production.example.com:8881",
    api_key="prod_api_key_here"
)
```

**Expected Response:**
```json
{
  "status": "success",
  "source_id": "src_prod_agents_123",
  "name": "Production Agents",
  "source_type": "automagik-agents",
  "url": "http://production.example.com:8881",
  "is_connected": true,
  "workflows_discovered": 8,
  "created_at": "2024-01-15T15:10:00Z",
  "message": "Source added successfully. Discovered 8 workflows."
}
```

## Real-World Usage Scenarios

### Scenario 1: Daily Report Automation

```python
# Add data analysis workflow
workflows = list_workflows()
data_workflow = next(w for w in workflows['workflows'] if 'analysis' in w['name'].lower())

# Schedule daily report generation
schedule = create_schedule(
    workflow_id=data_workflow['id'],
    schedule_type="cron",
    schedule_expr="0 8 * * 1-5",  # Weekdays at 8 AM
    input_value="Generate comprehensive daily report with sales, inventory, and customer metrics"
)

print(f"Daily report scheduled: {schedule['schedule_id']}")
print(f"Next run: {schedule['next_run']}")

# Monitor execution
tasks = list_tasks(workflow_id=data_workflow['id'], status="completed", limit=5)
print(f"Recent executions: {len(tasks['tasks'])}")
for task in tasks['tasks']:
    print(f"- {task['started_at']}: {task['status']} ({task['execution_time']})")
```

### Scenario 2: Multi-Source Workflow Orchestration

```python
# Connect to multiple sources
sources = [
    {
        "name": "Development Agents",
        "type": "automagik-agents",
        "url": "http://dev.example.com:8881",
        "api_key": "dev_key"
    },
    {
        "name": "Production Hive",
        "type": "automagik-hive",
        "url": "http://prod.example.com:8886",
        "api_key": "prod_key"
    }
]

for source in sources:
    result = add_source(
        name=source["name"],
        source_type=source["type"],
        url=source["url"],
        api_key=source["api_key"]
    )
    print(f"Added {source['name']}: {result['workflows_discovered']} workflows")

# List all available workflows from all sources
all_workflows = list_workflows(limit=100)
print(f"\nTotal workflows available: {all_workflows['total_count']}")

# Group by source
by_source = {}
for workflow in all_workflows['workflows']:
    source = workflow['source']
    by_source[source] = by_source.get(source, 0) + 1

for source, count in by_source.items():
    print(f"- {source}: {count} workflows")
```

### Scenario 3: Interval-Based Monitoring

```python
# Create health check workflow
health_check = run_workflow(
    workflow_id="system-health-agent",
    input_text="Check all system components and report status"
)

# Schedule regular monitoring
monitoring_schedule = create_schedule(
    workflow_id="system-health-agent",
    schedule_type="interval",
    schedule_expr="15m",  # Every 15 minutes
    input_value="Perform system health check and alert if issues found"
)

print(f"Monitoring active: Every 15 minutes")
print(f"Schedule ID: {monitoring_schedule['schedule_id']}")

# Check recent health checks
recent_checks = list_tasks(
    workflow_id="system-health-agent",
    limit=10
)

print(f"\nRecent health checks:")
for check in recent_checks['tasks']:
    status_emoji = "✅" if check['status'] == 'completed' else "❌"
    print(f"{status_emoji} {check['started_at']}: {check['status']}")
```

### Scenario 4: On-Demand Workflow Execution

```python
# Execute different workflows based on user requests
user_requests = [
    {
        "workflow": "code-reviewer-agent",
        "input": "Review the authentication module for security issues"
    },
    {
        "workflow": "data-analyst-agent",
        "input": "Analyze user engagement metrics from last week"
    },
    {
        "workflow": "content-writer-agent",
        "input": "Write a blog post about AI automation trends"
    }
]

results = []
for request in user_requests:
    # Find workflow by name
    workflows = list_workflows()
    workflow = next(
        (w for w in workflows['workflows'] if request['workflow'] in w['name'].lower()),
        None
    )
    
    if workflow:
        result = run_workflow(
            workflow_id=workflow['id'],
            input_text=request['input']
        )
        results.append({
            "workflow": workflow['name'],
            "task_id": result['task_id'],
            "status": result['status']
        })
        print(f"✓ Started: {workflow['name']}")
    else:
        print(f"✗ Workflow not found: {request['workflow']}")

# Monitor all tasks
print(f"\nMonitoring {len(results)} tasks...")
for result in results:
    task = get_task(result['task_id'])
    print(f"- {result['workflow']}: {task['status']}")
```

### Scenario 5: Schedule Management

```python
# List all schedules
schedules = list_schedules()

print(f"Active Schedules: {schedules['total_count']}\n")

for schedule in schedules['schedules']:
    print(f"📅 {schedule['workflow_name']}")
    print(f"   Schedule: {schedule['schedule_expression']} ({schedule['schedule_type']})")
    print(f"   Next run: {schedule['next_run']}")
    print(f"   Success rate: {schedule['success_rate']}")
    print(f"   Enabled: {schedule['is_enabled']}")
    
    # Disable schedules with low success rate
    if float(schedule['success_rate'].rstrip('%')) < 90:
        disable_schedule(schedule['id'])
        print(f"   ⚠️ Disabled due to low success rate")
    
    print()

# Create new schedule for weekend batch processing
weekend_schedule = create_schedule(
    workflow_id="batch-processing-workflow",
    schedule_type="cron",
    schedule_expr="0 2 * * 0",  # Sundays at 2 AM
    input_value="Run weekly batch processing and cleanup"
)

print(f"Weekend batch processing scheduled: {weekend_schedule['next_run']}")
```

## Features Demonstrated

1. **Workflow Execution**: Run AI workflows on demand
2. **Cron Scheduling**: Schedule tasks with cron expressions
3. **Interval Scheduling**: Run tasks at regular intervals
4. **Source Management**: Connect multiple workflow sources
5. **Task Monitoring**: Track execution status and results
6. **Schedule Control**: Enable, disable, and manage schedules
7. **Health Monitoring**: Check API and service status

## Schedule Expression Examples

### Cron Format

```python
# Every day at 9 AM
"0 9 * * *"

# Every Monday at 8:30 AM
"30 8 * * 1"

# Every 15 minutes
"*/15 * * * *"

# First day of every month at midnight
"0 0 1 * *"

# Weekdays at 6 PM
"0 18 * * 1-5"

# Every hour during business hours (9 AM - 5 PM) on weekdays
"0 9-17 * * 1-5"
```

### Interval Format

```python
# Every 5 minutes
"5m"

# Every 30 seconds
"30s"

# Every 2 hours
"2h"

# Every day
"1d"

# Every week
"7d"
```

## Best Practices

1. **Test First**: Run workflows manually before scheduling
2. **Monitor Performance**: Check task execution times and success rates
3. **Use Descriptive Names**: Name schedules clearly for easy management
4. **Set Appropriate Intervals**: Don't over-schedule - respect rate limits
5. **Handle Failures**: Implement retry logic and error notifications
6. **Clean Up**: Delete old tasks and unused schedules
7. **Source Organization**: Group workflows by environment (dev, staging, prod)

## Advanced Usage

### Sync Remote Workflows

```python
# Discover workflows from remote source
remote_workflows = list_remote_workflows(
    source_url="http://remote.example.com:8881"
)

print(f"Found {len(remote_workflows['workflows'])} remote workflows")

# Sync specific workflow
for workflow in remote_workflows['workflows']:
    if 'production' in workflow['name'].lower():
        sync_result = sync_workflow(
            workflow_id=workflow['id'],
            input_component="text",
            output_component="markdown"
        )
        print(f"Synced: {workflow['name']}")
```

### Conditional Scheduling

```python
# Get workflow details
workflow = get_workflow("data-analysis-workflow")

# Only schedule if workflow is healthy
if workflow['last_run_status'] == 'success':
    schedule = create_schedule(
        workflow_id=workflow['id'],
        schedule_type="cron",
        schedule_expr="0 */6 * * *",  # Every 6 hours
        input_value="Run analysis"
    )
    print(f"Scheduled: {schedule['schedule_id']}")
else:
    print(f"Workflow unhealthy, skipping schedule")
```

## Troubleshooting

### Common Issues

1. **"Unauthorized" (401)**
   - Check `SPARK_API_KEY` is correct
   - Verify API key has necessary permissions

2. **"Workflow not found" (404)**
   - List workflows to verify ID
   - Check workflow hasn't been deleted
   - Ensure source is connected

3. **"Validation Error" (422)**
   - Check schedule expression format
   - Verify workflow_id is valid UUID
   - Ensure input_value is provided

4. **Schedule not running**
   - Check schedule is enabled
   - Verify cron expression is correct
   - Check Spark scheduler is running

5. **Task execution failed**
   - Review task details with `get_task()`
   - Check workflow source is accessible
   - Verify input format matches workflow requirements

## Performance Tips

1. **Batch Operations**: Group related workflow executions
2. **Appropriate Intervals**: Don't schedule too frequently
3. **Monitor Resources**: Check task execution times
4. **Clean Up History**: Delete old task records periodically
5. **Use Filters**: Filter tasks by status and date for efficiency

## Security Considerations

- **API Key Protection**: Store securely, never in code
- **Source Authentication**: Use separate API keys per environment
- **Access Control**: Implement proper authentication
- **Input Validation**: Sanitize workflow inputs
- **Audit Logs**: Monitor workflow executions
- **Rate Limiting**: Respect API rate limits

## Next Steps

1. **Build Workflows**: Create custom workflows for your use case
2. **Set Up Monitoring**: Implement alerting for failed tasks
3. **Optimize Schedules**: Fine-tune timing based on usage patterns
4. **Scale Sources**: Connect additional workflow sources
5. **Integrate**: Connect Spark with your applications

## Additional Resources

- [Spark API Documentation](https://docs.automagik.ai/spark)
- [Cron Expression Guide](https://crontab.guru/)
- [AutoMagik Agents](https://github.com/namastexlabs/automagik-agents)
- [Automagik Tools GitHub](https://github.com/namastexlabs/automagik-tools)
