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

**In Claude Desktop, say:**
```
Check the status of the Automagik Hive service
```

**Claude responds:**
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

**In Claude Desktop, say:**
```
List all available agents in the Automagik Hive
```

**Claude responds:**
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

**In Claude Desktop, say:**
```
Start a conversation with the customer-service-agent about order #12345 for user customer-001
```

**Claude responds:**
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

**In Claude Desktop, say:**
```
Continue the conversation with customer-service-agent (run ID: run_abc123def456) with the message: My email is customer@example.com
```

**Claude responds:**
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

**In Claude Desktop, say:**
```
Execute the data-analysis-workflow with this input data for user analyst-001:
Dataset: sales_data_2024.csv
Analysis type: monthly_trends
Output format: report
```

**Claude responds:**
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

**In Claude Desktop, say:**
```
Start a team collaboration with the marketing-team for user marketing-manager. Task: Create a comprehensive social media campaign for our new product launch including content calendar, post designs, and engagement strategy
```

**Claude responds:**
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

**In Claude Desktop, say:**
```
Test the customer-service-agent with these scenarios for user test-user:
1. I want to return a product
2. My order hasn't arrived yet
3. I need to change my shipping address
4. Can I get a refund?

For each scenario, start a new conversation and then test a follow-up message: "Can you help me with that right now?"
```

**Claude does:**
- Tests the customer service agent with various scenarios
- Starts new conversations for each scenario
- Tests follow-up messages

**Claude responds:**
```json
{
  "status": "success",
  "message": "Tested 4 customer service scenarios successfully",
  "results": [
    {
      "scenario": "I want to return a product",
      "initial_response": "I'd be happy to help you with your return. Could you please provide your order number?",
      "follow_up_response": "I can process that return for you right away. I'll need your order number and reason for return."
    },
    {
      "scenario": "My order hasn't arrived yet",
      "initial_response": "I'm sorry to hear your order is delayed. Let me check the tracking information for you.",
      "follow_up_response": "I can help with that immediately. What's your order number so I can look up the details?"
    }
  ]
}
```

### Scenario 2: Data Analysis Pipeline

**In Claude Desktop, say:**
```
Execute the data-analysis-workflow for the data team with these quarterly sales datasets:
1. sales_q1.csv
2. sales_q2.csv
3. sales_q3.csv
4. sales_q4.csv

For each dataset, use analysis type "trends" and compare with previous periods. After completing all analyses, show the workflow execution history.
```

**Claude does:**
- Executes data analysis workflow for each quarterly dataset
- Compares trends with previous periods
- Shows execution history

**Claude responds:**
```json
{
  "status": "success",
  "message": "Executed 4 quarterly data analyses successfully",
  "results": [
    {
      "dataset": "sales_q1.csv",
      "summary": "Q1 analysis completed with 12% growth",
      "insights": ["New customer acquisition up 15%", "Top product: Widget Pro"]
    },
    {
      "dataset": "sales_q2.csv",
      "summary": "Q2 analysis completed with 8% growth",
      "insights": ["Seasonal products performed well", "Mobile app orders increased 20%"]
    }
  ],
  "total_executions": 4,
  "execution_history": {
    "workflow_id": "data-analysis-workflow",
    "total_runs": 12,
    "recent_runs": 4
  }
}
```

### Scenario 3: Multi-Agent Content Creation

**In Claude Desktop, say:**
```
Start a team collaboration with the content-creation-team for user content-manager. Task: Create a comprehensive blog post about AI in healthcare with these requirements:
- Research current trends and statistics
- Write engaging 2000-word article
- Create 3 infographics
- Optimize for SEO
- Generate social media snippets

Then monitor the progress of this collaboration.
```

**Claude does:**
- Assembles the content creation team
- Assigns the AI in healthcare blog task
- Monitors progress

**Claude responds:**
```json
{
  "status": "success",
  "message": "Content creation team assembled and working",
  "team_members": [
    "content-strategist-agent",
    "researcher-agent",
    "writer-agent",
    "designer-agent",
    "seo-specialist-agent"
  ],
  "initial_plan": {
    "phases": ["Research", "Writing", "Design", "SEO", "Social Media"],
    "estimated_time": "4 hours",
    "deliverables": ["Blog post", "Infographics", "Social snippets"]
  },
  "progress": {
    "percentage": 25,
    "current_phase": "Research",
    "completed_steps": 1,
    "total_steps": 5
  }
}
```

### Scenario 4: Agent Memory and Learning

**In Claude Desktop, say:**
```
Check what the customer-service-agent remembers about user customer-001, then start a new conversation with the same agent asking: "Do you remember my previous orders?"
```

**Claude does:**
- Checks the agent's memories about the user
- Starts a new conversation with context

**Claude responds:**
```json
{
  "status": "success",
  "message": "Retrieved agent memories and started new conversation",
  "memories": [
    {
      "content": "Customer has ordered 3 products in the last 6 months",
      "created_at": "2024-01-10T14:30:00Z"
    },
    {
      "content": "Customer prefers email communication and has premium account",
      "created_at": "2024-01-05T09:15:00Z"
    }
  ],
  "conversation_response": "Yes, I remember your previous orders. You've purchased 3 products from us in the last 6 months. Your most recent order was the Widget Pro, delivered on January 8th. Is there something specific about your previous orders you'd like to know?"
}
```

### Scenario 5: Quick Task Execution

**In Claude Desktop, say:**
```
Quickly analyze the sentiment of customer reviews from last month and provide a summary report using the data-analyst-agent
```

**Claude does:**
- Executes a quick sentiment analysis task
- Uses the specified data analyst agent

**Claude responds:**
```json
{
  "status": "success",
  "message": "Sentiment analysis completed successfully",
  "result": {
    "summary": "Overall positive sentiment with some areas for improvement",
    "sentiment_score": 0.72,
    "positive_reviews": 85,
    "negative_reviews": 15,
    "key_insights": [
      "Product quality praised consistently",
      "Shipping delays mentioned in 12% of negative reviews",
      "Customer service responsiveness needs improvement"
    ]
  },
  "execution_time": "12 seconds"
}
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

**In Claude Desktop, say:**
```
Rename the conversation with customer-service-agent (run ID: run_abc123def456) to "Customer 001 - Order Issue Resolution"

Also rename the workflow execution with ID exec_workflow_123 to "Q1 2024 Sales Analysis"
```

**Claude does:**
- Renames the specified conversation for better organization
- Renames the workflow execution

**Claude responds:**
```json
{
  "status": "success",
  "message": "Renamed conversation and workflow execution successfully",
  "renamed_items": [
    {
      "type": "conversation",
      "id": "run_abc123def456",
      "new_name": "Customer 001 - Order Issue Resolution"
    },
    {
      "type": "workflow_execution",
      "id": "exec_workflow_123",
      "new_name": "Q1 2024 Sales Analysis"
    }
  ]
}
```

### Filter and Search History

**In Claude Desktop, say:**
```
Get the specific conversation with customer-service-agent (run ID: run_abc123def456)

Then show all conversations for customer-service-agent with user customer-001

Finally, get the details for workflow execution with ID exec_workflow_123
```

**Claude does:**
- Retrieves the specific conversation
- Shows conversation history for the agent and user
- Gets workflow execution details

**Claude responds:**
```json
{
  "status": "success",
  "message": "Retrieved conversation history and execution details",
  "specific_conversation": {
    "run_id": "run_abc123def456",
    "agent_id": "customer-service-agent",
    "user_id": "customer-001",
    "messages": 8,
    "created_at": "2024-01-15T10:30:00Z"
  },
  "conversation_history": {
    "agent_id": "customer-service-agent",
    "user_id": "customer-001",
    "total_conversations": 3,
    "recent_conversations": [
      {
        "run_id": "run_abc123def456",
        "created_at": "2024-01-15T10:30:00Z",
        "message_count": 8
      }
    ]
  },
  "workflow_execution": {
    "execution_id": "exec_workflow_123",
    "workflow_id": "data-analysis-workflow",
    "status": "completed",
    "execution_time": "45 seconds"
  }
}
```

### Cleanup Old Data

**In Claude Desktop, say:**
```
Delete the old conversation with customer-service-agent (run ID: run_old_conversation)

Also delete the workflow execution with ID exec_old_workflow

Finally, delete the team collaboration with ID collab_old_team
```

**Claude does:**
- Deletes the specified old conversation
- Removes the workflow execution
- Cleans up the team collaboration

**Claude responds:**
```json
{
  "status": "success",
  "message": "Cleaned up old data successfully",
  "deleted_items": [
    {
      "type": "conversation",
      "id": "run_old_conversation",
      "status": "deleted"
    },
    {
      "type": "workflow_execution",
      "id": "exec_old_workflow",
      "status": "deleted"
    },
    {
      "type": "team_collaboration",
      "id": "collab_old_team",
      "status": "deleted"
    }
  ]
}
```

## Troubleshooting

### Common Issues

1. **"Hive not accessible"**
   - Check `HIVE_API_BASE_URL` is correct
   - Verify Hive server is running
   - Test connection: `curl http://localhost:8886/health`

2. **"Agent not found"**
   - Ask Claude to list available agents
   - Verify agent_id spelling
   - Check agent is active in Hive

3. **"Workflow execution failed"**
   - Check input_data format matches workflow requirements
   - Ask Claude to show workflow details to see expected inputs
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
5. **Use Quick Run**: For simple tasks, ask Claude to quickly run a task for efficiency

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
