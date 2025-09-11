import os
import logging
import json
from datetime import datetime, timedelta
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from models import User, db
import uuid

# Google OAuth configuration for doctors
SCOPES = [
    "openid", "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/calendar"
]
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_OAUTH_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_OAUTH_CLIENT_SECRET')
REDIRECT_URI = f"https://{os.environ.get('REPLIT_DEV_DOMAIN', 'localhost')}/doctor/auth/google/callback"

print("REDIRECT_URI = ", REDIRECT_URI)


class DoctorOAuthService:

    def __init__(self):
        self.has_credentials = GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET
        if self.has_credentials:
            logging.info(
                "Doctor OAuth service configured with Google credentials")
        else:
            logging.warning(
                "Google OAuth credentials not found for doctor integration")

    def get_authorization_url(self, doctor_id):
        """Get Google OAuth authorization URL for a specific doctor"""
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

            flow = Flow.from_client_config(client_config,
                                           scopes=SCOPES,
                                           redirect_uri=REDIRECT_URI)

            # Generate authorization URL with state parameter containing doctor ID
            auth_url, state = flow.authorization_url(
                access_type='offline',  # Request refresh token
                include_granted_scopes='true',
                prompt='consent',  # Force consent to get refresh token
                state=f"doctor_{doctor_id}"  # Include doctor ID in state
            )

            return auth_url, state

        except Exception as e:
            logging.error(
                f"Failed to generate OAuth URL for doctor {doctor_id}: {e}")
            return None, None

    def exchange_code_for_tokens(self, auth_code, state):
        """Exchange authorization code for access and refresh tokens"""
        try:
            if not self.has_credentials:
                return None

            # Extract doctor ID from state
            if not state or not state.startswith('doctor_'):
                logging.error("Invalid OAuth state parameter")
                return None

            doctor_id = int(state.split('_')[1])

            client_config = {
                "web": {
                    "client_id": GOOGLE_CLIENT_ID,
                    "client_secret": GOOGLE_CLIENT_SECRET,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [REDIRECT_URI]
                }
            }

            flow = Flow.from_client_config(client_config,
                                           scopes=SCOPES,
                                           redirect_uri=REDIRECT_URI)

            # Exchange code for tokens
            flow.fetch_token(code=auth_code)
            credentials = flow.credentials
            print("credentials = ", credentials)

            # Get user info to verify the Google account
            user_info = self._get_user_info(credentials)

            # Store tokens in database
            doctor = User.query.filter_by(id=doctor_id, role='doctor').first()
            if doctor:
                # Store encrypted tokens (in production, encrypt these!)
                doctor.google_access_token = credentials.token
                doctor.google_refresh_token = credentials.refresh_token
                doctor.google_token_expiry = credentials.expiry
                doctor.google_email = user_info.get(
                    'email') if user_info else None
                doctor.google_connected_at = datetime.utcnow()

                db.session.commit()

                logging.info(
                    f"✅ Doctor {doctor.name} connected Google Calendar: {doctor.google_email}"
                )
                return {
                    'doctor_id': doctor_id,
                    'doctor_name': doctor.name,
                    'google_email': doctor.google_email,
                    'connected_at': doctor.google_connected_at
                }
            else:
                logging.error(f"Doctor not found for ID: {doctor_id}")
                return None

        except Exception as e:
            logging.error(f"Failed to exchange OAuth code: {e}")
            return None

    def get_doctor_credentials(self, doctor_id):
        """Get valid Google credentials for a doctor, refreshing if necessary"""
        try:
            doctor = User.query.filter_by(id=doctor_id, role='doctor').first()
            if not doctor or not doctor.google_access_token:
                return None

            # Create credentials object
            credentials = Credentials(
                token=doctor.google_access_token,
                refresh_token=doctor.google_refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=GOOGLE_CLIENT_ID,
                client_secret=GOOGLE_CLIENT_SECRET,
                scopes=SCOPES)

            # Check if token needs refresh
            if credentials.expired and credentials.refresh_token:
                try:
                    credentials.refresh(Request())

                    # Update stored tokens
                    doctor.google_access_token = credentials.token
                    doctor.google_token_expiry = credentials.expiry
                    db.session.commit()

                    logging.info(
                        f"🔄 Refreshed OAuth token for doctor {doctor.name}")
                except Exception as e:
                    logging.error(
                        f"Failed to refresh token for doctor {doctor.name}: {e}"
                    )
                    return None

            return credentials

        except Exception as e:
            logging.error(f"Failed to get doctor credentials: {e}")
            return None

    def create_calendar_event_for_doctor(self, doctor_id, appointment_data):
        """Create a Google Calendar event in the doctor's personal calendar"""
        try:
            credentials = self.get_doctor_credentials(doctor_id)
            if not credentials:
                logging.warning(
                    f"No valid Google credentials for doctor {doctor_id}")
                return None

            # Build Calendar service
            service = build('calendar', 'v3', credentials=credentials)

            # Create the event object
            event = {
                'summary':
                appointment_data.get(
                    'summary', 'Red Dot Pharmacy - Patient Consultation'),
                'description':
                appointment_data.get('description', ''),
                'start': {
                    'dateTime': appointment_data['start_time'].isoformat(),
                    'timeZone': 'Asia/Karachi',
                },
                'end': {
                    'dateTime': appointment_data['end_time'].isoformat(),
                    'timeZone': 'Asia/Karachi',
                },
                'attendees': [{
                    'email': email
                } for email in appointment_data.get('attendee_emails', [])],
                'conferenceData': {
                    'createRequest': {
                        'requestId':
                        f"reddot-{appointment_data.get('appointment_id', uuid.uuid4().hex)}",
                        'conferenceSolutionKey': {
                            'type': 'hangoutsMeet'
                        }
                    }
                },
                'reminders': {
                    'useDefault':
                    False,
                    'overrides': [
                        {
                            'method': 'email',
                            'minutes': 24 * 60
                        },  # 1 day before
                        {
                            'method': 'popup',
                            'minutes': 15
                        },  # 15 minutes before
                    ],
                },
            }

            # Create the event with Meet integration
            created_event = service.events().insert(
                calendarId='primary',
                body=event,
                conferenceDataVersion=1  # Required for Meet integration
            ).execute()

            # Extract Google Meet link with enhanced logic
            meet_link = None

            # Method 1: Check conferenceData entryPoints
            if 'conferenceData' in created_event and 'entryPoints' in created_event[
                    'conferenceData']:
                for entry_point in created_event['conferenceData'][
                        'entryPoints']:
                    if entry_point.get('entryPointType') == 'video':
                        meet_link = entry_point.get('uri')
                        break

            # Method 2: Check hangoutLink
            if not meet_link:
                meet_link = created_event.get('hangoutLink')

            # Method 3: Extract from htmlLink
            if not meet_link and 'htmlLink' in created_event:
                html_link = created_event['htmlLink']
                import re
                meet_match = re.search(
                    r'meet\.google\.com/([a-z]{3}-[a-z0-9]{4}-[a-z]{3})',
                    html_link)
                if meet_match:
                    meet_link = f"https://meet.google.com/{meet_match.group(1)}"

            doctor = User.query.get(doctor_id)
            if doctor:
                if meet_link:
                    logging.info(
                        f"✅ SUCCESS: Created REAL Google Meet in {doctor.name}'s calendar: {meet_link}"
                    )
                else:
                    logging.error(
                        f"❌ FAILED: Calendar event created in {doctor.name}'s calendar but no Meet link found"
                    )

                return {
                    'event_id': created_event['id'],
                    'meet_link': meet_link,
                    'calendar_link': created_event.get('htmlLink'),
                    'doctor_calendar': doctor.google_email or 'Unknown'
                }
            else:
                logging.error(f"Doctor not found for ID: {doctor_id}")
                return {
                    'event_id': created_event['id'],
                    'meet_link': meet_link,
                    'calendar_link': created_event.get('htmlLink'),
                    'doctor_calendar': 'Unknown'
                }

        except HttpError as e:
            logging.error(
                f"Google Calendar API error for doctor {doctor_id}: {e}")
            return None
        except Exception as e:
            logging.error(
                f"Failed to create calendar event for doctor {doctor_id}: {e}")
            return None

    def _get_user_info(self, credentials):
        """Get user information from Google OAuth"""
        try:
            service = build('oauth2', 'v2', credentials=credentials)
            user_info = service.userinfo().get().execute()
            return user_info
        except Exception as e:
            logging.error(f"Failed to get user info: {e}")
            return None

    def revoke_doctor_authorization(self, doctor_id):
        """Revoke Google OAuth authorization for a doctor"""
        try:
            doctor = User.query.filter_by(id=doctor_id, role='doctor').first()
            if doctor:
                # Clear OAuth data
                doctor.google_access_token = None
                doctor.google_refresh_token = None
                doctor.google_token_expiry = None
                doctor.google_email = None
                doctor.google_connected_at = None

                db.session.commit()

                logging.info(
                    f"🔓 Revoked Google Calendar access for doctor {doctor.name}"
                )
                return True
            return False

        except Exception as e:
            logging.error(
                f"Failed to revoke authorization for doctor {doctor_id}: {e}")
            return False


# Initialize service
doctor_oauth_service = DoctorOAuthService()
