#!/usr/bin/env python3
"""
Reset a pharmacy admin's password.

Usage:
  python reset_pharmacy_password.py <email> <new_password>

Examples:
  python reset_pharmacy_password.py admin@reddotpharmacy.com Admin@1234
  python reset_pharmacy_password.py email.hassan.cs@gmail.com Admin@1234
  python reset_pharmacy_password.py bagankhan159@gmail.com Admin@1234
  python reset_pharmacy_password.py testpharmacy999@test.com Admin@1234
"""
import sys
import hashlib

def phash(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def main():
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)

    email    = sys.argv[1].strip()
    new_pass = sys.argv[2].strip()

    from app import app, db
    from models import PharmacyAdmin, Pharmacy

    with app.app_context():
        admin = PharmacyAdmin.query.filter_by(email=email).first()
        if not admin:
            print(f"ERROR: No pharmacy admin found with email: {email}")
            sys.exit(1)

        pharmacy = Pharmacy.query.get(admin.pharmacy_id)
        admin.password_hash = phash(new_pass)
        db.session.commit()

        print(f"Password reset successfully!")
        print(f"  Pharmacy : {pharmacy.name if pharmacy else 'N/A'}")
        print(f"  Email    : {email}")
        print(f"  Password : {new_pass}")
        print(f"  Status   : {pharmacy.status if pharmacy else 'N/A'}")
        if pharmacy and pharmacy.status != 'approved':
            print(f"\n  WARNING: This pharmacy is '{pharmacy.status}' — it must be approved by the super admin before login works.")

if __name__ == '__main__':
    main()
