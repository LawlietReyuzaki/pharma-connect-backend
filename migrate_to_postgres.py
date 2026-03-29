"""
SQLite -> PostgreSQL Migration Script
Red Dot Pharmacy

Run from project root (Anaconda Prompt):
    cd "C:\\Users\\Hassan\\Desktop\\red  dot\\UrduBotBooker"
    python migrate_to_postgres.py
"""

import sqlite3
import psycopg2
from psycopg2.extras import execute_batch
import sys
import os

# ── Configuration ──────────────────────────────────────────────────────────────
SQLITE_PATH = "red_dot_pharmacy.db"
PG_DSN      = "postgresql://reddot_user:reddot_pass@127.0.0.1:5434/red_dot_pharmacy"
BATCH_SIZE  = 500

# ── Table order: parents before children (FK-safe) ────────────────────────────
#
# Dependency map (from models.py):
#   admins              → no FK
#   users               → no FK
#   medicines           → no FK
#   payment_methods     → no FK
#   banking_details     → no FK
#   doctor_availability → FK → users
#   time_slots          → FK → users
#   appointments        → FK → users, time_slots
#   orders              → FK → users, admins
#   order_items         → FK → orders, medicines
#   chat_logs           → FK → users (nullable)
#
TABLES = [
    # (table_name,           primary_key_column)
    ("admins",               "admin_id"),
    ("users",                "id"),
    ("medicines",            "id"),
    ("payment_methods",      "id"),
    ("banking_details",      "id"),
    ("doctor_availability",  "id"),
    ("time_slots",           "id"),
    ("appointments",         "id"),
    ("orders",               "id"),
    ("order_items",          "id"),
    ("chat_logs",            "id"),
]

# ── Boolean columns per table (SQLite stores 0/1; PostgreSQL needs True/False) ─
BOOL_COLS = {
    "users":               ["doctor_password_set"],
    "doctor_availability": ["is_active"],
    "time_slots":          ["is_booked"],
    "payment_methods":     ["is_active", "requires_receipt"],
    "chat_logs":           ["flagged"],
}


def connect_sqlite():
    if not os.path.exists(SQLITE_PATH):
        print(f"\nERROR: SQLite file not found: '{SQLITE_PATH}'")
        print("Make sure you are running this script from the project root:")
        print('  cd "C:\\Users\\Hassan\\Desktop\\red  dot\\UrduBotBooker"')
        sys.exit(1)
    conn = sqlite3.connect(SQLITE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def connect_pg():
    try:
        return psycopg2.connect(PG_DSN)
    except Exception as e:
        print(f"\nERROR: Cannot connect to PostgreSQL: {e}")
        print("Check that the Docker container is running:")
        print("  docker ps --filter name=reddot-pharmacy-postgres")
        sys.exit(1)


def check_pg_tables(pg_conn):
    """Verify all 11 tables exist in PostgreSQL before migrating."""
    cur = pg_conn.cursor()
    cur.execute("SELECT tablename FROM pg_tables WHERE schemaname='public'")
    existing = {row[0] for row in cur.fetchall()}
    expected = {t[0] for t in TABLES}
    missing  = expected - existing
    if missing:
        print(f"\nERROR: Missing tables in PostgreSQL: {missing}")
        print("Run db.create_all() first:")
        print('  python -c "import os; os.environ[\'DATABASE_URL\']=\'postgresql://reddot_user:reddot_pass@127.0.0.1:5434/red_dot_pharmacy\'; from app import app,db; import models; app.app_context().push(); db.create_all()"')
        sys.exit(1)


def convert_row(table, columns, row):
    """Convert a SQLite row into a list safe for PostgreSQL insertion."""
    bool_cols = BOOL_COLS.get(table, [])
    values = []
    for col, val in zip(columns, row):
        if col in bool_cols:
            # SQLite 0/1/None -> PostgreSQL False/True/None
            values.append(None if val is None else bool(val))
        else:
            values.append(val)
    return values


def migrate_table(sqlite_conn, pg_conn, table, pk_col):
    """Copy all rows from one SQLite table into PostgreSQL."""
    sqlite_cur = sqlite_conn.cursor()
    pg_cur     = pg_conn.cursor()

    # Check table exists in SQLite (some may not exist in older DB versions)
    try:
        sqlite_cur.execute(f"SELECT * FROM {table} LIMIT 0")
    except sqlite3.OperationalError:
        print(f"  {table:28s}  SKIPPED (table not in SQLite)")
        return 0

    sqlite_cur.execute(f"SELECT * FROM {table}")
    rows = sqlite_cur.fetchall()

    if not rows:
        print(f"  {table:28s}  0 rows (empty)")
        return 0

    columns     = [desc[0] for desc in sqlite_cur.description]
    col_sql     = ", ".join(f'"{c}"' for c in columns)
    placeholders = ", ".join(["%s"] * len(columns))
    sql = f'INSERT INTO "{table}" ({col_sql}) VALUES ({placeholders}) ON CONFLICT DO NOTHING'

    converted = [convert_row(table, columns, row) for row in rows]

    try:
        execute_batch(pg_cur, sql, converted, page_size=BATCH_SIZE)
        pg_conn.commit()
    except Exception as e:
        pg_conn.rollback()
        print(f"\n  ERROR in '{table}': {e}")
        print("  This table was rolled back. Fix the issue and re-run.")
        raise

    print(f"  {table:28s}  {len(rows):>6} rows  OK")
    return len(rows)


def reset_sequences(pg_conn):
    """
    Reset all PostgreSQL SERIAL sequences to MAX(pk)+1.
    CRITICAL: Without this, the first INSERT after migration will
    fail with 'duplicate key value violates unique constraint'
    because sequences still start from 1.
    """
    print("\n[3/4] Resetting sequences...")
    pg_cur = pg_conn.cursor()

    for table, pk_col in TABLES:
        try:
            pg_cur.execute(f"""
                SELECT setval(
                    pg_get_serial_sequence('{table}', '{pk_col}'),
                    COALESCE((SELECT MAX("{pk_col}") FROM "{table}"), 1),
                    true
                )
            """)
            pg_conn.commit()

            pg_cur.execute(f'SELECT MAX("{pk_col}") FROM "{table}"')
            max_id = pg_cur.fetchone()[0] or 0
            print(f"  {table:28s}  next id -> {max_id + 1}")
        except Exception as e:
            print(f"  WARNING: Could not reset sequence for {table}: {e}")

    print("  All sequences reset.")


def verify(sqlite_conn, pg_conn):
    """Compare row counts between SQLite and PostgreSQL for every table."""
    print("\n[4/4] Verifying row counts...")
    sqlite_cur = sqlite_conn.cursor()
    pg_cur     = pg_conn.cursor()

    all_ok = True
    print(f"\n  {'Table':<28}  {'SQLite':>8}  {'PostgreSQL':>10}  Status")
    print(f"  {'-'*28}  {'-'*8}  {'-'*10}  ------")

    for table, _ in TABLES:
        try:
            sqlite_cur.execute(f"SELECT COUNT(*) FROM {table}")
            sqlite_count = sqlite_cur.fetchone()[0]
        except sqlite3.OperationalError:
            sqlite_count = 0

        pg_cur.execute(f'SELECT COUNT(*) FROM "{table}"')
        pg_count = pg_cur.fetchone()[0]

        ok = sqlite_count == pg_count
        status = "OK" if ok else "MISMATCH <---"
        if not ok:
            all_ok = False

        print(f"  {table:<28}  {sqlite_count:>8}  {pg_count:>10}  {status}")

    return all_ok


def main():
    print("=" * 62)
    print("   Red Dot Pharmacy — SQLite -> PostgreSQL Migration")
    print("=" * 62)
    print(f"\n  Source : {SQLITE_PATH}")
    print(f"  Target : {PG_DSN}\n")

    print("[1/4] Connecting...")
    sqlite_conn = connect_sqlite()
    pg_conn     = connect_pg()
    check_pg_tables(pg_conn)
    print("  Both databases connected. All 11 tables found in PostgreSQL.\n")

    print("[2/4] Migrating tables...")
    total = 0
    for table, pk_col in TABLES:
        total += migrate_table(sqlite_conn, pg_conn, table, pk_col)

    print(f"\n  Total rows migrated: {total}")

    reset_sequences(pg_conn)

    all_ok = verify(sqlite_conn, pg_conn)

    sqlite_conn.close()
    pg_conn.close()

    print("\n" + "=" * 62)
    if all_ok:
        print("  MIGRATION COMPLETE - All row counts match")
    else:
        print("  MIGRATION DONE WITH WARNINGS - Check mismatches above")
    print("=" * 62)


if __name__ == "__main__":
    main()
