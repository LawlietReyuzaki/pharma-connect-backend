# TODO Before Production Rollout

**Last updated:** 2026-05-02
**Owner:** Hassan
**Status:** Working list — tick items as you finish.

This list is the gap between today's codebase and a production-ready launch. Items are ordered by **risk to rollout** (CRITICAL → HIGH → MEDIUM → NICE-TO-HAVE).

For how the system *currently works*, see `USER_FLOWS.md`.

---

## CRITICAL (block launch)

### 1. Google Calendar Service Account
**Why it matters:** Without this, **patient appointments fail with HTTP 503**. Currently the booking flow tries:
1. Service account → fails (not configured)
2. Doctor's personal OAuth → fails (no doctor has connected their account)
3. Returns 503 to the patient

**What to do:**
- [ ] Create a Google Cloud project (or use existing one)
- [ ] Enable Google Calendar API
- [ ] Create a **service account** with domain-wide delegation
- [ ] Download `service_account_key.json`
- [ ] Either:
  - **Option A (local):** Place file at `service_account_key.json` in project root
  - **Option B (env):** Read the JSON content and set as `GOOGLE_SERVICE_ACCOUNT_KEY` env var (preferred for deployments)
- [ ] In Google Workspace admin (if using a workspace): grant domain-wide delegation with scopes:
  - `https://www.googleapis.com/auth/calendar`
  - `https://www.googleapis.com/auth/calendar.events`
- [ ] Verify by hitting `GET /api/appointments/check-calendar-setup` — should return `{ "configured": true }`
- [ ] Test booking an appointment as a patient — Meet link should appear

**Code references:**
- `services/google_calendar_service_account.py:57` — credentials loader
- `routes/appointment_routes.py:71-212` — booking flow
- `routes/appointment_routes.py:12-68` — diagnostic endpoint

---

### 2. Move ALL API Keys to Environment Variables

**Currently hardcoded (security risk — `.env` is in git):**

| Key | Where it is now | Where it should go |
|---|---|---|
| `GEMINI_API_KEY=AIzaSyBio...` | `.env:3` | Deployment secret (Replit/Cloud Run env) |
| `GOOGLE_API_KEY=AIzaSyBio...` (same key) | `.env:4` | Same as above |
| `TTS_API_KEY=8f1e5568-...` | **`routes/chatbot_routes.py:260` (in code!)** | env var `TTS_API_KEY` |
| `URDU_VOICE_ID=86cad650-...` | `routes/chatbot_routes.py:262` | env var `TTS_URDU_VOICE_ID` |
| `JWT_SECRET=red-dot-pharmacy-jwt-secret-key-2025` | `.env:1` + fallback `services/auth.py:15` | env var, **rotate to a random 64+ char string** |
| `SESSION_SECRET=red-dot-pharmacy-secret-key` | fallback `app.py:30` | env var, random value |

**Steps:**
- [ ] Generate a fresh GEMINI key in Google AI Studio (rotate the leaked one)
- [ ] Generate a new JWT secret: `python -c "import secrets; print(secrets.token_urlsafe(64))"`
- [ ] Generate a new SESSION secret the same way
- [ ] Edit `routes/chatbot_routes.py:260-262` — replace hardcoded values with `os.getenv('TTS_API_KEY')` etc.
- [ ] Set all keys in your deployment environment (Replit Secrets / Cloud Run env / Docker `--env-file`)
- [ ] **Remove `.env` from git** if it contains real keys: `git rm --cached .env && git commit`
- [ ] Add `.env` to `.gitignore` if not already (verify)
- [ ] Make sure `.env.example` exists with placeholder values for new devs

---

### 3. Change Default Super Admin Password

**Currently:** `admin@reddot.com / Admin@1234` (also displayed on the admin login page UI)

**Steps:**
- [ ] Pick a strong password (16+ chars, mixed case, symbols)
- [ ] Run: `python create_super_admin.py admin@yourdomain.com 'YourStrongPassword!' 'Hassan'`
- [ ] Delete the default `admin@reddot.com` row from the `admins` table OR change its password to something unguessable
- [ ] **Remove the default credentials hint** from `admin-app/src/pages/Login.tsx:98` (currently shows them on the login screen)
- [ ] Document the production password in your password manager — NOT in code

---

### 4. Replace SHA256 Password Hashing with bcrypt

**Why:** SHA256 is unsalted and fast — vulnerable to rainbow tables and brute force.

**Steps:**
- [ ] Add `bcrypt` to `requirements.txt` (or use `werkzeug.security` which uses scrypt/pbkdf2)
- [ ] Update `services/auth.py:9-11`:
  ```python
  from werkzeug.security import generate_password_hash, check_password_hash
  def phash(pw: str) -> str:
      return generate_password_hash(pw)
  def pverify(pw: str, hashed: str) -> bool:
      return check_password_hash(hashed, pw)
  ```
- [ ] Replace all `phash(pw)` calls across:
  - `routes/auth_routes.py`
  - `routes/admin_auth_routes.py`
  - `routes/pharmacy_admin_routes.py`
  - `routes/doctor_routes.py`
  - `routes/pharmacy_registration_routes.py`
- [ ] Build a one-shot migration script: for each existing user/admin/pharmacy_admin, force a password reset on next login (or rehash on first successful SHA256 login)
- [ ] Test: register a new patient, login — should still work

---

## HIGH PRIORITY

### 5. Unify Super Admin Token Naming

**Problem:** Two admin UIs use different localStorage keys.
- Old `Admin.tsx` → `admin_token`
- New admin-app → `super_admin_token`

**Decision needed:** which UI ships in production?

**Recommended:** Use the new admin-app (port 8090) because it's a cleaner separation of concerns. Then:
- [ ] Delete or hide route `/admin` in `App.tsx:59` (or redirect to admin-app)
- [ ] Standardize on `super_admin_token` everywhere
- [ ] Document deployment: admin app served at `admin.yourdomain.com`, patient app at `app.yourdomain.com`

---

### 6. Decide on Pharmacist Role

**Current state:** No `pharmacist` role exists. The schema has `users.role IN ('patient', 'doctor', 'admin')` and a separate `pharmacy_admins` table for pharmacy owners.

**Question for you:** Do pharmacists need their own logins?
- If pharmacists are basically the **owner** → already covered by `pharmacy_admins`
- If pharmacists are **floor staff** of a pharmacy who need limited dashboard access → needs new role

**If you need it, here's the work:**
- [ ] Add `pharmacist` to `users.role` enum
- [ ] Add `pharmacy_id` link (already exists for doctors — same column reusable)
- [ ] Define what a pharmacist can do (presumably: see/update orders for their pharmacy, but NOT add doctors / change settings)
- [ ] New endpoint: `POST /pharmacy-admin/api/pharmacists` (created by owner)
- [ ] New login: `POST /pharmacist/api/login` OR reuse `/api/auth/login` and gate dashboard by role
- [ ] New dashboard page: `PharmacistDashboard.tsx` (could be a stripped-down `PharmacyAdminDashboard`)
- [ ] Update `USER_FLOWS.md` to reflect

**If you don't need it:** delete this section and remove "pharmacists" from your mental model.

---

### 7. Email Notifications

**Currently:** zero emails are sent. Critical events happen silently.

**Need to send emails for:**
- [ ] Pharmacy approval → "Your pharmacy is approved, you can now log in"
- [ ] Pharmacy rejection → "Your application was rejected: [reason]"
- [ ] Pharmacy suspension → "Your pharmacy was suspended"
- [ ] Appointment booking confirmation → patient + doctor
- [ ] New doctor onboarding → "Your account at [pharmacy], temp password: [randomized]"
- [ ] Order placed → patient receipt
- [ ] Order status change → patient ("out for delivery", etc.)
- [ ] Payment receipt verified/rejected → patient

**How to implement:**
- [ ] Pick provider: SendGrid (easy) / Mailgun / AWS SES (cheap at scale)
- [ ] Add `flask-mail` or use the provider's SDK
- [ ] Create `services/email.py` with templated functions: `send_approval_email(...)`, etc.
- [ ] Add `SENDGRID_API_KEY` (or equivalent) to env
- [ ] Hook into approval/rejection routes in `admin_routes.py:2284` (approve) and `:2313` (reject)
- [ ] Hook into `appointment_routes.py:71` (booking)

---

### 8. Rate Limiting on Auth Endpoints

**Risk:** brute-force attacks against `/api/auth/login`, `/admin/auth/login`, `/pharmacy-admin/api/login`.

**Steps:**
- [ ] `pip install flask-limiter` and add to `requirements.txt`
- [ ] In `app.py`, configure:
  ```python
  from flask_limiter import Limiter
  from flask_limiter.util import get_remote_address
  limiter = Limiter(app=app, key_func=get_remote_address, storage_uri="memory://")
  ```
- [ ] Decorate each login endpoint:
  ```python
  @limiter.limit("5 per minute")
  ```
- [ ] For production: switch storage_uri to Redis if you have multiple Flask workers

---

### 9. Randomize New Doctor Temp Passwords

**Currently:** `routes/pharmacy_admin_routes.py:362` sets `changeme123` as the temp password for every new doctor.

**Steps:**
- [ ] Replace with `secrets.token_urlsafe(12)` to generate a random 12-char password per doctor
- [ ] Return the temp password ONCE in the API response (so the pharmacy owner can copy it to share with the doctor)
- [ ] Send via email if §7 is done
- [ ] Confirm doctor still has to call `/doctor/api/setup-password` on first login

---

## MEDIUM PRIORITY

### 10. Per-Pharmacy Medicine Inventory

**Currently:** `medicines` table is **global** — every pharmacy sees the same catalog. There's a `stock_quantity` column but nothing decrements it on order.

**Two options:**

**Option A (simpler): Keep global catalog, just track stock**
- [ ] On `POST /api/orders/`, decrement `medicines.stock_quantity` per item
- [ ] Reject orders if stock would go negative
- [ ] Add low-stock alerts visible to super admin

**Option B (proper multi-tenant): Per-pharmacy stock**
- [ ] Add new table `pharmacy_medicines` with `(pharmacy_id, medicine_id, price, stock_quantity)`
- [ ] Each pharmacy can set their own price + stock
- [ ] Update Shop.tsx to filter by selected pharmacy
- [ ] Update Pharmacy admin dashboard with "Inventory" tab

Pick one and go.

---

### 11. Remove Debug Code

- [ ] Remove `print("Chat endpoint called")` at `routes/chatbot_routes.py:268`
- [ ] Audit all `logging.debug(...)` calls — make sure they don't log passwords or tokens
- [ ] Check `services/google_calendar_service_account.py:63-95` — verify nothing sensitive is logged
- [ ] Set `LOG_LEVEL=INFO` in production env (don't run DEBUG in prod)

---

### 12. Restrict CORS

**Currently:** `CORS(app)` in `app.py:43` allows any origin.

- [ ] Whitelist your production domains:
  ```python
  CORS(app, origins=["https://app.yourdomain.com", "https://admin.yourdomain.com"])
  ```

---

### 13. Input Validation

**Risk areas:** registration forms, file uploads.

- [ ] Validate email format using `email-validator` (already in requirements) — currently regex-only or none
- [ ] Validate phone numbers (libphonenumber-py)
- [ ] On photo upload: check file extension AND MIME type AND file size (currently only extension is checked in some places)
- [ ] On payment receipt upload: same as above + scan with virus check (clamav-rest or cloud equivalent) — optional but recommended

---

### 14. Add Prescription Tracking

**Today:** appointments capture symptoms in a text field. No record of what was prescribed.

- [ ] New table `prescriptions(id, appointment_id, doctor_id, patient_id, medicine_id, dosage, duration, notes, created_at)`
- [ ] New endpoint `POST /doctor/api/appointments/:id/prescription` — doctor adds prescription after consult
- [ ] Patient sees prescription in `/appointments` page detail view
- [ ] Optional: pharmacy auto-creates a pre-filled order from prescription

---

## NICE-TO-HAVE / POLISH

### 15. Refund Tracking Table
Orders today can be cancelled but there's no refund record. If you accept real payments, this is needed for bookkeeping.

### 16. Notification Queue
Right now there's no in-app notification system. Adding a `notifications` table + bell icon in navbar would close that loop.

### 17. Frontend UI polish — Inner pages
The Stitch design has been applied to:
- ✅ Navbar
- ✅ Footer
- ✅ PlatformHome (full Stitch landing)
- ✅ PharmacyNetwork (Stitch hero + grid)
- ⚠️ PharmacyLanding — only token swap, layout untouched (per-pharmacy theming preserved)
- ❌ Shop, Consultation, Appointments, Assistant, Admin, Doctor, PharmacyAdmin — token swap only, original layouts

If you want full Stitch alignment on inner pages, it's another layout-rebuild pass per page.

### 18. Docker / Deployment hardening
- [ ] Multi-stage Dockerfile to slim image
- [ ] Health check endpoint `GET /healthz`
- [ ] Run Flask under gunicorn (not `flask run`)
- [ ] Set `WORKERS=4`, `THREADS=2` in production
- [ ] Add structured logging (JSON output) for Cloud Run / GKE consumption

---

## QUICK SANITY CHECKS (do these now)

- [ ] Does `python -c "import app"` succeed without errors?
- [ ] Does `npm run build` (in `react frontend/ui-ux-polish`) succeed?  ✅ Verified 2026-05-02
- [ ] Does `npm run build` for the admin-app succeed?
- [ ] Does the pharmacy approval flow work end-to-end on a fresh DB? (register → see in admin → approve → login as owner)
- [ ] Does a patient login + book an appointment work? (will fail until §1 done)
- [ ] Does the chatbot respond? (depends on §2 — current key may be revoked)

---

## DEPLOYMENT ENVIRONMENT VARIABLES (final list)

When you deploy, set these in your platform's secret manager:

```bash
# Database
DATABASE_URL=postgresql://user:pass@host/dbname

# Auth
JWT_SECRET=<random 64+ char string>
SESSION_SECRET=<random 64+ char string>

# Gemini / Google AI
GEMINI_API_KEY=<your gemini key>
GOOGLE_API_KEY=<your google key>
GEMINI_MODEL=gemini-2.0-flash
GEMINI_TEMPERATURE=0.7

# TTS (currently hardcoded — must move to env per §2)
TTS_API_KEY=<your tts key>
TTS_URDU_VOICE_ID=<voice id>

# Google Calendar (per §1)
GOOGLE_SERVICE_ACCOUNT_KEY=<full JSON content as a single env var>
# OR: GOOGLE_APPLICATION_CREDENTIALS=/path/to/service_account_key.json

# Google OAuth (only if using doctor OAuth fallback)
GOOGLE_OAUTH_CLIENT_ID=
GOOGLE_OAUTH_CLIENT_SECRET=

# Email (per §7)
SENDGRID_API_KEY=<your sendgrid key>
EMAIL_FROM=noreply@yourdomain.com

# Flask
FLASK_ENV=production
LOG_LEVEL=INFO

# GCS (uploads)
GCS_BUCKET_NAME=pharma-connect-uploads
```

---

## SUMMARY: WHAT'S CURRENTLY INTACT ✅

After today's UI rebuild work, the following are **verified working**:

- [x] React app builds clean (`vite build` exit 0)
- [x] TypeScript typecheck clean (`tsc --noEmit` exit 0)
- [x] Stitch design applied to: Navbar, Footer, PlatformHome, PharmacyNetwork
- [x] All auth contexts, routes, API calls preserved (no logic changes in UI rebuild)
- [x] Token storage keys unchanged (`auth_token`, `pharmacy_admin_token`, `doctor_token`, `super_admin_token`)
- [x] All four user types still have their entry points and dashboards
- [x] Pharmacy approval flow logic untouched
- [x] Chatbot endpoints untouched

The Stitch UI work didn't break anything — it was purely visual restructuring of the public-facing landing pages.

---

**Tracking:** Tick items as you finish them. When all CRITICAL + HIGH are done, you're production-ready.
