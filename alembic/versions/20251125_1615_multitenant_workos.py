"""Multi-tenant WorkOS integration

Revision ID: 3b899fb47f9b
Revises: 2a788fa36f8a
Create Date: 2025-11-25 16:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3b899fb47f9b'
down_revision: Union[str, None] = '2a788fa36f8a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create workspaces table first (users will reference it)
    op.create_table('workspaces',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('slug', sa.String(length=100), nullable=False),
        sa.Column('owner_id', sa.String(length=36), nullable=True),  # Will be updated after users table
        sa.Column('workos_org_id', sa.String(length=100), nullable=True),
        sa.Column('settings', sa.JSON(), nullable=True, default={}),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug'),
        sa.UniqueConstraint('workos_org_id')
    )
    op.create_index('idx_workspaces_slug', 'workspaces', ['slug'], unique=True)

    # Add new columns to users table
    op.add_column('users', sa.Column('workspace_id', sa.String(length=36), nullable=True))
    op.add_column('users', sa.Column('workos_user_id', sa.String(length=100), nullable=True))
    op.add_column('users', sa.Column('role', sa.String(length=50), nullable=False, server_default='workspace_owner'))
    op.add_column('users', sa.Column('is_super_admin', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('users', sa.Column('mfa_enabled', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('users', sa.Column('directory_synced', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('users', sa.Column('directory_user_id', sa.String(length=100), nullable=True))

    # Create foreign key from users to workspaces
    op.create_foreign_key('fk_users_workspace', 'users', 'workspaces', ['workspace_id'], ['id'])

    # Create foreign key from workspaces to users for owner
    op.create_foreign_key('fk_workspaces_owner', 'workspaces', 'users', ['owner_id'], ['id'])

    # Create index on workos_user_id for quick lookups
    op.create_index('idx_users_workos_user_id', 'users', ['workos_user_id'], unique=True)
    op.create_index('idx_users_workspace', 'users', ['workspace_id'], unique=False)

    # Add workspace_id to user_tools
    op.add_column('user_tools', sa.Column('workspace_id', sa.String(length=36), nullable=True))
    op.create_foreign_key('fk_user_tools_workspace', 'user_tools', 'workspaces', ['workspace_id'], ['id'])

    # Add workspace_id to tool_configs
    op.add_column('tool_configs', sa.Column('workspace_id', sa.String(length=36), nullable=True))
    op.create_foreign_key('fk_tool_configs_workspace', 'tool_configs', 'workspaces', ['workspace_id'], ['id'])

    # Add workspace_id to oauth_tokens
    op.add_column('oauth_tokens', sa.Column('workspace_id', sa.String(length=36), nullable=True))
    op.create_foreign_key('fk_oauth_tokens_workspace', 'oauth_tokens', 'workspaces', ['workspace_id'], ['id'])

    # Create directory sync tables
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

    # Create audit logs table
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

    # Remove workspace_id from oauth_tokens
    op.drop_constraint('fk_oauth_tokens_workspace', 'oauth_tokens', type_='foreignkey')
    op.drop_column('oauth_tokens', 'workspace_id')

    # Remove workspace_id from tool_configs
    op.drop_constraint('fk_tool_configs_workspace', 'tool_configs', type_='foreignkey')
    op.drop_column('tool_configs', 'workspace_id')

    # Remove workspace_id from user_tools
    op.drop_constraint('fk_user_tools_workspace', 'user_tools', type_='foreignkey')
    op.drop_column('user_tools', 'workspace_id')

    # Remove columns from users
    op.drop_index('idx_users_workspace', table_name='users')
    op.drop_index('idx_users_workos_user_id', table_name='users')
    op.drop_constraint('fk_users_workspace', 'users', type_='foreignkey')
    op.drop_column('users', 'directory_user_id')
    op.drop_column('users', 'directory_synced')
    op.drop_column('users', 'mfa_enabled')
    op.drop_column('users', 'is_super_admin')
    op.drop_column('users', 'role')
    op.drop_column('users', 'workos_user_id')
    op.drop_column('users', 'workspace_id')

    # Drop workspaces table (must drop owner FK first)
    op.drop_constraint('fk_workspaces_owner', 'workspaces', type_='foreignkey')
    op.drop_index('idx_workspaces_slug', table_name='workspaces')
    op.drop_table('workspaces')
