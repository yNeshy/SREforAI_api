"""
Security module for encryption and decryption of sensitive data.
Uses Fernet symmetric encryption for API keys.
"""

from cryptography.fernet import Fernet
from typing import Optional
import base64
import os


class EncryptionManager:
    """Manages encryption and decryption of sensitive data."""
    
    def __init__(self, encryption_key: Optional[str] = None):
        """
        Initialize the encryption manager.
        
        Args:
            encryption_key: Base64-encoded encryption key. If None, generates a new key.
        """
        if encryption_key:
            # Ensure the key is properly formatted for Fernet
            if len(encryption_key) == 44:  # Standard Fernet key length
                self.key = encryption_key.encode()
            else:
                # Derive a proper Fernet key from the provided key
                self.key = base64.urlsafe_b64encode(
                    encryption_key.encode()[:32].ljust(32, b'\0')
                )
        else:
            self.key = Fernet.generate_key()
        
        self.cipher = Fernet(self.key)
    
    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt a plaintext string.
        
        Args:
            plaintext: The string to encrypt.
            
        Returns:
            Base64-encoded encrypted string.
        """
        if not plaintext:
            return ""
        encrypted_bytes = self.cipher.encrypt(plaintext.encode())
        return encrypted_bytes.decode()
    
    def decrypt(self, ciphertext: str) -> str:
        """
        Decrypt a ciphertext string.
        
        Args:
            ciphertext: Base64-encoded encrypted string.
            
        Returns:
            Decrypted plaintext string.
            
        Raises:
            ValueError: If decryption fails.
        """
        if not ciphertext:
            return ""
        try:
            decrypted_bytes = self.cipher.decrypt(ciphertext.encode())
            return decrypted_bytes.decode()
        except Exception as e:
            raise ValueError(f"Decryption failed: {str(e)}")
    
    def get_key(self) -> str:
        """Get the encryption key (for storage/backup purposes)."""
        return self.key.decode()


# Global encryption manager instance
def get_encryption_manager() -> EncryptionManager:
    """Factory function to get the encryption manager instance."""
    from app.core.config import settings
    return EncryptionManager(settings.encryption_key)
