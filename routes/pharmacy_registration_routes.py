"""
Pharmacy registration routes — new pharmacies sign up here
"""

import os
import time
import logging
from flask import Blueprint, request, jsonify, render_template
from werkzeug.utils import secure_filename
from google.cloud import storage as gcs_storage
from models import Pharmacy, PharmacyAdmin
from services.pharmacy_service import generate_slug
from services.auth import phash
from config import AVAILABLE_THEMES
from app import db

bp = Blueprint("pharmacy_registration", __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
GCS_BUCKET = "pharma-connect-uploads"
GCS_PREFIX = "uploads/uploads"


def _allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def _save_photo(file, slug, photo_type):
    """Upload photo to GCS with a unique timestamp filename to bust caches."""
    ext = file.filename.rsplit('.', 1)[1].lower()
    ts = int(time.time())
    filename = secure_filename(f"{photo_type}_{slug}_{ts}.{ext}")
    gcs_path = f"{GCS_PREFIX}/pharmacies/{slug}/{filename}"
    client = gcs_storage.Client()
    bucket = client.bucket(GCS_BUCKET)
    blob = bucket.blob(gcs_path)
    blob.cache_control = "public, max-age=60"
    blob.upload_from_file(file.stream, rewind=True)
    return f"/static/uploads/pharmacies/{slug}/{filename}"


# ─── Template Routes ────────────────────────────────────────────────────────

@bp.route("/pharmacy")
def register_page():
    """Render pharmacy registration form"""
    return render_template("pharmacy_register.html", themes=AVAILABLE_THEMES)


# ─── API Routes ─────────────────────────────────────────────────────────────

@bp.route("/api/pharmacy", methods=["POST"])
def register_pharmacy():
    """Submit pharmacy registration (multipart/form-data)"""
    try:
        # Accept both form data and JSON
        if request.content_type and 'multipart/form-data' in request.content_type:
            data = request.form.to_dict()
        else:
            data = request.get_json() or {}

        # Accept either 'password' or 'admin_password'
        if data.get('password') and not data.get('admin_password'):
            data['admin_password'] = data['password']

        # Validate required fields
        required = ['name', 'owner_name', 'email', 'address', 'city', 'phone',
                     'admin_password']
        missing = [f for f in required if not data.get(f)]
        if missing:
            return jsonify({
                'error': f'Missing required fields: {", ".join(missing)}'
            }), 400

        # Check email uniqueness
        if Pharmacy.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'A pharmacy with this email already exists'}), 409

        if PharmacyAdmin.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'An admin account with this email already exists'}), 409

        # Generate slug
        slug = generate_slug(data['name'])

        # Validate theme
        theme_key = data.get('theme_key', 'theme-default')
        valid_themes = [t['key'] for t in AVAILABLE_THEMES]
        if theme_key not in valid_themes:
            theme_key = 'theme-default'

        # Create pharmacy record
        pharmacy = Pharmacy()
        pharmacy.name = data['name']
        pharmacy.slug = slug
        pharmacy.owner_name = data['owner_name']
        pharmacy.email = data['email']
        pharmacy.phone = data['phone']
        pharmacy.address = data['address']
        pharmacy.city = data['city']
        pharmacy.province = data.get('province', '')
        pharmacy.license_number = data.get('license_number', '')
        pharmacy.operating_hours = data.get('operating_hours', '')
        pharmacy.theme_key = theme_key
        pharmacy.status = 'pending'

        # GPS coordinates (optional)
        if data.get('latitude'):
            try:
                pharmacy.latitude = float(data['latitude'])
            except (ValueError, TypeError):
                pass
        if data.get('longitude'):
            try:
                pharmacy.longitude = float(data['longitude'])
            except (ValueError, TypeError):
                pass

        # Handle photo uploads
        if 'owner_photo' in request.files:
            file = request.files['owner_photo']
            if file and file.filename and _allowed_file(file.filename):
                pharmacy.owner_photo_path = _save_photo(file, slug, 'owner')

        if 'pharmacy_photo' in request.files:
            file = request.files['pharmacy_photo']
            if file and file.filename and _allowed_file(file.filename):
                pharmacy.pharmacy_photo_path = _save_photo(file, slug, 'pharmacy')

        db.session.add(pharmacy)
        db.session.flush()  # Get pharmacy ID

        # Create pharmacy admin account
        admin = PharmacyAdmin()
        admin.pharmacy_id = pharmacy.id
        admin.name = data['owner_name']
        admin.email = data['email']
        admin.password_hash = phash(data['admin_password'])
        db.session.add(admin)

        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Registration submitted! Your application is under review.',
            'pharmacy': {
                'id': pharmacy.id,
                'name': pharmacy.name,
                'slug': pharmacy.slug,
                'status': pharmacy.status,
            }
        }), 201

    except Exception as e:
        db.session.rollback()
        logging.error(f"Pharmacy registration error: {e}")
        return jsonify({'error': f'Registration failed: {str(e)}'}), 500


@bp.route("/api/pharmacy/status", methods=["GET"])
def check_registration_status():
    """Check pharmacy registration status by email"""
    try:
        email = request.args.get('email', '').strip()
        if not email:
            return jsonify({'error': 'Email is required'}), 400

        pharmacy = Pharmacy.query.filter_by(email=email).first()
        if not pharmacy:
            return jsonify({'error': 'No registration found for this email'}), 404

        return jsonify({
            'success': True,
            'status': pharmacy.status,
            'pharmacy_name': pharmacy.name,
            'rejection_reason': pharmacy.rejection_reason,
        })

    except Exception as e:
        logging.error(f"Check status error: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route("/api/themes", methods=["GET"])
def get_themes():
    """Get available color themes"""
    return jsonify({'success': True, 'themes': AVAILABLE_THEMES})
