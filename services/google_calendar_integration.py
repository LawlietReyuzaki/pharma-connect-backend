import os
import logging
import json
from datetime import datetime, timedelta
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import uuid

# Google API configuration
SCOPES = ['https://www.googleapis.com/auth/calendar']
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_OAUTH_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_OAUTH_CLIENT_SECRET')
REDIRECT_URI = f"https://{os.environ.get('REPLIT_DEV_DOMAIN', 'localhost')}/auth/google/callback"

class GoogleCalendarAPIService:
    def __init__(self):
        self.service = None
        self.credentials = None
        self.has_credentials = self._check_credentials()
    
    def _check_credentials(self):
        """Check if Google OAuth credentials are available"""
        return bool(GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET)
    
    def get_oauth_url(self):
        """Generate OAuth authorization URL"""
        try:
            if not self.has_credentials:
                return None
            
            client_config = {
                "web": {
                    "client_id": GOOGLE_CLIENT_ID,
                    "client_secret": GOOGLE_CLIENT_SECRET,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [REDIRECT_URI]
                }
            }
            
            flow = Flow.from_client_config(
                client_config,
                scopes=SCOPES,
                redirect_uri=REDIRECT_URI
            )
            
            auth_url, _ = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true'
            )
            
            return auth_url
            
        except Exception as e:
            logging.error(f"Failed to generate OAuth URL: {e}")
            return None
    
    def exchange_code_for_token(self, auth_code):
        """Exchange authorization code for access token"""
        try:
            if not self.has_credentials:
                return None
            
            client_config = {
                "web": {
                    "client_id": GOOGLE_CLIENT_ID,
                    "client_secret": GOOGLE_CLIENT_SECRET,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [REDIRECT_URI]
                }
            }
            
            flow = Flow.from_client_config(
                client_config,
                scopes=SCOPES,
                redirect_uri=REDIRECT_URI
            )
            
            flow.fetch_token(code=auth_code)
            self.credentials = flow.credentials
            
            # Build the service
            self.service = build('calendar', 'v3', credentials=self.credentials)
            
            return self.credentials
            
        except Exception as e:
            logging.error(f"Failed to exchange code for token: {e}")
            return None
    
    def create_calendar_event_with_meet(self, appointment_data):
        """
        Create a Google Calendar event with Google Meet integration
        
        Args:
            appointment_data (dict): {
                'summary': str,
                'description': str,
                'start_time': datetime,
                'end_time': datetime,
                'attendee_emails': list,
                'appointment_id': int
            }
        
        Returns:
            dict: {'event_id': str, 'meet_link': str, 'calendar_link': str} or None
        """
        try:
            if not self.service:
                logging.warning("Google Calendar service not initialized")
                return None
            
            # Create the event object
            event = {
                'summary': appointment_data.get('summary', 'Red Dot Pharmacy Consultation'),
                'description': appointment_data.get('description', ''),
                'start': {
                    'dateTime': appointment_data['start_time'].isoformat(),
                    'timeZone': 'Asia/Karachi',
                },
                'end': {
                    'dateTime': appointment_data['end_time'].isoformat(),
                    'timeZone': 'Asia/Karachi',
                },
                'attendees': [
                    {'email': email} for email in appointment_data.get('attendee_emails', [])
                ],
                'conferenceData': {
                    'createRequest': {
                        'requestId': f"reddot-{appointment_data.get('appointment_id', uuid.uuid4().hex)}",
                        'conferenceSolutionKey': {
                            'type': 'hangoutsMeet'
                        }
                    }
                },
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'email', 'minutes': 24 * 60},  # 1 day before
                        {'method': 'popup', 'minutes': 15},       # 15 minutes before
                    ],
                },
            }
            
            # Create the event
            created_event = self.service.events().insert(
                calendarId='primary',
                body=event,
                conferenceDataVersion=1  # Required for Meet integration
            ).execute()
            
            # Extract the Google Meet link with enhanced logic
            meet_link = None
            
            # Method 1: Check conferenceData entryPoints (most reliable)
            if 'conferenceData' in created_event and 'entryPoints' in created_event['conferenceData']:
                for entry_point in created_event['conferenceData']['entryPoints']:
                    if entry_point.get('entryPointType') == 'video':
                        meet_link = entry_point.get('uri')
                        break
            
            # Method 2: Check hangoutLink (legacy but works)
            if not meet_link:
                meet_link = created_event.get('hangoutLink')
            
            # Method 3: Try to extract from htmlLink if present
            if not meet_link and 'htmlLink' in created_event:
                html_link = created_event['htmlLink']
                # Sometimes the Meet link is embedded in the calendar HTML link
                import re
                meet_match = re.search(r'meet\.google\.com/([a-z]{3}-[a-z0-9]{4}-[a-z]{3})', html_link)
                if meet_match:
                    meet_link = f"https://meet.google.com/{meet_match.group(1)}"
            
            # Method 4: Check conference solution for conference ID
            if not meet_link and 'conferenceData' in created_event:
                conf_solution = created_event['conferenceData'].get('conferenceSolution', {})
                if conf_solution.get('key', {}).get('type') == 'hangoutsMeet':
                    conf_id = created_event['conferenceData'].get('conferenceId')
                    if conf_id:
                        meet_link = f"https://meet.google.com/{conf_id}"
            
            event_id = created_event['id']
            calendar_link = created_event.get('htmlLink')
            
            if meet_link:
                logging.info(f"✅ SUCCESS: Created Google Calendar event with REAL Meet link: {meet_link}")
            else:
                logging.error(f"❌ FAILED: Calendar event created but no Meet link found. Event data: {created_event}")
                # Log the full event structure for debugging
                logging.debug(f"Full event structure: {json.dumps(created_event, indent=2, default=str)}")
            
            return {
                'event_id': event_id,
                'meet_link': meet_link,
                'calendar_link': calendar_link,
                'raw_event': created_event  # Include for debugging
            }
            
        except HttpError as e:
            logging.error(f"Google Calendar API error: {e}")
            return None
        except Exception as e:
            logging.error(f"Failed to create calendar event: {e}")
            return None
    
    def update_calendar_event(self, event_id, updates):
        """Update existing calendar event"""
        try:
            if not self.service:
                return False
            
            event = self.service.events().get(calendarId='primary', eventId=event_id).execute()
            
            # Update the event with new data
            for key, value in updates.items():
                event[key] = value
            
            updated_event = self.service.events().update(
                calendarId='primary',
                eventId=event_id,
                body=event
            ).execute()
            
            logging.info(f"Updated Google Calendar event: {event_id}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to update calendar event: {e}")
            return False
    
    def delete_calendar_event(self, event_id):
        """Delete calendar event"""
        try:
            if not self.service:
                return False
            
            self.service.events().delete(calendarId='primary', eventId=event_id).execute()
            logging.info(f"Deleted Google Calendar event: {event_id}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to delete calendar event: {e}")
            return False

# Initialize the service
google_calendar_api = GoogleCalendarAPIService()