"""
Channel manager for Message Bridge MCP tool
"""

import asyncio
import os
import json
import fcntl
from datetime import datetime, timezone
from typing import Dict, List, Optional
from collections import defaultdict
from pathlib import Path

from .models import Message, ChannelInfo


def get_instance_id() -> str:
    """Get a unique identifier for this tool instance"""
    # Combine process ID with timestamp for uniqueness
    return f"instance_{os.getpid()}_{int(datetime.now().timestamp() * 1000)}"


class FileStorage:
    """File-based storage for cross-instance communication"""
    
    def __init__(self, storage_dir: str = "/tmp/agent_connect"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        self.channels_file = self.storage_dir / "channels.json"
        self.history_file = self.storage_dir / "history.json"
        self._ensure_files()
    
    def _ensure_files(self):
        """Ensure storage files exist"""
        if not self.channels_file.exists():
            self._write_json(self.channels_file, {})
        if not self.history_file.exists():
            self._write_json(self.history_file, {})
    
    def _read_json(self, filepath: Path) -> dict:
        """Read JSON file with file locking"""
        try:
            with open(filepath, 'r') as f:
                fcntl.flock(f.fileno(), fcntl.LOCK_SH)  # Shared lock for reading
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    def _write_json(self, filepath: Path, data: dict):
        """Write JSON file with file locking"""
        with open(filepath, 'w') as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)  # Exclusive lock for writing
            json.dump(data, f, default=str, indent=2)
    
    def get_channels_data(self) -> dict:
        """Get all channels data"""
        return self._read_json(self.channels_file)
    
    def update_channels_data(self, data: dict):
        """Update channels data"""
        self._write_json(self.channels_file, data)
    
    def get_history_data(self) -> dict:
        """Get all history data"""
        return self._read_json(self.history_file)
    
    def update_history_data(self, data: dict):
        """Update history data"""
        self._write_json(self.history_file, data)
    
    def add_message_to_channel(self, channel_id: str, message: Message):
        """Add a message to a channel (atomic operation)"""
        # Read current data
        channels_data = self.get_channels_data()
        history_data = self.get_history_data()
        
        # Initialize channel if not exists
        if channel_id not in channels_data:
            channels_data[channel_id] = {
                "messages": [],
                "listeners": 0,
                "info": {
                    "channel_id": channel_id,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "last_activity": datetime.now(timezone.utc).isoformat(),
                    "total_messages_sent": 0,
                    "active_listeners": 0,
                    "pending_messages": 0
                }
            }
        
        # Add message to pending queue
        channels_data[channel_id]["messages"].append(message.model_dump())
        channels_data[channel_id]["info"]["total_messages_sent"] += 1
        channels_data[channel_id]["info"]["last_activity"] = datetime.now(timezone.utc).isoformat()
        channels_data[channel_id]["info"]["pending_messages"] = len(channels_data[channel_id]["messages"])
        
        # Add to history
        if channel_id not in history_data:
            history_data[channel_id] = []
        history_data[channel_id].append(message.model_dump())
        
        # Write back
        self.update_channels_data(channels_data)
        self.update_history_data(history_data)
    
    def pop_message_from_channel(self, channel_id: str) -> Optional[dict]:
        """Pop the oldest message from a channel"""
        channels_data = self.get_channels_data()
        
        if channel_id in channels_data and channels_data[channel_id]["messages"]:
            message = channels_data[channel_id]["messages"].pop(0)
            channels_data[channel_id]["info"]["pending_messages"] = len(channels_data[channel_id]["messages"])
            self.update_channels_data(channels_data)
            return message
        return None


class ChannelManager:
    """Manages message channels with file-based storage for cross-instance communication"""
    
    def __init__(self, config):
        self.config = config
        self.storage = FileStorage(config.storage_dir)
        self._lock = asyncio.Lock()
        self._instance_id = get_instance_id()
        self._polling_tasks: Dict[str, asyncio.Task] = {}  # Track polling tasks
    
    async def wait_for_message(self, channel_id: str, timeout: Optional[float] = None) -> Optional[Message]:
        """Wait for a message on a channel (polling file storage)"""
        start_time = datetime.now()
        timeout_delta = timeout if timeout else float('inf')
        
        while True:
            # Check if we have a message
            message_data = self.storage.pop_message_from_channel(channel_id)
            if message_data:
                # Convert back to Message object
                return Message(**message_data)
            
            # Check timeout
            if timeout and (datetime.now() - start_time).total_seconds() >= timeout_delta:
                return None
            
            # Wait a bit before polling again
            await asyncio.sleep(0.1)
    
    async def send_to_channel(self, channel_id: str, message: Message) -> None:
        """Send a message to a channel"""
        # Add message to file storage
        self.storage.add_message_to_channel(channel_id, message)
    
    async def increment_listeners(self, channel_id: str) -> None:
        """Increment active listener count for a channel"""
        channels_data = self.storage.get_channels_data()
        if channel_id not in channels_data:
            channels_data[channel_id] = {
                "messages": [],
                "listeners": 0,
                "info": {
                    "channel_id": channel_id,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "last_activity": datetime.now(timezone.utc).isoformat(),
                    "total_messages_sent": 0,
                    "active_listeners": 0,
                    "pending_messages": 0
                }
            }
        channels_data[channel_id]["listeners"] += 1
        channels_data[channel_id]["info"]["active_listeners"] = channels_data[channel_id]["listeners"]
        self.storage.update_channels_data(channels_data)
    
    async def decrement_listeners(self, channel_id: str) -> None:
        """Decrement active listener count for a channel"""
        channels_data = self.storage.get_channels_data()
        if channel_id in channels_data and channels_data[channel_id]["listeners"] > 0:
            channels_data[channel_id]["listeners"] -= 1
            channels_data[channel_id]["info"]["active_listeners"] = channels_data[channel_id]["listeners"]
            self.storage.update_channels_data(channels_data)
    
    async def get_listener_count(self, channel_id: str) -> int:
        """Get current listener count for a channel"""
        channels_data = self.storage.get_channels_data()
        return channels_data.get(channel_id, {}).get("listeners", 0)
    
    async def get_channel_history(self, channel_id: str, limit: int = 100) -> List[Message]:
        """Get message history for a channel"""
        history_data = self.storage.get_history_data()
        history_list = history_data.get(channel_id, [])
        
        # Convert back to Message objects and apply limit
        messages = [Message(**msg_data) for msg_data in history_list]
        return messages[-limit:] if limit else messages
    
    async def clear_channel(self, channel_id: str) -> bool:
        """Clear all messages and reset a channel"""
        channels_data = self.storage.get_channels_data()
        history_data = self.storage.get_history_data()
        
        if channel_id in channels_data:
            # Clear messages
            channels_data[channel_id]["messages"] = []
            channels_data[channel_id]["info"]["total_messages_sent"] = 0
            channels_data[channel_id]["info"]["pending_messages"] = 0
            channels_data[channel_id]["info"]["last_activity"] = datetime.now(timezone.utc).isoformat()
            
            # Clear history
            history_data[channel_id] = []
            
            # Update storage
            self.storage.update_channels_data(channels_data)
            self.storage.update_history_data(history_data)
            return True
        return False
    
    async def get_active_channels(self) -> List[ChannelInfo]:
        """Get list of all active channels"""
        channels_data = self.storage.get_channels_data()
        active_channels = []
        
        for channel_id, data in channels_data.items():
            info_data = data["info"]
            # Update pending messages count
            info_data["pending_messages"] = len(data["messages"])
            
            channel_info = ChannelInfo(**info_data)
            active_channels.append(channel_info)
        
        return active_channels
    
    async def cleanup_inactive_channels(self, inactive_hours: int = 24) -> int:
        """Remove channels that have been inactive for specified hours"""
        channels_data = self.storage.get_channels_data()
        history_data = self.storage.get_history_data()
        now = datetime.now(timezone.utc)
        channels_to_remove = []
        
        for channel_id, data in channels_data.items():
            last_activity_str = data["info"]["last_activity"]
            last_activity = datetime.fromisoformat(last_activity_str.replace('Z', '+00:00'))
            hours_inactive = (now - last_activity).total_seconds() / 3600
            
            if hours_inactive > inactive_hours and data["listeners"] == 0:
                channels_to_remove.append(channel_id)
        
        # Remove inactive channels
        for channel_id in channels_to_remove:
            if channel_id in channels_data:
                del channels_data[channel_id]
            if channel_id in history_data:
                del history_data[channel_id]
        
        # Update storage
        if channels_to_remove:
            self.storage.update_channels_data(channels_data)
            self.storage.update_history_data(history_data)
        
        return len(channels_to_remove)
    
    def get_instance_id(self) -> str:
        """Get the instance ID for this manager"""
        return self._instance_id