"""
Fernet symmetric encryption utilities for storing sensitive credentials.
Uses the app's SECRET_KEY to derive a deterministic Fernet key.
"""

import base64
import hashlib
import logging

from cryptography.fernet import Fernet, InvalidToken

logger = logging.getLogger(__name__)


def get_fernet_key(secret_key):
    """
    Derive a 32-byte Fernet key from the app's SECRET_KEY.

    Args:
        secret_key: Application SECRET_KEY string

    Returns:
        URL-safe base64-encoded 32-byte key suitable for Fernet

    Raises:
        ValueError: If secret_key is None or empty
    """
    if not secret_key:
        raise ValueError("SECRET_KEY is required for encryption")

    key_bytes = hashlib.sha256(secret_key.encode('utf-8')).digest()
    return base64.urlsafe_b64encode(key_bytes)


def encrypt_value(value, secret_key):
    """
    Encrypt a plaintext string using Fernet symmetric encryption.

    Args:
        value: Plaintext string to encrypt
        secret_key: Application SECRET_KEY for key derivation

    Returns:
        Encrypted string (base64-encoded), or None if value is None/empty
    """
    if not value:
        return None

    if not isinstance(value, str):
        value = str(value)

    try:
        fernet_instance = Fernet(get_fernet_key(secret_key))
        return fernet_instance.encrypt(value.encode('utf-8')).decode('utf-8')
    except Exception as encryption_error:
        logger.error(f"Encryption failed: {encryption_error}")
        raise


def decrypt_value(encrypted_value, secret_key):
    """
    Decrypt a Fernet-encrypted string back to plaintext.

    Args:
        encrypted_value: Encrypted string (base64-encoded)
        secret_key: Application SECRET_KEY (must match the key used for encryption)

    Returns:
        Decrypted plaintext string, or None if encrypted_value is None/empty

    Raises:
        InvalidToken: If the SECRET_KEY doesn't match or data is corrupted
    """
    if not encrypted_value:
        return None

    if not isinstance(encrypted_value, str):
        encrypted_value = str(encrypted_value)

    try:
        fernet_instance = Fernet(get_fernet_key(secret_key))
        return fernet_instance.decrypt(encrypted_value.encode('utf-8')).decode('utf-8')
    except InvalidToken:
        logger.error(
            "Decryption failed: invalid token. "
            "This usually means SECRET_KEY has changed since the value was encrypted."
        )
        return None
    except Exception as decryption_error:
        logger.error(f"Decryption failed: {decryption_error}")
        return None
