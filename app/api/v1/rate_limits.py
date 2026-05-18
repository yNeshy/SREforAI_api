"""
Rate limits endpoint for fetching current token utilization and limits.
Reads cached data from database that is refreshed every 15 minutes by cron job.
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.api.schemas import RateLimitRequest, RateLimitResponse
from app.core.database import get_db
from app.models.rate_limits import RateLimitCache

router = APIRouter()


@router.post("/rate-limits", response_model=RateLimitResponse)
async def get_rate_limits(request: RateLimitRequest, db: Session = Depends(get_db)):
    """
    Fetch current token utilization and rate limits for a given provider.
    
    This endpoint:
    - Accepts a provider enum (openai, claude, gemini, deepseek) and API key
    - Reads cached data from the database (refreshed every 15 minutes by cron job)
    - Returns both current utilization and rate limits
    
    Args:
        request: RateLimitRequest with provider and api_key
        db: Database session
        
    Returns:
        RateLimitResponse with utilization, limits, provider, and timestamp
        
    Raises:
        HTTPException: If provider is unsupported or no cached data is found
    """
    try:
        # Use API key as the identifier for the cache
        api_key_id = request.api_key
        
        # Query the database for cached rate limit data
        cache = db.query(RateLimitCache).filter(
            RateLimitCache.provider == request.provider,
            RateLimitCache.api_key_id == api_key_id
        ).first()
        
        if not cache:
            raise HTTPException(
                status_code=404,
                detail=f"No cached rate limit data found for provider '{request.provider}'. "
                       f"Data may not have been fetched yet by the cron job."
            )
        
        # Return the cached data
        return RateLimitResponse(
            utilization=cache.utilization,
            limits=cache.limits,
            provider=cache.provider,
            timestamp=cache.updated_at.isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch rate limits: {str(e)}"
        )
