"""
Real Google Calendar API Integration

Supports:
- Creating/updating/deleting events
- Finding available time slots
- Recurring events
- Notifications and reminders
- Calendar sharing
"""

from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import json

import aiohttp
from utils.logger import get_logger
from utils.errors import ServiceException
from config.settings import settings
from app.integrations.oauth_manager import OAuthToken


logger = get_logger(__name__)


class GoogleCalendarService:
    """Real Google Calendar API integration."""
    
    API_BASE_URL = "https://www.googleapis.com/calendar/v3"
    
    def __init__(self):
        self.logger = get_logger(f"{__name__}.GoogleCalendarService")
    
    def _get_headers(self, oauth_token: OAuthToken) -> Dict[str, str]:
        """Get authorization headers for Calendar API."""
        if oauth_token.is_expired():
            raise ServiceException("OAuth token expired")
        
        return {
            "Authorization": f"Bearer {oauth_token.access_token}",
            "Content-Type": "application/json"
        }
    
    async def create_event(
        self,
        oauth_token: OAuthToken,
        title: str,
        start_time: datetime,
        end_time: datetime,
        description: Optional[str] = None,
        attendees: Optional[List[str]] = None,
        calendar_id: str = "primary",
        notifications: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Create a calendar event.
        
        Args:
            oauth_token: Valid Google OAuth token with calendar scope
            title: Event title
            start_time: Event start time
            end_time: Event end time
            description: Event description
            attendees: List of attendee email addresses
            calendar_id: Calendar ID (default: primary)
            notifications: List of notification objects
        """
        try:
            headers = self._get_headers(oauth_token)
            
            # Format times as RFC 3339 timestamp
            start = start_time.isoformat()
            end = end_time.isoformat()
            
            event_data = {
                "summary": title,
                "description": description or "",
                "start": {"dateTime": start, "timeZone": "UTC"},
                "end": {"dateTime": end, "timeZone": "UTC"}
            }
            
            # Add attendees
            if attendees:
                event_data["attendees"] = [
                    {"email": email} for email in attendees
                ]
                event_data["sendNotifications"] = True
            
            # Add notifications
            if notifications:
                event_data["reminders"] = {
                    "useDefault": False,
                    "overrides": notifications
                }
            else:
                # Default: 15 minutes before
                event_data["reminders"] = {
                    "useDefault": True
                }
            
            url = f"{self.API_BASE_URL}/calendars/{calendar_id}/events"
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=event_data, headers=headers) as response:
                    if response.status not in [200, 201]:
                        error_text = await response.text()
                        raise ServiceException(f"Calendar API error: {error_text}")
                    
                    result = await response.json()
                    
                    self.logger.info(f"Event created: {result['id']} - {title}")
                    
                    return {
                        "success": True,
                        "event_id": result["id"],
                        "title": title,
                        "start": start,
                        "end": end,
                        "html_link": result.get("htmlLink"),
                        "timestamp": datetime.utcnow().isoformat()
                    }
        
        except Exception as e:
            self.logger.error(f"Failed to create event: {str(e)}")
            raise ServiceException(f"Failed to create calendar event: {str(e)}")
    
    async def find_available_slots(
        self,
        oauth_token: OAuthToken,
        attendees: List[str],
        duration_minutes: int = 60,
        date: Optional[datetime] = None,
        hours_to_check: int = 24,
        calendar_id: str = "primary"
    ) -> List[Dict[str, Any]]:
        """
        Find available time slots for attendees.
        
        Queries Google Calendar to find times when all attendees are free.
        
        Args:
            oauth_token: Valid Google OAuth token
            attendees: List of attendee email addresses
            duration_minutes: Required duration for the slot
            date: Date to check (default: today)
            hours_to_check: Number of hours to look ahead
            calendar_id: Calendar ID to check
        """
        try:
            if not date:
                date = datetime.utcnow()
            
            headers = self._get_headers(oauth_token)
            
            # Define time range
            time_min = date.replace(hour=9, minute=0, second=0, microsecond=0)
            time_max = time_min + timedelta(hours=hours_to_check)
            
            # Query attendees' busy times
            query_data = {
                "items": [{"id": attendee} for attendee in attendees + [calendar_id]],
                "timeMin": time_min.isoformat() + "Z",
                "timeMax": time_max.isoformat() + "Z",
                "intervalMinutes": 30
            }
            
            url = f"{self.API_BASE_URL}/calendars/freebusy"
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=query_data, headers=headers) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise ServiceException(f"Freebusy query error: {error_text}")
                    
                    result = await response.json()
                    
                    # Parse busy times
                    busy_times = []
                    for calendar_id_key, cal_data in result.get("calendars", {}).items():
                        busy_times.extend(cal_data.get("busy", []))
                    
                    # Find available slots
                    available_slots = self._find_available_slots(
                        time_min,
                        time_max,
                        busy_times,
                        duration_minutes
                    )
                    
                    self.logger.info(f"Found {len(available_slots)} available slots")
                    
                    return available_slots
        
        except Exception as e:
            self.logger.error(f"Failed to find available slots: {str(e)}")
            raise ServiceException(f"Failed to find available slots: {str(e)}")
    
    def _find_available_slots(
        self,
        time_min: datetime,
        time_max: datetime,
        busy_times: List[Dict[str, str]],
        duration_minutes: int
    ) -> List[Dict[str, Any]]:
        """
        Find available slots given busy times.
        
        Internal method to compute free time.
        """
        slots = []
        current = time_min
        
        # Convert busy times to sorted list of (start, end) tuples
        busy_periods = []
        for busy in busy_times:
            start = datetime.fromisoformat(busy["start"].replace("Z", "+00:00"))
            end = datetime.fromisoformat(busy["end"].replace("Z", "+00:00"))
            busy_periods.append((start, end))
        
        busy_periods.sort()
        
        # Merge overlapping periods
        merged = []
        for start, end in busy_periods:
            if merged and start <= merged[-1][1]:
                merged[-1] = (merged[-1][0], max(merged[-1][1], end))
            else:
                merged.append((start, end))
        
        # Find gaps
        while current + timedelta(minutes=duration_minutes) <= time_max:
            slot_end = current + timedelta(minutes=duration_minutes)
            is_free = True
            
            for busy_start, busy_end in merged:
                if not (slot_end <= busy_start or current >= busy_end):
                    is_free = False
                    break
            
            if is_free:
                slots.append({
                    "start": current.isoformat(),
                    "end": slot_end.isoformat(),
                    "duration_minutes": duration_minutes
                })
            
            current += timedelta(minutes=30)
        
        return slots
    
    async def update_event(
        self,
        oauth_token: OAuthToken,
        event_id: str,
        updates: Dict[str, Any],
        calendar_id: str = "primary"
    ) -> Dict[str, Any]:
        """Update an existing calendar event."""
        try:
            headers = self._get_headers(oauth_token)
            
            url = f"{self.API_BASE_URL}/calendars/{calendar_id}/events/{event_id}"
            
            async with aiohttp.ClientSession() as session:
                async with session.patch(url, json=updates, headers=headers) as response:
                    if response.status not in [200, 201]:
                        error_text = await response.text()
                        raise ServiceException(f"Update error: {error_text}")
                    
                    result = await response.json()
                    
                    self.logger.info(f"Event updated: {event_id}")
                    
                    return {
                        "success": True,
                        "event_id": result["id"],
                        "title": result.get("summary"),
                        "timestamp": datetime.utcnow().isoformat()
                    }
        
        except Exception as e:
            self.logger.error(f"Failed to update event: {str(e)}")
            raise ServiceException(f"Failed to update event: {str(e)}")
    
    async def delete_event(
        self,
        oauth_token: OAuthToken,
        event_id: str,
        calendar_id: str = "primary"
    ) -> Dict[str, Any]:
        """Delete a calendar event."""
        try:
            headers = self._get_headers(oauth_token)
            
            url = f"{self.API_BASE_URL}/calendars/{calendar_id}/events/{event_id}"
            
            async with aiohttp.ClientSession() as session:
                async with session.delete(url, headers=headers) as response:
                    if response.status not in [200, 204]:
                        error_text = await response.text()
                        raise ServiceException(f"Delete error: {error_text}")
                    
                    self.logger.info(f"Event deleted: {event_id}")
                    
                    return {
                        "success": True,
                        "event_id": event_id,
                        "timestamp": datetime.utcnow().isoformat()
                    }
        
        except Exception as e:
            self.logger.error(f"Failed to delete event: {str(e)}")
            raise ServiceException(f"Failed to delete event: {str(e)}")


# Singleton instance
_calendar_service: Optional[GoogleCalendarService] = None


def get_google_calendar_service() -> GoogleCalendarService:
    """Get or create Google Calendar service singleton."""
    global _calendar_service
    if _calendar_service is None:
        _calendar_service = GoogleCalendarService()
    return _calendar_service
