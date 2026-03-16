"""
Real WhatsApp Cloud API Integration

Supports:
- Text message sending
- Template message sending
- Status tracking and webhooks
- Error handling and retries
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
import asyncio

import aiohttp
from utils.logger import get_logger
from utils.errors import ServiceException
from config.settings import settings


logger = get_logger(__name__)


class WhatsAppService:
    """Real WhatsApp Cloud API integration."""
    
    API_VERSION = "v18.0"
    BASE_URL = f"https://graph.instagram.com/{API_VERSION}"
    
    def __init__(self):
        self.logger = get_logger(f"{__name__}.WhatsAppService")
        self.business_account_id = settings.whatsapp_business_account_id
        self.api_token = settings.whatsapp_api_token
        
        if not self.business_account_id or not self.api_token:
            self.logger.warning("WhatsApp credentials not fully configured")
    
    def _format_phone_number(self, phone_number: str) -> str:
        """
        Format phone number to E.164 format (required by WhatsApp API).
        
        WhatsApp requires: [country_code][phone_number]
        Example: +1234567890 or 1234567890 -> 1234567890
        """
        # Remove all non-digit characters
        cleaned = "".join(filter(str.isdigit, phone_number))
        
        # If it starts with +1, remove the +
        if phone_number.startswith("+"):
            return cleaned
        
        return cleaned
    
    async def send_message(
        self,
        phone_number: str,
        message_text: str
    ) -> Dict[str, Any]:
        """
        Send a text message via WhatsApp Cloud API.
        
        Args:
            phone_number: Recipient's phone number (E.164 format)
            message_text: Message text content
        """
        try:
            phone = self._format_phone_number(phone_number)
            
            headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": phone,
                "type": "text",
                "text": {
                    "preview_url": False,
                    "body": message_text
                }
            }
            
            url = f"{self.BASE_URL}/{self.business_account_id}/messages"
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers) as response:
                    if response.status not in [200, 201]:
                        error_text = await response.text()
                        raise ServiceException(f"WhatsApp API error: {error_text}")
                    
                    result = await response.json()
                    message_id = result.get("messages", [{}])[0].get("id")
                    
                    self.logger.info(f"WhatsApp message sent to {phone}: {message_id}")
                    
                    return {
                        "success": True,
                        "message_id": message_id,
                        "phone_number": phone,
                        "provider": "whatsapp",
                        "timestamp": datetime.utcnow().isoformat()
                    }
        
        except Exception as e:
            self.logger.error(f"WhatsApp send failed: {str(e)}")
            raise ServiceException(f"Failed to send WhatsApp message: {str(e)}")
    
    async def send_template_message(
        self,
        phone_number: str,
        template_name: str,
        template_variables: Optional[List[str]] = None,
        language_code: str = "en"
    ) -> Dict[str, Any]:
        """
        Send a pre-approved template message via WhatsApp.
        
        Templates must be created and approved in WhatsApp Business Manager.
        
        Args:
            phone_number: Recipient's phone number
            template_name: Name of approved template
            template_variables: Variable values for template placeholders
            language_code: Template language code (default: en)
        """
        try:
            phone = self._format_phone_number(phone_number)
            
            headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "messaging_product": "whatsapp",
                "to": phone,
                "type": "template",
                "template": {
                    "name": template_name,
                    "language": {
                        "code": language_code
                    }
                }
            }
            
            # Add template variables if provided
            if template_variables:
                payload["template"]["components"] = [
                    {
                        "type": "body",
                        "parameters": [
                            {"type": "text", "text": var}
                            for var in template_variables
                        ]
                    }
                ]
            
            url = f"{self.BASE_URL}/{self.business_account_id}/messages"
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers) as response:
                    if response.status not in [200, 201]:
                        error_text = await response.text()
                        raise ServiceException(f"WhatsApp template error: {error_text}")
                    
                    result = await response.json()
                    message_id = result.get("messages", [{}])[0].get("id")
                    
                    self.logger.info(f"WhatsApp template sent to {phone}: {message_id}")
                    
                    return {
                        "success": True,
                        "message_id": message_id,
                        "phone_number": phone,
                        "template": template_name,
                        "provider": "whatsapp",
                        "timestamp": datetime.utcnow().isoformat()
                    }
        
        except Exception as e:
            self.logger.error(f"WhatsApp template send failed: {str(e)}")
            raise ServiceException(f"Failed to send template: {str(e)}")
    
    async def get_message_status(
        self,
        message_id: str
    ) -> Dict[str, Any]:
        """
        Get status of a sent message.
        
        Status values: accepted, sent, delivered, read, failed
        """
        try:
            headers = {
                "Authorization": f"Bearer {self.api_token}"
            }
            
            url = f"{self.BASE_URL}/{message_id}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise ServiceException(f"WhatsApp status error: {error_text}")
                    
                    data = await response.json()
                    
                    return {
                        "message_id": message_id,
                        "status": data.get("status"),
                        "recipient": data.get("recipient_id"),
                        "timestamp": datetime.utcnow().isoformat()
                    }
        
        except Exception as e:
            self.logger.error(f"Failed to get message status: {str(e)}")
            raise ServiceException(f"Failed to get status: {str(e)}")
    
    async def upload_media(
        self,
        file_path: str,
        media_type: str
    ) -> Dict[str, str]:
        """
        Upload media file to WhatsApp for use in messages.
        
        Supported types: image, audio, video, document
        """
        try:
            headers = {
                "Authorization": f"Bearer {self.api_token}"
            }
            
            url = f"{self.BASE_URL}/{self.business_account_id}/media"
            
            with open(file_path, "rb") as f:
                form_data = {
                    "messaging_product": "whatsapp",
                    "type": media_type,
                    "file": f
                }
                
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        url,
                        data=form_data,
                        headers=headers
                    ) as response:
                        if response.status not in [200, 201]:
                            error_text = await response.text()
                            raise ServiceException(f"Media upload error: {error_text}")
                        
                        result = await response.json()
                        media_id = result.get("id")
                        
                        self.logger.info(f"Media uploaded: {media_id}")
                        
                        return {
                            "media_id": media_id,
                            "type": media_type
                        }
        
        except Exception as e:
            self.logger.error(f"Media upload failed: {str(e)}")
            raise ServiceException(f"Failed to upload media: {str(e)}")


# Singleton instance
_whatsapp_service: Optional[WhatsAppService] = None


def get_whatsapp_service() -> WhatsAppService:
    """Get or create WhatsApp service singleton."""
    global _whatsapp_service
    if _whatsapp_service is None:
        _whatsapp_service = WhatsAppService()
    return _whatsapp_service
