# OMNI Multi-Channel Messaging Example

This example demonstrates how to use the OMNI tool for unified multi-channel messaging across WhatsApp, Slack, Discord, and other platforms through a single intelligent interface.

## Use Case Description

Use OMNI to:
- Manage messaging instances across multiple channels (WhatsApp, Slack, Discord)
- Send any type of message through a unified interface
- Track message delivery and debug issues with trace analytics
- Manage user profiles and profile pictures
- Monitor connection status across all channels
- Build omnichannel customer engagement systems

Perfect for customer support teams, marketing automation, multi-platform notifications, and building unified messaging systems.

## Setup

### Prerequisites

1. **OMNI Instance**: Running OMNI server
2. **API Credentials**: OMNI API key
3. **Messaging Accounts**: WhatsApp Business, Slack workspace, Discord server
4. **Python 3.12+**: For running automagik-tools

### Environment Configuration

Create a `.env` file or set environment variables:

```bash
# Required
OMNI_API_KEY=your-omni-api-key-here

# Optional
OMNI_BASE_URL=http://localhost:8882      # OMNI API base URL
OMNI_DEFAULT_INSTANCE=my-whatsapp        # Default instance name
OMNI_TIMEOUT=30                          # Request timeout in seconds
OMNI_MAX_RETRIES=3                       # Maximum retry attempts
```

## CLI Commands

### Direct Command Line Usage

```bash
# Run with stdio transport (for Claude/Cursor)
uvx automagik-tools tool omni --transport stdio

# Run with SSE transport (for web interfaces)
uvx automagik-tools tool omni --transport sse --port 8000

# Run with HTTP transport
uvx automagik-tools tool omni --transport http --port 8001
```

### Check OMNI Status

```bash
# Check API health
curl http://localhost:8882/health \
  -H "X-API-Key: your-omni-api-key"

# List instances
curl http://localhost:8882/api/instances \
  -H "X-API-Key: your-omni-api-key"
```

## MCP Configuration

### For Claude Desktop

Add this to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "omni": {
      "command": "uvx",
      "args": [
        "automagik-tools",
        "tool",
        "omni",
        "--transport",
        "stdio"
      ],
      "env": {
        "OMNI_API_KEY": "your-omni-api-key",
        "OMNI_BASE_URL": "http://localhost:8882",
        "OMNI_DEFAULT_INSTANCE": "my-whatsapp",
        "OMNI_TIMEOUT": "30"
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
    "omni": {
      "command": "uvx",
      "args": [
        "automagik-tools",
        "tool",
        "omni",
        "--transport",
        "stdio"
      ],
      "env": {
        "OMNI_API_KEY": "your-omni-api-key",
        "OMNI_BASE_URL": "http://localhost:8882"
      }
    }
  }
}
```

## Expected Output

### 1. List All Instances

**In Claude Desktop, say:**
```
List all OMNI messaging instances and their connection status
```

**Claude responds:**
```json
{
  "status": "success",
  "instances": [
    {
      "name": "my-whatsapp",
      "channel_type": "whatsapp",
      "connection_status": "connected",
      "phone_number": "+1234567890",
      "created_at": "2024-01-10T10:00:00Z",
      "last_activity": "2024-01-15T14:30:00Z",
      "messages_sent": 1250,
      "messages_received": 890
    },
    {
      "name": "support-slack",
      "channel_type": "slack",
      "connection_status": "connected",
      "workspace": "MyCompany",
      "created_at": "2024-01-12T09:00:00Z",
      "last_activity": "2024-01-15T14:25:00Z",
      "messages_sent": 450,
      "messages_received": 320
    },
    {
      "name": "community-discord",
      "channel_type": "discord",
      "connection_status": "connected",
      "server": "Community Server",
      "created_at": "2024-01-14T11:00:00Z",
      "last_activity": "2024-01-15T14:20:00Z",
      "messages_sent": 180,
      "messages_received": 240
    }
  ],
  "total_count": 3
}
```

### 2. Create New Instance

**In Claude Desktop, say:**
```
Create a new OMNI messaging instance named business-whatsapp for WhatsApp with auto QR code generation and webhook URL https://example.com/webhook
```

**Claude responds:**
```json
{
  "status": "success",
  "instance": {
    "name": "business-whatsapp",
    "channel_type": "whatsapp",
    "connection_status": "awaiting_qr",
    "qr_code": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA...",
    "qr_expires_at": "2024-01-15T14:40:00Z",
    "created_at": "2024-01-15T14:35:00Z"
  },
  "message": "Instance created. Scan QR code to connect WhatsApp."
}
```

### 3. Send Text Message

**In Claude Desktop, say:**
```
Send a text message to +1234567890 via my-whatsapp instance: "Hello! Thank you for contacting our support team. How can we help you today?"
```

**Claude responds:**
```json
{
  "status": "success",
  "message_id": "msg_abc123def456",
  "instance": "my-whatsapp",
  "recipient": "+1234567890",
  "message_type": "text",
  "sent_at": "2024-01-15T14:36:00Z",
  "delivery_status": "sent",
  "trace_id": "trace_xyz789"
}
```

### 4. Send Media Message

**In Claude Desktop, say:**
```
Send a media message to +1234567890 via my-whatsapp instance with the image from https://example.com/product-image.jpg, media type image, and caption: "Check out our new product! 🎉 Available now with 20% off."
```

**Claude responds:**
```json
{
  "status": "success",
  "message_id": "msg_def456ghi789",
  "instance": "my-whatsapp",
  "recipient": "+1234567890",
  "message_type": "media",
  "media_type": "image",
  "caption": "Check out our new product! 🎉 Available now with 20% off.",
  "sent_at": "2024-01-15T14:37:00Z",
  "delivery_status": "sent",
  "trace_id": "trace_abc456"
}
```

### 5. Get Message Traces

**In Claude Desktop, say:**
```
Get the last 10 message traces for the my-whatsapp instance
```

**Claude responds:**
```json
{
  "status": "success",
  "traces": [
    {
      "trace_id": "trace_xyz789",
      "instance": "my-whatsapp",
      "message_type": "text",
      "recipient": "+1234567890",
      "status": "delivered",
      "sent_at": "2024-01-15T14:36:00Z",
      "delivered_at": "2024-01-15T14:36:02Z",
      "read_at": "2024-01-15T14:36:15Z"
    },
    {
      "trace_id": "trace_abc456",
      "instance": "my-whatsapp",
      "message_type": "media",
      "media_type": "image",
      "recipient": "+1234567890",
      "status": "delivered",
      "sent_at": "2024-01-15T14:37:00Z",
      "delivered_at": "2024-01-15T14:37:03Z"
    }
  ],
  "total_count": 2,
  "page": 1,
  "limit": 10
}
```

### 6. Get Analytics

**In Claude Desktop, say:**
```
Get analytics for the my-whatsapp instance from January 1, 2024 to January 15, 2024
```

**Claude responds:**
```json
{
  "status": "success",
  "analytics": {
    "instance": "my-whatsapp",
    "period": {
      "start": "2024-01-01T00:00:00Z",
      "end": "2024-01-15T23:59:59Z"
    },
    "total_messages": 1250,
    "messages_by_type": {
      "text": 850,
      "media": 280,
      "audio": 65,
      "contact": 35,
      "location": 20
    },
    "delivery_stats": {
      "sent": 1250,
      "delivered": 1235,
      "read": 1180,
      "failed": 15
    },
    "success_rate": "98.8%",
    "average_delivery_time": "2.3 seconds",
    "peak_hours": ["10:00-11:00", "14:00-15:00", "19:00-20:00"]
  }
}
```

## Real-World Usage Scenarios

### Scenario 1: Multi-Channel Customer Support

**In Claude Desktop, say:**
```
First, check if all messaging instances are connected:
- support-whatsapp
- support-slack
- support-discord

For any disconnected instances, restart the connection.

Then, send this welcome message to users on all channels:
"Hello! Welcome to our support. How can we help you today?"

Send to:
- WhatsApp: +1234567890 via support-whatsapp
- Slack: User U12345678 via support-slack
- Discord: User 987654321098765432 via support-discord
```

**Claude does:**
- Checks connection status of all instances
- Restarts any disconnected instances
- Sends welcome messages across all channels

**Claude responds:**
```json
{
  "status": "success",
  "message": "Multi-channel support setup completed successfully",
  "instance_status": [
    {
      "instance": "support-whatsapp",
      "status": "connected",
      "action": "none"
    },
    {
      "instance": "support-slack",
      "status": "connected",
      "action": "none"
    },
    {
      "instance": "support-discord",
      "status": "connected",
      "action": "none"
    }
  ],
  "messages_sent": [
    {
      "channel": "whatsapp",
      "recipient": "+1234567890",
      "status": "sent",
      "message_id": "msg_whatsapp_123"
    },
    {
      "channel": "slack",
      "recipient": "U12345678",
      "status": "sent",
      "message_id": "msg_slack_456"
    },
    {
      "channel": "discord",
      "recipient": "987654321098765432",
      "status": "sent",
      "message_id": "msg_discord_789"
    }
  ]
}
```

### Scenario 2: Automated Marketing Campaign

**In Claude Desktop, say:**
```
Run an automated marketing campaign with this message:

🎉 Special Offer Just for You!

Hi {name}! 

Get 30% off on all products this weekend only!
Use code: WEEKEND30

Shop now: https://example.com/shop

Valid until Sunday midnight.

Send personalized messages to these customers via WhatsApp:
1. John Doe at +1234567890
2. Jane Smith at +0987654321

Add a 1-second delay between messages to avoid rate limiting.

After sending, show campaign performance analytics for the marketing-whatsapp instance from January 15-17, 2024.
```

**Claude does:**
- Sends personalized promotional messages to customers
- Adds delays between messages
- Tracks campaign performance with analytics

**Claude responds:**
```json
{
  "status": "success",
  "message": "Marketing campaign executed successfully",
  "messages_sent": [
    {
      "recipient": "John Doe",
      "phone": "+1234567890",
      "status": "sent",
      "message_id": "msg_campaign_123"
    },
    {
      "recipient": "Jane Smith",
      "phone": "+0987654321",
      "status": "sent",
      "message_id": "msg_campaign_456"
    }
  ],
  "campaign_analytics": {
    "period": "2024-01-15 to 2024-01-17",
    "messages_sent": 2,
    "delivery_rate": "100%",
    "read_rate": "85.0%",
    "success_rate": "100%"
  }
}
```

### Scenario 3: Order Notifications with Media

**In Claude Desktop, say:**
```
Send order confirmation notifications with media for this order:

Order ID: ORD-12345
Customer phone: +1234567890
Product image: https://example.com/products/widget-pro.jpg
Total: $99.99

First, send a media message with the product image and this caption:

✅ Order Confirmed!

Order ID: ORD-12345
Total: $99.99

Your order will be delivered in 3-5 business days.
Track your order: https://example.com/track/ORD-12345

Thank you for shopping with us!

Then, send a contact card with customer support information:
Name: Customer Support
Phone: +1-800-SUPPORT
Email: support@example.com

Send both messages via the orders-whatsapp instance.
```

**Claude does:**
- Sends order confirmation with product image
- Follows up with customer support contact information

**Claude responds:**
```json
{
  "status": "success",
  "message": "Order notification sent successfully",
  "order_confirmation": {
    "order_id": "ORD-12345",
    "recipient": "+1234567890",
    "media_message": {
      "status": "sent",
      "message_id": "msg_media_123",
      "media_type": "image"
    },
    "contact_message": {
      "status": "sent",
      "message_id": "msg_contact_456"
    }
  }
}
```

### Scenario 4: Trace Debugging and Monitoring

**In Claude Desktop, say:**
```
Monitor failed messages for the my-whatsapp instance, showing up to 50 failed traces. For each failed message, show:
- Trace ID
- Recipient
- Message type
- Sent time
- Error message
- Retry count

Then, get all message traces for phone number +1234567890 and show the total count and timestamp of the last message.
```

**Claude does:**
- Monitors failed messages and provides debugging information
- Retrieves message history for a specific phone number

**Claude responds:**
```json
{
  "status": "success",
  "message": "Trace debugging completed",
  "failed_messages": {
    "total_count": 2,
    "traces": [
      {
        "trace_id": "trace_failed_123",
        "recipient": "+0987654321",
        "message_type": "text",
        "sent_at": "2024-01-15T14:30:00Z",
        "error": "Recipient not available",
        "retry_count": 3
      }
    ]
  },
  "customer_history": {
    "phone": "+1234567890",
    "total_messages": 15,
    "last_message": "2024-01-15T14:36:00Z"
  }
}
```

### Scenario 5: Instance Management and QR Code Setup

**In Claude Desktop, say:**
```
Create a new WhatsApp messaging instance named sales-whatsapp with auto QR code generation.

Then, get the QR code for scanning and show when it expires.

Next, poll the connection status every 10 seconds for up to 30 attempts until connected, then set this instance as the default.
```

**Claude does:**
- Creates a new WhatsApp instance with auto QR generation
- Retrieves the QR code for scanning
- Polls connection status until connected
- Sets the instance as default

**Claude responds:**
```json
{
  "status": "success",
  "message": "Instance management completed successfully",
  "instance_setup": {
    "instance_created": "sales-whatsapp",
    "connection_status": "awaiting_qr",
    "qr_code": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA...",
    "qr_expires_at": "2024-01-15T15:00:00Z"
  },
  "connection_monitoring": {
    "attempts": 3,
    "connected": true,
    "phone_number": "+1234567890",
    "final_status": "connected"
  },
  "default_setting": {
    "instance": "sales-whatsapp",
    "status": "set_as_default"
  }
}
```

## Features Demonstrated

1. **Multi-Channel Support**: Unified interface for WhatsApp, Slack, Discord
2. **Instance Management**: Create, configure, and monitor messaging instances
3. **Unified Messaging**: Single API for all message types
4. **Trace Analytics**: Track delivery, debug issues, analyze performance
5. **Profile Management**: Fetch and update user profiles
6. **QR Code Setup**: Easy WhatsApp connection with QR codes
7. **Connection Monitoring**: Real-time status tracking

## Message Types Supported

### Text Messages

**In Claude Desktop, say:**
```
Send a text message to +1234567890: "Hello!"
```

**Claude responds:**
```json
{
  "status": "success",
  "message_id": "msg_text_123",
  "recipient": "+1234567890",
  "message_type": "text",
  "sent_at": "2024-01-15T14:36:00Z",
  "delivery_status": "sent"
}
```

### Media Messages (Images, Videos, Documents)

**In Claude Desktop, say:**
```
Send a media message to +1234567890 with the image from https://example.com/image.jpg, media type image, and caption: "Check this out!"
```

**Claude responds:**
```json
{
  "status": "success",
  "message_id": "msg_media_456",
  "recipient": "+1234567890",
  "message_type": "media",
  "media_type": "image",
  "caption": "Check this out!",
  "sent_at": "2024-01-15T14:37:00Z",
  "delivery_status": "sent"
}
```

### Audio Messages

**In Claude Desktop, say:**
```
Send an audio message to +1234567890 with the audio file from https://example.com/voice.mp3
```

**Claude responds:**
```json
{
  "status": "success",
  "message_id": "msg_audio_789",
  "recipient": "+1234567890",
  "message_type": "audio",
  "sent_at": "2024-01-15T14:38:00Z",
  "delivery_status": "sent"
}
```

### Stickers

**In Claude Desktop, say:**
```
Send a sticker to +1234567890 with the sticker from https://example.com/sticker.webp
```

**Claude responds:**
```json
{
  "status": "success",
  "message_id": "msg_sticker_123",
  "recipient": "+1234567890",
  "message_type": "sticker",
  "sent_at": "2024-01-15T14:39:00Z",
  "delivery_status": "sent"
}
```

### Contact Cards

**In Claude Desktop, say:**
```
Send a contact card to +1234567890 for John Doe with phone number +1234567890
```

**Claude responds:**
```json
{
  "status": "success",
  "message_id": "msg_contact_456",
  "recipient": "+1234567890",
  "message_type": "contact",
  "sent_at": "2024-01-15T14:40:00Z",
  "delivery_status": "sent"
}
```

### Reactions

**In Claude Desktop, say:**
```
React to message msg_123 from +1234567890 with a thumbs up emoji
```

**Claude responds:**
```json
{
  "status": "success",
  "message_id": "msg_reaction_789",
  "recipient": "+1234567890",
  "message_type": "reaction",
  "emoji": "👍",
  "sent_at": "2024-01-15T14:41:00Z",
  "delivery_status": "sent"
}
```

## Best Practices

1. **Instance Organization**: Use separate instances for different purposes (support, marketing, orders)
2. **Rate Limiting**: Add delays between bulk messages to avoid blocking
3. **Error Handling**: Always check response status and handle failures
4. **Trace Monitoring**: Regularly check traces for failed messages
5. **Analytics Review**: Monitor delivery rates and performance metrics
6. **Connection Health**: Check instance status before sending messages
7. **Default Instance**: Set a default to simplify operations

## Advanced Usage

### Cleanup Old Traces

**In Claude Desktop, say:**
```
Preview cleanup of message traces older than 30 days, then confirm and execute the cleanup if traces are found to be deleted.
```

**Claude does:**
- Previews cleanup of old traces
- Executes cleanup if traces are found

**Claude responds:**
```json
{
  "status": "success",
  "message": "Trace cleanup completed successfully",
  "preview": {
    "traces_to_delete": 1250,
    "space_freed": "25.6 MB"
  },
  "cleanup_result": {
    "deleted_count": 1250,
    "space_freed": "25.6 MB"
  }
}
```

### Profile Management

**In Claude Desktop, say:**
```
Fetch the user profile for +1234567890 on the my-whatsapp instance, then update the instance profile picture with the image from https://example.com/company-logo.jpg
```

**Claude does:**
- Fetches user profile information
- Updates the instance profile picture

**Claude responds:**
```json
{
  "status": "success",
  "message": "Profile management completed successfully",
  "profile_fetch": {
    "user": "John Doe",
    "status": "Available",
    "profile_picture": "https://example.com/profile-pic.jpg"
  },
  "profile_update": {
    "instance": "my-whatsapp",
    "new_picture": "https://example.com/company-logo.jpg",
    "updated_at": "2024-01-15T14:45:00Z"
  }
}
```

### Bulk Operations with Progress Tracking

**In Claude Desktop, say:**
```
Send an important announcement to a large list of recipients via WhatsApp, tracking progress every 10 messages and adding a 0.5 second delay between messages for rate limiting. Show success and failure counts when complete.
```

**Claude does:**
- Sends messages to all recipients with rate limiting
- Tracks progress and counts successes/failures

**Claude responds:**
```json
{
  "status": "success",
  "message": "Bulk messaging operation completed",
  "operation_details": {
    "total_recipients": 1000,
    "messages_sent": 985,
    "success_count": 985,
    "failed_count": 15,
    "completion_time": "8 minutes 23 seconds",
    "rate_limiting": "0.5 seconds between messages"
  },
  "progress_updates": [
    "Progress: 10/1000 (1.0%) - Success: 10, Failed: 0",
    "Progress: 20/1000 (2.0%) - Success: 20, Failed: 0",
    "Progress: 100/1000 (10.0%) - Success: 100, Failed: 0"
  ],
  "final_result": "Complete! Success: 985, Failed: 15"
}
```

## Troubleshooting

### Common Issues

1. **"Instance not found"**
   - List instances to verify name
   - Check instance hasn't been deleted
   - Verify spelling of instance name

2. **"Connection not established"**
   - Check instance status by asking Claude to show the status of your instance
   - Restart instance if needed
   - For WhatsApp, rescan QR code

3. **"Message delivery failed"**
   - Check recipient number format (+country code)
   - Verify instance is connected
   - Review trace details for specific error

4. **"Rate limit exceeded"**
   - Add delays between messages
   - Reduce sending frequency
   - Contact OMNI support for limit increase

5. **"Media upload failed"**
   - Verify media URL is accessible
   - Check file size limits
   - Ensure media type is supported

## Performance Tips

1. **Use Default Instance**: Set default to avoid specifying instance_name repeatedly
2. **Batch Traces**: Fetch traces in batches with pagination
3. **Filter Analytics**: Use date ranges to limit analytics queries
4. **Cleanup Regularly**: Delete old traces to improve performance
5. **Connection Pooling**: Reuse instances instead of creating new ones

## Security Considerations

- **API Key Protection**: Store securely, never expose in code
- **Phone Number Privacy**: Anonymize when logging
- **Media URLs**: Use secure HTTPS URLs only
- **Webhook Security**: Validate webhook signatures
- **Access Control**: Implement proper authentication
- **Audit Logs**: Monitor all messaging activity

## Next Steps

1. **Webhook Integration**: Set up webhooks for incoming messages
2. **Chatbot Development**: Build automated response systems
3. **Analytics Dashboard**: Create visualization for metrics
4. **Multi-Tenant Setup**: Configure separate instances per client
5. **Integration**: Connect OMNI with your CRM/support systems

## Additional Resources

- [OMNI API Documentation](https://docs.automagik.ai/omni)
- [WhatsApp Business API](https://developers.facebook.com/docs/whatsapp)
- [Slack API](https://api.slack.com/)
- [Discord API](https://discord.com/developers/docs)
- [Automagik Tools GitHub](https://github.com/namastexlabs/automagik-tools)
