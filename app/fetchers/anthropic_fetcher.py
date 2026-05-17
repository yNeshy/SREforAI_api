"""
Anthropic API fetcher for cost and usage data.
Queries the Anthropic Usage Report API with SRE-grade error handling.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from app.fetchers.base import BaseFetcher
from app.core.exceptions import SchemaParsingError

logger = logging.getLogger(__name__)


class AnthropicFetcher(BaseFetcher):
    """
    Fetcher for Anthropic Usage Report API.
    Endpoint: GET https://api.anthropic.com/v1/organizations/usage_report/messages
    """
    
    def __init__(self, api_key: str):
        """
        Initialize Anthropic fetcher.
        
        Args:
            api_key: Anthropic organization API key.
        """
        super().__init__(api_key)
        self.base_url = "https://api.anthropic.com/v1"
    
    def get_base_url(self) -> str:
        """Return Anthropic API base URL."""
        return self.base_url
    
    def get_auth_headers(self) -> Dict[str, str]:
        """Return Anthropic authentication headers."""
        return {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }
    
    def fetch_usage_data(
        self,
        start_date: datetime,
        end_date: datetime,
        group_by: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch usage data from Anthropic Usage Report API.
        
        Args:
            start_date: Start date for data fetch.
            end_date: End date for data fetch.
            group_by: List of fields to group by (e.g., ["model", "api_key_ids"]).
                      Defaults to ["model", "api_key_ids"].
        
        Returns:
            List of standardized usage records with fields:
            - provider: "anthropic"
            - model: Model name
            - api_key_id: API key identifier
            - input_tokens: Number of input tokens
            - output_tokens: Number of output tokens
            - cached_tokens: Number of cached tokens (prompt caching)
            - raw_cost_usd: Cost in USD
            - timestamp_bucket: Hourly timestamp bucket
        """
        if group_by is None:
            group_by = ["model", "api_key_ids"]
        
        logger.info(
            f"Fetching Anthropic usage data from {start_date} to {end_date} "
            f"grouped by {group_by}"
        )
        
        # Anthropic usage report API uses daily bucketing
        params = {
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "group_by": ",".join(group_by),
        }
        
        response_data = self.make_request(
            method="GET",
            endpoint="/organizations/usage_report/messages",
            params=params,
        )
        
        # Validate response schema
        self.validate_schema(response_data, ["data"])
        
        # Parse response into standardized format
        parsed_records = self.parse_response(response_data)
        
        logger.info(f"Fetched {len(parsed_records)} Anthropic usage records")
        return parsed_records
    
    def parse_response(self, response_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parse Anthropic API response into standardized format.
        
        Args:
            response_data: Raw API response from Anthropic usage report endpoint.
            
        Returns:
            List of standardized usage records.
        """
        records = []
        
        if "data" not in response_data:
            logger.warning(f"No data field in Anthropic response: {response_data}")
            return records
        
        for item in response_data["data"]:
            try:
                # Extract fields from Anthropic response
                # Anthropic usage report structure may vary, adapt as needed
                record = {
                    "provider": "anthropic",
                    "model": item.get("model", "unknown"),
                    "api_key_id": item.get("api_key_ids", ["unknown"])[0] if item.get("api_key_ids") else "unknown",
                    "input_tokens": int(item.get("input_tokens", 0) or 0),
                    "output_tokens": int(item.get("output_tokens", 0) or 0),
                    "cached_tokens": int(item.get("cache_creation_input_tokens", 0) or 0) + int(item.get("cache_read_input_tokens", 0) or 0),
                    "raw_cost_usd": float(item.get("cost", 0) or 0),
                    "timestamp_bucket": self._parse_timestamp(item.get("timestamp")),
                }
                
                # Validate required fields
                if not record["model"] or record["model"] == "unknown":
                    logger.warning(f"Skipping record with missing model: {item}")
                    continue
                
                records.append(record)
                
            except (ValueError, TypeError, IndexError) as e:
                logger.error(f"Error parsing Anthropic record: {e}, item: {item}")
                continue
        
        return records
    
    def _parse_timestamp(self, timestamp_str: Optional[str]) -> datetime:
        """
        Parse timestamp from Anthropic response.
        
        Args:
            timestamp_str: Timestamp string from API.
            
        Returns:
            Parsed datetime object.
        """
        if not timestamp_str:
            return datetime.utcnow()
        
        # Try common timestamp formats
        formats = [
            "%Y-%m-%dT%H:%M:%S.%fZ",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%d",
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(timestamp_str, fmt)
            except ValueError:
                continue
        
        logger.warning(f"Could not parse timestamp: {timestamp_str}, using current time")
        return datetime.utcnow()
    
    def fetch_daily_usage(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """
        Fetch daily usage summary from Anthropic.
        
        Args:
            start_date: Start date.
            end_date: End date.
            
        Returns:
            Daily usage summary data.
        """
        params = {
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
        }
        
        return self.make_request(
            method="GET",
            endpoint="/organizations/usage_report/messages",
            params=params,
        )
