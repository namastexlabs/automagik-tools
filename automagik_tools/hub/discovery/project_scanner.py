"""Project scanner for discovering .git repositories.

Scans base folders recursively (unlimited depth) to find projects.
Each .git directory = one project.
"""
import uuid
import subprocess
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Project, UserBaseFolder


class ProjectScanner:
    """Scans filesystem for .git repositories."""

    def __init__(self, session: AsyncSession):
        """Initialize project scanner.

        Args:
            session: Database session
        """
        self.session = session

    async def scan_base_folder(
        self,
        base_folder_id: str,
        workspace_id: str
    ) -> List[Project]:
        """Scan base folder for .git directories.

        Args:
            base_folder_id: UserBaseFolder ID
            workspace_id: Workspace ID

        Returns:
            List of discovered/updated projects
        """
        # Get base folder
        result = await self.session.execute(
            select(UserBaseFolder).where(UserBaseFolder.id == base_folder_id)
        )
        base_folder = result.scalar_one_or_none()
        if not base_folder:
            return []

        base_path = Path(base_folder.path)
        if not base_path.exists() or not base_path.is_dir():
            print(f"⚠️  Base folder not found: {base_path}")
            return []

        # Find all .git directories (unlimited depth)
        git_dirs = list(base_path.rglob(".git"))
        projects = []

        for git_dir in git_dirs:
            if not git_dir.is_dir():
                continue

            project_path = git_dir.parent

            # Get or create project
            project = await self._get_or_create_project(
                workspace_id=workspace_id,
                base_folder_id=base_folder_id,
                project_path=project_path
            )

            if project:
                projects.append(project)

        # Update last scanned timestamp
        base_folder.last_scanned_at = datetime.now(timezone.utc)
        await self.session.commit()

        print(f"✅ Scanned {base_path}: Found {len(projects)} projects")
        return projects

    async def _get_or_create_project(
        self,
        workspace_id: str,
        base_folder_id: str,
        project_path: Path
    ) -> Optional[Project]:
        """Get existing project or create new one.

        Args:
            workspace_id: Workspace ID
            base_folder_id: Base folder ID
            project_path: Absolute path to project

        Returns:
            Project or None if error
        """
        project_path_str = str(project_path.resolve())

        # Check if project exists
        result = await self.session.execute(
            select(Project).where(Project.path == project_path_str)
        )
        project = result.scalar_one_or_none()

        if project:
            # Update existing project
            project.last_synced_at = datetime.now(timezone.utc)
            project.is_active = True
            await self.session.commit()
            return project

        # Create new project
        project_name = project_path.name
        git_remote = self._get_git_remote(project_path)
        has_genie = (project_path / ".genie").exists()

        project = Project(
            id=str(uuid.uuid4()),
            workspace_id=workspace_id,
            base_folder_id=base_folder_id,
            name=project_name,
            path=project_path_str,
            git_remote_url=git_remote,
            has_genie_folder=has_genie,
            agent_count=0,
            is_active=True,
            discovered_at=datetime.now(timezone.utc),
            last_synced_at=datetime.now(timezone.utc),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        self.session.add(project)
        await self.session.commit()
        await self.session.refresh(project)

        print(f"📁 Discovered project: {project_name} ({project_path_str})")
        return project

    def _get_git_remote(self, project_path: Path) -> Optional[str]:
        """Get git remote URL for project.

        Args:
            project_path: Path to project

        Returns:
            Remote URL or None
        """
        try:
            result = subprocess.run(
                ["git", "config", "--get", "remote.origin.url"],
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception as e:
            print(f"⚠️  Failed to get git remote for {project_path}: {e}")

        return None

    async def rescan_project(self, project_id: str) -> Optional[Project]:
        """Rescan a specific project to update metadata.

        Args:
            project_id: Project ID

        Returns:
            Updated project or None
        """
        result = await self.session.execute(
            select(Project).where(Project.id == project_id)
        )
        project = result.scalar_one_or_none()
        if not project:
            return None

        project_path = Path(project.path)
        if not project_path.exists():
            # Mark inactive if path no longer exists
            project.is_active = False
            await self.session.commit()
            return project

        # Update metadata
        project.git_remote_url = self._get_git_remote(project_path)
        project.has_genie_folder = (project_path / ".genie").exists()
        project.last_synced_at = datetime.now(timezone.utc)
        project.is_active = True

        await self.session.commit()
        await self.session.refresh(project)

        return project

    async def get_projects(
        self,
        workspace_id: str,
        active_only: bool = True
    ) -> List[Project]:
        """Get all projects for workspace.

        Args:
            workspace_id: Workspace ID
            active_only: Only return active projects

        Returns:
            List of projects
        """
        query = select(Project).where(Project.workspace_id == workspace_id)

        if active_only:
            query = query.where(Project.is_active == True)

        query = query.order_by(Project.name)

        result = await self.session.execute(query)
        return list(result.scalars().all())
