"""
Core configuration module for the AI Cost Monitoring Platform.
Environment-based configuration with type safety and validation.
"""

import os
from typing import Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Application
    app_name: str = "AI Cost Monitoring Platform"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # Database
    database_url: str = Field(
        default="postgresql://user:password@localhost:5432/ai_cost_monitor",
        description="PostgreSQL connection URL"
    )
    
    # Security
    encryption_key: str = Field(
        ...,
        description="Fernet encryption key for API key storage"
    )
    
    # API Rate Limiting (SRE-grade defaults)
    openai_rate_limit_requests_per_minute: int = 3000
    openai_rate_limit_tokens_per_minute: int = 200000
    anthropic_rate_limit_requests_per_minute: int = 1000
    anthropic_rate_limit_tokens_per_minute: int = 80000
    
    # Retry Configuration
    max_retries: int = 5
    initial_retry_delay_seconds: float = 1.0
    max_retry_delay_seconds: float = 60.0
    retry_exponential_base: float = 2.0
    
    # Timeout Configuration
    request_timeout_seconds: float = 30.0
    connection_timeout_seconds: float = 10.0
    
    # Celery Configuration
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"
    
    # Ingestion Configuration
    ingestion_batch_size_days: int = 1
    ingestion_lookback_days: int = 30
    
    @field_validator("encryption_key")
    @classmethod
    def validate_encryption_key(cls, v: str) -> str:
        """Validate encryption key is properly formatted."""
        if len(v) < 32:
            raise ValueError("Encryption key must be at least 32 characters")
        return v
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()
