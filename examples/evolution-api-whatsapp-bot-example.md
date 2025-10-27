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

**What to say to Claude:**
```
Send a WhatsApp message to +1234567890: "Hello! Welcome to our customer support. How can I help you today?"
```

**Expected Response from Claude:**
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

**What to say to Claude:**
```
Send a WhatsApp document to +1234567890 with the file from https://example.com/product-catalog.pdf, caption: "Here's our latest product catalog! 📋", and filename: "Product_Catalog_2024.pdf"
```

**Expected Response from Claude:**
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

**What to say to Claude:**
```
Send a WhatsApp location to +1234567890: latitude 37.7749, longitude -122.4194, name "Our Main Store", address "123 Market St, San Francisco, CA 94103"
```

**Expected Response from Claude:**
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

**What to say to Claude:**
```
Send a WhatsApp contact card to +1234567890 for John Support, phone +1234567890, organization "Customer Support Team", email support@example.com
```

**Expected Response from Claude:**
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

**What to say to Claude:**
```
First show typing indicator to +1234567890, wait 2 seconds, then send: "Hi! 👋 I'm your support assistant. I can help you with:

1. Order tracking
2. Product information
3. Technical support
4. Store locations

What would you like help with?" to +1234567890
```

**What Claude does:**
- Shows typing indicator to +1234567890
- Waits 2 seconds
- Sends the welcome message

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
      "conversation": "Hi! 👋 I'm your support assistant..."
    }
  }
}
```

### Scenario 2: Order Confirmation with Invoice

**What to say to Claude:**
```
Send a WhatsApp document to +1234567890 with the invoice from https://example.com/invoices/INV-12345.pdf, caption: "✅ Order #12345 confirmed!

Total: $99.99
Estimated delivery: 3-5 business days

Your invoice is attached. Thank you for your order!", and filename: "Invoice_12345.pdf"
```

**What Claude does:**
- Sends the invoice document with the specified caption

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
        "caption": "✅ Order #12345 confirmed!\n\nTotal: $99.99\nEstimated delivery: 3-5 business days\n\nYour invoice is attached. Thank you for your order!"
      }
    }
  }
}
```

### Scenario 3: Store Location Sharing

**What to say to Claude:**
```
First, send a WhatsApp location to +1234567890: latitude 40.7128, longitude -74.0060, name "Downtown Store", address "456 Broadway, New York, NY 10013"

Then send: "📍 Our downtown store is open:

Mon-Fri: 9 AM - 8 PM
Sat-Sun: 10 AM - 6 PM

See you soon!" to +1234567890
```

**What Claude does:**
- Shares the store location
- Follows up with store hours

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
        "degreesLatitude": 40.7128,
        "degreesLongitude": -74.0060,
        "name": "Downtown Store",
        "address": "456 Broadway, New York, NY 10013"
      }
    }
  }
}
```

### Scenario 4: React to Customer Messages

**What to say to Claude:**
```
React to the customer's message with a thumbs up emoji
```

**What Claude does:**
- Adds a thumbs up reaction to the customer's message

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
      "reactionMessage": {
        "key": {
          "remoteJid": "1234567890@s.whatsapp.net",
          "fromMe": false,
          "id": "3EB0XXXXX"
        },
        "text": "👍"
      }
    }
  }
}
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

1. **Use Typing Indicators**: Make conversations feel natural by asking Claude to show typing indicators
2. **Add Delays**: Ask Claude to add delays between messages to space them out
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
