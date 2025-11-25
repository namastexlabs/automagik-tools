"""Zero-config setup and Genie agent discovery support

Revision ID: 002_zero_config_genie
Revises: 001_initial
Create Date: 2025-11-25 19:00:00.000000

This migration adds:
- system_config: For zero-config setup (app mode, encrypted secrets)
- user_base_folders: Where to scan for projects per user
- projects: Discovered .git repositories
- agents: Cached agents from .genie/agents/*.md
- project_tools: Tools enabled per project
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '002_zero_config_genie'
down_revision: Union[str, None] = '001_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # =========================================================================
    # SYSTEM CONFIG - Zero-Config Setup
    # =========================================================================

    op.create_table('system_config',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('config_key', sa.String(length=100), nullable=False),
        sa.Column('config_value', sa.Text(), nullable=True),
        sa.Column('is_secret', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('config_key')
    )
    op.create_index('idx_system_config_key', 'system_config', ['config_key'], unique=True)

    # =========================================================================
    # USER BASE FOLDERS - Project Scanning Roots
    # =========================================================================

    op.create_table('user_base_folders',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('workspace_id', sa.String(length=36), nullable=True),
        sa.Column('path', sa.Text(), nullable=False),
        sa.Column('label', sa.String(length=100), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('max_depth', sa.Integer(), nullable=False, server_default='3'),
        sa.Column('last_scanned_at', sa.DateTime(), nullable=True),
        sa.Column('project_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_base_folders_user', 'user_base_folders', ['user_id'], unique=False)
    op.create_index('idx_base_folders_workspace', 'user_base_folders', ['workspace_id'], unique=False)
    op.create_index('idx_base_folders_path', 'user_base_folders', ['user_id', 'path'], unique=True)

    # =========================================================================
    # PROJECTS - Discovered .git Repositories
    # =========================================================================

    op.create_table('projects',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('workspace_id', sa.String(length=36), nullable=True),
        sa.Column('base_folder_id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('path', sa.Text(), nullable=False),
        sa.Column('git_remote_url', sa.String(length=500), nullable=True),
        sa.Column('default_branch', sa.String(length=100), nullable=True),
        sa.Column('has_genie_folder', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('agent_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('discovered_at', sa.DateTime(), nullable=False),
        sa.Column('last_synced_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['base_folder_id'], ['user_base_folders.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_projects_workspace', 'projects', ['workspace_id'], unique=False)
    op.create_index('idx_projects_base_folder', 'projects', ['base_folder_id'], unique=False)
    op.create_index('idx_projects_path', 'projects', ['path'], unique=True)
    op.create_index('idx_projects_has_genie', 'projects', ['has_genie_folder'], unique=False)

    # =========================================================================
    # AGENTS - Cached from .genie/agents/*.md
    # =========================================================================

    op.create_table('agents',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('project_id', sa.String(length=36), nullable=False),
        sa.Column('workspace_id', sa.String(length=36), nullable=True),
        # File metadata
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('file_path', sa.Text(), nullable=False),
        sa.Column('relative_path', sa.Text(), nullable=False),  # e.g., "agents/dev/backend.md"
        sa.Column('file_hash', sa.String(length=64), nullable=False),
        # Parsed from frontmatter (genie: section)
        sa.Column('executor', sa.String(length=50), nullable=True),
        sa.Column('variant', sa.String(length=50), nullable=True),
        sa.Column('model', sa.String(length=50), nullable=True),
        # Parsed content
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        # Hub config (from hub: frontmatter, written back)
        sa.Column('icon', sa.String(length=50), nullable=False, server_default='bot'),  # Lucide icon name
        sa.Column('toolkit', sa.JSON(), nullable=True),
        # Raw frontmatter for reference
        sa.Column('raw_frontmatter', sa.JSON(), nullable=True),
        # Sync metadata
        sa.Column('sync_status', sa.String(length=20), nullable=False, server_default='synced'),
        sa.Column('synced_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_agents_project', 'agents', ['project_id'], unique=False)
    op.create_index('idx_agents_workspace', 'agents', ['workspace_id'], unique=False)
    op.create_index('idx_agents_file_path', 'agents', ['file_path'], unique=True)
    op.create_index('idx_agents_sync_status', 'agents', ['sync_status'], unique=False)

    # =========================================================================
    # PROJECT TOOLS - Tools Enabled Per Project
    # =========================================================================

    op.create_table('project_tools',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('project_id', sa.String(length=36), nullable=False),
        sa.Column('workspace_id', sa.String(length=36), nullable=True),
        sa.Column('tool_name', sa.String(length=100), nullable=False),
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('config', sa.JSON(), nullable=True),
        sa.Column('permissions', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_project_tools_project', 'project_tools', ['project_id'], unique=False)
    op.create_index('idx_project_tools_workspace', 'project_tools', ['workspace_id'], unique=False)
    op.create_index('idx_project_tools_unique', 'project_tools', ['project_id', 'tool_name'], unique=True)


def downgrade() -> None:
    # Drop project tools
    op.drop_index('idx_project_tools_unique', table_name='project_tools')
    op.drop_index('idx_project_tools_workspace', table_name='project_tools')
    op.drop_index('idx_project_tools_project', table_name='project_tools')
    op.drop_table('project_tools')

    # Drop agents
    op.drop_index('idx_agents_sync_status', table_name='agents')
    op.drop_index('idx_agents_file_path', table_name='agents')
    op.drop_index('idx_agents_workspace', table_name='agents')
    op.drop_index('idx_agents_project', table_name='agents')
    op.drop_table('agents')

    # Drop projects
    op.drop_index('idx_projects_has_genie', table_name='projects')
    op.drop_index('idx_projects_path', table_name='projects')
    op.drop_index('idx_projects_base_folder', table_name='projects')
    op.drop_index('idx_projects_workspace', table_name='projects')
    op.drop_table('projects')

    # Drop user base folders
    op.drop_index('idx_base_folders_path', table_name='user_base_folders')
    op.drop_index('idx_base_folders_workspace', table_name='user_base_folders')
    op.drop_index('idx_base_folders_user', table_name='user_base_folders')
    op.drop_table('user_base_folders')

    # Drop system config
    op.drop_index('idx_system_config_key', table_name='system_config')
    op.drop_table('system_config')
