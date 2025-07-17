# Agent Connect 🤖

Seamless multi-agent coordination through blocking message channels. Perfect for agent synchronization, request-response patterns, and workflow coordination.

## Features

- 🎧 **Blocking Message Listening** - True async blocking until messages arrive
- 📨 **Instant Message Sending** - Broadcast to other agents with optional reply waiting
- 📚 **Message History** - Browse past conversations and interactions
- 🔍 **Channel Discovery** - Find active channels and monitor agent activity
- 💾 **Cross-Instance Communication** - File-based storage for multi-process coordination
- ⏱️ **Flexible Timeouts** - Configurable timeouts for all operations

## Quick Start

### Using uvx (Recommended)

```bash
# Start the agent-connect MCP server
uvx automagik-tools serve agent-connect

# Or with custom transport
uvx automagik-tools serve agent-connect --transport sse --port 3001
```

### MCP Server Configuration

Add this to your MCP client configuration (e.g., Claude Desktop):

```json
{
  "mcpServers": {
    "agent-connect": {
      "command": "uvx",
      "args": ["automagik-tools", "serve", "agent-connect"],
      "env": {
        "AGENT_CONNECT_MAX_QUEUE_SIZE": "1000",
        "AGENT_CONNECT_DEFAULT_TIMEOUT": "300",
        "AGENT_CONNECT_STORAGE": "/path/to/your/storage"
      }
    }
  }
}
```

For SSE transport (web-based):
```json
{
  "mcpServers": {
    "agent-connect": {
      "command": "uvx",
      "args": ["automagik-tools", "serve", "agent-connect", "--transport", "sse", "--port", "3001"],
      "env": {
        "AGENT_CONNECT_MAX_QUEUE_SIZE": "1000",
        "AGENT_CONNECT_DEFAULT_TIMEOUT": "300"
      }
    }
  }
}
```

## Usage Examples

### Basic Agent Coordination

**Agent 1 (Listener):**
```python
# Listen for coordination messages
result = await listen_for_message(
    channel_id="coordination",
    timeout=60.0
)

if result["status"] == "received":
    print(f"Received: {result['message']['content']}")
```

**Agent 2 (Sender):**
```python
# Send coordination message
result = await send_message(
    channel_id="coordination",
    message="Start processing task #123"
)
```

### Request-Response Pattern

**Requesting Agent:**
```python
# Send request and wait for reply
result = await send_message(
    channel_id="task-requests",
    message="Process user data for ID 456",
    wait_for_reply=True,
    reply_timeout=30.0
)

if result["reply_status"] == "received":
    print(f"Reply: {result['reply']['content']}")
```

**Responding Agent:**
```python
# Listen for requests
request = await listen_for_message("task-requests", timeout=60.0)

if request["status"] == "received":
    # Process the request
    # ...
    
    # Send reply
    await send_reply(
        original_message_id=request["message"]["id"],
        reply_channel_id="task-requests", 
        reply_content="Task completed successfully"
    )
```

### Workflow Coordination

```python
# Multi-step workflow
channels = ["step1", "step2", "step3"]

for step in channels:
    # Wait for previous step completion
    result = await listen_for_message(step, timeout=120.0)
    
    if result["status"] == "received":
        # Process step
        print(f"Completed {step}")
        
        # Signal next step (if not last)
        if step != channels[-1]:
            next_step = channels[channels.index(step) + 1]
            await send_message(next_step, f"Ready for {next_step}")
```

## Tools Reference

### listen_for_message
Block until a message arrives on a channel.
- `channel_id: str` - Channel to listen on
- `timeout: Optional[float]` - Max seconds to wait (None = wait forever)

### send_message
Send a message to other agents on a channel.
- `channel_id: str` - Channel to send to
- `message: str` - Message content
- `wait_for_reply: bool` - Wait for a response
- `reply_timeout: Optional[float]` - Max seconds to wait for reply
- `metadata: Optional[Dict]` - Extra data to attach

### get_channel_history
Browse message history for a channel.
- `channel_id: str` - Channel to browse
- `limit: int` - Max messages to return (default: 100)

### clear_channel
Clear all messages in a channel and reset it.
- `channel_id: str` - Channel to clear

### list_active_channels
Discover all active channels and their status.

### send_reply
Send a reply to a specific message.
- `original_message_id: str` - ID of message being replied to
- `reply_channel_id: str` - Original channel
- `reply_content: str` - Reply message

## Configuration

Environment variables:

- `AGENT_CONNECT_MAX_QUEUE_SIZE` - Max messages per channel (default: 1000)
- `AGENT_CONNECT_MAX_HISTORY_SIZE` - Max history messages per channel (default: 100)
- `AGENT_CONNECT_DEFAULT_TIMEOUT` - Default listen timeout in seconds (default: 300)
- `AGENT_CONNECT_CLEANUP_INTERVAL` - Channel cleanup interval in seconds (default: 3600)
- `AGENT_CONNECT_INACTIVE_CHANNEL_HOURS` - Hours before cleaning inactive channels (default: 24)
- `AGENT_CONNECT_REPLY_TIMEOUT_DEFAULT` - Default reply timeout in seconds (default: 30)
- `AGENT_CONNECT_STORAGE` - Directory path for storing channel data (default: "/tmp/agent_connect")

## Storage

Agent Connect uses file-based storage for cross-instance communication (default: `/tmp/agent_connect/`):
- `channels.json` - Active channels and pending messages
- `history.json` - Message history

The storage directory can be customized using the `AGENT_CONNECT_STORAGE` environment variable.

This enables true multi-process agent coordination where agents in different processes can communicate seamlessly.

## Use Cases

- **Multi-Agent Workflows** - Coordinate complex tasks across multiple agents
- **Request-Response Patterns** - Implement agent-to-agent service calls
- **Event Broadcasting** - Notify multiple agents of important events
- **Workflow Orchestration** - Synchronize pipeline steps
- **Agent Approval Flows** - Wait for human or agent approval before proceeding
- **Status Coordination** - Share progress updates between agents