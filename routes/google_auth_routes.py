from flask import Blueprint, redirect, request, session, jsonify, url_for
import logging
from services.google_calendar_integration import google_calendar_api

bp = Blueprint('google_auth', __name__, url_prefix='/auth/google')

@bp.route('/authorize')
def authorize():
    """Initiate Google OAuth flow"""
    try:
        auth_url = google_calendar_api.get_oauth_url()
        
        if not auth_url:
            return jsonify({"error": "Google OAuth not configured"}), 500
        
        # Store the referring page to redirect back after auth
        session['auth_redirect'] = request.args.get('redirect', '/dashboard')
        
        return redirect(auth_url)
        
    except Exception as e:
        logging.error(f"OAuth authorization error: {e}")
        return jsonify({"error": "Failed to initiate OAuth"}), 500

@bp.route('/callback')
def callback():
    """Handle Google OAuth callback"""
    try:
        # Get the authorization code from the callback
        auth_code = request.args.get('code')
        
        if not auth_code:
            error = request.args.get('error')
            logging.error(f"OAuth callback error: {error}")
            return redirect('/dashboard?error=oauth_failed')
        
        # Exchange code for token
        credentials = google_calendar_api.exchange_code_for_token(auth_code)
        
        if credentials:
            # Store OAuth success in session
            session['google_oauth_completed'] = True
            session['google_oauth_email'] = getattr(credentials, 'id_token', {}).get('email', 'unknown')
            
            logging.info("Google OAuth completed successfully")
            
            # Redirect to original page or dashboard
            redirect_url = session.pop('auth_redirect', '/dashboard')
            return redirect(f"{redirect_url}?oauth=success")
        else:
            logging.error("Failed to exchange OAuth code for token")
            return redirect('/dashboard?error=oauth_exchange_failed')
            
    except Exception as e:
        logging.error(f"OAuth callback error: {e}")
        return redirect('/dashboard?error=oauth_callback_failed')

@bp.route('/status')
def status():
    """Check Google OAuth status"""
    try:
        oauth_completed = session.get('google_oauth_completed', False)
        oauth_email = session.get('google_oauth_email')
        
        return jsonify({
            "authorized": oauth_completed,
            "email": oauth_email,
            "service_available": google_calendar_api.has_credentials
        })
        
    except Exception as e:
        logging.error(f"OAuth status error: {e}")
        return jsonify({"error": "Failed to check OAuth status"}), 500

@bp.route('/revoke')
def revoke():
    """Revoke Google OAuth authorization"""
    try:
        # Clear OAuth session data
        session.pop('google_oauth_completed', None)
        session.pop('google_oauth_email', None)
        
        # Reset the service
        google_calendar_api.service = None
        google_calendar_api.credentials = None
        
        return jsonify({"success": True, "message": "OAuth authorization revoked"})
        
    except Exception as e:
        logging.error(f"OAuth revoke error: {e}")
        return jsonify({"error": "Failed to revoke OAuth"}), 500