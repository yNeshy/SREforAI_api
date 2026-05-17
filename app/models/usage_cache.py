"""
Hourly/Daily usage cache model for tracking token usage and costs.
"""

from sqlalchemy import Column, String, BigInteger, Numeric, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from app.core.database import Base


class HourlyDailyUsageCache(Base):
    """
    Tracks token usage and costs with hourly granularity.
    Enables precise analytics and cost breakdown by model and API key.
    """
    
    __tablename__ = "hourly_daily_usage_cache"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Categorization dimensions
    provider = Column(String(50), nullable=False)  # 'openai', 'anthropic'
    model = Column(String(100), nullable=False)  # 'gpt-4o', 'claude-3-5-sonnet'
    api_key_id = Column(String(255), nullable=False)  # Internal sub-key identifier
    
    # Quantitative metrics
    input_tokens = Column(BigInteger, nullable=False, default=0)
    output_tokens = Column(BigInteger, nullable=False, default=0)
    cached_tokens = Column(BigInteger, nullable=False, default=0)
    
    # Cost tracking (NUMERIC avoids floating-point errors)
    raw_cost_usd = Column(Numeric(12, 6), nullable=False, default=0.000000)
    
    # Time tracking (bucketed to the hour)
    timestamp_bucket = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self) -> str:
        return (
            f"<HourlyDailyUsageCache("
            f"org_id={self.org_id}, "
            f"provider={self.provider}, "
            f"model={self.model}, "
            f"api_key_id={self.api_key_id}, "
            f"timestamp_bucket={self.timestamp_bucket}"
            f")>"
        )
    
    def to_dict(self) -> dict:
        """Convert model to dictionary for API responses."""
        return {
            "id": str(self.id),
            "org_id": str(self.org_id),
            "provider": self.provider,
            "model": self.model,
            "api_key_id": self.api_key_id,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "cached_tokens": self.cached_tokens,
            "raw_cost_usd": float(self.raw_cost_usd),
            "timestamp_bucket": self.timestamp_bucket.isoformat(),
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
