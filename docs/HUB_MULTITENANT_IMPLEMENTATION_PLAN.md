# Automagik Tools Hub - Multi-Tenant Implementation Plan

**Project Goal**: Transform all tools to be multi-tenant compliant, create a comprehensive Hub UI for tool management, and deliver a production-ready multi-tenant Hub server with WorkOS AuthKit integration.

**Target Delivery**: Complete autonomous implementation with testing, documentation, and deployment ready for human QA.

---

## Phase 1: Foundation & Architecture (COMPLETE)

### ✅ 1.1 Research FastMCP Multi-Tenant Patterns
**Status**: COMPLETE

**Key Findings**:
- **Access Token Extraction**: Use `get_access_token()` dependency to get user info
- **User ID Extraction**: Extract from `token.claims.get("sub")` or custom claims
- **Context Usage**: Tools receive `ctx: Context` parameter for MCP features
- **Server Composition**: Use `mount()` for dynamic tool composition
- **AuthKit Integration**: WorkOS AuthKitProvider already configured

**Multi-Tenant Pattern**:
```python
from fastmcp import FastMCP, Context
from fastmcp.server.dependencies import get_access_token

@mcp.tool
async def my_tool(param: str, ctx: Context) -> str:
    """Multi-tenant tool example."""
    token = get_access_token()
    user_id = token.claims.get("sub") if token else None

    # Load per-user configuration
    user_config = await get_user_config(user_id)
    client = MyAPIClient(user_config)

    return await client.do_something(param)
```

### 📋 1.2 Create Implementation Plan
**Status**: IN PROGRESS (this document)

**Deliverables**:
- This comprehensive plan document
- Phase breakdown with priorities
- Technical architecture diagrams (to be created)
- Timeline estimates per phase

---

## Phase 2: Hub Backend - Tool Management & Discovery

### 2.1 Hub Tool Discovery & Catalogue API
**Priority**: CRITICAL
**Estimated Effort**: 8 hours

**Requirements**:
1. Dynamic tool discovery from `automagik_tools/tools/` directory
2. Tool metadata extraction (name, description, config schema, status)
3. Catalogue API endpoints:
   - `GET /api/tools/catalogue` - List all available tools
   - `GET /api/tools/{tool_name}/metadata` - Get tool details
   - `GET /api/tools/{tool_name}/schema` - Get configuration schema

**Implementation**:
```python
# automagik_tools/hub/catalogue.py
from fastapi import APIRouter
from typing import List, Dict, Any

router = APIRouter(prefix="/api/tools")

@router.get("/catalogue")
async def get_tool_catalogue() -> List[Dict[str, Any]]:
    """Discover and return all available tools."""
    tools = []
    tools_dir = Path("automagik_tools/tools")

    for tool_dir in tools_dir.iterdir():
        if tool_dir.is_dir() and not tool_dir.name.startswith("_"):
            metadata = await get_tool_metadata(tool_dir.name)
            tools.append(metadata)

    return tools

async def get_tool_metadata(tool_name: str) -> Dict[str, Any]:
    """Extract metadata from tool module."""
    # Import tool's get_metadata() function
    # Return: name, description, version, config_schema, multi_tenant_ready
    pass
```

**Database Schema**:
```sql
-- Add to existing Hub schema
CREATE TABLE tool_catalogue (
    tool_name TEXT PRIMARY KEY,
    display_name TEXT NOT NULL,
    description TEXT,
    version TEXT,
    config_schema JSON,
    multi_tenant_ready BOOLEAN DEFAULT FALSE,
    category TEXT, -- 'communication', 'productivity', 'ai', 'workflow'
    tags JSON, -- ['whatsapp', 'messaging', etc.]
    icon_url TEXT,
    documentation_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 2.2 Per-User Tool Configuration API
**Priority**: CRITICAL
**Estimated Effort**: 10 hours

**Requirements**:
1. CRUD API for per-user tool configurations
2. Encrypted credential storage
3. Configuration validation against tool schema
4. API endpoints:
   - `GET /api/user/tools` - List user's configured tools
   - `POST /api/user/tools/{tool_name}` - Add/configure tool
   - `PUT /api/user/tools/{tool_name}` - Update configuration
   - `DELETE /api/user/tools/{tool_name}` - Remove tool configuration
   - `POST /api/user/tools/{tool_name}/test` - Test connection

**Database Schema** (already exists in `hub_db.py`, needs enhancement):
```sql
CREATE TABLE IF NOT EXISTS tool_configs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    tool_name TEXT NOT NULL,
    config_data JSON NOT NULL, -- Encrypted credentials
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, tool_name)
);

CREATE INDEX idx_tool_configs_user ON tool_configs(user_id);
```

**Implementation**:
```python
# automagik_tools/hub/user_tools.py
from fastapi import APIRouter, Depends, HTTPException
from cryptography.fernet import Fernet

router = APIRouter(prefix="/api/user/tools")

@router.post("/{tool_name}")
async def configure_tool(
    tool_name: str,
    config: Dict[str, Any],
    user_id: str = Depends(get_current_user_id)
):
    """Configure a tool for the current user."""
    # Validate config against tool schema
    await validate_tool_config(tool_name, config)

    # Encrypt sensitive credentials
    encrypted_config = encrypt_credentials(config)

    # Store in database
    await save_tool_config(user_id, tool_name, encrypted_config)

    return {"status": "configured", "tool": tool_name}
```

### 2.3 Tool Lifecycle Management API
**Priority**: HIGH
**Estimated Effort**: 6 hours

**Requirements**:
1. Per-user tool instances (mounted servers)
2. Tool state tracking (running, stopped, error)
3. API endpoints:
   - `POST /api/user/tools/{tool_name}/start` - Start tool instance
   - `POST /api/user/tools/{tool_name}/stop` - Stop tool instance
   - `POST /api/user/tools/{tool_name}/refresh` - Reload configuration
   - `GET /api/user/tools/{tool_name}/status` - Get runtime status
   - `GET /api/user/tools/{tool_name}/logs` - Get recent logs

**Implementation**:
```python
# automagik_tools/hub/tool_lifecycle.py
from fastmcp import FastMCP
from typing import Dict

class ToolInstanceManager:
    """Manages per-user tool instances."""

    def __init__(self):
        self.instances: Dict[str, Dict[str, FastMCP]] = {}
        # Structure: {user_id: {tool_name: mcp_instance}}

    async def start_tool(self, user_id: str, tool_name: str):
        """Start a tool instance for a user."""
        # Load user configuration
        config = await get_user_tool_config(user_id, tool_name)

        # Create tool-specific MCP server
        tool_mcp = await create_tool_instance(tool_name, config)

        # Store instance
        if user_id not in self.instances:
            self.instances[user_id] = {}
        self.instances[user_id][tool_name] = tool_mcp

        # Mount on Hub (with user prefix)
        hub_mcp.mount(tool_mcp, prefix=f"{user_id}_{tool_name}")

        return {"status": "started"}
```

---

## Phase 3: Tool Migration - Multi-Tenant Conversion

### 3.1 Migration Pattern Template
**Universal Pattern** for all tools:

```python
# BEFORE (Single-Tenant)
from fastmcp import FastMCP

config = ToolConfig()  # Global config
client = ToolClient(config)  # Global client

mcp = FastMCP("Tool")

@mcp.tool()
async def do_something(param: str) -> str:
    return await client.execute(param)

# AFTER (Multi-Tenant)
from fastmcp import FastMCP, Context
from fastmcp.server.dependencies import get_access_token

mcp = FastMCP("Tool")

async def get_user_client(ctx: Context) -> ToolClient:
    """Get or create per-user client."""
    token = get_access_token()
    user_id = token.claims.get("sub") if token else None

    if not user_id:
        raise ValueError("Authentication required")

    # Load user-specific configuration
    config_data = await get_user_tool_config(user_id, "tool_name")
    config = ToolConfig(**config_data)

    # Create per-request client
    return ToolClient(config)

@mcp.tool()
async def do_something(param: str, ctx: Context) -> str:
    """Multi-tenant version with user isolation."""
    client = await get_user_client(ctx)
    return await client.execute(param)
```

### 3.2 Priority 1 - Critical Tools

#### 3.2.1 Evolution API (WhatsApp Business)
**File**: `automagik_tools/tools/evolution_api/__init__.py`
**Effort**: 4 hours
**Changes**:
- Add `ctx: Context` parameter to all tools
- Replace global `config` with per-user config loading
- Replace global `client` with per-request client creation
- Add `get_user_config()` helper function
- Test with multiple users

#### 3.2.2 OMNI (Multi-Tenant WhatsApp)
**Files**:
- `automagik_tools/tools/omni/__init__.py`
- `automagik_tools/tools/genie-omni/__init__.py`
**Effort**: 6 hours (OMNI + Genie-OMNI)
**Changes**:
- Add `ctx: Context` to all 40+ tools
- Replace global `OmniClient` with per-user instances
- Add user context to all WhatsApp operations
- Ensure message isolation between users
- Test conversation threading per user

#### 3.2.3 Gemini Assistant
**File**: `automagik_tools/tools/gemini_assistant/__init__.py`
**Effort**: 5 hours
**Changes**:
- Add `ctx: Context` parameter
- Replace global session storage with per-user sessions
- Use user_id as session key prefix
- Isolate conversation history per user
- Test multi-user concurrent sessions

#### 3.2.4 Genie Tool (MCP Orchestrator)
**File**: `automagik_tools/tools/genie_tool/__init__.py`
**Effort**: 6 hours
**Changes**:
- Add `ctx: Context` parameter
- Replace global OpenAI client with per-user instances
- Use per-user memory databases
- Isolate agent sessions per user
- Test agent memory isolation

### 3.3 Priority 2 - High Priority Tools

#### 3.3.1 Spark (Workflow Orchestration)
**File**: `automagik_tools/tools/spark/__init__.py`
**Effort**: 4 hours

#### 3.3.2 AutoMagik Hive
**File**: `automagik_tools/tools/automagik_hive/__init__.py`
**Effort**: 4 hours

---

## Phase 4: Hub UI Development

### 4.1 Copy and Adapt Electron UI
**Source**: `../automagik-omni/resources/ui/`
**Target**: `automagik_tools/hub_ui/`
**Effort**: 4 hours

**Structure to Copy**:
```
automagik_tools/hub_ui/
├── package.json (adapt dependencies)
├── vite.config.ts
├── tsconfig.json
├── index.html
├── src/
│   ├── main.tsx
│   ├── App.tsx (NEW: Hub-specific)
│   ├── components/
│   │   ├── ui/ (shadcn/ui components)
│   │   ├── ToolCatalogue.tsx (NEW)
│   │   ├── ToolCard.tsx (NEW)
│   │   ├── ToolConfig.tsx (NEW)
│   │   ├── ToolStatus.tsx (NEW)
│   │   └── OAuth/LoginButton.tsx
│   ├── pages/
│   │   ├── Dashboard.tsx (NEW)
│   │   ├── ToolsPage.tsx (NEW)
│   │   ├── SettingsPage.tsx (NEW)
│   │   └── LoginPage.tsx
│   ├── lib/
│   │   ├── api.ts (Hub API client)
│   │   └── auth.ts (OAuth client)
│   └── assets/
└── public/
```

### 4.2 Tool Catalogue UI
**File**: `hub_ui/src/components/ToolCatalogue.tsx`
**Effort**: 6 hours

**Features**:
- Grid/list view toggle
- Search and filter by category/tags
- Tool cards showing:
  - Icon, name, description
  - Multi-tenant status badge
  - Configured/Not Configured status
  - "Configure" / "Manage" buttons
- Responsive design (mobile, tablet, desktop)

**Component Structure**:
```typescript
interface ToolMetadata {
  name: string;
  displayName: string;
  description: string;
  category: string;
  tags: string[];
  iconUrl?: string;
  multiTenantReady: boolean;
  configured: boolean; // User-specific
  status?: 'running' | 'stopped' | 'error';
}

export function ToolCatalogue() {
  const [tools, setTools] = useState<ToolMetadata[]>([]);
  const [filter, setFilter] = useState<string>('all');
  const [search, setSearch] = useState<string>('');

  useEffect(() => {
    fetchToolCatalogue();
  }, []);

  return (
    <div className="tool-catalogue">
      <SearchBar onSearch={setSearch} />
      <FilterTabs onFilter={setFilter} />
      <ToolGrid tools={filteredTools} />
    </div>
  );
}
```

### 4.3 Tool Configuration Interface
**File**: `hub_ui/src/components/ToolConfig.tsx`
**Effort**: 8 hours

**Features**:
- Dynamic form generation from tool schema
- Field types: text, password, number, boolean, select
- Input validation
- Credential encryption indication
- Test connection button
- Save/Cancel actions

**Component Structure**:
```typescript
interface ToolConfigProps {
  toolName: string;
  schema: JSONSchema;
  existingConfig?: Record<string, any>;
  onSave: (config: Record<string, any>) => void;
  onCancel: () => void;
}

export function ToolConfig({ toolName, schema, existingConfig, onSave, onCancel }: ToolConfigProps) {
  const [config, setConfig] = useState(existingConfig || {});
  const [testing, setTesting] = useState(false);

  const handleTest = async () => {
    setTesting(true);
    const result = await testToolConnection(toolName, config);
    // Show result toast
  };

  return (
    <Card>
      <CardHeader>Configure {toolName}</CardHeader>
      <CardContent>
        <DynamicForm schema={schema} value={config} onChange={setConfig} />
      </CardContent>
      <CardFooter>
        <Button onClick={handleTest} disabled={testing}>Test Connection</Button>
        <Button onClick={() => onSave(config)}>Save</Button>
        <Button variant="outline" onClick={onCancel}>Cancel</Button>
      </CardFooter>
    </Card>
  );
}
```

### 4.4 Tool Control Panel
**File**: `hub_ui/src/components/ToolControlPanel.tsx`
**Effort**: 6 hours

**Features**:
- Tool status indicator (running/stopped/error)
- Start/Stop/Restart buttons
- Refresh configuration button
- View logs button
- Delete configuration button (with confirmation)
- Real-time status updates (WebSocket)

### 4.5 OAuth Login Flow
**File**: `hub_ui/src/pages/LoginPage.tsx`
**Effort**: 4 hours

**Features**:
- WorkOS AuthKit integration
- Redirect to AuthKit login
- Handle OAuth callback
- Store access token
- Redirect to dashboard on success

### 4.6 Auto-Browser-Open
**File**: `automagik_tools/hub_http.py`
**Effort**: 2 hours

**Implementation**:
```python
import webbrowser
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print(f"Hub server starting on http://localhost:{port}")

    # Open browser after 1 second
    import threading
    def open_browser():
        import time
        time.sleep(1)
        webbrowser.open(f"http://localhost:{port}")

    threading.Thread(target=open_browser, daemon=True).start()

    yield

    # Shutdown
    print("Hub server shutting down")

app = FastAPI(lifespan=lifespan)
```

---

## Phase 5: Integration & Testing

### 5.1 Hub Integration
**Effort**: 8 hours

**Tasks**:
1. Update `hub_http.py` to serve UI static files
2. Mount all migrated tools with user prefixes
3. Implement tool instance management
4. Add WebSocket support for real-time updates
5. Configure CORS for UI

**Implementation**:
```python
# automagik_tools/hub_http.py
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware

app = FastAPI()

# CORS for UI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount UI static files
app.mount("/", StaticFiles(directory="hub_ui/dist", html=True), name="ui")

# Mount catalogue API
app.include_router(catalogue.router)

# Mount user tools API
app.include_router(user_tools.router)

# Mount tool lifecycle API
app.include_router(tool_lifecycle.router)
```

### 5.2 End-to-End Testing
**Effort**: 10 hours

**Test Scenarios**:
1. **User Registration & Login**
   - Register new user via WorkOS
   - Login with existing user
   - Logout and re-login
   - Token expiration handling

2. **Tool Discovery**
   - View tool catalogue
   - Search tools
   - Filter by category
   - View tool details

3. **Tool Configuration**
   - Configure Evolution API
   - Configure OMNI
   - Configure Gemini Assistant
   - Test connection for each
   - Save configurations

4. **Tool Lifecycle**
   - Start configured tools
   - Stop running tools
   - Refresh tool configuration
   - View tool logs
   - Delete tool configuration

5. **Multi-User Isolation**
   - Create two users
   - Configure same tool differently
   - Verify data isolation
   - Test concurrent usage

6. **MCP Client Integration**
   - Configure .mcp.json for HTTP
   - Connect from Claude Desktop
   - Test tool discovery
   - Test tool execution
   - Verify OAuth flow

**Test Implementation**:
```python
# tests/test_hub_e2e.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_user_workflow():
    """Test complete user workflow."""
    async with AsyncClient(base_url="http://localhost:8884") as client:
        # 1. Login (mocked OAuth)
        token = await mock_oauth_login(client)

        # 2. Get catalogue
        response = await client.get("/api/tools/catalogue", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        tools = response.json()
        assert len(tools) > 0

        # 3. Configure tool
        config = {"api_key": "test-key", "base_url": "https://test.com"}
        response = await client.post(
            "/api/user/tools/evolution_api",
            json=config,
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200

        # 4. Start tool
        response = await client.post(
            "/api/user/tools/evolution_api/start",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200

        # 5. Verify MCP tool available
        # ... test MCP protocol
```

---

## Phase 6: Documentation & Deployment

### 6.1 Update Documentation
**Effort**: 6 hours

**Files to Update**:
1. `README.md` - Add Hub setup instructions
2. `docs/HUB_USER_GUIDE.md` - Complete user guide
3. `docs/HUB_ADMIN_GUIDE.md` - Admin/deployment guide
4. `docs/TOOL_MIGRATION_GUIDE.md` - For tool developers
5. `docs/API_REFERENCE.md` - Hub API documentation

### 6.2 Create .mcp.json
**File**: `.mcp.json`
**Effort**: 1 hour

```json
{
  "mcpServers": {
    "automagik-hub": {
      "url": "http://localhost:8884/mcp",
      "transport": {
        "type": "http"
      },
      "name": "Automagik Tools Hub",
      "description": "Multi-tenant hub for all Automagik tools",
      "icon": "https://automagik.dev/icon.png"
    }
  }
}
```

### 6.3 Deployment Verification
**Effort**: 4 hours

**Checklist**:
- [ ] All tools migrated to multi-tenant
- [ ] Hub UI builds successfully (`cd hub_ui && npm run build`)
- [ ] Hub server starts on port 8884
- [ ] Browser opens automatically
- [ ] OAuth login works
- [ ] Tool catalogue loads
- [ ] Tool configuration works
- [ ] Tool start/stop works
- [ ] MCP client can connect
- [ ] All tests pass
- [ ] Documentation complete
- [ ] Git committed and pushed

---

## Phase 7: Git Workflow & Commit Strategy

### 7.1 Branch Strategy
**Branch**: `feature/hub-multitenant-complete`

### 7.2 Commit Plan
**Atomic commits** for each major component:

```bash
# Phase 2 commits
git add automagik_tools/hub/catalogue.py
git commit -m "feat(hub): implement tool catalogue discovery API"

git add automagik_tools/hub/user_tools.py automagik_tools/hub/hub_db.py
git commit -m "feat(hub): implement per-user tool configuration API with encrypted storage"

git add automagik_tools/hub/tool_lifecycle.py
git commit -m "feat(hub): implement tool lifecycle management (start/stop/refresh)"

# Phase 3 commits (per tool)
git add automagik_tools/tools/evolution_api/
git commit -m "feat(evolution-api): migrate to multi-tenant with Context support"

git add automagik_tools/tools/omni/ automagik_tools/tools/genie-omni/
git commit -m "feat(omni): migrate to multi-tenant with per-user isolation"

# ... continue for each tool

# Phase 4 commits
git add automagik_tools/hub_ui/
git commit -m "feat(ui): copy and adapt Electron UI from automagik-omni"

git add automagik_tools/hub_ui/src/components/ToolCatalogue.tsx
git commit -m "feat(ui): implement tool catalogue with search and filters"

# ... continue for each UI component

# Phase 5 commits
git add tests/test_hub_e2e.py
git commit -m "test(hub): add comprehensive end-to-end test suite"

# Phase 6 commits
git add docs/ README.md
git commit -m "docs: comprehensive Hub documentation and user guide"

git add .mcp.json
git commit -m "feat(hub): add MCP client configuration for HTTP mode"

# Final commit
git add .
git commit -m "chore: finalize multi-tenant Hub implementation - ready for production"
```

---

## Success Criteria

### Functional Requirements
- ✅ All 6 non-compliant tools migrated to multi-tenant
- ✅ Hub discovers all tools dynamically
- ✅ Per-user tool configuration with encryption
- ✅ Tool lifecycle management (start/stop/refresh)
- ✅ OAuth authentication via WorkOS AuthKit
- ✅ Comprehensive UI for tool management
- ✅ Auto-browser-open on Hub start
- ✅ MCP client integration via HTTP

### Quality Requirements
- ✅ All tests passing (unit + integration + e2e)
- ✅ Code coverage > 80%
- ✅ No linting errors
- ✅ Documentation complete
- ✅ Performance: UI loads < 2s, API responses < 500ms
- ✅ Security: Credentials encrypted, no token leaks

### User Experience
- ✅ User can login via OAuth
- ✅ User can browse tool catalogue
- ✅ User can configure tools via UI
- ✅ User can start/stop tools
- ✅ User can see tool status in real-time
- ✅ MCP client can auto-discover Hub
- ✅ MCP client can authenticate and use tools

---

## Timeline Estimate

| Phase | Effort (hours) | Status |
|-------|----------------|--------|
| Phase 1: Research & Planning | 4 | ✅ COMPLETE |
| Phase 2: Hub Backend | 24 | 🟡 PENDING |
| Phase 3: Tool Migration | 29 | 🟡 PENDING |
| Phase 4: Hub UI | 30 | 🟡 PENDING |
| Phase 5: Integration & Testing | 18 | 🟡 PENDING |
| Phase 6: Documentation | 11 | 🟡 PENDING |
| **Total** | **116 hours** | **~3 days continuous** |

---

## Risk Mitigation

### Technical Risks
1. **Tool migration breaks existing functionality**
   - Mitigation: Maintain backward compatibility, comprehensive testing

2. **OAuth integration issues**
   - Mitigation: Test with WorkOS sandbox first, follow FastMCP examples

3. **Performance degradation with multiple users**
   - Mitigation: Connection pooling, caching, load testing

4. **UI doesn't work on all browsers**
   - Mitigation: Use modern React patterns, test on Chrome/Firefox/Safari

### Process Risks
1. **Scope creep**
   - Mitigation: Stick to this plan, defer enhancements to later

2. **Testing gaps**
   - Mitigation: Follow TDD, require 80% coverage

---

## Next Steps

**Immediate Actions**:
1. ✅ Complete this plan document
2. 🟡 Start Phase 2.1: Hub Tool Discovery API
3. 🟡 Continue systematically through each phase
4. 🟡 Commit after each major component
5. 🟡 Test continuously during development
6. 🟡 Final verification before user QA

**User Handoff**:
- User returns to complete implementation
- Run `uv run automagik-tools hub --host 0.0.0.0 --port 8884 --transport http`
- Browser auto-opens to Hub UI
- Login via WorkOS OAuth
- Test tool catalogue, configuration, lifecycle
- Report bugs for iterative fixes

---

**Document Version**: 1.0
**Last Updated**: 2025-11-23
**Author**: Claude Code (Autonomous Implementation)
