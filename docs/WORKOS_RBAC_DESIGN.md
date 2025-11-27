# WorkOS RBAC Design for Automagik Tools Hub

## Executive Summary

This document defines a comprehensive Role-Based Access Control (RBAC) system for the automagik-tools Hub using WorkOS Fine-Grained Authorization (FGA). The system balances security, usability, and flexibility for multi-tenant MCP tool deployment.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Role Hierarchy](#role-hierarchy)
3. [Permission Model](#permission-model)
4. [Schema Design](#schema-design)
5. [Implementation Guide](#implementation-guide)
6. [User Experience](#user-experience)
7. [Migration Strategy](#migration-strategy)
8. [Security Considerations](#security-considerations)

---

## Architecture Overview

### Current State
- Open access Hub: Any authenticated user can add/remove/configure all tools
- WorkOS AuthKit handles authentication (user identity)
- No authorization layer for tool access control

### Target State
- Fine-grained RBAC: Users have specific roles with defined permissions
- Organization-level and user-level permissions
- Audit trail for all authorization decisions
- WorkOS FGA handles all authorization checks

### Key Components

```
┌─────────────────────────────────────────────────────────────┐
│                    Automagik Tools Hub                       │
│  ┌────────────┐  ┌─────────────┐  ┌──────────────────┐     │
│  │  FastMCP   │  │   WorkOS    │  │   WorkOS FGA     │     │
│  │   Server   │→ │  AuthKit    │→ │  Authorization   │     │
│  │            │  │  (AuthN)    │  │    (AuthZ)       │     │
│  └────────────┘  └─────────────┘  └──────────────────┘     │
│         ↓                                     ↓              │
│  ┌────────────────────────────────────────────────────┐     │
│  │           Tool Collection per User                 │     │
│  │  - Google Calendar, Gmail, Drive, etc.            │     │
│  │  - Per-user credentials & configurations          │     │
│  └────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

---

## Role Hierarchy

### 1. Hub Admin (`hub-admin`)
**Scope**: Organization-wide

**Responsibilities**:
- Full system access and control
- Manage all users and their permissions
- View all tools across the organization
- Configure organization-wide settings
- Access audit logs
- Manage role assignments

**Use Cases**:
- IT administrators
- Platform administrators
- Security officers

**Typical Count**: 1-3 per organization

---

### 2. Team Manager (`team-manager`)
**Scope**: Team-level

**Responsibilities**:
- Manage team members' tool access
- View team activity and usage
- Configure team-wide tool defaults
- Assign tools to team members
- Limited audit log access (team only)

**Use Cases**:
- Engineering team leads
- Department managers
- Project managers

**Typical Count**: 5-15 per organization

---

### 3. Power User (`power-user`)
**Scope**: Personal collection + advanced features

**Responsibilities**:
- Full control over personal tool collection
- Add/remove/configure any available tool
- Manage personal credentials
- Export/import configurations
- Use advanced tool features

**Use Cases**:
- Senior developers
- Technical specialists
- Data analysts

**Typical Count**: 20-40% of users

---

### 4. Standard User (`standard-user`)
**Scope**: Personal collection (limited)

**Responsibilities**:
- Add approved tools to personal collection
- Configure personal tools (limited fields)
- View available tools
- Manage personal credentials (basic)

**Use Cases**:
- General employees
- Junior developers
- Business users

**Typical Count**: 50-70% of users

---

### 5. Read-Only User (`viewer`)
**Scope**: View-only access

**Responsibilities**:
- View available tools (catalog)
- View own tool collection
- View tool documentation
- Cannot add, modify, or delete

**Use Cases**:
- Contractors
- Temporary staff
- Auditors
- Compliance reviewers

**Typical Count**: 5-10% of users

---

## Permission Model

### Permission Scopes

All permissions follow the format: `<resource>:<action>`

#### Tool Management Permissions

| Permission | Description | Required By |
|------------|-------------|-------------|
| `tools:read` | View available tools catalog | All roles |
| `tools:add` | Add tools to personal collection | standard-user+ |
| `tools:add:any` | Add any tool (including restricted) | power-user+ |
| `tools:configure` | Modify tool settings (basic fields) | standard-user+ |
| `tools:configure:advanced` | Modify advanced settings & credentials | power-user+ |
| `tools:delete` | Remove tools from personal collection | standard-user+ |
| `tools:execute` | Execute/invoke tools | standard-user+ |

#### Credential Management Permissions

| Permission | Description | Required By |
|------------|-------------|-------------|
| `credentials:read` | View credential metadata (no secrets) | standard-user+ |
| `credentials:create` | Store new credentials | standard-user+ |
| `credentials:update` | Update existing credentials | standard-user+ |
| `credentials:delete` | Delete credentials | standard-user+ |
| `credentials:share` | Share credentials with team | team-manager+ |

#### User & Team Management Permissions

| Permission | Description | Required By |
|------------|-------------|-------------|
| `users:read` | View user list | team-manager+ |
| `users:read:all` | View all users across org | hub-admin |
| `users:manage` | Add/remove/update users | hub-admin |
| `roles:read` | View role assignments | team-manager+ |
| `roles:assign` | Assign roles to users | hub-admin |
| `teams:read` | View team information | team-manager+ |
| `teams:manage` | Create/update/delete teams | hub-admin |

#### Administration Permissions

| Permission | Description | Required By |
|------------|-------------|-------------|
| `admin:audit` | View audit logs | team-manager+ |
| `admin:audit:all` | View all audit logs | hub-admin |
| `admin:settings` | Modify org settings | hub-admin |
| `admin:billing` | View/manage billing | hub-admin |
| `admin:security` | Configure security policies | hub-admin |

---

## Schema Design

### WorkOS FGA Schema

```fga
version 0.3

# Core resource types
type user

type organization
    relation admin [user]
    relation manager [user]
    relation member [user]

    # Audit log access
    relation audit_viewer []
    inherit audit_viewer if
        any_of
            relation admin
            relation manager

type team
    relation parent [organization]
    relation manager [user]
    relation member [user]

    # Team managers can manage their team
    inherit manager if
        relation admin on parent [organization]

type role
    relation member [user]
    relation assignable_by [user, role]

    # Role assignment permissions
    relation can_assign []
    inherit can_assign if
        relation assignable_by

# Tool-related resource types
type tool_catalog
    relation owner [organization]

    # Permissions for tool catalog
    relation viewer [user, role]
    relation contributor [user, role]
    relation admin [user, role]

    # Inheritance
    inherit viewer if
        relation member on owner [organization]

    inherit contributor if
        relation admin

    inherit admin if
        relation admin on owner [organization]

type tool_instance
    relation owner [user]
    relation team [team]
    relation organization [organization]

    # Tool permissions
    relation executor [user, role]
    relation configurator [user, role]
    relation viewer [user, role]

    # Owner gets all permissions
    inherit executor if
        relation owner

    inherit configurator if
        any_of
            relation owner
            relation manager on team [team]

    inherit viewer if
        any_of
            relation executor
            relation configurator
            relation member on organization [organization]

type credential
    relation owner [user]
    relation shared_with [user, team]

    # Credential access
    relation accessor []
    inherit accessor if
        any_of
            relation owner
            relation member on shared_with [team]

# Role definitions with permissions
type permission
    relation holder [user, role, team]

    relation granted []
    inherit granted if
        relation holder

# Policy-based access control for advanced features
policy is_power_user(user_metadata map) {
    user_metadata.role in ["power-user", "team-manager", "hub-admin"]
}

policy has_tool_limit(user_metadata map, context map) {
    let max_tools = user_metadata.max_tools ?? 10;
    context.current_tool_count < max_tools
}

policy is_tool_approved(tool_metadata map) {
    tool_metadata.approval_status == "approved" ||
    tool_metadata.category in ["google", "microsoft", "standard"]
}
```

---

## Implementation Guide

### Phase 1: Schema Setup (Week 1)

#### 1.1 Create FGA Schema

```python
# automagik_tools/hub/rbac/schema.py
from workos import WorkOSClient

async def initialize_fga_schema():
    """Initialize WorkOS FGA schema for Hub RBAC."""
    workos = WorkOSClient(api_key=os.getenv("WORKOS_API_KEY"))

    # Load schema from file
    schema_path = Path(__file__).parent / "fga_schema.txt"
    with open(schema_path) as f:
        schema = f.read()

    # Apply schema
    await workos.fga.schema.apply(schema)
    print("✅ FGA schema initialized")
```

#### 1.2 Create Role Templates

```python
# automagik_tools/hub/rbac/roles.py
from enum import Enum
from typing import List, Dict, Any

class HubRole(str, Enum):
    HUB_ADMIN = "hub-admin"
    TEAM_MANAGER = "team-manager"
    POWER_USER = "power-user"
    STANDARD_USER = "standard-user"
    VIEWER = "viewer"

ROLE_PERMISSIONS: Dict[HubRole, List[str]] = {
    HubRole.HUB_ADMIN: [
        "tools:read", "tools:add:any", "tools:configure:advanced", "tools:delete",
        "tools:execute", "credentials:read", "credentials:create",
        "credentials:update", "credentials:delete", "credentials:share",
        "users:read:all", "users:manage", "roles:read", "roles:assign",
        "teams:read", "teams:manage", "admin:audit:all", "admin:settings",
        "admin:billing", "admin:security"
    ],
    HubRole.TEAM_MANAGER: [
        "tools:read", "tools:add:any", "tools:configure:advanced", "tools:delete",
        "tools:execute", "credentials:read", "credentials:create",
        "credentials:update", "credentials:delete", "credentials:share",
        "users:read", "roles:read", "teams:read", "admin:audit"
    ],
    HubRole.POWER_USER: [
        "tools:read", "tools:add:any", "tools:configure:advanced", "tools:delete",
        "tools:execute", "credentials:read", "credentials:create",
        "credentials:update", "credentials:delete"
    ],
    HubRole.STANDARD_USER: [
        "tools:read", "tools:add", "tools:configure", "tools:delete",
        "tools:execute", "credentials:read", "credentials:create",
        "credentials:update", "credentials:delete"
    ],
    HubRole.VIEWER: [
        "tools:read", "credentials:read"
    ]
}

def get_role_metadata(role: HubRole) -> Dict[str, Any]:
    """Get role metadata for display."""
    metadata = {
        HubRole.HUB_ADMIN: {
            "name": "Hub Administrator",
            "description": "Full system access and control",
            "color": "#DC2626",  # Red
            "icon": "shield-check"
        },
        HubRole.TEAM_MANAGER: {
            "name": "Team Manager",
            "description": "Manage team members and tools",
            "color": "#EA580C",  # Orange
            "icon": "users"
        },
        HubRole.POWER_USER: {
            "name": "Power User",
            "description": "Advanced tool access and configuration",
            "color": "#2563EB",  # Blue
            "icon": "zap"
        },
        HubRole.STANDARD_USER: {
            "name": "Standard User",
            "description": "Personal tool collection management",
            "color": "#059669",  # Green
            "icon": "user"
        },
        HubRole.VIEWER: {
            "name": "Viewer",
            "description": "Read-only access",
            "color": "#6B7280",  # Gray
            "icon": "eye"
        }
    }
    return metadata[role]
```

### Phase 2: Authorization Middleware (Week 1-2)

#### 2.1 Create Authorization Checker

```python
# automagik_tools/hub/rbac/checker.py
from workos import WorkOSClient
from fastmcp import Context
from typing import Optional, Dict, Any

class AuthorizationChecker:
    """Check user permissions using WorkOS FGA."""

    def __init__(self):
        self.workos = WorkOSClient(api_key=os.getenv("WORKOS_API_KEY"))

    async def check_permission(
        self,
        ctx: Context,
        permission: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Check if user has a specific permission.

        Args:
            ctx: FastMCP context with user info
            permission: Permission to check (e.g., "tools:add")
            resource_type: Optional resource type for fine-grained checks
            resource_id: Optional resource ID
            context: Additional context for policy evaluation
        """
        user_id = ctx.get_state("user_id")
        org_id = ctx.get_state("organization_id")

        if not user_id:
            return False

        # Build check request
        check_data = {
            "resource_type": resource_type or "permission",
            "resource_id": resource_id or permission,
            "relation": "granted",
            "subject": {
                "resource_type": "user",
                "resource_id": user_id
            }
        }

        # Add context for policy evaluation
        if context:
            check_data["context"] = context

        # Perform FGA check
        result = await self.workos.fga.check(**check_data)
        return result.result == "authorized"

    async def check_tool_access(
        self,
        ctx: Context,
        tool_name: str,
        action: str  # "read", "add", "configure", "delete", "execute"
    ) -> bool:
        """Check if user can perform action on a tool."""
        # Get user metadata
        user_id = ctx.get_state("user_id")
        user_metadata = await self._get_user_metadata(user_id)
        tool_metadata = await self._get_tool_metadata(tool_name)

        # Check permission with context
        permission = f"tools:{action}"
        context = {
            "user_metadata": user_metadata,
            "tool_metadata": tool_metadata,
            "current_tool_count": await self._get_user_tool_count(user_id)
        }

        return await self.check_permission(
            ctx,
            permission,
            context=context
        )

    async def get_user_permissions(self, ctx: Context) -> List[str]:
        """Get all permissions for current user."""
        user_id = ctx.get_state("user_id")

        # Query all permissions
        query = f"select permission where user:{user_id} is granted"
        results = await self.workos.fga.query(q=query)

        return [r.resource_id for r in results.data]

# Global instance
auth_checker = AuthorizationChecker()
```

#### 2.2 Create Permission Decorator

```python
# automagik_tools/hub/rbac/decorators.py
from functools import wraps
from fastmcp import Context
from .checker import auth_checker

def require_permission(permission: str, resource_type: str = None):
    """Decorator to enforce permission checks on MCP tools."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, ctx: Context = None, **kwargs):
            if not ctx:
                raise ValueError("Context required for permission check")

            # Check permission
            has_permission = await auth_checker.check_permission(
                ctx, permission, resource_type
            )

            if not has_permission:
                raise PermissionError(
                    f"User does not have required permission: {permission}"
                )

            # Call original function
            return await func(*args, ctx=ctx, **kwargs)

        return wrapper
    return decorator

def require_tool_action(action: str):
    """Decorator for tool-specific actions."""
    def decorator(func):
        @wraps(func)
        async def wrapper(tool_name: str, *args, ctx: Context = None, **kwargs):
            if not ctx:
                raise ValueError("Context required for permission check")

            # Check tool access
            has_access = await auth_checker.check_tool_access(
                ctx, tool_name, action
            )

            if not has_access:
                raise PermissionError(
                    f"User cannot {action} tool: {tool_name}"
                )

            return await func(tool_name, *args, ctx=ctx, **kwargs)

        return wrapper
    return decorator
```

### Phase 3: Update Hub Tools (Week 2)

#### 3.1 Add Authorization to Existing Tools

```python
# automagik_tools/hub/tools.py
from .rbac.decorators import require_permission, require_tool_action

@require_permission("tools:read")
async def get_available_tools(ctx: Context) -> List[Dict[str, Any]]:
    """List all tools available in the repository."""
    # ... existing implementation

@require_tool_action("add")
async def add_tool(tool_name: str, config: Dict[str, Any], ctx: Context) -> str:
    """Add a tool to personal collection."""
    # Check if tool requires approval
    tool_metadata = await get_tool_metadata(tool_name)

    # Additional policy check for restricted tools
    if tool_metadata.get("restricted"):
        has_advanced = await auth_checker.check_permission(
            ctx, "tools:add:any"
        )
        if not has_advanced:
            raise PermissionError(
                f"Tool {tool_name} requires 'tools:add:any' permission"
            )

    # ... existing implementation

@require_tool_action("delete")
async def remove_tool(tool_name: str, ctx: Context) -> str:
    """Remove a tool from personal collection."""
    # ... existing implementation

@require_tool_action("configure")
async def update_tool_config(
    tool_name: str,
    config: Dict[str, Any],
    ctx: Context
) -> str:
    """Update tool configuration."""
    # Check for advanced configuration fields
    advanced_fields = {"api_endpoint", "custom_auth", "webhook_url"}
    updating_advanced = any(field in config for field in advanced_fields)

    if updating_advanced:
        has_advanced = await auth_checker.check_permission(
            ctx, "tools:configure:advanced"
        )
        if not has_advanced:
            raise PermissionError(
                "Updating advanced fields requires 'tools:configure:advanced' permission"
            )

    # ... existing implementation
```

### Phase 4: User Management API (Week 2-3)

#### 4.1 Role Assignment Endpoints

```python
# automagik_tools/hub/admin_routes.py
from fastapi import APIRouter, Depends, HTTPException
from .rbac.checker import auth_checker
from .rbac.roles import HubRole, ROLE_PERMISSIONS

router = APIRouter(prefix="/admin", tags=["admin"])

@router.post("/users/{user_id}/roles")
async def assign_role(
    user_id: str,
    role: HubRole,
    ctx: Context = Depends(get_context)
):
    """Assign a role to a user (requires roles:assign permission)."""
    # Check permission
    if not await auth_checker.check_permission(ctx, "roles:assign"):
        raise HTTPException(403, "Insufficient permissions")

    # Create warrants for all role permissions
    workos = WorkOSClient(api_key=os.getenv("WORKOS_API_KEY"))
    org_id = ctx.get_state("organization_id")

    # Assign user to role
    await workos.fga.warrant.create(
        resource_type="role",
        resource_id=role.value,
        relation="member",
        subject={
            "resource_type": "user",
            "resource_id": user_id
        }
    )

    # Create permission warrants
    for permission in ROLE_PERMISSIONS[role]:
        await workos.fga.warrant.create(
            resource_type="permission",
            resource_id=permission,
            relation="holder",
            subject={
                "resource_type": "role",
                "resource_id": role.value,
                "relation": "member"
            }
        )

    return {"message": f"Role {role.value} assigned to user {user_id}"}

@router.delete("/users/{user_id}/roles/{role}")
async def revoke_role(
    user_id: str,
    role: HubRole,
    ctx: Context = Depends(get_context)
):
    """Revoke a role from a user."""
    if not await auth_checker.check_permission(ctx, "roles:assign"):
        raise HTTPException(403, "Insufficient permissions")

    workos = WorkOSClient(api_key=os.getenv("WORKOS_API_KEY"))

    await workos.fga.warrant.delete(
        resource_type="role",
        resource_id=role.value,
        relation="member",
        subject={
            "resource_type": "user",
            "resource_id": user_id
        }
    )

    return {"message": f"Role {role.value} revoked from user {user_id}"}

@router.get("/users/{user_id}/permissions")
async def get_user_permissions(
    user_id: str,
    ctx: Context = Depends(get_context)
):
    """Get all permissions for a user."""
    if not await auth_checker.check_permission(ctx, "users:read"):
        raise HTTPException(403, "Insufficient permissions")

    permissions = await auth_checker.get_user_permissions(ctx)
    return {"user_id": user_id, "permissions": permissions}
```

---

## User Experience

### 1. Permission-Based UI Rendering

The Hub UI should dynamically show/hide features based on user permissions:

```typescript
// hub_ui/src/composables/usePermissions.ts
import { ref, computed } from 'vue'
import { useAuth } from './useAuth'

export function usePermissions() {
  const { user } = useAuth()
  const permissions = ref<string[]>([])

  async function loadPermissions() {
    const response = await fetch('/api/users/me/permissions')
    permissions.value = await response.json()
  }

  function hasPermission(permission: string): boolean {
    return permissions.value.includes(permission)
  }

  const canAddTools = computed(() =>
    hasPermission('tools:add') || hasPermission('tools:add:any')
  )

  const canConfigureAdvanced = computed(() =>
    hasPermission('tools:configure:advanced')
  )

  const canManageUsers = computed(() =>
    hasPermission('users:manage')
  )

  return {
    permissions,
    loadPermissions,
    hasPermission,
    canAddTools,
    canConfigureAdvanced,
    canManageUsers
  }
}
```

### 2. Error Messages

Clear, actionable error messages for permission denials:

```typescript
// hub_ui/src/utils/errors.ts
export function formatPermissionError(error: PermissionError): string {
  const messages = {
    'tools:add': 'You need "Add Tools" permission. Contact your administrator.',
    'tools:add:any': 'This is a restricted tool. Request "Power User" role from your team manager.',
    'tools:configure:advanced': 'Advanced configuration requires "Power User" role.',
    'users:manage': 'User management is restricted to Hub Administrators.',
    'credentials:share': 'Only Team Managers can share credentials.'
  }

  return messages[error.permission] ||
    `You don't have permission to perform this action. Required: ${error.permission}`
}
```

### 3. Role Badge Display

Visual indicators for user roles:

```vue
<!-- hub_ui/src/components/RoleBadge.vue -->
<template>
  <span
    :class="['role-badge', `role-${role}`]"
    :style="{ backgroundColor: metadata.color }"
  >
    <Icon :name="metadata.icon" />
    {{ metadata.name }}
  </span>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { getRoleMetadata } from '@/utils/roles'

const props = defineProps<{ role: string }>()
const metadata = computed(() => getRoleMetadata(props.role))
</script>
```

### 4. Admin Dashboard

For Hub Admins and Team Managers:

```vue
<!-- hub_ui/src/views/AdminDashboard.vue -->
<template>
  <div class="admin-dashboard">
    <h1>User Management</h1>

    <UserList
      v-if="canManageUsers"
      @assign-role="handleRoleAssignment"
      @revoke-role="handleRoleRevocation"
    />

    <div v-else class="permission-required">
      <Icon name="lock" />
      <p>You need administrator permissions to access this page.</p>
    </div>

    <AuditLog v-if="canViewAudit" />
  </div>
</template>
```

---

## Migration Strategy

### Phase 1: Preparation (Week 1)

**Objective**: Set up FGA infrastructure without breaking existing functionality

1. **Deploy FGA Schema**
   - Create and apply WorkOS FGA schema
   - Test schema with sample warrants
   - Validate inheritance rules

2. **Implement Authorization Layer**
   - Add AuthorizationChecker class
   - Create permission decorators
   - Do NOT enforce yet (log-only mode)

3. **Logging Mode**
   ```python
   # During migration, log instead of blocking
   async def check_permission(ctx, permission, enforce=False):
       has_permission = await _check_fga(ctx, permission)

       if not has_permission:
           logger.warning(f"Permission denied (not enforced): {permission}")
           if enforce:
               raise PermissionError(permission)

       return True  # Always return True during migration
   ```

### Phase 2: Initial Deployment (Week 2)

**Objective**: Assign default roles to existing users

1. **User Audit**
   - Export all existing users from AuthKit
   - Categorize by usage patterns:
     - Active tool users → `standard-user`
     - High usage (>10 tools) → `power-user`
     - First users / system owners → `hub-admin`

2. **Batch Role Assignment**
   ```python
   async def migrate_existing_users():
       """Assign default roles to existing users."""
       workos = WorkOSClient(api_key=os.getenv("WORKOS_API_KEY"))

       # Get all users
       users = await get_all_hub_users()

       for user in users:
           # Determine default role
           if user.email in ADMIN_EMAILS:
               role = HubRole.HUB_ADMIN
           elif user.tool_count > 10:
               role = HubRole.POWER_USER
           else:
               role = HubRole.STANDARD_USER

           # Assign role
           await assign_role(user.id, role)
           logger.info(f"Assigned {role} to {user.email}")
   ```

3. **Communication**
   - Email all users about new RBAC system
   - Explain their assigned role
   - Provide link to role documentation
   - Include process for requesting role changes

### Phase 3: Gradual Enforcement (Week 3-4)

**Objective**: Enable enforcement for low-risk operations first

1. **Week 3: Read Operations**
   - Enforce permissions for viewing users
   - Enforce permissions for viewing audit logs
   - Low risk - no data modification

2. **Week 4: Write Operations**
   - Enforce permissions for tool management
   - Enforce permissions for credential management
   - Monitor error rates closely

3. **Rollback Plan**
   ```python
   # Feature flag for quick rollback
   ENFORCE_RBAC = os.getenv("ENFORCE_RBAC", "false").lower() == "true"

   async def check_permission(ctx, permission):
       if not ENFORCE_RBAC:
           return True  # Open access mode

       return await _check_fga(ctx, permission)
   ```

### Phase 4: Full Enforcement (Week 5)

**Objective**: Complete migration to RBAC

1. **Enable Full Enforcement**
   - Set `ENFORCE_RBAC=true`
   - Remove fallback logic
   - Monitor for 48 hours

2. **User Support**
   - Create role request form
   - Provide admin dashboard for role management
   - Set up Slack channel for RBAC questions

3. **Documentation**
   - Update all docs to reflect RBAC
   - Create role comparison chart
   - Document permission request process

---

## Security Considerations

### 1. Principle of Least Privilege

- **Default Role**: New users get `standard-user` (not `power-user`)
- **Explicit Grants**: No implicit role assignments
- **Regular Audits**: Quarterly review of user roles

### 2. Sensitive Operations

High-risk operations require additional checks:

```python
# Require MFA for admin operations
@require_permission("users:manage")
@require_mfa
async def delete_user(user_id: str, ctx: Context):
    """Delete user (requires MFA)."""
    pass

# Rate limit role assignments
@rate_limit(max_requests=10, window=3600)  # 10 per hour
async def assign_role(user_id: str, role: HubRole, ctx: Context):
    """Assign role (rate limited)."""
    pass
```

### 3. Audit Logging

All authorization decisions must be logged:

```python
class AuditLogger:
    async def log_auth_check(
        self,
        user_id: str,
        permission: str,
        resource: str,
        result: bool,
        reason: Optional[str] = None
    ):
        """Log authorization check for audit trail."""
        await self.db.audit_logs.insert({
            "timestamp": datetime.now(timezone.utc),
            "user_id": user_id,
            "permission": permission,
            "resource": resource,
            "result": "allowed" if result else "denied",
            "reason": reason,
            "ip_address": get_client_ip(),
            "user_agent": get_user_agent()
        })
```

### 4. Credential Isolation

Users can only access their own credentials:

```python
async def get_credential(tool_name: str, ctx: Context):
    """Get credential with ownership check."""
    user_id = ctx.get_state("user_id")

    # Check ownership via FGA
    has_access = await workos.fga.check(
        resource_type="credential",
        resource_id=f"{user_id}:{tool_name}",
        relation="accessor",
        subject={"resource_type": "user", "resource_id": user_id}
    )

    if not has_access:
        raise PermissionError("Credential not found or access denied")

    return await db.credentials.find_one({
        "user_id": user_id,
        "tool_name": tool_name
    })
```

### 5. Tool Execution Sandboxing

Tools execute with user's permissions only:

```python
class HubToolWrapper:
    """Wrapper that enforces user context for tool execution."""

    @staticmethod
    def wrap(tool_name: str, original_fn):
        async def wrapped(*args, ctx: Context, **kwargs):
            # Check execution permission
            if not await auth_checker.check_tool_access(ctx, tool_name, "execute"):
                raise PermissionError(f"Cannot execute tool: {tool_name}")

            # Inject user credentials
            user_id = ctx.get_state("user_id")
            credentials = await get_user_credentials(user_id, tool_name)

            # Execute with user context
            return await original_fn(*args, credentials=credentials, **kwargs)

        return wrapped
```

---

## Testing Strategy

### 1. Unit Tests

```python
# tests/test_rbac.py
import pytest
from automagik_tools.hub.rbac.checker import auth_checker

@pytest.mark.asyncio
async def test_standard_user_can_add_approved_tools():
    """Standard users can add approved tools."""
    ctx = create_mock_context(role="standard-user")

    result = await auth_checker.check_tool_access(
        ctx, "google-calendar", "add"
    )

    assert result is True

@pytest.mark.asyncio
async def test_standard_user_cannot_add_restricted_tools():
    """Standard users cannot add restricted tools."""
    ctx = create_mock_context(role="standard-user")

    result = await auth_checker.check_tool_access(
        ctx, "admin-api", "add"
    )

    assert result is False

@pytest.mark.asyncio
async def test_power_user_can_add_any_tool():
    """Power users can add restricted tools."""
    ctx = create_mock_context(role="power-user")

    result = await auth_checker.check_tool_access(
        ctx, "admin-api", "add"
    )

    assert result is True
```

### 2. Integration Tests

```python
@pytest.mark.integration
async def test_role_assignment_flow():
    """Test complete role assignment flow."""
    # Create test user
    user = await create_test_user()

    # Assign power-user role
    await assign_role(user.id, HubRole.POWER_USER)

    # Verify permissions
    permissions = await get_user_permissions(user.id)
    assert "tools:add:any" in permissions
    assert "tools:configure:advanced" in permissions

    # Revoke role
    await revoke_role(user.id, HubRole.POWER_USER)

    # Verify permissions removed
    permissions = await get_user_permissions(user.id)
    assert "tools:add:any" not in permissions
```

### 3. Load Tests

```python
@pytest.mark.load
async def test_authorization_performance():
    """Ensure authorization checks don't degrade performance."""
    ctx = create_mock_context(role="power-user")

    start = time.time()

    # Perform 1000 checks
    for i in range(1000):
        await auth_checker.check_permission(ctx, "tools:read")

    duration = time.time() - start

    # Should complete in < 1 second
    assert duration < 1.0
```

---

## Monitoring & Alerting

### Key Metrics

1. **Authorization Failures**
   - Track permission denials by permission type
   - Alert on spike in denials (possible attack)

2. **Role Distribution**
   - Monitor role assignment patterns
   - Alert on unusual admin role grants

3. **Performance**
   - P95 latency for FGA checks
   - FGA API error rate

### Dashboard

```yaml
# Grafana dashboard config
Dashboard: Hub RBAC
Panels:
  - Authorization Checks (rate)
  - Permission Denials by Type (breakdown)
  - FGA Check Latency (P50, P95, P99)
  - Active Users by Role (pie chart)
  - Role Assignments (timeline)
Alerts:
  - Authorization failure rate > 5%
  - FGA check P95 > 200ms
  - Admin role granted (notify security team)
```

---

## Cost Estimate

### WorkOS FGA Pricing

**Based on**: [WorkOS Pricing](https://workos.com/pricing)

- **Free Tier**: Up to 1M FGA checks/month
- **Growth**: $0.005 per 1K checks after 1M
- **Enterprise**: Custom pricing

### Expected Usage

For a Hub with 100 active users:

```
Calculations:
- 100 users × 50 tool operations/day = 5,000 operations/day
- 5,000 operations × 2 FGA checks/operation = 10,000 checks/day
- 10,000 checks/day × 30 days = 300,000 checks/month

Result: Well within free tier (1M checks/month)
```

For 1,000 users:
- 3M checks/month
- Cost: (3M - 1M) / 1000 × $0.005 = **$10/month**

---

## Conclusion

This RBAC design provides:

✅ **Security**: Fine-grained permissions prevent unauthorized access
✅ **Flexibility**: Roles adapt to different organizational structures
✅ **Scalability**: WorkOS FGA handles millions of authorization checks
✅ **Auditability**: Complete trail of authorization decisions
✅ **Usability**: Clear roles and intuitive permissions
✅ **Migration Path**: Gradual rollout minimizes disruption

### Next Steps

1. **Review with team**: Gather feedback on role definitions
2. **Test schema**: Validate FGA schema in staging environment
3. **Implement Phase 1**: Deploy authorization layer (log-only mode)
4. **User communication**: Notify users of upcoming RBAC rollout
5. **Phased enforcement**: Gradually enable permission checks
6. **Monitor & iterate**: Adjust roles/permissions based on usage

---

## Appendix

### A. Permission Matrix

| Permission | Viewer | Standard | Power | Team Mgr | Admin |
|------------|--------|----------|-------|----------|-------|
| tools:read | ✅ | ✅ | ✅ | ✅ | ✅ |
| tools:add | ❌ | ✅ | ✅ | ✅ | ✅ |
| tools:add:any | ❌ | ❌ | ✅ | ✅ | ✅ |
| tools:configure | ❌ | ✅ | ✅ | ✅ | ✅ |
| tools:configure:advanced | ❌ | ❌ | ✅ | ✅ | ✅ |
| tools:delete | ❌ | ✅ | ✅ | ✅ | ✅ |
| tools:execute | ❌ | ✅ | ✅ | ✅ | ✅ |
| credentials:read | ✅ | ✅ | ✅ | ✅ | ✅ |
| credentials:create | ❌ | ✅ | ✅ | ✅ | ✅ |
| credentials:update | ❌ | ✅ | ✅ | ✅ | ✅ |
| credentials:delete | ❌ | ✅ | ✅ | ✅ | ✅ |
| credentials:share | ❌ | ❌ | ❌ | ✅ | ✅ |
| users:read | ❌ | ❌ | ❌ | ✅ | ✅ |
| users:read:all | ❌ | ❌ | ❌ | ❌ | ✅ |
| users:manage | ❌ | ❌ | ❌ | ❌ | ✅ |
| roles:read | ❌ | ❌ | ❌ | ✅ | ✅ |
| roles:assign | ❌ | ❌ | ❌ | ❌ | ✅ |
| teams:read | ❌ | ❌ | ❌ | ✅ | ✅ |
| teams:manage | ❌ | ❌ | ❌ | ❌ | ✅ |
| admin:audit | ❌ | ❌ | ❌ | ✅ | ✅ |
| admin:audit:all | ❌ | ❌ | ❌ | ❌ | ✅ |
| admin:settings | ❌ | ❌ | ❌ | ❌ | ✅ |
| admin:billing | ❌ | ❌ | ❌ | ❌ | ✅ |
| admin:security | ❌ | ❌ | ❌ | ❌ | ✅ |

### B. Common Workflows

**New Employee Onboarding**:
1. User signs up via AuthKit
2. Auto-assigned `standard-user` role
3. Can immediately add approved tools
4. Manager can upgrade to `power-user` if needed

**Team Lead Promotion**:
1. Admin assigns `team-manager` role
2. User gains team management permissions
3. Can now assign tools to team members
4. Can view team audit logs

**Security Audit**:
1. Security team requests audit log access
2. Admin assigns temporary `viewer` role
3. Security team reviews logs
4. Role revoked after audit complete

### C. FAQ

**Q: Can a user have multiple roles?**
A: Yes. WorkOS FGA supports multiple role assignments. Permissions are additive.

**Q: How quickly do permission changes take effect?**
A: Immediately. WorkOS FGA checks are real-time.

**Q: What happens if FGA is unavailable?**
A: Implement fallback: fail-safe (deny) or fail-open (allow) based on operation risk.

**Q: Can permissions be temporary?**
A: Yes. Use warrant policies with time-based conditions:
```python
policy = f"date() < date('{expiration_date}')"
```

**Q: How do we handle service accounts?**
A: Create `service-account` resource type with its own permissions:
```fga
type service_account
    relation owner [user]
    relation executor []
```

---

**Document Version**: 1.0
**Last Updated**: 2025-01-25
**Author**: Product Manager (Council)
**Status**: Ready for Review
