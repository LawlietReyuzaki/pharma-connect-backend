"""
Pharmacy Network Service — Business logic for multi-pharmacy platform
"""

import os
import re
import math
import logging
from datetime import datetime
from app import db
from models import Pharmacy, PharmacyReview, Order, Appointment, User, ChatLog


def generate_slug(name):
    """Convert pharmacy name to URL-safe slug, ensure uniqueness"""
    slug = re.sub(r'[^a-zA-Z0-9\s-]', '', name.lower())
    slug = re.sub(r'[\s]+', '-', slug.strip())
    slug = re.sub(r'-+', '-', slug)

    # Check uniqueness
    base_slug = slug
    counter = 1
    while Pharmacy.query.filter_by(slug=slug).first():
        slug = f"{base_slug}-{counter}"
        counter += 1

    return slug


def haversine(lat1, lon1, lat2, lon2):
    """Calculate distance between two GPS coordinates in km"""
    R = 6371  # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) *
         math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    return R * 2 * math.asin(math.sqrt(a))


def get_nearby_pharmacies(lat, lng, limit=10):
    """Return approved pharmacies sorted by distance from lat/lng"""
    pharmacies = Pharmacy.query.filter_by(status='approved').all()
    with_distance = []
    for p in pharmacies:
        if p.latitude and p.longitude:
            dist = haversine(lat, lng, p.latitude, p.longitude)
            with_distance.append((p, round(dist, 1)))
    with_distance.sort(key=lambda x: x[1])
    return with_distance[:limit]


def approve_pharmacy(pharmacy_id, admin_id):
    """Approve a pending pharmacy registration"""
    pharmacy = Pharmacy.query.get(pharmacy_id)
    if not pharmacy:
        return None, "Pharmacy not found"
    if pharmacy.status != 'pending':
        return None, f"Pharmacy is already {pharmacy.status}"

    pharmacy.status = 'approved'
    pharmacy.approved_by = admin_id
    pharmacy.approved_at = datetime.utcnow()
    db.session.commit()
    return pharmacy, None


def reject_pharmacy(pharmacy_id, reason):
    """Reject a pending pharmacy registration"""
    pharmacy = Pharmacy.query.get(pharmacy_id)
    if not pharmacy:
        return None, "Pharmacy not found"
    if pharmacy.status != 'pending':
        return None, f"Pharmacy is already {pharmacy.status}"

    pharmacy.status = 'rejected'
    pharmacy.rejection_reason = reason
    db.session.commit()
    return pharmacy, None


def recalculate_rating(pharmacy_id):
    """Recalculate avg_rating and review_count for a pharmacy"""
    pharmacy = Pharmacy.query.get(pharmacy_id)
    if not pharmacy:
        return

    reviews = PharmacyReview.query.filter_by(pharmacy_id=pharmacy_id).all()
    if reviews:
        pharmacy.review_count = len(reviews)
        pharmacy.avg_rating = round(
            sum(r.rating for r in reviews) / len(reviews), 1
        )
    else:
        pharmacy.review_count = 0
        pharmacy.avg_rating = 0.0

    db.session.commit()


def get_pharmacy_stats(pharmacy_id):
    """Return dashboard stats for a specific pharmacy"""
    today = datetime.utcnow().date()

    orders_today = Order.query.filter(
        Order.pharmacy_id == pharmacy_id,
        db.func.date(Order.created_at) == today
    ).count()

    total_orders = Order.query.filter_by(pharmacy_id=pharmacy_id).count()

    pending_appointments = Appointment.query.join(
        User, Appointment.doctor_id == User.id
    ).filter(
        User.pharmacy_id == pharmacy_id,
        Appointment.status == 'pending'
    ).count()

    total_revenue = db.session.query(
        db.func.sum(Order.total_amount)
    ).filter(
        Order.pharmacy_id == pharmacy_id,
        Order.status == 'delivered'
    ).scalar() or 0

    new_reviews = PharmacyReview.query.filter(
        PharmacyReview.pharmacy_id == pharmacy_id,
        db.func.date(PharmacyReview.created_at) == today
    ).count()

    total_doctors = User.query.filter_by(
        pharmacy_id=pharmacy_id, role='doctor'
    ).count()

    return {
        'orders_today': orders_today,
        'total_orders': total_orders,
        'pending_appointments': pending_appointments,
        'total_revenue': total_revenue,
        'new_reviews': new_reviews,
        'total_doctors': total_doctors,
    }


def pharmacy_to_dict(pharmacy, distance=None):
    """Serialize a Pharmacy model to dict"""
    data = {
        'id': pharmacy.id,
        'name': pharmacy.name,
        'slug': pharmacy.slug,
        'owner_name': pharmacy.owner_name,
        'owner_photo_path': pharmacy.owner_photo_path,
        'pharmacy_photo_path': pharmacy.pharmacy_photo_path,
        'email': pharmacy.email,
        'phone': pharmacy.phone,
        'address': pharmacy.address,
        'city': pharmacy.city,
        'province': pharmacy.province,
        'license_number': pharmacy.license_number,
        'operating_hours': pharmacy.operating_hours,
        'theme_key': pharmacy.theme_key,
        'status': pharmacy.status,
        'avg_rating': pharmacy.avg_rating,
        'review_count': pharmacy.review_count,
        'created_at': pharmacy.created_at.isoformat() if pharmacy.created_at else None,
    }
    if distance is not None:
        data['distance_km'] = distance

    # Count doctors
    data['doctor_count'] = User.query.filter_by(
        pharmacy_id=pharmacy.id, role='doctor'
    ).count()

    return data
