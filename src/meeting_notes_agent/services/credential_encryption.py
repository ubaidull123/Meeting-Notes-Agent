"""Credential Encryption Service using AES-GCM with HKDF-SHA256 key derivation.

Isolated behind a service interface for future KMS replacement.
"""
import base64
import json
import os
from typing import Optional

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF


class CredentialEncryptionService:
    """Service for encrypting/decrypting API credentials using AES-GCM.

    Uses HKDF-SHA256 to derive a 256-bit encryption key from the master key.
    Each encryption generates a random 96-bit nonce for semantic security.
    """

    # AES-GCM constants
    KEY_SIZE = 32  # 256 bits
    NONCE_SIZE = 12  # 96 bits (recommended for AES-GCM)
    TAG_SIZE = 16  # 128 bits

    def __init__(self, master_key: Optional[str] = None):
        """Initialize with master key from settings or parameter.

        Args:
            master_key: Master encryption key. If None, reads from settings.
        """
        if master_key is None:
            from meeting_notes_agent.config.core.config import settings
            master_key = settings.credential_encryption_key

        if not master_key:
            raise ValueError("Credential encryption key not configured")

        self._master_key = master_key.encode() if isinstance(master_key, str) else master_key
        self._encryption_key = self._derive_key(self._master_key)

    @staticmethod
    def _derive_key(master_key: bytes) -> bytes:
        """Derive 256-bit encryption key from master key using HKDF-SHA256."""
        hkdf = HKDF(
            algorithm=hashes.SHA256(),
            length=CredentialEncryptionService.KEY_SIZE,
            salt=None,  # No salt - deterministic derivation from master key
            info=b"meeting-notes-credential-encryption",
        )
        return hkdf.derive(master_key)

    def encrypt(self, plaintext: str) -> str:
        """Encrypt plaintext string using AES-GCM.

        Returns:
            Base64-encoded string containing: nonce (12 bytes) + ciphertext + tag (16 bytes)
        """
        if not plaintext:
            return self._encrypt_bytes(b"")

        nonce = os.urandom(self.NONCE_SIZE)
        aesgcm = AESGCM(self._encryption_key)
        ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)

        # Combine nonce + ciphertext (which includes tag at the end)
        encrypted_data = nonce + ciphertext
        return base64.b64encode(encrypted_data).decode("ascii")

    def _encrypt_bytes(self, data: bytes) -> str:
        """Encrypt raw bytes (for empty string handling)."""
        nonce = os.urandom(self.NONCE_SIZE)
        aesgcm = AESGCM(self._encryption_key)
        ciphertext = aesgcm.encrypt(nonce, data, None)
        encrypted_data = nonce + ciphertext
        return base64.b64encode(encrypted_data).decode("ascii")

    def decrypt(self, encrypted: str) -> str:
        """Decrypt base64-encoded ciphertext back to plaintext.

        Args:
            encrypted: Base64 string from encrypt()

        Returns:
            Decrypted plaintext string

        Raises:
            ValueError: If decryption fails (invalid key, tampered data, etc.)
        """
        if not encrypted:
            return ""

        try:
            encrypted_data = base64.b64decode(encrypted.encode("ascii"))
        except Exception as e:
            raise ValueError(f"Invalid base64 encoding: {e}")

        if len(encrypted_data) < self.NONCE_SIZE + self.TAG_SIZE:
            raise ValueError("Ciphertext too short")

        nonce = encrypted_data[:self.NONCE_SIZE]
        ciphertext = encrypted_data[self.NONCE_SIZE:]

        aesgcm = AESGCM(self._encryption_key)
        try:
            plaintext = aesgcm.decrypt(nonce, ciphertext, None)
            return plaintext.decode("utf-8")
        except Exception as e:
            raise ValueError(f"Decryption failed: {e}")

    def encrypt_json(self, value: dict) -> str:
        """Encrypt structured provider configuration without exposing it to clients."""
        return self.encrypt(json.dumps(value, separators=(",", ":"), sort_keys=True))

    def decrypt_json(self, encrypted: str | None) -> dict:
        if not encrypted:
            return {}
        value = json.loads(self.decrypt(encrypted))
        return value if isinstance(value, dict) else {}

    @staticmethod
    def mask_key(api_key: str) -> str:
        """Mask API key for display: show only last 4 characters.

        Args:
            api_key: Full API key string

        Returns:
            Masked string in format ••••abcd
        """
        if not api_key:
            return "••••"

        if len(api_key) <= 4:
            return "••••" + api_key

        return "••••" + api_key[-4:]

    @classmethod
    def generate_master_key(cls) -> str:
        """Generate a new random master key suitable for CREDENTIAL_ENCRYPTION_KEY.

        Returns:
            Base64-encoded 32-byte random key
        """
        return base64.b64encode(os.urandom(cls.KEY_SIZE)).decode("ascii")
