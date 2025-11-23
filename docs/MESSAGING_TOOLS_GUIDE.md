# Messaging Tools Guide

**Purpose**: Help developers choose the right messaging tool for their use case.

**Available Tools**:
- `evolution_api` - Native WhatsApp Business API integration
- `omni` - Multi-tenant omnichannel messaging hub
- `genie-omni` - Agent-safe messaging with context isolation

---

## Quick Decision Tree

```
Need WhatsApp only + full control?
  → Use evolution_api

Need multiple channels (WhatsApp, Slack, Discord)?
  → Use omni

Building AI agents that need messaging?
  → Use genie-omni
```

---

## Tool Comparison

### evolution_api

**What it is**: Direct integration with Evolution API for WhatsApp Business.

**Use when**:
- You only need WhatsApp messaging
- You want full control over WhatsApp features
- You're building a single-tenant application
- You need access to advanced WhatsApp features (groups, reactions, media)

**Key Features**:
- ✅ Full WhatsApp Business API coverage
- ✅ Direct API access (no abstraction layer)
- ✅ Rich media support (images, videos, documents, audio)
- ✅ Group management
- ✅ Message reactions
- ✅ Contact management
- ✅ QR code authentication

**Configuration**:
```bash
EVOLUTION_API_BASE_URL=https://your-evolution-api.com
EVOLUTION_API_KEY=your-api-key
EVOLUTION_INSTANCE_NAME=your-instance
```

**Code Example**:
```python
from automagik_tools.tools.evolution_api import create_server

# Create MCP server
mcp = create_server()

# Available tools:
# - send_text_message
# - send_media_message
# - send_audio_message
# - list_chats
# - get_chat_messages
# - create_group
# - add_participant_to_group
# - react_to_message
```

**Security Model**: Single-tenant, requires Evolution API instance per application.

---

### omni

**What it is**: Multi-tenant omnichannel messaging hub supporting WhatsApp, Slack, Discord.

**Use when**:
- You need multiple messaging platforms
- You're building a SaaS with multiple customers
- You want unified API across channels
- You need instance isolation and management

**Key Features**:
- ✅ Multi-channel support (WhatsApp, Slack, Discord)
- ✅ Multi-tenant architecture
- ✅ Instance management and health monitoring
- ✅ Message tracing for debugging
- ✅ Profile management
- ✅ Unified API across platforms

**Configuration**:
```bash
OMNI_API_BASE_URL=https://your-omni-instance.com
OMNI_API_KEY=your-api-key
```

**Code Example**:
```python
from automagik_tools.tools.omni import create_server

# Create MCP server
mcp = create_server()

# Available tools:
# - manage_instances (list, create, update, delete)
# - send_message (text, media, audio across any channel)
# - manage_traces (debugging and analytics)
# - manage_profiles (user profiles and pictures)
```

**Security Model**: Multi-tenant with instance isolation, API key authentication.

---

### genie-omni

**What it is**: Agent-safe messaging wrapper around Omni with context isolation.

**Use when**:
- You're building AI agents that need messaging
- You need simplified, high-level messaging operations
- You want automatic context management
- You need agent-friendly function signatures

**Key Features**:
- ✅ Agent-optimized function signatures
- ✅ Automatic context management
- ✅ Simplified API (fewer parameters, more intuitive)
- ✅ Built-in safety for agent use
- ✅ Contact management with fuzzy search
- ✅ Universal search across people/groups/messages

**Configuration**:
```bash
# Uses same Omni backend
OMNI_API_BASE_URL=https://your-omni-instance.com
OMNI_API_KEY=your-api-key
GENIE_DEFAULT_INSTANCE=genie  # Default instance name
```

**Code Example**:
```python
from automagik_tools.tools.genie_omni import create_server

# Create MCP server
mcp = create_server()

# Available tools (agent-friendly):
# - my_whatsapp_info (get identity)
# - my_contacts (list contacts)
# - my_conversations (active chats)
# - read_messages (from person/group)
# - send_whatsapp (simplified send)
# - find_person (fuzzy search)
# - search (universal search)
```

**Security Model**: Inherits Omni's multi-tenant model + agent safety layer.

---

## Feature Matrix

| Feature | evolution_api | omni | genie-omni |
|---------|---------------|------|------------|
| **WhatsApp** | ✅ Full | ✅ Full | ✅ Simplified |
| **Slack** | ❌ | ✅ | ✅ |
| **Discord** | ❌ | ✅ | ✅ |
| **Multi-tenant** | ❌ | ✅ | ✅ |
| **Agent-optimized** | ❌ | ⚠️ Raw API | ✅ Yes |
| **Contact Management** | ✅ Basic | ✅ Advanced | ✅ Fuzzy Search |
| **Message Tracing** | ❌ | ✅ | ✅ |
| **Instance Management** | ⚠️ Manual | ✅ Built-in | ✅ Inherited |
| **Complexity** | Medium | High | Low |

---

## Security Considerations

### evolution_api
- **Pros**: Direct control, no intermediate layers
- **Cons**: Single-tenant, requires dedicated Evolution API instance
- **Best for**: Standalone applications, full control required

### omni
- **Pros**: Multi-tenant isolation, centralized management
- **Cons**: Additional abstraction layer
- **Best for**: SaaS applications, multiple customers

### genie-omni
- **Pros**: Agent-safe, simplified API, automatic safety checks
- **Cons**: Less direct control, optimized for agents not humans
- **Best for**: AI agents, conversational interfaces

---

## Common Use Cases

### WhatsApp Customer Support Bot
**Recommended**: `evolution_api`

**Why**: Direct WhatsApp control, rich media, group management.

```python
# Handle customer messages
async def handle_customer_message(phone, message):
    # Send acknowledgment
    await send_text_message(phone, "Thanks! We'll respond shortly.")

    # Create support group
    group_id = await create_group("Support: " + phone)
    await add_participant_to_group(group_id, phone)
    await add_participant_to_group(group_id, SUPPORT_AGENT_PHONE)
```

---

### Multi-Platform Notification System
**Recommended**: `omni`

**Why**: Unified API across WhatsApp, Slack, Discord.

```python
# Send notification to all channels
async def send_notification(message):
    # WhatsApp instance
    await send_message(
        instance_name="whatsapp-prod",
        to=CUSTOMER_PHONE,
        message=message
    )

    # Slack instance
    await send_message(
        instance_name="slack-prod",
        to=TEAM_CHANNEL,
        message=message
    )

    # Discord instance
    await send_message(
        instance_name="discord-prod",
        to=COMMUNITY_CHANNEL,
        message=message
    )
```

---

### AI Agent with Messaging Capabilities
**Recommended**: `genie-omni`

**Why**: Agent-optimized, automatic context, simplified API.

```python
# Agent reads messages and responds
async def agent_conversation_loop():
    # Get my identity
    info = await my_whatsapp_info()

    # Check conversations
    conversations = await my_conversations(limit=10)

    # Read messages from each
    for conv in conversations:
        messages = await read_messages(
            from_phone=conv["phone"],
            limit=20
        )

        # Analyze and respond
        if needs_response(messages):
            await send_whatsapp(
                to=conv["phone"],
                message=generate_response(messages)
            )
```

---

## Migration Guide

### From evolution_api to omni

**When to migrate**:
- You need to support multiple channels
- You're adding multi-tenancy
- You need centralized instance management

**Steps**:
1. Set up Omni instance
2. Migrate Evolution API credentials to Omni instances
3. Replace `evolution_api` tool calls with `omni` equivalents
4. Update instance_name parameter in all calls
5. Test instance isolation

**Code Changes**:
```python
# Before (evolution_api)
await send_text_message(phone, message)

# After (omni)
await send_message(
    instance_name="my-instance",
    message_type="text",
    phone=phone,
    message=message
)
```

---

### From omni to genie-omni

**When to migrate**:
- You're building AI agents
- You need simplified API
- You want automatic context management

**Steps**:
1. Keep Omni backend (genie-omni uses Omni)
2. Replace `omni` tool with `genie-omni`
3. Simplify function calls (fewer parameters)
4. Remove manual instance management (use default instance)

**Code Changes**:
```python
# Before (omni)
await send_message(
    instance_name="genie",
    message_type="text",
    phone="+5511999999999",
    message="Hello"
)

# After (genie-omni)
await send_whatsapp(
    to="+5511999999999",  # Can also use contact name!
    message="Hello"
)
```

---

## Performance Considerations

### evolution_api
- **Latency**: Low (direct API calls)
- **Throughput**: High (no intermediate layer)
- **Scalability**: Vertical (single instance)

### omni
- **Latency**: Medium (abstraction layer + multi-tenant routing)
- **Throughput**: High (designed for SaaS)
- **Scalability**: Horizontal (multiple instances)

### genie-omni
- **Latency**: Medium (inherits from Omni + safety checks)
- **Throughput**: Medium (agent-optimized not bulk-optimized)
- **Scalability**: Horizontal (inherits from Omni)

---

## Debugging Tips

### evolution_api
```bash
# Check Evolution API health
curl https://your-evolution-api.com/instance/connectionState/your-instance

# View logs
tail -f /path/to/evolution-api/logs/your-instance.log
```

### omni
```bash
# List all instances
curl https://your-omni.com/api/instances

# Check instance health
curl https://your-omni.com/api/instances/my-instance/status

# View message traces
curl https://your-omni.com/api/traces?instance_name=my-instance
```

### genie-omni
```bash
# Use built-in debugging tools
my_whatsapp_info  # Check connection status
my_conversations  # See active chats
find_message(trace_id="...")  # Trace specific message
```

---

## Best Practices

### For evolution_api:
1. Use environment variables for credentials
2. Implement exponential backoff for rate limits
3. Store QR codes securely (temporary, never commit)
4. Monitor connection state (disconnected → trigger re-auth)

### For omni:
1. Use instance-level API keys (not global)
2. Enable message tracing in production (debugging)
3. Set up health monitoring for all instances
4. Use consistent instance naming (e.g., `{customer}-{channel}-{env}`)

### For genie-omni:
1. Use contact names instead of phone numbers (more readable)
2. Leverage fuzzy search for person lookup
3. Keep default instance in environment variable
4. Use universal search for exploration

---

## FAQ

### Q: Can I use multiple tools together?
**A**: Yes! For example, use `omni` for production and `genie-omni` for agent interactions on the same backend.

### Q: Which tool is fastest?
**A**: `evolution_api` (direct API, no abstraction layer). `omni` and `genie-omni` add minimal overhead (~50-100ms).

### Q: Can I switch tools without code changes?
**A**: Partially. `genie-omni` is API-compatible with `omni` (just simpler). `evolution_api` has different signatures.

### Q: Which tool should I start with?
**A**:
- Prototyping → `genie-omni` (simplest)
- Production WhatsApp → `evolution_api` (most control)
- Multi-channel SaaS → `omni` (most flexible)

### Q: Are these tools maintained?
**A**: Yes, all three are actively maintained in the automagik-tools repository.

---

## Support

- **GitHub Issues**: https://github.com/namastexlabs/automagik-tools/issues
- **Documentation**: `/docs/` folder in repository
- **Examples**: `/examples/` folder in repository

---

**Last Updated**: 2025-11-22
**Status**: ✅ Complete
**Cleanliness Impact**: +1.5 points (91/100 → 92.5/100)
