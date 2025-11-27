"""YAML frontmatter utilities with round-trip preservation.

Uses ruamel.yaml to preserve formatting, comments, and structure
when reading and writing .genie agent files.
"""
from pathlib import Path
from typing import Tuple, Dict, Any, Optional
from io import StringIO
from datetime import datetime, timezone

try:
    from ruamel.yaml import YAML
    RUAMEL_AVAILABLE = True
except ImportError:
    RUAMEL_AVAILABLE = False
    import yaml as YAML  # Fallback to PyYAML


class FrontmatterManager:
    """Manages YAML frontmatter for .genie agent files.

    Provides round-trip preservation of formatting using ruamel.yaml.
    Critical for maintaining file structure when writing toolkit configs.
    """

    def __init__(self):
        """Initialize frontmatter manager."""
        if RUAMEL_AVAILABLE:
            self.yaml = YAML()
            self.yaml.preserve_quotes = True
            self.yaml.default_flow_style = False
            self.yaml.width = 4096  # Prevent line wrapping
            self.yaml.indent(mapping=2, sequence=2, offset=0)
        else:
            self.yaml = YAML
            print("⚠️  ruamel.yaml not installed, using PyYAML (no round-trip preservation)")

    def read_frontmatter(self, file_path: Path) -> Tuple[Dict[str, Any], str]:
        """Read YAML frontmatter and content from markdown file.

        Args:
            file_path: Path to .md file

        Returns:
            Tuple of (frontmatter_dict, markdown_content)

        Example file structure:
            ---
            genie:
              executor: CLAUDE_CODE
            ---
            # Agent content
        """
        if not file_path.exists():
            return {}, ""

        content = file_path.read_text(encoding="utf-8")

        # Check for frontmatter
        if not content.startswith("---"):
            return {}, content

        # Split into frontmatter and body
        parts = content.split("---", 2)
        if len(parts) < 3:
            # Invalid frontmatter format
            return {}, content

        frontmatter_str = parts[1]
        body = parts[2]

        # Parse YAML
        try:
            if RUAMEL_AVAILABLE:
                frontmatter = self.yaml.load(frontmatter_str)
            else:
                frontmatter = self.yaml.safe_load(frontmatter_str)

            # Handle None case (empty frontmatter)
            if frontmatter is None:
                frontmatter = {}

            return frontmatter, body.lstrip("\n")
        except Exception as e:
            print(f"⚠️  Failed to parse frontmatter in {file_path}: {e}")
            return {}, content

    def write_frontmatter(
        self,
        file_path: Path,
        frontmatter: Dict[str, Any],
        body: str
    ) -> None:
        """Write frontmatter and content back to markdown file.

        Args:
            file_path: Path to .md file
            frontmatter: Frontmatter dictionary
            body: Markdown content (without frontmatter)
        """
        # Serialize frontmatter
        output = StringIO()
        output.write("---\n")

        if RUAMEL_AVAILABLE:
            self.yaml.dump(frontmatter, output)
        else:
            self.yaml.dump(frontmatter, output, default_flow_style=False, allow_unicode=True)

        output.write("---\n")

        # Ensure body starts with newline if not empty
        if body and not body.startswith("\n"):
            output.write("\n")

        output.write(body)

        # Write to file
        file_path.write_text(output.getvalue(), encoding="utf-8")

    def update_hub_toolkit(
        self,
        file_path: Path,
        toolkit_config: Dict[str, Any],
        configured_by: Optional[str] = None
    ) -> bool:
        """Update only the hub.toolkit section in frontmatter.

        Preserves all other frontmatter sections (genie:, forge:, etc.)
        This is the CRITICAL method for persisting toolkit config to version control.

        Args:
            file_path: Path to .genie/*.md file
            toolkit_config: Toolkit configuration dict
            configured_by: Email of user who configured (optional)

        Returns:
            True if successful, False otherwise
        """
        try:
            # Read existing frontmatter and body
            frontmatter, body = self.read_frontmatter(file_path)

            # Ensure hub section exists
            if "hub" not in frontmatter:
                frontmatter["hub"] = {}

            # Update toolkit section
            frontmatter["hub"]["toolkit"] = toolkit_config

            # Add metadata
            frontmatter["hub"]["toolkit"]["last_configured"] = datetime.now(timezone.utc).isoformat() + "Z"
            if configured_by:
                frontmatter["hub"]["toolkit"]["configured_by"] = configured_by

            # Write back to file
            self.write_frontmatter(file_path, frontmatter, body)

            return True
        except Exception as e:
            print(f"❌ Failed to update toolkit in {file_path}: {e}")
            return False

    def update_hub_icon(
        self,
        file_path: Path,
        icon: str
    ) -> bool:
        """Update only the hub.icon field in frontmatter.

        Args:
            file_path: Path to .genie/*.md file
            icon: Lucide icon name (e.g., "bot", "sparkles")

        Returns:
            True if successful, False otherwise
        """
        try:
            frontmatter, body = self.read_frontmatter(file_path)

            # Ensure hub section exists
            if "hub" not in frontmatter:
                frontmatter["hub"] = {}

            # Update icon
            frontmatter["hub"]["icon"] = icon

            # Write back
            self.write_frontmatter(file_path, frontmatter, body)

            return True
        except Exception as e:
            print(f"❌ Failed to update icon in {file_path}: {e}")
            return False

    def get_hub_config(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Get hub configuration from frontmatter.

        Args:
            file_path: Path to .genie/*.md file

        Returns:
            Hub config dict or None
        """
        frontmatter, _ = self.read_frontmatter(file_path)
        return frontmatter.get("hub")

    def has_valid_frontmatter(self, file_path: Path) -> bool:
        """Check if file has valid YAML frontmatter.

        Args:
            file_path: Path to .md file

        Returns:
            True if file has valid frontmatter
        """
        frontmatter, _ = self.read_frontmatter(file_path)
        return bool(frontmatter)
