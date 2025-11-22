# Tool Inventory - Complete Audit

**Date**: 2025-11-22
**Purpose**: Complete audit of ALL tools in automagik-tools for major QA preparation

## Summary

**Total Tools Found**: 19 tools in automagik-tools
**Configured in ecosystem.config.cjs**: 9 tools (ports 8001-8009)
**Configured in .mcp.json**: 22 total entries (9 automagik-tools + 13 external)
**Missing from ecosystem.config.cjs**: 10 Google Workspace tools
**Old directories to remove**: 1 (openapi_bridge)

---

## Tools in automagik-tools Repository

### Core Tools (Production Ready)

#### 1. evolution-api ✅
- **Location**: `automagik_tools/tools/evolution_api/`
- **Description**: Complete WhatsApp messaging suite for Evolution API v2
- **ecosystem.config.cjs**: ✅ Port 8001
- **mcp.json**: ✅ Port 8001
- **pyproject.toml**: ✅ evolution-api dependencies
- **Status**: CONFIGURED - Ready for QA

#### 2. openapi ✅
- **Location**: `automagik_tools/tools/openapi/`
- **Description**: Universal OpenAPI to MCP converter - plugin any API spec automatically
- **ecosystem.config.cjs**: ✅ Port 8002
- **mcp.json**: ✅ Port 8002
- **pyproject.toml**: ✅ openapi dependencies
- **Status**: CONFIGURED - Ready for QA
- **Note**: Renamed from openapi_bridge (old directory still exists)

#### 3. genie_tool ✅
- **Location**: `automagik_tools/tools/genie_tool/`
- **Description**: Intelligent MCP tool orchestrator with persistent memory using Agno
- **ecosystem.config.cjs**: ✅ Port 8003
- **mcp.json**: ✅ Port 8003
- **pyproject.toml**: ✅ genie_tool dependencies
- **Status**: CONFIGURED - Ready for QA

#### 4. hive ⚠️
- **Location**: `automagik_tools/tools/hive/` (NOT FOUND)
- **Description**: Hive API integration
- **ecosystem.config.cjs**: ✅ Port 8004
- **mcp.json**: ✅ Port 8004
- **pyproject.toml**: ✅ hive dependencies
- **Status**: MISSING DIRECTORY - Tool configured but files don't exist

#### 5. wait ✅
- **Location**: `automagik_tools/tools/wait/`
- **Description**: Smart timing functions for agent workflows
- **ecosystem.config.cjs**: ✅ Port 8005
- **mcp.json**: ✅ Port 8005
- **pyproject.toml**: ❌ No separate dependency group
- **Status**: CONFIGURED - Ready for QA

---

### Legacy Tools (Backward Compatibility)

#### 6. omni ✅
- **Location**: `automagik_tools/tools/omni/`
- **Description**: Multi-tenant omnichannel messaging (WhatsApp, Slack, Discord)
- **ecosystem.config.cjs**: ✅ Port 8006
- **mcp.json**: ✅ Port 8006
- **pyproject.toml**: ❌ No separate dependency group
- **Status**: CONFIGURED - Ready for QA

#### 7. json-to-google-docs ✅
- **Location**: `automagik_tools/tools/json_to_google_docs/`
- **Description**: Converts JSON to Google Docs with templates and markdown
- **ecosystem.config.cjs**: ✅ Port 8007
- **mcp.json**: ✅ Port 8007
- **pyproject.toml**: ❌ No separate dependency group
- **Status**: CONFIGURED - Ready for QA

---

### Experimental Tools

#### 8. spark ✅
- **Location**: `automagik_tools/tools/spark/`
- **Description**: AutoMagik workflow orchestration and AI agent management
- **ecosystem.config.cjs**: ✅ Port 8008
- **mcp.json**: ✅ Port 8008
- **pyproject.toml**: ❌ No separate dependency group
- **Status**: CONFIGURED - Ready for QA

#### 9. gemini-assistant ✅
- **Location**: `automagik_tools/tools/gemini_assistant/`
- **Description**: Advanced Gemini consultation tool with session management
- **ecosystem.config.cjs**: ✅ Port 8009
- **mcp.json**: ✅ Port 8009
- **pyproject.toml**: ✅ gemini-assistant dependencies
- **Status**: CONFIGURED - Ready for QA

---

### Google Workspace Tools (NOT in ecosystem.config.cjs)

#### 10. google-workspace ✅
- **Location**: `automagik_tools/tools/google_workspace/`
- **Description**: Comprehensive Google Workspace integration (all services)
- **ecosystem.config.cjs**: ❌ MISSING
- **mcp.json**: ✅ Port 11011
- **Status**: NOT IN ECOSYSTEM - Separate PM2 configuration

#### 11. google-calendar ✅
- **Location**: `automagik_tools/tools/google_calendar/`
- **Description**: 40+ tools for managing Calendar
- **ecosystem.config.cjs**: ❌ MISSING
- **mcp.json**: ✅ Port 11002
- **Status**: NOT IN ECOSYSTEM - Separate PM2 configuration

#### 12. google-gmail ✅
- **Location**: `automagik_tools/tools/google_gmail/`
- **Description**: Comprehensive Gmail integration with 12+ tools
- **ecosystem.config.cjs**: ❌ MISSING
- **mcp.json**: ✅ Port 11003
- **Status**: NOT IN ECOSYSTEM - Separate PM2 configuration

#### 13. google-drive ✅
- **Location**: `automagik_tools/tools/google_drive/`
- **Description**: 30+ tools for managing Drive
- **ecosystem.config.cjs**: ❌ MISSING
- **mcp.json**: ✅ Port 11004
- **Status**: NOT IN ECOSYSTEM - Separate PM2 configuration

#### 14. google-docs ✅
- **Location**: `automagik_tools/tools/google_docs/`
- **Description**: 45+ tools for managing Docs
- **ecosystem.config.cjs**: ❌ MISSING
- **mcp.json**: ✅ Port 11005
- **Status**: NOT IN ECOSYSTEM - Separate PM2 configuration

#### 15. google-sheets ✅
- **Location**: `automagik_tools/tools/google_sheets/`
- **Description**: 20+ tools for managing Sheets
- **ecosystem.config.cjs**: ❌ MISSING
- **mcp.json**: ✅ Port 11006
- **Status**: NOT IN ECOSYSTEM - Separate PM2 configuration

#### 16. google-slides ✅
- **Location**: `automagik_tools/tools/google_slides/`
- **Description**: 10+ tools for managing Slides
- **ecosystem.config.cjs**: ❌ MISSING
- **mcp.json**: ✅ Port 11007
- **Status**: NOT IN ECOSYSTEM - Separate PM2 configuration

#### 17. google-forms ✅
- **Location**: `automagik_tools/tools/google_forms/`
- **Description**: 9+ tools for managing Forms
- **ecosystem.config.cjs**: ❌ MISSING
- **mcp.json**: ✅ Port 11008
- **Status**: NOT IN ECOSYSTEM - Separate PM2 configuration

#### 18. google-tasks ✅
- **Location**: `automagik_tools/tools/google_tasks/`
- **Description**: 34+ tools for managing Tasks
- **ecosystem.config.cjs**: ❌ MISSING
- **mcp.json**: ✅ Port 11009
- **Status**: NOT IN ECOSYSTEM - Separate PM2 configuration

#### 19. google-chat ✅
- **Location**: `automagik_tools/tools/google_chat/`
- **Description**: 7+ tools for managing Chat
- **ecosystem.config.cjs**: ❌ MISSING
- **mcp.json**: ✅ Port 11010
- **Status**: NOT IN ECOSYSTEM - Separate PM2 configuration

---

## External Tools (Not in automagik-tools)

These tools are referenced in `.mcp.json` but are NOT part of the automagik-tools repository:

1. **namastex-oauth** (Port 11000) - OAuth server
2. **google-calendar-test** (Port 11001) - Calendar testing tool
3. **genie-omni** (Port 11012) - Genie omni tool
4. **gofastmcp** (https://gofastmcp.com/mcp) - External FastMCP service

---

## Old Directories to Remove

### openapi_bridge (DUPLICATE)
- **Location**: `automagik_tools/tools/openapi_bridge/`
- **Status**: OLD DIRECTORY - Should be removed
- **Reason**: Tool was renamed to `openapi`, this is the old version
- **Action**: Delete this directory

---

## Critical Findings

### 1. Missing Tool Directory
- **hive** is configured in ecosystem.config.cjs and pyproject.toml but directory doesn't exist
- **Action Required**: Either create the tool or remove from configurations

### 2. Two Separate PM2 Ecosystems
The repository appears to have TWO separate PM2 deployments:
- **ecosystem.config.cjs** (ports 8001-8009): automagik-tools core
- **Separate ecosystem** (ports 11000-11012): Google Workspace tools + OAuth

**Recommendation**: Decide if Google Workspace tools should be:
- A) Added to ecosystem.config.cjs (unified deployment)
- B) Kept separate (document why)

### 3. Inconsistent pyproject.toml
Some tools have dedicated dependency groups in pyproject.toml, others don't:
- ✅ Have: evolution-api, openapi, genie_tool, gemini-assistant, hive
- ❌ Missing: wait, omni, json-to-google-docs, spark, all Google Workspace tools

**Action Required**: Add dependency groups for all tools

### 4. Port Allocation Strategy
Current allocation:
- 8001-8009: Core automagik-tools (ecosystem.config.cjs)
- 11000-11012: Google Workspace + OAuth (separate PM2)

**Recommendation**: Document this strategy in TESTING.md or PM2_SETUP.md

---

## Tool Testing Checklist

For each tool, verify:
- [ ] HTTP mode (SSE) works via PM2
- [ ] STDIO mode works for Claude Desktop
- [ ] Environment variables documented
- [ ] Dependencies in pyproject.toml
- [ ] README.md exists
- [ ] __main__.py exists for standalone execution

---

## Next Steps for Major QA

1. **Fix missing hive directory** - Determine if tool should exist or be removed
2. **Remove openapi_bridge** - Old duplicate directory
3. **Decide on Google Workspace tools** - Add to ecosystem.config.cjs or document separation
4. **Update pyproject.toml** - Add missing dependency groups
5. **Document port allocation** - Clarify two-tier strategy
6. **Test each tool individually** - Both HTTP and STDIO modes
7. **Update TESTING.md** - Add Google Workspace tools to checklist

---

## Tool Count Summary

| Category | Count | Status |
|----------|-------|--------|
| Total in Repository | 19 | Mixed |
| In ecosystem.config.cjs | 9 | Configured |
| Google Workspace Tools | 10 | Not in ecosystem |
| External Tools | 4 | Separate |
| Old/Duplicate Directories | 1 | Need removal |
| **Total Unique Tools** | **23** | **Across all systems** |
