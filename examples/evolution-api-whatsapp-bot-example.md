# Evolution API WhatsApp Bot Example

This example demonstrates how to use automagik-tools to create a complete WhatsApp bot using Evolution API v2 for automated customer support and notifications.

## Use Case Description

Build an intelligent WhatsApp bot that can:
- Send automated welcome messages to new customers
- Handle customer inquiries with typing indicators
- Send media (images, documents, videos) with captions
- Share location information for store addresses
- Send contact cards for support team members
- React to customer messages with emojis
- Send voice notes for personalized responses

Perfect for customer support, marketing campaigns, order notifications, and automated engagement.

## Setup

### Prerequisites

1. **Evolution API Instance**: Running Evolution API v2 server
2. **WhatsApp Business Account**: Connected to Evolution API
3. **API Credentials**: Evolution API key and instance name

### Environment Configuration

Create a `.env` file or set environment variables:

```bash
# Required
EVOLUTION_API_BASE_URL=http://localhost:18080
EVOLUTION_API_KEY=your-evolution-api-key
EVOLUTION_API_INSTANCE=my-whatsapp-bot

# Optional
EVOLUTION_API_TIMEOUT=30
EVOLUTION_API_MAX_RETRIES=3
EVOLUTION_API_FIXED_RECIPIENT=+1234567890  # For testing/security
```

## CLI Commands

### Direct Command Line Usage

```bash
# Run with stdio transport (for Claude/Cursor)
uvx automagik-tools tool evolution-api --transport stdio

# Run with SSE transport (for web interfaces)
uvx automagik-tools tool evolution-api --transport sse --port 8000

# Run with HTTP transport
uvx automagik-tools tool evolution-api --transport http --port 8001
```

### Test Connection

```bash
# Check if Evolution API is accessible
curl http://localhost:18080/instance/connectionState/my-whatsapp-bot \
  -H "apikey: your-evolution-api-key"
```

## MCP Configuration

### For Claude Desktop

Add this to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "evolution-api": {
      "command": "uvx",
      "args": [
        "automagik-tools",
        "tool",
        "evolution-api",
        "--transport",
        "stdio"
      ],
      "env": {
        "EVOLUTION_API_BASE_URL": "http://localhost:18080",
        "EVOLUTION_API_KEY": "your-evolution-api-key",
        "EVOLUTION_API_INSTANCE": "my-whatsapp-bot",
        "EVOLUTION_API_TIMEOUT": "30"
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
    "evolution-api": {
      "command": "uvx",
      "args": [
        "automagik-tools",
        "tool",
        "evolution-api",
        "--transport",
        "stdio"
      ],
      "env": {
        "EVOLUTION_API_BASE_URL": "http://localhost:18080",
        "EVOLUTION_API_KEY": "your-evolution-api-key",
        "EVOLUTION_API_INSTANCE": "my-whatsapp-bot"
      }
    }
  }
}
```

## Expected Output

### 1. Sending a Text Message

**Command:**
```python
send_text_message(
    instance="my-whatsapp-bot",
    message="Hello! Welcome to our customer support. How can I help you today?",
    number="+1234567890",
    delay=1000,
    linkPreview=True
)
```

**Expected Response:**
```json
{
  "status": "success",
  "result": {
    "key": {
      "remoteJid": "1234567890@s.whatsapp.net",
      "fromMe": true,
      "id": "3EB0XXXXX"
    },
    "message": {
      "conversation": "Hello! Welcome to our customer support..."
    },
    "messageTimestamp": "1234567890"
  },
  "instance": "my-whatsapp-bot",
  "number": "+1234567890",
  "message_preview": "Hello! Welcome to our customer support. How..."
}
```

### 2. Sending Media with Caption

**Command:**
```python
send_media(
    instance="my-whatsapp-bot",
    media="https://example.com/product-catalog.pdf",
    mediatype="document",
    mimetype="application/pdf",
    number="+1234567890",
    caption="Here's our latest product catalog! 📋",
    fileName="Product_Catalog_2024.pdf"
)
```

**Expected Response:**
```json
{
  "status": "success",
  "result": {
    "key": {
      "remoteJid": "1234567890@s.whatsapp.net",
      "fromMe": true,
      "id": "3EB0XXXXX"
    },
    "message": {
      "documentMessage": {
        "url": "...",
        "mimetype": "application/pdf",
        "caption": "Here's our latest product catalog! 📋"
      }
    }
  },
  "instance": "my-whatsapp-bot",
  "number": "+1234567890",
  "mediatype": "document",
  "caption": "Here's our latest product catalog! 📋"
}
```

### 3. Sending Location

**Command:**
```python
send_location(
    instance="my-whatsapp-bot",
    latitude=37.7749,
    longitude=-122.4194,
    number="+1234567890",
    name="Our Main Store",
    address="123 Market St, San Francisco, CA 94103"
)
```

**Expected Response:**
```json
{
  "status": "success",
  "result": {
    "key": {
      "remoteJid": "1234567890@s.whatsapp.net",
      "fromMe": true,
      "id": "3EB0XXXXX"
    },
    "message": {
      "locationMessage": {
        "degreesLatitude": 37.7749,
        "degreesLongitude": -122.4194,
        "name": "Our Main Store",
        "address": "123 Market St, San Francisco, CA 94103"
      }
    }
  },
  "instance": "my-whatsapp-bot",
  "number": "+1234567890",
  "coordinates": "37.7749, -122.4194",
  "name": "Our Main Store"
}
```

### 4. Sending Contact Card

**Command:**
```python
send_contact(
    instance="my-whatsapp-bot",
    contact=[
        {
            "fullName": "John Support",
            "wuid": "1234567890",
            "phoneNumber": "+1234567890",
            "organization": "Customer Support Team",
            "email": "support@example.com"
        }
    ],
    number="+1234567890"
)
```

**Expected Response:**
```json
{
  "status": "success",
  "result": {
    "key": {
      "remoteJid": "1234567890@s.whatsapp.net",
      "fromMe": true,
      "id": "3EB0XXXXX"
    },
    "message": {
      "contactMessage": {
        "displayName": "John Support",
        "vcard": "BEGIN:VCARD..."
      }
    }
  },
  "instance": "my-whatsapp-bot",
  "number": "+1234567890",
  "contacts_count": 1
}
```

## Real-World Usage Scenarios

### Scenario 1: Customer Support Bot

```python
# Step 1: Send typing indicator
send_presence(
    instance="my-whatsapp-bot",
    number="+1234567890",
    presence="composing",
    delay=2000
)

# Step 2: Send welcome message
send_text_message(
    instance="my-whatsapp-bot",
    message="Hi! 👋 I'm your support assistant. I can help you with:\n\n1. Order tracking\n2. Product information\n3. Technical support\n4. Store locations\n\nWhat would you like help with?",
    number="+1234567890"
)
```

### Scenario 2: Order Confirmation with Invoice

```python
# Send order confirmation with invoice document
send_media(
    instance="my-whatsapp-bot",
    media="https://example.com/invoices/INV-12345.pdf",
    mediatype="document",
    mimetype="application/pdf",
    number="+1234567890",
    caption="✅ Order #12345 confirmed!\n\nTotal: $99.99\nEstimated delivery: 3-5 business days\n\nYour invoice is attached. Thank you for your order!",
    fileName="Invoice_12345.pdf"
)
```

### Scenario 3: Store Location Sharing

```python
# Share store location with customer
send_location(
    instance="my-whatsapp-bot",
    latitude=40.7128,
    longitude=-74.0060,
    number="+1234567890",
    name="Downtown Store",
    address="456 Broadway, New York, NY 10013"
)

# Follow up with store hours
send_text_message(
    instance="my-whatsapp-bot",
    message="📍 Our downtown store is open:\n\nMon-Fri: 9 AM - 8 PM\nSat-Sun: 10 AM - 6 PM\n\nSee you soon!",
    number="+1234567890"
)
```

### Scenario 4: React to Customer Messages

```python
# React with thumbs up to acknowledge message
send_reaction(
    instance="my-whatsapp-bot",
    remote_jid="1234567890@s.whatsapp.net",
    from_me=False,
    message_id="3EB0XXXXX",
    reaction="👍"
)
```

## Features Demonstrated

1. **Auto-Typing Indicators**: Messages automatically show typing before sending
2. **Media Support**: Send images, videos, documents, and audio
3. **Rich Messaging**: Locations, contacts, reactions, and emojis
4. **Delay Control**: Control message timing for natural conversation flow
5. **Link Previews**: Automatic preview generation for URLs
6. **Mentions**: Tag users in group messages
7. **Fixed Recipient Mode**: Security feature for controlled environments

## Best Practices

1. **Use Typing Indicators**: Make conversations feel natural with `send_presence()`
2. **Add Delays**: Use the `delay` parameter to space out messages
3. **Rich Media**: Use appropriate media types (image, video, document)
4. **Clear Captions**: Always add descriptive captions to media
5. **Error Handling**: Check response status before proceeding
6. **Rate Limiting**: Don't spam - respect WhatsApp's rate limits
7. **Testing**: Use `EVOLUTION_API_FIXED_RECIPIENT` for safe testing

## Troubleshooting

### Common Issues

1. **"Evolution API client not configured"**
   - Ensure `EVOLUTION_API_KEY` is set
   - Verify `EVOLUTION_API_BASE_URL` is correct

2. **"No recipient number provided"**
   - Set `EVOLUTION_API_FIXED_RECIPIENT` or provide `number` parameter

3. **Connection timeout**
   - Check Evolution API server is running
   - Verify network connectivity
   - Increase `EVOLUTION_API_TIMEOUT`

4. **Message not delivered**
   - Verify WhatsApp instance is connected
   - Check recipient number format (+country code)
   - Ensure instance has active WhatsApp session

## Security Considerations

- **API Key Protection**: Never expose API keys in code or logs
- **Fixed Recipient Mode**: Use for testing to prevent accidental messages
- **Rate Limiting**: Implement delays to avoid being blocked
- **Webhook Security**: Validate webhook signatures if using webhooks
- **Data Privacy**: Follow WhatsApp's privacy policies and GDPR

## Next Steps

1. **Implement Webhooks**: Receive incoming messages and events
2. **Add Message Queue**: Handle high-volume messaging
3. **Create Templates**: Design reusable message templates
4. **Build Flows**: Create conversation flows with state management
5. **Analytics**: Track message delivery and engagement rates

## Additional Resources

- [Evolution API Documentation](https://doc.evolution-api.com/)
- [WhatsApp Business API Guidelines](https://developers.facebook.com/docs/whatsapp)
- [Automagik Tools GitHub](https://github.com/namastexlabs/automagik-tools)
