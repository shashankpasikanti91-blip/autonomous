"""
Sandbox mock providers for safe integration testing.
Can be enabled via configuration to simulate real providers for testing.
"""
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import logging
import random
import string


logger = logging.getLogger(__name__)


class MockEmailProvider:
    """Mock email provider for testing."""
    
    def __init__(self):
        self.sent_emails: List[Dict[str, Any]] = []
    
    async def send_email(
        self,
        to_address: str,
        subject: str,
        body_html: str,
        body_text: Optional[str] = None,
        from_name: Optional[str] = None,
        reply_to: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Mock send email."""
        email = {
            "id": f"email_{self._random_id()}",
            "to": to_address,
            "subject": subject,
            "body_html": body_html,
            "body_text": body_text,
            "from_name": from_name,
            "reply_to": reply_to,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "delivered",
        }
        self.sent_emails.append(email)
        logger.debug(f"Mock email sent to {to_address}")
        return email
    
    async def send_batch_emails(
        self,
        recipients: List[Dict[str, str]],
        template_subject: str,
        template_body: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Mock send batch emails."""
        results = []
        for recipient in recipients:
            result = await self.send_email(
                to_address=recipient["email"],
                subject=template_subject.format(**recipient),
                body_html=template_body.format(**recipient),
            )
            results.append(result)
        
        return {
            "batch_id": f"batch_{self._random_id()}",
            "total": len(recipients),
            "sent": len(recipients),
            "failed": 0,
            "emails": results,
        }
    
    def get_sent_emails(self) -> List[Dict[str, Any]]:
        """Get all mock-sent emails (for testing)."""
        return self.sent_emails
    
    @staticmethod
    def _random_id() -> str:
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))


class MockWhatsAppProvider:
    """Mock WhatsApp provider for testing."""
    
    def __init__(self):
        self.sent_messages: List[Dict[str, Any]] = []
    
    async def send_message(
        self,
        phone_number: str,
        message: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Mock send WhatsApp message."""
        msg = {
            "id": f"msg_{self._random_id()}",
            "phone_number": phone_number,
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "sent",
        }
        self.sent_messages.append(msg)
        logger.debug(f"Mock WhatsApp message sent to {phone_number}")
        return msg
    
    async def send_template_message(
        self,
        phone_number: str,
        template_name: str,
        variables: List[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Mock send template message."""
        msg = {
            "id": f"msg_{self._random_id()}",
            "phone_number": phone_number,
            "template_name": template_name,
            "variables": variables,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "sent",
        }
        self.sent_messages.append(msg)
        return msg
    
    async def get_message_status(self, message_id: str) -> Dict[str, Any]:
        """Mock get message status."""
        return {
            "id": message_id,
            "status": "delivered",
            "timestamp": datetime.utcnow().isoformat(),
        }
    
    def get_sent_messages(self) -> List[Dict[str, Any]]:
        """Get all mock-sent messages (for testing)."""
        return self.sent_messages
    
    @staticmethod
    def _random_id() -> str:
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))


class MockGoogleCalendarProvider:
    """Mock Google Calendar provider for testing."""
    
    def __init__(self):
        self.created_events: List[Dict[str, Any]] = []
    
    async def create_event(
        self,
        oauth_token: str,
        title: str,
        start_time: datetime,
        end_time: datetime,
        description: Optional[str] = None,
        location: Optional[str] = None,
        attendees: List[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Mock create event."""
        event = {
            "id": f"event_{self._random_id()}",
            "title": title,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "description": description,
            "location": location,
            "attendees": attendees or [],
            "created": datetime.utcnow().isoformat(),
            "status": "confirmed",
        }
        self.created_events.append(event)
        logger.debug(f"Mock event created: {title}")
        return event
    
    async def find_available_slots(
        self,
        oauth_token: str,
        start_time: datetime,
        end_time: datetime,
        duration_minutes: int,
        attendee_emails: List[str] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Mock find available slots."""
        slots = []
        current = start_time
        
        while current + timedelta(minutes=duration_minutes) <= end_time:
            slots.append({
                "start": current.isoformat(),
                "end": (current + timedelta(minutes=duration_minutes)).isoformat(),
            })
            current += timedelta(minutes=30)  # 30-min intervals
        
        logger.debug(f"Mock found {len(slots)} available slots")
        return slots
    
    async def update_event(
        self,
        oauth_token: str,
        event_id: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Mock update event."""
        return {
            "id": event_id,
            "updated": datetime.utcnow().isoformat(),
            "status": "confirmed",
        }
    
    async def delete_event(
        self,
        oauth_token: str,
        event_id: str,
        **kwargs
    ):
        """Mock delete event."""
        logger.debug(f"Mock event deleted: {event_id}")
    
    def get_created_events(self) -> List[Dict[str, Any]]:
        """Get all mock-created events (for testing)."""
        return self.created_events
    
    @staticmethod
    def _random_id() -> str:
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))


class MockHubSpotProvider:
    """Mock HubSpot CRM provider for testing."""
    
    def __init__(self):
        self.contacts: Dict[str, Dict[str, Any]] = {}
        self.deals: Dict[str, Dict[str, Any]] = {}
        self.activities: List[Dict[str, Any]] = []
    
    async def create_contact(
        self,
        email: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        phone: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Mock create contact."""
        contact_id = f"contact_{self._random_id()}"
        contact = {
            "id": contact_id,
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
            "phone": phone,
            "created": datetime.utcnow().isoformat(),
        }
        self.contacts[contact_id] = contact
        logger.debug(f"Mock contact created: {email}")
        return contact
    
    async def get_contact(self, contact_id: str) -> Optional[Dict[str, Any]]:
        """Mock get contact."""
        return self.contacts.get(contact_id)
    
    async def update_contact(
        self,
        contact_id: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Mock update contact."""
        if contact_id in self.contacts:
            self.contacts[contact_id].update(kwargs)
            self.contacts[contact_id]["updated"] = datetime.utcnow().isoformat()
            return self.contacts[contact_id]
        return {}
    
    async def create_deal(
        self,
        deal_name: str,
        contact_id: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Mock create deal."""
        deal_id = f"deal_{self._random_id()}"
        deal = {
            "id": deal_id,
            "name": deal_name,
            "contact_id": contact_id,
            "created": datetime.utcnow().isoformat(),
        }
        self.deals[deal_id] = deal
        logger.debug(f"Mock deal created: {deal_name}")
        return deal
    
    async def log_activity(
        self,
        contact_id: str,
        activity_type: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Mock log activity."""
        activity = {
            "id": f"activity_{self._random_id()}",
            "contact_id": contact_id,
            "activity_type": activity_type,
            "timestamp": datetime.utcnow().isoformat(),
        }
        self.activities.append(activity)
        logger.debug(f"Mock activity logged: {activity_type}")
        return activity
    
    async def search_contacts(self, query: str) -> List[Dict[str, Any]]:
        """Mock search contacts."""
        return [
            c for c in self.contacts.values()
            if query.lower() in (c.get("email") or "").lower() or
               query.lower() in (c.get("first_name") or "").lower() or
               query.lower() in (c.get("last_name") or "").lower()
        ]
    
    def get_contacts(self) -> Dict[str, Dict[str, Any]]:
        """Get all mock contacts (for testing)."""
        return self.contacts
    
    def get_deals(self) -> Dict[str, Dict[str, Any]]:
        """Get all mock deals (for testing)."""
        return self.deals
    
    @staticmethod
    def _random_id() -> str:
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))


# Global mock provider instances
_mock_email = MockEmailProvider()
_mock_whatsapp = MockWhatsAppProvider()
_mock_calendar = MockGoogleCalendarProvider()
_mock_hubspot = MockHubSpotProvider()


def get_mock_email_provider() -> MockEmailProvider:
    """Get global mock email provider."""
    return _mock_email


def get_mock_whatsapp_provider() -> MockWhatsAppProvider:
    """Get global mock WhatsApp provider."""
    return _mock_whatsapp


def get_mock_calendar_provider() -> MockGoogleCalendarProvider:
    """Get global mock calendar provider."""
    return _mock_calendar


def get_mock_hubspot_provider() -> MockHubSpotProvider:
    """Get global mock HubSpot provider."""
    return _mock_hubspot


def reset_all_mocks():
    """Reset all mock providers (useful between test runs)."""
    global _mock_email, _mock_whatsapp, _mock_calendar, _mock_hubspot
    _mock_email = MockEmailProvider()
    _mock_whatsapp = MockWhatsAppProvider()
    _mock_calendar = MockGoogleCalendarProvider()
    _mock_hubspot = MockHubSpotProvider()
    logger.info("All mock providers reset")
