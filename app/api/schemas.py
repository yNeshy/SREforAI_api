"""
Pydantic schemas for request/response validation.
Provides type-safe data validation and serialization for API endpoints.
"""

from datetime import datetime
from typing import Optional, List, Literal
from pydantic import BaseModel, Field, EmailStr, validator


# ============================================================================
# Authentication Schemas
# ============================================================================

class SignupRequest(BaseModel):
    """Request schema for user/organization signup."""
    organization_name: str = Field(..., min_length=1, max_length=255, description="Organization name")
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, max_length=128, description="User password (min 8 characters)")
    
    @validator('password')
    def password_strength(cls, v):
        """Validate password strength."""
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v


class SignupResponse(BaseModel):
    """Response schema for successful signup."""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    organization_id: str = Field(..., description="Organization UUID")
    email: str = Field(..., description="User email")


class APIKeyRequest(BaseModel):
    """Request schema for adding/updating API keys."""
    provider: Literal['openai', 'anthropic'] = Field(..., description="API provider")
    admin_api_key: str = Field(..., min_length=1, description="Admin API key to encrypt and store")


class APIKeyResponse(BaseModel):
    """Response schema for API key operations."""
    message: str = Field(..., description="Operation result message")
    provider: str = Field(..., description="API provider")


# ============================================================================
# Metrics Schemas
# ============================================================================

class MetricsSummaryRequest(BaseModel):
    """Request schema for metrics summary endpoint."""
    start_date: datetime = Field(..., description="Start date for metrics range")
    end_date: datetime = Field(..., description="End date for metrics range")
    
    @validator('end_date')
    def end_date_after_start_date(cls, v, values):
        """Validate end_date is after start_date."""
        if 'start_date' in values and v <= values['start_date']:
            raise ValueError('end_date must be after start_date')
        return v


class MetricsSummaryResponse(BaseModel):
    """Response schema for metrics summary."""
    total_cost_usd: float = Field(..., description="Total cost in USD")
    total_input_tokens: int = Field(..., description="Total input tokens")
    total_output_tokens: int = Field(..., description="Total output tokens")
    total_cached_tokens: int = Field(..., description="Total cached tokens")
    total_requests: int = Field(..., description="Total number of requests")
    start_date: datetime = Field(..., description="Start date of the range")
    end_date: datetime = Field(..., description="End date of the range")


class MetricsBreakdownRequest(BaseModel):
    """Request schema for metrics breakdown endpoint."""
    start_date: datetime = Field(..., description="Start date for metrics range")
    end_date: datetime = Field(..., description="End date for metrics range")
    group_by: Literal['model', 'provider', 'api_key_id'] = Field(
        ...,
        description="Grouping dimension for breakdown"
    )
    
    @validator('end_date')
    def end_date_after_start_date(cls, v, values):
        """Validate end_date is after start_date."""
        if 'start_date' in values and v <= values['start_date']:
            raise ValueError('end_date must be after start_date')
        return v


class MetricsBreakdownItem(BaseModel):
    """Single item in metrics breakdown response."""
    group_key: str = Field(..., description="The grouping dimension value")
    total_cost_usd: float = Field(..., description="Total cost for this group")
    input_tokens: int = Field(..., description="Input tokens for this group")
    output_tokens: int = Field(..., description="Output tokens for this group")
    cached_tokens: int = Field(..., description="Cached tokens for this group")
    request_count: int = Field(..., description="Number of requests for this group")


class MetricsBreakdownResponse(BaseModel):
    """Response schema for metrics breakdown."""
    breakdown: List[MetricsBreakdownItem] = Field(..., description="List of breakdown items")
    start_date: datetime = Field(..., description="Start date of the range")
    end_date: datetime = Field(..., description="End date of the range")
    group_by: str = Field(..., description="Grouping dimension used")


class LeakDetectorInsight(BaseModel):
    """Single cost-saving insight from leak detector."""
    insight_type: str = Field(..., description="Type of insight (e.g., cache_efficiency, anomaly)")
    description: str = Field(..., description="Human-readable description of the insight")
    severity: Literal['low', 'medium', 'high'] = Field(..., description="Severity level")
    potential_savings_usd: Optional[float] = Field(None, description="Estimated potential savings in USD")
    metadata: dict = Field(default_factory=dict, description="Additional metadata for the insight")


class LeakDetectorResponse(BaseModel):
    """Response schema for leak detector endpoint."""
    insights: List[LeakDetectorInsight] = Field(..., description="List of cost-saving insights")
    total_insights: int = Field(..., description="Total number of insights")
    generated_at: datetime = Field(..., description="Timestamp when insights were generated")


# ============================================================================
# Context Schemas
# ============================================================================

class OrganizationContext(BaseModel):
    """Organization context injected by authentication dependency."""
    org_id: str = Field(..., description="Organization UUID")
    email: str = Field(..., description="User email")
    
    class Config:
        """Pydantic configuration."""
        arbitrary_types_allowed = True
