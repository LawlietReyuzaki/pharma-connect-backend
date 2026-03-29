"""
Migration Script — Add multi-pharmacy network tables and columns.
Run once after updating models.py:
    python migrate_add_pharmacy.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Force SQLite for local development migration
os.environ['DATABASE_URL'] = 'sqlite:///red_dot_pharmacy.db'

from app import create_app, db
from sqlalchemy import text, inspect

app = create_app()

with app.app_context():
    # 1. Create all new tables (Pharmacy, PharmacyAdmin, PharmacyReview)
    print("Creating new tables...")
    db.create_all()
    print("  Done.")

    # 2. Add pharmacy_id column to existing tables if not present
    inspector = inspect(db.engine)

    alterations = {
        'users': 'pharmacy_id INTEGER REFERENCES pharmacies(id)',
        'orders': 'pharmacy_id INTEGER REFERENCES pharmacies(id)',
        'chat_logs': 'pharmacy_id INTEGER REFERENCES pharmacies(id)',
    }

    for table, col_def in alterations.items():
        col_name = col_def.split()[0]
        existing_cols = [c['name'] for c in inspector.get_columns(table)]
        if col_name in existing_cols:
            print(f"  {table}.{col_name} already exists — skipping.")
            continue
        try:
            with db.engine.connect() as conn:
                conn.execute(text(f'ALTER TABLE {table} ADD COLUMN {col_def}'))
                conn.commit()
            print(f"  Added {col_name} to {table}")
        except Exception as e:
            print(f"  Skipped {table}.{col_name}: {e}")

    # 3. Create uploads directory
    upload_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'static', 'uploads', 'pharmacies'
    )
    os.makedirs(upload_dir, exist_ok=True)
    print(f"  Upload directory ready: {upload_dir}")

    print("\nMigration complete!")
    print("Next step: Run 'python migrate_existing_data.py' to assign existing data to a pharmacy.")
