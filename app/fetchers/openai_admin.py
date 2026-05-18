"""
OpenAI Admin API fetcher for current rate limits and token utilization.
"""

from typing import Dict, Any
from datetime import datetime, timedelta, timezone
import requests
from app.fetchers.admin_base import BaseAdminFetcher


class OpenAIAdminFetcher(BaseAdminFetcher):
    """
    Admin fetcher for OpenAI API.
    Fetches current rate limits and token utilization using admin API keys.
    """
    
    def __init__(self, admin_key: str):
        """
        Initialize OpenAI admin fetcher.
        
        Args:
            admin_key: OpenAI admin API key.
        """
        super().__init__(admin_key)
        self.base_url = "https://api.openai.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.admin_key}",
            "Content-Type": "application/json",
            "User-Agent": "SRECostPlatform/1.0.0"
        }
    
    def get_current_utilization(self) -> Dict[str, Any]:
        """
        Fetch current token utilization from OpenAI's admin API.
        
        Returns:
            Dictionary containing current utilization metrics.
        """
        try:
            # OpenAI doesn't have a direct utilization endpoint
            # We'll fetch usage data for the current billing period
            endpoint = f"{self.base_url}/usage"
            params = {
                "start_date": (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d"),
                "end_date": datetime.now(timezone.utc).strftime("%Y-%m-%d")
            }
            
            response = requests.get(endpoint, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # Extract utilization from the usage data
            total_tokens = 0
            total_cost = 0.0
            total_requests = 0
            
            if "data" in data:
                for item in data["data"]:
                    total_tokens += int(item.get("n_context_tokens_total", 0) or 0)
                    total_tokens += int(item.get("n_generated_tokens_total", 0) or 0)
                    total_cost += float(item.get("cost_in_usd", 0) or 0)
                    total_requests += 1
            
            return {
                "tokens_used_last_24h": total_tokens,
                "cost_last_24h_usd": total_cost,
                "requests_last_24h": total_requests
            }
            
        except Exception as e:
            # Return empty utilization if fetch fails
            return {
                "tokens_used_last_24h": 0,
                "cost_last_24h_usd": 0.0,
                "requests_last_24h": 0,
                "error": str(e)
            }
    
    def get_rate_limits(self) -> Dict[str, Any]:
        """
        Fetch current rate limits from OpenAI's admin API.
        
        OpenAI provides rate limit information via the /rate_limits endpoint.
        
        Returns:
            Dictionary containing rate limit information.
        """
        try:
            endpoint = f"{self.base_url}/rate_limits"
            response = requests.get(endpoint, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # Extract rate limits from the response
            limits = {}
            
            if "data" in data:
                for item in data["data"]:
                    model = item.get("model", "unknown")
                    limits[model] = {
                        "rpm_limit": item.get("limit", 0),
                        "rpm_remaining": item.get("remaining", 0),
                        "reset_time": item.get("reset_at")
                    }
            
            return limits
            
        except Exception as e:
            # Return empty limits if fetch fails
            return {
                "error": str(e)
            }
