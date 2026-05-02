# Red Dot Pharmacy — User Flow & System Map

**Last updated:** 2026-05-02
**Purpose:** Authoritative reference for how every user type signs up, logs in, and operates the system. Read this before changing auth, dashboards, or routes.

---

## 1. System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    React Frontend (Vite)                    │
│  Patient/Public app  ────────────────  Super Admin app      │
│  (port 8080)                            (port 8090)         │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTP (proxied /api, /admin, /static)
┌──────────────────────▼──────────────────────────────────────┐
│                  Flask Backend (port 5000)                  │
│  Auth ─ Pharmacy Admin ─ Super Admin ─ Doctor ─ Chat ─ ...  │
└──────────────────────┬──────────────────────────────────────┘
                       │
              ┌────────▼────────┐
              │  PostgreSQL/    │
              │  SQLite (dev)   │
              └─────────────────┘
                       │
              ┌────────▼────────┐
              │   GCS bucket    │  (uploaded photos, receipts)
              │ pharma-connect- │
              │    uploads      │
              └─────────────────┘
```

**Frontend repo:** `C:\Users\Hassan\Desktop\red  dot\react frontend\ui-ux-polish`
**Backend repo:** `C:\Users\Hassan\Desktop\red  dot\UrduBotBooker`

---

## 2. The Four User Types (At a Glance)

| User Type | Sign-up URL | Login URL | Approval? | Token Key (localStorage) | Dashboard |
|---|---|---|---|---|---|
| **Patient / Customer** | `/` (Sign-up modal) | `/` (Login modal) | ❌ instant | `auth_token` | shop, appointments, AI chat |
| **Pharmacy Owner** | `/pharmacy/register` | `/pharmacy-admin` (login modal) | ✅ super-admin must approve | `pharmacy_admin_token` | `/pharmacy-admin` |
| **Doctor** | Created BY pharmacy owner | `/doctor/dashboard` | ❌ created in approved state | `doctor_token` | `/doctor/dashboard` |
| **Super Admin** | CLI script only | Admin app (port 8090) `/admin` | ❌ manual creation | `super_admin_token` *(see gap §8)* | `/admin` |

> ⚠️ **Pharmacist role does NOT exist as a separate entity.** The schema has `users.role IN ('patient', 'doctor', 'admin')`. There is no `pharmacist` role. Today, anyone working at a pharmacy is either:
>   1. The **pharmacy owner** (login through `pharmacy_admins` table), OR
>   2. A **doctor** added by the owner (login through `users` table with `role='doctor'`).
>
> If "pharmacist" needs to be a distinct role with its own dashboard, it must be added — see `TODO_BEFORE_PRODUCTION.md` §6.

---

## 3. Patient / Customer Flow

### Sign-up
- **Where:** Click "Get Started" on the navbar (any public page) → opens `register` modal in `Navbar.tsx`
- **Endpoint:** `POST /api/auth/register` → `routes/auth_routes.py:50`
- **Inputs:** name, email, phone, password
- **Result:** account created, JWT issued, stored as `auth_token`, modal closes
- **Approval:** none — instant access

### Login
- **Where:** "Login" link in navbar → opens `login` modal
- **Endpoint:** `POST /api/auth/login` → `routes/auth_routes.py:13`
- **Token:** JWT in `auth_token` localStorage key

### What a Customer Can Do

| Feature | Page | Endpoint | Notes |
|---|---|---|---|
| Browse pharmacies | `/pharmacies` (`PharmacyNetwork.tsx`) | `GET /pharmacy/api/list` | City filter, search, "near me" |
| View pharmacy detail | `/pharmacy/:slug` (`PharmacyLanding.tsx`) | `GET /pharmacy/api/{slug}` | Reviews, doctors, medicines |
| Shop for medicine | `/shop` (`Shop.tsx`) | `GET /api/store/medicines` | Add to cart |
| Place order | Cart drawer | `POST /api/orders/` | Creates pending order |
| Upload payment receipt | After order | `POST /api/payments/upload-receipt` | Manual super-admin approval |
| Book a doctor appointment | `/consultation` (`Consultation.tsx`) | `POST /api/appointments/` | Triggers Google Calendar |
| View my appointments | `/appointments` (`Appointments.tsx`) | `GET /api/appointments/` | Status pending/approved/completed |
| AI chat (medical advice) | `/assistant` (`Assistant.tsx`) | `POST /api/chat/medical-chat` | Recommends medicines from DB |
| Web search chat | `/assistant` | `POST /api/chat/web-search` | Gemini + Google Search |
| Voice input (Urdu/English) | `/assistant` | `POST /api/chat/voice` | Speech-to-text |
| Leave pharmacy review | `/pharmacy/:slug` | `POST /pharmacy/api/{slug}/reviews` | After order/appointment |

### Customer Journey (Happy Path)
```
Land on / → see hero + bento grid
   ↓
Click "Patient Portal" card → /shop
   ↓
Click navbar "Login" → modal → sign in OR register
   ↓
Browse pharmacies → /pharmacies
   ↓
Pick pharmacy → /pharmacy/:slug → add medicine to cart
   ↓
Cart drawer → place order → upload receipt
   ↓
Or: book appointment → /consultation → Google Meet link emailed
   ↓
Or: ask AI chatbot anytime → /assistant
```

---

## 4. Pharmacy Owner Flow

### Sign-up (Public)
- **Where:** `/pharmacy/register` (`PharmacyRegister.tsx`)
- **Endpoint:** `POST /register/api/pharmacy` (multipart) → `routes/pharmacy_registration_routes.py:52`
- **Inputs:** pharmacy name, slug, address, city, province, phone, license #, operating hours, owner name, owner photo, pharmacy photo, theme color, **owner email + password**
- **Effect:**
  1. New row in `pharmacies` table with `status='pending'`
  2. New row in `pharmacy_admins` table with hashed password
  3. Photos uploaded to GCS
- **Result:** "Application submitted" screen — owner cannot log in yet
- **Status check:** `GET /register/api/pharmacy/status?email=...` (public, no auth) — owner can poll

### Approval (Super Admin)
*See §6 below.* Until approved, **login fails with HTTP 403** and a "Your application is under review" message.

### Login
- **Where:** Navbar "Pharmacy Login" link OR `/pharmacy-admin` directly (auto-prompts login modal)
- **Endpoint:** `POST /pharmacy-admin/api/login` → `routes/pharmacy_admin_routes.py`
- **Backend gate:** if `pharmacy.status != 'approved'`, returns `403` with reason
- **Token:** JWT in `pharmacy_admin_token` localStorage key

### Dashboard: `/pharmacy-admin` (`PharmacyAdminDashboard.tsx`)

Tabs/sections:

| Tab | What it shows | Key endpoints |
|---|---|---|
| **Stats** | Orders today, revenue, appointments, reviews | `GET /pharmacy-admin/api/stats` |
| **Orders** | All orders for this pharmacy, update status | `GET /pharmacy-admin/api/orders`, `PUT /pharmacy-admin/api/orders/:id/status` |
| **Appointments** | All appointments with this pharmacy's doctors | `GET /pharmacy-admin/api/appointments` |
| **Doctors** | Add/list/delete doctors at this pharmacy | `POST /pharmacy-admin/api/doctors` |
| **Reviews** | Patient reviews + reply to them | `GET /pharmacy-admin/api/reviews`, `POST /pharmacy-admin/api/reviews/:id/reply` |
| **Chat Logs** | Chatbot conversations attributed to this pharmacy | `GET /pharmacy-admin/api/chatlogs` |
| **Settings** | Pharmacy profile, hours, theme | `GET/PUT /pharmacy-admin/api/profile` |

### Adding a Doctor (Important — this is how "staff" gets created)
- **From the pharmacy admin dashboard "Doctors" tab**
- **Endpoint:** `POST /pharmacy-admin/api/doctors`
- **What happens:**
  1. New row in `users` table with `role='doctor'`, `pharmacy_id={this pharmacy}`
  2. Temporary password is set (currently hardcoded `changeme123` — see TODO §3)
  3. Doctor must change it on first login
- **Doctor receives:** their email + temp password (currently no email is sent — manual handoff)

### Pharmacy Owner Journey (Happy Path)
```
/ → click "Register Your Pharmacy" CTA → /pharmacy/register
   ↓
Fill form (incl. owner email + password + photos)
   ↓
"Application submitted — pending approval" screen
   ↓
[wait 1-2 days for super admin approval]
   ↓
Try to login at /pharmacy-admin → "approved" → dashboard loads
   ↓
Add doctors, see orders, manage appointments, reply to reviews
```

---

## 5. Doctor Flow

### Account Creation
- **Doctors do NOT self-sign-up.** The pharmacy owner adds them via `POST /pharmacy-admin/api/doctors`.
- After creation, doctor exists with `users.doctor_password_set = false` and a temp password.

### First-time Login
- **Where:** `/doctor/dashboard` (`DoctorDashboard.tsx`)
- **Endpoint:** `POST /doctor/api/login`
- **First time:** redirect to password setup → `POST /doctor/api/setup-password`
- **Token:** `doctor_token`

### Dashboard: `/doctor/dashboard`

| Section | What it does | Endpoint |
|---|---|---|
| **Profile** | View own info | `GET /doctor/api/profile` |
| **Appointments** | Pending / approved / today / completed | `GET /doctor/api/appointments` |
| **Approve / Decline / Complete** | Per-appointment actions | `POST /doctor/api/appointments/:id/approve|decline|complete` |
| **Time Slots** | Create one-off availability | `POST /doctor/api/time-slots` |
| **Google Calendar** | Connect personal calendar (OAuth) | `GET /auth/google/authorize` |

### Google Calendar Integration
A doctor can **connect their personal Google account** so appointments are synced. This is one of two paths the system uses to create Meet links:
1. **Service Account** (preferred — admin-side config)
2. **Doctor OAuth** (fallback — per-doctor)

→ See `TODO_BEFORE_PRODUCTION.md` §1 for setup.

---

## 6. Super Admin Flow (You)

### Account Creation
- **Manual CLI:** `python create_super_admin.py [email] [password] [name]`
- **Default:** `admin@reddot.com` / `Admin@1234` ⚠️ **change this before production**
- **Stored in:** `admins` table (separate from `users`)

### Login
There are **two admin UIs** — pick one for production (see TODO §7):

#### Option A: New dedicated admin app (port 8090)
- **Start:** `npm run admin` (in `react frontend/ui-ux-polish`)
- **URL:** `http://localhost:8090`
- **Login page:** `admin-app/src/pages/Login.tsx`
- **Token:** stored as `super_admin_token`

#### Option B: Old in-app admin route
- **URL:** `/admin` on the patient app
- **Page:** `src/pages/Admin.tsx`
- **Token:** stored as `admin_token`

**Endpoint (both):** `POST /admin/auth/login` → JWT issued

### Dashboard: `/admin` or `localhost:8090`

| Page | Purpose | Key endpoints |
|---|---|---|
| **Dashboard** | High-level stats | `GET /admin/api/stats` |
| **Pharmacy Applications** | Approve/reject pending pharmacies | `GET /admin/api/pharmacy-applications?status=pending`, `POST /admin/api/pharmacy-applications/:id/approve\|reject` |
| **All Pharmacies** | View, suspend, reactivate any pharmacy | `GET /admin/api/all-pharmacies`, `PUT /admin/api/all-pharmacies/:id/suspend\|reactivate` |
| **Users** | List/edit/disable patient accounts | `GET/POST/PUT /admin/api/users` |
| **Medicines** | Add/edit/delete medicine catalog | `GET/POST/PUT/DELETE /admin/api/medicines` |
| **Orders** | All orders across pharmacies, change status | `GET /admin/api/orders`, `PUT /admin/api/orders/:id/status` |
| **Appointments** | All appointments, force-approve/decline | `GET /admin/api/appointments` |
| **Payments** | Verify uploaded receipts → approve/decline | `GET /admin/api/payments/pending`, `POST /admin/api/payments/:id/verify` |
| **Time Slots** | Bulk-generate doctor slots | `POST /admin/api/availability/generate-slots` |
| **Chat Logs** | All chatbot conversations (audit) | `GET /admin/api/chat-logs` |
| **Banking Details** | Configure JazzCash/EasyPaisa accounts | `GET/PUT /admin/api/banking-details` |

### Super Admin Critical Action: Approving Pharmacies

This is the gate that lets pharmacy owners onto the platform.

```
1. Owner registers at /pharmacy/register
   ↓
2. New row in pharmacies (status=pending)
   ↓
3. Super admin sees it in /admin → "Pharmacy Applications" → status=pending
   ↓
4. Super admin clicks "View" → reviews:
     • License number
     • Photos (owner + pharmacy)
     • Address
     • Operating hours
   ↓
5. Click [Approve]:
     POST /admin/api/pharmacy-applications/:id/approve
     → pharmacy.status = 'approved'
     → pharmacy.approved_by = your admin_id
     → pharmacy.approved_at = now()
   ↓
6. Owner can now login at /pharmacy-admin
```

**Reject path:**
```
Click [Reject] → modal asks for reason
  POST /admin/api/pharmacy-applications/:id/reject  body: { reason: "..." }
  → pharmacy.status = 'rejected'
  → pharmacy.rejection_reason = "..."
  → owner sees reason when polling /register/api/pharmacy/status
```

**Suspend an existing pharmacy** (e.g. policy violation):
```
PUT /admin/api/all-pharmacies/:id/suspend
→ pharmacy.status = 'suspended'
→ owner immediately can't log in
→ pharmacy hidden from public pharmacy list
```

### Super Admin Journey (Daily Operations)
```
Login at localhost:8090 (or /admin)
   ↓
Dashboard → see new applications count
   ↓
Pharmacy Applications → review pending
   • Approve good ones, reject bad ones
   ↓
Payments → check uploaded receipts → approve real ones
   ↓
Orders → check delivery status if escalated
   ↓
Chat Logs → audit any flagged AI conversations
   ↓
Medicines → add new SKUs to catalog
```

---

## 7. The AI Chatbot — Who Uses It

Currently accessible from `/assistant` to **anyone** (logged in or not). The conversation is logged and attributed to:
- `user_id` (if patient is logged in)
- `pharmacy_id` (if accessed from a specific pharmacy's branded page) — currently unwired
- Otherwise anonymous

### Roles that interact with chat
| Role | How they use it | Where |
|---|---|---|
| **Patient/Customer** | Ask medical questions, get medicine recommendations from DB | `/assistant` |
| **Pharmacy Owner** | View customer chat logs scoped to their pharmacy | Dashboard "Chat Logs" tab |
| **Super Admin** | View ALL chat logs, audit flagged conversations | `/admin` "Chat Logs" |
| **Doctor** | Not directly — but appointments may reference chat history (not currently linked) | — |

### Endpoints
- `POST /api/chat/medical-chat` — main medical advice (DB-grounded)
- `POST /api/chat/web-search` — Gemini + Google Search
- `POST /api/chat/voice` — voice input
- `POST /api/chat/transcribe-urdu` / `transcribe-english` — STT
- `POST /api/chat/speak-urdu` / `speak-english` — TTS

### Configuration concerns → see `TODO_BEFORE_PRODUCTION.md` §2

---

## 8. Approval & State Machine — Pharmacy

```
┌─────────┐     register form      ┌──────────┐
│ (none)  │──────────────────────► │ pending  │
└─────────┘                        └────┬─────┘
                                        │
                  super admin: approve  │   super admin: reject
                                  ┌─────┴─────┐
                                  │           │
                                  ▼           ▼
                            ┌──────────┐ ┌──────────┐
                            │ approved │ │ rejected │
                            └────┬─────┘ └──────────┘
                                 │           ▲
                  super admin:   │           │ owner can
                     suspend     │           │ re-register
                                 ▼           │
                            ┌──────────┐     │
                            │suspended │─────┘
                            └──────────┘
                                 │
                  super admin:   │  reactivate
                                 ▼
                            ┌──────────┐
                            │ approved │
                            └──────────┘
```

Owner login behaviour by state:
- **pending** → 403 "Application under review"
- **approved** → login succeeds
- **rejected** → 403 "Application was rejected: [reason]"
- **suspended** → 403 "Pharmacy suspended — contact support"

---

## 9. Database Schema (key tables)

| Table | Purpose |
|---|---|
| `users` | All patients + doctors. `role` discriminator. Doctor-specific cols (specialization, qualification, google_*) are nullable. |
| `pharmacies` | The pharmacy entity itself. Has `status` (pending/approved/rejected/suspended). |
| `pharmacy_admins` | **Separate** auth table for pharmacy owners. Each pharmacy has 1 admin row. |
| `admins` | Super admins. Tiny table, manually populated. |
| `medicines` | Global medicine catalog. **Not per-pharmacy** — see TODO §5. |
| `orders` + `order_items` | Patient orders. Manual payment verification. |
| `appointments` | Doctor appointments. Linked to time_slots, has Google Meet link. |
| `time_slots` | Bookable slots per doctor per day. |
| `doctor_availability` | Weekly recurring schedule (used to generate slots). |
| `pharmacy_reviews` | Patient reviews of pharmacies. Owner can reply. |
| `chat_logs` | All chatbot interactions. Used for audit. |
| `payment_methods` + `banking_details` | Configurable payment options (JazzCash, EasyPaisa, etc.) |

**Tables that DON'T exist but might be needed:** see `TODO_BEFORE_PRODUCTION.md` §6.

---

## 10. Frontend Routes Map (React)

```
Public app (port 8080):
  /                       → PlatformHome (Stitch hero + bento + featured + CTA)
  /pharmacies             → PharmacyNetwork (grid + filters)
  /pharmacy/:slug         → PharmacyLanding (per-pharmacy detail, themed)
  /shop                   → Shop (medicine catalog)
  /consultation           → Consultation (book doctor)
  /appointments           → Appointments (my bookings)
  /assistant              → Assistant (AI chat — standalone, no navbar wrap)
  /pharmacy/register      → PharmacyRegister (owner sign-up)
  /pharmacy-admin         → PharmacyAdminDashboard (owner login + dashboard)
  /admin                  → Admin (legacy super admin page — see §11 gap)
  /doctor/dashboard       → DoctorDashboard
  /video                  → VideoRoom (Google Meet embed)
  *                       → NotFound

Admin app (port 8090, separate Vite build):
  /                       → Login → Dashboard → all admin pages
```

---

## 11. Known Gaps & Inconsistencies

These are listed for awareness — full action items live in `TODO_BEFORE_PRODUCTION.md`.

1. **Pharmacist role missing** — only patient/doctor/admin roles exist. If you want pharmacy-floor staff to log in separately, schema + auth need extension.
2. **Two super admin UIs** — old `/admin` route AND new admin-app on 8090 with different localStorage key names (`admin_token` vs `super_admin_token`). Pick one.
3. **Default super admin password** is `Admin@1234` — must change before launch.
4. **All API keys hardcoded in `.env`** which is checked into git. Move to deployment secrets.
5. **TTS API key hardcoded directly in code** (`routes/chatbot_routes.py:260`) — must be moved to env var.
6. **Google Calendar setup** is incomplete — `service_account_key.json` not configured. Appointments will fail with 503 unless the doctor has done OAuth.
7. **Doctor temp password** for new doctors is hardcoded as `changeme123` — should be randomized + emailed.
8. **No email notifications** at all — pharmacy approval, appointment confirmation, doctor onboarding all happen silently.
9. **No rate limiting** on auth endpoints — brute-force vulnerable.
10. **SHA256 password hashing** — should be bcrypt or argon2.

---

## 12. Production Operating Picture

When the system is live, here's what happens in a typical day:

**Morning:**
- Super admin logs in at `localhost:8090` → checks "Pharmacy Applications" → approves/rejects 0–5 pending pharmacies
- Checks "Payments" → verifies overnight uploaded receipts

**Throughout the day:**
- Patients register, browse, place orders, book appointments
- Pharmacy owners log in, mark orders as "out_for_delivery", reply to reviews
- Doctors log in, approve/decline appointments, create slots
- Chatbot serves anyone (logged in or anonymous)

**Triggers admin attention:**
- New pharmacy applications (super admin approves)
- Uploaded payment receipts (super admin verifies)
- Flagged chat logs (super admin reviews)
- Suspended pharmacies / disputes (super admin moderates)

---

**End of user flow map.** For action items, see `TODO_BEFORE_PRODUCTION.md`.
