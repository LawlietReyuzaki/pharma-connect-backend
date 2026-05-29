"""
Load clinical_use.jsonl (plain text per medicine) into the medicines table.

Adds a `clinical_use` TEXT column via ALTER TABLE if missing, then writes the
text for each id.

Usage:
  python scripts/load_clinical_use.py
"""
import os
import sys
import json
import logging

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from dotenv import load_dotenv
load_dotenv(os.path.join(ROOT, ".env"))

JSONL_PATH = os.path.join(ROOT, "data", "clinical_use.jsonl")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("load_clinical_use")


def load():
    if not os.path.exists(JSONL_PATH):
        log.error(f"Not found: {JSONL_PATH}. Run generate_clinical_use.py first.")
        sys.exit(1)

    records = {}
    with open(JSONL_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                text = obj.get("text") or ""
                if text:
                    records[int(obj["id"])] = text
            except Exception as e:
                log.warning(f"Bad line: {e}")

    log.info(f"Loaded {len(records)} clinical_use texts from JSONL")

    from app import app, db
    from sqlalchemy import text as sql_text

    with app.app_context():
        with db.engine.connect() as conn:
            try:
                conn.execute(sql_text("ALTER TABLE medicines ADD COLUMN clinical_use TEXT"))
                conn.commit()
                log.info("Added clinical_use column to medicines table")
            except Exception:
                log.info("clinical_use column already exists (ok)")

        updated = 0
        for mid, txt in records.items():
            try:
                with db.engine.connect() as conn:
                    conn.execute(
                        sql_text("UPDATE medicines SET clinical_use = :cu WHERE id = :id"),
                        {"cu": txt, "id": mid},
                    )
                    conn.commit()
                updated += 1
            except Exception as e:
                log.warning(f"id={mid} update failed: {e}")

        log.info(f"Updated {updated} rows")


if __name__ == "__main__":
    load()
