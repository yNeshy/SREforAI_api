"""
Custom exceptions for the AI Cost Monitoring Platform.
Provides specific exception types for better error handling and monitoring.
"""


class BaseApplicationError(Exception):
    """Base exception for all application errors."""
    
    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class ConfigurationError(BaseApplicationError):
    """Raised when there's a configuration error."""
    pass


class EncryptionError(BaseApplicationError):
    """Raised when encryption/decryption fails."""
    pass


class DatabaseError(BaseApplicationError):
    """Raised when database operations fail."""
    pass


class APIError(BaseApplicationError):
    """Base exception for API-related errors."""
    
    def __init__(
        self,
        message: str,
        status_code: int = None,
        response_body: str = None,
        details: dict = None
    ):
        self.status_code = status_code
        self.response_body = response_body
        super().__init__(message, details)


class RateLimitError(APIError):
    """Raised when API rate limits are exceeded."""
    
    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: int = None,
        details: dict = None
    ):
        self.retry_after = retry_after
        super().__init__(message, status_code=429, details=details)


class AuthenticationError(APIError):
    """Raised when API authentication fails."""
    
    def __init__(self, message: str = "Authentication failed", details: dict = None):
        super().__init__(message, status_code=401, details=details)


class ValidationError(BaseApplicationError):
    """Raised when data validation fails."""
    pass


class IngestionError(BaseApplicationError):
    """Raised when data ingestion fails."""
    pass


class SchemaParsingError(BaseApplicationError):
    """Raised when API response schema doesn't match expectations."""
    pass
