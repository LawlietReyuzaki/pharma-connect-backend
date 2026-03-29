"""
Migrate all data from SQLite -> PostgreSQL (Docker)
Run AFTER: docker-compose up -d
Usage: python migrate_sqlite_to_postgres.py
"""
import sqlite3
import os
import sys
import time

SQLITE_PATH = "red_dot_pharmacy.db"
PG_URL = "postgresql://reddot_user:reddot_pass@127.0.0.1:5434/red_dot_pharmacy"

def wait_for_postgres(engine, retries=10):
    from sqlalchemy import text
    for i in range(retries):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print("[OK] PostgreSQL is ready")
            return True
        except Exception as e:
            print(f"[wait] Waiting for PostgreSQL... ({i+1}/{retries})")
            time.sleep(2)
    return False

def migrate():
    # Check SQLite exists
    if not os.path.exists(SQLITE_PATH):
        print(f"[ERR] SQLite file not found: {SQLITE_PATH}")
        sys.exit(1)

    print("=" * 60)
    print("  Red Dot Pharmacy - SQLite to PostgreSQL Migration")
    print("=" * 60)

    # Set DATABASE_URL so Flask uses Postgres
    os.environ["DATABASE_URL"] = PG_URL

    from sqlalchemy import create_engine, text
    from app import create_app, db

    app = create_app()

    # Override with postgres URL
    app.config["SQLALCHEMY_DATABASE_URI"] = PG_URL

    pg_engine = create_engine(PG_URL)

    if not wait_for_postgres(pg_engine):
        print("[ERR] PostgreSQL not reachable. Is Docker running? (docker-compose up -d)")
        sys.exit(1)

    # Create all tables in Postgres
    print("\n[>>] Creating tables in PostgreSQL...")
    with app.app_context():
        db.create_all()
    print("[OK] Tables created")

    # Connect to SQLite
    sqlite_conn = sqlite3.connect(SQLITE_PATH)
    sqlite_conn.row_factory = sqlite3.Row
    cursor = sqlite_conn.cursor()

    # Get all table names from SQLite
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    tables = [row[0] for row in cursor.fetchall()]
    print(f"\n[list] Tables to migrate: {tables}\n")

    # Migrate table by table in FK-safe order
    ordered = [
        "admins", "users", "medicines", "payment_methods", "banking_details",
        "pharmacies", "pharmacy_admins", "doctor_availability", "time_slots",
        "appointments", "orders", "order_items", "chat_logs",
        "pharmacy_reviews",
    ]
    # Add any tables not in ordered list at the end
    remaining = [t for t in tables if t not in ordered]
    migrate_order = [t for t in ordered if t in tables] + remaining

    with pg_engine.connect() as pg_conn:
        # Disable FK checks during migration
        pg_conn.execute(text("SET session_replication_role = 'replica'"))

        for table in migrate_order:
            try:
                # Get rows from SQLite
                cursor.execute(f"SELECT * FROM {table}")
                rows = cursor.fetchall()
                if not rows:
                    print(f"  [skip]  {table}: empty, skipping")
                    continue

                cols = [desc[0] for desc in cursor.description]
                col_list = ", ".join(f'"{c}"' for c in cols)
                placeholders = ", ".join(f":{c}" for c in cols)

                # Clear existing data in postgres table
                pg_conn.execute(text(f'DELETE FROM "{table}"'))

                # Insert rows
                row_dicts = [dict(zip(cols, row)) for row in rows]
                pg_conn.execute(
                    text(f'INSERT INTO "{table}" ({col_list}) VALUES ({placeholders})'),
                    row_dicts
                )
                pg_conn.commit()
                print(f"  [OK] {table}: {len(rows)} rows migrated")

            except Exception as e:
                pg_conn.rollback()
                print(f"  ⚠️  {table}: {e}")

        # Re-enable FK checks
        pg_conn.execute(text("SET session_replication_role = 'origin'"))

        # Reset sequences so auto-increment works correctly
        print("\n[reset] Resetting sequences...")
        seq_tables = [
            ("admins", "admin_id"), ("users", "id"), ("medicines", "id"),
            ("pharmacies", "id"), ("pharmacy_admins", "id"),
            ("orders", "id"), ("order_items", "id"), ("appointments", "id"),
            ("chat_logs", "id"), ("pharmacy_reviews", "id"),
        ]
        for table, pk in seq_tables:
            if table in tables:
                try:
                    pg_conn.execute(text(
                        f"SELECT setval(pg_get_serial_sequence('{table}', '{pk}'), "
                        f"COALESCE((SELECT MAX({pk}) FROM \"{table}\"), 1))"
                    ))
                    pg_conn.commit()
                except Exception as e:
                    print(f"  ⚠️  Sequence reset for {table}: {e}")

    sqlite_conn.close()

    print("\n" + "=" * 60)
    print("[OK] MIGRATION COMPLETE!")
    print("=" * 60)
    print(f"\n[note] Now update your .env:")
    print(f"   DATABASE_URL=postgresql://reddot_user:reddot2025@127.0.0.1:5433/red_dot_pharmacy")
    print(f"\n[run] Then restart Flask: python main.py")

if __name__ == "__main__":
    migrate()
