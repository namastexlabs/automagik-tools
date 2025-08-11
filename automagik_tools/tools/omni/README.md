# OMNI MCP Tool

Multi-tenant omnichannel messaging MCP tool for managing WhatsApp, Slack, Discord and other messaging platforms through a unified interface.

## Overview

The OMNI tool provides intelligent aggregation of 30+ API endpoints into 4 main MCP functions, making it easy for AI agents to:
- Manage messaging instances across multiple channels
- Send any type of message (text, media, audio, stickers, contacts, reactions)
- Track and analyze message traces for debugging
- Manage user profiles and profile pictures

## Features

- **Multi-Channel Support**: WhatsApp, Slack, Discord (more coming)
- **Instance Management**: Create, configure, and manage multiple messaging instances
- **Unified Messaging**: Single interface for all message types
- **Trace Analytics**: Track messages, debug issues, analyze performance
- **Profile Management**: Fetch profiles, update profile pictures
- **QR Code Generation**: Easy connection setup for WhatsApp
- **Connection Status**: Real-time connection monitoring

## Configuration

Set the following environment variables:

```bash
# Required
OMNI_API_KEY=your-api-key-here       # API key for authentication

# Optional
OMNI_BASE_URL=http://localhost:8882  # OMNI API base URL (default: localhost:8882)
OMNI_DEFAULT_INSTANCE=my-whatsapp    # Default instance name for operations
OMNI_TIMEOUT=30                      # Request timeout in seconds
OMNI_MAX_RETRIES=3                   # Maximum retry attempts
```

## Installation & Usage

### Standalone Usage

```bash
# Run with STDIO transport (for Claude/Cursor)
uvx automagik-tools tool omni

# Run with SSE transport (for web interfaces)
uvx automagik-tools tool omni --transport sse --port 8000
```

### Claude Desktop Configuration

Add to your Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "omni": {
      "command": "uvx",
      "args": ["automagik-tools", "tool", "omni"],
      "env": {
        "OMNI_API_KEY": "your-api-key",
        "OMNI_BASE_URL": "http://localhost:8882",
        "OMNI_DEFAULT_INSTANCE": "my-whatsapp"
      }
    }
  }
}
```

### Cursor Configuration

Similar to Claude Desktop, add to your Cursor MCP configuration.

## Available Tools

### 1. `manage_instances`

Comprehensive instance management for all messaging channels.

**Operations:**
- `list` - List all instances with status
- `get` - Get specific instance details
- `create` - Create new instance
- `update` - Update instance configuration
- `delete` - Delete an instance
- `set_default` - Set instance as default
- `status` - Get connection status
- `qr` - Get QR code for connection
- `restart` - Restart instance connection
- `logout` - Logout/disconnect instance

**Examples:**
```python
# List all instances
manage_instances(operation="list")

# Get instance details
manage_instances(operation="get", instance_name="my-whatsapp")

# Create new WhatsApp instance
manage_instances(
    operation="create",
    config={
        "name": "business-whatsapp",
        "channel_type": "whatsapp",
        "auto_qr": True
    }
)

# Get QR code for connection
manage_instances(operation="qr", instance_name="my-whatsapp")
```

### 2. `send_message`

Unified interface for sending all message types.

**Message Types:**
- `text` - Send text messages
- `media` - Send images, videos, documents
- `audio` - Send audio messages or voice notes
- `sticker` - Send stickers
- `contact` - Send contact cards
- `reaction` - Send emoji reactions

**Examples:**
```python
# Send text message
send_message(
    message_type="text",
    phone="+1234567890",
    message="Hello from OMNI!"
)

# Send image with caption
send_message(
    message_type="media",
    phone="+1234567890",
    media_url="https://example.com/image.jpg",
    media_type="image",
    caption="Check out this image!"
)

# Send voice note
send_message(
    message_type="audio",
    phone="+1234567890",
    audio_url="https://example.com/voice.mp3"
)

# Send reaction
send_message(
    message_type="reaction",
    phone="+1234567890",
    message_id="msg_123",
    emoji="👍"
)

# Send contact
send_message(
    message_type="contact",
    phone="+1234567890",
    contacts=[
        {
            "full_name": "John Doe",
            "phone_number": "+0987654321",
            "email": "john@example.com"
        }
    ]
)
```

### 3. `manage_traces`

Comprehensive trace management for debugging and analytics.

**Operations:**
- `list` - List traces with filters
- `get` - Get specific trace details
- `get_payloads` - Get trace payloads for debugging
- `analytics` - Get analytics summary
- `by_phone` - Get traces for specific phone
- `cleanup` - Clean up old traces

**Examples:**
```python
# List recent traces
manage_traces(
    operation="list",
    instance_name="my-whatsapp",
    limit=20
)

# Get analytics
manage_traces(
    operation="analytics",
    start_date="2024-01-01",
    instance_name="my-whatsapp"
)

# Get traces for phone
manage_traces(
    operation="by_phone",
    phone="+1234567890"
)

# Preview cleanup (dry run)
manage_traces(
    operation="cleanup",
    days_old=30,
    dry_run=True
)
```

### 4. `manage_profiles`

Profile management operations.

**Operations:**
- `fetch` - Fetch user profile information
- `update_picture` - Update instance profile picture

**Examples:**
```python
# Fetch user profile
manage_profiles(
    operation="fetch",
    phone_number="+1234567890"
)

# Update profile picture
manage_profiles(
    operation="update_picture",
    picture_url="https://example.com/profile.jpg"
)
```

## Advanced Usage

### Using Default Instance

Set a default instance to avoid specifying it for every operation:

```bash
export OMNI_DEFAULT_INSTANCE=my-whatsapp
```

Then you can omit `instance_name` in operations:
```python
# Will use default instance
send_message(message_type="text", phone="+1234567890", message="Hello!")
```

### Filtering Traces

The trace management supports comprehensive filtering:

```python
manage_traces(
    operation="list",
    instance_name="my-whatsapp",
    trace_status="failed",          # Filter by status
    message_type="media",            # Filter by type
    has_media=True,                  # Only media messages
    start_date="2024-01-01",        # Date range
    end_date="2024-01-31",
    limit=100
)
```

### Bulk Operations

While the tool doesn't explicitly support bulk operations, you can easily script them:

```python
# Send message to multiple recipients
recipients = ["+1234567890", "+0987654321", "+1111111111"]
for phone in recipients:
    send_message(
        message_type="text",
        phone=phone,
        message="Bulk message to all!"
    )
```

## Error Handling

All tools return JSON responses with success status and error messages:

```json
{
  "success": false,
  "error": "Detailed error message here"
}
```

Always check the `success` field before processing results.

## Integration Tips

1. **Instance Discovery**: Start by listing instances to see what's available
2. **Connection Check**: Use `status` operation to verify connections before sending
3. **QR Code Flow**: For new WhatsApp instances, create → get QR → wait for scan → check status
4. **Trace Debugging**: Use traces to debug message delivery issues
5. **Analytics**: Regular analytics checks help monitor system health

## Support

For issues or questions:
- Check OMNI API documentation
- Review trace logs for debugging
- Contact Namastex Labs support

## License

Part of automagik-tools by Namastex Labs