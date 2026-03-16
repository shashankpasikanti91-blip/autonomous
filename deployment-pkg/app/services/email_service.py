"""
Real Email Service Implementation

Supports:
- Gmail API for authenticated sending
- SMTP for direct sending
- SendGrid for high-volume sending
- Template rendering and batch operations
"""

import base64
import smtplib
import asyncio
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, List, Dict, Any
from datetime import datetime

import aiohttp
from utils.logger import get_logger
from utils.errors import ServiceException
from config.settings import settings

# DeferredImport to avoid circular dependency
OAuthToken = None

def _import_oauth_token():
    global OAuthToken
    if OAuthToken is None:
        from app.integrations.oauth_manager import OAuthToken as OT
        OAuthToken = OT
    return OAuthToken


logger = get_logger(__name__)


class EmailService:
    """Real email service with multiple provider support."""
    
    def __init__(self):
        self.logger = get_logger(f"{__name__}.EmailService")
        self.provider = settings.email_provider
        self._initialize_provider()
    
    def _initialize_provider(self) -> None:
        """Initialize configured email provider."""
        self.logger.info(f"Initializing email provider: {self.provider}")
        
        if self.provider == "gmail":
            if not settings.gmail_oauth_client_id:
                self.logger.warning("Gmail OAuth not configured, falling back to SMTP")
                self.provider = "smtp"
        
        elif self.provider == "sendgrid":
            if not settings.sendgrid_api_key:
                self.logger.warning("SendGrid API key not configured, falling back to SMTP")
                self.provider = "smtp"
        
        elif self.provider == "smtp":
            if not settings.smtp_host:
                self.logger.warning("SMTP not properly configured")
    
    async def send_gmail(
        self,
        to_address: str,
        subject: str,
        body_html: str,
        oauth_token: Optional[OAuthToken] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Send email via Gmail API.
        
        Requires OAuth token with gmail.send scope.
        """
        try:
            if not oauth_token or oauth_token.is_expired():
                raise ServiceException("Valid Gmail OAuth token required")
            
            # Create MIME message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = settings.smtp_from_address
            msg["To"] = to_address
            
            if cc:
                msg["Cc"] = ", ".join(cc)
            
            # Add HTML part
            html_part = MIMEText(body_html, "html")
            msg.attach(html_part)
            
            # Encode message
            raw_message = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")
            
            # Send via Gmail API
            headers = {"Authorization": f"Bearer {oauth_token.access_token}"}
            payload = {"raw": raw_message}
            
            async with aiohttp.ClientSession() as session:
                url = "https://www.googleapis.com/gmail/v1/users/me/messages/send"
                async with session.post(url, json=payload, headers=headers) as response:
                    if response.status != 200:
                        error = await response.text()
                        raise ServiceException(f"Gmail API error: {error}")
                    
                    result = await response.json()
                    self.logger.info(f"Email sent via Gmail to {to_address}: {result['id']}")
                    
                    return {
                        "success": True,
                        "message_id": result["id"],
                        "provider": "gmail",
                        "timestamp": datetime.utcnow().isoformat()
                    }
        
        except Exception as e:
            self.logger.error(f"Gmail send failed: {str(e)}")
            raise ServiceException(f"Failed to send via Gmail: {str(e)}")
    
    async def send_sendgrid(
        self,
        to_address: str,
        subject: str,
        body_html: str,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Send email via SendGrid API."""
        try:
            headers = {
                "Authorization": f"Bearer {settings.sendgrid_api_key}",
                "Content-Type": "application/json"
            }
            
            # Build recipients list
            personalizations = [{
                "to": [{"email": to_address}]
            }]
            
            if cc:
                personalizations[0]["cc"] = [{"email": email} for email in cc]
            if bcc:
                personalizations[0]["bcc"] = [{"email": email} for email in bcc]
            
            payload = {
                "personalizations": personalizations,
                "from": {"email": settings.smtp_from_address},
                "subject": subject,
                "content": [{
                    "type": "text/html",
                    "value": body_html
                }]
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.sendgrid.com/v3/mail/send",
                    json=payload,
                    headers=headers
                ) as response:
                    if response.status != 202:
                        error = await response.text()
                        raise ServiceException(f"SendGrid error: {error}")
                    
                    self.logger.info(f"Email sent via SendGrid to {to_address}")
                    
                    return {
                        "success": True,
                        "message_id": f"sendgrid_{hash(to_address)}",
                        "provider": "sendgrid",
                        "timestamp": datetime.utcnow().isoformat()
                    }
        
        except Exception as e:
            self.logger.error(f"SendGrid send failed: {str(e)}")
            raise ServiceException(f"Failed to send via SendGrid: {str(e)}")
    
    async def send_smtp(
        self,
        to_address: str,
        subject: str,
        body_html: str,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Send email via SMTP."""
        try:
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            
            def _send():
                msg = MIMEMultipart("alternative")
                msg["Subject"] = subject
                msg["From"] = settings.smtp_from_address
                msg["To"] = to_address
                
                if cc:
                    msg["Cc"] = ", ".join(cc)
                
                html_part = MIMEText(body_html, "html")
                msg.attach(html_part)
                
                # Determine if TLS needed
                use_tls = settings.smtp_port == 587
                
                server = smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10)
                try:
                    if use_tls:
                        server.starttls()
                    
                    if settings.smtp_username:
                        server.login(settings.smtp_username, settings.smtp_password)
                    
                    recipients = [to_address]
                    if cc:
                        recipients.extend(cc)
                    if bcc:
                        recipients.extend(bcc)
                    
                    server.sendmail(
                        settings.smtp_from_address,
                        recipients,
                        msg.as_string()
                    )
                finally:
                    server.quit()
                
                return True
            
            await loop.run_in_executor(None, _send)
            
            self.logger.info(f"Email sent via SMTP to {to_address}")
            
            return {
                "success": True,
                "message_id": f"smtp_{hash(to_address)}",
                "provider": "smtp",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            self.logger.error(f"SMTP send failed: {str(e)}")
            raise ServiceException(f"Failed to send via SMTP: {str(e)}")
    
    async def send_email(
        self,
        to_address: str,
        subject: str,
        body_html: str,
        oauth_token: Optional[OAuthToken] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Send email using configured provider.
        
        Automatically falls back to SMTP if primary fails.
        """
        try:
            if self.provider == "gmail":
                return await self.send_gmail(
                    to_address, subject, body_html, oauth_token, cc, bcc
                )
            elif self.provider == "sendgrid":
                return await self.send_sendgrid(
                    to_address, subject, body_html, cc, bcc
                )
            else:  # smtp or fallback
                return await self.send_smtp(
                    to_address, subject, body_html, cc, bcc
                )
        
        except Exception as e:
            # Fallback to SMTP on any error
            self.logger.warning(f"Primary provider {self.provider} failed, falling back to SMTP")
            try:
                return await self.send_smtp(to_address, subject, body_html, cc, bcc)
            except Exception as fallback_error:
                self.logger.error(f"All email providers failed: {str(fallback_error)}")
                raise ServiceException(f"Failed to send email: {str(fallback_error)}")
    
    async def send_batch_emails(
        self,
        recipients: List[Dict[str, str]],
        subject_template: str,
        body_html_template: str
    ) -> Dict[str, Any]:
        """Send batch emails with template substitution."""
        try:
            results = []
            errors = []
            
            for idx, recipient in enumerate(recipients):
                try:
                    # Simple template substitution
                    subject = subject_template.format(**recipient)
                    body_html = body_html_template.format(**recipient)
                    
                    result = await self.send_email(
                        to_address=recipient["email"],
                        subject=subject,
                        body_html=body_html
                    )
                    results.append(result)
                
                except Exception as e:
                    error_msg = f"Failed to send to {recipient.get('email')}: {str(e)}"
                    self.logger.error(error_msg)
                    errors.append(error_msg)
            
            self.logger.info(f"Batch send complete: {len(results)} succeeded, {len(errors)} failed")
            
            return {
                "success": len(errors) == 0,
                "sent": len(results),
                "failed": len(errors),
                "results": results,
                "errors": errors if errors else None
            }
        
        except Exception as e:
            self.logger.error(f"Batch send failed: {str(e)}")
            raise ServiceException(f"Batch send failed: {str(e)}")


# Singleton instance
_email_service: Optional[EmailService] = None


def get_email_service() -> EmailService:
    """Get or create email service singleton."""
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service
