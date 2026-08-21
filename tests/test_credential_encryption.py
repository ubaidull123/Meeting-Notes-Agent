"""Tests for CredentialEncryptionService."""
import pytest
import os
from meeting_notes_agent.services.credential_encryption import CredentialEncryptionService


class TestCredentialEncryptionService:
    """Test AES-GCM encryption service for API credentials."""

    @pytest.fixture
    def encryption_service(self):
        # Use a consistent test key (32 bytes for AES-256)
        test_key = "0123456789abcdef0123456789abcdef"  # 32 chars = 256 bits
        return CredentialEncryptionService(master_key=test_key)

    def test_encrypt_decrypt_roundtrip(self, encryption_service):
        """Encrypting then decrypting returns original plaintext."""
        plaintext = "sk-test-abcdefghijklmnopqrstuvwxyz123456"
        encrypted = encryption_service.encrypt(plaintext)
        decrypted = encryption_service.decrypt(encrypted)
        assert decrypted == plaintext

    def test_encrypt_produces_different_ciphertext(self, encryption_service):
        """Multiple encryptions of same plaintext produce different ciphertexts (nonce)."""
        plaintext = "sk-test-key"
        encrypted1 = encryption_service.encrypt(plaintext)
        encrypted2 = encryption_service.encrypt(plaintext)
        assert encrypted1 != encrypted2  # Different nonces
        # But both decrypt to same plaintext
        assert encryption_service.decrypt(encrypted1) == plaintext
        assert encryption_service.decrypt(encrypted2) == plaintext

    def test_encrypt_empty_string(self, encryption_service):
        """Encrypting empty string works."""
        encrypted = encryption_service.encrypt("")
        decrypted = encryption_service.decrypt(encrypted)
        assert decrypted == ""

    def test_encrypt_unicode(self, encryption_service):
        """Encrypting unicode characters works."""
        plaintext = "sk-test-🔑-ключ-密钥"
        encrypted = encryption_service.encrypt(plaintext)
        decrypted = encryption_service.decrypt(encrypted)
        assert decrypted == plaintext

    def test_mask_key_standard(self):
        """mask_key returns •••• + last 4 chars for standard keys."""
        assert CredentialEncryptionService.mask_key("sk-abcdefgh1234") == "••••1234"
        assert CredentialEncryptionService.mask_key("sk_test_abcd") == "••••abcd"

    def test_mask_key_short(self):
        """mask_key handles keys shorter than 4 chars."""
        assert CredentialEncryptionService.mask_key("abc") == "••••abc"
        assert CredentialEncryptionService.mask_key("") == "••••"

    def test_mask_key_exactly_four(self):
        """mask_key handles keys exactly 4 chars."""
        assert CredentialEncryptionService.mask_key("abcd") == "••••abcd"

    def test_different_keys_produce_different_results(self):
        """Different master keys cannot decrypt each other's data."""
        service1 = CredentialEncryptionService(master_key="0123456789abcdef0123456789abcdef")
        service2 = CredentialEncryptionService(master_key="fedcba9876543210fedcba9876543210")

        plaintext = "sk-test-secret"
        encrypted = service1.encrypt(plaintext)

        # service2 should fail to decrypt
        with pytest.raises(Exception):
            service2.decrypt(encrypted)

    def test_tampered_ciphertext_fails(self, encryption_service):
        """Tampered ciphertext fails authentication."""
        plaintext = "sk-test-key"
        encrypted = encryption_service.encrypt(plaintext)

        # Tamper with the ciphertext (flip a bit in the middle)
        tampered = encrypted[:-5] + chr(ord(encrypted[-5]) ^ 1) + encrypted[-4:]

        with pytest.raises(Exception):
            encryption_service.decrypt(tampered)

    def test_key_derivation_from_env(self):
        """Service derives key from master_key parameter (simulating env var)."""
        # Key should be 32 bytes after HKDF derivation
        service = CredentialEncryptionService(master_key="my-secret-master-key-from-env")
        plaintext = "test-key"
        encrypted = service.encrypt(plaintext)
        decrypted = service.decrypt(encrypted)
        assert decrypted == plaintext

    def test_encrypt_returns_base64_string(self, encryption_service):
        """Encrypted output is base64 encoded string."""
        encrypted = encryption_service.encrypt("test")
        # Should be valid base64
        import base64
        decoded = base64.b64decode(encrypted)
        assert len(decoded) > 0  # nonce (12) + ciphertext + tag (16)