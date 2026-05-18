"""
Anthropic Admin API fetcher for current rate limits and token utilization.
Based on the provided pseudo code with SRE-grade error handling.
"""

from typing import Dict, Any
from datetime import datetime, timedelta, timezone
import requests
from app.fetchers.admin_base import BaseAdminFetcher


class AnthropicAdminFetcher(BaseAdminFetcher):
    """
    Admin fetcher for Anthropic API.
    Fetches current rate limits and token utilization using admin API keys.
    """
    
    def __init__(self, admin_key: str):
        """
        Initialize Anthropic admin fetcher.
        
        Args:
            admin_key: Anthropic admin API key (must start with "sk-ant-admin").
            
        Raises:
            ValueError: If the key is not an admin key.
        """
        if not admin_key.startswith("sk-ant-admin"):
            raise ValueError("Must use an Anthropic Admin key (sk-ant-admin...) to pull metadata reports.")
        
        super().__init__(admin_key)
        self.base_url = "https://api.anthropic.com/v1/organizations"
        self.headers = {
            "x-api-key": self.admin_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
            "User-Agent": "SRECostPlatform/1.0.0"
        }
    
    def get_current_utilization(self) -> Dict[str, Any]:
        """
        Fetch current token utilization from Anthropic's admin API.
        
        Returns:
            Dictionary containing current utilization metrics.
        """
        # Fetch usage data for the last day to get current utilization
        try:
            usage_data = self.fetch_historical_costs_and_usage(days_back=1)
            
            # Extract utilization from the usage data
            # This is a simplified extraction - adjust based on actual API response structure
            utilization = {
                "tokens_used_last_24h": self._extract_total_tokens(usage_data.get("usage_data", {})),
                "cost_last_24h_usd": self._extract_total_cost(usage_data.get("cost_data", {})),
                "requests_last_24h": self._extract_total_requests(usage_data.get("usage_data", {}))
            }
            
            return utilization
            
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
        Fetch current rate limits from Anthropic's admin API.
        
        Because Anthropic doesn't have a static config API for limits, this executes
        an ultra-low-max-token sample call to capture the capacity fields returned
        in the rate-limit headers.
        
        Returns:
            Dictionary containing rate limit information.
        """
        return self.extract_live_rate_limits(model="claude-3-5-sonnet")
    
    def fetch_historical_costs_and_usage(self, days_back: int = 1) -> Dict[str, Any]:
        """
        Queries Anthropic's Admin logs to retrieve absolute tokens consumed
        and raw financial costs, grouped cleanly by active model profiles.
        
        Args:
            days_back: Number of days to look back for historical data.
            
        Returns:
            Dictionary containing usage_data and cost_data.
        """
        # Format ISO strings to define window bounds
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(days=days_back)
        
        endpoint = f"{self.base_url}/usage_report/messages"
        params = {
            "starting_at": start_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "ending_at": end_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "bucket_width": "1d",
            "group_by[]": "model"
        }
        
        try:
            # 1. Fetch Token metrics
            usage_response = requests.get(endpoint, headers=self.headers, params=params, timeout=30)
            usage_response.raise_for_status()
            
            # 2. Fetch Dollar financial metrics
            cost_endpoint = f"{self.base_url}/cost_report"
            cost_response = requests.get(cost_endpoint, headers=self.headers, params=params, timeout=30)
            cost_response.raise_for_status()
            
            return {
                "usage_data": usage_response.json(),
                "cost_data": cost_response.json()
            }
        except requests.exceptions.RequestException as e:
            # SRE Practice: In your actual codebase, hook this into an explicit fallback retry loop
            print(f"Failed to query Anthropic Admin API: {e}")
            raise
    
    def extract_live_rate_limits(self, model: str = "claude-3-5-sonnet") -> Dict[str, int]:
        """
        Because Anthropic doesn't have a static config API for limits, execute
        an ultra-low-max-token sample call to capture the capacity fields returned
        in the rate-limit headers.
        
        Args:
            model: The model to use for the sample call.
            
        Returns:
            Dictionary containing rate limit information from headers.
        """
        inference_url = "https://api.anthropic.com/v1/messages"
        payload = {
            "model": model,
            "max_tokens": 1,
            "messages": [{"role": "user", "content": "ping"}]
        }
        
        try:
            # Execute mock call against standard message endpoint
            response = requests.post(inference_url, headers=self.headers, json=payload, timeout=30)
            response.raise_for_status()
            
            headers = response.headers
            return {
                "requests_per_minute_limit": int(headers.get("anthropic-ratelimit-requests-limit", 0)),
                "requests_remaining": int(headers.get("anthropic-ratelimit-requests-remaining", 0)),
                "input_tokens_per_minute_limit": int(headers.get("anthropic-ratelimit-input-tokens-limit", 0)),
                "input_tokens_remaining": int(headers.get("anthropic-ratelimit-input-tokens-remaining", 0)),
                "output_tokens_per_minute_limit": int(headers.get("anthropic-ratelimit-output-tokens-limit", 0)),
            }
        except requests.exceptions.RequestException as e:
            print(f"Failed to extract header rate limits: {e}")
            return {}
    
    def _extract_total_tokens(self, usage_data: Dict[str, Any]) -> int:
        """Extract total tokens from usage data."""
        try:
            if "data" in usage_data and isinstance(usage_data["data"], list):
                total = 0
                for item in usage_data["data"]:
                    total += int(item.get("input_tokens", 0) or 0)
                    total += int(item.get("output_tokens", 0) or 0)
                return total
        except (KeyError, TypeError, ValueError):
            pass
        return 0
    
    def _extract_total_cost(self, cost_data: Dict[str, Any]) -> float:
        """Extract total cost from cost data."""
        try:
            if "data" in cost_data and isinstance(cost_data["data"], list):
                total = 0.0
                for item in cost_data["data"]:
                    total += float(item.get("cost", 0) or 0)
                return total
        except (KeyError, TypeError, ValueError):
            pass
        return 0.0
    
    def _extract_total_requests(self, usage_data: Dict[str, Any]) -> int:
        """Extract total requests from usage data."""
        try:
            if "data" in usage_data and isinstance(usage_data["data"], list):
                return len(usage_data["data"])
        except (KeyError, TypeError):
            pass
        return 0
