"""Agent parser for discovering and parsing .genie/*.md files.

Scans all .md files within .genie/ (unlimited depth).
Any .md file with valid YAML frontmatter = agent.
"""
import uuid
import hashlib
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Project, Agent
from .frontmatter_utils import FrontmatterManager


class AgentParser:
    """Parses .genie/*.md files to discover agents."""

    def __init__(self, session: AsyncSession):
        """Initialize agent parser.

        Args:
            session: Database session
        """
        self.session = session
        self.frontmatter = FrontmatterManager()

    async def scan_project(self, project_id: str) -> List[Agent]:
        """Scan project's .genie folder for agent files.

        Args:
            project_id: Project ID

        Returns:
            List of discovered/updated agents
        """
        # Get project
        result = await self.session.execute(
            select(Project).where(Project.id == project_id)
        )
        project = result.scalar_one_or_none()
        if not project:
            return []

        project_path = Path(project.path)
        genie_dir = project_path / ".genie"

        if not genie_dir.exists():
            return []

        # Find all .md files (unlimited depth)
        md_files = list(genie_dir.rglob("*.md"))
        agents = []

        for md_file in md_files:
            # Check if has valid frontmatter
            if not self.frontmatter.has_valid_frontmatter(md_file):
                continue

            # Parse and create/update agent
            agent = await self._parse_agent_file(
                project=project,
                file_path=md_file
            )

            if agent:
                agents.append(agent)

        # Update project agent count
        project.agent_count = len(agents)
        project.last_synced_at = datetime.now(timezone.utc)
        await self.session.commit()

        print(f"🤖 Scanned {project.name}: Found {len(agents)} agents")
        return agents

    async def _parse_agent_file(
        self,
        project: Project,
        file_path: Path
    ) -> Optional[Agent]:
        """Parse single agent file.

        Args:
            project: Project object
            file_path: Absolute path to .md file

        Returns:
            Agent or None if parse error
        """
        try:
            # Read frontmatter
            frontmatter, body = self.frontmatter.read_frontmatter(file_path)

            # Calculate file hash for change detection
            file_hash = self._calculate_file_hash(file_path)

            # Get relative path within .genie/
            project_path = Path(project.path)
            genie_dir = project_path / ".genie"
            relative_path = str(file_path.relative_to(genie_dir))

            # Check if agent exists
            file_path_str = str(file_path.resolve())
            result = await self.session.execute(
                select(Agent).where(Agent.file_path == file_path_str)
            )
            agent = result.scalar_one_or_none()

            # Extract metadata from frontmatter
            genie_config = frontmatter.get("genie", {})
            hub_config = frontmatter.get("hub", {})

            # Extract title and description from body
            title, description = self._extract_title_description(body)

            if agent:
                # Update existing agent if changed
                if agent.file_hash != file_hash:
                    agent.filename = file_path.name
                    agent.relative_path = relative_path
                    agent.file_hash = file_hash
                    agent.executor = genie_config.get("executor")
                    agent.variant = genie_config.get("variant")
                    agent.model = frontmatter.get("forge", {}).get("model") or genie_config.get("model")
                    agent.title = title or file_path.stem
                    agent.description = description
                    agent.icon = hub_config.get("icon", "bot")
                    agent.toolkit = hub_config.get("toolkit")
                    agent.raw_frontmatter = frontmatter
                    agent.sync_status = "synced"
                    agent.synced_at = datetime.now(timezone.utc)
                    agent.updated_at = datetime.now(timezone.utc)

                    await self.session.commit()
                    print(f"  ↻ Updated: {relative_path}")

                return agent

            # Create new agent
            agent = Agent(
                id=str(uuid.uuid4()),
                project_id=project.id,
                workspace_id=project.workspace_id,
                filename=file_path.name,
                file_path=file_path_str,
                relative_path=relative_path,
                file_hash=file_hash,
                executor=genie_config.get("executor"),
                variant=genie_config.get("variant"),
                model=frontmatter.get("forge", {}).get("model") or genie_config.get("model"),
                title=title or file_path.stem,
                description=description,
                icon=hub_config.get("icon", "bot"),
                toolkit=hub_config.get("toolkit"),
                raw_frontmatter=frontmatter,
                sync_status="synced",
                synced_at=datetime.now(timezone.utc),
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )

            self.session.add(agent)
            await self.session.commit()
            await self.session.refresh(agent)

            print(f"  ✨ Discovered: {relative_path}")
            return agent

        except Exception as e:
            print(f"⚠️  Failed to parse {file_path}: {e}")
            return None

    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of file for change detection.

        Args:
            file_path: Path to file

        Returns:
            SHA256 hex digest
        """
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    def _extract_title_description(self, body: str) -> tuple[Optional[str], Optional[str]]:
        """Extract title (first # heading) and description (first paragraph).

        Args:
            body: Markdown body content

        Returns:
            Tuple of (title, description)
        """
        lines = body.strip().split("\n")
        title = None
        description = None

        # Find first heading
        for i, line in enumerate(lines):
            line = line.strip()
            if line.startswith("# "):
                title = line[2:].strip()
                # Look for description in next non-empty line
                for j in range(i + 1, len(lines)):
                    desc_line = lines[j].strip()
                    if desc_line and not desc_line.startswith("#"):
                        description = desc_line
                        break
                break

        return title, description

    async def reload_agent(self, file_path: Path) -> Optional[Agent]:
        """Reload single agent file (for file watcher).

        Args:
            file_path: Absolute path to .md file

        Returns:
            Updated agent or None
        """
        file_path_str = str(file_path.resolve())

        # Find agent by file path
        result = await self.session.execute(
            select(Agent).where(Agent.file_path == file_path_str)
        )
        agent = result.scalar_one_or_none()

        if not agent:
            # New file - need to find project first
            # Try to infer project from path
            return None

        # Get project
        result = await self.session.execute(
            select(Project).where(Project.id == agent.project_id)
        )
        project = result.scalar_one_or_none()

        if not project:
            return None

        # Re-parse file
        return await self._parse_agent_file(project, file_path)

    async def get_project_agents(
        self,
        project_id: str
    ) -> List[Agent]:
        """Get all agents for a project.

        Args:
            project_id: Project ID

        Returns:
            List of agents
        """
        result = await self.session.execute(
            select(Agent)
            .where(Agent.project_id == project_id)
            .order_by(Agent.relative_path)
        )
        return list(result.scalars().all())

    async def get_agents_by_workspace(
        self,
        workspace_id: str
    ) -> List[Agent]:
        """Get all agents in workspace.

        Args:
            workspace_id: Workspace ID

        Returns:
            List of agents
        """
        result = await self.session.execute(
            select(Agent)
            .where(Agent.workspace_id == workspace_id)
            .order_by(Agent.relative_path)
        )
        return list(result.scalars().all())
