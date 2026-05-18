"""
Factory pattern for creating admin fetchers based on provider enum.
Provides drop-in provider implementations for rate limit and utilization fetching.
"""

from typing import Literal
from app.fetchers.admin_base import BaseAdminFetcher
from app.fetchers.anthropic_admin import AnthropicAdminFetcher
from app.fetchers.openai_admin import OpenAIAdminFetcher
from app.fetchers.gemini_admin import GeminiAdminFetcher
from app.fetchers.deepseek_admin import DeepSeekAdminFetcher


ProviderType = Literal["openai", "claude", "gemini", "deepseek"]


class AdminFetcherFactory:
    """
    Factory class for creating admin fetchers based on provider type.
    Implements the Factory pattern for drop-in provider implementations.
    """
    
    @staticmethod
    def create_fetcher(provider: ProviderType, api_key: str) -> BaseAdminFetcher:
        """
        Create an admin fetcher instance for the specified provider.
        
        Args:
            provider: The provider type (openai, claude, gemini, deepseek).
            api_key: The admin API key for the provider.
            
        Returns:
            An instance of the appropriate admin fetcher.
            
        Raises:
            ValueError: If the provider is not supported.
        """
        fetcher_map = {
            "openai": OpenAIAdminFetcher,
            "claude": AnthropicAdminFetcher,
            "gemini": GeminiAdminFetcher,
            "deepseek": DeepSeekAdminFetcher,
        }
        
        fetcher_class = fetcher_map.get(provider)
        
        if fetcher_class is None:
            raise ValueError(
                f"Unsupported provider: {provider}. "
                f"Supported providers: {', '.join(fetcher_map.keys())}"
            )
        
        return fetcher_class(api_key)
