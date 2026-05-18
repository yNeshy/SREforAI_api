"""
Database model for storing rate limits and utilization data.
Stores normalized data fetched by the cron job from various provider admin APIs.
"""

from sqlalchemy import Column, String, Text, DateTime, Integer, Float, JSON, Index
from sqlalchemy.sql import func
from app.core.database import Base


class RateLimitCache(Base):
    """
    Cached rate limits and utilization data for various providers.
    Data is refreshed every 15 minutes by a cron job.
    """
    __tablename__ = "rate_limit_cache"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Provider information
    provider = Column(String(50), nullable=False, index=True)
    api_key_id = Column(String(255), nullable=False, index=True)
    
    # Utilization metrics
    utilization = Column(JSON, nullable=False)
    
    # Rate limit information
    limits = Column(JSON, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Composite index for efficient lookups
    __table_args__ = (
        Index('idx_provider_api_key', 'provider', 'api_key_id'),
    )
    
    def __repr__(self):
        return f"<RateLimitCache(provider={self.provider}, api_key_id={self.api_key_id}, updated_at={self.updated_at})>"
