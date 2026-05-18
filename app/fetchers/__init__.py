"""
Fetchers package initialization.
"""

from app.fetchers.base import BaseFetcher
from app.fetchers.openai_fetcher import OpenAIFetcher
from app.fetchers.anthropic_fetcher import AnthropicFetcher
from app.fetchers.admin_base import BaseAdminFetcher
from app.fetchers.anthropic_admin import AnthropicAdminFetcher
from app.fetchers.openai_admin import OpenAIAdminFetcher
from app.fetchers.gemini_admin import GeminiAdminFetcher
from app.fetchers.deepseek_admin import DeepSeekAdminFetcher
from app.fetchers.admin_factory import AdminFetcherFactory

__all__ = [
    "BaseFetcher",
    "OpenAIFetcher",
    "AnthropicFetcher",
    "BaseAdminFetcher",
    "AnthropicAdminFetcher",
    "OpenAIAdminFetcher",
    "GeminiAdminFetcher",
    "DeepSeekAdminFetcher",
    "AdminFetcherFactory",
]
