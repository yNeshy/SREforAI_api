"""
Cron job to fetch rate limits and utilization data from provider admin APIs.
Runs every 15 minutes to refresh cached data in the database.
"""

import logging
from datetime import datetime
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.rate_limits import RateLimitCache
from app.fetchers.admin_factory import AdminFetcherFactory

logger = logging.getLogger(__name__)


def fetch_and_store_rate_limits(db: Session, provider: str, api_key: str, api_key_id: str):
    """
    Fetch rate limits and utilization data for a provider and store in database.
    
    Args:
        db: Database session
        provider: Provider name (openai, claude, gemini, deepseek)
        api_key: Admin API key for the provider
        api_key_id: Identifier for the API key (for tracking)
    """
    try:
        # Create fetcher using factory
        fetcher = AdminFetcherFactory.create_fetcher(provider, api_key)
        
        # Fetch utilization and limits
        result = fetcher.get_utilization_and_limits()
        
        # Check if existing record exists
        existing = db.query(RateLimitCache).filter(
            RateLimitCache.provider == provider,
            RateLimitCache.api_key_id == api_key_id
        ).first()
        
        if existing:
            # Update existing record
            existing.utilization = result["utilization"]
            existing.limits = result["limits"]
            existing.updated_at = datetime.utcnow()
            logger.info(f"Updated rate limit cache for {provider} (api_key_id: {api_key_id})")
        else:
            # Create new record
            cache = RateLimitCache(
                provider=provider,
                api_key_id=api_key_id,
                utilization=result["utilization"],
                limits=result["limits"]
            )
            db.add(cache)
            logger.info(f"Created rate limit cache for {provider} (api_key_id: {api_key_id})")
        
        db.commit()
        
    except Exception as e:
        logger.error(f"Failed to fetch and store rate limits for {provider}: {e}")
        db.rollback()
        raise


def fetch_all_rate_limits():
    """
    Fetch rate limits for all configured providers and API keys.
    This function is called by the cron job every 15 minutes.
    """
    logger.info("Starting rate limits fetch job")
    
    db = next(get_db())
    
    try:
        # Get all organizations with stored API keys
        from app.models.organization import Organization
        organizations = db.query(Organization).all()
        
        for org in organizations:
            # Fetch for each provider if API key is stored
            if org.openai_api_key_encrypted:
                try:
                    from app.core.security import get_encryption_manager
                    encryption_manager = get_encryption_manager()
                    openai_key = encryption_manager.decrypt(org.openai_api_key_encrypted)
                    fetch_and_store_rate_limits(db, "openai", openai_key, str(org.id))
                except Exception as e:
                    logger.error(f"Failed to fetch OpenAI rate limits for org {org.id}: {e}")
            
            if org.anthropic_api_key_encrypted:
                try:
                    from app.core.security import get_encryption_manager
                    encryption_manager = get_encryption_manager()
                    anthropic_key = encryption_manager.decrypt(org.anthropic_api_key_encrypted)
                    fetch_and_store_rate_limits(db, "claude", anthropic_key, str(org.id))
                except Exception as e:
                    logger.error(f"Failed to fetch Anthropic rate limits for org {org.id}: {e}")
            
            if org.gemini_api_key_encrypted:
                try:
                    from app.core.security import get_encryption_manager
                    encryption_manager = get_encryption_manager()
                    gemini_key = encryption_manager.decrypt(org.gemini_api_key_encrypted)
                    fetch_and_store_rate_limits(db, "gemini", gemini_key, str(org.id))
                except Exception as e:
                    logger.error(f"Failed to fetch Gemini rate limits for org {org.id}: {e}")
            
            if org.deepseek_api_key_encrypted:
                try:
                    from app.core.security import get_encryption_manager
                    encryption_manager = get_encryption_manager()
                    deepseek_key = encryption_manager.decrypt(org.deepseek_api_key_encrypted)
                    fetch_and_store_rate_limits(db, "deepseek", deepseek_key, str(org.id))
                except Exception as e:
                    logger.error(f"Failed to fetch DeepSeek rate limits for org {org.id}: {e}")
        
        logger.info("Completed rate limits fetch job")
        
    finally:
        db.close()


if __name__ == "__main__":
    # Run the fetch job
    fetch_all_rate_limits()
