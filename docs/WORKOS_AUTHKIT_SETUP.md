# WorkOS AuthKit Setup Guide

This guide walks you through setting up WorkOS AuthKit with the Automagik Tools Hub using FastMCP's native integration.

## Prerequisites

1. A **[WorkOS Account](https://workos.com/)** (free tier available)
2. The Automagik Tools Hub installed (`uv install` or `uvx automagik-tools`)
3. Your Hub's URL (e.g., `http://localhost:8884` for development)

## Step 1: Create WorkOS Project

1. Go to **[WorkOS Dashboard](https://dashboard.workos.com/)**
2. Click **"Create New Project"**
3. Name your project (e.g., "Automagik Tools Hub")
4. Click **"Create Project"**

## Step 2: Enable AuthKit

1. In your project dashboard, navigate to **"Authentication" → "AuthKit"**
2. Click **"Enable AuthKit"**
3. Configure your AuthKit settings:
   - **Display Name**: "Automagik Tools Hub"
   - **Logo URL**: (optional)
   - **Primary Color**: (optional)

## Step 3: Configure Dynamic Client Registration

<Accordion title="Why Dynamic Client Registration?">
FastMCP uses Dynamic Client Registration (DCR) to automatically register MCP clients with your AuthKit instance. This allows any MCP client (like Claude Desktop, Cline, etc.) to authenticate without manual OAuth app setup.
</Accordion>

1. Navigate to **"Applications" → "Configuration"**
2. Enable **"Dynamic Client Registration"**
3. Save settings

![Enable DCR](https://mintcdn.com/fastmcp/hUosZw7ujHZFemrG/integrations/images/authkit/enable_dcr.png)

## Step 4: Get Your AuthKit Domain

1. In the AuthKit configuration page, find your **AuthKit Domain**
2. It will look like: `https://your-project-12345.authkit.app`
3. Copy this domain - you'll need it for configuration

## Step 5: Configure Hub Environment

You have two options for configuration:

### Option A: Environment Variables (Recommended for Development)

Set these environment variables:

```bash
export WORKOS_AUTHKIT_DOMAIN=https://your-project-12345.authkit.app
export HUB_BASE_URL=http://localhost:8884  # Change for production
```

### Option B: .env File (Not Recommended - Zero Config Goal)

Create a `.env` file (only if necessary):

```bash
# AuthKit (WorkOS) - FastMCP Native Integration
WORKOS_AUTHKIT_DOMAIN=https://your-project-12345.authkit.app
HUB_BASE_URL=http://localhost:8884

# Optional: Required OAuth scopes (comma-separated)
# FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_REQUIRED_SCOPES=openid,profile,email
```

### Option C: CLI Flags (Best - Zero Config)

```bash
uvx automagik-tools hub \
  --env WORKOS_AUTHKIT_DOMAIN=https://your-project-12345.authkit.app \
  --env HUB_BASE_URL=http://localhost:8884
```

## Step 6: Start the Hub

### Development Mode

```bash
# Using CLI flags (zero-config)
uvx automagik-tools hub \
  --env WORKOS_AUTHKIT_DOMAIN=https://your-project-12345.authkit.app \
  --env HUB_BASE_URL=http://localhost:8884 \
  --port 8884 \
  --reload
```

### Production Mode

```bash
# Using environment variables
uvx automagik-tools hub --port 8884
```

You should see:

```
🚀 Initializing Hub...
📅 Importing Google Calendar tools...
✅ Hub ready!
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8884
```

## Step 7: Test Authentication

### Test with FastMCP Client

Create a test script `test_auth.py`:

```python
from fastmcp import Client
import asyncio

async def main():
    async with Client("http://localhost:8884/mcp", auth="oauth") as client:
        # This will trigger OAuth flow in your browser
        assert await client.ping()
        print("✅ Authentication successful!")

        # Test a tool
        tools = await client.list_tools()
        print(f"📦 Available tools: {len(tools)}")

if __name__ == "__main__":
    asyncio.run(main())
```

Run the test:

```bash
uv run python test_auth.py
```

### Test with MCP Client (Claude Desktop, etc.)

Add to your MCP client configuration (e.g., `claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "automagik-hub": {
      "command": "uvx",
      "args": [
        "automagik-tools",
        "hub",
        "--env", "WORKOS_AUTHKIT_DOMAIN=https://your-project-12345.authkit.app",
        "--env", "HUB_BASE_URL=http://localhost:8884",
        "--port", "8884"
      ]
    }
  }
}
```

## Step 8: Verify Database

Check that users are being created:

```bash
# Open SQLite database
sqlite3 hub_data/hub.db

# List users
SELECT email, oauth_provider, created_at FROM users;

# Exit
.quit
```

## How FastMCP AuthKit Works

FastMCP's `AuthKitProvider` automatically handles:

1. **OAuth Flow**: Redirects users to AuthKit for login
2. **Token Validation**: Validates JWT tokens from AuthKit
3. **User Injection**: Injects `user_id` into `Context` for all tools
4. **Session Management**: Handles token refresh and expiration

### User Context in Tools

Every authenticated tool call receives user context:

```python
@hub.tool()
async def add_tool(tool_name: str, config: Dict[str, Any], ctx: Context) -> str:
    # User ID is automatically available
    user_id = ctx.get_state("user_id")

    # Your tool logic here...
    await db.add_user_tool(user_id, tool_name, config)
```

## Troubleshooting

### Error: "WORKOS_AUTHKIT_DOMAIN not set"

**Solution**: Set the environment variable or use CLI flags:

```bash
uvx automagik-tools hub \
  --env WORKOS_AUTHKIT_DOMAIN=https://your-project-12345.authkit.app
```

### Error: "Dynamic Client Registration not enabled"

**Solution**:
1. Go to WorkOS Dashboard → Applications → Configuration
2. Enable "Dynamic Client Registration"
3. Restart the Hub

### OAuth Flow Opens Browser But Fails

**Solution**: Check that `HUB_BASE_URL` matches your actual server URL:

```bash
# Development (localhost)
--env HUB_BASE_URL=http://localhost:8884

# Production (public URL)
--env HUB_BASE_URL=https://hub.yourdomain.com
```

### Users Not Appearing in Database

**Solution**: Check database initialization:

```bash
# View Hub logs for database initialization
# You should see: "🚀 Initializing Hub..."

# Manually initialize database
uv run alembic upgrade head
```

## Production Deployment

### Environment Variables for Production

```bash
# Required
export WORKOS_AUTHKIT_DOMAIN=https://your-project-12345.authkit.app
export HUB_BASE_URL=https://hub.yourdomain.com

# Optional (with defaults)
export HUB_HOST=0.0.0.0
export HUB_PORT=8884
export HUB_DATABASE_PATH=/var/lib/automagik-hub/hub.db
```

### HTTPS Configuration

For production, you MUST use HTTPS. Options:

1. **Reverse Proxy** (Recommended)
   - Use Nginx/Caddy in front of Hub
   - Let reverse proxy handle SSL/TLS
   - Hub listens on localhost:8884

2. **Cloud Deployment**
   - Deploy on Fly.io, Railway, etc.
   - Use their built-in SSL/TLS

### Security Checklist

- [ ] Enable HTTPS (required for OAuth)
- [ ] Set `HUB_BASE_URL` to your public HTTPS URL
- [ ] Restrict `HUB_HOST` to `127.0.0.1` if using reverse proxy
- [ ] Enable Dynamic Client Registration in WorkOS
- [ ] Review OAuth scopes (minimal permissions)
- [ ] Set up database backups
- [ ] Monitor authentication logs

## Next Steps

1. **Add Tools**: Use `add_tool()` to activate tools for your account
2. **Configure OAuth**: Set up Google OAuth for Google Workspace tools
3. **Invite Users**: Share Hub URL with team members
4. **Monitor Usage**: Check database for user activity

## Resources

- [WorkOS Dashboard](https://dashboard.workos.com/)
- [AuthKit Documentation](https://workos.com/docs/authkit)
- [FastMCP AuthKit Guide](https://docs.fastmcp.com/integrations/authkit)
- [Automagik Tools Documentation](../README.md)
