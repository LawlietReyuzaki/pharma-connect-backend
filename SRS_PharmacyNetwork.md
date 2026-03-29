# Software Requirements Specification (SRS)
## Red Dot — Multi-Pharmacy Network Platform
### Version 1.0 | Date: March 15, 2026

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Overall Description](#2-overall-description)
3. [Stakeholders & User Roles](#3-stakeholders--user-roles)
4. [Functional Requirements](#4-functional-requirements)
   - 4.1 Pharmacy Registration & Onboarding
   - 4.2 Pharmacy Profile Page
   - 4.3 Pharmacy Branding & Theming
   - 4.4 Shared Medicine Catalog
   - 4.5 Shared Chatbot & AI Assistant
   - 4.6 Doctor Listings & Appointments
   - 4.7 Order Management Per Pharmacy
   - 4.8 Customer-Facing Discovery & Search
   - 4.9 Location-Based Pharmacy Recommendations
   - 4.10 Reviews & Ratings
   - 4.11 Pharmacy Dashboard (Admin Portal Per Pharmacy)
   - 4.12 Super Admin (Platform Owner) Portal
5. [Non-Functional Requirements](#5-non-functional-requirements)
6. [What Is Shared vs. What Is Unique Per Pharmacy](#6-what-is-shared-vs-what-is-unique-per-pharmacy)
7. [User Journeys](#7-user-journeys)
8. [Out of Scope (Version 1)](#8-out-of-scope-version-1)
9. [Open Questions & Decisions Pending](#9-open-questions--decisions-pending)

---

## 1. Introduction

### 1.1 Purpose

This document describes the requirements for a new top-level layer to be built on top of the existing Red Dot Pharmacy platform. The goal is to transform the current single-pharmacy system into a **national multi-pharmacy network** — a social media-style directory platform where pharmacies across Pakistan can register, create their own branded profile pages, and serve their local customers — all powered by the same shared infrastructure already built.

### 1.2 Vision

Think of it as **"LinkedIn for Pharmacies"** — or more precisely, a **Trustpilot + LinkedIn hybrid for the healthcare/pharmacy sector in Pakistan**. Each pharmacy gets its own public-facing page. Customers can discover, compare, review, and engage with pharmacies. All the core functionality (chatbot, appointment booking, medicine ordering) is inherited automatically by every registered pharmacy.

### 1.3 Background

The existing Red Dot Pharmacy platform has the following capabilities already built:
- AI-powered bilingual medical chatbot (English & Urdu)
- Medicine catalog with ordering and home delivery
- Doctor appointment scheduling with Google Meet integration
- Admin dashboard for managing orders, appointments, and users
- Role-based access for patients, doctors, and admins

This SRS focuses **only on the new layer** to be built on top — the multi-pharmacy network.

---

## 2. Overall Description

### 2.1 What We Are Building

A **pharmacy network platform** that:

1. Allows pharmacies from all over Pakistan to register and create a profile on the platform.
2. Automatically generates a unique, branded **pharmacy profile page** for each registered pharmacy.
3. Lets customers find pharmacies, browse their doctors, consult the chatbot, order medicines, and leave reviews — all from within that pharmacy's page.
4. Recommends the **nearest pharmacy** to a customer based on their location.
5. Routes all orders and appointments to the **specific pharmacy's own dashboard** — each pharmacy manages its own business independently.
6. Shares the **medicine catalog and chatbot** infrastructure across all pharmacies so no pharmacy has to build these from scratch.

### 2.2 Analogy

| Concept | Analogy |
|---|---|
| Platform itself | LinkedIn (directory of organizations) |
| Pharmacy profile page | LinkedIn Company Page |
| Reviews | Trustpilot ratings |
| Shared chatbot & medicines | Shared SaaS infrastructure |
| Nearest pharmacy recommendation | Google Maps "near me" |
| Each pharmacy's dashboard | Their own private admin panel |

---

## 3. Stakeholders & User Roles

### 3.1 Platform Super Admin
- The owner/operator of the Red Dot network platform.
- Approves pharmacy registrations.
- Manages the global medicine catalog.
- Has visibility across all pharmacies on the platform.
- Can suspend or remove pharmacies.

### 3.2 Pharmacy Owner / Pharmacy Admin
- Registers the pharmacy on the platform.
- Sets up the pharmacy profile (information, pictures, theme).
- Manages their own doctors, appointments, and orders.
- Views their own pharmacy's analytics dashboard.
- Cannot see data from other pharmacies.

### 3.3 Doctor (under a Pharmacy)
- Registered by the Pharmacy Owner as part of the pharmacy's team.
- Manages their own availability and appointments.
- Can use their existing doctor portal.

### 3.4 Customer / Patient
- Visits the platform to find a pharmacy.
- Can browse all pharmacies or be recommended the nearest one.
- Visits a specific pharmacy's page to consult the chatbot, book a doctor, or order medicines.
- Can leave reviews on a pharmacy's page.

---

## 4. Functional Requirements

---

### 4.1 Pharmacy Registration & Onboarding

**FR-01** — A pharmacy must be able to register on the platform by providing the following information:

| Field | Description |
|---|---|
| Pharmacy Name | Official name of the pharmacy/clinic |
| Owner Name | Full name of the lead pharmacy owner |
| Owner Photo | Profile picture of the owner |
| Pharmacy Photo | Exterior or interior picture of the pharmacy |
| Address | Full street address |
| City & Province | Location within Pakistan |
| GPS Coordinates | For location-based recommendations (can be auto-detected or manually entered) |
| Contact Number | Phone number for the pharmacy |
| Email Address | For platform communication |
| Operating Hours | Days and times the pharmacy is open |
| License Number | Pharmacy registration/license number (for verification) |
| Doctors | List of doctors associated with the pharmacy (see 4.6) |
| Preferred Color Theme | Choice from available color theme combinations |

**FR-02** — After submitting registration, the pharmacy application must go to the Super Admin for review and approval before the profile goes live.

**FR-03** — Once approved, the platform automatically generates a unique pharmacy profile page and a separate pharmacy dashboard for that pharmacy.

**FR-04** — The pharmacy must receive a notification (email) when their registration is approved or rejected, with a reason if rejected.

---

### 4.2 Pharmacy Profile Page

**FR-05** — Every approved pharmacy gets a publicly visible **Pharmacy Profile Page** that displays:

- Pharmacy name and logo/photo at the top (hero section)
- Owner's photo and name
- Address, city, contact number, operating hours
- A map pin showing the pharmacy's location
- List of affiliated doctors with their names, specializations, and photos
- Customer reviews and overall star rating
- The shared medicine catalog (available for browsing and ordering)
- An "Consult Chatbot" button that opens the shared AI chatbot
- A "Book Appointment" button to schedule with one of the pharmacy's doctors
- A "Order Medicines" button

**FR-06** — The pharmacy profile page must have a unique URL (e.g., `platform.com/pharmacy/red-dot-islamabad`).

**FR-07** — The page must be publicly accessible — customers do not need to log in just to view the profile.

---

### 4.3 Pharmacy Branding & Theming

**FR-08** — The platform must provide a set of **pre-defined color theme combinations** that a pharmacy can choose from during registration or from their dashboard.

**FR-09** — The selected color theme must be applied to that pharmacy's profile page only — it does not affect any other pharmacy's page or the main platform homepage.

**FR-10** — At minimum, the following elements must reflect the pharmacy's chosen theme:
- Primary background color
- Button colors
- Header/navigation bar color
- Accent/highlight colors

**FR-11** — The pharmacy's **owner photo and pharmacy photo** must be prominently displayed on the profile page, giving it a personalized feel unique to that pharmacy.

**FR-12** — The platform must offer at least **8–10 distinct color theme combinations** to choose from at launch.

---

### 4.4 Shared Medicine Catalog

**FR-13** — There is a single, centrally maintained medicine catalog managed by the Super Admin.

**FR-14** — Every pharmacy's profile page displays this shared catalog — pharmacies do not need to add medicines themselves.

**FR-15** — When a customer orders a medicine from a pharmacy's page, that order is automatically associated with that specific pharmacy.

**FR-16** — The Super Admin can add, edit, or remove medicines from the global catalog, and the change reflects across all pharmacy pages immediately.

**FR-17** — In a future version, individual pharmacies may be allowed to mark medicines as "out of stock" for their location specifically — but this is **not required for Version 1**.

---

### 4.5 Shared Chatbot & AI Assistant

**FR-18** — The AI medical chatbot is a shared service available on every pharmacy's page.

**FR-19** — When a customer uses the chatbot from a specific pharmacy's page, the chatbot experience is branded with that pharmacy's theme and name.

**FR-20** — Chatbot conversations are logged and visible in that pharmacy's own dashboard (not visible to other pharmacies).

**FR-21** — The chatbot retains all existing capabilities: bilingual support, emergency detection, medicine recommendations, and Wikipedia panels.

**FR-22** — If the chatbot recommends a medicine, the "Order Now" button directs the customer to order from the pharmacy whose page they are currently on.

---

### 4.6 Doctor Listings & Appointments

**FR-23** — During pharmacy registration (or later from the dashboard), the Pharmacy Owner can add doctors to their pharmacy profile with the following information per doctor:

| Field | Description |
|---|---|
| Doctor's Full Name | |
| Specialization | e.g., General Physician, Cardiologist |
| Qualifications | e.g., MBBS, FCPS |
| Photo | Profile picture |
| Years of Experience | |
| Languages Spoken | e.g., Urdu, English, Punjabi |
| Consultation Fee | |
| Availability Schedule | Days and times available |

**FR-24** — Doctors listed under a pharmacy appear on that pharmacy's profile page.

**FR-25** — Customers can book an appointment with a specific doctor from the pharmacy's page using the existing appointment scheduling system.

**FR-26** — Google Meet links and calendar invites are generated automatically as per the existing system.

**FR-27** — Each doctor's appointments are visible only in the dashboard of the pharmacy they belong to.

---

### 4.7 Order Management Per Pharmacy

**FR-28** — When a customer places a medicine order from a pharmacy's page, that order is routed to **that pharmacy's dashboard only**.

**FR-29** — The pharmacy's admin can view, process, and update the status of orders from their own dashboard.

**FR-30** — The pharmacy dashboard must show the customer's delivery address and selected payment method.

**FR-31** — Payment verification (for online payments with receipt upload) is handled by the pharmacy's own admin.

**FR-32** — Pharmacies cannot see orders belonging to other pharmacies.

---

### 4.8 Customer-Facing Discovery & Search

**FR-33** — The platform homepage must have a **search bar** where customers can search for a pharmacy by name, city, or area.

**FR-34** — Search results must display pharmacy cards showing:
- Pharmacy photo
- Pharmacy name
- City/area
- Star rating (from reviews)
- Number of doctors
- A "Visit Page" button

**FR-35** — Customers can filter search results by:
- City
- Star rating
- Specialization of available doctors

---

### 4.9 Location-Based Pharmacy Recommendations

**FR-36** — When a customer visits the platform, the platform must request permission to access their device location (GPS).

**FR-37** — If location access is granted, the platform must display a **"Pharmacies Near You"** section on the homepage showing the closest registered pharmacies first.

**FR-38** — Each pharmacy card in the "Near You" section must show the estimated distance from the customer's location (e.g., "2.3 km away").

**FR-39** — If location access is denied, the platform falls back to showing pharmacies by city (customer manually selects their city).

**FR-40** — Location data must only be used for recommendations and must not be stored or shared.

---

### 4.10 Reviews & Ratings

**FR-41** — Logged-in customers can submit a review for a pharmacy after they have:
- Placed an order from that pharmacy, OR
- Completed an appointment with a doctor at that pharmacy.

**FR-42** — A review consists of:
- Star rating (1 to 5 stars)
- Written comment (optional, max 500 characters)
- Date of review

**FR-43** — Reviews are publicly visible on the pharmacy's profile page.

**FR-44** — The pharmacy's overall star rating is calculated as the average of all submitted reviews and displayed prominently on their profile page and search results cards.

**FR-45** — The Pharmacy Owner can respond to reviews from their dashboard (a single written reply per review).

**FR-46** — The Super Admin can remove reviews that violate platform guidelines (e.g., abusive language).

**FR-47** — Customers cannot submit more than one review per completed transaction (one review per order or one per appointment).

---

### 4.11 Pharmacy Dashboard (Per Pharmacy Admin Portal)

**FR-48** — Each registered and approved pharmacy gets access to their own private dashboard. The dashboard must include:

| Section | What It Shows |
|---|---|
| Overview | Summary stats: total orders today, pending appointments, revenue, new reviews |
| Orders | All orders placed via their pharmacy page with status management |
| Appointments | All booked appointments for their doctors |
| Doctors | Manage the list of associated doctors (add, edit, remove) |
| Reviews | View all customer reviews and respond to them |
| Profile Settings | Update pharmacy info, photos, color theme, operating hours |
| Analytics | Charts for orders over time, popular medicines, appointment trends |

**FR-49** — The pharmacy dashboard is only accessible to that pharmacy's admin — it is completely isolated from other pharmacies.

**FR-50** — The Pharmacy Owner uses a separate login from customers. Their account type is "Pharmacy Admin."

---

### 4.12 Super Admin (Platform Owner) Portal

**FR-51** — The Super Admin portal must include all existing admin features plus the following new ones:

| Feature | Description |
|---|---|
| Pharmacy Applications | View and approve/reject incoming pharmacy registration requests |
| All Pharmacies List | See all registered pharmacies, their status (active/suspended), and key stats |
| Global Medicine Catalog | Add, edit, delete medicines that are shared across all pharmacies |
| Platform Analytics | Aggregate stats across all pharmacies (total users, total orders, total revenue) |
| Review Moderation | Remove inappropriate reviews from any pharmacy's page |
| Suspend/Reactivate | Ability to suspend a pharmacy from the platform |
| Theme Management | Add or remove available color themes from the selection pool |

---

## 5. Non-Functional Requirements

### 5.1 Performance
- Pharmacy profile pages must load within 3 seconds on a standard mobile connection.
- Location-based recommendations must return results within 2 seconds of location access being granted.

### 5.2 Scalability
- The platform must be able to support at least 500 registered pharmacies at launch without degradation in performance.

### 5.3 Security & Privacy
- Each pharmacy's data (orders, appointments, chat logs) must be strictly isolated — no pharmacy can access another's data.
- Customer location data must not be stored on the server — it is used in-session only.
- All passwords must be encrypted. Pharmacy admin accounts must support password reset via email.

### 5.4 Mobile Responsiveness
- All pages — the platform homepage, pharmacy profile pages, and dashboards — must be fully functional on mobile devices (phones and tablets).

### 5.5 Language
- The platform must support both **English and Urdu** across all customer-facing pages, consistent with the existing system.

### 5.6 Availability
- The platform should target 99.5% uptime. Scheduled maintenance must be communicated to pharmacy admins in advance.

---

## 6. What Is Shared vs. What Is Unique Per Pharmacy

| Feature | Shared Across All Pharmacies | Unique Per Pharmacy |
|---|---|---|
| Medicine Catalog | Yes — one global catalog | No customization in V1 |
| AI Chatbot | Yes — same engine | Branded with pharmacy name/theme |
| Appointment System | Yes — same booking engine | Doctors are unique per pharmacy |
| Theme/Colors | No | Each pharmacy picks their own |
| Pharmacy Photo | No | Each pharmacy uploads their own |
| Owner Photo | No | Each pharmacy uploads their own |
| Dashboard | No | Fully separate per pharmacy |
| Orders | No | Routed to respective pharmacy only |
| Reviews | No | Per pharmacy |
| Doctors | No | Each pharmacy registers their own |
| Chat Logs | No | Visible only to that pharmacy |

---

## 7. User Journeys

### 7.1 Customer Finding a Pharmacy

1. Customer visits the platform homepage.
2. Platform requests location access.
3. Platform shows "Pharmacies Near You" with distance.
4. Customer taps on a pharmacy card.
5. Customer is taken to that pharmacy's branded profile page.
6. Customer can consult the chatbot, book a doctor, or order medicines from that page.

### 7.2 Customer Leaving a Review

1. Customer completes an order or appointment.
2. Customer receives a prompt (or visits the pharmacy page) to leave a review.
3. Customer selects a star rating and optionally writes a comment.
4. Review is submitted and appears on the pharmacy's profile page.
5. Pharmacy Owner is notified of the new review in their dashboard.

### 7.3 Pharmacy Registering on the Platform

1. Pharmacy Owner visits the platform and clicks "Register Your Pharmacy."
2. Fills in all required information (pharmacy details, doctors, photos, preferred theme).
3. Submits the registration form.
4. Super Admin reviews and approves or rejects the application.
5. Pharmacy Owner receives an email with the decision.
6. If approved, their pharmacy profile page is live and their dashboard is activated.

### 7.4 Pharmacy Admin Processing an Order

1. Customer places a medicine order from Pharmacy X's page.
2. Pharmacy X's admin receives a notification in their dashboard.
3. Admin views the order details (customer name, delivery address, medicines, payment method).
4. Admin updates the order status (processing → out for delivery → delivered).
5. Customer sees the updated status on their end.

---

## 8. Out of Scope (Version 1)

The following features are **not** required for the first version of the platform but may be considered for future versions:

- Per-pharmacy custom medicine additions (pharmacies adding their own unique medicines not in the shared catalog)
- In-app messaging between customers and pharmacy staff
- Pharmacy subscription/pricing tiers (all pharmacies are on one plan in V1)
- Advertisements or featured/promoted pharmacy listings
- Multi-branch support (one pharmacy having multiple locations)
- Loyalty points or reward programs
- Insurance integration
- Live chat support between patient and doctor (text-based real-time chat)

---

## 9. Open Questions & Decisions Pending

The following questions should be reviewed and decided before development begins:

| # | Question | Options / Notes |
|---|---|---|
| Q1 | How many color theme combinations will be available at launch? | Suggested: 8–10 pre-built themes |
| Q2 | Will pharmacy registration be free or paid (subscription model)? | Decision needed from business side |
| Q3 | Who handles medicine delivery — Red Dot centrally or each pharmacy independently? | Affects the order routing architecture |
| Q4 | Can a doctor be listed under more than one pharmacy? | Needs a policy decision |
| Q5 | How is pharmacy license verification done — manual review only or integrated with a national database? | Manual review is simpler for V1 |
| Q6 | Will the platform URL structure be a subdomain per pharmacy (pharmacy-name.reddot.pk) or a path (reddot.pk/pharmacy/pharmacy-name)? | Technical + branding decision |
| Q7 | What happens to a customer's account if they interact with multiple pharmacies — is there one customer account across all, or per pharmacy? | Single unified customer account is recommended |
| Q8 | Will reviews require moderation/approval before going live, or are they instantly published? | Recommend instant publish with report/remove option |

---

*End of Document*

*Prepared for: Red Dot Platform — Internal Use*
*Next Step: Review this document, answer the open questions in Section 9, and sign off before development planning begins.*
