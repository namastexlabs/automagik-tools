"""Initial migration with multi-tenant WorkOS support

Revision ID: 001_initial
Revises:
Create Date: 2025-11-25 17:00:00.000000

This is the unified initial migration that includes:
- Core tool management tables (tool_presets, tool_registry, users, oauth_tokens, etc.)
- Multi-tenant workspaces with WorkOS integration
- Directory sync support for Google Workspace
- Audit logging for compliance

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # =========================================================================
    # CORE TABLES - Tool Registry & Presets
    # =========================================================================

    op.create_table('tool_presets',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('preset_name', sa.String(length=100), nullable=False),
        sa.Column('display_name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('tools', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('preset_name')
    )

    op.create_table('tool_registry',
        sa.Column('tool_name', sa.String(length=100), nullable=False),
        sa.Column('display_name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('auth_type', sa.String(length=20), nullable=False),
        sa.Column('config_schema', sa.JSON(), nullable=False),
        sa.Column('required_oauth', sa.JSON(), nullable=True),
        sa.Column('icon_url', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('tool_name')
    )

    # =========================================================================
    # MULTI-TENANT - Workspaces
    # =========================================================================

    op.create_table('workspaces',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('slug', sa.String(length=100), nullable=False),
        sa.Column('owner_id', sa.String(length=36), nullable=True),
        sa.Column('workos_org_id', sa.String(length=100), nullable=True),
        sa.Column('settings', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug'),
        sa.UniqueConstraint('workos_org_id')
    )
    op.create_index('idx_workspaces_slug', 'workspaces', ['slug'], unique=True)

    # =========================================================================
    # USERS - With WorkOS & Multi-Tenant Support
    # =========================================================================

    op.create_table('users',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('first_name', sa.String(length=255), nullable=True),
        sa.Column('last_name', sa.String(length=255), nullable=True),
        sa.Column('workspace_id', sa.String(length=36), nullable=True),
        sa.Column('workos_user_id', sa.String(length=100), nullable=True),
        sa.Column('role', sa.String(length=50), nullable=False, server_default='workspace_owner'),
        sa.Column('is_super_admin', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('mfa_enabled', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('directory_synced', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('directory_user_id', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    op.create_index('idx_users_workos_user_id', 'users', ['workos_user_id'], unique=True)
    op.create_index('idx_users_workspace', 'users', ['workspace_id'], unique=False)

    # Note: Circular FK (workspaces.owner_id -> users.id) not added due to SQLite limitations
    # The application enforces this relationship at runtime

    # =========================================================================
    # OAUTH TOKENS - With Workspace Isolation
    # =========================================================================

    op.create_table('oauth_tokens',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('workspace_id', sa.String(length=36), nullable=True),
        sa.Column('tool_name', sa.String(length=100), nullable=False),
        sa.Column('provider', sa.String(length=50), nullable=False),
        sa.Column('access_token', sa.Text(), nullable=False),
        sa.Column('refresh_token', sa.Text(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('scopes', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_oauth_tokens_lookup', 'oauth_tokens', ['user_id', 'tool_name'], unique=False)
    op.create_index('idx_oauth_tokens_unique', 'oauth_tokens', ['user_id', 'tool_name', 'provider'], unique=True)

    # =========================================================================
    # TOOL CONFIGS - With Workspace Isolation
    # =========================================================================

    op.create_table('tool_configs',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('workspace_id', sa.String(length=36), nullable=True),
        sa.Column('tool_name', sa.String(length=100), nullable=False),
        sa.Column('config_key', sa.String(length=100), nullable=False),
        sa.Column('config_value', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_tool_configs_lookup', 'tool_configs', ['user_id', 'tool_name'], unique=False)
    op.create_index('idx_tool_configs_unique', 'tool_configs', ['user_id', 'tool_name', 'config_key'], unique=True)

    # =========================================================================
    # USER TOOLS - With Workspace Isolation
    # =========================================================================

    op.create_table('user_tools',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('workspace_id', sa.String(length=36), nullable=True),
        sa.Column('tool_name', sa.String(length=100), nullable=False),
        sa.Column('enabled', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_user_tools_lookup', 'user_tools', ['user_id', 'enabled'], unique=False)
    op.create_index('idx_user_tools_unique', 'user_tools', ['user_id', 'tool_name'], unique=True)

    # =========================================================================
    # DIRECTORY SYNC - Google Workspace / WorkOS Directory
    # =========================================================================

    op.create_table('directory_sync_users',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('workspace_id', sa.String(length=36), nullable=False),
        sa.Column('directory_user_id', sa.String(length=100), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('first_name', sa.String(length=255), nullable=True),
        sa.Column('last_name', sa.String(length=255), nullable=True),
        sa.Column('state', sa.String(length=20), nullable=False, server_default='active'),
        sa.Column('raw_attributes', sa.JSON(), nullable=True),
        sa.Column('synced_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('directory_user_id')
    )
    op.create_index('idx_directory_sync_users_workspace', 'directory_sync_users', ['workspace_id'], unique=False)
    op.create_index('idx_directory_sync_users_email', 'directory_sync_users', ['email'], unique=False)

    op.create_table('directory_groups',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('workspace_id', sa.String(length=36), nullable=False),
        sa.Column('directory_group_id', sa.String(length=100), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('raw_attributes', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('directory_group_id')
    )
    op.create_index('idx_directory_groups_workspace', 'directory_groups', ['workspace_id'], unique=False)

    op.create_table('directory_group_memberships',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('group_id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['group_id'], ['directory_groups.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['directory_sync_users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_directory_memberships_group', 'directory_group_memberships', ['group_id'], unique=False)
    op.create_index('idx_directory_memberships_user', 'directory_group_memberships', ['user_id'], unique=False)
    op.create_index('idx_directory_memberships_unique', 'directory_group_memberships', ['group_id', 'user_id'], unique=True)

    # =========================================================================
    # AUDIT LOGS - Compliance & Security Tracking
    # =========================================================================

    op.create_table('audit_logs',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('workspace_id', sa.String(length=36), nullable=True),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('actor_id', sa.String(length=36), nullable=True),
        sa.Column('actor_email', sa.String(length=255), nullable=True),
        sa.Column('actor_type', sa.String(length=20), nullable=False, server_default='user'),
        sa.Column('target_type', sa.String(length=50), nullable=True),
        sa.Column('target_id', sa.String(length=36), nullable=True),
        sa.Column('target_name', sa.String(length=255), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('request_id', sa.String(length=36), nullable=True),
        sa.Column('event_metadata', sa.JSON(), nullable=True),
        sa.Column('success', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('occurred_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_audit_logs_workspace', 'audit_logs', ['workspace_id'], unique=False)
    op.create_index('idx_audit_logs_action', 'audit_logs', ['action'], unique=False)
    op.create_index('idx_audit_logs_category', 'audit_logs', ['category'], unique=False)
    op.create_index('idx_audit_logs_occurred', 'audit_logs', ['occurred_at'], unique=False)
    op.create_index('idx_audit_logs_actor', 'audit_logs', ['actor_id'], unique=False)


def downgrade() -> None:
    # Drop audit logs
    op.drop_index('idx_audit_logs_actor', table_name='audit_logs')
    op.drop_index('idx_audit_logs_occurred', table_name='audit_logs')
    op.drop_index('idx_audit_logs_category', table_name='audit_logs')
    op.drop_index('idx_audit_logs_action', table_name='audit_logs')
    op.drop_index('idx_audit_logs_workspace', table_name='audit_logs')
    op.drop_table('audit_logs')

    # Drop directory sync tables
    op.drop_index('idx_directory_memberships_unique', table_name='directory_group_memberships')
    op.drop_index('idx_directory_memberships_user', table_name='directory_group_memberships')
    op.drop_index('idx_directory_memberships_group', table_name='directory_group_memberships')
    op.drop_table('directory_group_memberships')

    op.drop_index('idx_directory_groups_workspace', table_name='directory_groups')
    op.drop_table('directory_groups')

    op.drop_index('idx_directory_sync_users_email', table_name='directory_sync_users')
    op.drop_index('idx_directory_sync_users_workspace', table_name='directory_sync_users')
    op.drop_table('directory_sync_users')

    # Drop user tools
    op.drop_index('idx_user_tools_unique', table_name='user_tools')
    op.drop_index('idx_user_tools_lookup', table_name='user_tools')
    op.drop_table('user_tools')

    # Drop tool configs
    op.drop_index('idx_tool_configs_unique', table_name='tool_configs')
    op.drop_index('idx_tool_configs_lookup', table_name='tool_configs')
    op.drop_table('tool_configs')

    # Drop oauth tokens
    op.drop_index('idx_oauth_tokens_unique', table_name='oauth_tokens')
    op.drop_index('idx_oauth_tokens_lookup', table_name='oauth_tokens')
    op.drop_table('oauth_tokens')

    # Drop users
    op.drop_index('idx_users_workspace', table_name='users')
    op.drop_index('idx_users_workos_user_id', table_name='users')
    op.drop_table('users')

    # Drop workspaces
    op.drop_index('idx_workspaces_slug', table_name='workspaces')
    op.drop_table('workspaces')

    # Drop tool tables
    op.drop_table('tool_registry')
    op.drop_table('tool_presets')
