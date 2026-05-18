"""
Unit tests for authentication flow.
Tests JWT token generation/validation, password hashing, and signup endpoint.
"""

import pytest
from datetime import datetime, timedelta
from app.core.auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    decode_access_token
)


class TestPasswordHashing:
    """Test password hashing and verification."""
    
    def test_password_hashing(self):
        """Test that password hashing produces a hash."""
        password = "SecurePass123"
        hashed = get_password_hash(password)
        
        assert hashed is not None
        assert hashed != password
        assert len(hashed) > 0
    
    def test_password_verification_success(self):
        """Test that correct password verifies successfully."""
        password = "SecurePass123"
        hashed = get_password_hash(password)
        
        assert verify_password(password, hashed) is True
    
    def test_password_verification_failure(self):
        """Test that incorrect password fails verification."""
        password = "SecurePass123"
        wrong_password = "WrongPass456"
        hashed = get_password_hash(password)
        
        assert verify_password(wrong_password, hashed) is False
    
    def test_hash_is_different_for_same_password(self):
        """Test that bcrypt generates different hashes for the same password."""
        password = "SecurePass123"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        
        assert hash1 != hash2  # bcrypt uses salt


class TestJWTToken:
    """Test JWT token generation and validation."""
    
    def test_token_creation(self):
        """Test that JWT token is created successfully."""
        data = {"sub": "test@example.com", "org_id": "test-org-id"}
        token = create_access_token(data)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_token_decoding_success(self):
        """Test that valid token decodes successfully."""
        data = {"sub": "test@example.com", "org_id": "test-org-id"}
        token = create_access_token(data)
        
        decoded = decode_access_token(token)
        
        assert decoded is not None
        assert decoded["sub"] == "test@example.com"
        assert decoded["org_id"] == "test-org-id
    
    def test_token_decoding_failure_invalid_token(self):
        """Test that invalid token returns None."""
        invalid_token = "invalid.token.here"
        
        decoded = decode_access_token(invalid_token)
        
        assert decoded is None
    
    def test_token_expiration(self):
        """Test that expired token returns None."""
        data = {"sub": "test@example.com", "org_id": "test-org-id"}
        # Create token with very short expiration
        token = create_access_token(data, expires_delta=timedelta(seconds=-1))
        
        decoded = decode_access_token(token)
        
        assert decoded is None
    
    def test_token_contains_exp_claim(self):
        """Test that token contains expiration claim."""
        data = {"sub": "test@example.com", "org_id": "test-org-id"}
        token = create_access_token(data)
        
        decoded = decode_access_token(token)
        
        assert "exp" in decoded
        assert isinstance(decoded["exp"], int)


class TestAuthIntegration:
    """Integration tests for auth flow components."""
    
    def test_complete_auth_flow(self):
        """Test complete auth flow: hash password, create token, decode token."""
        password = "SecurePass123"
        email = "test@example.com"
        org_id = "test-org-id"
        
        # Hash password
        hashed = get_password_hash(password)
        assert verify_password(password, hashed)
        
        # Create token
        token_data = {"sub": email, "org_id": org_id}
        token = create_access_token(token_data)
        
        # Decode token
        decoded = decode_access_token(token)
        assert decoded["sub"] == email
        assert decoded["org_id"] == org_id
