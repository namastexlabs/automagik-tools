# Automagik Tools Hub Configuration Guide

## Zero Configuration Philosophy

The Automagik Tools Hub is designed for **zero configuration** - all settings are managed through intuitive web interfaces, with configuration securely stored in an encrypted SQLite database.

## Three-Phase Configuration Model

### 1. Bootstrap Phase (Before Database Exists)

**Required: `.env` file with database path**

```bash
HUB_DATABASE_PATH=./data/hub.db
```

This is the ONLY environment variable needed. The Hub cannot start without knowing where to store its database.

### 2. Migration Phase (Database Exists, Incomplete Config)

**Automatic migration of legacy .env values**

On first run with an existing `.env` file, the Hub will:
1. Detect `.env` contains configuration values
2. Check if database has corresponding settings
3. Auto-migrate values from `.env` → database (idempotent)
4. Log deprecation warnings if `.env` still used after migration

This ensures smooth upgrades from older installations.

### 3. Runtime Phase (Database Fully Populated)

**Database is single source of truth**

All configuration loaded from database via `RuntimeConfig`. The `.env` file is ignored (except `HUB_DATABASE_PATH` for database connection).

## Configuration Interfaces

### Setup Wizard (`/setup`)

**URL:** `http://localhost:8884/setup`

**Purpose:** Initial Hub configuration

**Settings Managed:**
- **Authentication Mode:**
  - WorkOS (recommended): OAuth, SSO, MFA support
  - Local: Simple username/password (no external dependencies)
- **WorkOS Credentials** (if WorkOS mode):
  - Client ID
  - API Key
  - AuthKit Domain
- **Admin Settings:**
  - Super admin emails (comma-separated)
- **Network Configuration:**
  - CORS allowed origins
  - HSTS enable/disable (production HTTPS)
  - CSP report URI (optional monitoring)

**When to Use:**
- First-time installation
- Switching authentication modes
- Updating network security settings

### Tool Catalogue (`/catalogue`)

**URL:** `http://localhost:8884/catalogue`

**Purpose:** Per-tool configuration

**Settings Managed:**
- **Tool Installation:** Install/uninstall tools per workspace
- **OAuth Credentials:** Per-tool OAuth client ID/secret (e.g., Google tools)
- **API Keys:** Per-tool API keys (e.g., Evolution API, OMNI)
- **Tool Parameters:** Tool-specific settings defined in tool metadata

**When to Use:**
- Installing a new tool
- Configuring tool-specific credentials
- Updating tool parameters

**Example: Google Gmail Tool**

When you install the Google Gmail tool, the catalogue UI detects it requires OAuth and shows:
- Google Client ID (input field)
- Google Client Secret (secure input)
- Redirect URI (auto-generated)

These credentials are stored per workspace in the `tool_configs` table, NOT globally.

### Settings UI (`/settings`) - Advanced

**URL:** `http://localhost:8884/settings`

**Purpose:** Runtime configuration adjustments

**Settings Managed:**
- Security headers (HSTS, CSP)
- CORS origins (add/remove)
- Admin user management
- Workspace settings

**When to Use:**
- Production deployment (enable HSTS)
- Adding allowed origins
- Managing super admins

## Configuration Storage

### Database Schema

**Table: `config_store`**
```sql
CREATE TABLE config_store (
    config_key TEXT PRIMARY KEY,
    config_value TEXT NOT NULL,     -- Encrypted for sensitive values
    is_encrypted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

**Encrypted Keys:**
- `workos_api_key`
- `workos_cookie_password`
- Any key ending in `_secret`, `_key`, `_password`

**Table: `tool_configs`**
```sql
CREATE TABLE tool_configs (
    workspace_id TEXT NOT NULL,
    tool_name TEXT NOT NULL,
    config_key TEXT NOT NULL,
    config_value TEXT NOT NULL,     -- Encrypted for OAuth/API keys
    is_encrypted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    PRIMARY KEY (workspace_id, tool_name, config_key)
);
```

**Per-Tool Config Keys:**
- `{tool_name}.oauth_client_id`
- `{tool_name}.oauth_client_secret`
- `{tool_name}.api_key`
- `{tool_name}.{custom_param}` (from tool metadata config_schema)

### Encryption

**Algorithm:** AES-256-GCM via Fernet (Python cryptography library)

**Key Derivation:**
1. Master key generated from `HUB_DATABASE_PATH` + system entropy
2. Stored in `data/.hub.key` (gitignored, secure permissions)
3. Used to encrypt/decrypt sensitive config values

**Encrypted Values:**
- WorkOS API key
- WorkOS cookie password
- Tool OAuth client secrets
- Tool API keys
- Any value marked as sensitive in tool metadata

## Tool Configuration Schema

Tools define their configurable parameters via `get_metadata()`:

```python
def get_metadata():
    return {
        "name": "google_gmail",
        "description": "Google Gmail integration",
        "auth_type": "oauth",  # Triggers OAuth UI flow
        "config_schema": {
            "oauth_client_id": {
                "type": "string",
                "required": True,
                "description": "Google OAuth Client ID",
                "sensitive": False,
            },
            "oauth_client_secret": {
                "type": "string",
                "required": True,
                "description": "Google OAuth Client Secret",
                "sensitive": True,  # Encrypted in database
            },
            "max_results": {
                "type": "integer",
                "required": False,
                "default": 50,
                "description": "Max emails to fetch per query",
            },
        },
    }
```

**Catalogue UI automatically generates:**
- OAuth flow for `auth_type: "oauth"`
- Input fields for each `config_schema` parameter
- Secure inputs for `sensitive: True`
- Validation based on `type` and `required`

## Migration from Legacy .env

### What Gets Migrated

**WorkOS Credentials:**
- `WORKOS_API_KEY` → `config_store.workos_api_key` (encrypted)
- `WORKOS_CLIENT_ID` → `config_store.workos_client_id`
- `WORKOS_AUTHKIT_DOMAIN` → `config_store.workos_authkit_domain`

**Security Settings:**
- `HUB_ENABLE_HSTS` → `config_store.hsts_enabled`
- `HUB_CSP_REPORT_URI` → `config_store.csp_report_uri`
- `HUB_ALLOWED_ORIGINS` → `config_store.allowed_origins`
- `SUPER_ADMIN_EMAILS` → `config_store.super_admin_emails`

**Tool Credentials (Google example):**
- `GOOGLE_CLIENT_ID` → `tool_configs.google_gmail.oauth_client_id`
- `GOOGLE_CLIENT_SECRET` → `tool_configs.google_gmail.oauth_client_secret` (encrypted)

### What Does NOT Get Migrated

**Bootstrap variable:**
- `HUB_DATABASE_PATH` - Still required in `.env`

**Single-tenant tools:**
- Evolution API, OMNI, Gemini, Spark, Hive, Genie
- These tools are NOT multi-tenant compatible
- Use standalone mode only, NOT via Hub
- See `docs/MULTI_TENANT_STATUS.md` for status

**Development settings:**
- `HUB_HOST`, `HUB_PORT` - Use command-line args instead
- `PYPI_*` - CI/CD only, not runtime

### Migration Process

1. **Automatic on first run:**
   ```python
   # In bootstrap.py
   if os.path.exists(".env") and not config_store.is_populated():
       await mode_manager.migrate_from_env()
   ```

2. **Idempotent:** Safe to run multiple times, skips existing values

3. **Logged:** Migration actions logged to `logs/hub.log`

4. **Warnings:** Deprecation warnings if `.env` used after migration

### Manual Migration

If you prefer manual migration:

1. **Visit Setup Wizard:** `http://localhost:8884/setup`
2. **Enter credentials:** Copy from `.env` to web form
3. **Save:** Submit form to store in database
4. **Verify:** Check `data/hub.db` has values
5. **Remove:** Delete old `.env` entries (keep `HUB_DATABASE_PATH`)

## Security Best Practices

### Production Deployment

1. **Enable HSTS:**
   - Settings UI → Security → Enable HSTS
   - Only enable after HTTPS is working

2. **Restrict CORS Origins:**
   - Settings UI → Security → CORS Origins
   - Remove `*`, add specific domains only

3. **Set Super Admin Emails:**
   - Setup Wizard → Admin Settings
   - Limit to trusted email addresses

4. **Rotate Secrets:**
   - Settings UI → Credentials → Rotate WorkOS API Key
   - Update WorkOS dashboard → Update Hub database

### Backup Configuration

**Database backup includes all configuration:**
```bash
cp data/hub.db data/hub.db.backup
cp data/.hub.key data/.hub.key.backup
```

**Restore:**
```bash
cp data/hub.db.backup data/hub.db
cp data/.hub.key.backup data/.hub.key
```

**WARNING:** `.hub.key` is required to decrypt sensitive values. Losing this file = losing encrypted config.

## Troubleshooting

### "WorkOS not configured" Error

**Cause:** Database missing WorkOS credentials

**Fix:**
1. Visit `/setup` wizard
2. Complete WorkOS configuration
3. Or: Check `.env` has `WORKOS_*` values for auto-migration

### "Invalid or expired token" Error

**Cause:** WorkOS session expired or cookie password changed

**Fix:**
1. Clear browser cookies
2. Log in again at `/auth/authorize`

### Tool Configuration Not Saving

**Cause:** Tool metadata missing `config_schema`

**Fix:**
1. Check tool's `get_metadata()` has `config_schema` defined
2. Restart Hub to reload tool metadata
3. Refresh Catalogue UI

### Migration Not Working

**Cause:** Database already has values (idempotent check)

**Fix:**
1. Check `data/hub.db` with SQLite browser
2. Delete specific key: `DELETE FROM config_store WHERE config_key = 'workos_api_key';`
3. Restart Hub to trigger re-migration

## Advanced Configuration

### Custom Database Path

**Set via environment variable:**
```bash
HUB_DATABASE_PATH=/custom/path/hub.db python -m automagik_tools.hub
```

**Or via `.env`:**
```bash
HUB_DATABASE_PATH=/custom/path/hub.db
```

### Runtime Config Override (Development)

**For testing, you can override RuntimeConfig:**
```python
from automagik_tools.hub.setup import RuntimeConfig

# Override in code (NOT recommended for production)
config = RuntimeConfig(
    app_mode="LOCAL",
    hsts_enabled=False,
    allowed_origins=["http://localhost:3000"],
)
```

**Better approach:** Use Settings UI or database updates.

### Database-First Enforcement

**To ensure no .env fallbacks:**
1. Remove all env vars except `HUB_DATABASE_PATH`
2. Restart Hub
3. If it fails, you've found a missing database migration
4. Report as bug - all config should be database-first

## FAQ

**Q: Can I still use .env for everything?**
A: No. After migration, only `HUB_DATABASE_PATH` is read from `.env`. All other config must be in database.

**Q: What if I want to manage config via files?**
A: Use database exports: `sqlite3 data/hub.db .dump > config.sql`. Config-as-code via database schema.

**Q: How do I reset to factory defaults?**
A: Delete `data/hub.db` and `data/.hub.key`, restart Hub, complete setup wizard.

**Q: Can I share config across multiple Hub instances?**
A: Yes, share the same database file (`HUB_DATABASE_PATH`) and encryption key (`data/.hub.key`). Use network storage for multi-node deployments.

**Q: Where are tool OAuth tokens stored?**
A: Per-user tokens in `user_credentials` table (encrypted). Per-tool config in `tool_configs` table.

**Q: What's the difference between Setup Wizard and Tool Catalogue?**
A: Setup Wizard = Hub-level config (auth, admins, network). Tool Catalogue = per-tool config (OAuth, API keys, params).

## Support

**Issues:** https://github.com/namastexlabs/automagik-tools/issues
**Docs:** https://docs.genieos.namastex.io
**Community:** Discord (link in README)
