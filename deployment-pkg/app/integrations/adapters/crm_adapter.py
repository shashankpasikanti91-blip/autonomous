"""
CRM service adapter wrapping CRMService.
Provides unified error handling, retry logic, and rate limiting for HubSpot CRM.
"""
from typing import Optional, Dict, Any
import logging

from app.services.crm_service import get_crm_service, CRMService
from .base_adapter import BaseAdapter, AdapterRequest, AdapterResponse
from .errors import (
    AdapterError,
    ErrorCategory,
    ProviderConnectionError,
    ProviderAuthError,
    ProviderRateLimitError,
    ProviderValidationError,
    ProviderNotFoundError,
    ErrorSeverity,
)
from .retry_policy import ProviderRetryConfig, MODERATE_RETRY, AGGRESSIVE_RETRY
from .rate_limiter import RateLimitConfig, HUBSPOT_RATE_LIMIT


logger = logging.getLogger(__name__)


class CRMAdapter(BaseAdapter):
    """
    Adapter for CRM service (HubSpot).
    
    Handles:
    - Contact, deal, and activity operations
    - Rate limiting (10 req/s with operation-specific overrides)
    - Retry logic with moderate backoff
    - Error categorization and logging
    - Health monitoring
    """
    
    def __init__(
        self,
        crm_service: Optional[CRMService] = None,
        retry_config: Optional[ProviderRetryConfig] = None,
        rate_limit_config: Optional[RateLimitConfig] = None,
    ):
        """
        Initialize CRM adapter.
        
        Args:
            crm_service: CRMService instance (gets singleton if not provided)
            retry_config: Retry configuration
            rate_limit_config: Rate limit configuration
        """
        self.crm_service = crm_service or get_crm_service()
        
        # Moderate retry for CRM operations
        if retry_config is None:
            retry_config = ProviderRetryConfig(
                default=MODERATE_RETRY,
                overrides={
                    "search_contacts": AGGRESSIVE_RETRY,  # Search can be expensive
                }
            )
        
        # Use HubSpot rate limit
        if rate_limit_config is None:
            rate_limit_config = HUBSPOT_RATE_LIMIT
        
        super().__init__(
            provider_name="crm_hubspot",
            retry_config=retry_config,
            rate_limit_config=rate_limit_config,
        )
    
    async def health_check(self) -> bool:
        """
        Check CRM service health.
        
        Tests connectivity by attempting simple API call.
        
        Returns:
            True if service is healthy
        """
        try:
            # Try to get a non-existent contact to test API connectivity
            # We expect 404, which means API is working
            try:
                await self.crm_service.get_contact("test-nonexistent-id")
            except Exception as e:
                # 404 is expected, any other error indicates a real problem
                if "404" not in str(e):
                    return False
            
            return True
        except Exception as e:
            logger.error(f"CRM health check failed: {e}")
            return False
    
    async def execute_operation(
        self,
        request: AdapterRequest
    ) -> AdapterResponse:
        """
        Execute CRM operation.
        
        Supported operations:
        - create_contact: Create new contact
        - get_contact: Get contact by ID
        - update_contact: Update contact
        - create_deal: Create deal and associate with contact
        - log_activity: Log activity (email, call, meeting, etc)
        - search_contacts: Search contacts by criteria
        """
        operation = request.operation
        
        try:
            if operation == "create_contact":
                return await self._create_contact(request)
            
            elif operation == "get_contact":
                return await self._get_contact(request)
            
            elif operation == "update_contact":
                return await self._update_contact(request)
            
            elif operation == "create_deal":
                return await self._create_deal(request)
            
            elif operation == "log_activity":
                return await self._log_activity(request)
            
            elif operation == "search_contacts":
                return await self._search_contacts(request)
            
            else:
                error = ProviderValidationError(
                    provider=self.provider_name,
                    operation=operation,
                    message=f"Unknown operation: {operation}",
                )
                return AdapterResponse(
                    success=False,
                    data=None,
                    error=error,
                    correlation_id=request.correlation_id,
                )
        
        except AdapterError as e:
            return AdapterResponse(
                success=False,
                data=None,
                error=e,
                correlation_id=request.correlation_id,
            )
        except Exception as e:
            logger.error(f"Unexpected error in CRM adapter: {e}", exc_info=True)
            error = AdapterError(
                provider=self.provider_name,
                operation=operation,
                category=ErrorCategory.UNKNOWN,
                message=f"Unexpected error: {str(e)}",
                correlation_id=request.correlation_id,
                original_error=e,
            )
            return AdapterResponse(
                success=False,
                data=None,
                error=error,
                correlation_id=request.correlation_id,
            )
    
    async def _create_contact(self, request: AdapterRequest) -> AdapterResponse:
        """Handle create_contact operation."""
        params = request.parameters
        
        # Require at least email or phone
        if not params.get("email") and not params.get("phone"):
            raise ProviderValidationError(
                provider=self.provider_name,
                operation="create_contact",
                message="Either email or phone required",
            )
        
        try:
            result = await self.crm_service.create_contact(
                email=params.get("email"),
                first_name=params.get("first_name"),
                last_name=params.get("last_name"),
                phone=params.get("phone"),
                company=params.get("company"),
                custom_properties=params.get("custom_properties", {}),
            )
            
            return AdapterResponse(
                success=True,
                data=result,
                correlation_id=request.correlation_id,
            )
        except Exception as e:
            raise self._map_crm_error(e, "create_contact", request)
    
    async def _get_contact(self, request: AdapterRequest) -> AdapterResponse:
        """Handle get_contact operation."""
        params = request.parameters
        
        if "contact_id" not in params:
            raise ProviderValidationError(
                provider=self.provider_name,
                operation="get_contact",
                message="contact_id required",
            )
        
        try:
            result = await self.crm_service.get_contact(params["contact_id"])
            
            if result is None:
                raise ProviderNotFoundError(
                    provider=self.provider_name,
                    operation="get_contact",
                    resource_id=params["contact_id"],
                    correlation_id=request.correlation_id,
                )
            
            return AdapterResponse(
                success=True,
                data=result,
                correlation_id=request.correlation_id,
            )
        except Exception as e:
            raise self._map_crm_error(e, "get_contact", request)
    
    async def _update_contact(self, request: AdapterRequest) -> AdapterResponse:
        """Handle update_contact operation."""
        params = request.parameters
        
        if "contact_id" not in params:
            raise ProviderValidationError(
                provider=self.provider_name,
                operation="update_contact",
                message="contact_id required",
            )
        
        try:
            result = await self.crm_service.update_contact(
                contact_id=params["contact_id"],
                email=params.get("email"),
                first_name=params.get("first_name"),
                last_name=params.get("last_name"),
                phone=params.get("phone"),
                company=params.get("company"),
                custom_properties=params.get("custom_properties", {}),
            )
            
            return AdapterResponse(
                success=True,
                data=result,
                correlation_id=request.correlation_id,
            )
        except Exception as e:
            raise self._map_crm_error(e, "update_contact", request)
    
    async def _create_deal(self, request: AdapterRequest) -> AdapterResponse:
        """Handle create_deal operation."""
        params = request.parameters
        
        if "deal_name" not in params:
            raise ProviderValidationError(
                provider=self.provider_name,
                operation="create_deal",
                message="deal_name required",
            )
        
        try:
            result = await self.crm_service.create_deal(
                deal_name=params["deal_name"],
                deal_stage=params.get("deal_stage", "negotiation"),
                deal_amount=params.get("deal_amount"),
                contact_id=params.get("contact_id"),
                custom_properties=params.get("custom_properties", {}),
            )
            
            return AdapterResponse(
                success=True,
                data=result,
                correlation_id=request.correlation_id,
            )
        except Exception as e:
            raise self._map_crm_error(e, "create_deal", request)
    
    async def _log_activity(self, request: AdapterRequest) -> AdapterResponse:
        """Handle log_activity operation."""
        params = request.parameters
        
        required = ["contact_id", "activity_type"]
        missing = [p for p in required if p not in params]
        if missing:
            raise ProviderValidationError(
                provider=self.provider_name,
                operation="log_activity",
                message=f"Missing required: {missing}",
            )
        
        try:
            result = await self.crm_service.log_activity(
                contact_id=params["contact_id"],
                activity_type=params["activity_type"],
                title=params.get("title"),
                description=params.get("description"),
                notes=params.get("notes"),
            )
            
            return AdapterResponse(
                success=True,
                data=result,
                correlation_id=request.correlation_id,
            )
        except Exception as e:
            raise self._map_crm_error(e, "log_activity", request)
    
    async def _search_contacts(self, request: AdapterRequest) -> AdapterResponse:
        """Handle search_contacts operation."""
        params = request.parameters
        
        if "query" not in params:
            raise ProviderValidationError(
                provider=self.provider_name,
                operation="search_contacts",
                message="query required",
            )
        
        try:
            result = await self.crm_service.search_contacts(params["query"])
            
            return AdapterResponse(
                success=True,
                data=result,
                correlation_id=request.correlation_id,
            )
        except Exception as e:
            raise self._map_crm_error(e, "search_contacts", request)
    
    def _map_crm_error(
        self,
        exc: Exception,
        operation: str,
        request: AdapterRequest,
    ) -> AdapterError:
        """Map CRM service exceptions to adapter errors."""
        
        # Connection errors
        if isinstance(exc, (ConnectionError, OSError)):
            return ProviderConnectionError(
                provider=self.provider_name,
                message=f"Failed to connect to CRM: {str(exc)}",
                original_error=exc,
                correlation_id=request.correlation_id,
            )
        
        # Authentication errors
        if "401" in str(exc) or "unauthorized" in str(exc).lower():
            return ProviderAuthError(
                provider=self.provider_name,
                message="CRM authentication failed",
                original_error=exc,
                correlation_id=request.correlation_id,
            )
        
        # Rate limiting
        if "429" in str(exc) or "rate" in str(exc).lower():
            return ProviderRateLimitError(
                provider=self.provider_name,
                message="CRM rate limited",
                original_error=exc,
                correlation_id=request.correlation_id,
            )
        
        # Not found
        if "404" in str(exc) or "not found" in str(exc).lower():
            return ProviderNotFoundError(
                provider=self.provider_name,
                operation=operation,
                resource_id="unknown",
                original_error=exc,
                correlation_id=request.correlation_id,
            )
        
        # Default
        return AdapterError(
            provider=self.provider_name,
            operation=operation,
            category=ErrorCategory.UNKNOWN,
            message=f"CRM error: {str(exc)}",
            original_error=exc,
            correlation_id=request.correlation_id,
        )


# Global CRM adapter instance
_crm_adapter: Optional[CRMAdapter] = None


def get_crm_adapter() -> CRMAdapter:
    """Get or create global CRM adapter."""
    global _crm_adapter
    if _crm_adapter is None:
        _crm_adapter = CRMAdapter()
    return _crm_adapter
