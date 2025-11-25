"""Zero-configuration setup wizard for Automagik Hub."""

from .encryption import EncryptionManager
from .config_store import ConfigStore, SystemConfig
from .mode_manager import AppMode, ModeManager
from .local_auth import LocalAuthManager, LocalAuthSession
from .wizard_routes import router as setup_router
from .middleware import SetupRequiredMiddleware, add_setup_middleware

__all__ = [
    "EncryptionManager",
    "ConfigStore",
    "SystemConfig",
    "AppMode",
    "ModeManager",
    "LocalAuthManager",
    "LocalAuthSession",
    "setup_router",
    "SetupRequiredMiddleware",
    "add_setup_middleware",
]
