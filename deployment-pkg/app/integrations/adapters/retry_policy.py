"""
Retry policy for provider adapters.
Implements configurable retry strategies with exponential backoff, jitter, and provider-specific rules.
"""
from enum import Enum
from typing import Callable, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import asyncio
import random


class RetryStrategy(str, Enum):
    """Retry strategy types."""
    EXPONENTIAL = "exponential"         # 2^attempt * base_delay
    LINEAR = "linear"                  # attempt * base_delay
    FIBONACCI = "fibonacci"             # Fibonacci sequence
    FIXED = "fixed"                    # Always same delay


@dataclass
class RetryPolicy:
    """
    Configurable retry policy for provider operations.
    
    Attributes:
        max_attempts: Maximum number of retry attempts (>= 1)
        base_delay_seconds: Base delay for first retry
        max_delay_seconds: Maximum delay between retries
        strategy: Retry strategy (exponential, linear, fibonacci, fixed)
        jitter: Add random jitter (0-1) to avoid thundering herd
        retryable_status_codes: HTTP status codes to retry on
        retryable_exceptions: Exception types to retry on
        on_retry_callback: Optional callback on retry attempt
    """
    
    max_attempts: int = 3
    base_delay_seconds: float = 1.0
    max_delay_seconds: float = 60.0
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL
    jitter: float = 0.1  # Add 0-10% random jitter
    
    retryable_status_codes: set = field(default_factory=lambda: {408, 429, 500, 502, 503, 504})
    retryable_exceptions: tuple = field(default_factory=lambda: (
        TimeoutError,
        ConnectionError,
        OSError,
    ))
    
    on_retry_callback: Optional[Callable] = None
    
    def is_retryable(self, attempt: int, status_code: Optional[int] = None, 
                    exception: Optional[Exception] = None) -> bool:
        """
        Check if operation should be retried.
        
        Args:
            attempt: Current attempt number (1-indexed)
            status_code: HTTP status code if applicable
            exception: Exception that occurred if applicable
        
        Returns:
            True if should retry, False otherwise
        """
        if attempt >= self.max_attempts:
            return False
        
        # Check status code
        if status_code is not None:
            return status_code in self.retryable_status_codes
        
        # Check exception type
        if exception is not None:
            return isinstance(exception, self.retryable_exceptions)
        
        return True
    
    def get_delay_seconds(self, attempt: int) -> float:
        """
        Calculate delay for retry attempt.
        
        Args:
            attempt: Attempt number (1-indexed)
        
        Returns:
            Delay in seconds before next retry
        """
        # Calculate base delay
        if self.strategy == RetryStrategy.EXPONENTIAL:
            delay = self.base_delay_seconds * (2 ** (attempt - 1))
        elif self.strategy == RetryStrategy.LINEAR:
            delay = self.base_delay_seconds * attempt
        elif self.strategy == RetryStrategy.FIBONACCI:
            delay = self._fibonacci_delay(attempt)
        else:  # FIXED
            delay = self.base_delay_seconds
        
        # Cap at max delay
        delay = min(delay, self.max_delay_seconds)
        
        # Add jitter
        if self.jitter > 0:
            jitter_amount = delay * self.jitter
            delay = delay + (random.uniform(-jitter_amount, jitter_amount))
            delay = max(0, delay)  # Ensure non-negative
        
        return delay
    
    def _fibonacci_delay(self, n: int) -> float:
        """Calculate fibonacci number for delay."""
        if n <= 1:
            return self.base_delay_seconds
        if n == 2:
            return self.base_delay_seconds
        
        a, b = 1, 1
        for _ in range(n - 2):
            a, b = b, a + b
        
        return self.base_delay_seconds * b
    
    async def execute_with_retry(
        self,
        operation: Callable[..., Any],
        *args,
        **kwargs
    ) -> Any:
        """
        Execute operation with automatic retry on failure.
        
        Args:
            operation: Async callable to execute
            *args: Positional arguments for operation
            **kwargs: Keyword arguments for operation
        
        Returns:
            Result from operation
        
        Raises:
            Last exception from operation if all retries exhausted
        """
        last_exception = None
        
        for attempt in range(1, self.max_attempts + 1):
            try:
                return await operation(*args, **kwargs)
            except Exception as e:
                last_exception = e
                
                # Check if retryable
                if not self.is_retryable(attempt, exception=e):
                    raise
                
                # Execute retry callback if provided
                if self.on_retry_callback:
                    await self.on_retry_callback(attempt, e)
                
                # Calculate and wait for delay
                if attempt < self.max_attempts:
                    delay = self.get_delay_seconds(attempt)
                    await asyncio.sleep(delay)
        
        # All retries exhausted
        raise last_exception


@dataclass
class ProviderRetryConfig:
    """Per-provider retry configuration."""
    
    # Standard retry policy
    default: RetryPolicy = field(default_factory=RetryPolicy)
    
    # Operation-specific overrides
    overrides: dict = field(default_factory=dict)  # {operation_name: RetryPolicy}
    
    # Provider-specific backoff multiplier
    backoff_multiplier: float = 1.0
    
    def get_policy(self, operation: str = None) -> RetryPolicy:
        """Get retry policy for operation, with provider-specific adjustments."""
        # Use operation-specific policy if available
        if operation and operation in self.overrides:
            policy = self.overrides[operation]
        else:
            policy = self.default
        
        # Apply provider-specific backoff multiplier
        if self.backoff_multiplier != 1.0:
            policy = RetryPolicy(
                max_attempts=policy.max_attempts,
                base_delay_seconds=policy.base_delay_seconds * self.backoff_multiplier,
                max_delay_seconds=policy.max_delay_seconds * self.backoff_multiplier,
                strategy=policy.strategy,
                jitter=policy.jitter,
                retryable_status_codes=policy.retryable_status_codes,
                retryable_exceptions=policy.retryable_exceptions,
                on_retry_callback=policy.on_retry_callback,
            )
        
        return policy


# Pre-configured retry policies for common provider types

# Conservative: Few retries, short delays (for operations with strict latency SLAs)
CONSERVATIVE_RETRY = RetryPolicy(
    max_attempts=2,
    base_delay_seconds=0.5,
    max_delay_seconds=5.0,
    strategy=RetryStrategy.EXPONENTIAL,
)

# Moderate: Standard retry behavior
MODERATE_RETRY = RetryPolicy(
    max_attempts=3,
    base_delay_seconds=1.0,
    max_delay_seconds=30.0,
    strategy=RetryStrategy.EXPONENTIAL,
)

# Aggressive: More retries, longer delays (for critical operations)
AGGRESSIVE_RETRY = RetryPolicy(
    max_attempts=5,
    base_delay_seconds=2.0,
    max_delay_seconds=120.0,
    strategy=RetryStrategy.EXPONENTIAL,
)

# Very Aggressive: Maximum retries (for batch operations)
VERY_AGGRESSIVE_RETRY = RetryPolicy(
    max_attempts=10,
    base_delay_seconds=1.0,
    max_delay_seconds=300.0,
    strategy=RetryStrategy.EXPONENTIAL,
)
