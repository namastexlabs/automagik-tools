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

**What to say to Claude:**
```
Check the health status of the Spark service
```

**Expected Response from Claude:**
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

**What to say to Claude:**
```
List available workflows, limit to 10
```

**Expected Response from Claude:**
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

**What to say to Claude:**
```
Run the Python Expert Agent workflow with this question: "What are the best practices for error handling in Python async functions?"
```

**Expected Response from Claude:**
```json
{
  "status": "success",
  "task_id": "task_abc123def456",
  "workflow_id": "f9c38d51-56a4-42e8-8b0f-10b180345468",
  "workflow_name": "Python Expert Agent",
  "result": {
    "response": "Here are the best practices for error handling in Python async functions:\n\n1. **Use try-except blocks**:\n```python\nasync def fetch_data():\n    try:\n        result = await api_call()\n        return result\n    except aiohttp.ClientError as e:\n        logger.error(f'API call failed: {e}')\n        raise\n```\n\n2. **Handle specific exceptions first**:\n- Catch specific exceptions before generic ones\n- Use asyncio.TimeoutError for timeouts\n- Handle asyncio.CancelledError for task cancellation\n\n3. **Use asyncio.gather with return_exceptions**:\n```python\nresults = await asyncio.gather(\n    task1(), task2(), task3(),\n    return_exceptions=True\n)\n```",
        "tokens_used": 245,
        "execution_time": "3.2s"
    },
    "started_at": "2024-01-15T15:00:00Z",
    "completed_at": "2024-01-15T15:00:03Z",
    "execution_time": "3.2 seconds"
}
```

### 4. Create a Schedule

**What to say to Claude:**
```
Create a schedule for the Data Analysis Workflow to run daily at 9 AM with the input: "Generate daily sales report for yesterday"
```

**Expected Response from Claude:**
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

**What to say to Claude:**
```
List all active schedules
```

**Expected Response from Claude:**
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

**What to say to Claude:**
```
Add a new workflow source named "Production Agents" with URL http://production.example.com:8881 and API key prod_api_key_here
```

**Expected Response from Claude:**
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

**What to say to Claude:**
```
First, find the data analysis workflow and then schedule it to generate a comprehensive daily report with sales, inventory, and customer metrics every weekday at 8 AM
```

**What Claude does:**
- Finds the data analysis workflow
- Schedules it to run weekdays at 8 AM
- Monitors recent executions

**Expected Response:**
```json
{
  "status": "success",
  "message": "Daily report scheduled successfully. Next run: Monday at 8:00 AM",
  "schedule_id": "sched_xyz789abc123",
  "workflow_name": "Data Analysis Workflow"
}
```

### Scenario 2: Multi-Source Workflow Orchestration

**What to say to Claude:**
```
Connect to multiple workflow sources:
1. Development Agents at http://dev.example.com:8881 with API key dev_key
2. Production Hive at http://prod.example.com:8886 with API key prod_key

Then list all available workflows from all sources and group them by source
```

**What Claude does:**
- Connects to multiple workflow sources
- Lists all available workflows
- Groups workflows by source

**Expected Response:**
```json
{
  "status": "success",
  "message": "Connected to 2 sources. Discovered 15 total workflows.",
  "sources": [
    {
      "name": "Development Agents",
      "workflows": 7
    },
    {
      "name": "Production Hive",
      "workflows": 8
    }
  ]
}
```

### Scenario 3: Interval-Based Monitoring

**What to say to Claude:**
```
First, run a system health check workflow to check all system components and report status

Then, schedule regular monitoring to perform system health checks every 15 minutes and alert if issues are found

Finally, show recent health checks
```

**What Claude does:**
- Runs an initial system health check
- Schedules regular monitoring every 15 minutes
- Shows recent health check results

**Expected Response:**
```json
{
  "status": "success",
  "message": "Monitoring scheduled every 15 minutes. Recent checks: 8 completed, 0 failed.",
  "schedule_id": "sched_health_123",
  "recent_checks": [
    {
      "timestamp": "2024-01-15T15:00:00Z",
      "status": "completed",
      "duration": "2.1s"
    },
    {
      "timestamp": "2024-01-15T14:45:00Z",
      "status": "completed",
      "duration": "1.9s"
    }
  ]
}
```

### Scenario 4: On-Demand Workflow Execution

**What to say to Claude:**
```
Execute these workflows:
1. Run the code reviewer agent to review the authentication module for security issues
2. Run the data analyst agent to analyze user engagement metrics from last week
3. Run the content writer agent to write a blog post about AI automation trends

Then monitor all tasks
```

**What Claude does:**
- Executes multiple workflows based on user requests
- Monitors all task statuses

**Expected Response:**
```json
{
  "status": "success",
  "message": "Started 3 workflows. Monitoring in progress.",
  "tasks": [
    {
      "workflow": "Code Reviewer Agent",
      "task_id": "task_abc123",
      "status": "running"
    },
    {
      "workflow": "Data Analyst Agent",
      "task_id": "task_def456",
      "status": "completed"
    },
    {
      "workflow": "Content Writer Agent",
      "task_id": "task_ghi789",
      "status": "running"
    }
  ]
}
```

### Scenario 5: Schedule Management

**What to say to Claude:**
```
First, list all active schedules and show their details including success rates

Then, disable any schedules with success rates below 90%

Finally, create a new schedule for weekend batch processing to run weekly cleanup on Sundays at 2 AM
```

**What Claude does:**
- Lists all active schedules with details
- Disables schedules with low success rates
- Creates a new weekend batch processing schedule

**Expected Response:**
```json
{
  "status": "success",
  "message": "Schedule management completed. 1 schedule disabled, 1 new schedule created.",
  "disabled_schedules": [
    "sched_old_123"
  ],
  "new_schedules": [
    {
      "name": "Weekend Batch Processing",
      "next_run": "2024-01-21T02:00:00Z",
      "schedule_id": "sched_weekend_456"
    }
  ]
}
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

These are examples of cron expressions you can use when scheduling workflows:

- `0 9 * * *` - Every day at 9 AM
- `30 8 * * 1` - Every Monday at 8:30 AM
- `*/15 * * * *` - Every 15 minutes
- `0 0 1 * *` - First day of every month at midnight
- `0 18 * * 1-5` - Weekdays at 6 PM
- `0 9-17 * * 1-5` - Every hour during business hours (9 AM - 5 PM) on weekdays

### Interval Format

These are examples of interval expressions you can use when scheduling workflows:

- `5m` - Every 5 minutes
- `30s` - Every 30 seconds
- `2h` - Every 2 hours
- `1d` - Every day
- `7d` - Every week

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

**What to say to Claude:**
```
Discover workflows from the remote source at http://remote.example.com:8881

Then sync any workflows with 'production' in their name
```

**What Claude does:**
- Discovers workflows from the remote source
- Syncs production workflows

**Expected Response:**
```json
{
  "status": "success",
  "message": "Discovered 5 remote workflows. Synced 2 production workflows.",
  "discovered": 5,
  "synced": [
    "Production Data Pipeline",
    "Production Monitoring Agent"
  ]
}
```

### Conditional Scheduling

**What to say to Claude:**
```
Check if the data analysis workflow is healthy, and if so, schedule it to run every 6 hours
```

**What Claude does:**
- Checks the workflow's last run status
- Schedules it to run every 6 hours if healthy

**Expected Response:**
```json
{
  "status": "success",
  "message": "Workflow is healthy. Scheduled to run every 6 hours.",
  "schedule_id": "sched_cond_789",
  "next_run": "2024-01-15T21:00:00Z"
}
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
   - Ask Claude to review task details
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
