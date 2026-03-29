#!/usr/bin/env python3
"""
Create or reset the super admin account.
Run once: python create_super_admin.py
"""
import hashlib
import sys

def phash(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def main():
    # Accept email/password from CLI or use defaults
    email    = sys.argv[1] if len(sys.argv) > 1 else 'admin@reddot.com'
    password = sys.argv[2] if len(sys.argv) > 2 else 'Admin@1234'
    name     = sys.argv[3] if len(sys.argv) > 3 else 'Super Admin'

    from app import app, db
    from models import Admin

    with app.app_context():
        db.create_all()  # Ensure all tables exist

        existing = Admin.query.filter_by(email=email).first()
        if existing:
            existing.password = phash(password)
            existing.name = name
            db.session.commit()
            print(f"[UPDATED] Admin password reset for: {email}")
        else:
            admin = Admin(name=name, email=email, password=phash(password))
            db.session.add(admin)
            db.session.commit()
            print(f"[CREATED] Super admin created: {email}")

        print(f"  Email   : {email}")
        print(f"  Password: {password}")
        print(f"  Login at: /admin  (use these credentials in the admin panel)")

if __name__ == '__main__':
    main()
