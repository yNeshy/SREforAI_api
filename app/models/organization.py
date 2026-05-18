"""
Organization model with encrypted API key storage.
"""

from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from app.core.database import Base


class Organization(Base):
    """
    Organization model storing client information and encrypted API keys.
    """
    
    __tablename__ = "organizations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    
    # Encrypted API keys (never store raw keys!)
    openai_api_key_encrypted = Column(String, nullable=True)
    anthropic_api_key_encrypted = Column(String, nullable=True)
    gemini_api_key_encrypted = Column(String, nullable=True)
    deepseek_api_key_encrypted = Column(String, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self) -> str:
        return f"<Organization(id={self.id}, name={self.name})>"
