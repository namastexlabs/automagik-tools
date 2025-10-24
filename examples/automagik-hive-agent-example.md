# Automagik Hive Agent Collaboration Example

This example demonstrates how to use the Automagik Hive tool to interact with AI agents, execute workflows, and collaborate with agent teams in a safe testing environment.

## Use Case Description

Use Automagik Hive to:
- Test and interact with AI agents before production deployment
- Execute complex multi-step workflows with your data
- Collaborate with teams of specialized agents on projects
- Maintain conversation history and agent memories
- Experiment with agent capabilities in a risk-free playground
- Monitor agent performance and workflow results

Perfect for developers building AI agent systems, testing agent behaviors, and orchestrating multi-agent workflows.

## Setup

### Prerequisites

1. **Automagik Hive Instance**: Running Hive server
2. **API Access**: Hive API endpoint and optional API key
3. **Python 3.12+**: For running automagik-tools

### Environment Configuration

Create a `.env` file or set environment variables:

```bash
# Required
HIVE_API_BASE_URL=http://localhost:8886

# Optional
HIVE_API_KEY=your_hive_api_key_here  # Only if API requires authentication
HIVE_TIMEOUT=30                       # Request timeout in seconds
```

## CLI Commands

### Direct Command Line Usage

```bash
# Run with stdio transport (for Claude/Cursor)
uvx automagik-tools tool automagik-hive --transport stdio

# Run with SSE transport
uvx automagik-tools tool automagik-hive --transport sse --port 8000

# Generate Claude Desktop config
uvx automagik-tools mcp-config automagik-hive
```

### Check Hive Status

```bash
# Check if Hive is running
curl http://localhost:8886/health

# List available agents
curl http://localhost:8886/api/agents
```

## MCP Configuration

### For Claude Desktop

Add this to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "automagik-hive": {
      "command": "uvx",
      "args": [
        "automagik-tools",
        "tool",
        "automagik-hive",
        "--transport",
        "stdio"
      ],
      "env": {
        "HIVE_API_BASE_URL": "http://localhost:8886",
        "HIVE_TIMEOUT": "30"
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
    "automagik-hive": {
      "command": "uvx",
      "args": [
        "automagik-tools",
        "tool",
        "automagik-hive",
        "--transport",
        "stdio"
      ],
      "env": {
        "HIVE_API_BASE_URL": "http://localhost:8886"
      }
    }
  }
}
```

## Expected Output

### 1. Check Hive Status

**Command:**
```python
check_playground_status()
```

**Expected Response:**
```json
{
  "status": "healthy",
  "hive_version": "1.0.0",
  "available_agents": 5,
  "available_workflows": 3,
  "available_teams": 2,
  "uptime": "2 days, 5 hours",
  "message": "Hive is running and ready"
}
```

### 2. List Available Agents

**Command:**
```python
list_available_agents()
```

**Expected Response:**
```json
{
  "agents": [
    {
      "id": "customer-service-agent",
      "name": "Customer Service Agent",
      "description": "Handles customer inquiries and support requests",
      "capabilities": ["conversation", "memory", "tools"],
      "status": "active",
      "model": "gpt-4o"
    },
    {
      "id": "data-analyst-agent",
      "name": "Data Analyst Agent",
      "description": "Analyzes data and generates insights",
      "capabilities": ["data_analysis", "visualization", "reporting"],
      "status": "active",
      "model": "gpt-4o"
    },
    {
      "id": "code-reviewer-agent",
      "name": "Code Reviewer",
      "description": "Reviews code for quality and best practices",
      "capabilities": ["code_review", "static_analysis"],
      "status": "active",
      "model": "gpt-4o"
    }
  ],
  "total_count": 3
}
```

### 3. Start Agent Conversation

**Command:**
```python
start_agent_conversation(
    agent_id="customer-service-agent",
    message="Hello, I need help with my recent order #12345",
    user_id="customer-001"
)
```

**Expected Response:**
```json
{
  "status": "success",
  "run_id": "run_abc123def456",
  "agent_id": "customer-service-agent",
  "response": "Hello! I'd be happy to help you with order #12345. Let me look that up for you. Could you please provide your email address associated with the order so I can verify your account?",
  "conversation_id": "conv_xyz789",
  "created_at": "2024-01-15T10:30:00Z",
  "tokens_used": 45
}
```

### 4. Continue Agent Conversation

**Command:**
```python
continue_agent_conversation(
    agent_id="customer-service-agent",
    run_id="run_abc123def456",
    message="My email is customer@example.com"
)
```

**Expected Response:**
```json
{
  "status": "success",
  "run_id": "run_abc123def456",
  "response": "Thank you! I've found your order #12345 placed on January 10th. It's currently in transit and expected to arrive by January 18th. The tracking number is TRK123456789. Is there anything specific about this order you'd like to know?",
  "conversation_id": "conv_xyz789",
  "tokens_used": 62,
  "context_retrieved": true
}
```

### 5. Execute Workflow

**Command:**
```python
execute_workflow(
    workflow_id="data-analysis-workflow",
    input_data={
        "dataset": "sales_data_2024.csv",
        "analysis_type": "monthly_trends",
        "output_format": "report"
    },
    user_id="analyst-001"
)
```

**Expected Response:**
```json
{
  "status": "success",
  "execution_id": "exec_workflow_123",
  "workflow_id": "data-analysis-workflow",
  "result": {
    "summary": "Analysis completed successfully",
    "insights": [
      "Sales increased 15% in Q1 2024",
      "Top performing product: Widget Pro",
      "Peak sales day: Fridays"
    ],
    "charts_generated": 3,
    "report_url": "https://hive.example.com/reports/exec_workflow_123"
  },
  "execution_time": "45 seconds",
  "steps_completed": 5,
  "created_at": "2024-01-15T10:35:00Z"
}
```

### 6. Start Team Collaboration

**Command:**
```python
start_team_collaboration(
    team_id="marketing-team",
    task_description="Create a comprehensive social media campaign for our new product launch including content calendar, post designs, and engagement strategy",
    user_id="marketing-manager"
)
```

**Expected Response:**
```json
{
  "status": "success",
  "collaboration_id": "collab_team_456",
  "team_id": "marketing-team",
  "team_members": [
    "content-strategist-agent",
    "graphic-designer-agent",
    "social-media-manager-agent"
  ],
  "coordinator_response": "I've assembled the marketing team to work on your product launch campaign. Here's our approach:\n\n1. Content Strategist will develop the messaging framework\n2. Graphic Designer will create visual assets\n3. Social Media Manager will plan the posting schedule\n\nLet's start with the content strategy...",
  "initial_plan": {
    "phases": ["Strategy", "Design", "Scheduling", "Review"],
    "estimated_time": "2 hours",
    "deliverables": ["Content calendar", "Post designs", "Engagement plan"]
  },
  "created_at": "2024-01-15T10:40:00Z"
}
```

## Real-World Usage Scenarios

### Scenario 1: Customer Support Automation

```python
# Test customer service agent with various scenarios
test_scenarios = [
    "I want to return a product",
    "My order hasn't arrived yet",
    "I need to change my shipping address",
    "Can I get a refund?"
]

for scenario in test_scenarios:
    # Start new conversation for each scenario
    result = start_agent_conversation(
        agent_id="customer-service-agent",
        message=scenario,
        user_id="test-user"
    )
    
    print(f"Scenario: {scenario}")
    print(f"Response: {result['response']}\n")
    
    # Test follow-up
    follow_up = continue_agent_conversation(
        agent_id="customer-service-agent",
        run_id=result['run_id'],
        message="Can you help me with that right now?"
    )
    
    print(f"Follow-up: {follow_up['response']}\n")
    print("-" * 50)
```

### Scenario 2: Data Analysis Pipeline

```python
# Execute data analysis workflow with different datasets
datasets = [
    {"name": "sales_q1.csv", "type": "quarterly"},
    {"name": "sales_q2.csv", "type": "quarterly"},
    {"name": "sales_q3.csv", "type": "quarterly"},
    {"name": "sales_q4.csv", "type": "quarterly"}
]

results = []
for dataset in datasets:
    result = execute_workflow(
        workflow_id="data-analysis-workflow",
        input_data={
            "dataset": dataset["name"],
            "analysis_type": "trends",
            "compare_previous": True
        },
        user_id="data-team"
    )
    results.append(result)
    
    print(f"Analyzed {dataset['name']}: {result['result']['summary']}")

# Get comprehensive view
history = view_workflow_execution_history(
    workflow_id="data-analysis-workflow",
    user_id="data-team"
)
print(f"\nTotal executions: {len(history['executions'])}")
```

### Scenario 3: Multi-Agent Content Creation

```python
# Collaborate with content creation team
collaboration = start_team_collaboration(
    team_id="content-creation-team",
    task_description="""
    Create a comprehensive blog post about AI in healthcare:
    - Research current trends and statistics
    - Write engaging 2000-word article
    - Create 3 infographics
    - Optimize for SEO
    - Generate social media snippets
    """,
    user_id="content-manager"
)

print(f"Team assembled: {collaboration['team_members']}")
print(f"Initial plan: {collaboration['initial_plan']}")

# Monitor progress
details = get_team_collaboration_details(
    collaboration_id=collaboration['collaboration_id']
)

print(f"Progress: {details['progress_percentage']}%")
print(f"Current phase: {details['current_phase']}")
```

### Scenario 4: Agent Memory and Learning

```python
# Check what agent remembers about user
memories = view_agent_memories(
    agent_id="customer-service-agent",
    user_id="customer-001"
)

print("Agent Memories:")
for memory in memories['memories']:
    print(f"- {memory['content']} (learned: {memory['created_at']})")

# Continue conversation with context
result = start_agent_conversation(
    agent_id="customer-service-agent",
    message="Do you remember my previous orders?",
    user_id="customer-001"
)

print(f"\nAgent response: {result['response']}")
```

### Scenario 5: Quick Task Execution

```python
# Use quick_run for fast task execution
result = quick_run(
    task_description="Analyze the sentiment of customer reviews from last month and provide a summary report",
    agent_id="data-analyst-agent"  # Optional: specify agent
)

print(f"Task completed: {result['status']}")
print(f"Result: {result['result']}")
print(f"Execution time: {result['execution_time']}")
```

## Features Demonstrated

1. **Agent Conversations**: Interactive dialogues with AI agents
2. **Workflow Execution**: Run complex multi-step processes
3. **Team Collaboration**: Coordinate multiple agents on tasks
4. **Memory Management**: Agents remember user interactions
5. **Session History**: Track all conversations and executions
6. **Quick Actions**: Fast task execution without complex setup
7. **Status Monitoring**: Check hive health and availability

## Best Practices

1. **Test Before Production**: Use Hive to test agent behaviors safely
2. **Session Management**: Use meaningful user_ids for tracking
3. **Memory Review**: Periodically check what agents remember
4. **Workflow Validation**: Test workflows with sample data first
5. **Error Handling**: Check response status before proceeding
6. **Resource Cleanup**: Delete old sessions to free resources
7. **Naming Conventions**: Use descriptive names for sessions

## Advanced Usage

### Rename Sessions for Organization

```python
# Rename conversation for easy reference
rename_agent_conversation(
    agent_id="customer-service-agent",
    run_id="run_abc123def456",
    new_name="Customer 001 - Order Issue Resolution"
)

# Rename workflow execution
rename_workflow_execution(
    execution_id="exec_workflow_123",
    new_name="Q1 2024 Sales Analysis"
)
```

### Filter and Search History

```python
# Get specific conversation
conversation = get_specific_agent_conversation(
    agent_id="customer-service-agent",
    run_id="run_abc123def456"
)

# View all conversations for an agent
history = view_agent_conversation_history(
    agent_id="customer-service-agent",
    user_id="customer-001"
)

# Get workflow execution details
execution = get_workflow_execution_details(
    execution_id="exec_workflow_123"
)
```

### Cleanup Old Data

```python
# Delete old conversations
delete_agent_conversation(
    agent_id="customer-service-agent",
    run_id="run_old_conversation"
)

# Delete workflow executions
delete_workflow_execution(
    execution_id="exec_old_workflow"
)

# Delete team collaborations
delete_team_collaboration(
    collaboration_id="collab_old_team"
)
```

## Troubleshooting

### Common Issues

1. **"Hive not accessible"**
   - Check `HIVE_API_BASE_URL` is correct
   - Verify Hive server is running
   - Test connection: `curl http://localhost:8886/health`

2. **"Agent not found"**
   - List available agents with `list_available_agents()`
   - Verify agent_id spelling
   - Check agent is active in Hive

3. **"Workflow execution failed"**
   - Check input_data format matches workflow requirements
   - Use `get_workflow_details()` to see expected inputs
   - Review execution logs for specific errors

4. **"Session not found"**
   - Session may have expired
   - Verify run_id or execution_id is correct
   - Check session history with list functions

5. **"Memory not persisting"**
   - Ensure user_id is consistent across sessions
   - Check Hive memory configuration
   - Verify agent has memory enabled

## Performance Tips

1. **Reuse Sessions**: Continue conversations instead of starting new ones
2. **Batch Operations**: Group related tasks together
3. **Monitor Resources**: Check Hive status regularly
4. **Cleanup Regularly**: Delete old sessions to improve performance
5. **Use Quick Run**: For simple tasks, use `quick_run()` for efficiency

## Security Considerations

- **API Keys**: Store securely, never in code
- **User IDs**: Use anonymized identifiers when possible
- **Data Privacy**: Be aware of what agents remember
- **Access Control**: Implement proper authentication if required
- **Audit Logs**: Monitor agent interactions for compliance

## Next Steps

1. **Production Deployment**: Move tested agents to production
2. **Custom Agents**: Create specialized agents for your use case
3. **Workflow Library**: Build reusable workflow templates
4. **Integration**: Connect Hive with your applications
5. **Monitoring**: Set up alerts for agent performance

## Additional Resources

- [Automagik Hive Documentation](https://github.com/namastexlabs/automagik-hive)
- [Agent Development Guide](https://docs.automagik.ai/agents)
- [Workflow Creation Tutorial](https://docs.automagik.ai/workflows)
- [Automagik Tools GitHub](https://github.com/namastexlabs/automagik-tools)
