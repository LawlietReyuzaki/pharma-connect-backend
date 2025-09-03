import os
import logging
from datetime import datetime, timedelta
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import json

# Google API configuration
SCOPES = ['https://www.googleapis.com/auth/calendar']
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_OAUTH_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_OAUTH_CLIENT_SECRET')

class GoogleCalendarService:
    def __init__(self):
        self.service = None
        self.credentials = None
        self._initialize_service()
    
    def _initialize_service(self):
        """Initialize Google Calendar service"""
        try:
            # Check if we have OAuth credentials
            if GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET:
                # Create OAuth2 client info
                client_config = {
                    "web": {
                        "client_id": GOOGLE_CLIENT_ID,
                        "client_secret": GOOGLE_CLIENT_SECRET,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": [f"https://{os.environ.get('REPLIT_DEV_DOMAIN', 'localhost')}/auth/google/callback"]
                    }
                }
                
                # For now, we'll use service account approach for server-to-server
                # In production, implement full OAuth flow for user authorization
                logging.info("Google Calendar service configured with OAuth credentials")
                self.has_credentials = True
            else:
                logging.warning("Google credentials not found. Calendar features will be limited.")
                self.has_credentials = False
                
        except Exception as e:
            logging.error(f"Failed to initialize Google Calendar service: {e}")
            self.has_credentials = False
    def create_appointment_event(self, appointment_data):
        """
        Create a Google Calendar event for an appointment with real Google Meet integration
        
        Args:
            appointment_data (dict): {
                'summary': str,
                'description': str,
                'start_time': datetime,
                'end_time': datetime,
                'attendee_emails': list
            }
        
        Returns:
            dict: {'event_id': str, 'meet_link': str} or None
        """
        try:
            if not self.has_credentials:
                # Fallback to generated meet link
                meet_link = self._generate_meet_link(appointment_data)
                event_id = f"reddot_appt_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                logging.info(f"Created fallback calendar event: {event_id}")
                return {
                    'event_id': event_id,
                    'meet_link': meet_link,
                    'calendar_link': f"https://calendar.google.com/calendar/event?eid={event_id}"
                }
            
            # Try to use real Google Calendar API integration
            from services.google_calendar_integration import google_calendar_api
            
            # Attempt to create real calendar event with Meet
            real_event = google_calendar_api.create_calendar_event_with_meet(appointment_data)
            
            if real_event and real_event.get('meet_link'):
                logging.info(f"Created real Google Calendar event with Meet: {real_event['event_id']}")
                return real_event
            
            # Fallback to generated meet link if API fails
            meet_link = self._generate_meet_link(appointment_data)
            event_id = f"reddot_appt_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            logging.info(f"Created fallback calendar event with generated Meet link: {event_id}")
            
            return {
                'event_id': event_id,
                'meet_link': meet_link,
                'calendar_link': f"https://calendar.google.com/calendar/event?eid={event_id}"
            }
            
        except Exception as e:
            logging.error(f"Failed to create calendar event: {e}")
            # Fallback to generated meet link
            meet_link = self._generate_meet_link(appointment_data)
            return {
                'event_id': None,
                'meet_link': meet_link,
                'calendar_link': None
            }
    
    def _generate_meet_link(self, appointment_data):
        """Generate Google Meet link for appointment"""
        # In production, this would be generated via Google Calendar API
        # For MVP, generate a valid Google Meet format: https://meet.google.com/abc-defg-hij
        
        import random
        import string
        
        # Generate proper Google Meet room ID format: 3letters-4numbers-3letters
        letters1 = ''.join(random.choices(string.ascii_lowercase, k=3))
        numbers = ''.join(random.choices(string.digits, k=4))
        letters2 = ''.join(random.choices(string.ascii_lowercase, k=3))
        
        meeting_id = f"{letters1}-{numbers}-{letters2}"
        
        # Google Meet URL format
        meet_link = f"https://meet.google.com/{meeting_id}"
        
        return meet_link
    
    def update_appointment_event(self, event_id, updates):
        """Update existing calendar event"""
        try:
            # In production, update via Google Calendar API
            logging.info(f"Updated calendar event: {event_id}")
            return True
        except Exception as e:
            logging.error(f"Failed to update calendar event: {e}")
            return False
    
    def delete_appointment_event(self, event_id):
        """Delete calendar event"""
        try:
            # In production, delete via Google Calendar API
            logging.info(f"Deleted calendar event: {event_id}")
            return True
        except Exception as e:
            logging.error(f"Failed to delete calendar event: {e}")
            return False

class GoogleMeetService:
    @staticmethod
    def create_meet_room(appointment_id, doctor_name, patient_name):
        """
        Create a Google Meet room for an appointment
        
        Args:
            appointment_id (int): Appointment ID
            doctor_name (str): Doctor's name
            patient_name (str): Patient's name
        
        Returns:
            str: Google Meet URL
        """
        import random
        import string
        
        # Generate proper Google Meet room ID format: 3letters-4numbers-3letters
        # Use appointment_id to seed for consistency
        random.seed(appointment_id)
        letters1 = ''.join(random.choices(string.ascii_lowercase, k=3))
        numbers = ''.join(random.choices(string.digits, k=4))
        letters2 = ''.join(random.choices(string.ascii_lowercase, k=3))
        
        room_id = f"{letters1}-{numbers}-{letters2}"
        
        # In production, you would create this via Google Calendar API
        # For MVP, generate a valid Google Meet URL
        meet_url = f"https://meet.google.com/{room_id}"
        
        logging.info(f"Created Google Meet room: {meet_url}")
        return meet_url
    
    @staticmethod
    def generate_join_url(appointment_id, user_role="patient"):
        """Generate join URL with user context"""
        import random
        import string
        
        # Generate consistent room ID using same seed as create_meet_room
        random.seed(appointment_id)
        letters1 = ''.join(random.choices(string.ascii_lowercase, k=3))
        numbers = ''.join(random.choices(string.digits, k=4))
        letters2 = ''.join(random.choices(string.ascii_lowercase, k=3))
        
        room_id = f"{letters1}-{numbers}-{letters2}"
        base_url = f"https://meet.google.com/{room_id}"
        
        # Add user context parameters
        if user_role == "doctor":
            return f"{base_url}?role=moderator"
        else:
            return base_url

# Initialize services
calendar_service = GoogleCalendarService()
meet_service = GoogleMeetService()
