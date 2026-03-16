"""
Rate limiting for provider adapters.
Implements token bucket algorithm for rate protection across multiple adapters.
"""
from typing import Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import asyncio
from collections import defaultdict


@dataclass
class RateLimitConfig:
    """
    Configuration for rate limiting per provider.
    
    Attributes:
        requests_per_second: Maximum requests per second
        burst_size: Maximum burst size (tokens in bucket at once)
        per_operation: Optional operation-specific limits
    """
    
    requests_per_second: float = 10.0
    burst_size: int = None            # Defaults to requests_per_second if None
    per_operation: Dict[str, float] = field(default_factory=dict)  # {op: req/s}
    
    def __post_init__(self):
        """Set burst size to requests per second if not specified."""
        if self.burst_size is None:
            self.burst_size = max(1, int(self.requests_per_second))


class TokenBucket:
    """
    Token bucket rate limiter.
    
    Maintains a bucket of tokens that refill at a constant rate.
    Each request costs 1 token. When bucket is empty, requests wait.
    """
    
    def __init__(self, capacity: float, refill_rate: float):
        """
        Initialize token bucket.
        
        Args:
            capacity: Maximum tokens in bucket
            refill_rate: Tokens added per second
        """
        self.capacity = capacity
        self.refill_rate = refill_rate  # Tokens per second
        
        self.tokens = capacity  # Start full
        self.last_refill = datetime.utcnow()
        self.lock = asyncio.Lock()
    
    async def acquire(self, tokens: int = 1) -> float:
        """
        Acquire tokens from bucket.
        Blocks until tokens available.
        
        Args:
            tokens: Number of tokens to acquire (default 1)
        
        Returns:
            Wait time in seconds
        """
        async with self.lock:
            # Refill tokens based on time elapsed
            now = datetime.utcnow()
            elapsed = (now - self.last_refill).total_seconds()
            self.tokens = min(self.capacity, self.tokens + (elapsed * self.refill_rate))
            self.last_refill = now
            
            # If not enough tokens, wait
            if self.tokens < tokens:
                wait_time = (tokens - self.tokens) / self.refill_rate
                await asyncio.sleep(wait_time)
                
                # Refill after wait
                self.tokens = self.capacity
                self.last_refill = datetime.utcnow()
            else:
                wait_time = 0.0
            
            # Deduct tokens
            self.tokens -= tokens
            return wait_time
    
    def try_acquire(self, tokens: int = 1) -> bool:
        """
        Try to acquire tokens without blocking.
        
        Args:
            tokens: Number of tokens to acquire
        
        Returns:
            True if acquired, False if not enough tokens
        """
        # Refill tokens based on time elapsed
        now = datetime.utcnow()
        elapsed = (now - self.last_refill).total_seconds()
        self.tokens = min(self.capacity, self.tokens + (elapsed * self.refill_rate))
        self.last_refill = now
        
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        
        return False
    
    async def wait_for_available(self) -> float:
        """
        Wait until at least 1 token is available.
        
        Returns:
            Wait time in seconds
        """
        return await self.acquire(1)
    
    def get_available(self) -> float:
        """Get current available tokens (may be > capacity due to refill)."""
        now = datetime.utcnow()
        elapsed = (now - self.last_refill).total_seconds()
        return min(self.capacity, self.tokens + (elapsed * self.refill_rate))


class RateLimiter:
    """
    Multi-provider rate limiter using token buckets.
    Manages rate limits across multiple providers and operations.
    """
    
    def __init__(self):
        """Initialize rate limiter."""
        self.providers: Dict[str, Dict[str, TokenBucket]] = defaultdict(dict)
        self.config: Dict[str, RateLimitConfig] = {}
        self.lock = asyncio.Lock()
    
    def configure(self, provider: str, config: RateLimitConfig):
        """Configure rate limit for provider."""
        self.config[provider] = config
        
        # Create default bucket for provider
        bucket = TokenBucket(
            capacity=config.burst_size,
            refill_rate=config.requests_per_second
        )
        self.providers[provider]["_default"] = bucket
        
        # Create operation-specific buckets
        for operation, rate in config.per_operation.items():
            bucket = TokenBucket(
                capacity=max(1, int(rate)),
                refill_rate=rate
            )
            self.providers[provider][operation] = bucket
    
    def get_bucket(self, provider: str, operation: str = None) -> Optional[TokenBucket]:
        """Get token bucket for provider/operation."""
        if provider not in self.providers:
            return None
        
        # Try operation-specific bucket
        if operation and operation in self.providers[provider]:
            return self.providers[provider][operation]
        
        # Fallback to default bucket
        return self.providers[provider].get("_default")
    
    async def acquire(self, provider: str, operation: str = None, tokens: int = 1) -> float:
        """
        Acquire tokens for provider operation.
        Blocks until available.
        
        Args:
            provider: Provider name
            operation: Operation name (optional)
            tokens: Number of tokens to acquire
        
        Returns:
            Wait time in seconds
        """
        bucket = self.get_bucket(provider, operation)
        if bucket is None:
            return 0.0  # No rate limit configured
        
        return await bucket.acquire(tokens)
    
    def try_acquire(self, provider: str, operation: str = None, tokens: int = 1) -> bool:
        """
        Try to acquire tokens without blocking.
        
        Args:
            provider: Provider name
            operation: Operation name (optional)
            tokens: Number of tokens to acquire
        
        Returns:
            True if acquired, False otherwise
        """
        bucket = self.get_bucket(provider, operation)
        if bucket is None:
            return True  # No rate limit configured
        
        return bucket.try_acquire(tokens)
    
    async def wait_until_available(self, provider: str, operation: str = None) -> float:
        """Wait until tokens available."""
        bucket = self.get_bucket(provider, operation)
        if bucket is None:
            return 0.0
        
        return await bucket.wait_for_available()
    
    def get_available(self, provider: str, operation: str = None) -> float:
        """Get available tokens for provider."""
        bucket = self.get_bucket(provider, operation)
        if bucket is None:
            return float('inf')  # Unlimited if no config
        
        return bucket.get_available()
    
    def reset(self, provider: str = None):
        """Reset rate limiter for provider or all providers."""
        if provider:
            self.providers.pop(provider, None)
        else:
            self.providers.clear()


# Global rate limiter instance
_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """Get or create global rate limiter instance."""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter


# Pre-configured rate limit configs for common providers

# Gmail API: 1,000,000 per day (best effort: ~12 per second)
GMAIL_RATE_LIMIT = RateLimitConfig(
    requests_per_second=10.0,  # Conservative estimate
    burst_size=50
)

# SendGrid: 100,000 emails per day (best effort: ~1.2 per second)
SENDGRID_RATE_LIMIT = RateLimitConfig(
    requests_per_second=1.0,
    burst_size=10
)

# Google Calendar: 1,000,000 per day (best effort: ~12 per second)
CALENDAR_RATE_LIMIT = RateLimitConfig(
    requests_per_second=10.0,
    burst_size=50
)

# HubSpot API: 100 per 10 seconds (best effort: 10 per second)
HUBSPOT_RATE_LIMIT = RateLimitConfig(
    requests_per_second=10.0,
    burst_size=100,
    per_operation={
        "create_contact": 5.0,      # More conservative for writes
        "update_contact": 5.0,
        "create_deal": 5.0,
        "search_contacts": 3.0,     # More conservative for reads
    }
)

# WhatsApp Cloud API: Varies by tier, conservative estimate
WHATSAPP_RATE_LIMIT = RateLimitConfig(
    requests_per_second=10.0,
    burst_size=50
)

# Fallback generic rate limit
DEFAULT_RATE_LIMIT = RateLimitConfig(
    requests_per_second=10.0,
    burst_size=50
)
