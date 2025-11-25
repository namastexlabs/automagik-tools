"""Encryption utilities for storing secrets in the database.

Uses Fernet symmetric encryption with machine-derived keys.
Keys are derived from machine ID + salt using PBKDF2.
"""
import hashlib
import os
import uuid
from pathlib import Path
from typing import Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
import base64


class EncryptionManager:
    """Manages encryption/decryption of secrets using machine-derived keys."""

    def __init__(self, salt: Optional[bytes] = None):
        """Initialize encryption manager.

        Args:
            salt: Encryption salt. If None, generates new salt (for first setup).
        """
        self.salt = salt or self._generate_salt()
        self._fernet: Optional[Fernet] = None

    @staticmethod
    def _generate_salt() -> bytes:
        """Generate a new random salt."""
        return os.urandom(32)

    @staticmethod
    def _get_machine_id() -> str:
        """Get stable machine identifier.

        Uses:
        1. /etc/machine-id (Linux)
        2. Platform UUID (macOS/BSD)
        3. Hostname + MAC address fallback

        Returns:
            Machine identifier string
        """
        # Try /etc/machine-id (most Linux systems)
        machine_id_path = Path("/etc/machine-id")
        if machine_id_path.exists():
            return machine_id_path.read_text().strip()

        # Try /var/lib/dbus/machine-id (some Linux)
        dbus_machine_id = Path("/var/lib/dbus/machine-id")
        if dbus_machine_id.exists():
            return dbus_machine_id.read_text().strip()

        # Fallback: hostname + MAC address
        import socket
        hostname = socket.gethostname()

        try:
            # Get MAC address of default interface
            import netifaces
            gws = netifaces.gateways()
            default_interface = gws['default'][netifaces.AF_INET][1]
            mac = netifaces.ifaddresses(default_interface)[netifaces.AF_LINK][0]['addr']
        except (ImportError, KeyError, IndexError):
            # Fallback to uuid.getnode() (MAC address as int)
            mac = str(uuid.getnode())

        return f"{hostname}:{mac}"

    def _derive_key(self) -> bytes:
        """Derive encryption key from machine ID + salt using PBKDF2.

        Returns:
            32-byte encryption key suitable for Fernet
        """
        machine_id = self._get_machine_id()
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self.salt,
            iterations=480000,  # OWASP recommendation for PBKDF2-SHA256
        )
        key = kdf.derive(machine_id.encode())
        return base64.urlsafe_b64encode(key)

    def _get_fernet(self) -> Fernet:
        """Get or create Fernet cipher."""
        if self._fernet is None:
            key = self._derive_key()
            self._fernet = Fernet(key)
        return self._fernet

    def encrypt(self, plaintext: str) -> str:
        """Encrypt plaintext string.

        Args:
            plaintext: String to encrypt

        Returns:
            Base64-encoded encrypted string
        """
        fernet = self._get_fernet()
        encrypted_bytes = fernet.encrypt(plaintext.encode())
        return base64.urlsafe_b64encode(encrypted_bytes).decode()

    def decrypt(self, ciphertext: str) -> str:
        """Decrypt ciphertext string.

        Args:
            ciphertext: Base64-encoded encrypted string

        Returns:
            Decrypted plaintext string

        Raises:
            cryptography.fernet.InvalidToken: If decryption fails
        """
        fernet = self._get_fernet()
        encrypted_bytes = base64.urlsafe_b64decode(ciphertext.encode())
        decrypted_bytes = fernet.decrypt(encrypted_bytes)
        return decrypted_bytes.decode()

    def get_salt_b64(self) -> str:
        """Get base64-encoded salt for storage.

        Returns:
            Base64-encoded salt string
        """
        return base64.urlsafe_b64encode(self.salt).decode()

    @classmethod
    def from_salt_b64(cls, salt_b64: str) -> "EncryptionManager":
        """Create EncryptionManager from base64-encoded salt.

        Args:
            salt_b64: Base64-encoded salt string

        Returns:
            EncryptionManager instance
        """
        salt = base64.urlsafe_b64decode(salt_b64.encode())
        return cls(salt=salt)


# Singleton instance (initialized on first use)
_encryption_manager: Optional[EncryptionManager] = None


def get_encryption_manager(salt_b64: Optional[str] = None) -> EncryptionManager:
    """Get or create encryption manager singleton.

    Args:
        salt_b64: Optional base64-encoded salt. If provided, creates new instance.

    Returns:
        EncryptionManager instance
    """
    global _encryption_manager

    if salt_b64:
        _encryption_manager = EncryptionManager.from_salt_b64(salt_b64)
    elif _encryption_manager is None:
        _encryption_manager = EncryptionManager()

    return _encryption_manager
