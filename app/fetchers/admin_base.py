"""
Base admin fetcher class for fetching current rate limits and token utilization.
Implements Strategy pattern for drop-in provider implementations.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any
from datetime import datetime


class BaseAdminFetcher(ABC):
    """
    Abstract base class for admin API fetchers.
    Provides a common interface for fetching current rate limits and token utilization
    across different providers (OpenAI, Anthropic, Gemini, DeepSeek).
    """
    
    def __init__(self, admin_key: str):
        """
        Initialize the admin fetcher with API credentials.
        
        Args:
            admin_key: The admin API key for authentication.
        """
        self.admin_key = admin_key
    
    @abstractmethod
    def get_current_utilization(self) -> Dict[str, Any]:
        """
        Fetch current token utilization from the provider's admin API.
        
        Returns:
            Dictionary containing current utilization metrics (e.g., tokens used, requests made).
        """
        pass
    
    @abstractmethod
    def get_rate_limits(self) -> Dict[str, Any]:
        """
        Fetch current rate limits from the provider's admin API.
        
        Returns:
            Dictionary containing rate limit information (e.g., requests per minute, tokens per minute).
        """
        pass
    
    def get_utilization_and_limits(self) -> Dict[str, Any]:
        """
        Fetch both current utilization and rate limits in a single call.
        
        Returns:
            Dictionary containing both utilization and limits:
            {
                "utilization": {...},
                "limits": {...},
                "provider": "provider_name",
                "timestamp": "ISO_8601_timestamp"
            }
        """
        return {
            "utilization": self.get_current_utilization(),
            "limits": self.get_rate_limits(),
            "provider": self.__class__.__name__.replace("AdminFetcher", "").lower(),
            "timestamp": datetime.utcnow().isoformat()
        }
