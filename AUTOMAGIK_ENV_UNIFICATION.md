# AUTOMAGIK Environment Variable Unification

## Summary
Unified all AUTOMAGIK-related environment variables across the codebase to use a single, consistent naming scheme.

## Changes Made

### 1. Environment Variable Renaming
- `AUTOMAGIK_AGENTS_API_KEY` → `AUTOMAGIK_API_KEY`
- `AUTOMAGIK_AGENTS_BASE_URL` → `AUTOMAGIK_BASE_URL`
- `AUTOMAGIK_AGENTS_TIMEOUT` → `AUTOMAGIK_TIMEOUT`
- `AUTOMAGIK_AGENTS_ENABLE_MARKDOWN` → `AUTOMAGIK_ENABLE_MARKDOWN`
- `AUTOMAGIK_AGENTS_OPENAPI_URL` → `AUTOMAGIK_OPENAPI_URL`

### 2. Removed Duplicate Variables
- Removed `GENIE_AUTOMAGIK_API_KEY` (now uses `AUTOMAGIK_API_KEY`)
- Removed `GENIE_AUTOMAGIK_BASE_URL` (now uses `AUTOMAGIK_BASE_URL`)
- Removed `GENIE_AUTOMAGIK_TIMEOUT` (now uses `AUTOMAGIK_TIMEOUT`)

### 3. Code Updates
- **automagik_tools/tools/automagik/config.py**: Updated field aliases and env_prefix
- **automagik_tools/tools/automagik/__init__.py**: Updated required env vars and metadata
- **automagik_tools/tools/genie/config.py**: Updated to use unified AUTOMAGIK_* variables
- **README.md**: Updated all documentation examples
- **.env.example**: Updated with unified variables and proper documentation
- **.env**: Updated to use new variable names

### 4. Benefits
- **Simplicity**: One set of AUTOMAGIK_* variables for all tools
- **No Duplication**: Genie and Automagik tools share the same configuration
- **Clarity**: Clear, consistent naming without AGENTS or GENIE prefixes
- **Maintainability**: Easier to document and manage

## Migration Guide

If you have existing configurations, update your environment variables:

```bash
# Old variables
AUTOMAGIK_AGENTS_API_KEY=your-key
AUTOMAGIK_AGENTS_BASE_URL=http://localhost:8881
GENIE_AUTOMAGIK_API_KEY=your-key
GENIE_AUTOMAGIK_BASE_URL=http://localhost:8881

# New unified variables
AUTOMAGIK_API_KEY=your-key
AUTOMAGIK_BASE_URL=http://localhost:8881
```

Both the Automagik tool and Genie will now use the same AUTOMAGIK_* variables.