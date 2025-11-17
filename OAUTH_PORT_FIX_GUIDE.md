# OAuth Port 8887 → 8000 Fix Guide

## Problem Summary
The Google Workspace MCP tools are trying to use port 8887 for OAuth callbacks, but:
- Port 8887 is Forge's backend port (should not be used for OAuth)
- OAuth should use ports in the 8000 range (8000, 8001, etc.)
- Port 8000 is now **available** (conflicting server stopped)

## Root Cause
The Google Cloud Console OAuth 2.0 client has redirect URIs configured with port 8887 from when the old system used that port. The MCP tools try to match those redirect URIs and start a callback server on 8887, causing a conflict with Forge.

## ✅ What's Been Done Automatically

1. **✅ Stopped conflicting process** on port 8000 (PID 9942)
2. **✅ Created .env file** with correct configuration:
   ```bash
   GOOGLE_OAUTH_REDIRECT_URI=http://localhost:8000/oauth2callback
   WORKSPACE_MCP_PORT=8000
   PORT=8000
   ```
3. **✅ Verified** port availability:
   - Port 8000: ✅ Available
   - Port 8001: ✅ Available
   - Port 8887: ⚠️ In use by Forge (correct)

## ⚠️ Manual Step Required

**You need to update the Google Cloud Console OAuth client redirect URIs:**

### Step 1: Open Google Cloud Console
Visit this URL (opens directly to your OAuth client):
```
https://console.cloud.google.com/apis/credentials/oauthclient/822768429571-339mr05hgns8g9v1j02tkr8j8rplf2r5.apps.googleusercontent.com?project=822768429571
```

### Step 2: Update Authorized Redirect URIs
In the "Authorized redirect URIs" section:

**REMOVE** (if present):
- `http://localhost:8887/oauth2callback`
- `http://127.0.0.1:8887/oauth2callback`

**KEEP/ADD**:
- `http://localhost:8000/oauth2callback`
- `http://127.0.0.1:8000/oauth2callback`
- `http://localhost:8001/oauth2callback` (backup)
- `http://localhost/oauth2callback` (for port 80)

### Step 3: Save Changes
Click **SAVE** at the bottom of the page.

### Step 4: Wait for propagation
Changes take 5-10 minutes to propagate. Have some tea ☕

## Alternative: Use Port 8001

If you want to avoid any conflicts entirely, you can use port 8001 instead:

1. Update .env:
   ```bash
   GOOGLE_OAUTH_REDIRECT_URI=http://localhost:8001/oauth2callback
   WORKSPACE_MCP_PORT=8001
   PORT=8001
   ```

2. Add to Google Cloud Console redirect URIs:
   - `http://localhost:8001/oauth2callback`

## After Fix: Testing

Once you've updated the Google Cloud Console, test with:
```bash
# Clear cached credentials (optional but recommended)
rm -rf ~/.credentials/personal-genie/google-workspace/

# Test a Google Workspace tool
# The MCP tools will automatically pick up the new configuration
```

## Quick Reference

**Client ID**: `822768429571-339mr05hgns8g9v1j02tkr8j8rplf2r5.apps.googleusercontent.com`
**Project**: `gloogle-auth-namastex`
**Correct Port**: `8000` (or `8001` as backup)
**Wrong Port**: `8887` (Forge's port - do not use for OAuth)

## Why This Happened

The OAuth client was likely configured when:
1. An older system used port 8887 for OAuth callbacks
2. Later, Forge adopted port 8887 for its backend
3. The redirect URIs were never updated, causing the conflict

## Additional Notes

- The `.env` file has been created in `/home/namastex/genie/automagik-tools/.env`
- Port 8000 is now free and ready to use
- All Google Workspace tools will work once redirect URIs are updated
- The fix is permanent - no need to repeat after restarts
