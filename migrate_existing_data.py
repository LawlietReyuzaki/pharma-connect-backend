"""
Migration Script — Assign existing data to the original Red Dot Pharmacy.
Run AFTER migrate_add_pharmacy.py:
    python migrate_existing_data.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Force SQLite for local development migration
os.environ['DATABASE_URL'] = 'sqlite:///red_dot_pharmacy.db'

from app import create_app, db
from models import Pharmacy, PharmacyAdmin, User, Order, ChatLog
from services.auth import phash
from datetime import datetime

app = create_app()

with app.app_context():
    # Check if already migrated
    existing = Pharmacy.query.filter_by(slug='red-dot').first()
    if existing:
        print(f"Red Dot Pharmacy already exists (id={existing.id}). Skipping creation.")
        pharmacy_id = existing.id
    else:
        # Create the original pharmacy
        reddot = Pharmacy()
        reddot.name = 'Red Dot Pharmacy'
        reddot.slug = 'red-dot'
        reddot.owner_name = 'Red Dot Pharmacy'
        reddot.email = 'info@reddotpharmacy.com'
        reddot.phone = '051-5111222'
        reddot.address = 'Shop #69 Ground Floor Silver City Plaza, G11 Markaz'
        reddot.city = 'Islamabad'
        reddot.province = 'ICT'
        reddot.latitude = 33.6844
        reddot.longitude = 72.8282
        reddot.theme_key = 'theme-crimson'
        reddot.status = 'approved'
        reddot.approved_at = datetime.utcnow()
        db.session.add(reddot)
        db.session.flush()  # Get ID
        pharmacy_id = reddot.id
        print(f"Created Red Dot Pharmacy (id={pharmacy_id})")

    # Create a pharmacy admin if none exists
    existing_admin = PharmacyAdmin.query.filter_by(pharmacy_id=pharmacy_id).first()
    if not existing_admin:
        admin = PharmacyAdmin()
        admin.pharmacy_id = pharmacy_id
        admin.name = 'Red Dot Admin'
        admin.email = 'admin@reddotpharmacy.com'
        admin.password_hash = phash('reddot2025')
        db.session.add(admin)
        print("Created pharmacy admin: admin@reddotpharmacy.com / reddot2025")
    else:
        print(f"Pharmacy admin already exists (id={existing_admin.id})")

    # Assign all existing users to this pharmacy
    unassigned_users = User.query.filter_by(pharmacy_id=None).count()
    if unassigned_users > 0:
        User.query.filter_by(pharmacy_id=None).update({'pharmacy_id': pharmacy_id})
        print(f"Assigned {unassigned_users} users to Red Dot Pharmacy")
    else:
        print("All users already assigned")

    # Assign all existing orders
    unassigned_orders = Order.query.filter_by(pharmacy_id=None).count()
    if unassigned_orders > 0:
        Order.query.filter_by(pharmacy_id=None).update({'pharmacy_id': pharmacy_id})
        print(f"Assigned {unassigned_orders} orders to Red Dot Pharmacy")
    else:
        print("All orders already assigned")

    # Assign all existing chat logs
    unassigned_chats = ChatLog.query.filter_by(pharmacy_id=None).count()
    if unassigned_chats > 0:
        ChatLog.query.filter_by(pharmacy_id=None).update({'pharmacy_id': pharmacy_id})
        print(f"Assigned {unassigned_chats} chat logs to Red Dot Pharmacy")
    else:
        print("All chat logs already assigned")

    db.session.commit()
    print("\nData migration complete!")
    print(f"  Red Dot Pharmacy: /pharmacy/red-dot")
    print(f"  Pharmacy Admin login: /pharmacy-admin")
    print(f"    Email: admin@reddotpharmacy.com")
    print(f"    Password: reddot2025")
