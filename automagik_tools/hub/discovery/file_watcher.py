"""File watcher for hot-reloading .genie agent files.

Uses watchdog library with 500ms debounce (like Forge's ProfileCacheManager).
Monitors .genie/ directories for changes and updates database + cache.
"""
import asyncio
import time
from pathlib import Path
from typing import Dict, Set, Optional, Callable
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent

from .cache import AgentCache, get_agent_cache


class GenieAgentWatcher(FileSystemEventHandler):
    """Watches .genie/agents/ directories for changes.

    Implements 500ms debounce to batch rapid file changes.
    """

    DEBOUNCE_MS = 500  # Same as Forge's ProfileCacheManager

    def __init__(
        self,
        cache: AgentCache,
        reload_callback: Optional[Callable] = None
    ):
        """Initialize file watcher.

        Args:
            cache: Agent cache instance
            reload_callback: Optional async callback for reload
        """
        super().__init__()
        self.cache = cache
        self.reload_callback = reload_callback
        self._pending_updates: Dict[str, float] = {}
        self._lock = asyncio.Lock()
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    def set_event_loop(self, loop: asyncio.AbstractEventLoop):
        """Set event loop for async operations.

        Args:
            loop: Event loop
        """
        self._loop = loop

    def on_modified(self, event: FileSystemEvent):
        """Handle file modification events.

        Args:
            event: Filesystem event
        """
        if event.is_directory:
            return

        file_path = event.src_path
        if not file_path.endswith(".md"):
            return

        # Schedule debounced reload
        if self._loop:
            asyncio.run_coroutine_threadsafe(
                self._schedule_reload(file_path),
                self._loop
            )

    def on_created(self, event: FileSystemEvent):
        """Handle file creation events.

        Args:
            event: Filesystem event
        """
        self.on_modified(event)  # Treat creation as modification

    def on_deleted(self, event: FileSystemEvent):
        """Handle file deletion events.

        Args:
            event: Filesystem event
        """
        if event.is_directory:
            return

        file_path = event.src_path
        if not file_path.endswith(".md"):
            return

        # Remove from cache
        if self._loop:
            asyncio.run_coroutine_threadsafe(
                self._handle_deletion(file_path),
                self._loop
            )

    async def _schedule_reload(self, file_path: str):
        """Schedule debounced reload.

        Args:
            file_path: Path to modified file
        """
        async with self._lock:
            self._pending_updates[file_path] = time.time()

        # Wait for debounce period
        await asyncio.sleep(self.DEBOUNCE_MS / 1000)

        async with self._lock:
            # Check if still pending and no newer update
            if file_path in self._pending_updates:
                last_update = self._pending_updates[file_path]
                if time.time() - last_update >= (self.DEBOUNCE_MS / 1000):
                    # Process the update
                    del self._pending_updates[file_path]
                    await self._process_update(file_path)

    async def _process_update(self, file_path: str):
        """Process file update.

        Args:
            file_path: Path to modified file
        """
        print(f"🔄 Reloading agent: {file_path}")

        try:
            # Call reload callback if provided
            if self.reload_callback:
                await self.reload_callback(Path(file_path))
            else:
                # Fallback to cache reload
                await self.cache.reload_agent(file_path)
        except Exception as e:
            print(f"⚠️  Failed to reload {file_path}: {e}")

    async def _handle_deletion(self, file_path: str):
        """Handle file deletion.

        Args:
            file_path: Path to deleted file
        """
        print(f"🗑️  Agent deleted: {file_path}")

        try:
            # Get agent from cache
            agent = await self.cache.get_by_file_path(file_path)
            if agent:
                agent_id = agent.get("id")
                if agent_id:
                    await self.cache.remove(agent_id)
        except Exception as e:
            print(f"⚠️  Failed to handle deletion of {file_path}: {e}")


class AgentDiscoveryService:
    """Main service for discovering and watching agents.

    Coordinates project scanning, agent parsing, and file watching.
    """

    def __init__(self):
        """Initialize discovery service."""
        self.observer: Optional[Observer] = None
        self.cache = get_agent_cache()
        self.watcher: Optional[GenieAgentWatcher] = None
        self._watched_paths: Set[str] = set()
        self._reload_callback: Optional[Callable] = None

    def set_reload_callback(self, callback: Callable):
        """Set callback for file reload.

        Args:
            callback: Async function(file_path: Path) -> None
        """
        self._reload_callback = callback

    def start_watching(
        self,
        base_folders: list[Path],
        event_loop: asyncio.AbstractEventLoop
    ):
        """Start watching base folders for changes.

        Args:
            base_folders: List of base folders to watch
            event_loop: Event loop for async operations
        """
        if self.observer:
            print("⚠️  Observer already running")
            return

        # Create observer
        self.observer = Observer()
        self.watcher = GenieAgentWatcher(
            cache=self.cache,
            reload_callback=self._reload_callback
        )
        self.watcher.set_event_loop(event_loop)

        # Watch each base folder
        for folder in base_folders:
            if not folder.exists():
                continue

            folder_str = str(folder.resolve())
            if folder_str in self._watched_paths:
                continue

            try:
                self.observer.schedule(
                    self.watcher,
                    folder_str,
                    recursive=True
                )
                self._watched_paths.add(folder_str)
                print(f"👁️  Watching: {folder_str}")
            except Exception as e:
                print(f"⚠️  Failed to watch {folder_str}: {e}")

        # Start observer
        self.observer.start()
        print("✅ File watcher started")

    def stop_watching(self):
        """Stop file watching."""
        if self.observer:
            self.observer.stop()
            self.observer.join(timeout=5)
            self.observer = None
            self._watched_paths.clear()
            print("⏹️  File watcher stopped")

    def is_watching(self) -> bool:
        """Check if file watching is active.

        Returns:
            True if watching
        """
        return self.observer is not None and self.observer.is_alive()


# Global service instance
_discovery_service: Optional[AgentDiscoveryService] = None


def get_discovery_service() -> AgentDiscoveryService:
    """Get global discovery service instance.

    Returns:
        AgentDiscoveryService singleton
    """
    global _discovery_service
    if _discovery_service is None:
        _discovery_service = AgentDiscoveryService()
    return _discovery_service
