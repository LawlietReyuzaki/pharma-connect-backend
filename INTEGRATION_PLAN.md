# Integration Plan — Multi-Pharmacy Network Layer
## Building on Top of Red Dot Pharmacy (Existing Codebase)
### Version 1.0 | March 15, 2026

---

## Overview

This plan describes **exactly what to add, change, and extend** in the existing codebase to transform the single-pharmacy Red Dot system into a multi-pharmacy network platform. It is ordered by implementation phase so that each phase builds on the previous one without breaking existing functionality.

**Core principle:** We do not rewrite what exists. We extend it.

---

## Phase 0 — Preparation (Before Writing Any Code)

### 0.1 Answer These Before Starting

These decisions affect the architecture of every phase:

| Decision | Recommended Choice | Reason |
|---|---|---|
| Customer account model | Single unified account across all pharmacies | Avoids duplicate registration friction |
| Medicine catalog ownership | Global catalog, managed by Super Admin only | Already exists; no per-pharmacy medicines in V1 |
| Delivery model | Each pharmacy manages its own delivery | Simpler; matches SRS |
| Pharmacy URL structure | `/pharmacy/<slug>` path-based | Easier without DNS per pharmacy |
| Theme system | CSS custom properties (variables) injected via template | Simplest implementation, no extra libraries |
| Doctor-pharmacy link | A doctor belongs to exactly one pharmacy in V1 | Avoids complexity |
| Reviews go live | Instantly (no moderation queue in V1) | Faster; report/remove available |

### 0.2 Backup Current Database

```bash
cp red_dot_pharmacy.db red_dot_pharmacy_backup_$(date +%Y%m%d).db
```

---

## Phase 1 — Database Layer (Models)

**Goal:** Add the data structures needed for multi-tenancy without breaking any existing models.

### 1.1 New Model: `Pharmacy`

Add to `models.py`:

```python
class Pharmacy(db.Model):
    __tablename__ = 'pharmacies'

    id                  = db.Column(db.Integer, primary_key=True)
    name                = db.Column(db.String(200), nullable=False)
    slug                = db.Column(db.String(100), unique=True, nullable=False)  # URL-safe name
    owner_name          = db.Column(db.String(120), nullable=False)
    owner_photo_path    = db.Column(db.String(255))
    pharmacy_photo_path = db.Column(db.String(255))
    email               = db.Column(db.String(120), unique=True, nullable=False)
    phone               = db.Column(db.String(50))
    address             = db.Column(db.Text)
    city                = db.Column(db.String(100))
    province            = db.Column(db.String(100))
    latitude            = db.Column(db.Float)   # For location recommendations
    longitude           = db.Column(db.Float)
    license_number      = db.Column(db.String(100))
    operating_hours     = db.Column(db.Text)    # JSON string e.g. {"mon":"9-5","tue":"9-5"...}
    theme_key           = db.Column(db.String(50), default='theme-default')
    status              = db.Column(db.String(30), default='pending')  # pending|approved|suspended
    approved_by         = db.Column(db.Integer, db.ForeignKey('admins.admin_id'))
    approved_at         = db.Column(db.DateTime)
    rejection_reason    = db.Column(db.Text)
    avg_rating          = db.Column(db.Float, default=0.0)
    review_count        = db.Column(db.Integer, default=0)
    created_at          = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at          = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    users       = db.relationship('User', backref='pharmacy', lazy='dynamic')
    orders      = db.relationship('Order', backref='pharmacy', lazy='dynamic')
    reviews     = db.relationship('PharmacyReview', backref='pharmacy', lazy='dynamic')
```

### 1.2 New Model: `PharmacyAdmin`

Pharmacy owners log in through this model (separate from the Super Admin `Admin` model):

```python
class PharmacyAdmin(db.Model):
    __tablename__ = 'pharmacy_admins'

    id            = db.Column(db.Integer, primary_key=True)
    pharmacy_id   = db.Column(db.Integer, db.ForeignKey('pharmacies.id'), nullable=False)
    name          = db.Column(db.String(120), nullable=False)
    email         = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)

    pharmacy = db.relationship('Pharmacy', backref='admins')
```

### 1.3 New Model: `PharmacyReview`

```python
class PharmacyReview(db.Model):
    __tablename__ = 'pharmacy_reviews'

    id            = db.Column(db.Integer, primary_key=True)
    pharmacy_id   = db.Column(db.Integer, db.ForeignKey('pharmacies.id'), nullable=False)
    user_id       = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    rating        = db.Column(db.Integer, nullable=False)   # 1–5
    comment       = db.Column(db.String(500))
    owner_reply   = db.Column(db.Text)
    source_type   = db.Column(db.String(20))  # 'order' | 'appointment'
    source_id     = db.Column(db.Integer)     # order_id or appointment_id
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)

    user     = db.relationship('User', backref='reviews')
```

### 1.4 Modify Existing Models (Add `pharmacy_id`)

Add `pharmacy_id` as a nullable foreign key to these existing models. Making it nullable preserves all existing data rows (they will have `pharmacy_id = NULL`, treated as "legacy/unscoped"):

**`User` model** — add:
```python
pharmacy_id = db.Column(db.Integer, db.ForeignKey('pharmacies.id'), nullable=True)
```

**`Order` model** — add:
```python
pharmacy_id = db.Column(db.Integer, db.ForeignKey('pharmacies.id'), nullable=True)
```

**`ChatLog` model** — add:
```python
pharmacy_id = db.Column(db.Integer, db.ForeignKey('pharmacies.id'), nullable=True)
```

> Note: `Medicine` model does NOT get a `pharmacy_id` — the catalog is global (shared).
> Note: `Appointment` is linked via `doctor_id → User → pharmacy_id` so no direct change needed.

### 1.5 Database Migration Script

Create `migrate_add_pharmacy.py`:

```python
# Adds new tables and columns without dropping existing data
# Run once after model changes:
#   python migrate_add_pharmacy.py

from app import create_app, db
from sqlalchemy import text

app = create_app()
with app.app_context():
    # Create new tables
    db.create_all()

    # Add pharmacy_id column to existing tables if not exists
    with db.engine.connect() as conn:
        for table, col in [
            ('users',     'pharmacy_id INTEGER REFERENCES pharmacies(id)'),
            ('orders',    'pharmacy_id INTEGER REFERENCES pharmacies(id)'),
            ('chat_logs', 'pharmacy_id INTEGER REFERENCES pharmacies(id)'),
        ]:
            try:
                conn.execute(text(f'ALTER TABLE {table} ADD COLUMN {col}'))
                conn.commit()
                print(f'Added pharmacy_id to {table}')
            except Exception as e:
                print(f'Skipped {table}: {e}')

    print('Migration complete.')
```

---

## Phase 2 — Theme System

**Goal:** Each pharmacy page renders with their chosen color theme. Zero CSS duplication.

### 2.1 Define Themes in a Config File

Create `static/css/themes.css`:

```css
/* Each theme defines CSS custom properties */
.theme-default   { --primary: #2563eb; --accent: #1d4ed8; --bg: #f8fafc; --nav: #1e3a5f; }
.theme-emerald   { --primary: #059669; --accent: #047857; --bg: #f0fdf4; --nav: #064e3b; }
.theme-crimson   { --primary: #dc2626; --accent: #b91c1c; --bg: #fff5f5; --nav: #7f1d1d; }
.theme-violet    { --primary: #7c3aed; --accent: #6d28d9; --bg: #faf5ff; --nav: #4c1d95; }
.theme-amber     { --primary: #d97706; --accent: #b45309; --bg: #fffbeb; --nav: #78350f; }
.theme-sky       { --primary: #0284c7; --accent: #0369a1; --bg: #f0f9ff; --nav: #0c4a6e; }
.theme-rose      { --primary: #e11d48; --accent: #be123c; --bg: #fff1f2; --nav: #881337; }
.theme-teal      { --primary: #0d9488; --accent: #0f766e; --bg: #f0fdfa; --nav: #134e4a; }
.theme-indigo    { --primary: #4338ca; --accent: #3730a3; --bg: #eef2ff; --nav: #1e1b4b; }
.theme-orange    { --primary: #ea580c; --accent: #c2410c; --bg: #fff7ed; --nav: #7c2d12; }
```

Update `static/css/style.css` to use `var(--primary)` etc. everywhere a color is hardcoded (do this incrementally — only pharmacy profile pages need theming initially).

### 2.2 Theme Selection in Pharmacy Profile Template

In `pharmacy_profile.html` (new template, see Phase 4), apply the theme class to the `<body>`:

```html
<body class="{{ pharmacy.theme_key }}">
```

The pharmacy's `theme_key` (e.g., `theme-emerald`) is pulled from the DB and injected by the route.

### 2.3 Available Themes List (for Registration Form)

Store theme options in `config.py`:

```python
AVAILABLE_THEMES = [
    {'key': 'theme-default', 'name': 'Blue (Default)', 'preview': '#2563eb'},
    {'key': 'theme-emerald', 'name': 'Emerald Green',  'preview': '#059669'},
    {'key': 'theme-crimson', 'name': 'Crimson Red',    'preview': '#dc2626'},
    {'key': 'theme-violet',  'name': 'Violet Purple',  'preview': '#7c3aed'},
    {'key': 'theme-amber',   'name': 'Amber Gold',     'preview': '#d97706'},
    {'key': 'theme-sky',     'name': 'Sky Blue',        'preview': '#0284c7'},
    {'key': 'theme-rose',    'name': 'Rose Pink',       'preview': '#e11d48'},
    {'key': 'theme-teal',    'name': 'Teal',            'preview': '#0d9488'},
    {'key': 'theme-indigo',  'name': 'Indigo',          'preview': '#4338ca'},
    {'key': 'theme-orange',  'name': 'Orange',          'preview': '#ea580c'},
]
```

---

## Phase 3 — New Routes & Blueprints

### 3.1 New Blueprint: `pharmacy_routes.py` (Public-Facing)

Register at prefix `/pharmacy` in `app.py`.

| Method | Route | Purpose |
|---|---|---|
| GET | `/` (platform homepage) | Landing page with search + "near me" |
| GET | `/pharmacy/<slug>` | Pharmacy public profile page |
| GET | `/api/pharmacies` | JSON: list pharmacies (search, city, rating filters) |
| GET | `/api/pharmacies/nearby` | JSON: nearest pharmacies (lat/lng query params) |
| GET | `/api/pharmacies/<slug>` | JSON: single pharmacy detail |
| GET | `/api/pharmacies/<slug>/doctors` | JSON: doctors at pharmacy |
| GET | `/api/pharmacies/<slug>/reviews` | JSON: paginated reviews |

### 3.2 New Blueprint: `pharmacy_registration_routes.py`

Register at prefix `/register` in `app.py`.

| Method | Route | Purpose |
|---|---|---|
| GET | `/register/pharmacy` | Registration form page |
| POST | `/api/register/pharmacy` | Submit registration (multipart/form-data) |
| GET | `/register/status` | Check registration status (email lookup) |

**Registration handler logic:**
1. Validate all required fields.
2. Save uploaded `owner_photo` and `pharmacy_photo` to `static/uploads/pharmacies/<slug>/`.
3. Auto-generate `slug` from pharmacy name (lowercase, spaces→hyphens, unique).
4. Create `Pharmacy` record with `status='pending'`.
5. Create `PharmacyAdmin` record (email + hashed password).
6. Send confirmation email to pharmacy (optional in V1).
7. Notify Super Admin (flag in admin dashboard).

### 3.3 New Blueprint: `pharmacy_admin_routes.py`

Register at prefix `/pharmacy-admin` in `app.py`.

| Method | Route | Purpose |
|---|---|---|
| GET | `/pharmacy-admin` | Pharmacy admin dashboard page |
| POST | `/pharmacy-admin/api/login` | Pharmacy admin login |
| POST | `/pharmacy-admin/api/verify` | Verify pharmacy admin token |
| GET | `/pharmacy-admin/api/stats` | Dashboard stats (orders, appointments, reviews) |
| GET | `/pharmacy-admin/api/orders` | Orders for this pharmacy only |
| PUT | `/pharmacy-admin/api/orders/<id>/status` | Update order status |
| GET | `/pharmacy-admin/api/appointments` | Appointments for this pharmacy's doctors |
| GET | `/pharmacy-admin/api/doctors` | Doctors under this pharmacy |
| POST | `/pharmacy-admin/api/doctors` | Add doctor to pharmacy |
| PUT | `/pharmacy-admin/api/doctors/<id>` | Update doctor |
| DELETE | `/pharmacy-admin/api/doctors/<id>` | Remove doctor from pharmacy |
| GET | `/pharmacy-admin/api/reviews` | Reviews for this pharmacy |
| POST | `/pharmacy-admin/api/reviews/<id>/reply` | Reply to a review |
| GET | `/pharmacy-admin/api/profile` | Get pharmacy profile info |
| PUT | `/pharmacy-admin/api/profile` | Update pharmacy info, photos, theme |
| GET | `/pharmacy-admin/api/chat-logs` | Chat logs from this pharmacy's page |

**Authentication for pharmacy admin routes:**
- Use a new `require_pharmacy_admin` decorator in `services/auth.py`
- JWT payload includes `pharmacy_id` and `role: 'pharmacy_admin'`
- All DB queries in pharmacy admin routes filter by `pharmacy_id`

### 3.4 New API Routes: Reviews

Add to `pharmacy_routes.py`:

| Method | Route | Purpose |
|---|---|---|
| POST | `/api/pharmacies/<slug>/reviews` | Submit a review (requires login + completed order or appointment) |
| GET | `/api/pharmacies/<slug>/reviews` | Get reviews (public) |

**Submit review validation:**
1. User must be logged in.
2. User must have at least one completed order or appointment at this pharmacy.
3. User must not have reviewed this source (order_id or appointment_id) before.
4. Rating must be 1–5.
5. On successful save, recalculate `pharmacy.avg_rating` and `pharmacy.review_count`.

### 3.5 Extend Existing Routes for Pharmacy Scoping

**`store_routes.py`** — No change needed. Medicine catalog is global.

**`order_routes.py`** — Modify `POST /api/orders/` to accept an optional `pharmacy_id` in the request body. When present, save it to `order.pharmacy_id`.

**`chatbot_routes.py`** — Modify `POST /api/chat/medical-chat` to accept an optional `pharmacy_id` and save it to `chat_log.pharmacy_id`.

**`appointment_routes.py`** — No structural change needed. Appointment is scoped through the doctor, who belongs to a pharmacy.

### 3.6 Extend Super Admin Routes

Add to `admin_routes.py` (existing file):

| Method | Route | Purpose |
|---|---|---|
| GET | `/admin/api/pharmacy-applications` | List pending pharmacy registrations |
| POST | `/admin/api/pharmacy-applications/<id>/approve` | Approve pharmacy |
| POST | `/admin/api/pharmacy-applications/<id>/reject` | Reject with reason |
| GET | `/admin/api/all-pharmacies` | List all approved pharmacies |
| PUT | `/admin/api/all-pharmacies/<id>/suspend` | Suspend pharmacy |
| PUT | `/admin/api/all-pharmacies/<id>/reactivate` | Reactivate pharmacy |
| DELETE | `/admin/api/reviews/<id>` | Remove inappropriate review |
| GET | `/admin/api/platform-stats` | Aggregate stats across all pharmacies |

---

## Phase 4 — New Templates (HTML Pages)

### 4.1 New Template: `platform_home.html`

The new platform landing page (replaces or extends current `index.html`).

**Sections:**
1. **Hero** — Headline "Find Your Pharmacy", search bar (name/city), "Use My Location" button
2. **Pharmacies Near You** — Horizontally scrollable cards (shown if location granted)
3. **Browse All Pharmacies** — Grid of pharmacy cards with filters (city, rating, specialization)
4. **How It Works** — 3-step explainer for customers
5. **Register Your Pharmacy** — CTA for pharmacy owners

**Each pharmacy card shows:**
- Pharmacy photo (thumbnail)
- Pharmacy name
- City · Star rating (⭐ 4.2 · 38 reviews)
- Number of doctors
- Distance (if location granted)
- "Visit Page" button → `/pharmacy/<slug>`

### 4.2 New Template: `pharmacy_profile.html`

The branded, per-pharmacy page.

**Structure:**
```html
<body class="{{ pharmacy.theme_key }}">
  <!-- Hero Section -->
  <div class="pharmacy-hero">
    <img src="{{ pharmacy.pharmacy_photo_path }}" />
    <div>
      <h1>{{ pharmacy.name }}</h1>
      <p>{{ pharmacy.address }}, {{ pharmacy.city }}</p>
      <span>⭐ {{ pharmacy.avg_rating }} ({{ pharmacy.review_count }} reviews)</span>
    </div>
    <img src="{{ pharmacy.owner_photo_path }}" class="owner-photo" />
    <span>{{ pharmacy.owner_name }}</span>
  </div>

  <!-- Quick Action Buttons -->
  <div class="actions">
    <button onclick="openChatbot()">Consult AI Assistant</button>
    <button onclick="scrollToDoctors()">Book Appointment</button>
    <button onclick="scrollToMedicines()">Order Medicines</button>
  </div>

  <!-- Doctors Section -->
  <section id="doctors">...</section>

  <!-- Medicine Catalog (reuse existing shop UI) -->
  <section id="medicines">...</section>

  <!-- Reviews Section -->
  <section id="reviews">...</section>

  <!-- Map (pharmacy location) -->
  <section id="location">...</section>
</body>
```

The chatbot widget, shop, and booking form are **embedded** from existing functionality — just themed.

### 4.3 New Template: `pharmacy_register.html`

Multi-step registration form:

- **Step 1:** Pharmacy details (name, address, city, contact, license number, operating hours)
- **Step 2:** Owner info (owner name, owner photo upload, pharmacy photo upload)
- **Step 3:** Theme selection (visual grid of 10 color swatches)
- **Step 4:** Account setup (email, password for Pharmacy Admin login)
- **Step 5:** Confirmation page ("Application submitted, you'll hear from us within 24–48 hours")

### 4.4 New Template: `pharmacy_admin_dashboard.html`

Modeled after `admin.html` but scoped to one pharmacy. Reuse the same Bootstrap/Chart.js setup.

**Sidebar nav:**
- Overview (stats)
- Orders
- Appointments
- My Doctors
- Reviews
- Profile Settings

### 4.5 Update Existing Templates

**`base.html`** — No change needed for now (pharmacy pages use their own base).

**`index.html`** — Either replace it with `platform_home.html` or redirect `/` to the platform home. Keep old single-pharmacy flow accessible at `/pharmacy/red-dot` (the original pharmacy registers as the first pharmacy on the network).

---

## Phase 5 — Services Layer

### 5.1 New Service: `services/pharmacy_service.py`

Business logic for pharmacy operations:

```python
def get_nearby_pharmacies(lat, lng, limit=10):
    """Return pharmacies sorted by Haversine distance from lat/lng"""

def generate_slug(name):
    """Convert pharmacy name to URL-safe slug, ensure uniqueness"""

def approve_pharmacy(pharmacy_id, admin_id):
    """Approve pharmacy, create default PharmacyAdmin if needed, send notification"""

def recalculate_rating(pharmacy_id):
    """Recalculate avg_rating and review_count after new review"""

def get_pharmacy_stats(pharmacy_id):
    """Return stats dict: orders_today, pending_appointments, revenue, new_reviews"""
```

### 5.2 Update `services/auth.py`

Add pharmacy admin authentication:

```python
def create_pharmacy_admin_token(pharmacy_admin):
    """JWT payload includes pharmacy_id"""

def verify_pharmacy_admin_token(token):
    """Decode and validate pharmacy admin JWT"""

def require_pharmacy_admin(f):
    """Decorator that checks for valid pharmacy admin JWT"""

def get_current_pharmacy_admin():
    """Extract pharmacy admin from Authorization header"""
```

### 5.3 Update `services/chatbot.py`

Add `pharmacy_id` parameter to `generate_response()` and `log_chat_interaction()` so chatbot conversations are scoped to the pharmacy page they originate from.

```python
def generate_response(text, session_id, lang, pharmacy_id=None):
    # existing logic unchanged
    log_chat_interaction(..., pharmacy_id=pharmacy_id)
```

---

## Phase 6 — Location Feature

### 6.1 Frontend (JavaScript)

Add to `static/js/platform.js` (new file):

```javascript
function requestLocation() {
    if (!navigator.geolocation) return;
    navigator.geolocation.getCurrentPosition(
        position => {
            const { latitude, longitude } = position.coords;
            loadNearbyPharmacies(latitude, longitude);
        },
        () => showCityFallback()
    );
}

async function loadNearbyPharmacies(lat, lng) {
    const res = await fetch(`/api/pharmacies/nearby?lat=${lat}&lng=${lng}`);
    const data = await res.json();
    renderPharmacyCards(data.pharmacies, 'nearby-section');
}
```

### 6.2 Backend (Haversine Distance)

In `services/pharmacy_service.py`:

```python
import math

def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return R * 2 * math.asin(math.sqrt(a))

def get_nearby_pharmacies(lat, lng, limit=10):
    pharmacies = Pharmacy.query.filter_by(status='approved').all()
    with_distance = [
        (p, haversine(lat, lng, p.latitude, p.longitude))
        for p in pharmacies if p.latitude and p.longitude
    ]
    return sorted(with_distance, key=lambda x: x[1])[:limit]
```

---

## Phase 7 — File Uploads for Pharmacies

### 7.1 New Upload Directories

```
static/uploads/
  pharmacies/
    <slug>/
      owner_photo.jpg
      pharmacy_photo.jpg
```

Create on registration: `os.makedirs(f'static/uploads/pharmacies/{slug}', exist_ok=True)`

### 7.2 Update Upload Logic

In `pharmacy_registration_routes.py`, handle `multipart/form-data`:

```python
from werkzeug.utils import secure_filename

def save_pharmacy_photo(file, slug, photo_type):
    filename = secure_filename(f"{photo_type}_{slug}.{file.filename.rsplit('.',1)[1]}")
    path = f"static/uploads/pharmacies/{slug}/{filename}"
    file.save(path)
    return f"/static/uploads/pharmacies/{slug}/{filename}"
```

---

## Phase 8 — Super Admin Dashboard Extensions

The existing `admin.html` and `admin.js` get new sections. No need to rewrite the whole file.

### 8.1 Add to `admin.html` Sidebar

```html
<!-- New items in existing sidebar -->
<li onclick="showSection('pharmacy-applications')">
  Pharmacy Applications <span class="badge" id="pending-apps-count"></span>
</li>
<li onclick="showSection('all-pharmacies')">All Pharmacies</li>
<li onclick="showSection('platform-stats')">Platform Analytics</li>
```

### 8.2 Add to `admin.js`

New functions (appended to existing file):

```javascript
async function loadPharmacyApplications() { ... }
async function approvePharmacy(id) { ... }
async function rejectPharmacy(id, reason) { ... }
async function suspendPharmacy(id) { ... }
async function loadAllPharmacies() { ... }
async function loadPlatformStats() { ... }
```

---

## Phase 9 — Existing Pharmacy Migration

The current Red Dot Pharmacy data (users, orders, appointments) needs to be assigned to a pharmacy record.

### 9.1 Migration Script: `migrate_existing_data.py`

```python
# Run after Phase 1 migration
# Creates a "Red Dot Pharmacy" record and assigns all existing data to it

from app import create_app, db
from models import Pharmacy, User, Order, ChatLog, PharmacyAdmin

app = create_app()
with app.app_context():
    # Create the original pharmacy
    reddot = Pharmacy(
        name='Red Dot Pharmacy',
        slug='red-dot',
        owner_name='Red Dot Owner',
        email='admin@reddot.pk',
        address='Shop #69 Ground Floor Silver City Plaza, G11 Markaz',
        city='Islamabad',
        province='ICT',
        theme_key='theme-default',
        status='approved'
    )
    db.session.add(reddot)
    db.session.flush()  # Get ID

    # Assign all existing users, orders, chat_logs to this pharmacy
    User.query.update({'pharmacy_id': reddot.id})
    Order.query.update({'pharmacy_id': reddot.id})
    ChatLog.query.update({'pharmacy_id': reddot.id})

    db.session.commit()
    print(f'Migrated all data to pharmacy id={reddot.id}')
```

---

## Implementation Order (Recommended)

| Phase | What Gets Built | Can Test By |
|---|---|---|
| 1 | Database models + migration | Running migration script, checking DB |
| 2 | Theme CSS system | Viewing `/pharmacy/red-dot` with theme applied |
| 9 | Migrate existing data | Existing admin dashboard still works |
| 3a | `pharmacy_routes.py` (profile page) | Visiting `/pharmacy/red-dot` |
| 4.2 | `pharmacy_profile.html` | Seeing styled pharmacy profile |
| 3b | `pharmacy_registration_routes.py` | Submitting registration form |
| 4.3 | `pharmacy_register.html` | Full registration flow |
| 3c | `pharmacy_admin_routes.py` | Pharmacy admin can log in + see dashboard |
| 4.4 | `pharmacy_admin_dashboard.html` | Pharmacy admin manages their data |
| 3d | Super admin extensions | Super admin can approve pharmacies |
| 4.1 | `platform_home.html` | Platform homepage with search |
| 5 | Services layer | All features using service functions |
| 6 | Location feature | "Near Me" works on homepage |
| 7 | Reviews system | Customers can leave reviews |
| 8 | Admin dashboard extensions | Super admin sees platform stats |

---

## Files Created (New)

```
models.py                          ← MODIFIED (add 3 new models, modify 3 existing)
config.py                          ← MODIFIED (add AVAILABLE_THEMES)
app.py                             ← MODIFIED (register 3 new blueprints)

routes/
  pharmacy_routes.py               ← NEW
  pharmacy_registration_routes.py  ← NEW
  pharmacy_admin_routes.py         ← NEW

services/
  pharmacy_service.py              ← NEW

templates/
  platform_home.html               ← NEW
  pharmacy_profile.html            ← NEW
  pharmacy_register.html           ← NEW
  pharmacy_admin_dashboard.html    ← NEW

static/
  css/themes.css                   ← NEW
  js/platform.js                   ← NEW

migrate_add_pharmacy.py            ← NEW (run once)
migrate_existing_data.py           ← NEW (run once)
```

## Files Modified (Existing — Minimal Changes)

```
models.py                   Add 3 models, add pharmacy_id to 3 models
app.py                      Register 3 new blueprints
config.py                   Add AVAILABLE_THEMES list
routes/order_routes.py      Accept pharmacy_id in order creation
routes/chatbot_routes.py    Accept + save pharmacy_id in chat
routes/admin_routes.py      Add 6 new pharmacy management endpoints
services/auth.py            Add pharmacy admin JWT functions
services/chatbot.py         Add pharmacy_id param to log function
static/js/admin.js          Append pharmacy management functions
templates/admin.html        Add pharmacy management sections to sidebar
```

---

## What Does NOT Change

- All existing patient/doctor login flows
- All existing appointment booking (Google Calendar/Meet)
- All existing medicine catalog and order flow
- All existing admin dashboard features
- All existing chatbot functionality
- Database records for existing users, medicines, orders, appointments

---

## Risk Notes

| Risk | Mitigation |
|---|---|
| Adding `pharmacy_id` column breaks existing queries | Made nullable — existing rows work with NULL |
| Existing admin panel breaks | Only appending new sections; no existing code removed |
| Theme CSS conflicts with existing styles | Themes only applied in pharmacy profile page body class; existing pages unaffected |
| Slug collision on registration | `generate_slug()` checks uniqueness, appends numeric suffix if needed |
| Location permission denied | Graceful fallback to city-based search |

---

*End of Integration Plan*
*Next step: Start with Phase 1 (models) and Phase 9 (existing data migration) to establish the data foundation.*
