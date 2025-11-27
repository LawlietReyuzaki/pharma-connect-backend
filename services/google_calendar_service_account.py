"""
Google Calendar Service Account Integration

This service uses a Google Service Account with domain-wide delegation
to create calendar events with Google Meet links for both doctors and patients.

Requirements:
1. Service Account JSON key stored in GOOGLE_SERVICE_ACCOUNT_KEY secret
2. Domain-wide delegation enabled for the service account
3. Calendar API scopes authorized in Google Workspace Admin Console
"""

import os
import json
import logging
import uuid
from datetime import datetime, timedelta

try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    GOOGLE_LIBS_AVAILABLE = True
except ImportError:
    GOOGLE_LIBS_AVAILABLE = False
    logging.warning("Google API libraries not available. Install google-api-python-client and google-auth")

SCOPES = [
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/calendar.events'
]

TIMEZONE = 'Asia/Karachi'


class GoogleCalendarServiceAccount:
    """
    Service Account-based Google Calendar integration.
    Supports domain-wide delegation for creating events in user calendars.
    """
    
    def __init__(self):
        self.credentials = None
        self.has_credentials = False
        self.service_account_email = None
        self._initialize_credentials()
    
    def _initialize_credentials(self):
        """Initialize service account credentials from environment"""
        try:
            if not GOOGLE_LIBS_AVAILABLE:
                logging.error("Google API libraries not installed")
                return
            
            service_account_key = os.environ.get('GOOGLE_SERVICE_ACCOUNT_KEY')
            
            if not service_account_key:
                logging.warning("GOOGLE_SERVICE_ACCOUNT_KEY not found in environment")
                return
            
            logging.info(f"Service account key length: {len(service_account_key)}")
            logging.info(f"Service account key starts with: {service_account_key[:50] if len(service_account_key) > 50 else service_account_key}...")
            
            try:
                key_data = json.loads(service_account_key)
                logging.info(f"Parsed JSON successfully. Keys: {list(key_data.keys())}")
            except json.JSONDecodeError as e:
                logging.error(f"Invalid JSON in GOOGLE_SERVICE_ACCOUNT_KEY: {e}")
                logging.error(f"First 100 chars: {service_account_key[:100]}")
                return
            
            required_fields = ['type', 'project_id', 'private_key_id', 'private_key', 'client_email']
            missing = [f for f in required_fields if f not in key_data]
            if missing:
                logging.error(f"Missing required fields in service account key: {missing}")
                return
            
            self.credentials = service_account.Credentials.from_service_account_info(
                key_data,
                scopes=SCOPES
            )
            
            self.service_account_email = key_data.get('client_email')
            self.has_credentials = True
            
            logging.info(f"✅ Google Calendar Service Account initialized: {self.service_account_email}")
            
        except Exception as e:
            logging.error(f"Failed to initialize service account: {e}")
            import traceback
            logging.error(f"Traceback: {traceback.format_exc()}")
            self.has_credentials = False
    
    def _get_delegated_credentials(self, user_email):
        """
        Get credentials that impersonate a specific user.
        Requires domain-wide delegation to be enabled.
        """
        if not self.has_credentials:
            return None
        
        try:
            delegated_credentials = self.credentials.with_subject(user_email)
            return delegated_credentials
        except Exception as e:
            logging.error(f"Failed to create delegated credentials for {user_email}: {e}")
            return None
    
    def _get_service(self, user_email=None):
        """
        Build Calendar service, optionally impersonating a user.
        If user_email is provided, uses domain-wide delegation.
        """
        if not self.has_credentials:
            return None
        
        try:
            if user_email:
                creds = self._get_delegated_credentials(user_email)
                if not creds:
                    return None
            else:
                creds = self.credentials
            
            service = build('calendar', 'v3', credentials=creds)
            return service
            
        except Exception as e:
            logging.error(f"Failed to build Calendar service: {e}")
            return None
    
    def create_event_with_meet(self, event_data, organizer_email=None):
        """
        Create a calendar event with Google Meet link.
        
        Args:
            event_data: dict with keys:
                - summary: Event title
                - description: Event description
                - start_time: datetime object
                - end_time: datetime object
                - attendees: list of email addresses
            organizer_email: Email of user to impersonate (for domain-wide delegation)
        
        Returns:
            dict with event_id, meet_link, html_link, or None on failure
        """
        if not self.has_credentials:
            logging.warning("No service account credentials available")
            return self._create_fallback_result(event_data)
        
        try:
            service = self._get_service(organizer_email)
            if not service:
                return self._create_fallback_result(event_data)
            
            start_time = event_data['start_time']
            end_time = event_data['end_time']
            
            if isinstance(start_time, str):
                start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            if isinstance(end_time, str):
                end_time = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            
            unique_id = f"reddot-{uuid.uuid4().hex[:12]}"
            
            event = {
                'summary': event_data.get('summary', 'Online Consultation'),
                'description': event_data.get('description', 'Auto-scheduled consultation between doctor and patient.'),
                'start': {
                    'dateTime': start_time.isoformat(),
                    'timeZone': TIMEZONE,
                },
                'end': {
                    'dateTime': end_time.isoformat(),
                    'timeZone': TIMEZONE,
                },
                'attendees': [
                    {'email': email, 'responseStatus': 'accepted'} 
                    for email in event_data.get('attendees', [])
                ],
                'conferenceData': {
                    'createRequest': {
                        'requestId': unique_id,
                        'conferenceSolutionKey': {
                            'type': 'hangoutsMeet'
                        }
                    }
                },
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'email', 'minutes': 60},
                        {'method': 'popup', 'minutes': 15},
                    ],
                },
                'guestsCanModify': False,
                'guestsCanInviteOthers': False,
            }
            
            created_event = service.events().insert(
                calendarId='primary',
                body=event,
                conferenceDataVersion=1,
                sendNotifications=True,
                sendUpdates='all'
            ).execute()
            
            meet_link = None
            conference_data = created_event.get('conferenceData', {})
            entry_points = conference_data.get('entryPoints', [])
            
            for entry in entry_points:
                if entry.get('entryPointType') == 'video':
                    meet_link = entry.get('uri')
                    break
            
            if not meet_link:
                meet_link = conference_data.get('hangoutLink')
            
            result = {
                'event_id': created_event.get('id'),
                'meet_link': meet_link,
                'html_link': created_event.get('htmlLink'),
                'organizer': organizer_email,
                'success': True
            }
            
            logging.info(f"✅ Created Google Calendar event: {result['event_id']}, Meet: {meet_link}")
            return result
            
        except HttpError as e:
            error_content = e.content.decode('utf-8') if hasattr(e, 'content') else str(e)
            logging.error(f"Google Calendar API error: {error_content}")
            
            if 'forbiddenForServiceAccounts' in str(error_content):
                logging.error("Service account needs domain-wide delegation for Google Meet")
            elif 'Invalid conference type' in str(error_content):
                logging.error("Google Meet not available - check Workspace settings")
            
            return self._create_fallback_result(event_data)
            
        except Exception as e:
            logging.error(f"Failed to create calendar event: {e}")
            return self._create_fallback_result(event_data)
    
    def create_event_for_both_calendars(self, appointment_data):
        """
        Create calendar events in BOTH doctor's and patient's calendars.
        
        Args:
            appointment_data: dict with keys:
                - doctor_email: Doctor's email address
                - patient_email: Patient's email address
                - doctor_name: Doctor's name
                - patient_name: Patient's name
                - start_time: datetime object
                - end_time: datetime object
                - symptoms: Patient symptoms
                - appointment_id: Unique appointment ID
        
        Returns:
            dict with event details for both calendars
        """
        doctor_email = appointment_data.get('doctor_email')
        patient_email = appointment_data.get('patient_email')
        doctor_name = appointment_data.get('doctor_name', 'Doctor')
        patient_name = appointment_data.get('patient_name', 'Patient')
        
        base_event = {
            'summary': 'Online Consultation - Red Dot Pharmacy',
            'description': f"""Auto-scheduled consultation between doctor and patient.

Doctor: {doctor_name}
Patient: {patient_name}
Symptoms: {appointment_data.get('symptoms', 'Not specified')}

Appointment ID: {appointment_data.get('appointment_id', 'N/A')}

Please join the Google Meet link at the scheduled time.
This is an automated message from Red Dot Pharmacy.""",
            'start_time': appointment_data['start_time'],
            'end_time': appointment_data['end_time'],
            'attendees': [doctor_email, patient_email],
        }
        
        result = {
            'doctor_event': None,
            'patient_event': None,
            'meet_link': None,
            'success': False
        }
        
        doctor_result = self.create_event_with_meet(base_event, doctor_email)
        
        if doctor_result and doctor_result.get('success'):
            result['doctor_event'] = doctor_result
            result['meet_link'] = doctor_result.get('meet_link')
            result['success'] = True
            
            logging.info(f"✅ Created event in doctor's calendar: {doctor_email}")
        else:
            logging.warning(f"Failed to create event in doctor's calendar: {doctor_email}")
        
        patient_result = self.create_event_with_meet(base_event, patient_email)
        
        if patient_result and patient_result.get('success'):
            result['patient_event'] = patient_result
            
            if not result['meet_link'] and patient_result.get('meet_link'):
                result['meet_link'] = patient_result.get('meet_link')
            
            result['success'] = True
            logging.info(f"✅ Created event in patient's calendar: {patient_email}")
        else:
            logging.warning(f"Failed to create event in patient's calendar: {patient_email}")
        
        if not result['meet_link']:
            result['meet_link'] = self._generate_jitsi_fallback(appointment_data.get('appointment_id'))
            logging.info(f"Using Jitsi Meet fallback: {result['meet_link']}")
        
        return result
    
    def update_event(self, event_id, updates, user_email=None):
        """Update an existing calendar event"""
        if not self.has_credentials:
            return None
        
        try:
            service = self._get_service(user_email)
            if not service:
                return None
            
            event = service.events().get(
                calendarId='primary',
                eventId=event_id
            ).execute()
            
            if 'summary' in updates:
                event['summary'] = updates['summary']
            if 'description' in updates:
                event['description'] = updates['description']
            if 'status' in updates and updates['status'] == 'cancelled':
                event['status'] = 'cancelled'
            
            updated_event = service.events().update(
                calendarId='primary',
                eventId=event_id,
                body=event,
                sendUpdates='all'
            ).execute()
            
            return updated_event
            
        except Exception as e:
            logging.error(f"Failed to update calendar event: {e}")
            return None
    
    def delete_event(self, event_id, user_email=None):
        """Delete/cancel a calendar event"""
        if not self.has_credentials:
            return False
        
        try:
            service = self._get_service(user_email)
            if not service:
                return False
            
            service.events().delete(
                calendarId='primary',
                eventId=event_id,
                sendUpdates='all'
            ).execute()
            
            logging.info(f"Deleted calendar event: {event_id}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to delete calendar event: {e}")
            return False
    
    def _generate_jitsi_fallback(self, appointment_id=None):
        """Generate a Jitsi Meet link as fallback"""
        import hashlib
        
        room_base = f"reddotpharmacy-{appointment_id or 'consultation'}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        room_hash = hashlib.md5(room_base.encode()).hexdigest()[:12]
        room_name = f"RedDotPharmacy-{room_hash}"
        
        return f"https://meet.jit.si/{room_name}"
    
    def _create_fallback_result(self, event_data):
        """Create a fallback result when Google Calendar fails"""
        appointment_id = event_data.get('appointment_id', uuid.uuid4().hex[:8])
        
        return {
            'event_id': f"fallback_{appointment_id}",
            'meet_link': self._generate_jitsi_fallback(appointment_id),
            'html_link': None,
            'success': False,
            'fallback': True
        }
    
    def reinitialize(self):
        """Reinitialize credentials from environment (useful after secret updates)"""
        self.credentials = None
        self.has_credentials = False
        self.service_account_email = None
        self._initialize_credentials()
        return self.has_credentials
    
    def check_service_account_setup(self):
        """Check if service account is properly configured"""
        if not self.has_credentials:
            self.reinitialize()
        
        status = {
            'has_credentials': self.has_credentials,
            'service_account_email': self.service_account_email,
            'libraries_available': GOOGLE_LIBS_AVAILABLE,
            'issues': []
        }
        
        if not GOOGLE_LIBS_AVAILABLE:
            status['issues'].append("Google API libraries not installed")
        
        if not os.environ.get('GOOGLE_SERVICE_ACCOUNT_KEY'):
            status['issues'].append("GOOGLE_SERVICE_ACCOUNT_KEY secret not set")
        
        if not self.has_credentials:
            status['issues'].append("Failed to initialize service account credentials")
        
        return status


calendar_service_account = GoogleCalendarServiceAccount()
