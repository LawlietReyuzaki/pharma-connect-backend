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
- **Medicines table** with inventory management and categorization
- **Appointments table** linking patients to doctors with video call support
- **Orders/OrderItems** for medicine purchase workflow
- **ChatLog** for tracking conversational AI interactions

### Authentication & Authorization
- SHA256 password hashing for user security
- JWT tokens with 12-hour expiration for session management
- Role-based access control decorators (@require_role)
- Token verification middleware for protected endpoints

### Medical Chatbot System
- **Medical guardrails** with red-flag pattern matching in English and Urdu
- **OpenAI integration** as optional LLM fallback for complex queries
- **Bilingual support** (English/Urdu) with automatic language detection
- **Voice integration** using Web Speech API for speech-to-text and text-to-speech
- **Session management** for conversation context tracking

### Frontend Architecture
- **Flask templates** with Jinja2 for server-side rendering
- **Bootstrap 5** for responsive UI components
- **Vanilla JavaScript** for dynamic interactions and API calls
- **Chart.js** for admin dashboard analytics
- **Font Awesome** for consistent iconography

### Video Consultation
- **Jitsi Meet** embedded iframe solution (no server infrastructure required)
- **Google Calendar API** integration for appointment scheduling
- **Appointment status workflow** (scheduled → ongoing → completed)

### Order Management
- **Shopping cart** with local storage persistence
- **Inventory validation** before order confirmation
- **Order status tracking** (pending → processing → delivered)
- **Address and phone validation** for delivery coordination

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
- **Jitsi Meet** - Embedded video conferencing (iframe-based)
- **Google Calendar API** - Appointment scheduling integration
- **Google Meet** - Video call link generation

### Development & Deployment
- **Replit** hosting platform with auto-scaling
- **SQLite** - Default database (production-ready for PostgreSQL migration)
- **Environment variables** - Secure configuration management