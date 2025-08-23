"""Data models for Spark API"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class WorkflowType(str, Enum):
    """Workflow types supported by Spark"""
    AGENT = "hive_agent"
    TEAM = "hive_team"
    WORKFLOW = "hive_workflow"
    LEGACY = "langflow"


class TaskStatus(str, Enum):
    """Task execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ScheduleType(str, Enum):
    """Schedule type for workflow execution"""
    INTERVAL = "interval"
    CRON = "cron"


class ScheduleStatus(str, Enum):
    """Schedule status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PAUSED = "paused"


class SourceType(str, Enum):
    """Workflow source types"""
    AUTOMAGIK_AGENTS = "automagik-agents"
    AUTOMAGIK_HIVE = "automagik-hive"
    LANGFLOW = "langflow"