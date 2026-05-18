"""
Unit tests for RateLimitCache model.
Tests the database model for storing rate limit and utilization data.
"""

import pytest
from app.models.rate_limits import RateLimitCache


class TestRateLimitCacheModel:
    """Test RateLimitCache model."""
    
    def test_model_attributes(self):
        """Test that model has all required attributes."""
        cache = RateLimitCache(
            provider="claude",
            api_key_id="test-key-id",
            utilization={"tokens": 1000},
            limits={"rpm": 500}
        )
        
        assert cache.provider == "claude"
        assert cache.api_key_id == "test-key-id"
        assert cache.utilization == {"tokens": 1000}
        assert cache.limits == {"rpm": 500}
    
    def test_model_repr(self):
        """Test model string representation."""
        cache = RateLimitCache(
            provider="claude",
            api_key_id="test-key-id",
            utilization={"tokens": 1000},
            limits={"rpm": 500}
        )
        
        repr_str = repr(cache)
        assert "claude" in repr_str
        assert "test-key-id" in repr_str
    
    def test_model_json_fields(self):
        """Test that JSON fields can store complex data."""
        utilization = {
            "tokens_used_last_24h": 1000,
            "cost_last_24h_usd": 5.50,
            "requests_last_24h": 50
        }
        limits = {
            "requests_per_minute_limit": 60,
            "requests_remaining": 50,
            "input_tokens_per_minute_limit": 32000
        }
        
        cache = RateLimitCache(
            provider="openai",
            api_key_id="test-key-id",
            utilization=utilization,
            limits=limits
        )
        
        assert cache.utilization["tokens_used_last_24h"] == 1000
        assert cache.utilization["cost_last_24h_usd"] == 5.50
        assert cache.limits["requests_per_minute_limit"] == 60
    
    def test_model_all_providers(self):
        """Test that model can store data for all supported providers."""
        providers = ["openai", "claude", "gemini", "deepseek"]
        
        for provider in providers:
            cache = RateLimitCache(
                provider=provider,
                api_key_id=f"test-{provider}",
                utilization={"tokens": 1000},
                limits={"rpm": 500}
            )
            assert cache.provider == provider
