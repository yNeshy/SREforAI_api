"""
Base fetcher class with common functionality for all API providers.
Implements SRE-grade error handling, retry logic, and schema validation.
"""

import logging
import time
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import httpx
from app.core.exceptions import APIError, RateLimitError, SchemaParsingError
from app.core.retry import RetryStrategy
from app.core.config import settings

logger = logging.getLogger(__name__)


class BaseFetcher(ABC):
    """
    Abstract base class for API fetchers.
    Provides common functionality for HTTP requests, retry logic, and error handling.
    """
    
    def __init__(self, api_key: str):
        """
        Initialize the fetcher with API credentials.
        
        Args:
            api_key: The API key for authentication.
        """
        self.api_key = api_key
        self.base_url: str = ""
        self.retry_strategy = RetryStrategy(
            max_retries=settings.max_retries,
            initial_delay=settings.initial_retry_delay_seconds,
            max_delay=settings.max_retry_delay_seconds,
            exponential_base=settings.retry_exponential_base,
            jitter=True,
        )
        
        # Configure HTTP client with timeouts
        self.client = httpx.Client(
            timeout=httpx.Timeout(
                connect=settings.connection_timeout_seconds,
                read=settings.request_timeout_seconds,
                write=settings.request_timeout_seconds,
                pool=settings.request_timeout_seconds,
            ),
            limits=httpx.Limits(max_keepalive_connections=20, max_connections=100),
        )
    
    @abstractmethod
    def get_base_url(self) -> str:
        """Return the base URL for the API."""
        pass
    
    @abstractmethod
    def get_auth_headers(self) -> Dict[str, str]:
        """Return authentication headers for the API."""
        pass
    
    @abstractmethod
    def fetch_usage_data(
        self,
        start_date: datetime,
        end_date: datetime,
        group_by: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Fetch usage data from the API.
        
        Args:
            start_date: Start date for data fetch.
            end_date: End date for data fetch.
            group_by: List of fields to group by (e.g., ["model", "api_key_id"]).
            
        Returns:
            List of usage data records.
        """
        pass
    
    @abstractmethod
    def parse_response(self, response_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parse API response into standardized format.
        
        Args:
            response_data: Raw API response data.
            
        Returns:
            List of standardized usage records.
        """
        pass
    
    def make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Make HTTP request with retry logic and error handling.
        
        Args:
            method: HTTP method (GET, POST, etc.).
            endpoint: API endpoint path.
            params: Query parameters.
            headers: Additional headers.
            
        Returns:
            Parsed JSON response.
            
        Raises:
            APIError: If request fails after retries.
            RateLimitError: If rate limit is exceeded.
        """
        url = f"{self.base_url}{endpoint}"
        request_headers = self.get_auth_headers()
        if headers:
            request_headers.update(headers)
        
        def _make_request() -> Dict[str, Any]:
            try:
                response = self.client.request(
                    method=method,
                    url=url,
                    params=params,
                    headers=request_headers,
                )
                
                # Handle rate limits
                if response.status_code == 429:
                    retry_after = response.headers.get("Retry-After")
                    retry_after_seconds = int(retry_after) if retry_after else None
                    raise RateLimitError(
                        message=f"Rate limit exceeded for {url}",
                        retry_after=retry_after_seconds,
                        details={"endpoint": endpoint, "params": params}
                    )
                
                # Handle other 4xx errors (client errors)
                if 400 <= response.status_code < 500:
                    raise APIError(
                        message=f"Client error {response.status_code} for {url}",
                        status_code=response.status_code,
                        response_body=response.text,
                        details={"endpoint": endpoint, "params": params}
                    )
                
                # Handle 5xx errors (server errors) - these should be retried
                if response.status_code >= 500:
                    raise APIError(
                        message=f"Server error {response.status_code} for {url}",
                        status_code=response.status_code,
                        response_body=response.text,
                        details={"endpoint": endpoint, "params": params}
                    )
                
                # Successful response
                response.raise_for_status()
                return response.json()
                
            except httpx.TimeoutException as e:
                raise APIError(
                    message=f"Request timeout for {url}",
                    details={"endpoint": endpoint, "params": params}
                ) from e
            except httpx.NetworkError as e:
                raise APIError(
                    message=f"Network error for {url}: {str(e)}",
                    details={"endpoint": endpoint, "params": params}
                ) from e
            except httpx.HTTPStatusError as e:
                raise APIError(
                    message=f"HTTP error for {url}: {str(e)}",
                    status_code=e.response.status_code,
                    response_body=e.response.text,
                    details={"endpoint": endpoint, "params": params}
                ) from e
        
        return self.retry_strategy.execute_with_retry(_make_request)
    
    def validate_schema(self, data: Dict[str, Any], required_fields: List[str]) -> None:
        """
        Validate that response data contains required fields.
        
        Args:
            data: Response data to validate.
            required_fields: List of required field names.
            
        Raises:
            SchemaParsingError: If validation fails.
        """
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            raise SchemaParsingError(
                message=f"Missing required fields in API response: {missing_fields}",
                details={"missing_fields": missing_fields, "data": data}
            )
    
    def close(self):
        """Close the HTTP client."""
        self.client.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
