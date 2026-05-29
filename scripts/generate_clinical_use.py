"""
Generate clinical_use text for every medicine, READING FROM AND WRITING TO
the local SQLite DB directly.

For each medicine row where clinical_use IS NULL:
  - ask Gemini Flash for ONE short paragraph saying what the drug is FOR and NOT-FOR
  - UPDATE medicines SET clinical_use = <text> WHERE id = <id>

Resumable: only touches rows where clinical_use IS NULL.

Usage:
  python scripts/generate_clinical_use.py              # incremental
  python scripts/generate_clinical_use.py --rebuild    # wipe all clinical_use first
  python scripts/generate_clinical_use.py --limit 50   # only do 50 (for testing)
"""
import os
import sys
import json
import time
import logging
import argparse
import sqlite3

try:
    from tqdm import tqdm
except ImportError:
    print("Installing tqdm...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "tqdm"])
    from tqdm import tqdm

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

DB_PATH = os.path.join(ROOT, "instance", "red_dot_pharmacy.db")
BATCH_SIZE = 15
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("generate_clinical_use")


BATCH_PROMPT = """\
You are a clinical pharmacology expert. For each medicine below, write ONE short paragraph (60-100 words) saying exactly what the medicine is used FOR and what it is NOT used for. Base this strictly on the active ingredient(s) — do not invent uses.

Structure each paragraph as:
1) Drug class (1 phrase).
2) Main indications and what symptoms patients take it for — include common synonyms a patient might say (e.g. "high blood pressure", "BP", "hypertension").
3) Then a sentence beginning "NOT used for" listing 5-8 unrelated conditions/symptoms a user might wrongly query.

Return a JSON array, one object per medicine, in the same order, with fields:
  "id": integer (copy exactly)
  "text": string (the paragraph)

MEDICINES:
{batch_block}

Respond ONLY with a JSON array. No markdown, no commentary."""


def ensure_column(con):
    cur = con.cursor()
    cur.execute("PRAGMA table_info(medicines)")
    cols = {r[1] for r in cur.fetchall()}
    if "clinical_use" not in cols:
        cur.execute("ALTER TABLE medicines ADD COLUMN clinical_use TEXT")
        con.commit()
        log.info("Added clinical_use column to medicines table")
    else:
        log.info("clinical_use column already exists")


def fetch_pending(con, limit=None):
    cur = con.cursor()
    q = "SELECT id, name, chemical, category, substr(coalesce(description,''),1,200) FROM medicines WHERE clinical_use IS NULL OR clinical_use = '' ORDER BY id"
    if limit:
        q += f" LIMIT {int(limit)}"
    cur.execute(q)
    rows = cur.fetchall()
    return [
        {"id": r[0], "name": r[1] or "", "chemical": r[2] or "unknown",
         "category": r[3] or "", "description": r[4] or ""}
        for r in rows
    ]


def build_batch_block(batch):
    lines = []
    for m in batch:
        desc = m["description"].replace("\n", " ")
        lines.append(
            f'id={m["id"]} | name="{m["name"]}" | chemical="{m["chemical"]}" '
            f'| category="{m["category"]}" | desc="{desc}"'
        )
    return "\n".join(lines)


def call_gemini(client, batch, retry=3):
    from google.genai import types as genai_types
    prompt = BATCH_PROMPT.format(batch_block=build_batch_block(batch))
    schema = {
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "id": {"type": "integer"},
                "text": {"type": "string"},
            },
            "required": ["id", "text"],
        },
    }
    for attempt in range(retry):
        try:
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
                config=genai_types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=schema,
                    max_output_tokens=8192,
                    temperature=0.1,
                ),
            )
            raw = (response.text or "").strip()
            if not raw:
                raise ValueError("empty")
            parsed = json.loads(raw)
            if not isinstance(parsed, list):
                raise ValueError(f"got {type(parsed)}")
            return parsed
        except Exception as e:
            wait = 2 ** attempt
            log.warning(f"Gemini call failed (attempt {attempt+1}/{retry}): {e}. Retry in {wait}s")
            time.sleep(wait)
    raise RuntimeError(f"failed after {retry} for batch starting id={batch[0]['id']}")


def generate(rebuild=False, limit=None):
    if not os.path.exists(DB_PATH):
        log.error(f"DB not found: {DB_PATH}")
        sys.exit(1)

    con = sqlite3.connect(DB_PATH)
    ensure_column(con)

    if rebuild:
        con.execute("UPDATE medicines SET clinical_use = NULL")
        con.commit()
        log.info("Wiped clinical_use for all rows")

    todo = fetch_pending(con, limit=limit)
    total = con.execute("SELECT COUNT(*) FROM medicines").fetchone()[0]
    done = total - len(todo) if not limit else 0
    log.info(f"DB has {total} medicines. To process: {len(todo)}. Already filled: {done}")

    if not todo:
        log.info("Nothing to do.")
        con.close()
        return

    try:
        from google import genai
        from dotenv import load_dotenv
        load_dotenv(os.path.join(ROOT, ".env"))
        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY not set in environment / .env")
        client = genai.Client(api_key=api_key)
        log.info(f"Gemini client ready (model={GEMINI_MODEL})")
    except Exception as e:
        log.error(f"Init failed: {e}")
        sys.exit(1)

    written = 0
    pbar = tqdm(total=len(todo), desc="clinical_use", unit="med", ncols=100)

    for batch_start in range(0, len(todo), BATCH_SIZE):
        batch = todo[batch_start: batch_start + BATCH_SIZE]
        ids = [m["id"] for m in batch]

        try:
            records = call_gemini(client, batch)
        except RuntimeError as e:
            log.error(f"Skip batch ids {ids[0]}..{ids[-1]}: {e}")
            pbar.update(len(batch))
            continue

        rec_map = {}
        for rec in records:
            try:
                rec_map[int(rec["id"])] = rec.get("text", "")
            except Exception:
                pass

        cur = con.cursor()
        for m in batch:
            mid = m["id"]
            text = rec_map.get(mid) or f"{m['name']} contains {m['chemical']}. Consult a pharmacist."
            cur.execute("UPDATE medicines SET clinical_use = ? WHERE id = ?", (text, mid))
            written += 1
        con.commit()
        pbar.update(len(batch))
        pbar.set_postfix_str(f"ids {ids[0]}..{ids[-1]}")
        time.sleep(0.2)

    pbar.close()

    con.close()
    log.info(f"Done. Wrote {written} new rows this run.")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--rebuild", action="store_true")
    p.add_argument("--limit", type=int, default=None)
    args = p.parse_args()
    generate(rebuild=args.rebuild, limit=args.limit)


if __name__ == "__main__":
    main()
