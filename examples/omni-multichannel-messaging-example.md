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

**Command:**
```python
manage_instances(operation="list")
```

**Expected Response:**
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

**Command:**
```python
manage_instances(
    operation="create",
    config={
        "name": "business-whatsapp",
        "channel_type": "whatsapp",
        "auto_qr": True,
        "webhook_url": "https://example.com/webhook"
    }
)
```

**Expected Response:**
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

**Command:**
```python
send_message(
    message_type="text",
    phone="+1234567890",
    message="Hello! Thank you for contacting our support team. How can we help you today?",
    instance_name="my-whatsapp"
)
```

**Expected Response:**
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

**Command:**
```python
send_message(
    message_type="media",
    phone="+1234567890",
    media_url="https://example.com/product-image.jpg",
    media_type="image",
    caption="Check out our new product! 🎉 Available now with 20% off.",
    instance_name="my-whatsapp"
)
```

**Expected Response:**
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

**Command:**
```python
manage_traces(
    operation="list",
    instance_name="my-whatsapp",
    limit=10
)
```

**Expected Response:**
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

**Command:**
```python
manage_traces(
    operation="analytics",
    instance_name="my-whatsapp",
    start_date="2024-01-01",
    end_date="2024-01-15"
)
```

**Expected Response:**
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

```python
# Setup instances for different channels
channels = [
    {"name": "support-whatsapp", "type": "whatsapp"},
    {"name": "support-slack", "type": "slack"},
    {"name": "support-discord", "type": "discord"}
]

# Check all instances are connected
instances = manage_instances(operation="list")

for instance in instances['instances']:
    if instance['connection_status'] != 'connected':
        print(f"⚠️ {instance['name']} is not connected!")
        # Restart connection
        manage_instances(
            operation="restart",
            instance_name=instance['name']
        )
    else:
        print(f"✓ {instance['name']} is connected")

# Send welcome message across all channels
welcome_message = "Hello! Welcome to our support. How can we help you today?"

# WhatsApp
send_message(
    message_type="text",
    phone="+1234567890",
    message=welcome_message,
    instance_name="support-whatsapp"
)

# Slack (using phone field for user ID)
send_message(
    message_type="text",
    phone="U12345678",  # Slack user ID
    message=welcome_message,
    instance_name="support-slack"
)

# Discord (using phone field for user ID)
send_message(
    message_type="text",
    phone="987654321098765432",  # Discord user ID
    message=welcome_message,
    instance_name="support-discord"
)
```

### Scenario 2: Automated Marketing Campaign

```python
# Send promotional campaign to customer list
customers = [
    {"phone": "+1234567890", "name": "John Doe", "channel": "whatsapp"},
    {"phone": "+0987654321", "name": "Jane Smith", "channel": "whatsapp"},
    # ... more customers
]

campaign_message = """
🎉 Special Offer Just for You!

Hi {name}! 

Get 30% off on all products this weekend only!
Use code: WEEKEND30

Shop now: https://example.com/shop

Valid until Sunday midnight.
"""

# Send personalized messages
for customer in customers:
    personalized_message = campaign_message.format(name=customer['name'])
    
    result = send_message(
        message_type="text",
        phone=customer['phone'],
        message=personalized_message,
        instance_name=f"marketing-{customer['channel']}"
    )
    
    print(f"Sent to {customer['name']}: {result['status']}")
    
    # Add delay to avoid rate limiting
    import time
    time.sleep(1)

# Track campaign performance
analytics = manage_traces(
    operation="analytics",
    instance_name="marketing-whatsapp",
    start_date="2024-01-15",
    end_date="2024-01-17"
)

print(f"\nCampaign Results:")
print(f"Messages sent: {analytics['analytics']['total_messages']}")
print(f"Delivery rate: {analytics['analytics']['success_rate']}")
print(f"Read rate: {analytics['analytics']['delivery_stats']['read'] / analytics['analytics']['total_messages'] * 100:.1f}%")
```

### Scenario 3: Order Notifications with Media

```python
# Send order confirmation with product images
orders = [
    {
        "order_id": "ORD-12345",
        "customer_phone": "+1234567890",
        "product_image": "https://example.com/products/widget-pro.jpg",
        "total": "$99.99"
    }
]

for order in orders:
    # Send product image with order details
    send_message(
        message_type="media",
        phone=order['customer_phone'],
        media_url=order['product_image'],
        media_type="image",
        caption=f"""
✅ Order Confirmed!

Order ID: {order['order_id']}
Total: {order['total']}

Your order will be delivered in 3-5 business days.
Track your order: https://example.com/track/{order['order_id']}

Thank you for shopping with us!
        """,
        instance_name="orders-whatsapp"
    )
    
    # Send follow-up text with contact info
    send_message(
        message_type="contact",
        phone=order['customer_phone'],
        contacts=[
            {
                "full_name": "Customer Support",
                "phone_number": "+1-800-SUPPORT",
                "email": "support@example.com"
            }
        ],
        instance_name="orders-whatsapp"
    )
```

### Scenario 4: Trace Debugging and Monitoring

```python
# Monitor failed messages
failed_traces = manage_traces(
    operation="list",
    instance_name="my-whatsapp",
    trace_status="failed",
    limit=50
)

print(f"Failed messages: {failed_traces['total_count']}")

for trace in failed_traces['traces']:
    print(f"\n❌ Failed Message:")
    print(f"   Trace ID: {trace['trace_id']}")
    print(f"   Recipient: {trace['recipient']}")
    print(f"   Type: {trace['message_type']}")
    print(f"   Sent at: {trace['sent_at']}")
    
    # Get detailed payload for debugging
    payload = manage_traces(
        operation="get_payloads",
        trace_id=trace['trace_id']
    )
    
    print(f"   Error: {payload['error_message']}")
    print(f"   Retry count: {payload['retry_count']}")

# Get traces for specific phone number
customer_traces = manage_traces(
    operation="by_phone",
    phone="+1234567890"
)

print(f"\nMessages to +1234567890: {customer_traces['total_count']}")
print(f"Last message: {customer_traces['traces'][0]['sent_at']}")
```

### Scenario 5: Instance Management and QR Code Setup

```python
# Create new WhatsApp instance
new_instance = manage_instances(
    operation="create",
    config={
        "name": "sales-whatsapp",
        "channel_type": "whatsapp",
        "auto_qr": True
    }
)

print(f"Instance created: {new_instance['instance']['name']}")
print(f"Status: {new_instance['instance']['connection_status']}")

# Get QR code for scanning
qr_result = manage_instances(
    operation="qr",
    instance_name="sales-whatsapp"
)

print(f"\nQR Code available at: {qr_result['qr_code']}")
print(f"Expires at: {qr_result['qr_expires_at']}")
print("Please scan with WhatsApp mobile app")

# Poll for connection status
import time
max_attempts = 30
for attempt in range(max_attempts):
    status = manage_instances(
        operation="status",
        instance_name="sales-whatsapp"
    )
    
    if status['connection_status'] == 'connected':
        print(f"\n✓ Connected! Phone: {status['phone_number']}")
        break
    
    print(f"Waiting for connection... ({attempt + 1}/{max_attempts})")
    time.sleep(10)

# Set as default instance
manage_instances(
    operation="set_default",
    instance_name="sales-whatsapp"
)
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
```python
send_message(message_type="text", phone="+1234567890", message="Hello!")
```

### Media Messages (Images, Videos, Documents)
```python
send_message(
    message_type="media",
    phone="+1234567890",
    media_url="https://example.com/image.jpg",
    media_type="image",
    caption="Check this out!"
)
```

### Audio Messages
```python
send_message(
    message_type="audio",
    phone="+1234567890",
    audio_url="https://example.com/voice.mp3"
)
```

### Stickers
```python
send_message(
    message_type="sticker",
    phone="+1234567890",
    sticker_url="https://example.com/sticker.webp"
)
```

### Contact Cards
```python
send_message(
    message_type="contact",
    phone="+1234567890",
    contacts=[{"full_name": "John Doe", "phone_number": "+1234567890"}]
)
```

### Reactions
```python
send_message(
    message_type="reaction",
    phone="+1234567890",
    message_id="msg_123",
    emoji="👍"
)
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

```python
# Preview cleanup (dry run)
cleanup_preview = manage_traces(
    operation="cleanup",
    days_old=30,
    dry_run=True
)

print(f"Traces to be deleted: {cleanup_preview['traces_to_delete']}")
print(f"Space to be freed: {cleanup_preview['space_freed']}")

# Confirm and execute cleanup
if cleanup_preview['traces_to_delete'] > 0:
    cleanup_result = manage_traces(
        operation="cleanup",
        days_old=30,
        dry_run=False
    )
    print(f"Deleted {cleanup_result['deleted_count']} traces")
```

### Profile Management

```python
# Fetch user profile
profile = manage_profiles(
    operation="fetch",
    phone_number="+1234567890",
    instance_name="my-whatsapp"
)

print(f"User: {profile['name']}")
print(f"Status: {profile['status']}")
print(f"Profile picture: {profile['profile_picture_url']}")

# Update instance profile picture
manage_profiles(
    operation="update_picture",
    picture_url="https://example.com/company-logo.jpg",
    instance_name="my-whatsapp"
)
```

### Bulk Operations with Progress Tracking

```python
# Send to large recipient list with progress tracking
recipients = [...]  # Large list of phone numbers

total = len(recipients)
success_count = 0
failed_count = 0

for i, phone in enumerate(recipients, 1):
    try:
        result = send_message(
            message_type="text",
            phone=phone,
            message="Important announcement..."
        )
        
        if result['status'] == 'success':
            success_count += 1
        else:
            failed_count += 1
            
    except Exception as e:
        failed_count += 1
        print(f"Error sending to {phone}: {e}")
    
    # Progress update every 10 messages
    if i % 10 == 0:
        print(f"Progress: {i}/{total} ({i/total*100:.1f}%) - Success: {success_count}, Failed: {failed_count}")
    
    time.sleep(0.5)  # Rate limiting

print(f"\nComplete! Success: {success_count}, Failed: {failed_count}")
```

## Troubleshooting

### Common Issues

1. **"Instance not found"**
   - List instances to verify name
   - Check instance hasn't been deleted
   - Verify spelling of instance name

2. **"Connection not established"**
   - Check instance status with `manage_instances(operation="status")`
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
