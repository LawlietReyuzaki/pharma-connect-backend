from flask import Blueprint, request, jsonify
from services.auth import verify_user, create_token
from models import User
from app import db
import hashlib

bp = Blueprint("auth", __name__)

def phash(pw):
    """Hash password using SHA256"""
    return hashlib.sha256(pw.encode()).hexdigest()

@bp.route("/login", methods=["POST"])
def login():
    """User login endpoint"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        email = data.get("email", "").strip()
        password = data.get("password", "")
        
        if not email or not password:
            return jsonify({"error": "Email and password are required"}), 400
        
        # Verify user credentials
        user = verify_user(email, password)
        if not user:
            return jsonify({"error": "Invalid credentials"}), 401
        
        # Create JWT token
        token = create_token(user)
        
        return jsonify({
            "success": True,
            "token": token,
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "role": user.role,
                "phone": user.phone
            }
        })
        
    except Exception as e:
        return jsonify({"error": f"Login failed: {str(e)}"}), 500

@bp.route("/register", methods=["POST"])
def register():
    """Patient registration endpoint"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Validate required fields
        required_fields = ["name", "email", "password", "phone"]
        for field in required_fields:
            if not data.get(field):
                return jsonify({"error": f"{field} is required"}), 400
        
        # Check if email already exists
        existing_user = User.query.filter_by(email=data["email"]).first()
        if existing_user:
            return jsonify({"error": "Email already registered"}), 400
        
        # Create new patient user
        new_user = User()
        new_user.name = data["name"]
        new_user.email = data["email"]
        new_user.phone = data["phone"]
        new_user.role = "patient"  # Default role for registration
        new_user.password_hash = phash(data["password"])
        
        db.session.add(new_user)
        db.session.commit()
        
        # Create token for immediate login
        token = create_token(new_user)
        
        return jsonify({
            "success": True,
            "message": "Registration successful",
            "token": token,
            "user": {
                "id": new_user.id,
                "name": new_user.name,
                "email": new_user.email,
                "role": new_user.role,
                "phone": new_user.phone
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Registration failed: {str(e)}"}), 500

@bp.route("/verify", methods=["POST"])
def verify_token():
    """Verify JWT token"""
    try:
        from services.auth import verify_token
        
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({"error": "No valid token provided"}), 401
        
        token = auth_header.split(' ')[1]
        user_data = verify_token(token)
        
        if not user_data:
            return jsonify({"error": "Invalid or expired token"}), 401
        
        # Get fresh user data from database
        user = User.query.get(user_data['sub'])
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        return jsonify({
            "valid": True,
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "role": user.role,
                "phone": user.phone
            }
        })
        
    except Exception as e:
        return jsonify({"error": f"Token verification failed: {str(e)}"}), 500

@bp.route("/profile", methods=["PUT"])
def update_profile():
    """Update user profile"""
    try:
        from services.auth import require_auth, get_current_user
        
        # Verify authentication
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({"error": "Authentication required"}), 401
        
        current_user = get_current_user()
        if not current_user:
            return jsonify({"error": "User not found"}), 404
        
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Update allowed fields
        if "name" in data:
            current_user.name = data["name"]
        if "phone" in data:
            current_user.phone = data["phone"]
        
        # Update password if provided
        if "password" in data and data["password"]:
            current_user.password_hash = phash(data["password"])
        
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Profile updated successfully",
            "user": {
                "id": current_user.id,
                "name": current_user.name,
                "email": current_user.email,
                "role": current_user.role,
                "phone": current_user.phone
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Profile update failed: {str(e)}"}), 500
