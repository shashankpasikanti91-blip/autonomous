"""
OAuth Manager for handling OAuth2 flows.

Supports:
- Google OAuth (Gmail, Google Calendar)
- HubSpot OAuth
- Incremental authorization and token refresh
"""

import json
import base64
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from urllib.parse import urlencode

import aiohttp
from utils.logger import get_logger
from utils.errors import AuthenticationException
from config.settings import settings


logger = get_logger(__name__)


class OAuthToken:
    """Represents an OAuth token with expiry tracking."""
    
    def __init__(
        self,
        access_token: str,
        token_type: str = "Bearer",
        expires_in: Optional[int] = None,
        refresh_token: Optional[str] = None,
        scope: Optional[str] = None
    ):
        self.access_token = access_token
        self.token_type = token_type
        self.refresh_token = refresh_token
        self.scope = scope
        self.created_at = datetime.utcnow()
        self.expires_in = expires_in
        self.expires_at = (
            self.created_at + timedelta(seconds=expires_in)
            if expires_in
            else None
        )
    
    def is_expired(self, buffer_seconds: int = 300) -> bool:
        """Check if token is expired (with buffer for safety)."""
        if not self.expires_at:
            return False
        return datetime.utcnow() >= (self.expires_at - timedelta(seconds=buffer_seconds))
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize token to dictionary."""
        return {
            "access_token": self.access_token,
            "token_type": self.token_type,
            "refresh_token": self.refresh_token,
            "scope": self.scope,
            "expires_in": self.expires_in,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OAuthToken":
        """Create token from dictionary."""
        token = cls(
            access_token=data["access_token"],
            token_type=data.get("token_type", "Bearer"),
            expires_in=data.get("expires_in"),
            refresh_token=data.get("refresh_token"),
            scope=data.get("scope")
        )
        if data.get("expires_at"):
            token.expires_at = datetime.fromisoformat(data["expires_at"])
        return token


class GoogleOAuthManager:
    """Manager for Google OAuth 2.0 flows."""
    
    GOOGLE_OAUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
    GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
    
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        scopes: Optional[list] = None
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.scopes = scopes or []
        self.logger = get_logger(f"{__name__}.GoogleOAuthManager")
    
    def get_authorization_url(self, state: Optional[str] = None, incremental: bool = False) -> str:
        """
        Generate authorization URL for user consent.
        
        Args:
            state: State parameter for CSRF protection
            incremental: Use incremental authorization
        """
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": " ".join(self.scopes),
            "access_type": "offline",
            "prompt": "consent"
        }
        
        if state:
            params["state"] = state
        
        if incremental:
            params["incremental_auth"] = "true"  # type: ignore
        
        auth_url = f"{self.GOOGLE_OAUTH_URL}?{urlencode(params)}"
        self.logger.info(f"Generated authorization URL (scopes: {', '.join(self.scopes[:2])}...)")
        
        return auth_url
    
    async def exchange_code_for_token(self, authorization_code: str) -> OAuthToken:
        """
        Exchange authorization code for access token.
        
        Args:
            authorization_code: Code from authorization response
            
        Returns:
            OAuthToken with access and refresh tokens
        """
        try:
            async with aiohttp.ClientSession() as session:
                data = {
                    "code": authorization_code,
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "redirect_uri": self.redirect_uri,
                    "grant_type": "authorization_code"
                }
                
                async with session.post(self.GOOGLE_TOKEN_URL, data=data) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise AuthenticationException(f"Token exchange failed: {error_text}")
                    
                    token_data = await response.json()
                    token = OAuthToken(
                        access_token=token_data["access_token"],
                        token_type=token_data.get("token_type", "Bearer"),
                        expires_in=token_data.get("expires_in"),
                        refresh_token=token_data.get("refresh_token"),
                        scope=token_data.get("scope")
                    )
                    
                    self.logger.info("Successfully exchanged authorization code for token")
                    return token
        
        except Exception as e:
            self.logger.error(f"Token exchange failed: {str(e)}")
            raise AuthenticationException(f"Failed to exchange code for token: {str(e)}")
    
    async def refresh_access_token(self, refresh_token: str) -> OAuthToken:
        """
        Refresh an access token using a refresh token.
        
        Args:
            refresh_token: Refresh token from a previous authorization
            
        Returns:
            New OAuthToken with fresh access token
        """
        try:
            async with aiohttp.ClientSession() as session:
                data = {
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "refresh_token": refresh_token,
                    "grant_type": "refresh_token"
                }
                
                async with session.post(self.GOOGLE_TOKEN_URL, data=data) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise AuthenticationException(f"Token refresh failed: {error_text}")
                    
                    token_data = await response.json()
                    token = OAuthToken(
                        access_token=token_data["access_token"],
                        token_type=token_data.get("token_type", "Bearer"),
                        expires_in=token_data.get("expires_in"),
                        refresh_token=refresh_token,  # Use original if not provided
                        scope=token_data.get("scope")
                    )
                    
                    self.logger.info("Successfully refreshed access token")
                    return token
        
        except Exception as e:
            self.logger.error(f"Token refresh failed: {str(e)}")
            raise AuthenticationException(f"Failed to refresh token: {str(e)}")


class HubSpotOAuthManager:
    """Manager for HubSpot OAuth 2.0 flows."""
    
    HUBSPOT_OAUTH_URL = "https://app.hubspot.com/oauth/authorize"
    HUBSPOT_TOKEN_URL = "https://api.hubapi.com/oauth/v1/token"
    
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        scopes: Optional[list] = None
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.scopes = scopes or ["crm.objects.contacts.read", "crm.objects.contacts.write"]
        self.logger = get_logger(f"{__name__}.HubSpotOAuthManager")
    
    def get_authorization_url(self, state: Optional[str] = None) -> str:
        """Generate authorization URL for HubSpot."""
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": " ".join(self.scopes),
            "state": state or ""
        }
        auth_url = f"{self.HUBSPOT_OAUTH_URL}?{urlencode(params)}"
        self.logger.info(f"Generated HubSpot authorization URL")
        return auth_url
    
    async def exchange_code_for_token(self, authorization_code: str) -> OAuthToken:
        """Exchange authorization code for access token."""
        try:
            async with aiohttp.ClientSession() as session:
                data = {
                    "grant_type": "authorization_code",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "redirect_uri": self.redirect_uri,
                    "code": authorization_code
                }
                
                async with session.post(self.HUBSPOT_TOKEN_URL, data=data) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise AuthenticationException(f"HubSpot token exchange failed: {error_text}")
                    
                    token_data = await response.json()
                    token = OAuthToken(
                        access_token=token_data["access_token"],
                        token_type=token_data.get("token_type", "Bearer"),
                        expires_in=token_data.get("expires_in"),
                        refresh_token=None,  # HubSpot doesn't return refresh token
                        scope=" ".join(self.scopes)
                    )
                    
                    self.logger.info("Successfully exchanged HubSpot authorization code")
                    return token
        
        except Exception as e:
            self.logger.error(f"HubSpot token exchange failed: {str(e)}")
            raise AuthenticationException(f"Failed to exchange HubSpot code: {str(e)}")


class OAuthManager:
    """Central OAuth manager supporting multiple providers."""
    
    def __init__(self):
        self.logger = get_logger(f"{__name__}.OAuthManager")
        self.providers: Dict[str, Any] = {}
        self._initialize_providers()
    
    def _initialize_providers(self) -> None:
        """Initialize OAuth managers for enabled providers."""
        # Google OAuth (Gmail + Calendar)
        if (settings.gmail_oauth_client_id and settings.gmail_oauth_client_secret):
            self.providers["google"] = GoogleOAuthManager(
                client_id=settings.gmail_oauth_client_id,
                client_secret=settings.gmail_oauth_client_secret,
                redirect_uri=f"{settings.base_url}/auth/callback/google",
                scopes=[
                    "https://www.googleapis.com/auth/gmail.send",
                    "https://www.googleapis.com/auth/calendar"
                ]
            )
            self.logger.info("Initialized Google OAuth manager")
        
        # HubSpot OAuth
        if settings.hubspot_oauth_client_id and settings.hubspot_oauth_client_secret:
            self.providers["hubspot"] = HubSpotOAuthManager(
                client_id=settings.hubspot_oauth_client_id,
                client_secret=settings.hubspot_oauth_client_secret,
                redirect_uri=f"{settings.base_url}/auth/callback/hubspot"
            )
            self.logger.info("Initialized HubSpot OAuth manager")
    
    def get_authorization_url(self, provider: str, state: Optional[str] = None) -> str:
        """Get authorization URL for a provider."""
        if provider not in self.providers:
            raise AuthenticationException(f"Provider '{provider}' not configured")
        return self.providers[provider].get_authorization_url(state)
    
    async def exchange_code(self, provider: str, code: str) -> OAuthToken:
        """Exchange authorization code for token."""
        if provider not in self.providers:
            raise AuthenticationException(f"Provider '{provider}' not configured")
        return await self.providers[provider].exchange_code_for_token(code)


# Singleton instance
_oauth_manager: Optional[OAuthManager] = None


def get_oauth_manager() -> OAuthManager:
    """Get or create OAuth manager singleton."""
    global _oauth_manager
    if _oauth_manager is None:
        _oauth_manager = OAuthManager()
    return _oauth_manager
