# OAuth Authentication Guide

## Overview

Automagik Tools uses OAuth 2.1 for secure authentication with Google services. This guide covers everything you need to know about authenticating, troubleshooting, and managing your OAuth sessions.

## 🚀 Quick Start

### 1. Configure OAuth Credentials

Set up your OAuth client credentials using environment variables:

```bash
export GOOGLE_OAUTH_CLIENT_ID='your-client-id.apps.googleusercontent.com'
export GOOGLE_OAUTH_CLIENT_SECRET='GOCSPX-your-client-secret'
export GOOGLE_OAUTH_REDIRECT_URI='http://localhost:8000/oauth2callback'
```

### 2. Authenticate

Call `start_google_auth` with your email:

```python
start_google_auth(
    user_google_email="you@example.com",
    service_name="gmail"
)
```

### 3. Follow the Link

Click the authentication link in your terminal/browser, grant permissions, and you're done!

---

## 🔐 Enhanced OAuth Features

Automagik Tools includes several FastMCP-inspired enhancements for a seamless OAuth experience:

### ✨ Automatic Retry on Stale Credentials

If your token expires or gets revoked, the system automatically:
1. Detects the stale credential error
2. Clears the cached credential
3. Retries the operation
4. Provides clear guidance if retry fails

**No manual intervention needed** in most cases!

### 🎯 User-Friendly Error Messages

Get actionable guidance instead of cryptic errors:

```
🔐 Authentication Error: Token Expired

Message: Your authentication token for gmail has expired.

✅ Action Required:
   Please reauthenticate to continue:

   Call start_google_auth with your email and service name:
     user_email: "you@example.com"
     service_name: "gmail"

   Then follow the browser link to grant permissions.

💡 Example:

   # Reauthenticate
   start_google_auth(
       user_google_email="you@example.com",
       service_name="gmail"
   )

📚 Documentation: https://github.com/namastexlabs/automagik-tools/blob/main/docs/OAUTH_GUIDE.md#token-expired
```

### 🧹 Automatic Session Cleanup

Sessions automatically expire after 24 hours (configurable) to prevent:
- Memory leaks from unlimited session bindings
- Stale sessions accumulating over time
- Security risks from long-lived sessions

Background cleanup runs every hour to remove expired sessions.

### 🔍 Smart Auth Detection

The system automatically detects if authentication is required before making requests, reducing unnecessary auth prompts.

---

## 📖 Common Scenarios

### Scenario 1: First-Time Authentication

```python
# First time authenticating
result = start_google_auth(
    user_google_email="you@example.com",
    service_name="gmail"
)

# Click the link in the output
# Grant permissions in browser
# Done! Token is saved for future use
```

### Scenario 2: Token Expired

```python
# Try to use a service
try:
    messages = get_gmail_messages(user_google_email="you@example.com")
except GoogleAuthenticationError as e:
    print(e)  # Get helpful guidance

    # Reauthenticate
    start_google_auth(
        user_google_email="you@example.com",
        service_name="gmail"
    )
```

**With automatic retry**, this happens automatically in many cases!

### Scenario 3: Switching Users

```python
# Authenticate as first user
start_google_auth(user_google_email="user1@example.com", service_name="gmail")

# Use services as first user
messages1 = get_gmail_messages(user_google_email="user1@example.com")

# Authenticate as second user (in the same session)
start_google_auth(user_google_email="user2@example.com", service_name="gmail")

# Use services as second user
messages2 = get_gmail_messages(user_google_email="user2@example.com")
```

### Scenario 4: Clearing Credentials

```python
# Clear cached credentials for a user
clear_google_auth(user_google_email="you@example.com")

# Now reauthenticate
start_google_auth(user_google_email="you@example.com", service_name="gmail")
```

---

## 🛠️ Advanced Configuration

### Custom Session TTL

```python
from automagik_tools.tools.google_workspace_core.auth.session_manager import get_session_manager
from datetime import timedelta

# Get session manager
manager = get_session_manager()

# Bind session with custom TTL (e.g., 1 hour instead of 24)
manager.bind_session(
    session_id="my_session",
    user_email="you@example.com",
    ttl=timedelta(hours=1)
)
```

### Disable Automatic Retry

```python
from automagik_tools.tools.google_workspace_core.auth.retry_handler import configure_retry

# Disable automatic retry globally
configure_retry(enabled=False)

# Or change retry behavior
configure_retry(
    default_max_retries=3,  # More retries
    default_backoff_base=1.5  # Faster backoff
)
```

### Custom Token Storage

```python
from automagik_tools.tools.google_workspace_core.auth.token_storage_adapter import (
    TokenStorageAdapter,
    OAuthToken
)

class DatabaseTokenStorage(TokenStorageAdapter):
    """Store tokens in a database instead of files"""

    def get_tokens(self, user_id: str):
        # Load from database
        pass

    def set_tokens(self, user_id: str, tokens: OAuthToken):
        # Save to database
        pass

    # Implement other methods...
```

---

## 🐛 Troubleshooting

### Token Expired

**Symptom**: Error message about expired token

**Solution**:
1. Reauthenticate using `start_google_auth`
2. If automatic retry is enabled, this should happen automatically

### Token Revoked

**Symptom**: Error message about revoked token

**Common Causes**:
- Changed Google account password
- Manually revoked access in Google Account settings
- App credentials were reset

**Solution**:
1. Clear credentials: `clear_google_auth(user_google_email="you@example.com")`
2. Reauthenticate: `start_google_auth(...)`

### Insufficient Permissions

**Symptom**: Error about missing scopes/permissions

**Solution**:
1. Reauthenticate with the same command
2. Google will show the additional permissions needed
3. Grant all permissions

### Session Already Bound

**Symptom**: "Session already authenticated as different user"

**Solution**:

**Option 1**: Start a new session (recommended)
- Open a new terminal/browser window
- Authenticate there as the new user

**Option 2**: Log out first
```python
logout_google_auth()  # Log out current user
start_google_auth(user_google_email="new_user@example.com", ...)
```

### Network Errors

**Symptom**: Connection timeout or network errors

**Checklist**:
1. Check internet connection: `ping google.com`
2. Verify firewall settings
3. If using proxy, check proxy configuration
4. Try again in a few minutes
5. Check Google Cloud Status: https://status.cloud.google.com

### OAuth Client Not Configured

**Symptom**: "OAuth client credentials are not configured"

**Solution**:

**Method 1**: Environment Variables (Recommended)
```bash
export GOOGLE_OAUTH_CLIENT_ID='your-client-id'
export GOOGLE_OAUTH_CLIENT_SECRET='your-client-secret'
export GOOGLE_OAUTH_REDIRECT_URI='http://localhost:8000/oauth2callback'
```

**Method 2**: Client Secrets File
```bash
# Download client_secret.json from Google Cloud Console
export GOOGLE_CLIENT_SECRET_PATH='/path/to/client_secret.json'
```

**Method 3**: Default Location
- Place `client_secret.json` in the auth directory

---

## 🔒 Security Best Practices

### 1. Never Share Credentials

- ❌ Don't commit `client_secret.json` to version control
- ❌ Don't share OAuth tokens
- ✅ Use environment variables for credentials
- ✅ Add `client_secret.json` to `.gitignore`

### 2. Use Minimal Scopes

Only request the permissions you actually need:

```python
# Good: Only request what you need
scopes = ["https://www.googleapis.com/auth/gmail.readonly"]

# Bad: Requesting everything
scopes = ["https://www.googleapis.com/auth/gmail"]  # Includes send, modify, delete
```

### 3. Regular Credential Rotation

For production systems:
- Rotate OAuth client secrets regularly
- Set up credential expiry policies
- Monitor for unusual authentication activity

### 4. Secure Storage

- File-based credentials are stored in `~/.google_workspace_mcp/credentials/`
- Files are created with restrictive permissions (600)
- Consider encrypting credentials at rest for production

---

## 📊 Monitoring & Debugging

### View Session Statistics

```python
from automagik_tools.tools.google_workspace_core.auth.session_manager import get_session_manager

manager = get_session_manager()
stats = manager.get_stats()

print(f"Active sessions: {stats['active_sessions']}")
print(f"Expired sessions: {stats['expired_sessions']}")
print(f"Unique users: {stats['unique_users']}")
```

### Enable Debug Logging

```python
import logging

# Enable debug logs for OAuth module
logging.getLogger('automagik_tools.tools.google_workspace_core.auth').setLevel(logging.DEBUG)

# Now you'll see detailed OAuth flow logs
```

### Check If Auth Required

```python
from automagik_tools.tools.google_workspace_core.auth.auth_checker import check_if_auth_required

# Check if endpoint requires authentication
auth_needed = await check_if_auth_required("http://localhost:8000/mcp")

if auth_needed:
    print("Authentication required")
else:
    print("No authentication needed")
```

---

## 🎓 Understanding OAuth 2.1

### What is OAuth 2.1?

OAuth 2.1 is the latest OAuth standard that:
- Requires PKCE (Proof Key for Code Exchange) for security
- Deprecates implicit grant flow
- Mandates exact redirect URI matching
- Improves security best practices

### How Does It Work?

1. **Authorization Request**: Your app redirects user to Google's authorization server
2. **User Consent**: User reviews and grants permissions
3. **Authorization Code**: Google redirects back with a code
4. **Token Exchange**: Your app exchanges code for access & refresh tokens
5. **API Calls**: Use access token to call Google APIs
6. **Token Refresh**: When access token expires, use refresh token to get a new one

### Token Types

- **Access Token**: Short-lived (~1 hour), used for API requests
- **Refresh Token**: Long-lived, used to get new access tokens
- **ID Token**: Contains user identity information (OpenID Connect)

---

## 📚 Reference

### Environment Variables

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `GOOGLE_OAUTH_CLIENT_ID` | Yes | OAuth client ID | `123.apps.googleusercontent.com` |
| `GOOGLE_OAUTH_CLIENT_SECRET` | Yes | OAuth client secret | `GOCSPX-abc123...` |
| `GOOGLE_OAUTH_REDIRECT_URI` | Yes | Redirect URI | `http://localhost:8000/oauth2callback` |
| `GOOGLE_CLIENT_SECRET_PATH` | No | Path to client_secret.json | `/path/to/client_secret.json` |
| `MCP_ENABLE_OAUTH21` | No | Enable OAuth 2.1 mode | `true` (default) |
| `WORKSPACE_MCP_STATELESS_MODE` | No | Enable stateless mode | `false` (default) |

### Common Scopes

| Scope | Description | Access Level |
|-------|-------------|--------------|
| `gmail.readonly` | Read Gmail messages | Read-only |
| `gmail.send` | Send emails | Write |
| `gmail.modify` | Modify Gmail | Read/Write |
| `drive.readonly` | Read Drive files | Read-only |
| `drive` | Full Drive access | Read/Write |
| `calendar` | Manage calendar | Read/Write |
| `documents` | Edit Google Docs | Read/Write |
| `spreadsheets` | Edit Google Sheets | Read/Write |

### API Functions

| Function | Description |
|----------|-------------|
| `start_google_auth(user_email, service_name)` | Start OAuth flow |
| `clear_google_auth(user_email)` | Clear cached credentials |
| `logout_google_auth()` | Log out current session |

---

## 🤝 Getting Help

- **Documentation**: https://github.com/namastexlabs/automagik-tools/tree/main/docs
- **Issues**: https://github.com/namastexlabs/automagik-tools/issues
- **Discussions**: https://github.com/namastexlabs/automagik-tools/discussions

---

**Last Updated**: 2025-01-17
**Version**: 1.0
**Status**: Production Ready
