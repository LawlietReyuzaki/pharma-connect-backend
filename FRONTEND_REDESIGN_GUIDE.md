# Red Dot Pharmacy — Frontend Redesign Guide
> Full analysis of existing UI, all Flask endpoints, API contracts, and UX enhancement plan.
> Written for the incoming frontend engineer. Do NOT change any backend route URLs or request/response shapes.

---

## 1. Application Overview

**Red Dot Pharmacy** is a full-stack Pakistani healthcare platform with:
- Online medicine store (browse, search, cart, buy-now, order)
- Doctor consultation booking (with Google Calendar + Meet integration)
- AI-powered medical chatbot (English + Urdu, voice input, TTS)
- Admin dashboard (medicines, users, orders, payments, appointments)
- Doctor dashboard (time slots, appointment approval)
- Payment system (Cash-on-delivery, EasyPaisa, JazzCash, Meezan Bank, NayaPay)

**Tech stack:** Flask (Python), SQLite/PostgreSQL, Bootstrap 5, Vanilla JS, JWT auth stored in `localStorage`.

**Brand color:** `#dc3545` (Bootstrap danger red). All UI should respect this primary color.

---

## 2. Page Routes (Flask renders these templates)

| URL | Template | Description |
|-----|----------|-------------|
| `GET /` | `index.html` | Landing page — hero, services, medicines, consultation, about, chatbot widget |
| `GET /shop` | `shop.html` | Full medicine store with category-based browsing |
| `GET /consultation` | `consultation.html` | Doctor booking form + doctor grid |
| `GET /appointments` | `appointments.html` | Patient's appointment list (standalone navbar) |
| `GET /assistant` | `assistant.html` | Full-page AI chatbot (hides base navbar/footer) |
| `GET /admin` | `admin.html` | Admin dashboard (auth-guarded via JS) |
| `GET /video` | `video.html` | Video room (Google Meet redirect) |
| `GET /doctor/dashboard` | `doctor_dashboard.html` | Doctor's private dashboard |

All templates extend `base.html` except `appointments.html` (standalone) and `assistant.html` (full-page override).

---

## 3. Complete API Endpoint Reference

> **Auth:** All protected endpoints require `Authorization: Bearer <jwt_token>` header.
> **Token storage:** `localStorage.getItem('auth_token')` and `localStorage.getItem('user')`.

---

### 3.1 Authentication — `/api/auth/`

| Method | URL | Auth | Body / Params | Response |
|--------|-----|------|---------------|----------|
| `POST` | `/api/auth/login` | No | `{email, password}` | `{success, token, user:{id,name,email,role,phone}}` |
| `POST` | `/api/auth/register` | No | `{name, email, phone, password}` | `{success, token, user:{...}}` |
| `POST` | `/api/auth/verify` | Bearer | — | `{valid, user:{...}}` |
| `PUT` | `/api/auth/profile` | Bearer | `{name?, phone?, password?}` | `{success, user:{...}}` |

**Login flow:** POST → receive token → store in `localStorage('auth_token')` → store user object in `localStorage('user')`.

---

### 3.2 Medicine Store — `/api/store/`

| Method | URL | Auth | Params | Response |
|--------|-----|------|--------|----------|
| `GET` | `/api/store/medicines` | No | `?category=&search=&status=in_stock&limit=50&offset=0` | `{medicines:[{id,name,chemical,description,price,image_path,status,stock_quantity,category}], total_count}` |
| `GET` | `/api/store/medicines/<id>` | No | — | `{medicine:{...}}` |
| `POST` | `/api/store/medicines` | Bearer (admin) | `{name,price,chemical?,description?,image_path?,status?,stock_quantity?,category?}` | `{success, medicine:{...}}` |
| `PUT` | `/api/store/medicines/<id>` | Bearer (admin) | Any medicine fields | `{success, medicine:{...}}` |
| `DELETE` | `/api/store/medicines/<id>` | Bearer (admin) | — | `{success, message}` |
| `GET` | `/api/store/categories` | No | — | `{categories:[string], categories_with_counts:[{name,count}]}` |
| `GET` | `/api/store/search` | No | `?q=&min_price=&max_price=&category=` | `{results:[{id,name,chemical,price,category,image_path}], count}` |

**Image path:** medicines use `image_path` field from API; fallback is `/static/images/default-medicine.png`.

---

### 3.3 Orders — `/api/orders/`

| Method | URL | Auth | Body / Params | Response |
|--------|-----|------|---------------|----------|
| `POST` | `/api/orders/` | Bearer | `{address, phone, items:[{medicine_id,quantity}], payment_method?, delivery_fee?, notes?, payment_receipt_path?}` | `{success, order:{id,total_amount,delivery_fee,status,items,estimated_delivery}}` |
| `GET` | `/api/orders/` | Bearer | `?status=&limit=20&offset=0` | `{orders:[{...}], total_count}` |
| `GET` | `/api/orders/<id>` | Bearer | — | `{order:{id,customer,address,total_amount,status,payment_method,payment_status,items,created_at}}` |
| `PUT` | `/api/orders/<id>/status` | Bearer (admin) | `{status, notes?}` | `{success, order:{...}}` |
| `GET` | `/api/orders/stats` | Bearer (admin) | — | `{stats:{total_orders,pending_orders,processing_orders,delivered_orders,total_revenue,recent_orders}}` |
| `POST` | `/api/orders/cart/calculate` | No | `{items:[{medicine_id,quantity}], delivery_fee?}` | `{calculation:{items,subtotal,delivery_fee,total,item_count}}` |

**Order statuses:** `pending`, `processing`, `out_for_delivery`, `delivered`, `cancelled`
**Payment methods (slug):** `cash_on_delivery`, `easypaisa`, `jazzcash`, `meezan_bank`, `nayapay`
**Delivery fee:** PKR 100 default.

---

### 3.4 Appointments — `/api/appointments/`

| Method | URL | Auth | Body / Params | Response |
|--------|-----|------|---------------|----------|
| `GET` | `/api/appointments/doctors` | No | — | `{doctors:[{id,name,email,phone,specialization,qualification,experience_years,current_hospital,upcoming_appointments}]}` |
| `GET` | `/api/appointments/available-slots/<doctor_id>` | No | `?date=YYYY-MM-DD` | `{slots:[{slot_id,start_time,end_time,display_time,available}]}` |
| `POST` | `/api/appointments/` | Bearer | `{doctor_id, slot_id, symptoms, note?}` | `{success, google_meet_link, appointment:{id,doctor_name,start_time,end_time,status,google_meet_link}}` |
| `GET` | `/api/appointments/` | Bearer | `?status=&limit=10` | `{appointments:[{id,patient_name,doctor_name,doctor_specialization,starts_at,status,approval_status,symptoms,google_meet_link}]}` |
| `GET` | `/api/appointments/<id>` | Bearer | — | `{appointment:{id,patient,doctor,start_time,end_time,status,symptoms,google_meet_link}}` |
| `PUT` | `/api/appointments/<id>/status` | Bearer (doctor/admin) | `{status, note?}` | `{success, appointment:{...}}` |
| `POST` | `/api/appointments/schedule-appointment` | No | `{doctorEmail,patientEmail,start,end?,reason?}` | `{success,google_meet_link,appointment:{...}}` |

**Approval statuses:** `pending`, `approved`, `declined`
**Appointment statuses:** `scheduled`, `ongoing`, `completed`, `cancelled`

---

### 3.5 Chatbot — `/api/chat/`

| Method | URL | Auth | Body / Params | Response |
|--------|-----|------|---------------|----------|
| `POST` | `/api/chat/` | No | `{message, session_id?, prefer_urdu?, user_id?, include_wiki?}` | `{success, message, flagged, needs_doctor, suggested_medicines, wiki?:{title,page_url,summary,images}}` |
| `POST` | `/api/chat/medical-chat` | No | `{message, lang?, session_id?, user_id?, include_wiki?}` | `{success, message, language, flagged, needs_doctor, disclaimer, wiki?:{...}, medicines?}` |
| `POST` | `/api/chat/voice` | No | `{transcript, session_id?, prefer_urdu?, user_id?}` | `{success, transcript, message, flagged, needs_doctor}` |
| `GET` | `/api/chat/history/<session_id>` | No | — | `{history:[{message,response,timestamp,flagged}]}` |
| `GET` | `/api/chat/sessions` | Bearer | — | `{sessions:[{session_id,created_at,preview}]}` |
| `POST` | `/api/chat/transcribe-urdu` | No | multipart `audio` file | `{success, transcript}` |
| `POST` | `/api/chat/transcribe-english` | No | multipart `audio` file | `{success, transcript}` |
| `POST` | `/api/chat/translate` | No | `{text, target_lang}` (target: `en` or `ur`) | `{success, original, translated, target_lang}` |
| `POST` | `/api/chat/speak-english` | No | `{text}` | audio/mpeg file (MP3) |
| `POST` | `/api/chat/speak-urdu` | No | `{text}` | audio/mpeg file (MP3) |

**Wiki data** is returned inline in each chat response when available.
**Language auto-detection** handles English/Urdu mixing automatically.

---

### 3.6 Payments — `/api/payments/`

| Method | URL | Auth | Body / Params | Response |
|--------|-----|------|---------------|----------|
| `GET` | `/api/payments/methods` | No | — | `{payment_methods:[{id,name,slug,logo_path,requires_receipt,account_title,account_number,account_details}]}` |
| `POST` | `/api/payments/upload-receipt` | Bearer | multipart `receipt` file (PNG/JPG/PDF ≤5MB) | `{success, receipt_path}` |
| `POST` | `/api/payments/reupload-receipt/<order_id>` | Bearer | multipart `receipt` file | `{success, receipt_path}` |
| `GET` | `/api/payments/banking-details` | No | — | `{banking_details:{bank_name,account_title,account_number,iban,easypaisa_number,jazzcash_number,additional_instructions}}` |
| `POST` | `/api/payments/init-methods` | No | — | One-time setup, initializes default methods |

**Payment logos** are at `/static/images/payment-logos/<method>.png`.

---

### 3.7 Doctor Routes — `/doctor/`

| Method | URL | Auth | Body / Params | Response |
|--------|-----|------|---------------|----------|
| `GET` | `/doctor/dashboard` | — | — | Renders `doctor_dashboard.html` |
| `POST` | `/doctor/api/login` | No | `{email, password}` | `{success, token, doctor:{...}}` |
| `POST` | `/doctor/api/setup-password` | No | `{email, password, confirm_password}` | `{success, token, doctor:{...}}` |
| `GET` | `/doctor/api/profile` | Bearer | — | `{doctor:{id,name,email,phone,specialization,qualification,experience_years,current_hospital}}` |
| `PUT` | `/doctor/api/profile` | Bearer | `{name?,phone?,specialization?,qualification?,experience_years?,current_hospital?,password?}` | `{success, doctor:{...}}` |
| `GET` | `/doctor/api/appointments` | Bearer | `?status=all/pending/scheduled/completed` | `{appointments:[...], stats:{total,pending,approved}}` |
| `POST` | `/doctor/api/appointments/<id>/approve` | Bearer | — | `{success, message}` |
| `POST` | `/doctor/api/appointments/<id>/decline` | Bearer | `{reason?}` | `{success, message}` |
| `POST` | `/doctor/api/appointments/<id>/complete` | Bearer | — | `{success, message}` |
| `GET` | `/doctor/api/time-slots` | Bearer | `?date=YYYY-MM-DD` | `{slots:[{id,appointment_date,start_time,end_time,is_booked,can_delete}], stats:{total,available,booked}}` |
| `POST` | `/doctor/api/time-slots` | Bearer | `{appointment_date, start_time (HH:MM), end_time (HH:MM)}` | `{success, slot:{...}, google_calendar:{...}}` |
| `DELETE` | `/doctor/api/time-slots/<id>` | Bearer | — | `{success, message}` |

---

### 3.8 Admin Routes — `/admin/`

| Method | URL | Auth | Description |
|--------|-----|------|-------------|
| `GET` | `/admin/api/stats` | Admin JWT | Dashboard stats (users, orders, appointments, revenue) |
| `GET` | `/admin/api/users` | Admin JWT | List all users |
| `GET` | `/admin/api/users/<id>` | Admin JWT | Get user details |
| `POST` | `/admin/api/users` | Admin JWT | Create user (doctor/patient/admin) |
| `PUT` | `/admin/api/users/<id>` | Admin JWT | Update user |
| `DELETE` | `/admin/api/users/<id>` | Admin JWT | Delete user |
| `GET` | `/admin/api/medicines` | Admin JWT | List medicines with full details |
| `POST` | `/admin/api/medicines` | Admin JWT | Add medicine with image upload |
| `PUT` | `/admin/api/medicines/<id>` | Admin JWT | Update medicine |
| `DELETE` | `/admin/api/medicines/<id>` | Admin JWT | Delete/discontinue medicine |
| `GET` | `/admin/api/orders` | Admin JWT | List all orders |
| `PUT` | `/admin/api/orders/<id>/status` | Admin JWT | Update order status |
| `GET` | `/admin/api/appointments` | Admin JWT | List all appointments |
| `PUT` | `/admin/api/appointments/<id>/approve` | Admin JWT | Approve appointment |
| `PUT` | `/admin/api/appointments/<id>/decline` | Admin JWT | Decline appointment |
| `GET` | `/admin/api/payments/pending` | Admin JWT | List pending payment receipts |
| `POST` | `/admin/api/payments/<id>/approve` | Admin JWT | Approve payment receipt |
| `POST` | `/admin/api/payments/<id>/decline` | Admin JWT | Decline payment with reason |
| `GET` | `/admin/api/banking-details` | Admin JWT | Get banking details |
| `PUT` | `/admin/api/banking-details` | Admin JWT | Update banking details |
| `GET` | `/admin/api/time-slots` | Admin JWT | List all doctor time slots |
| `POST` | `/admin/api/time-slots` | Admin JWT | Create time slot for any doctor |
| `DELETE` | `/admin/api/time-slots/<id>` | Admin JWT | Delete time slot |
| `GET` | `/admin/api/chat-logs` | Admin JWT | View all chatbot logs |
| `GET` | `/admin/api/chat-logs/<session_id>` | Admin JWT | View specific session |

**Admin auth** is separate from patient auth: uses a different `Admin` model with admin-specific JWT stored also in `localStorage` under a different key. Admin login is at `/admin/auth/login`.

---

### 3.9 Google OAuth Routes

| Method | URL | Description |
|--------|-----|-------------|
| `GET` | `/auth/google/authorize` | Initiate Google OAuth for patient |
| `GET` | `/auth/google/callback` | Google OAuth callback |
| `GET` | `/auth/google/status` | Check patient's Google auth status |
| `GET` | `/auth/google/revoke` | Revoke patient's Google auth |
| `GET` | `/doctor/oauth/authorize` | Initiate Google OAuth for doctor |
| `GET` | `/doctor/oauth/callback` | Doctor Google OAuth callback |

---

## 4. Current Template Inventory & Issues

### `base.html`
- Navbar: fixed-top, dark red, has Login/Register buttons, user dropdown, cart button
- Modals embedded: Login, Register, Doctor Login, Doctor Password Setup, Admin Login, Shopping Cart
- JS loaded: `main.js`, `chatbot.js`, `voice.js`
- **Issues:** Navbar is not collapsible (no hamburger toggle for mobile), dropdown uses `style="display:none"` toggled by JS instead of Bootstrap classes

### `index.html` (Landing page)
- Sections: Hero, Services (4 cards), Medicine Store (with search + category filter + grid), Consultation (form + doctor grid), About, AI CTA banner, Chat widget
- **Issues:** Hero image is external Unsplash URL (no CDN fallback), medicines and doctors loaded via AJAX on DOMContentLoaded, section fade-in animation sets `opacity:0` on load which flickers

### `shop.html`
- Full store: Hero, Search bar, Category cards grid, All-categories view, Products grid, Why-choose-us, CTA
- State management via JS: `allMedicines`, `allCategories`, `currentShopCategory`
- **Issues:** `medicinesGrid` ID mismatch (filterShopByCategory targets `medicinesGrid` but grid ID is `shopMedicineGrid`), search is client-side only

### `consultation.html`
- Booking form, doctor grid, How-it-works steps, Benefits
- **Issues:** Duplicates Login/Register modals from `base.html` (two separate modal instances), uses `alert()` for errors throughout

### `appointments.html`
- Standalone page (does NOT extend `base.html`), own navbar, filter tabs, appointment cards
- **Issues:** References `app.showLogin()` etc. which depends on `PharmacyApp` class from `main.js`, broken image reference `url_for('static', filename='images/logo.png')` (logo.png doesn't exist)

### `assistant.html`
- Full-page ChatGPT-style layout with sidebar for chat sessions
- Hides base navbar/footer via CSS `display: none`
- Has Urdu font (Noto Nastaliq), Wikipedia panel, voice input
- **Issues:** Large (59KB), inline styles mixed with external CSS

### `admin.html`
- Admin dashboard with tabs: Overview, Users, Medicines, Orders, Appointments, Payments, Time Slots, Chat Logs
- **Issues:** 101KB+ file, all JS inline, no separation of concerns, uses `alert()` and `confirm()` throughout

### `doctor_dashboard.html`
- Doctor's interface: appointment management, time slot creation

---

## 5. JavaScript Architecture

### `main.js` — `PharmacyApp` class
The entire frontend app is a single class instantiated as `window.app = new PharmacyApp()`. Key methods:
- `app.addToCart(medicineId)` — adds to cart (cart stored in `localStorage`)
- `app.viewMedicine(id)` — opens medicine detail modal, calls `GET /api/store/medicines/<id>`
- `app.buyNow(id)` — opens cart with single item then checkout
- `app.showCart()` — opens cart modal
- `app.showLogin()` / `app.showRegister()` — shows login/register modals
- `app.logout()` — clears localStorage, reloads
- `app.placeOrder()` — calls `POST /api/orders/` with cart contents
- `loadMedicines()` — calls `GET /api/store/medicines?limit=500`
- `loadDoctors()` — calls `GET /api/appointments/doctors`
- `loadTimeSlots(doctorId, date)` — calls `GET /api/appointments/available-slots/<id>?date=`

### `chatbot.js`
- `sendMessage()` — calls `POST /api/chat/`
- `toggleVoiceInput()` — starts/stops browser speech recognition

### `voice.js`
- Handles audio recording, calls `POST /api/chat/transcribe-urdu` or `transcribe-english`
- Calls `POST /api/chat/speak-urdu` or `speak-english` for TTS

### `wikiDisplay.js`
- Renders Wikipedia data panel in the assistant page

---

## 6. UI/UX Enhancement Plan

### 6.1 Design System (Global)

**Keep:** Red (#dc3545) as primary, Bootstrap 5, Font Awesome icons, Inter + Poppins fonts.

**Add:**
- CSS custom properties for consistent spacing, shadows, radius
- A proper `404.html` and error page (currently same `403.html` used for all errors)
- Toast notifications to replace ALL `alert()` calls (Bootstrap 5 Toast component)
- Smooth skeleton loading states instead of spinner-only
- Consistent card component with uniform padding, radius (12px), and shadow depth

---

### 6.2 Navbar (`base.html`)
**Problems:** No mobile hamburger collapse, auth state managed by JS `display` toggling.

**Fix:**
- Add proper `navbar-toggler` button with `data-bs-toggle="collapse"`
- Add `data-bs-target="#navbarNav"` and make nav collapsible
- Use Bootstrap `d-none`/`d-flex` classes instead of inline `style="display:none"`
- Add active state to current nav item via Jinja2 `request.path` comparison
- Sticky behavior is fine (keep `fixed-top`, adjust body padding-top to `~72px`)

---

### 6.3 Landing Page (`index.html`)
**Problems:** Unsplash images (CORS risk), section opacity flicker, no mobile optimization.

**Fix:**
- Replace Unsplash images with `/static/images/` local assets or use `onerror` fallback properly
- Remove JS-driven `opacity:0` fade-in on sections — use CSS `@keyframes` with `animation-fill-mode: backwards`
- Medicine grid: show skeleton cards (3x) while loading
- Consultation form: show inline validation messages, not browser-default HTML5 popups
- Chat widget: position should be `position: fixed; bottom: 24px; right: 24px` — ensure it doesn't cover other content on mobile

---

### 6.4 Shop Page (`shop.html`)
**Problems:** ID mismatch bug, client-side-only search, no pagination UI.

**Fix:**
- Fix `medicinesGrid` → `shopMedicineGrid` mismatch in `filterShopByCategory()`
- Search should call `GET /api/store/search?q=` (server-side) for accuracy
- Add price range filter UI (min/max inputs) that passes `?min_price=&max_price=` to search endpoint
- Category filter pills should be scrollable on mobile (horizontal scroll)
- Medicine cards: standardize to `col-xl-3 col-lg-4 col-md-6 col-12`
- Add "Out of Stock" visual overlay on medicine card image instead of just badge

---

### 6.5 Consultation Page (`consultation.html`)
**Problems:** Duplicated modals, alert() usage, no feedback after booking.

**Fix:**
- Remove duplicate Login/Register modals — rely on `base.html` modals and call `showLogin()` from there
- Replace `alert()` with Bootstrap Toast for all user feedback
- After successful booking, show appointment details in a proper modal (not alert)
- Doctor grid: add specialization badge, rating stars placeholder, "Next Available" badge
- Time slot grid: use a better visual (colored pills with hover state) not just plain divs

---

### 6.6 Appointments Page (`appointments.html`)
**Problems:** Standalone page with inconsistent navbar, broken logo reference.

**Fix:**
- Migrate to extend `base.html` — use `{% extends "base.html" %}` and `{% block content %}`
- Fix logo: either add logo.png to `/static/images/` or remove `<img>` and use text logo like base.html
- Filter tabs: keep the pill-tab design but add count badges to each tab
- Appointment cards: add a "Copy Meet Link" button, show appointment status timeline
- Add empty state illustration (inline SVG) when no appointments exist
- Google Calendar integration status banner: move inside a collapsible alert

---

### 6.7 AI Assistant Page (`assistant.html`)
**Problems:** 59KB monolithic file, hides base elements via CSS hack.

**Fix:**
- Keep the full-page layout — this is correct UX for a chat interface
- Improve sidebar: show session preview text, allow session deletion
- Message bubbles: use `marked.js` for markdown rendering (already loaded), add copy button on bot messages
- Wikipedia panel: move to a slide-in drawer on mobile instead of side column
- Voice recording: add audio visualizer (animated waveform bars) during recording
- Language toggle: persistent UI button (EN/UR) that sets `lang` param for all requests
- TTS: Add speaker button per bot message to call `/api/chat/speak-english` or `/api/chat/speak-urdu`

---

### 6.8 Admin Dashboard (`admin.html`)
**Problems:** 101KB monolithic file, all logic inline.

**Fix:**
- Split JS into separate files: `admin_medicines.js`, `admin_orders.js`, `admin_appointments.js`, etc.
- Replace all `alert()` / `confirm()` with Bootstrap Toast and confirmation modals
- Stats cards: add sparkline chart (Chart.js or inline SVG) for trend visualization
- Orders table: add color-coded status badges, sortable columns
- Payment receipts: add image preview lightbox before approve/decline
- Medicine management: add bulk upload CSV capability
- Time slot management: calendar view (month/week grid) instead of flat list

---

### 6.9 Doctor Dashboard (`doctor_dashboard.html`)
**Fix:**
- Appointment request cards: show patient details, symptom summary, one-click approve/decline
- Time slot creation: add a visual weekly calendar where doctor clicks to add slots
- Add "Today's Schedule" section at the top

---

## 7. Cart & Checkout Flow (Connection Strings)

```
Cart (localStorage) → showCart modal
  │
  ├── placeOrder() [Cash on Delivery]
  │     POST /api/orders/
  │     body: {address, phone, items, payment_method:"cash_on_delivery"}
  │
  └── placeOrder() [Online Payment]
        1. GET /api/payments/methods → show payment options
        2. User selects method, transfers money
        3. POST /api/payments/upload-receipt (multipart, field name: "receipt")
           → returns {receipt_path}
        4. POST /api/orders/
           body: {address, phone, items, payment_method:"easypaisa", payment_receipt_path:"/static/uploads/receipts/..."}
```

---

## 8. Auth Flow (Connection Strings)

```
Patient Login:
  POST /api/auth/login → {token, user}
  localStorage.setItem('auth_token', token)
  localStorage.setItem('user', JSON.stringify(user))

Patient Register:
  POST /api/auth/register → {token, user}
  (same localStorage storage)

Doctor Login:
  POST /doctor/api/login → {token, doctor}
  localStorage.setItem('auth_token', token)
  localStorage.setItem('user', JSON.stringify(doctor))

Doctor First-Time Password Setup:
  POST /doctor/api/setup-password → {token, doctor}

Admin Login:
  POST /admin/auth/login → {token, admin}
  (stored separately)

Token Verification (on page load):
  POST /api/auth/verify
  headers: {Authorization: "Bearer <token>"}
  → {valid:true, user:{role:"patient"|"doctor"|"admin"}}
```

---

## 9. Static Assets Reference

```
/static/css/style.css            — Main stylesheet
/static/css/admin.css            — Admin-specific styles
/static/js/main.js               — PharmacyApp class (core frontend logic)
/static/js/chatbot.js            — Chat widget JS
/static/js/voice.js              — Voice recording + TTS
/static/js/wikiDisplay.js        — Wikipedia panel renderer
/static/js/doctor_dashboard.js  — Doctor dashboard JS

/static/images/default-medicine.png     — Medicine fallback image
/static/images/medicines/               — Pre-seeded medicine images
/static/images/payment-logos/           — EasyPaisa, JazzCash, Meezan, NayaPay, COD logos
/static/uploads/medicines/              — Admin-uploaded medicine images
/static/uploads/receipts/               — User-uploaded payment receipts
```

---

## 10. Critical Rules for New Frontend

1. **Never change API endpoint URLs** — backend routes are fixed.
2. **Always send `Authorization: Bearer <token>` header** for protected routes.
3. **Cart is localStorage-based** — `localStorage.getItem('cart')` holds `[{id, quantity}]`.
4. **Medicine image fallback:** always add `onerror="this.src='/static/images/default-medicine.png'"`.
5. **Doctor vs Patient auth** — both use `auth_token` key in localStorage but doctor token carries `role:"doctor"`.
6. **Admin is a separate auth system** — uses `Admin` model, separate login at `/admin/auth/login`.
7. **Urdu text** — use `font-family: 'Noto Nastaliq Urdu'`, `direction: rtl`, `text-align: right` for Urdu content.
8. **All currency is PKR** — display as `PKR 100` (no decimal for round numbers).
9. **Delivery fee is always PKR 100** (hardcoded default in backend).
10. **Google Meet links** are only created when appointment is approved — do not show join button for pending appointments.
11. **Payment receipts** must be PNG/JPG/JPEG/PDF, max 5MB.
12. **Time slots** use ISO datetime strings from backend — always use `new Date(isoString)` to parse.

---

## 11. Recommended Tech Additions for Redesign

| Need | Recommendation |
|------|---------------|
| Toast notifications | Bootstrap 5 Toast (already loaded) |
| Charts (admin) | Chart.js via CDN |
| Rich text in chat | marked.js (already loaded in assistant.html) |
| Date picker | Flatpickr (lightweight, mobile-friendly) |
| Image lightbox | GLightbox or Bootstrap's own modal |
| Loading skeletons | Pure CSS skeleton shimmer |
| Urdu font | Noto Nastaliq Urdu (already in assistant.html, add to base.html) |
| Form validation | Custom Bootstrap validation classes (`is-invalid`, `invalid-feedback`) |
| Confirm dialogs | Bootstrap modal with confirm/cancel (replace all `confirm()`) |

---

*Last updated: 2026-03-10 | Analyzed by Claude Code*
