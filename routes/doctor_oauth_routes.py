from flask import Blueprint, request, redirect, session, jsonify, url_for
import logging
from services.doctor_oauth_service import doctor_oauth_service
from services.auth import verify_token
from models import User
from functools import wraps

# JWT-based doctor authentication decorator
def require_doctor_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({"error": "Authentication required"}), 401
        
        token = auth_header.split(' ')[1]
        user_data = verify_token(token)
        
        if not user_data:
            return jsonify({"error": "Invalid or expired token"}), 401
        
        doctor = User.query.filter_by(id=user_data['sub'], role="doctor").first()
        if not doctor:
            return jsonify({"error": "Doctor not found"}), 404
        
        # Store doctor in kwargs for the decorated function
        kwargs['doctor'] = doctor
        return f(*args, **kwargs)
    return decorated_function

bp = Blueprint('doctor_oauth', __name__, url_prefix='/doctor/auth/google')

@bp.route('/authorize')
def authorize():
    """Initiate Google OAuth flow for the logged-in doctor"""
    try:
        # Get doctor ID from query parameter (passed from frontend)
        doctor_id = request.args.get('doctor_id')
        if not doctor_id:
            return redirect('/doctor/dashboard?error=missing_doctor_id')
        
        try:
            doctor_id = int(doctor_id)
        except ValueError:
            return redirect('/doctor/dashboard?error=invalid_doctor_id')
        
        # Verify doctor exists
        doctor = User.query.filter_by(id=doctor_id, role='doctor').first()
        if not doctor:
            return redirect('/doctor/dashboard?error=doctor_not_found')
        
        # Get OAuth authorization URL
        auth_result = doctor_oauth_service.get_authorization_url(doctor_id)
        
        if not auth_result or auth_result == (None, None):
            return jsonify({"error": "Google OAuth not configured"}), 500
        
        auth_url, state = auth_result
        
        if not auth_url:
            return jsonify({"error": "Failed to generate OAuth URL"}), 500
        
        # Store state in session for security
        session['oauth_state'] = state
        session['oauth_redirect'] = request.args.get('redirect', '/doctor/dashboard')
        
        return redirect(auth_url)
        
    except Exception as e:
        logging.error(f"Doctor OAuth authorization error: {e}")
        return jsonify({"error": "Failed to initiate OAuth"}), 500

@bp.route('/callback')
def callback():
    """Handle Google OAuth callback for doctor"""
    try:
        # Get authorization code and state from callback
        auth_code = request.args.get('code')
        state = request.args.get('state')
        
        if not auth_code:
            error = request.args.get('error')
            logging.error(f"OAuth callback error: {error}")
            return redirect('/doctor/dashboard?error=oauth_failed')
        
        # Verify state parameter
        expected_state = session.pop('oauth_state', None)
        if state != expected_state:
            logging.error("OAuth state mismatch - possible CSRF attack")
            return redirect('/doctor/dashboard?error=oauth_security_error')
        
        # Exchange code for tokens
        result = doctor_oauth_service.exchange_code_for_tokens(auth_code, state)
        
        if result:
            # Store success in session
            session['google_oauth_completed'] = True
            session['google_oauth_doctor_name'] = result['doctor_name']
            session['google_oauth_email'] = result['google_email']
            
            logging.info(f"✅ Doctor {result['doctor_name']} connected Google Calendar: {result['google_email']}")
            
            # Redirect to dashboard with success message
            redirect_url = session.pop('oauth_redirect', '/doctor/dashboard')
            return redirect(f"{redirect_url}?oauth=success")
        else:
            logging.error("Failed to exchange OAuth code for tokens")
            return redirect('/doctor/dashboard?error=oauth_exchange_failed')
            
    except Exception as e:
        logging.error(f"Doctor OAuth callback error: {e}")
        return redirect('/doctor/dashboard?error=oauth_callback_failed')

@bp.route('/status')
@require_doctor_auth
def status(doctor):
    """Check Google OAuth status for the logged-in doctor"""
    try:
        doctor_id = doctor.id
        
        # Check if doctor has Google OAuth connected
        is_connected = bool(doctor.google_access_token and doctor.google_email)
        
        # Test if credentials are still valid
        credentials_valid = False
        if is_connected:
            credentials = doctor_oauth_service.get_doctor_credentials(doctor_id)
            credentials_valid = credentials is not None
        
        return jsonify({
            "connected": is_connected,
            "credentials_valid": credentials_valid,
            "google_email": doctor.google_email if is_connected else None,
            "connected_at": doctor.google_connected_at.isoformat() if doctor.google_connected_at else None,
            "doctor_name": doctor.name,
            "service_available": doctor_oauth_service.has_credentials
        })
        
    except Exception as e:
        logging.error(f"Doctor OAuth status error: {e}")
        return jsonify({"error": "Failed to check OAuth status"}), 500

@bp.route('/revoke', methods=['POST'])
@require_doctor_auth
def revoke(doctor):
    """Revoke Google OAuth authorization for the logged-in doctor"""
    try:
        doctor_id = doctor.id
        
        success = doctor_oauth_service.revoke_doctor_authorization(doctor_id)
        
        if success:
            # Clear OAuth session data
            session.pop('google_oauth_completed', None)
            session.pop('google_oauth_doctor_name', None)
            session.pop('google_oauth_email', None)
            
            return jsonify({
                "success": True,
                "message": "Google Calendar access revoked successfully"
            })
        else:
            return jsonify({"error": "Failed to revoke authorization"}), 500
            
    except Exception as e:
        logging.error(f"Doctor OAuth revoke error: {e}")
        return jsonify({"error": "Failed to revoke authorization"}), 500

@bp.route('/test-calendar', methods=['POST'])
@require_doctor_auth
def test_calendar(doctor):
    """Test doctor's Google Calendar integration"""
    try:
        doctor_id = doctor.id
        
        # Check if doctor has Google OAuth connected
        if not doctor.google_access_token:
            return jsonify({"error": "Google Calendar not connected"}), 400
        
        # Test credentials
        credentials = doctor_oauth_service.get_doctor_credentials(doctor_id)
        if not credentials:
            return jsonify({"error": "Invalid or expired credentials"}), 400
        
        # Try to create a test event (but don't actually save it)
        from datetime import datetime, timedelta
        from googleapiclient.discovery import build
        
        service = build('calendar', 'v3', credentials=credentials)
        
        # Just test by listing calendars (read-only operation)
        calendar_list = service.calendarList().list().execute()
        
        return jsonify({
            "success": True,
            "message": "Google Calendar integration working",
            "calendar_count": len(calendar_list.get('items', [])),
            "primary_calendar": calendar_list.get('items', [{}])[0].get('summary', 'Primary')
        })
        
    except Exception as e:
        logging.error(f"Doctor calendar test error: {e}")
        return jsonify({"error": f"Calendar test failed: {str(e)}"}), 500