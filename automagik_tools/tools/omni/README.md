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

**Usage (Natural Language):**

Once the MCP server is running, interact with Claude in natural language:

> "List all my messaging instances"

> "Show me details for the my-whatsapp instance"

> "Create a new WhatsApp instance called business-whatsapp with auto QR code generation"

> "Get the QR code for my-whatsapp instance so I can connect"

Claude will use the `manage_instances` MCP tool to execute these requests and return the results.

### 2. `send_message`

Unified interface for sending all message types.

**Message Types:**
- `text` - Send text messages
- `media` - Send images, videos, documents
- `audio` - Send audio messages or voice notes
- `sticker` - Send stickers
- `contact` - Send contact cards
- `reaction` - Send emoji reactions

**Usage (Natural Language):**

Talk to Claude naturally to send any type of message:

> "Send a text message to +1234567890: 'Hello from OMNI!'"

> "Send this image to +1234567890 with caption 'Check out this image!': https://example.com/image.jpg"

> "Send a voice note to +1234567890: https://example.com/voice.mp3"

> "React with a thumbs up 👍 to message msg_123 for +1234567890"

> "Send contact card for John Doe (+0987654321, john@example.com) to +1234567890"

Claude will automatically choose the correct message type and use the `send_message` MCP tool.

### 3. `manage_traces`

Comprehensive trace management for debugging and analytics.

**Operations:**
- `list` - List traces with filters
- `get` - Get specific trace details
- `get_payloads` - Get trace payloads for debugging
- `analytics` - Get analytics summary
- `by_phone` - Get traces for specific phone
- `cleanup` - Clean up old traces

**Usage (Natural Language):**

> "List the 20 most recent message traces for my-whatsapp instance"

> "Show me analytics for my-whatsapp instance starting from January 1st, 2024"

> "Get all message traces for phone number +1234567890"

> "Preview cleaning up traces older than 30 days (dry run first)"

Claude will use the `manage_traces` MCP tool to provide debugging and analytics information.

### 4. `manage_profiles`

Profile management operations.

**Operations:**
- `fetch` - Fetch user profile information
- `update_picture` - Update instance profile picture

**Usage (Natural Language):**

> "Fetch the profile information for +1234567890"

> "Update my profile picture to this image: https://example.com/profile.jpg"

Claude will use the `manage_profiles` MCP tool to handle profile operations.

## Advanced Usage

### Using Default Instance

Set a default instance to avoid specifying it for every operation:

```bash
export OMNI_DEFAULT_INSTANCE=my-whatsapp
```

Then Claude can automatically use the default instance:

> "Send a message to +1234567890: 'Hello!'"

(Claude will automatically use the default instance without you needing to specify it)

### Filtering Traces

The trace management supports comprehensive filtering. Just ask Claude naturally:

> "List failed message traces for my-whatsapp instance from January 1-31, 2024, only show media messages, limit to 100 results"

Claude will apply all the appropriate filters when calling the `manage_traces` MCP tool.

### Bulk Operations

Claude can help coordinate sending to multiple recipients:

> "Send the message 'Bulk message to all!' to these numbers: +1234567890, +0987654321, +1111111111"

Claude will iterate through the recipients and use the `send_message` MCP tool for each one.

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