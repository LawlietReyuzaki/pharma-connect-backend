# replit.md

## Overview

Red Dot Pharmacy is a comprehensive healthcare platform built with Flask that provides online medicine ordering, video consultations with doctors, and an Urdu-supported medical chatbot. The application serves patients who can browse medicines, book appointments, and receive medical guidance through a conversational AI assistant with built-in medical safety guardrails.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Backend Framework
- **Flask** with SQLAlchemy ORM for rapid development and Replit compatibility
- **SQLite** database for simplicity (easily replaceable with PostgreSQL)
- **Blueprint-based routing** for modular organization of API endpoints
- **JWT authentication** for stateless user sessions

### Database Design
- **Users table** with role-based access control (patient/doctor/admin)
  - Doctor-specific fields: specialization, qualification, experience_years, current_hospital
  - Google OAuth integration for calendar access
- **Medicines table** with inventory management and categorization
- **TimeSlots table** for doctor availability management
- **Appointments table** linking patients to doctors with video call support
- **Orders/OrderItems** for medicine purchase workflow
- **ChatLog** for tracking conversational AI interactions
- **Admins table** for secure admin authentication (JWT-based)

### Authentication & Authorization
- SHA256 password hashing for user security
- JWT tokens with 12-hour expiration for session management
- Role-based access control decorators (@require_role)
- Token verification middleware for protected endpoints

### Medical Chatbot System
- **Google Gemini 2.0 Flash** AI model for intelligent medical assistance
- **Medical guardrails** with red-flag pattern matching in English and Urdu
- **Comprehensive safety features** with emergency response for critical symptoms
- **Bilingual support** (English/Urdu) with automatic language detection (>30% Urdu = Urdu response)
- **Voice integration** using Web Speech API for speech-to-text and Google TTS for text-to-speech
- **Session management** for conversation context tracking
- **Chat logging** to database for analysis and improvement
- **Endpoints**:
  - `POST /api/chat/medical-chat` - Main chatbot endpoint with safety guardrails
  - `POST /api/chat/transcribe-urdu` - Urdu voice transcription
  - `POST /api/chat/transcribe-english` - English voice transcription
  - `POST /api/chat/speak-urdu` - Text-to-speech for Urdu
- **UI**: `/assistant` page with medical-themed chat interface

### Frontend Architecture
- **Flask templates** with Jinja2 for server-side rendering
- **Bootstrap 5** for responsive UI components
- **Vanilla JavaScript** for dynamic interactions and API calls
- **Chart.js** for admin dashboard analytics
- **Font Awesome** for consistent iconography

### Doctor Management
- **Admin Panel Features**:
  - Add, edit, and delete doctors from the admin dashboard
  - Manage doctor profiles (specialization, experience, qualifications, hospital)
  - View appointment counts and doctor statistics
  - Time slot management for each doctor
- **Customer-Facing Features**:
  - Browse available doctors with detailed profiles
  - Select doctors by specialization and availability
  - View doctor experience, qualifications, and current hospital
  - Book appointments with specific doctors
- **Appointment Workflow**:
  - Customer selects doctor and available time slot
  - Admin reviews and approves appointment requests
  - Google Meet links generated automatically for approved appointments
  - Status tracking (pending → approved → scheduled → ongoing → completed)

### Video Consultation
- **Google Meet ONLY** for video consultations (no Jitsi fallback)
- Appointments require Google Calendar integration to work
- Calendar events created in BOTH doctor's and patient's Google Calendars automatically
- Google Meet links generated automatically when appointments are scheduled
- **Time slot system** prevents double-booking
- **Appointment workflow**: Patient selects doctor → selects time slot → appointment created → calendar events + Meet link generated

### Order Management
- **Shopping cart** with local storage persistence
- **Inventory validation** before order confirmation
- **Order status tracking** (pending → processing → delivered)
- **Address and phone validation** for delivery coordination

### Payment Management
- **Dedicated Payment Admin Page** at `/admin/payments` for full payment method control
- **PaymentMethod model** with fields:
  - name, slug, logo_path
  - account_title, account_number (for displaying to customers)
  - account_details (additional instructions)
  - is_active (admin toggle), requires_receipt
  - display_order for sorting
- **Supported Payment Methods**:
  - Cash on Delivery
  - EasyPaisa (online, requires receipt)
  - JazzCash (online, requires receipt)
  - Meezan Bank (online, requires receipt)
  - NayaPay (online, requires receipt)
- **Admin Features**:
  - Add/Edit account title and account number for each method
  - Toggle payment methods on/off
  - Set display order
  - View and verify payment receipts
  - Accept/Decline payments
- **Customer Features**:
  - View active payment methods during checkout
  - See account details (title, number) with copy button
  - Upload payment receipt for online payments
  - Order confirmation shows selected payment method info

## External Dependencies

### Core Framework
- **Flask** - Web application framework
- **Flask-SQLAlchemy** - Database ORM
- **Flask-CORS** - Cross-origin request handling
- **PyJWT** - JSON Web Token implementation

### AI & Language Processing
- **OpenAI API** (optional) - Advanced medical query handling
- **Web Speech API** - Browser-based speech recognition and synthesis for Urdu/English

### Frontend Libraries
- **Bootstrap 5** - CSS framework for responsive design
- **Font Awesome** - Icon library
- **Chart.js** - Data visualization for admin dashboard

### Video & Calendar Integration
- **Google Calendar Service Account Integration** (REQUIRED) for automatic calendar event creation
  - Creates events in BOTH doctor's and patient's Google Calendars
  - Auto-generates Google Meet video conference links
  - Sends automatic email notifications to both parties
  - Service account: `red-dot-pharmacy@stable-balancer-479507-j8.iam.gserviceaccount.com`
  - **Key stored in**: `service_account_key.json` file (preferred) or `GOOGLE_SERVICE_ACCOUNT_KEY` secret
  - Requires domain-wide delegation enabled in Google Workspace Admin Console
  - Service account needs "Make changes and manage sharing" permission
- **NO FALLBACK** - Appointments will fail if Google Calendar is not properly configured
- Video call links generated automatically when appointments are created
- Links are deterministic and unique per appointment
- **Diagnostic endpoint**: `GET /api/appointments/check-calendar-setup` to verify configuration

### Google Calendar Setup Requirements
1. Create a Service Account in Google Cloud Console
2. Enable Google Calendar API
3. Download JSON key file and save as `service_account_key.json` in project root
4. Enable domain-wide delegation
5. In Google Workspace Admin Console, add the service account client ID with scopes:
   - `https://www.googleapis.com/auth/calendar`
   - `https://www.googleapis.com/auth/calendar.events`
6. Alternative: Add the JSON key contents to `GOOGLE_SERVICE_ACCOUNT_KEY` secret in Replit

### Current Service Account Status
- **Active**: `red-dot-pharmacy@stable-balancer-479507-j8.iam.gserviceaccount.com`
- **Project**: `stable-balancer-479507-j8`
- **Calendar Access**: Verified working

### Development & Deployment
- **Replit** hosting platform with auto-scaling
- **SQLite** - Default database (production-ready for PostgreSQL migration)
- **Environment variables** - Secure configuration management