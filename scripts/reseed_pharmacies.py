"""
One-shot: wipe all pharmacies and re-seed from local pharmacy/owner image folders.
Uploads owner + pharmacy thumbnails to GCS with timestamped filenames.
Prints generated credentials to stdout.
Run: python scripts/reseed_pharmacies.py
"""
import os
import sys
import time
import secrets
import string
import hashlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault('DATABASE_URL', 'postgresql://reddot_user:RedDot%402025@136.118.42.101:5432/red_dot_pharmacy')

from google.cloud import storage as gcs_storage
from sqlalchemy import text
from app import create_app, db
from models import Pharmacy, PharmacyAdmin
from services.pharmacy_service import generate_slug

GCS_BUCKET = "pharma-connect-uploads"
GCS_PREFIX = "uploads/uploads"

PHARMACY_DIR = Path(r"C:\Users\Hassan\Desktop\pharmacy thumbnail")
OWNER_DIR = Path(r"C:\Users\Hassan\Desktop\owner of pharmacy")

# (excel_name, owner_filename_stem, owner_display_name, phone, address, city)
SEED = [
    ("D watson",                         "Zafar Bakhtawari",       "Zafar Bakhtawari",      "051-8447077",      "Din Pavillion, F-7, Blue Area",                               "Islamabad"),
    ("Bestcare Pharmacy",                "alex diamond",           "Alex Diamond",          "+92 5127 503 97",  "Sector D-12, D-12 Markaz",                                     "Islamabad"),
    ("Prime Health Pharmacy",            "Prof.-Dr.-Jamal-Zafar",  "Prof. Dr. Jamal Zafar", "(051) 5918171",    "Ghora Chowk Filter Plant, Plaza #12, Bahria Phase 7",          "Islamabad"),
    ("Pharmacy Prime",                   "Khawaja UmerZeb",        "Khawaja UmerZeb",       "+92 5121 577 53",  "Ghauri Town, Phase 5A",                                        "Islamabad"),
    ("Kuresure, Lab Clinic & Pharmacy",  "Mr Hussein Hadi",        "Hussein Hadi",          "(051) 5913887",    "Bahria Ave, Phase 7 near Fatima Masjid",                       "Islamabad"),
    ("Kure sure pharmacy",               "Raheel Kaiser",          "Raheel Kaiser",         "+92 300 0000000",  "Wallayat Complex, Street 7, Phase 7",                          "Rawalpindi"),
    ("Cure and Care pharmacy",           "Nasir Nazir Satti",      "Nasir Nazir Satti",     "+92 333 5412404",  "Bahria Town, Phase 8 Block M",                                 "Rawalpindi"),
    ("Hanif Pharmacy - Saidpur Road",    "arif khan",              "Arif Khan",             "+92 308 8487999",  "Saidpur Rd, adjacent Bank Alfalah, Asghar Mall Scheme",        "Rawalpindi"),
    ("National Pharmacy Kurri Road",     "Abdurahiman",            "Abdur Rahiman",         "+92 330 5333133",  "Farooq-e-Azam Rd, near Haroon Chowk, Kuri Road",               "Rawalpindi"),
    ("Town Pharmacy",                    "Usama Rehman",           "Usama Rehman",          "+92 51 4453806",   "E-1-1, Saidpur Road",                                          "Rawalpindi"),
    ("MM Pharmacy",                      "faisal memon",           "Faisal Memon",          "+92 332 0747241",  "B-847 Commercial Market Rd, Satellite Town",                   "Rawalpindi"),
    ("Sial Pharmacy",                    "usman sial",             "Usman Sial",            "+92 328 0440404",  "Opposite ARL Cricket Ground, Morgah",                          "Rawalpindi"),
    ("Yellow Pharmacy",                  "SAJID MEHSOD",           "Sajid Mehsood",         "051-5189748",      "Lane #7, Officers Colony, Misrial Road",                       "Rawalpindi"),
]


def random_password(n=10):
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(n))


def phash(pw):
    return hashlib.sha256(pw.encode()).hexdigest()


def find_file(directory, stem):
    """Find a file in `directory` matching `stem` (case/space tolerant)."""
    stem_norm = stem.strip().lower().replace(' ', '').replace('-', '').replace('.', '')
    for p in directory.iterdir():
        if p.is_file():
            fname_norm = p.stem.strip().lower().replace(' ', '').replace('-', '').replace('.', '')
            if fname_norm == stem_norm:
                return p
    return None


def upload_blob(local_path: Path, gcs_subpath: str) -> str:
    """Upload a local file to GCS under the given subpath (relative to GCS_PREFIX)."""
    client = gcs_storage.Client()
    bucket = client.bucket(GCS_BUCKET)
    blob = bucket.blob(f"{GCS_PREFIX}/{gcs_subpath}")
    blob.cache_control = "public, max-age=60"
    blob.upload_from_filename(str(local_path))
    return f"/static/uploads/{gcs_subpath}"


def main():
    app = create_app()
    with app.app_context():
        print("=" * 70)
        print("WIPING existing pharmacy data…")
        db.session.execute(text("DELETE FROM chat_logs WHERE pharmacy_id IS NOT NULL"))
        db.session.execute(text("UPDATE users SET pharmacy_id = NULL WHERE pharmacy_id IS NOT NULL"))
        db.session.execute(text("DELETE FROM pharmacy_reviews"))
        db.session.execute(text("DELETE FROM time_slots"))
        db.session.execute(text("DELETE FROM doctor_availability"))
        db.session.execute(text("DELETE FROM pharmacy_admins"))
        db.session.execute(text("DELETE FROM pharmacies"))
        db.session.commit()
        print("Old pharmacy records deleted.\n")

        credentials = []
        for pharm_name, owner_stem, owner_display, phone, address, city in SEED:
            slug = generate_slug(pharm_name)
            pharm_img = find_file(PHARMACY_DIR, pharm_name)
            owner_img = find_file(OWNER_DIR, owner_stem)
            if not pharm_img:
                print(f"  [!] Pharmacy image not found for '{pharm_name}' — skipping")
                continue
            if not owner_img:
                print(f"  [!] Owner image not found for '{owner_stem}' — skipping")
                continue

            ts = int(time.time())
            owner_ext = owner_img.suffix.lstrip('.').lower()
            pharm_ext = pharm_img.suffix.lstrip('.').lower()
            owner_path = upload_blob(owner_img, f"pharmacies/{slug}/owner_{slug}_{ts}.{owner_ext}")
            pharm_path = upload_blob(pharm_img, f"pharmacies/{slug}/pharmacy_{slug}_{ts}.{pharm_ext}")

            email = f"admin+{slug}@reddotpharmacy.com"
            password = random_password()

            pharmacy = Pharmacy()
            pharmacy.name = pharm_name
            pharmacy.slug = slug
            pharmacy.owner_name = owner_display
            pharmacy.email = email
            pharmacy.phone = phone
            pharmacy.address = address
            pharmacy.city = city
            pharmacy.province = "Punjab"
            pharmacy.theme_key = "theme-default"
            pharmacy.status = "approved"
            pharmacy.owner_photo_path = owner_path
            pharmacy.pharmacy_photo_path = pharm_path
            db.session.add(pharmacy)
            db.session.flush()

            admin = PharmacyAdmin()
            admin.pharmacy_id = pharmacy.id
            admin.name = owner_display
            admin.email = email
            admin.password_hash = phash(password)
            db.session.add(admin)

            credentials.append((pharm_name, email, password))
            print(f"  [+] {pharm_name:40s} owner={owner_display}")

        db.session.commit()
        print()
        print("=" * 70)
        print("LOGIN CREDENTIALS (save these!)")
        print("=" * 70)
        for name, email, pw in credentials:
            print(f"{name:40s}  {email:45s}  {pw}")


if __name__ == "__main__":
    main()
