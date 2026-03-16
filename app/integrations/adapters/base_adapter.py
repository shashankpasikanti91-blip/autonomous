"""
Base adapter for all provider integrations.

Provides:
- Unified interface for all providers
- Automatic error handling and categorization
- Retry logic with exponential backoff
- Rate limiting protection
- Health checking
- Correlation ID tracking for observability
- Fallback strategy support
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Callable, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import asyncio
import uuid
import logging

from .errors import AdapterError, ErrorCategory, ErrorSeverity
from .retry_policy import RetryPolicy, ProviderRetryConfig, MODERATE_RETRY
from .rate_limiter import RateLimitConfig, get_rate_limiter


logger = logging.getLogger(__name__)


@dataclass
class AdapterRequest:
    """Request metadata for adapter operation."""
    operation: str                      # Operation name
    parameters: Dict[str, Any]          # Operation parameters
    correlation_id: str = field(default_factory=lambda: str(uuid.uuid4()))  # For tracing
    timeout_seconds: float = 30.0       # Operation timeout
    retries_allowed: bool = True        # Allow automatic retries


@dataclass
class AdapterResponse:
    """Response from adapter operation."""
    success: bool
    data: Any                           # Response data on success
    error: Optional[AdapterError] = None  # Error on failure
    operation_took_seconds: float = 0.0
    correlation_id: str = ""
    retry_count: int = 0                # Number of retries performed


class BaseAdapter(ABC):
    """
    Abstract base adapter for provider integrations.
    
    Provides framework for:
    - Unified error handling
    - Retry policies
    - Rate limiting
    - Health checking
    - Observability integration
    """
    
    def __init__(
        self,
        provider_name: str,
        retry_config: Optional[ProviderRetryConfig] = None,
        rate_limit_config: Optional[RateLimitConfig] = None,
        fallback_adapter: Optional['BaseAdapter'] = None,
    ):
        """
        Initialize adapter.
        
        Args:
            provider_name: Name of provider (gmail, hubspot, etc)
            retry_config: Retry policy configuration
            rate_limit_config: Rate limiting configuration
            fallback_adapter: Fallback adapter if this one fails
        """
        self.provider_name = provider_name
        self.retry_config = retry_config or ProviderRetryConfig()
        self.fallback_adapter = fallback_adapter
        
        # Set up rate limiting
        self.rate_limiter = get_rate_limiter()
        if rate_limit_config:
            self.rate_limiter.configure(provider_name, rate_limit_config)
        
        # Health tracking
        self.last_health_check: Optional[datetime] = None
        self.last_health_status: bool = True
        self.consecutive_failures = 0
        self.total_requests = 0
        self.total_failures = 0
        self.total_retries = 0
        
        logger.info(f"Initialized adapter for {provider_name}")
    
    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check provider connectivity and health.
        
        Returns:
            True if provider is healthy, False otherwise
        """
        pass
    
    @abstractmethod
    async def execute_operation(
        self,
        request: AdapterRequest
    ) -> AdapterResponse:
        """
        Execute provider operation.
        
        Must be implemented by subclasses to call specific provider APIs.
        
        Args:
            request: Operation request with parameters
        
        Returns:
            AdapterResponse with result or error
        """
        pass
    
    async def call(
        self,
        operation: str,
        parameters: Dict[str, Any] = None,
        correlation_id: str = None,
        timeout_seconds: float = 30.0,
    ) -> AdapterResponse:
        """
        Execute operation with full retry, rate limiting, and error handling.
        
        Args:
            operation: Operation name
            parameters: Operation parameters
            correlation_id: Correlation ID for tracing (generated if not provided)
            timeout_seconds: Operation timeout
        
        Returns:
            AdapterResponse with result or error
        """
        if parameters is None:
            parameters = {}
        
        if correlation_id is None:
            correlation_id = str(uuid.uuid4())
        
        request = AdapterRequest(
            operation=operation,
            parameters=parameters,
            correlation_id=correlation_id,
            timeout_seconds=timeout_seconds,
        )
        
        # Rate limit
        await self.rate_limiter.acquire(self.provider_name, operation)
        
        # Execute with retry
        self.total_requests += 1
        retry_count = 0
        start_time = datetime.utcnow()
        
        try:
            response = await self._execute_with_retry(request)
            
            if response.success:
                self.consecutive_failures = 0
            else:
                self.total_failures += 1
                self.consecutive_failures += 1
            
            response.retry_count = retry_count
            return response
        
        except AdapterError as e:
            self.total_failures += 1
            self.consecutive_failures += 1
            
            # Log error
            logger.error(
                f"Adapter error in {self.provider_name}",
                extra={
                    "provider": self.provider_name,
                    "operation": operation,
                    "error": str(e),
                    "correlation_id": correlation_id,
                }
            )
            
            # Attempt fallback if available and appropriate
            if self._should_use_fallback(e):
                response = await self._call_fallback(
                    operation, parameters, correlation_id, timeout_seconds
                )
                response.correlation_id = correlation_id
                return response
            
            # Return error response
            elapsed = (datetime.utcnow() - start_time).total_seconds()
            return AdapterResponse(
                success=False,
                data=None,
                error=e,
                operation_took_seconds=elapsed,
                correlation_id=correlation_id,
                retry_count=retry_count,
            )
    
    async def _execute_with_retry(self, request: AdapterRequest) -> AdapterResponse:
        """Execute operation with retry logic."""
        policy = self.retry_config.get_policy(request.operation)
        
        async def operation_wrapper() -> AdapterResponse:
            """Wrap operation with timeout."""
            try:
                return await asyncio.wait_for(
                    self.execute_operation(request),
                    timeout=request.timeout_seconds
                )
            except asyncio.TimeoutError:
                error = AdapterError(
                    provider=self.provider_name,
                    operation=request.operation,
                    category=ErrorCategory.SERVICE_UNAVAILABLE,
                    message=f"Operation timeout after {request.timeout_seconds}s",
                    correlation_id=request.correlation_id,
                    severity=ErrorSeverity.MEDIUM,
                    is_retryable=True,
                )
                return AdapterResponse(
                    success=False,
                    data=None,
                    error=error,
                    correlation_id=request.correlation_id,
                )
        
        # Execute operation
        response = await operation_wrapper()
        
        # If successful, return
        if response.success:
            return response
        
        # If error not retryable, return
        if not response.error or not response.error.is_retryable:
            return response
        
        # Retry if configured
        if not request.retries_allowed or policy.max_attempts <= 1:
            return response
        
        # Perform retries
        for attempt in range(2, policy.max_attempts + 1):
            self.total_retries += 1
            
            # Calculate delay
            delay = policy.get_delay_seconds(attempt - 1)
            logger.info(
                f"Retrying {self.provider_name}.{request.operation} "
                f"(attempt {attempt}/{policy.max_attempts}) after {delay:.2f}s",
                extra={"correlation_id": request.correlation_id}
            )
            
            await asyncio.sleep(delay)
            
            # Try again
            response = await operation_wrapper()
            if response.success:
                return response
        
        return response
    
    def _should_use_fallback(self, error: AdapterError) -> bool:
        """Check if should attempt fallback adapter."""
        return (
            self.fallback_adapter is not None and
            error.should_fallback()
        )
    
    async def _call_fallback(
        self,
        operation: str,
        parameters: Dict[str, Any],
        correlation_id: str,
        timeout_seconds: float,
    ) -> AdapterResponse:
        """Call fallback adapter."""
        logger.info(
            f"Using fallback adapter for {self.provider_name}.{operation}",
            extra={"correlation_id": correlation_id}
        )
        
        return await self.fallback_adapter.call(
            operation=operation,
            parameters=parameters,
            correlation_id=correlation_id,
            timeout_seconds=timeout_seconds,
        )
    
    async def check_health(self, force: bool = False) -> bool:
        """
        Check provider health with caching.
        
        Args:
            force: Skip cache and re-check
        
        Returns:
            True if healthy, False otherwise
        """
        # Return cached result if recent and force=False
        if (not force and 
            self.last_health_check and
            (datetime.utcnow() - self.last_health_check) < timedelta(seconds=60)):
            return self.last_health_status
        
        try:
            self.last_health_status = await self.health_check()
            self.last_health_check = datetime.utcnow()
            
            if self.last_health_status:
                self.consecutive_failures = 0
            
            return self.last_health_status
        except Exception as e:
            logger.error(f"Health check failed for {self.provider_name}: {e}")
            self.last_health_status = False
            self.last_health_check = datetime.utcnow()
            return False
    
    def is_healthy(self) -> bool:
        """Get last known health status without performing check."""
        return self.last_health_status
    
    def is_degraded(self) -> bool:
        """Check if adapter is in degraded mode (failures detected)."""
        return self.consecutive_failures > 2  # Degraded after 3 consecutive failures
    
    def get_stats(self) -> Dict[str, Any]:
        """Get adapter statistics."""
        return {
            "provider": self.provider_name,
            "total_requests": self.total_requests,
            "total_failures": self.total_failures,
            "failure_rate": (
                self.total_failures / self.total_requests 
                if self.total_requests > 0 else 0.0
            ),
            "consecutive_failures": self.consecutive_failures,
            "total_retries": self.total_retries,
            "is_healthy": self.last_health_status,
            "is_degraded": self.is_degraded(),
            "last_health_check": self.last_health_check.isoformat() if self.last_health_check else None,
        }
