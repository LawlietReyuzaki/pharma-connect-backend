from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
import jwt
import hashlib
import logging
import os
from app import db

bp = Blueprint("admin_auth", __name__)

def hash_password(password):
    """Hash password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

def create_admin_token(admin):
    """Create JWT token for admin"""
    try:
        payload = {
            'admin_id': admin['admin_id'],
            'email': admin['email'],
            'name': admin['name'],
            'role': 'admin',
            'exp': datetime.utcnow() + timedelta(hours=12)
        }
        
        secret_key = os.environ.get('SESSION_SECRET', 'red-dot-pharmacy-secret-key')
        token = jwt.encode(payload, secret_key, algorithm='HS256')
        return token
    except Exception as e:
        logging.error(f"Token creation error: {e}")
        return None

def verify_admin_token(token):
    """Verify admin JWT token"""
    try:
        secret_key = os.environ.get('SESSION_SECRET', 'red-dot-pharmacy-secret-key')
        payload = jwt.decode(token, secret_key, algorithms=['HS256'])
        
        # Ensure this is an admin token
        if payload.get('role') != 'admin':
            return None
            
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
    except Exception as e:
        logging.error(f"Token verification error: {e}")
        return None

@bp.route("/login", methods=["POST"])
def admin_login():
    """Admin login endpoint"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        email = data.get("email", "").strip()
        password = data.get("password", "").strip()
        
        if not email or not password:
            return jsonify({"error": "Email and password are required"}), 400
        
        # Query admins table directly
        from app import db
        from sqlalchemy import text
        cursor = db.session.execute(
            text("SELECT admin_id, name, email, password FROM admins WHERE email = :email"),
            {"email": email}
        )
        admin_row = cursor.fetchone()
        
        if not admin_row:
            return jsonify({"error": "Invalid admin credentials"}), 401
        
        # Verify password
        hashed_password = hash_password(password)
        stored_password = admin_row[3]  # password is at index 3
        
        # Debug logging
        logging.info(f"Login attempt for admin: {email}")
        logging.info(f"Password hash from input: {hashed_password}")
        logging.info(f"Stored password hash: {stored_password}")
        
        if stored_password != hashed_password:
            logging.warning(f"Password mismatch for admin {email}")
            return jsonify({"error": "Invalid admin credentials"}), 401
        
        # Convert row to dict for token creation
        admin_data = {
            'admin_id': admin_row[0],
            'name': admin_row[1],
            'email': admin_row[2]
        }
        
        # Create JWT token
        token = create_admin_token(admin_data)
        if not token:
            return jsonify({"error": "Failed to create session"}), 500
        
        return jsonify({
            "success": True,
            "token": token,
            "admin": {
                "admin_id": admin_data['admin_id'],
                "name": admin_data['name'],
                "email": admin_data['email'],
                "role": "admin"
            }
        })
        
    except Exception as e:
        logging.error(f"Admin login error: {e}")
        return jsonify({"error": f"Login failed: {str(e)}"}), 500

@bp.route("/verify", methods=["POST"])
def verify_admin_token_route():
    """Verify admin JWT token"""
    try:
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({"error": "No valid token provided"}), 401
        
        token = auth_header.split(' ')[1]
        admin_data = verify_admin_token(token)
        
        if not admin_data:
            return jsonify({"error": "Invalid or expired token"}), 401
        
        # Get fresh admin data from database  
        from sqlalchemy import text
        cursor = db.session.execute(
            text("SELECT admin_id, name, email FROM admins WHERE admin_id = :admin_id"),
            {"admin_id": admin_data['admin_id']}
        )
        admin_row = cursor.fetchone()
        
        if not admin_row:
            return jsonify({"error": "Admin not found"}), 404
        
        return jsonify({
            "valid": True,
            "admin": {
                "admin_id": admin_row[0],
                "name": admin_row[1],
                "email": admin_row[2],
                "role": "admin"
            }
        })
        
    except Exception as e:
        logging.error(f"Admin token verification error: {e}")
        return jsonify({"error": f"Token verification failed: {str(e)}"}), 500

def get_current_admin():
    """Get current authenticated admin from request"""
    try:
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return None
        
        token = auth_header.split(' ')[1]
        admin_data = verify_admin_token(token)
        
        if not admin_data:
            return None
        
        # Get admin from database
        from sqlalchemy import text
        cursor = db.session.execute(
            text("SELECT admin_id, name, email FROM admins WHERE admin_id = :admin_id"),
            {"admin_id": admin_data['admin_id']}
        )
        admin_row = cursor.fetchone()
        
        if not admin_row:
            return None
            
        return {
            'admin_id': admin_row[0],
            'name': admin_row[1],
            'email': admin_row[2],
            'role': 'admin'
        }
        
    except Exception as e:
        logging.error(f"Get current admin error: {e}")
        return None

def require_admin():
    """Decorator to require admin authentication"""
    def decorator(f):
        def wrapper(*args, **kwargs):
            admin = get_current_admin()
            if not admin:
                return jsonify({"error": "Admin access required"}), 403
            return f(*args, **kwargs)
        wrapper.__name__ = f.__name__
        return wrapper
    return decorator