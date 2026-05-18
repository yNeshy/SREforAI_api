"""
Unit tests for admin fetcher factory.
Tests the factory pattern for creating provider-specific fetchers.
"""

import pytest
from app.fetchers.admin_factory import AdminFetcherFactory
from app.fetchers.anthropic_admin import AnthropicAdminFetcher
from app.fetchers.openai_admin import OpenAIAdminFetcher
from app.fetchers.gemini_admin import GeminiAdminFetcher
from app.fetchers.deepseek_admin import DeepSeekAdminFetcher
from app.fetchers.admin_base import BaseAdminFetcher


class TestAdminFetcherFactory:
    """Test admin fetcher factory."""
    
    def test_create_openai_fetcher(self):
        """Test creating OpenAI admin fetcher."""
        fetcher = AdminFetcherFactory.create_fetcher("openai", "sk-test-key")
        
        assert isinstance(fetcher, OpenAIAdminFetcher)
        assert isinstance(fetcher, BaseAdminFetcher)
        assert fetcher.admin_key == "sk-test-key"
    
    def test_create_claude_fetcher(self):
        """Test creating Anthropic admin fetcher."""
        fetcher = AdminFetcherFactory.create_fetcher("claude", "sk-ant-admin-test")
        
        assert isinstance(fetcher, AnthropicAdminFetcher)
        assert isinstance(fetcher, BaseAdminFetcher)
        assert fetcher.admin_key == "sk-ant-admin-test"
    
    def test_create_gemini_fetcher(self):
        """Test creating Gemini admin fetcher."""
        fetcher = AdminFetcherFactory.create_fetcher("gemini", "test-key")
        
        assert isinstance(fetcher, GeminiAdminFetcher)
        assert isinstance(fetcher, BaseAdminFetcher)
        assert fetcher.admin_key == "test-key"
    
    def test_create_deepseek_fetcher(self):
        """Test creating DeepSeek admin fetcher."""
        fetcher = AdminFetcherFactory.create_fetcher("deepseek", "test-key")
        
        assert isinstance(fetcher, DeepSeekAdminFetcher)
        assert isinstance(fetcher, BaseAdminFetcher)
        assert fetcher.admin_key == "test-key"
    
    def test_unsupported_provider_raises_error(self):
        """Test that unsupported provider raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            AdminFetcherFactory.create_fetcher("invalid", "test-key")
        
        assert "Unsupported provider" in str(exc_info.value)
        assert "invalid" in str(exc_info.value)
    
    def test_all_supported_providers(self):
        """Test that all supported providers can be created."""
        supported_providers = ["openai", "claude", "gemini", "deepseek"]
        
        for provider in supported_providers:
            fetcher = AdminFetcherFactory.create_fetcher(provider, "test-key")
            assert isinstance(fetcher, BaseAdminFetcher)
            assert fetcher.admin_key == "test-key"
