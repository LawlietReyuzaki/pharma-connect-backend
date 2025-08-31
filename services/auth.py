import os
import time
import jwt
import hashlib
from functools import wraps
from flask import request, jsonify, current_app, g
from models import User

def phash(pw):
    """Hash password using SHA256"""
    return hashlib.sha256(pw.encode()).hexdigest()

def create_token(user):
    """Create JWT token for user"""
    secret = os.environ.get("JWT_SECRET", "red-dot-pharmacy-jwt-secret-key-2025")
    payload = {
        "sub": str(user.id),  # Convert to string for JWT compatibility
        "role": user.role,
        "name": user.name,
        "email": user.email,
        "exp": int(time.time()) + 60*60*24  # 24 hours
    }
    return jwt.encode(payload, secret, algorithm="HS256")

def verify_token(token):
    """Verify JWT token and return user data"""
    try:
        secret = os.environ.get("JWT_SECRET", "red-dot-pharmacy-jwt-secret-key-2025")
        payload = jwt.decode(token, secret, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def verify_user(email, password):
    """Verify user credentials"""
    user = User.query.filter_by(email=email).first()
    if not user:
        return None
    
    if user.password_hash == phash(password):
        return user
    
    return None

def require_auth(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization')
        
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
        
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        
        user_data = verify_token(token)
        if not user_data:
            return jsonify({'error': 'Token is invalid or expired'}), 401
        
        # Add user data to request context
        g.current_user = user_data
        
        return f(*args, **kwargs)
    
    return decorated

def require_role(required_role):
    """Decorator to require specific role"""
    def decorator(f):
        @wraps(f)
        @require_auth
        def decorated(*args, **kwargs):
            user_data = g.current_user
            
            if user_data['role'] != required_role and user_data['role'] != 'admin':
                return jsonify({'error': 'Insufficient permissions'}), 403
            
            return f(*args, **kwargs)
        
        return decorated
    return decorator

def get_current_user():
    """Get current user from token"""
    token = None
    auth_header = request.headers.get('Authorization')
    
    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header.split(' ')[1]
    
    if token:
        user_data = verify_token(token)
        if user_data:
            return User.query.get(user_data['sub'])
    
    return None
