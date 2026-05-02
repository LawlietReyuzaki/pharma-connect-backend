# Google Calendar + Meet — Setup Plan

**Goal:** patient books appointment → Google Calendar event auto-created in doctor's & patient's calendars → both get a Google Meet link.

**Status of code:** 90% built and well-architected. The plumbing is solid. What's missing is the **Google Cloud setup** + **2 env vars** + **1 small code tweak** (optional but recommended).

This document has 4 parts:
1. **Decide which setup path fits you** (workspace vs no workspace)
2. **Copy-paste prompt for the Claude agent in Google Cloud Console** to do the GCP-side configuration
3. **Local app fixes** — what to change in the codebase / env after the GCP agent finishes
4. **End-to-end test** — verify it works

---

## Part 1 — Decide Your Setup Path

The current code uses **domain-wide delegation**, which means the service account needs to *impersonate* a real human user to create calendar events on their behalf. This has a hard requirement:

> **Domain-wide delegation only works on Google Workspace accounts** (`@yourdomain.com` style), NOT on free `@gmail.com` accounts.

So you have three real options:

### Path A — Google Workspace + Service Account *(recommended for production)*
- **Cost:** ~$6–12/user/month for Workspace (or use existing if you have one)
- **What it does:** Service account impersonates each doctor's workspace email → creates event in their calendar with Meet link → patient added as attendee, gets calendar invite
- **Doctor email constraint:** doctors must have `@yourworkspacedomain.com` emails (e.g., `dr.ahmed@reddotpharmacy.com`)
- **Patient email:** any email works (gmail.com, yahoo.com, etc.) — they just receive an invite

### Path B — Google Workspace + Single Scheduler Account *(simpler, more flexible)*
- **Cost:** 1 Workspace seat (~$6/mo for one `scheduler@yourdomain.com` user)
- **What it does:** Service account always impersonates ONE Workspace user (`scheduler@reddotpharmacy.com`). All calendar events created on the scheduler's calendar. Both doctor + patient added as attendees and get invites.
- **Doctor email constraint:** none — any email works for both doctor and patient
- **Code change required:** small — see Part 3 §3
- **Trade-off:** doctor doesn't see events on their *own* calendar by default — they only see them in the email invite (until they accept). For most doctors this is fine.

### Path C — No Workspace, Doctor OAuth fallback
- **Cost:** free
- **What it does:** Each doctor must click "Connect Google Calendar" once → authorizes via OAuth → app stores their refresh token → creates events on their personal calendar
- **Friction:** every doctor onboards manually
- **Code state:** already coded as fallback in `services/doctor_oauth_service.py`, but `GOOGLE_OAUTH_CLIENT_ID/SECRET` not yet set
- **Limitation:** if a doctor never connects, their patients can't book

### My recommendation
**Path B** — get one Workspace seat, set up one `scheduler@yourdomain.com`, all events flow through it. Simplest mental model, works with any doctor/patient email, lowest ongoing maintenance.

If you want zero monthly cost, do **Path C**.

If you already have a Workspace and your doctors use it, do **Path A** (no code changes needed).

---

## Part 2 — Prompt for the Claude Agent in Google Cloud Console

Open Google Cloud Console → click the Claude / Cloud Shell icon → start a Claude session. Paste this prompt verbatim. Replace the bracketed `[…]` values with yours.

> ⚠️ **Before pasting:** decide which path you chose (A, B, or C). The prompt below covers Path A and B. For Path C, skip this entirely — you instead create OAuth client credentials, not a service account; jump to Part 3 §6.

---

```
You are helping me set up a Google Cloud service account so my Flask app can create Google Calendar events with Google Meet links on behalf of users.

Project context: 
- I run a multi-pharmacy healthcare app called "Red Dot Pharmacy"
- Backend is Flask, deployed at [your domain or Replit URL]
- I have a Google Workspace at the domain: [yourdomain.com]
- My Workspace super admin email is: [admin@yourdomain.com]
- I want appointments booked in my app to auto-create Google Calendar events with Meet links
- I will paste the resulting service account JSON into my app's environment as GOOGLE_SERVICE_ACCOUNT_KEY

Please do the following, in order, and tell me when each step is done. Stop and ask if anything fails.

═══════════════════════════════════════════════════════════════
STEP 1 — Pick or create a GCP project
═══════════════════════════════════════════════════════════════
- Run: gcloud projects list
- If a project named "red-dot-pharmacy" or similar exists, use it. Tell me the project ID.
- If not, create one: gcloud projects create red-dot-pharmacy-prod --name="Red Dot Pharmacy"
- Set it as the active project: gcloud config set project [project-id]
- Note the project ID for later. Tell me what it is.

═══════════════════════════════════════════════════════════════
STEP 2 — Link a billing account
═══════════════════════════════════════════════════════════════
- Run: gcloud billing accounts list
- If no billing account is linked, ask me to set one up at https://console.cloud.google.com/billing
  (Calendar API needs a billing-linked project even though calls are free at this volume)
- Link: gcloud billing projects link [project-id] --billing-account=[billing-account-id]

═══════════════════════════════════════════════════════════════
STEP 3 — Enable required APIs
═══════════════════════════════════════════════════════════════
Run:
  gcloud services enable calendar-json.googleapis.com
  gcloud services enable admin.googleapis.com
  gcloud services enable iam.googleapis.com
  gcloud services enable iamcredentials.googleapis.com

Verify with: gcloud services list --enabled | grep -E "(calendar|admin|iam)"

═══════════════════════════════════════════════════════════════
STEP 4 — Create the service account
═══════════════════════════════════════════════════════════════
Run:
  gcloud iam service-accounts create reddot-calendar-scheduler \
    --display-name="Red Dot Calendar Scheduler" \
    --description="Creates calendar events + Meet links for patient appointments"

Get the email of the account just created:
  gcloud iam service-accounts list

Tell me the service account email — it will look like:
  reddot-calendar-scheduler@[project-id].iam.gserviceaccount.com

═══════════════════════════════════════════════════════════════
STEP 5 — Generate a JSON key for the service account
═══════════════════════════════════════════════════════════════
Run:
  gcloud iam service-accounts keys create ~/reddot-calendar-key.json \
    --iam-account=reddot-calendar-scheduler@[project-id].iam.gserviceaccount.com

Then cat the file and SHOW ME THE FULL JSON contents. I need to copy this into my app's GOOGLE_SERVICE_ACCOUNT_KEY environment variable.

After showing it, tell me to delete the local file with:
  rm ~/reddot-calendar-key.json

(I'll have it stored in my app's secrets after that — no need to keep it on disk.)

═══════════════════════════════════════════════════════════════
STEP 6 — Note the OAuth Client ID for domain-wide delegation
═══════════════════════════════════════════════════════════════
Run:
  gcloud iam service-accounts describe reddot-calendar-scheduler@[project-id].iam.gserviceaccount.com --format="value(uniqueId)"

This is the "Client ID" I'll need in the next step. It's a long numeric string. Tell me what it is.

═══════════════════════════════════════════════════════════════
STEP 7 — Manual step: enable domain-wide delegation (Workspace Admin)
═══════════════════════════════════════════════════════════════
This MUST be done by me as Workspace super admin in the browser. Give me these exact instructions:

1. Open: https://admin.google.com → Security → Access and data control → API controls → Manage Domain Wide Delegation
2. Click "Add new"
3. Client ID: paste the unique ID from Step 6
4. OAuth scopes (paste exactly, comma-separated, no spaces):
   https://www.googleapis.com/auth/calendar,https://www.googleapis.com/auth/calendar.events
5. Click "Authorize"

Confirm when I tell you I've done this.

═══════════════════════════════════════════════════════════════
STEP 8 — Final summary
═══════════════════════════════════════════════════════════════
Print a summary block I can save:
  - GCP Project ID:
  - Service Account Email:
  - Service Account Unique ID (Client ID):
  - JSON key — already pasted above
  - Domain-wide delegation: confirmed by user
  - Scopes authorized: calendar, calendar.events

Then tell me: "Now go to your app, paste the JSON into GOOGLE_SERVICE_ACCOUNT_KEY env var, and run the smoke test endpoint /api/appointments/check-calendar-setup"
```

---

## Part 3 — What to Fix on the App Side

### 3.1 — Set the env var (REQUIRED, after the GCP agent finishes)

The agent will give you a JSON blob. Take it and set it as one env variable:

**Local development** (`.env` file):

```bash
# Remove or comment out the file-path approach (line 7 in your .env):
# GOOGLE_APPLICATION_CREDENTIALS=C:\Users\Hassan\Desktop\red  dot\UrduBotBooker\service_account_key.json

# Replace with the full JSON as one line (escape internal newlines in the private_key):
GOOGLE_SERVICE_ACCOUNT_KEY={"type":"service_account","project_id":"…","private_key":"-----BEGIN PRIVATE KEY-----\n…\n-----END PRIVATE KEY-----\n","client_email":"reddot-calendar-scheduler@…","…":"…"}
```

> 💡 **Easier alternative:** save the JSON as `service_account_key.json` in the project root. The code at `services/google_calendar_service_account.py:57` checks for the file FIRST, before the env var. Either approach works. **For production deployments use the env var** — never commit the JSON file to git.

If you go with the file approach, also add `service_account_key.json` to `.gitignore`.

**Production** (Replit / Cloud Run / wherever): set `GOOGLE_SERVICE_ACCOUNT_KEY` as a deployment secret. Don't ship the JSON file.

### 3.2 — Do NOT commit the JSON to git

Add to `.gitignore` if not already:
```
service_account_key.json
.env
```
And rotate the existing leaked credentials in `.env` (Gemini key etc.) — they're in your git history.

### 3.3 — *(Optional but recommended)* Switch to "single scheduler" mode (Path B)

If you chose **Path B**, make this small code change so all events route through one Workspace user instead of impersonating each doctor:

**File:** `services/google_calendar_service_account.py:259-334`

In the `create_event_for_both_calendars()` method, change the impersonation target to a fixed scheduler email read from env:

```python
def create_event_for_both_calendars(self, appointment_data):
    # … existing code …
    
    # NEW: prefer fixed scheduler if configured (Path B)
    SCHEDULER_EMAIL = os.environ.get('GOOGLE_SCHEDULER_EMAIL')
    organizer_email = SCHEDULER_EMAIL or doctor_email
    
    # Single event creation (replaces the dual create_event_with_meet calls):
    result_data = self.create_event_with_meet(base_event, organizer_email)
    
    return {
        'doctor_event': result_data,
        'patient_event': None,  # not needed — patient gets invite from organizer
        'meet_link': result_data.get('meet_link') if result_data else None,
        'success': bool(result_data and result_data.get('success'))
    }
```

Then add to `.env`:
```bash
GOOGLE_SCHEDULER_EMAIL=scheduler@yourworkspacedomain.com
```

If you stick with **Path A** (impersonate each doctor), no code change needed — the existing implementation already does this correctly.

### 3.4 — Verify Python libraries are installed

Already good — `requirements.txt` already includes:
- `google-api-python-client>=2.179.0`
- `google-auth>=2.40.3`
- `google-auth-oauthlib>=1.2.2`

No install needed.

### 3.5 — Make sure `GOOGLE_APPLICATION_CREDENTIALS` doesn't conflict

Your current `.env:7` has:
```
GOOGLE_APPLICATION_CREDENTIALS=C:\Users\Hassan\Desktop\red  dot\UrduBotBooker\service_account_key.json
```

This is a Google SDK convention pointing to a JSON file. The code in `google_calendar_service_account.py` does NOT use this env var — it checks for the literal file `service_account_key.json` in the project root.

**Action:** either
- Delete the line entirely (recommended — it's misleading), OR
- Make sure the path it points to actually exists and has the JSON

### 3.6 — Path C only: configure Doctor OAuth env vars

If you went with **Path C** (no Workspace, OAuth-only), you also need:

1. In GCP Console → APIs & Services → Credentials → Create OAuth Client ID (type: Web application)
2. Add authorized redirect URI: `https://yourdomain.com/doctor/auth/google/callback` (and `http://localhost:5000/doctor/auth/google/callback` for dev)
3. Copy the Client ID + Secret
4. Add to `.env`:
```bash
GOOGLE_OAUTH_CLIENT_ID=…apps.googleusercontent.com
GOOGLE_OAUTH_CLIENT_SECRET=GOCSPX-…
```

Then each doctor logs into `/doctor/dashboard` and clicks "Connect Google Calendar" once. From then on, the OAuth fallback path in `routes/appointment_routes.py:152-173` will succeed.

---

## Part 4 — End-to-End Test

After Parts 2 + 3 are done, verify in this order:

### Test 1 — Service account loaded
```bash
# Start the Flask backend
python app.py

# In another terminal:
curl http://localhost:5000/api/appointments/check-calendar-setup
```

**Expected response:**
```json
{
  "success": true,
  "service_account_status": {
    "has_credentials": true,
    "service_account_email": "reddot-calendar-scheduler@…",
    "issues": []
  },
  "calendar_test": {
    "calendar_access": true,
    "calendars_count": …
  },
  "recommendation": "Service account is properly configured and can access calendars!"
}
```

If `has_credentials: false` → JSON not loading → check env var or file path.
If `calendar_test.error` mentions "forbidden" → domain-wide delegation not authorized in Workspace Admin Console (Step 7).

### Test 2 — Book an appointment end-to-end

1. Patient signs up at `/` (sign-up modal)
2. Patient navigates to `/consultation`, picks a doctor + slot, fills symptoms, clicks "Book"
3. Backend creates `Appointment` row + calls `create_event_for_both_calendars()`
4. Patient is returned a `google_meet_link` in the API response
5. Patient sees appointment with Meet link in `/appointments`
6. Doctor email receives a Google Calendar invite (real-world)
7. Click the Meet link from either party — opens Google Meet

**If test 2 fails:**
- Check Flask logs for the error message
- Run `/api/appointments/check-calendar-setup` again to confirm setup
- If "forbiddenForServiceAccounts" → domain-wide delegation scope missing
- If "Invalid conference type" → you're on Workspace plan that doesn't include Meet (rare; basic plans include it)

### Test 3 — Verify the calendar event exists
- Open the doctor's calendar (or scheduler's calendar in Path B) in Google Calendar UI
- Confirm the event shows up with: correct date/time, both attendees, Meet link attached, "Red Dot Pharmacy" in summary

---

## Files Modified by This Plan

| Action | File | Type |
|---|---|---|
| Set env var `GOOGLE_SERVICE_ACCOUNT_KEY` | `.env` (and prod secrets) | config |
| *(optional)* Set `GOOGLE_SCHEDULER_EMAIL` | `.env` (and prod secrets) | config (Path B) |
| *(optional)* Edit `create_event_for_both_calendars()` to use scheduler email | `services/google_calendar_service_account.py` | code (Path B only) |
| Remove or fix `GOOGLE_APPLICATION_CREDENTIALS` line | `.env` | cleanup |
| Add `service_account_key.json` to `.gitignore` | `.gitignore` | safety |
| *(if Path C)* Add `GOOGLE_OAUTH_CLIENT_ID` + `GOOGLE_OAUTH_CLIENT_SECRET` | `.env` | config |

**No new code files needed. No new database migrations. No new endpoints.** The existing implementation handles everything once the credentials are in place.

---

## Quick Reference: What's Already Working in Code

To save you time: I verified that the following are correctly implemented and don't need changes:

✅ `services/google_calendar_service_account.py` — full service account class with delegation, Meet creation, dual-calendar write, error handling, fallback paths
✅ `services/doctor_oauth_service.py` — doctor OAuth fallback (Path C)
✅ `routes/appointment_routes.py:71-212` — appointment creation endpoint with all 3 paths (service account → doctor OAuth → 503 error)
✅ `routes/appointment_routes.py:12-68` — `/check-calendar-setup` diagnostic endpoint
✅ `routes/google_auth_routes.py` — doctor OAuth login flow + token storage
✅ `models.py:155-174` (Appointment): fields `google_meet_link`, `google_calendar_event_id` exist
✅ `models.py:93-97` (User/Doctor): fields `google_access_token`, `google_refresh_token`, `google_token_expiry`, `google_email`, `google_connected_at` exist
✅ All Python libraries in `requirements.txt`

The whole reason this isn't working today is **the service account JSON doesn't exist yet** + **domain-wide delegation isn't authorized in Workspace**. That's it. Two fixable things, both addressed by Parts 2 + 3 above.

---

**Once Parts 2 + 3 are done, update `TODO_BEFORE_PRODUCTION.md` §1 to mark it ✅.**
