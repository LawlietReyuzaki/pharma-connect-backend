"""
Public-facing pharmacy routes — discovery, profiles, reviews
"""

from flask import Blueprint, request, jsonify, render_template
from models import Pharmacy, PharmacyReview, User, Order, Appointment
from services.pharmacy_service import (
    get_nearby_pharmacies, pharmacy_to_dict, recalculate_rating
)
from services.auth import get_current_user
from app import db
import logging

bp = Blueprint("pharmacy", __name__)


# ─── Template Routes ────────────────────────────────────────────────────────

@bp.route("/<slug>")
def pharmacy_profile(slug):
    """Render a pharmacy's branded profile page"""
    pharmacy = Pharmacy.query.filter_by(slug=slug, status='approved').first_or_404()
    doctors = User.query.filter_by(pharmacy_id=pharmacy.id, role='doctor').all()
    return render_template(
        "pharmacy_profile.html",
        pharmacy=pharmacy,
        doctors=doctors
    )


# ─── API Routes ─────────────────────────────────────────────────────────────

@bp.route("/api/list", methods=["GET"])
def list_pharmacies():
    """List approved pharmacies with search, filter, pagination"""
    try:
        search = request.args.get('search', '').strip()
        city = request.args.get('city', '').strip()
        min_rating = request.args.get('min_rating', type=float)
        specialization = request.args.get('specialization', '').strip()
        limit = request.args.get('limit', 20, type=int)
        offset = request.args.get('offset', 0, type=int)

        query = Pharmacy.query.filter_by(status='approved')

        if search:
            query = query.filter(
                db.or_(
                    Pharmacy.name.ilike(f'%{search}%'),
                    Pharmacy.city.ilike(f'%{search}%'),
                    Pharmacy.address.ilike(f'%{search}%')
                )
            )

        if city:
            query = query.filter(Pharmacy.city.ilike(f'%{city}%'))

        if min_rating:
            query = query.filter(Pharmacy.avg_rating >= min_rating)

        total = query.count()

        # If specialization filter, join with doctors
        if specialization:
            pharmacy_ids = db.session.query(User.pharmacy_id).filter(
                User.role == 'doctor',
                User.specialization.ilike(f'%{specialization}%')
            ).distinct().subquery()
            query = query.filter(Pharmacy.id.in_(pharmacy_ids))
            total = query.count()

        pharmacies = query.order_by(
            Pharmacy.avg_rating.desc()
        ).offset(offset).limit(limit).all()

        return jsonify({
            'success': True,
            'pharmacies': [pharmacy_to_dict(p) for p in pharmacies],
            'total': total,
            'offset': offset,
            'limit': limit,
        })

    except Exception as e:
        logging.error(f"List pharmacies error: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route("/api/nearby", methods=["GET"])
def nearby_pharmacies():
    """Get pharmacies sorted by distance from user's location"""
    try:
        lat = request.args.get('lat', type=float)
        lng = request.args.get('lng', type=float)
        limit = request.args.get('limit', 10, type=int)

        if lat is None or lng is None:
            return jsonify({'error': 'lat and lng are required'}), 400

        results = get_nearby_pharmacies(lat, lng, limit)

        return jsonify({
            'success': True,
            'pharmacies': [
                pharmacy_to_dict(p, distance=dist) for p, dist in results
            ]
        })

    except Exception as e:
        logging.error(f"Nearby pharmacies error: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route("/api/<slug>", methods=["GET"])
def get_pharmacy(slug):
    """Get single pharmacy details by slug"""
    try:
        pharmacy = Pharmacy.query.filter_by(slug=slug, status='approved').first()
        if not pharmacy:
            return jsonify({'error': 'Pharmacy not found'}), 404

        data = pharmacy_to_dict(pharmacy)

        # Include doctors
        doctors = User.query.filter_by(
            pharmacy_id=pharmacy.id, role='doctor'
        ).all()
        data['doctors'] = [{
            'id': d.id,
            'name': d.name,
            'specialization': d.specialization,
            'qualification': d.qualification,
            'experience_years': d.experience_years,
        } for d in doctors]

        return jsonify({'success': True, 'pharmacy': data})

    except Exception as e:
        logging.error(f"Get pharmacy error: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route("/api/<slug>/doctors", methods=["GET"])
def get_pharmacy_doctors(slug):
    """Get doctors for a pharmacy"""
    try:
        pharmacy = Pharmacy.query.filter_by(slug=slug, status='approved').first()
        if not pharmacy:
            return jsonify({'error': 'Pharmacy not found'}), 404

        doctors = User.query.filter_by(
            pharmacy_id=pharmacy.id, role='doctor'
        ).all()

        return jsonify({
            'success': True,
            'doctors': [{
                'id': d.id,
                'name': d.name,
                'specialization': d.specialization,
                'qualification': d.qualification,
                'experience_years': d.experience_years,
            } for d in doctors]
        })

    except Exception as e:
        logging.error(f"Get pharmacy doctors error: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route("/api/<slug>/reviews", methods=["GET"])
def get_pharmacy_reviews(slug):
    """Get paginated reviews for a pharmacy"""
    try:
        pharmacy = Pharmacy.query.filter_by(slug=slug, status='approved').first()
        if not pharmacy:
            return jsonify({'error': 'Pharmacy not found'}), 404

        limit = request.args.get('limit', 20, type=int)
        offset = request.args.get('offset', 0, type=int)

        query = PharmacyReview.query.filter_by(pharmacy_id=pharmacy.id)
        total = query.count()
        reviews = query.order_by(
            PharmacyReview.created_at.desc()
        ).offset(offset).limit(limit).all()

        return jsonify({
            'success': True,
            'reviews': [{
                'id': r.id,
                'rating': r.rating,
                'comment': r.comment,
                'owner_reply': r.owner_reply,
                'user_name': r.user.name if r.user else 'Anonymous',
                'created_at': r.created_at.isoformat() if r.created_at else None,
            } for r in reviews],
            'total': total,
            'avg_rating': pharmacy.avg_rating,
            'review_count': pharmacy.review_count,
        })

    except Exception as e:
        logging.error(f"Get reviews error: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route("/api/<slug>/reviews", methods=["POST"])
def submit_review(slug):
    """Submit a review for a pharmacy (requires login + completed order/appointment)"""
    try:
        current_user = get_current_user()
        if not current_user:
            return jsonify({'error': 'Login required to leave a review'}), 401

        pharmacy = Pharmacy.query.filter_by(slug=slug, status='approved').first()
        if not pharmacy:
            return jsonify({'error': 'Pharmacy not found'}), 404

        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        rating = data.get('rating')
        if not rating or not (1 <= int(rating) <= 5):
            return jsonify({'error': 'Rating must be between 1 and 5'}), 400

        # Check that user has a completed order or appointment at this pharmacy
        has_order = Order.query.filter_by(
            user_id=current_user.id,
            pharmacy_id=pharmacy.id,
            status='delivered'
        ).first()

        has_appointment = Appointment.query.join(
            User, Appointment.doctor_id == User.id
        ).filter(
            Appointment.user_id == current_user.id,
            User.pharmacy_id == pharmacy.id,
            Appointment.status == 'completed'
        ).first()

        if not has_order and not has_appointment:
            return jsonify({
                'error': 'You must have a completed order or appointment to leave a review'
            }), 403

        # Check for duplicate review on same source
        source_type = data.get('source_type', 'order')
        source_id = data.get('source_id')
        if source_id:
            existing = PharmacyReview.query.filter_by(
                pharmacy_id=pharmacy.id,
                user_id=current_user.id,
                source_type=source_type,
                source_id=source_id
            ).first()
            if existing:
                return jsonify({'error': 'You have already reviewed this transaction'}), 409

        review = PharmacyReview()
        review.pharmacy_id = pharmacy.id
        review.user_id = current_user.id
        review.rating = int(rating)
        review.comment = data.get('comment', '')[:500]
        review.source_type = source_type
        review.source_id = source_id
        db.session.add(review)
        db.session.commit()

        # Recalculate pharmacy rating
        recalculate_rating(pharmacy.id)

        return jsonify({
            'success': True,
            'message': 'Review submitted successfully',
            'review': {
                'id': review.id,
                'rating': review.rating,
                'comment': review.comment,
            }
        }), 201

    except Exception as e:
        db.session.rollback()
        logging.error(f"Submit review error: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route("/api/cities", methods=["GET"])
def get_cities():
    """Get list of cities with approved pharmacies"""
    try:
        cities = db.session.query(
            Pharmacy.city, db.func.count(Pharmacy.id)
        ).filter(
            Pharmacy.status == 'approved',
            Pharmacy.city.isnot(None)
        ).group_by(Pharmacy.city).all()

        return jsonify({
            'success': True,
            'cities': [{'name': c[0], 'count': c[1]} for c in cities if c[0]]
        })

    except Exception as e:
        logging.error(f"Get cities error: {e}")
        return jsonify({'error': str(e)}), 500
