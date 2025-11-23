# Hub Multi-Tenant Architecture Plan

**Version**: 1.1
**Date**: 2025-11-23
**FastMCP Version**: 2.13.1 (Latest)
**Status**: Implementation Ready - Simplified Stack

## 🎯 Executive Summary

Transform the automagik-tools Hub from a static tool aggregator into a **dynamic, multi-tenant MCP server** where assistants can programmatically manage tools for individual users. Each user has their own tool collection with isolated configurations, OAuth credentials, and preferences.

### Key Capabilities

1. **Dynamic Tool Management**: Add/remove/configure tools at runtime via MCP tools
2. **Multi-Tenancy**: Complete user isolation with per-user tool instances
3. **Persistent State**: SQLite/PostgreSQL + encrypted storage for configs and tokens
4. **OAuth Integration**: Namastex OAuth for user authentication
5. **HTTP Deployment**: Production-ready HTTP server with FastMCP 2.13.0

### Current vs Future State

| Aspect | Current | Future |
|--------|---------|--------|
| **Tool Loading** | All tools at startup | Per-user, on-demand |
| **Configuration** | Global env vars | Per-user, per-tool DB configs |
| **User Model** | Single user (implicit) | Multi-tenant with auth |
| **Tool Management** | Static (restart required) | Dynamic (runtime add/remove) |
| **Storage** | None (ephemeral) | Persistent (encrypted SQLite/PostgreSQL) |
| **Authentication** | None | OAuth Namastex |
| **Transport** | stdio/SSE | HTTP (production) |

---

## 🎯 Final Architecture Decisions (Simplified for 10 Users)

### Primary Use Case
- **Scale**: 10 employees of Namastex company
- **Access**: Each person logs in via Namastex OAuth
- **Isolation**: Each user gets their own personal MCP Server Hub
- **Portability**: Accessible from any application, anywhere
- **Management**: Users can ask assistant to add/remove MCP tools dynamically
- **Goal**: Simplest production-ready solution

### Simplified Stack (Zero Extra Infrastructure)

```
┌─────────────────────────────────────────────────────────────────┐
│                    Production Stack                              │
├─────────────────────────────────────────────────────────────────┤
│ Database:        SQLite + aiosqlite (relational data)           │
│ Token Storage:   DiskStore + FernetEncryptionWrapper (OAuth)    │
│ Cache:           In-memory (mount registry TTL)                  │
│ Migrations:      Alembic                                         │
│ HTTP Server:     Uvicorn (direct HTTP, not ASGI mount)          │
│ Authentication:  Namastex OAuth + FastMCP OAuthProxy            │
│                                                                   │
│ ❌ No Redis       (not needed for 10 users)                      │
│ ❌ No PostgreSQL  (SQLite sufficient for this scale)             │
│ ❌ No extra infra (single server deployment)                     │
└─────────────────────────────────────────────────────────────────┘
```

### Why This Stack?

**Scale Analysis**:
- 10 concurrent users = **LOW load scenario**
- SQLite handles thousands of concurrent reads efficiently
- Write operations (tool add/remove) are infrequent
- Single server deployment = simpler than distributed setup

**Storage Decisions**:

1. **SQLite for Relational Data**:
   - Tables: `users`, `user_tools`, `tool_configs`, `tool_registry`
   - Why: Perfect for structured queries, joins, transactions
   - When to upgrade: If you grow beyond 50 users or need HA

2. **DiskStore for OAuth Tokens**:
   - From `py-key-value-aio` (built into FastMCP)
   - Encrypted with `FernetEncryptionWrapper`
   - File-based persistence (no extra database needed)
   - Why: OAuth tokens are key-value data, DiskStore is simplest

3. **No Redis**:
   - Redis is typically for distributed caching or pub/sub
   - 10 users don't need distributed cache
   - In-memory mount cache (5min TTL) is sufficient
   - Saves infrastructure complexity

**Timeline**: 3-4 weeks instead of 10
- Week 1: FastMCP 2.13.1 + SQLite schema + Namastex OAuth + DiskStore
- Week 2: Hub management tools (add/remove/list tools)
- Week 3: Dynamic mounting engine + testing with 2-3 users
- Week 4: HTTP deploy + docs + onboard all 10 users

---

## 📚 Research Summary

### FastMCP 2.13.1 Key Features (Latest - November 2025)

✅ **Pluggable Storage Backends** - py-key-value-aio with encryption
✅ **OAuth Maturity** - WorkOS, GitHub, Google, Azure, AWS Cognito, Auth0, JWTs
✅ **Response Caching Middleware** - Performance for expensive operations
✅ **Server Lifespans** - Proper init/cleanup hooks
✅ **Context API** - User context propagation (`ctx.set_state/get_state`)
✅ **Dynamic Composition** - `mount()` for live server linking
✅ **Middleware System** - Authentication, logging, rate limiting

### Critical Documentation References

- **Storage**: [Storage Backends](https://gofastmcp.com/servers/storage-backends) - py-key-value-aio
- **Auth**: [OAuth Proxy](https://gofastmcp.com/servers/auth/oauth-proxy) - Token management
- **Composition**: [Server Composition](https://gofastmcp.com/servers/composition) - mount() vs import_server()
- **Context**: [State Management](https://gofastmcp.com/servers/context) - User context injection
- **HTTP**: [HTTP Deployment](https://gofastmcp.com/deployment/http) - Production transport

---

## 🏗️ Architecture Design

### System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    Hub FastMCP Server                            │
│              (HTTP Transport + OAuth Namastex)                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │              Authentication Middleware                      │ │
│  │  • Validate OAuth token (Namastex)                         │ │
│  │  • Extract user_id from JWT claims                         │ │
│  │  • ctx.set_state("user_id", user_id)                       │ │
│  │  • ctx.set_state("user_email", email)                      │ │
│  └────────────────────────────────────────────────────────────┘ │
│                              ↓                                    │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │              Hub Management Tools                           │ │
│  │                                                             │ │
│  │  Tool Discovery:                                            │ │
│  │  • get_available_tools() → List all tools in repository    │ │
│  │  • get_tool_metadata(tool_name) → Schemas, descriptions    │ │
│  │                                                             │ │
│  │  User Tool Management:                                      │ │
│  │  • add_tool(tool_name, config) → Enable + configure        │ │
│  │  • remove_tool(tool_name) → Disable for user               │ │
│  │  • list_my_tools() → User's active tools                   │ │
│  │  • get_tool_config(tool_name) → Current config             │ │
│  │  • update_tool_config(tool_name, config) → Update          │ │
│  │  • restart_tool(tool_name) → Remount with fresh config     │ │
│  │                                                             │ │
│  │  Pre-population:                                            │ │
│  │  • quick_setup(preset_name) → Add common tool bundles      │ │
│  │  • import_config(json) → Bulk import tools                 │ │
│  └────────────────────────────────────────────────────────────┘ │
│                              ↓                                    │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │           Dynamic Tool Mounting Engine                      │ │
│  │                                                             │ │
│  │  Per-Request Flow:                                          │ │
│  │  1. Extract user_id from Context                           │ │
│  │  2. Query DB: SELECT tools WHERE user_id = ?               │ │
│  │  3. For each tool:                                          │ │
│  │     a. Check mount cache (in-memory registry)              │ │
│  │     b. If not cached: create_server() with user config     │ │
│  │     c. mcp.mount(server, prefix=f"{user_id}_{tool}")       │ │
│  │     d. Cache mount for 5 minutes (TTL)                     │ │
│  │  4. Forward request to mounted tool                        │ │
│  │                                                             │ │
│  │  Mount Registry Structure:                                  │ │
│  │  {                                                          │ │
│  │    "user_123": {                                            │ │
│  │      "evolution_api": <FastMCP instance>,                  │ │
│  │      "google_calendar": <FastMCP instance>                 │ │
│  │    },                                                       │ │
│  │    "user_456": { ... }                                      │ │
│  │  }                                                          │ │
│  └────────────────────────────────────────────────────────────┘ │
│                              ↓                                    │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │         User's Mounted Tools (isolated per user)           │ │
│  │                                                             │ │
│  │  User 123:                    User 456:                    │ │
│  │  ┌──────────────┐            ┌──────────────┐             │ │
│  │  │ evolution_   │            │ evolution_   │             │ │
│  │  │ (Instance A) │            │ (Instance B) │             │ │
│  │  │ Config A     │            │ Config B     │             │ │
│  │  └──────────────┘            └──────────────┘             │ │
│  │  ┌──────────────┐            ┌──────────────┐             │ │
│  │  │ google_cal   │            │ slack        │             │ │
│  │  │ (Account A)  │            │ (Team B)     │             │ │
│  │  └──────────────┘            └──────────────┘             │ │
│  └────────────────────────────────────────────────────────────┘ │
│                              ↓                                    │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │           Storage Layer (py-key-value-aio)                 │ │
│  │                                                             │ │
│  │  ┌──────────────────────────────────────────────────────┐ │ │
│  │  │  PostgreSQL/SQLite (Primary Storage)                 │ │ │
│  │  │                                                       │ │ │
│  │  │  Tables:                                              │ │ │
│  │  │  • users (id, email, name, created_at)               │ │ │
│  │  │  • user_tools (user_id, tool_name, enabled)          │ │ │
│  │  │  • tool_configs (user_id, tool_name, key, value)     │ │ │
│  │  │  • oauth_tokens (user_id, tool, provider, tokens)    │ │ │
│  │  │  • tool_registry (name, metadata, config_schema)     │ │ │
│  │  └──────────────────────────────────────────────────────┘ │ │
│  │                                                             │ │
│  │  ┌──────────────────────────────────────────────────────┐ │ │
│  │  │  Redis (Optional - Cache + Sessions)                 │ │ │
│  │  │                                                       │ │ │
│  │  │  • OAuth tokens (encrypted, TTL)                     │ │ │
│  │  │  • Response cache (tool results)                     │ │ │
│  │  │  • Session data (active mounts)                      │ │ │
│  │  └──────────────────────────────────────────────────────┘ │ │
│  │                                                             │ │
│  │  Encryption: FernetEncryptionWrapper on all storages       │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘

External Components:
┌──────────────────┐     ┌──────────────────┐     ┌──────────────┐
│  Namastex OAuth  │────▶│   Claude / LLM   │────▶│  Hub Server  │
│  (User Auth)     │     │   (MCP Client)   │     │  (HTTP/8000) │
└──────────────────┘     └──────────────────┘     └──────────────┘
```

### Component Responsibilities

#### 1. Authentication Middleware
```python
class UserAuthMiddleware(Middleware):
    """Extract user identity from OAuth token and inject into context."""

    async def on_call_tool(self, context: MiddlewareContext, call_next):
        # Validate token with Namastex OAuth
        token = context.request.headers.get("Authorization")
        claims = validate_token(token)  # JWT validation

        # Inject user context
        context.fastmcp_context.set_state("user_id", claims["sub"])
        context.fastmcp_context.set_state("user_email", claims["email"])
        context.fastmcp_context.set_state("user_name", claims["name"])

        return await call_next(context)
```

#### 2. Hub Management Tools
```python
@hub.tool
async def add_tool(
    tool_name: str,
    config: dict[str, str],
    ctx: Context
) -> str:
    """Add a tool to your personal collection."""
    user_id = ctx.get_state("user_id")

    # Validate tool exists in registry
    if tool_name not in TOOL_REGISTRY:
        return f"❌ Tool '{tool_name}' not found. Use get_available_tools()."

    # Validate config against schema
    schema = TOOL_REGISTRY[tool_name]["config_schema"]
    validated_config = validate_config(config, schema)

    # Store in database
    await db.execute("""
        INSERT INTO user_tools (user_id, tool_name, enabled)
        VALUES (?, ?, TRUE)
        ON CONFLICT (user_id, tool_name) DO UPDATE SET enabled = TRUE
    """, (user_id, tool_name))

    for key, value in validated_config.items():
        await db.execute("""
            INSERT INTO tool_configs (user_id, tool_name, config_key, config_value)
            VALUES (?, ?, ?, ?)
            ON CONFLICT (user_id, tool_name, config_key)
            DO UPDATE SET config_value = ?, updated_at = NOW()
        """, (user_id, tool_name, key, value, value))

    # Clear mount cache to force remount on next request
    clear_mount_cache(user_id, tool_name)

    return f"✅ Tool '{tool_name}' added successfully! It's now available for use."

@hub.tool
async def list_my_tools(ctx: Context) -> list[dict]:
    """List all tools in your collection."""
    user_id = ctx.get_state("user_id")

    tools = await db.fetch_all("""
        SELECT tool_name, enabled, created_at
        FROM user_tools
        WHERE user_id = ? AND enabled = TRUE
        ORDER BY created_at DESC
    """, (user_id,))

    return [
        {
            "name": tool["tool_name"],
            "description": TOOL_REGISTRY[tool["tool_name"]]["description"],
            "added_at": tool["created_at"].isoformat()
        }
        for tool in tools
    ]
```

#### 3. Dynamic Tool Mounting Engine
```python
class DynamicToolMounter:
    """Manages per-user tool mounting with caching."""

    def __init__(self, hub: FastMCP, db: Database):
        self.hub = hub
        self.db = db
        # Cache: {user_id: {tool_name: (server, mount_time)}}
        self.mount_cache: dict[str, dict[str, tuple[FastMCP, float]]] = {}
        self.cache_ttl = 300  # 5 minutes

    async def mount_user_tools(self, user_id: str) -> None:
        """Mount all enabled tools for a user."""
        # Get user's tools from DB
        tools = await self.db.fetch_all("""
            SELECT tool_name FROM user_tools
            WHERE user_id = ? AND enabled = TRUE
        """, (user_id,))

        for row in tools:
            tool_name = row["tool_name"]
            await self.ensure_mounted(user_id, tool_name)

    async def ensure_mounted(self, user_id: str, tool_name: str) -> None:
        """Ensure a tool is mounted for the user (with caching)."""
        # Check cache
        if user_id in self.mount_cache:
            if tool_name in self.mount_cache[user_id]:
                server, mount_time = self.mount_cache[user_id][tool_name]
                if time.time() - mount_time < self.cache_ttl:
                    return  # Still valid

        # Load tool config from DB
        config = await self.load_tool_config(user_id, tool_name)

        # Create tool server instance with user's config
        tool_module = import_tool(tool_name)
        server = tool_module.create_server(**config)

        # Mount with user-specific prefix
        prefix = f"{user_id}_{tool_name}"
        self.hub.mount(server, prefix=prefix, as_proxy=True)

        # Cache
        if user_id not in self.mount_cache:
            self.mount_cache[user_id] = {}
        self.mount_cache[user_id][tool_name] = (server, time.time())

        logger.info(f"Mounted {tool_name} for user {user_id}")

    async def load_tool_config(self, user_id: str, tool_name: str) -> dict:
        """Load tool configuration from database."""
        configs = await self.db.fetch_all("""
            SELECT config_key, config_value
            FROM tool_configs
            WHERE user_id = ? AND tool_name = ?
        """, (user_id, tool_name))

        return {
            row["config_key"]: json.loads(row["config_value"])
            for row in configs
        }
```

#### 4. Storage Layer

**Database Schema (PostgreSQL/SQLite)**:
```sql
-- Users
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    name TEXT,
    oauth_provider TEXT NOT NULL,  -- 'namastex', 'google', etc
    oauth_sub TEXT NOT NULL,        -- OAuth subject ID
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_users_oauth ON users(oauth_provider, oauth_sub);

-- User's enabled tools
CREATE TABLE user_tools (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    tool_name TEXT NOT NULL,
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, tool_name)
);
CREATE INDEX idx_user_tools_lookup ON user_tools(user_id, enabled);

-- Tool configurations (key-value per user per tool)
CREATE TABLE tool_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    tool_name TEXT NOT NULL,
    config_key TEXT NOT NULL,
    config_value TEXT NOT NULL,  -- JSON string
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, tool_name, config_key)
);
CREATE INDEX idx_tool_configs_lookup ON tool_configs(user_id, tool_name);

-- OAuth tokens for external services (encrypted)
CREATE TABLE oauth_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    tool_name TEXT NOT NULL,
    provider TEXT NOT NULL,         -- 'google', 'github', etc
    access_token TEXT NOT NULL,     -- encrypted
    refresh_token TEXT,             -- encrypted
    expires_at TIMESTAMP,
    scopes TEXT[],
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, tool_name, provider)
);
CREATE INDEX idx_oauth_tokens_lookup ON oauth_tokens(user_id, tool_name);

-- Tool registry (metadata about available tools)
CREATE TABLE tool_registry (
    tool_name TEXT PRIMARY KEY,
    display_name TEXT NOT NULL,
    description TEXT NOT NULL,
    category TEXT NOT NULL,        -- 'communication', 'productivity', 'analytics'
    config_schema JSONB NOT NULL,  -- Pydantic schema as JSON
    required_oauth TEXT[],         -- ['google', 'github']
    icon_url TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Pre-populated configurations (templates)
CREATE TABLE tool_presets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    preset_name TEXT UNIQUE NOT NULL,
    display_name TEXT NOT NULL,
    description TEXT NOT NULL,
    tools JSONB NOT NULL,          -- Array of {tool_name, default_config}
    created_at TIMESTAMP DEFAULT NOW()
);
```

**Storage Implementation**:
```python
from key_value.aio.stores.postgres import PostgresStore
from key_value.aio.stores.redis import RedisStore
from key_value.aio.wrappers.encryption import FernetEncryptionWrapper
from cryptography.fernet import Fernet
import os

# Primary storage (encrypted)
db_storage = FernetEncryptionWrapper(
    key_value=PostgresStore(
        connection_string=os.environ["DATABASE_URL"]
    ),
    fernet=Fernet(os.environ["STORAGE_ENCRYPTION_KEY"])
)

# OAuth token storage (encrypted Redis)
oauth_storage = FernetEncryptionWrapper(
    key_value=RedisStore(
        host=os.environ.get("REDIS_HOST", "localhost"),
        port=int(os.environ.get("REDIS_PORT", 6379))
    ),
    fernet=Fernet(os.environ["OAUTH_ENCRYPTION_KEY"])
)
```

---

## 🔐 Authentication Flow

### Namastex OAuth Integration

```python
from fastmcp.server.auth.providers import OAuthProxy

# Configure OAuth Proxy for Namastex
auth_provider = OAuthProxy(
    # Namastex OAuth endpoints
    authorization_url="https://oauth.namastex.com/authorize",
    token_url="https://oauth.namastex.com/token",
    userinfo_url="https://oauth.namastex.com/userinfo",

    # Our Hub credentials (register with Namastex)
    client_id=os.environ["NAMASTEX_CLIENT_ID"],
    client_secret=os.environ["NAMASTEX_CLIENT_SECRET"],

    # Hub server URL
    base_url=os.environ.get("HUB_BASE_URL", "http://localhost:8000"),
    redirect_path="/auth/callback",

    # Required scopes
    required_scopes=["openid", "profile", "email", "tools:manage"],

    # Production token management
    jwt_signing_key=os.environ["JWT_SIGNING_KEY"],
    client_storage=oauth_storage,

    # Security
    forward_pkce=True,
    issuer_url=os.environ.get("HUB_BASE_URL", "http://localhost:8000")
)

# Create Hub with OAuth
hub = FastMCP(
    name="Automagik Tools Hub",
    instructions="Multi-tenant MCP tool management hub",
    auth=auth_provider
)
```

### Authentication Flow Diagram

```
┌─────────┐                 ┌─────────┐                 ┌─────────┐
│  Claude │                 │   Hub   │                 │Namastex │
│  (LLM)  │                 │ Server  │                 │  OAuth  │
└────┬────┘                 └────┬────┘                 └────┬────┘
     │                           │                           │
     │ 1. Call hub tool          │                           │
     ├──────────────────────────▶│                           │
     │    (no token)             │                           │
     │                           │                           │
     │ 2. 401 + OAuth URL        │                           │
     │◀──────────────────────────┤                           │
     │                           │                           │
     │ 3. Open browser           │                           │
     │   (OAuth flow)            │                           │
     ├───────────────────────────┼──────────────────────────▶│
     │                           │                           │
     │                           │ 4. User authorizes        │
     │                           │◀──────────────────────────┤
     │                           │    + code                 │
     │                           │                           │
     │                           │ 5. Exchange code for token│
     │                           ├──────────────────────────▶│
     │                           │                           │
     │                           │ 6. Access token           │
     │                           │◀──────────────────────────┤
     │                           │                           │
     │ 7. Hub token (JWT)        │                           │
     │◀──────────────────────────┤                           │
     │                           │                           │
     │ 8. Call tool with token   │                           │
     ├──────────────────────────▶│                           │
     │    Bearer: <jwt>          │                           │
     │                           │                           │
     │                           │ 9. Validate & extract     │
     │                           │    user_id from JWT       │
     │                           │                           │
     │ 10. Tool response         │                           │
     │◀──────────────────────────┤                           │
     │                           │                           │
```

---

## 📋 Implementation Roadmap

### Phase 1: Core Infrastructure (Week 1-2)

#### 1.1 Upgrade FastMCP
- [ ] Update `pyproject.toml`: `fastmcp = "^2.13.0"`
- [ ] Install py-key-value-aio dependencies
- [ ] Test compatibility with existing tools

#### 1.2 Database Setup
- [ ] Create SQLite schema (dev) + PostgreSQL schema (prod)
- [ ] Implement database migrations (Alembic)
- [ ] Setup encrypted storage wrappers
- [ ] Create database access layer (asyncpg/aiosqlite)

#### 1.3 OAuth Integration
- [ ] Register Hub with Namastex OAuth
- [ ] Configure OAuthProxy provider
- [ ] Implement authentication middleware
- [ ] Test OAuth flow end-to-end

**Deliverable**: Hub server with OAuth, empty tools, persistent storage

---

### Phase 2: Hub Management API (Week 3-4)

#### 2.1 Tool Registry
- [ ] Build tool discovery system (scan `tools/` directory)
- [ ] Extract tool metadata (name, description, config schema)
- [ ] Populate `tool_registry` table
- [ ] Create tool validation functions

#### 2.2 Management Tools
- [ ] `get_available_tools()` - List tools in registry
- [ ] `get_tool_metadata(tool_name)` - Get config schema
- [ ] `add_tool(tool_name, config)` - Enable tool for user
- [ ] `remove_tool(tool_name)` - Disable tool
- [ ] `list_my_tools()` - User's active tools
- [ ] `get_tool_config(tool_name)` - Current config
- [ ] `update_tool_config(tool_name, config)` - Update config

#### 2.3 Pre-population Support
- [ ] Create preset bundles (e.g., "Communication Suite", "Productivity Pack")
- [ ] Implement `quick_setup(preset_name)` tool
- [ ] Implement `import_config(json)` for bulk import

**Deliverable**: Hub with full CRUD API for tool management

---

### Phase 3: Dynamic Tool Mounting (Week 5-6)

#### 3.1 Mounting Engine
- [ ] Implement `DynamicToolMounter` class
- [ ] Per-user mount registry (in-memory cache)
- [ ] Load tool configs from database
- [ ] Create tool instances with user configs
- [ ] Mount tools with user-specific prefixes

#### 3.2 Request Flow
- [ ] Middleware: inject user_id into Context
- [ ] Pre-request hook: mount user's tools
- [ ] Tool invocation with user context
- [ ] Post-request cleanup (optional TTL unmount)

#### 3.3 Tool Lifecycle Management
- [ ] `restart_tool(tool_name)` - Clear cache + remount
- [ ] Handle tool errors gracefully
- [ ] Cache invalidation strategies
- [ ] Mount/unmount logging

**Deliverable**: Fully functional dynamic tool mounting per user

---

### Phase 4: Production Features (Week 7-8)

#### 4.1 Performance
- [ ] Add response caching middleware (FastMCP 2.13)
- [ ] Optimize database queries (indexes, prepared statements)
- [ ] Implement mount cache with TTL
- [ ] Add Redis for distributed cache (optional)

#### 4.2 Security
- [ ] Rate limiting per user (middleware)
- [ ] Input validation (Pydantic models)
- [ ] Audit logging (who did what when)
- [ ] Secrets management (env vars, vault)

#### 4.3 Monitoring
- [ ] Request logging middleware
- [ ] Prometheus metrics (optional)
- [ ] Error tracking (Sentry)
- [ ] Health check endpoints

#### 4.4 CLI Updates
- [ ] `serve hub` - Start multi-tenant hub
- [ ] `serve-all` - Mark as deprecated
- [ ] Migration guide for users

**Deliverable**: Production-ready Hub with observability

---

### Phase 5: Deployment & Documentation (Week 9-10)

#### 5.1 Deployment
- [ ] Docker container for Hub
- [ ] docker-compose with PostgreSQL + Redis
- [ ] Kubernetes manifests (optional)
- [ ] Deploy to FastMCP Cloud or self-hosted

#### 5.2 Documentation
- [ ] API reference (all Hub tools)
- [ ] User guide (how to add/configure tools)
- [ ] Admin guide (deployment, monitoring)
- [ ] Migration guide (old hub → new hub)
- [ ] Video tutorial (optional)

#### 5.3 Testing
- [ ] Unit tests (tool management functions)
- [ ] Integration tests (OAuth flow)
- [ ] Load tests (concurrent users)
- [ ] Security audit

**Deliverable**: Deployed Hub + comprehensive documentation

---

## 🎨 User Experience Examples

### Example 1: Assistant Adds WhatsApp Tool

```
User: "I need to send WhatsApp messages. Can you set up the Evolution API tool for me?"

Assistant (thinking): "User needs WhatsApp messaging. I'll check available tools and configure Evolution API."

[Assistant calls: get_available_tools()]

Hub Response:
{
  "tools": [
    {
      "name": "evolution_api",
      "display_name": "Evolution API",
      "description": "Send WhatsApp messages via Evolution API",
      "category": "communication",
      "required_config": ["instance_url", "api_key", "instance_name"]
    },
    ...
  ]
}
Assistant: "Perfect\! I found Evolution API. Now I'll get the configuration schema."

[Assistant calls: get_tool_metadata("evolution_api")]

Hub Response:
{
  "config_schema": {
    "instance_url": {
      "type": "string",
      "description": "URL of your Evolution API instance",
      "required": true
    },
    "api_key": {
      "type": "string",
      "description": "Your Evolution API key",
      "required": true,
      "sensitive": true
    },
    "instance_name": {
      "type": "string",
      "description": "Instance name for WhatsApp connection",
      "required": true
    }
  }
}

Assistant: "Great\! I have all the info. Let me add the tool to your collection."

[Assistant calls: add_tool("evolution_api", {
  "instance_url": "https://evo.example.com",
  "api_key": "sk-abc123...",
  "instance_name": "my_whatsapp"
})]

Hub Response:
"✅ Tool 'evolution_api' added successfully\! It's now available for use."

Assistant: "Done\! You can now use Evolution API to send WhatsApp messages. Would you like me to send a test message?"
```

---

## 🚀 HTTP Deployment (Production)

### Overview

FastMCP 2.13.1 supports **direct HTTP deployment** with Uvicorn for production use. This is the recommended approach for the multi-tenant Hub.

### Implementation Options

#### Option 1: Direct HTTP Server (Recommended for Hub)

```python
# automagik_tools/hub_http.py
from fastmcp import FastMCP
from key_value.aio.stores.disk import DiskStore
from key_value.aio.wrappers.encryption import FernetEncryptionWrapper
from cryptography.fernet import Fernet
import os

# Create encrypted token storage
token_storage = FernetEncryptionWrapper(
    key_value=DiskStore(path="./hub_tokens"),
    fernet=Fernet(os.environ["OAUTH_ENCRYPTION_KEY"])
)

# Create Hub with OAuth
from fastmcp.server.auth.providers import OAuthProxy
auth = OAuthProxy(
    authorization_url=os.environ["NAMASTEX_OAUTH_AUTHORIZE"],
    token_url=os.environ["NAMASTEX_OAUTH_TOKEN"],
    userinfo_url=os.environ["NAMASTEX_OAUTH_USERINFO"],
    client_id=os.environ["NAMASTEX_CLIENT_ID"],
    client_secret=os.environ["NAMASTEX_CLIENT_SECRET"],
    base_url=os.environ.get("HUB_BASE_URL", "http://localhost:8000"),
    redirect_path="/auth/callback",
    required_scopes=["openid", "profile", "email", "tools:manage"],
    jwt_signing_key=os.environ["JWT_SIGNING_KEY"],
    client_storage=token_storage,
    forward_pkce=True
)

hub = FastMCP(
    name="Automagik Tools Hub",
    instructions="Multi-tenant MCP tool management hub",
    auth=auth
)

# Add Hub management tools
@hub.tool
async def get_available_tools() -> list[dict]:
    """List all tools available in the repository."""
    # Implementation
    pass

@hub.tool
async def add_tool(tool_name: str, config: dict, ctx: Context) -> str:
    """Add a tool to your personal collection."""
    user_id = ctx.get_state("user_id")
    # Implementation
    pass

# Run HTTP server directly
if __name__ == "__main__":
    hub.run(transport="http", host="0.0.0.0", port=8000)
```

**Start server:**
```bash
# Development
python automagik_tools/hub_http.py

# Production with Uvicorn
uvicorn automagik_tools.hub_http:hub --host 0.0.0.0 --port 8000
```

---

#### Option 2: ASGI Application (For existing FastAPI apps)

```python
# automagik_tools/hub_http.py
from fastmcp import FastMCP
from fastapi import FastAPI

# Create Hub (same as Option 1)
hub = FastMCP(...)

# Export ASGI app
http_app = hub.http_app()

# Mount in existing FastAPI app (optional)
app = FastAPI()
app.mount("/mcp", http_app)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(http_app, host="0.0.0.0", port=8000)
```

---

### Production Deployment

#### 1. Environment Configuration

```bash
# .env.production
# Database
DATABASE_URL=sqlite:///./hub.db
ALEMBIC_CONFIG=alembic.ini

# OAuth (Namastex)
NAMASTEX_OAUTH_AUTHORIZE=https://oauth.namastex.com/authorize
NAMASTEX_OAUTH_TOKEN=https://oauth.namastex.com/token
NAMASTEX_OAUTH_USERINFO=https://oauth.namastex.com/userinfo
NAMASTEX_CLIENT_ID=hub_client_abc123
NAMASTEX_CLIENT_SECRET=secret_xyz789

# Hub Server
HUB_BASE_URL=https://hub.namastex.com
JWT_SIGNING_KEY=<random-256-bit-key>

# Token Encryption
OAUTH_ENCRYPTION_KEY=<fernet-key>
STORAGE_ENCRYPTION_KEY=<fernet-key>

# Optional
LOG_LEVEL=INFO
WORKERS=4
```

#### 2. Uvicorn Production Settings

```bash
# Single worker (sufficient for 10 users)
uvicorn automagik_tools.hub_http:hub \
  --host 0.0.0.0 \
  --port 8000 \
  --log-level info

# Multiple workers (if needed for scale)
uvicorn automagik_tools.hub_http:hub \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 4 \
  --log-level info
```

#### 3. Systemd Service

```ini
# /etc/systemd/system/automagik-hub.service
[Unit]
Description=Automagik Tools Hub
After=network.target

[Service]
Type=simple
User=hub
WorkingDirectory=/opt/automagik-hub
Environment="PATH=/opt/automagik-hub/venv/bin"
EnvironmentFile=/opt/automagik-hub/.env.production
ExecStart=/opt/automagik-hub/venv/bin/uvicorn \
    automagik_tools.hub_http:hub \
    --host 0.0.0.0 \
    --port 8000 \
    --log-level info

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### 4. NGINX Reverse Proxy

```nginx
# /etc/nginx/sites-available/hub.namastex.com
server {
    listen 443 ssl http2;
    server_name hub.namastex.com;

    ssl_certificate /etc/letsencrypt/live/hub.namastex.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/hub.namastex.com/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support (if needed)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name hub.namastex.com;
    return 301 https://$server_name$request_uri;
}
```

---

### Security Checklist

- [ ] **HTTPS Only**: SSL/TLS certificates (Let's Encrypt)
- [ ] **Token Encryption**: All OAuth tokens encrypted at rest (Fernet)
- [ ] **JWT Signing**: Secure random key for JWT tokens
- [ ] **CORS**: Configure allowed origins (if browser clients)
- [ ] **Rate Limiting**: Per-user request limits (middleware)
- [ ] **Input Validation**: Pydantic models for all tool inputs
- [ ] **Audit Logging**: Log all tool operations with user_id
- [ ] **Secrets Management**: Use environment vars or vault (never commit secrets)
- [ ] **Database Backups**: Regular SQLite backups (daily)
- [ ] **Monitoring**: Health check endpoint + error tracking

---

### Simplified 3-4 Week Roadmap

#### Week 1: Foundation
1. Update `pyproject.toml`: FastMCP 2.13.1 + aiosqlite + alembic + cryptography
2. Create SQLite schema with Alembic
3. Setup Namastex OAuth with DiskStore + FernetEncryptionWrapper
4. Test OAuth flow end-to-end

**Deliverable**: Hub HTTP server with OAuth, empty database

---

#### Week 2: Hub Management Tools
1. Build tool registry (scan `tools/` directory)
2. Implement Hub management tools:
   - `get_available_tools()` - List tools
   - `get_tool_metadata(tool_name)` - Get config schema
   - `add_tool(tool_name, config)` - Enable tool for user
   - `remove_tool(tool_name)` - Disable tool
   - `list_my_tools()` - User's active tools
   - `update_tool_config(tool_name, config)` - Update config
3. Test with 1 user + 1 tool (Evolution API)

**Deliverable**: Working CRUD API for tool management

---

#### Week 3: Dynamic Mounting
1. Implement `DynamicToolMounter` class
2. Per-user mount registry (in-memory cache with 5min TTL)
3. Load tool configs from SQLite database
4. Mount tools with user-specific prefixes
5. Test with 2-3 users simultaneously

**Deliverable**: Multi-tenant dynamic mounting working

---

#### Week 4: Production Deploy
1. Uvicorn production configuration
2. Systemd service setup
3. NGINX reverse proxy + SSL
4. Documentation (API reference, user guide)
5. Onboard all 10 users
6. Monitor for 1 week

**Deliverable**: Production Hub serving 10 users

---

## ✅ Success Criteria

1. **Functional**: Each user can add/remove/configure tools independently
2. **Secure**: OAuth authentication + encrypted token storage
3. **Fast**: Tool operations complete in <1 second
4. **Reliable**: 99% uptime for 10 concurrent users
5. **Simple**: Zero external infrastructure (no Redis, no PostgreSQL)
6. **Documented**: User guide + API reference complete

---

## 📝 Next Steps

1. ✅ **Plan Complete** - Architecture decisions finalized
2. ⏭️ **Phase 1.1** - Update `pyproject.toml` dependencies
3. ⏭️ **Phase 1.2** - Create SQLite schema with Alembic
4. ⏭️ **Phase 1.3** - Setup OAuth Namastex + DiskStore

**Ready to start implementation!** 🚀
