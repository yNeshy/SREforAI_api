"""
SRE-grade retry mechanism with exponential backoff.
Handles rate limits (429s) and transient 5xx errors intelligently.
"""

import time
import random
import logging
from typing import Callable, Type, Tuple, Optional, Any
from functools import wraps
from app.core.exceptions import RateLimitError, APIError

logger = logging.getLogger(__name__)


class RetryStrategy:
    """
    Configurable retry strategy with exponential backoff.
    Implements SRE-grade retry logic with jitter.
    """
    
    def __init__(
        self,
        max_retries: int = 5,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        retryable_exceptions: Tuple[Type[Exception], ...] = (Exception,),
        retryable_status_codes: Tuple[int, ...] = (429, 500, 502, 503, 504),
    ):
        """
        Initialize retry strategy.
        
        Args:
            max_retries: Maximum number of retry attempts.
            initial_delay: Initial delay between retries in seconds.
            max_delay: Maximum delay between retries in seconds.
            exponential_base: Base for exponential backoff calculation.
            jitter: Add random jitter to avoid thundering herd.
            retryable_exceptions: Exception types that should trigger retries.
            retryable_status_codes: HTTP status codes that should trigger retries.
        """
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.retryable_exceptions = retryable_exceptions
        self.retryable_status_codes = retryable_status_codes
    
    def calculate_delay(self, attempt: int) -> float:
        """
        Calculate delay for given retry attempt with exponential backoff.
        
        Args:
            attempt: Current retry attempt number (0-indexed).
            
        Returns:
            Delay in seconds.
        """
        # Exponential backoff: delay = initial_delay * (base ^ attempt)
        delay = self.initial_delay * (self.exponential_base ** attempt)
        
        # Cap at maximum delay
        delay = min(delay, self.max_delay)
        
        # Add jitter to avoid thundering herd (±25%)
        if self.jitter:
            delay = delay * (0.75 + random.random() * 0.5)
        
        return delay
    
    def should_retry(
        self,
        exception: Exception,
        attempt: int
    ) -> bool:
        """
        Determine if operation should be retried based on exception.
        
        Args:
            exception: The exception that occurred.
            attempt: Current retry attempt number.
            
        Returns:
            True if should retry, False otherwise.
        """
        if attempt >= self.max_retries:
            return False
        
        # Check if exception is retryable
        if isinstance(exception, self.retryable_exceptions):
            return True
        
        # Check for specific API errors
        if isinstance(exception, RateLimitError):
            return True
        
        if isinstance(exception, APIError):
            if exception.status_code in self.retryable_status_codes:
                return True
        
        return False
    
    def execute_with_retry(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """
        Execute function with retry logic.
        
        Args:
            func: Function to execute.
            *args: Positional arguments for function.
            **kwargs: Keyword arguments for function.
            
        Returns:
            Function return value.
            
        Raises:
            The last exception if all retries are exhausted.
        """
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                
                if not self.should_retry(e, attempt):
                    logger.error(
                        f"Non-retryable exception on attempt {attempt + 1}: {str(e)}"
                    )
                    raise
                
                if attempt < self.max_retries:
                    delay = self.calculate_delay(attempt)
                    
                    # Log retry with context
                    logger.warning(
                        f"Retryable exception on attempt {attempt + 1}/{self.max_retries}: "
                        f"{str(e)}. Retrying in {delay:.2f}s..."
                    )
                    
                    # Handle RateLimitError with custom retry-after if available
                    if isinstance(e, RateLimitError) and e.retry_after:
                        delay = max(delay, e.retry_after)
                        logger.info(f"Using RateLimit retry-after: {delay}s")
                    
                    time.sleep(delay)
        
        # All retries exhausted
        logger.error(f"All {self.max_retries} retries exhausted. Last error: {str(last_exception)}")
        raise last_exception


def retry_with_backoff(
    max_retries: int = 5,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
):
    """
    Decorator for automatic retry with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts.
        initial_delay: Initial delay between retries in seconds.
        max_delay: Maximum delay between retries in seconds.
        exponential_base: Base for exponential backoff calculation.
        jitter: Add random jitter to avoid thundering herd.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            strategy = RetryStrategy(
                max_retries=max_retries,
                initial_delay=initial_delay,
                max_delay=max_delay,
                exponential_base=exponential_base,
                jitter=jitter
            )
            return strategy.execute_with_retry(func, *args, **kwargs)
        return wrapper
    return decorator
