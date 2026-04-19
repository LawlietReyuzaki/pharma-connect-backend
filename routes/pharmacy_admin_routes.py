"""
Pharmacy Admin Dashboard routes — each pharmacy manages its own data here
"""

import os
import time
import logging
import hashlib
from datetime import datetime
from flask import Blueprint, request, jsonify, render_template, g
from google.cloud import storage as gcs_storage
from models import (
    Pharmacy, PharmacyAdmin, PharmacyReview, User, Order, OrderItem,
    Appointment, ChatLog, Medicine
)
from services.auth import (
    phash, create_pharmacy_admin_token, verify_pharmacy_admin_token,
    get_current_pharmacy_admin, require_pharmacy_admin
)
from services.pharmacy_service import get_pharmacy_stats, pharmacy_to_dict
from config import AVAILABLE_THEMES
from app import db

bp = Blueprint("pharmacy_admin", __name__)

GCS_BUCKET = "pharma-connect-uploads"
GCS_PREFIX = "uploads/uploads"

def upload_to_gcs(file_stream, gcs_path):
    """Upload a file stream to GCS and return the public /static/uploads/ URL."""
    try:
        client = gcs_storage.Client()
        bucket = client.bucket(GCS_BUCKET)
        blob = bucket.blob(f"{GCS_PREFIX}/{gcs_path}")
        blob.cache_control = "public, max-age=60"
        blob.upload_from_file(file_stream, rewind=True)
        return f"/static/uploads/{gcs_path}"
    except Exception as e:
        logging.error(f"GCS upload failed: {e}")
        raise


# ─── Template Route ─────────────────────────────────────────────────────────

@bp.route("/")
def dashboard_page():
    """Render pharmacy admin dashboard"""
    return render_template("pharmacy_admin_dashboard.html")


# ─── Auth ────────────────────────────────────────────────────────────────────

@bp.route("/api/login", methods=["POST"])
def pharmacy_admin_login():
    """Pharmacy admin login"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        email = data.get('email', '').strip()
        password = data.get('password', '').strip()
        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400

        admin = PharmacyAdmin.query.filter_by(email=email).first()
        if not admin:
            return jsonify({'error': 'No account found with this email. Please register first.'}), 401
        if admin.password_hash != phash(password):
            return jsonify({'error': 'Incorrect password. Please try again.'}), 401

        # Check pharmacy is approved
        pharmacy = Pharmacy.query.get(admin.pharmacy_id)
        if not pharmacy:
            return jsonify({'error': 'Pharmacy record not found. Contact support.'}), 404
        if pharmacy.status == 'pending':
            return jsonify({'error': 'Your pharmacy application is still under review. You will be notified once approved.', 'status': 'pending'}), 403
        if pharmacy.status == 'suspended':
            return jsonify({'error': 'Your pharmacy has been suspended. Contact support for details.', 'status': 'suspended'}), 403
        if pharmacy.status != 'approved':
            return jsonify({'error': f'Your pharmacy status is: {pharmacy.status}. Only approved pharmacies can log in.', 'status': pharmacy.status}), 403

        token = create_pharmacy_admin_token(admin)

        return jsonify({
            'success': True,
            'token': token,
            'admin': {
                'id': admin.id,
                'name': admin.name,
                'email': admin.email,
                'pharmacy_id': admin.pharmacy_id,
                'pharmacy_name': pharmacy.name,
                'pharmacy_slug': pharmacy.slug,
            }
        })

    except Exception as e:
        logging.error(f"Pharmacy admin login error: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route("/api/verify", methods=["POST"])
def verify_token_route():
    """Verify pharmacy admin token"""
    try:
        admin = get_current_pharmacy_admin()
        if not admin:
            return jsonify({'error': 'Invalid token'}), 401

        pharmacy = Pharmacy.query.get(admin.pharmacy_id)
        return jsonify({
            'valid': True,
            'admin': {
                'id': admin.id,
                'name': admin.name,
                'email': admin.email,
                'pharmacy_id': admin.pharmacy_id,
                'pharmacy_name': pharmacy.name if pharmacy else '',
            }
        })

    except Exception as e:
        logging.error(f"Token verify error: {e}")
        return jsonify({'error': str(e)}), 500


# ─── Dashboard Stats ────────────────────────────────────────────────────────

@bp.route("/api/stats", methods=["GET"])
@require_pharmacy_admin
def dashboard_stats():
    """Get dashboard statistics for this pharmacy"""
    try:
        from models import Appointment, ChatLog
        s = get_pharmacy_stats(g.pharmacy_id)
        pharmacy = Pharmacy.query.get(g.pharmacy_id)

        pending_orders = Order.query.filter_by(
            pharmacy_id=g.pharmacy_id, status='pending'
        ).count()

        total_appointments = Appointment.query.join(
            User, Appointment.doctor_id == User.id
        ).filter(User.pharmacy_id == g.pharmacy_id).count()

        total_chat_logs = ChatLog.query.filter_by(
            pharmacy_id=g.pharmacy_id
        ).count()

        stats = {
            'total_orders': s['total_orders'],
            'pending_orders': pending_orders,
            'total_appointments': total_appointments,
            'total_doctors': s['total_doctors'],
            'avg_rating': pharmacy.avg_rating if pharmacy else 0,
            'review_count': pharmacy.review_count if pharmacy else 0,
            'total_chat_logs': total_chat_logs,
        }
        return jsonify({'success': True, 'stats': stats})
    except Exception as e:
        logging.error(f"Pharmacy stats error: {e}")
        return jsonify({'error': str(e)}), 500


# ─── Orders ─────────────────────────────────────────────────────────────────

@bp.route("/api/orders", methods=["GET"])
@require_pharmacy_admin
def list_orders():
    """List orders for this pharmacy"""
    try:
        status = request.args.get('status')
        limit = request.args.get('limit', 20, type=int)
        offset = request.args.get('offset', 0, type=int)

        query = Order.query.filter_by(pharmacy_id=g.pharmacy_id)
        if status:
            query = query.filter_by(status=status)

        total = query.count()
        orders = query.order_by(Order.created_at.desc()).offset(offset).limit(limit).all()

        order_list = []
        for order in orders:
            customer = User.query.get(order.user_id)
            items = [{
                'medicine_name': item.medicine.name,
                'quantity': item.qty,
                'price_each': item.price_each,
            } for item in order.items]

            order_list.append({
                'id': order.id,
                'customer_name': customer.name if customer else 'Unknown',
                'phone': order.phone,
                'address': order.address,
                'total_amount': order.total_amount,
                'status': order.status,
                'payment_method': order.payment_method,
                'payment_status': order.payment_status,
                'items': items,
                'created_at': order.created_at.isoformat(),
            })

        return jsonify({
            'success': True,
            'orders': order_list,
            'total': total,
        })

    except Exception as e:
        logging.error(f"List pharmacy orders error: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route("/api/orders/<int:order_id>/status", methods=["PUT"])
@require_pharmacy_admin
def update_order_status(order_id):
    """Update order status (pharmacy admin)"""
    try:
        order = Order.query.filter_by(
            id=order_id, pharmacy_id=g.pharmacy_id
        ).first()
        if not order:
            return jsonify({'error': 'Order not found'}), 404

        data = request.get_json()
        new_status = data.get('status')
        valid = ['pending', 'processing', 'out_for_delivery', 'delivered', 'cancelled']
        if new_status not in valid:
            return jsonify({'error': 'Invalid status'}), 400

        old_status = order.status
        order.status = new_status

        # Restore stock on cancellation
        if new_status == 'cancelled' and old_status != 'cancelled':
            for item in order.items:
                med = Medicine.query.get(item.medicine_id)
                if med:
                    med.stock_quantity += item.qty
                    if med.status == 'out_of_stock' and med.stock_quantity > 0:
                        med.status = 'in_stock'

        db.session.commit()
        return jsonify({'success': True, 'message': f'Order status updated to {new_status}'})

    except Exception as e:
        db.session.rollback()
        logging.error(f"Update pharmacy order error: {e}")
        return jsonify({'error': str(e)}), 500


# ─── Appointments ────────────────────────────────────────────────────────────

@bp.route("/api/appointments", methods=["GET"])
@require_pharmacy_admin
def list_appointments():
    """List appointments for doctors at this pharmacy"""
    try:
        status = request.args.get('status')
        limit = request.args.get('limit', 20, type=int)
        offset = request.args.get('offset', 0, type=int)

        query = Appointment.query.join(
            User, Appointment.doctor_id == User.id
        ).filter(User.pharmacy_id == g.pharmacy_id)

        if status:
            query = query.filter(Appointment.status == status)

        total = query.count()
        appointments = query.order_by(
            Appointment.created_at.desc()
        ).offset(offset).limit(limit).all()

        appt_list = []
        for a in appointments:
            patient = User.query.get(a.user_id)
            doctor = User.query.get(a.doctor_id)
            appt_list.append({
                'id': a.id,
                'patient_name': patient.name if patient else 'Unknown',
                'doctor_name': doctor.name if doctor else 'Unknown',
                'date': a.appointment_date.isoformat() if a.appointment_date else None,
                'starts_at': a.starts_at.isoformat() if a.starts_at else None,
                'status': a.status,
                'google_meet_link': a.google_meet_link,
                'symptoms': a.symptoms,
                'created_at': a.created_at.isoformat(),
            })

        return jsonify({
            'success': True,
            'appointments': appt_list,
            'total': total,
        })

    except Exception as e:
        logging.error(f"List pharmacy appointments error: {e}")
        return jsonify({'error': str(e)}), 500


# ─── Doctors ─────────────────────────────────────────────────────────────────

@bp.route("/api/doctors", methods=["GET"])
@require_pharmacy_admin
def list_doctors():
    """List doctors at this pharmacy"""
    try:
        doctors = User.query.filter_by(
            pharmacy_id=g.pharmacy_id, role='doctor'
        ).all()

        return jsonify({
            'success': True,
            'doctors': [{
                'id': d.id,
                'name': d.name,
                'email': d.email,
                'specialization': d.specialization,
                'qualification': d.qualification,
                'experience_years': d.experience_years,
                'phone': d.phone,
                'photo_path': d.photo_path,
            } for d in doctors]
        })

    except Exception as e:
        logging.error(f"List pharmacy doctors error: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route("/api/doctors", methods=["POST"])
@require_pharmacy_admin
def add_doctor():
    """Add a doctor to this pharmacy"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        required = ['name', 'email']
        missing = [f for f in required if not data.get(f)]
        if missing:
            return jsonify({'error': f'Missing: {", ".join(missing)}'}), 400

        # Check if email already exists
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'A user with this email already exists'}), 409

        doctor = User()
        doctor.name = data['name']
        doctor.email = data['email']
        doctor.role = 'doctor'
        doctor.pharmacy_id = g.pharmacy_id
        doctor.specialization = data.get('specialization', '')
        doctor.qualification = data.get('qualification', '')
        doctor.experience_years = data.get('experience_years')
        doctor.phone = data.get('phone', '')
        doctor.password_hash = phash(data.get('password', 'changeme123'))
        doctor.doctor_password_set = False

        db.session.add(doctor)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Doctor added successfully',
            'doctor': {'id': doctor.id, 'name': doctor.name}
        }), 201

    except Exception as e:
        db.session.rollback()
        logging.error(f"Add doctor error: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route("/api/doctors/<int:doctor_id>", methods=["PUT"])
@require_pharmacy_admin
def update_doctor(doctor_id):
    """Update a doctor's info"""
    try:
        doctor = User.query.filter_by(
            id=doctor_id, pharmacy_id=g.pharmacy_id, role='doctor'
        ).first()
        if not doctor:
            return jsonify({'error': 'Doctor not found'}), 404

        data = request.get_json()
        if data.get('name'):
            doctor.name = data['name']
        if data.get('specialization') is not None:
            doctor.specialization = data['specialization']
        if data.get('qualification') is not None:
            doctor.qualification = data['qualification']
        if data.get('experience_years') is not None:
            doctor.experience_years = data['experience_years']
        if data.get('phone') is not None:
            doctor.phone = data['phone']

        db.session.commit()
        return jsonify({'success': True, 'message': 'Doctor updated'})

    except Exception as e:
        db.session.rollback()
        logging.error(f"Update doctor error: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route("/api/doctors/<int:doctor_id>/photo", methods=["POST"])
@require_pharmacy_admin
def upload_doctor_photo(doctor_id):
    """Upload a photo for a doctor"""
    try:
        doctor = User.query.filter_by(
            id=doctor_id, pharmacy_id=g.pharmacy_id, role='doctor'
        ).first()
        if not doctor:
            return jsonify({'error': 'Doctor not found'}), 404

        if 'photo' not in request.files:
            return jsonify({'error': 'No photo file provided'}), 400

        file = request.files['photo']
        if not file or not file.filename:
            return jsonify({'error': 'No file selected'}), 400

        from werkzeug.utils import secure_filename
        pharmacy = Pharmacy.query.get(g.pharmacy_id)
        ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else 'jpg'
        ts = int(time.time())
        filename = secure_filename(f"doctor_{doctor.id}_{ts}.{ext}")
        gcs_path = f"pharmacies/{pharmacy.slug}/doctors/{filename}"
        doctor.photo_path = upload_to_gcs(file.stream, gcs_path)

        db.session.commit()
        return jsonify({
            'success': True,
            'photo_path': doctor.photo_path
        })

    except Exception as e:
        db.session.rollback()
        logging.error(f"Upload doctor photo error: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route("/api/doctors/<int:doctor_id>", methods=["DELETE"])
@require_pharmacy_admin
def remove_doctor(doctor_id):
    """Remove a doctor from this pharmacy"""
    try:
        doctor = User.query.filter_by(
            id=doctor_id, pharmacy_id=g.pharmacy_id, role='doctor'
        ).first()
        if not doctor:
            return jsonify({'error': 'Doctor not found'}), 404

        doctor.pharmacy_id = None  # Unlink, don't delete
        db.session.commit()
        return jsonify({'success': True, 'message': 'Doctor removed from pharmacy'})

    except Exception as e:
        db.session.rollback()
        logging.error(f"Remove doctor error: {e}")
        return jsonify({'error': str(e)}), 500


# ─── Reviews ────────────────────────────────────────────────────────────────

@bp.route("/api/reviews", methods=["GET"])
@require_pharmacy_admin
def list_reviews():
    """List reviews for this pharmacy"""
    try:
        reviews = PharmacyReview.query.filter_by(
            pharmacy_id=g.pharmacy_id
        ).order_by(PharmacyReview.created_at.desc()).all()

        return jsonify({
            'success': True,
            'reviews': [{
                'id': r.id,
                'rating': r.rating,
                'comment': r.comment,
                'owner_reply': r.owner_reply,
                'user_name': r.user.name if r.user else 'Anonymous',
                'created_at': r.created_at.isoformat() if r.created_at else None,
            } for r in reviews]
        })

    except Exception as e:
        logging.error(f"List reviews error: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route("/api/reviews/<int:review_id>/reply", methods=["POST"])
@require_pharmacy_admin
def reply_to_review(review_id):
    """Reply to a customer review"""
    try:
        review = PharmacyReview.query.filter_by(
            id=review_id, pharmacy_id=g.pharmacy_id
        ).first()
        if not review:
            return jsonify({'error': 'Review not found'}), 404

        data = request.get_json()
        reply = data.get('reply', '').strip()
        if not reply:
            return jsonify({'error': 'Reply text is required'}), 400

        review.owner_reply = reply
        db.session.commit()
        return jsonify({'success': True, 'message': 'Reply added'})

    except Exception as e:
        db.session.rollback()
        logging.error(f"Reply to review error: {e}")
        return jsonify({'error': str(e)}), 500


# ─── Profile Settings ───────────────────────────────────────────────────────

@bp.route("/api/profile", methods=["GET"])
@require_pharmacy_admin
def get_profile():
    """Get pharmacy profile info"""
    try:
        pharmacy = Pharmacy.query.get(g.pharmacy_id)
        if not pharmacy:
            return jsonify({'error': 'Pharmacy not found'}), 404

        return jsonify({
            'success': True,
            'pharmacy': pharmacy_to_dict(pharmacy),
            'themes': AVAILABLE_THEMES,
        })

    except Exception as e:
        logging.error(f"Get profile error: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route("/api/profile", methods=["PUT"])
@require_pharmacy_admin
def update_profile():
    """Update pharmacy profile"""
    try:
        pharmacy = Pharmacy.query.get(g.pharmacy_id)
        if not pharmacy:
            return jsonify({'error': 'Pharmacy not found'}), 404

        if request.content_type and 'multipart/form-data' in request.content_type:
            data = request.form.to_dict()
        else:
            data = request.get_json() or {}

        # Update fields
        updatable = ['name', 'owner_name', 'phone', 'address', 'city',
                      'province', 'operating_hours', 'theme_key']
        for field in updatable:
            if field in data:
                setattr(pharmacy, field, data[field])

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
        from werkzeug.utils import secure_filename
        if 'owner_photo' in request.files:
            file = request.files['owner_photo']
            if file and file.filename:
                ext = file.filename.rsplit('.', 1)[1].lower()
                ts = int(time.time())
                filename = secure_filename(f"owner_{pharmacy.slug}_{ts}.{ext}")
                gcs_path = f"pharmacies/{pharmacy.slug}/{filename}"
                pharmacy.owner_photo_path = upload_to_gcs(file.stream, gcs_path)

        if 'pharmacy_photo' in request.files:
            file = request.files['pharmacy_photo']
            if file and file.filename:
                ext = file.filename.rsplit('.', 1)[1].lower()
                ts = int(time.time())
                filename = secure_filename(f"pharmacy_{pharmacy.slug}_{ts}.{ext}")
                gcs_path = f"pharmacies/{pharmacy.slug}/{filename}"
                pharmacy.pharmacy_photo_path = upload_to_gcs(file.stream, gcs_path)

        db.session.commit()
        return jsonify({'success': True, 'message': 'Profile updated'})

    except Exception as e:
        db.session.rollback()
        logging.error(f"Update profile error: {e}")
        return jsonify({'error': str(e)}), 500


# ─── Chat Logs ──────────────────────────────────────────────────────────────

@bp.route("/api/chat-logs", methods=["GET"])
@require_pharmacy_admin
def list_chat_logs():
    """Get chat logs for this pharmacy"""
    try:
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)

        query = ChatLog.query.filter_by(pharmacy_id=g.pharmacy_id)
        total = query.count()
        logs = query.order_by(
            ChatLog.created_at.desc()
        ).offset(offset).limit(limit).all()

        return jsonify({
            'success': True,
            'logs': [{
                'id': l.id,
                'message': l.message,
                'response': l.response,
                'language': l.language,
                'flagged': l.flagged,
                'created_at': l.created_at.isoformat() if l.created_at else None,
            } for l in logs],
            'total': total,
        })

    except Exception as e:
        logging.error(f"Chat logs error: {e}")
        return jsonify({'error': str(e)}), 500
