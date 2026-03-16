"""
Credential lifecycle manager for OAuth tokens and API keys.
Handles token refresh, expiration detection, and credential rotation.
"""
from typing import Dict, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging
import asyncio


logger = logging.getLogger(__name__)


@dataclass
class Credential:
    """Represents a credential (OAuth token or API key)."""
    credential_id: str          # Unique identifier
    provider: str               # Provider name (gmail, hubspot, etc)
    credential_type: str        # Type (oauth_token, api_key, etc)
    access_token: str           # Primary token/key
    refresh_token: Optional[str] = None  # Refresh token if available
    expires_at: Optional[datetime] = None  # Expiration time
    metadata: Dict[str, Any] = field(default_factory=dict)  # Additional data
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    last_used_at: Optional[datetime] = None
    
    def is_expired(self, buffer_seconds: int = 300) -> bool:
        """
        Check if credential is expired.
        
        Args:
            buffer_seconds: Buffer before expiration (300s = 5 min default)
        
        Returns:
            True if expired or will expire soon
        """
        if self.expires_at is None:
            return False  # No expiration
        
        return datetime.utcnow() >= (self.expires_at - timedelta(seconds=buffer_seconds))
    
    def mark_used(self):
        """Mark credential as used."""
        self.last_used_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize credential."""
        return {
            "credential_id": self.credential_id,
            "provider": self.provider,
            "credential_type": self.credential_type,
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
        }


class CredentialManager:
    """
    Manages credential lifecycle.
    
    Provides:
    - Credential storage and retrieval
    - Token refresh logic
    - Expiration detection
    - Automatic refresh before expiration
    - Rotation support
    """
    
    def __init__(self):
        """Initialize credential manager."""
        self.credentials: Dict[str, Credential] = {}  # {credential_id: credential}
        self.refresh_callbacks: Dict[str, any] = {}  # {provider: refresh_callback}
        self.rotation_history: Dict[str, list] = {}  # {credential_id: [old_credentials]}
        self.lock = asyncio.Lock()
        
        logger.info("Credential manager initialized")
    
    def register_refresh_callback(
        self,
        provider: str,
        callback,
    ):
        """
        Register callback to refresh provider credentials.
        
        Callback signature: async callback(credential: Credential) -> Credential
        """
        self.refresh_callbacks[provider] = callback
        logger.info(f"Registered refresh callback for {provider}")
    
    async def store_credential(
        self,
        credential: Credential,
    ):
        """Store credential."""
        async with self.lock:
            self.credentials[credential.credential_id] = credential
            logger.debug(f"Stored credential: {credential.credential_id}")
    
    async def get_credential(
        self,
        credential_id: str,
        auto_refresh: bool = True,
    ) -> Optional[Credential]:
        """
        Get credential by ID.
        
        Args:
            credential_id: Credential identifier
            auto_refresh: Automatically refresh if expired
        
        Returns:
            Credential or None if not found
        """
        async with self.lock:
            credential = self.credentials.get(credential_id)
            
            if credential is None:
                return None
            
            # Mark as used
            credential.mark_used()
            
            # Auto-refresh if expired
            if auto_refresh and credential.is_expired():
                logger.info(f"Credential expired, attempting refresh: {credential_id}")
                credential = await self._refresh_credential(credential)
        
        return credential
    
    async def get_credentials_by_provider(
        self,
        provider: str,
    ) -> list[Credential]:
        """Get all credentials for provider."""
        async with self.lock:
            return [
                c for c in self.credentials.values()
                if c.provider == provider
            ]
    
    async def revoke_credential(self, credential_id: str):
        """Revoke credential by removing it."""
        async with self.lock:
            self.credentials.pop(credential_id, None)
            logger.info(f"Revoked credential: {credential_id}")
    
    async def rotate_credential(
        self,
        old_credential_id: str,
        new_credential: Credential,
    ):
        """
        Rotate credential to new one.
        
        Args:
            old_credential_id: Old credential ID to replace
            new_credential: New credential
        """
        async with self.lock:
            # Save old credential to history
            if old_credential_id in self.credentials:
                old = self.credentials[old_credential_id]
                if new_credential.credential_id not in self.rotation_history:
                    self.rotation_history[new_credential.credential_id] = []
                self.rotation_history[new_credential.credential_id].append(old)
            
            # Store new credential
            self.credentials[new_credential.credential_id] = new_credential
            
            # Optionally remove old credential
            self.credentials.pop(old_credential_id, None)
            
            logger.info(
                f"Rotated credential: {old_credential_id} -> {new_credential.credential_id}"
            )
    
    async def _refresh_credential(
        self,
        credential: Credential,
    ) -> Credential:
        """
        Refresh credential using provider callback.
        
        Args:
            credential: Credential to refresh
        
        Returns:
            Refreshed credential
        """
        provider = credential.provider
        
        # Get refresh callback for provider
        callback = self.refresh_callbacks.get(provider)
        if callback is None:
            logger.warning(f"No refresh callback registered for {provider}")
            return credential
        
        try:
            # Call provider refresh
            refreshed = await callback(credential)
            
            # Update stored credential
            self.credentials[credential.credential_id] = refreshed
            logger.info(f"Refreshed credential: {credential.credential_id}")
            
            return refreshed
        
        except Exception as e:
            logger.error(f"Credential refresh failed: {e}")
            return credential
    
    async def cleanup_expired(self, keep_history: bool = True):
        """
        Clean up expired credentials.
        
        Args:
            keep_history: Keep old credentials in history
        """
        async with self.lock:
            expired = [
                cred_id for cred_id, cred in self.credentials.items()
                if cred.is_expired(buffer_seconds=0)  # Already expired, not soon
            ]
            
            for cred_id in expired:
                if keep_history:
                    self.rotation_history.setdefault(cred_id, []).append(
                        self.credentials[cred_id]
                    )
                self.credentials.pop(cred_id, None)
                logger.debug(f"Cleaned up credential: {cred_id}")
            
            if expired:
                logger.info(f"Cleaned up {len(expired)} expired credentials")
    
    async def get_expiring_soon(self, seconds: int = 300) -> list[Credential]:
        """
        Get credentials expiring soon.
        
        Args:
            seconds: Time threshold (default 5 minutes)
        
        Returns:
            List of credentials expiring soon
        """
        async with self.lock:
            return [
                cred for cred in self.credentials.values()
                if cred.expires_at and
                datetime.utcnow() < cred.expires_at < (datetime.utcnow() + timedelta(seconds=seconds))
            ]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get credential manager statistics."""
        providers = {}
        for cred in self.credentials.values():
            if cred.provider not in providers:
                providers[cred.provider] = {"total": 0, "expired": 0, "expiring_soon": 0}
            
            providers[cred.provider]["total"] += 1
            
            if cred.is_expired():
                providers[cred.provider]["expired"] += 1
            elif cred.is_expired(buffer_seconds=3600):  # Expiring within 1 hour
                providers[cred.provider]["expiring_soon"] += 1
        
        return {
            "total_credentials": len(self.credentials),
            "providers": providers,
            "rotation_history_size": sum(len(v) for v in self.rotation_history.values()),
        }


# Global credential manager instance
_credential_manager: Optional[CredentialManager] = None


def get_credential_manager() -> CredentialManager:
    """Get or create global credential manager."""
    global _credential_manager
    if _credential_manager is None:
        _credential_manager = CredentialManager()
    return _credential_manager
