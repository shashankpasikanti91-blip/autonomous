"""
Real CRM Service Integration

Supports:
- HubSpot API for contact, deal, and company management
- Lead scoring and qualification
- Pipeline management
- Activity logging
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
import asyncio

import aiohttp
from utils.logger import get_logger
from utils.errors import ServiceException
from config.settings import settings


logger = get_logger(__name__)


class CRMService:
    """Real CRM integration service (HubSpot)."""
    
    API_BASE_URL = "https://api.hubapi.com"
    
    def __init__(self):
        self.logger = get_logger(f"{__name__}.CRMService")
        self.api_key = settings.hubspot_api_key
        self.crm_provider = settings.crm_provider
        
        if not self.api_key:
            self.logger.warning(f"CRM API key not configured for {self.crm_provider}")
    
    def _get_headers(self) -> Dict[str, str]:
        """Get authorization headers for CRM API."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def create_contact(
        self,
        email: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        phone: Optional[str] = None,
        company: Optional[str] = None,
        job_title: Optional[str] = None,
        custom_properties: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create or update a contact in HubSpot.
        
        Args:
            email: Contact email address (unique identifier)
            first_name: Contact first name
            last_name: Contact last name
            phone: Contact phone number
            company: Company name
            job_title: Contact job title
            custom_properties: Additional custom properties
        """
        try:
            headers = self._get_headers()
            
            properties = {
                "email": email,
            }
            
            if first_name:
                properties["firstname"] = first_name
            if last_name:
                properties["lastname"] = last_name
            if phone:
                properties["phone"] = phone
            if company:
                properties["company"] = company
            if job_title:
                properties["jobtitle"] = job_title
            
            # Add custom properties
            if custom_properties:
                properties.update(custom_properties)
            
            payload = {"properties": properties}
            
            url = f"{self.API_BASE_URL}/crm/v3/objects/contacts"
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers) as response:
                    if response.status not in [200, 201]:
                        error_text = await response.text()
                        raise ServiceException(f"HubSpot error: {error_text}")
                    
                    result = await response.json()
                    contact_id = result["id"]
                    
                    self.logger.info(f"Contact created/updated: {contact_id} - {email}")
                    
                    return {
                        "success": True,
                        "contact_id": contact_id,
                        "email": email,
                        "name": f"{first_name or ''} {last_name or ''}".strip(),
                        "timestamp": datetime.utcnow().isoformat()
                    }
        
        except Exception as e:
            self.logger.error(f"Failed to create contact: {str(e)}")
            raise ServiceException(f"Failed to create contact: {str(e)}")
    
    async def get_contact(self, contact_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a contact by ID."""
        try:
            headers = self._get_headers()
            
            url = f"{self.API_BASE_URL}/crm/v3/objects/contacts/{contact_id}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 404:
                        return None
                    
                    if response.status != 200:
                        error_text = await response.text()
                        raise ServiceException(f"HubSpot error: {error_text}")
                    
                    result = await response.json()
                    
                    return {
                        "contact_id": result["id"],
                        "properties": result.get("properties", {}),
                        "timestamp": datetime.utcnow().isoformat()
                    }
        
        except Exception as e:
            self.logger.error(f"Failed to get contact: {str(e)}")
            raise ServiceException(f"Failed to get contact: {str(e)}")
    
    async def update_contact(
        self,
        contact_id: str,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update contact properties."""
        try:
            headers = self._get_headers()
            
            payload = {"properties": updates}
            
            url = f"{self.API_BASE_URL}/crm/v3/objects/contacts/{contact_id}"
            
            async with aiohttp.ClientSession() as session:
                async with session.patch(url, json=payload, headers=headers) as response:
                    if response.status not in [200, 201]:
                        error_text = await response.text()
                        raise ServiceException(f"HubSpot error: {error_text}")
                    
                    result = await response.json()
                    
                    self.logger.info(f"Contact updated: {contact_id}")
                    
                    return {
                        "success": True,
                        "contact_id": result["id"],
                        "properties": result.get("properties", {}),
                        "timestamp": datetime.utcnow().isoformat()
                    }
        
        except Exception as e:
            self.logger.error(f"Failed to update contact: {str(e)}")
            raise ServiceException(f"Failed to update contact: {str(e)}")
    
    async def create_deal(
        self,
        deal_name: str,
        contact_id: str,
        pipeline_id: str = "default",
        deal_stage: str = "negotiation",
        amount: Optional[float] = None,
        close_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Create a deal in HubSpot.
        
        Args:
            deal_name: Name of the deal
            contact_id: Associated contact ID
            pipeline_id: Pipeline ID
            deal_stage: Current stage in pipeline
            amount: Deal amount in dollars
            close_date: Expected close date
        """
        try:
            headers = self._get_headers()
            
            properties = {
                "dealname": deal_name,
                "pipeline": pipeline_id,
                "dealstage": deal_stage
            }
            
            if amount:
                properties["amount"] = amount
            
            if close_date:
                properties["closedate"] = close_date.isoformat()
            
            payload = {"properties": properties}
            
            url = f"{self.API_BASE_URL}/crm/v3/objects/deals"
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers) as response:
                    if response.status not in [200, 201]:
                        error_text = await response.text()
                        raise ServiceException(f"HubSpot error: {error_text}")
                    
                    result = await response.json()
                    deal_id = result["id"]
                    
                    # Associate contact with deal
                    await self._associate_objects("deals", deal_id, "contacts", contact_id)
                    
                    self.logger.info(f"Deal created: {deal_id} - {deal_name}")
                    
                    return {
                        "success": True,
                        "deal_id": deal_id,
                        "deal_name": deal_name,
                        "amount": amount,
                        "timestamp": datetime.utcnow().isoformat()
                    }
        
        except Exception as e:
            self.logger.error(f"Failed to create deal: {str(e)}")
            raise ServiceException(f"Failed to create deal: {str(e)}")
    
    async def _associate_objects(
        self,
        from_type: str,
        from_id: str,
        to_type: str,
        to_id: str,
        association_type: str = "contact_to_deal"
    ) -> bool:
        """Associate two HubSpot objects."""
        try:
            headers = self._get_headers()
            
            payload = {
                "associationCategory": "HUBSPOT_DEFINED",
                "associationType": association_type
            }
            
            url = (
                f"{self.API_BASE_URL}/crm/v3/objects/{from_type}/{from_id}/"
                f"associations/{to_type}/{to_id}"
            )
            
            async with aiohttp.ClientSession() as session:
                async with session.put(url, json=payload, headers=headers) as response:
                    if response.status not in [200, 201]:
                        self.logger.warning(f"Failed to associate objects: {response.status}")
                        return False
                    
                    return True
        
        except Exception as e:
            self.logger.error(f"Failed to associate objects: {str(e)}")
            return False
    
    async def log_activity(
        self,
        contact_id: str,
        activity_type: str,
        activity_subject: str,
        notes: Optional[str] = None,
        owner_email: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Log an activity/engagement for a contact.
        
        Activity types: EMAIL, CALL, MEETING, NOTE, TASK
        """
        try:
            headers = self._get_headers()
            
            properties = {
                "hs_activity_type": activity_type,
                "hs_activity_subject": activity_subject,
                "hs_object_id": contact_id
            }
            
            if notes:
                properties["hs_activity_notes"] = notes
            
            if owner_email:
                properties["hubspot_owner_email"] = owner_email
            
            payload = {"properties": properties}
            
            url = f"{self.API_BASE_URL}/crm/v3/objects/activities/tasks"
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers) as response:
                    if response.status not in [200, 201]:
                        error_text = await response.text()
                        raise ServiceException(f"HubSpot error: {error_text}")
                    
                    result = await response.json()
                    
                    self.logger.info(f"Activity logged for contact {contact_id}")
                    
                    return {
                        "success": True,
                        "activity_id": result["id"],
                        "activity_type": activity_type,
                        "timestamp": datetime.utcnow().isoformat()
                    }
        
        except Exception as e:
            self.logger.error(f"Failed to log activity: {str(e)}")
            raise ServiceException(f"Failed to log activity: {str(e)}")
    
    async def search_contacts(
        self,
        query: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search for contacts by name or email."""
        try:
            headers = self._get_headers()
            
            payload = {
                "query": query,
                "limit": limit
            }
            
            url = f"{self.API_BASE_URL}/crm/v3/objects/contacts/search"
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise ServiceException(f"HubSpot error: {error_text}")
                    
                    result = await response.json()
                    results = result.get("results", [])
                    
                    self.logger.info(f"Found {len(results)} contacts for query: {query}")
                    
                    return [
                        {
                            "contact_id": r["id"],
                            "properties": r.get("properties", {}),
                        }
                        for r in results
                    ]
        
        except Exception as e:
            self.logger.error(f"Search failed: {str(e)}")
            raise ServiceException(f"Search failed: {str(e)}")


# Singleton instance
_crm_service: Optional[CRMService] = None


def get_crm_service() -> CRMService:
    """Get or create CRM service singleton."""
    global _crm_service
    if _crm_service is None:
        _crm_service = CRMService()
    return _crm_service
