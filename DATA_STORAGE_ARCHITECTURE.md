# Red Dot Pharmacy - Data Storage Architecture

## Overview

This document details all data storage locations, database configurations, and the RAG (Retrieval-Augmented Generation) system architecture for the Red Dot Pharmacy application.

---

## 1. Primary Database

### Database Type
- **Default**: SQLite (file-based)
- **Production**: PostgreSQL (via Replit's built-in database)

### Database Configuration
Located in `app.py`:
```python
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///red_dot_pharmacy.db")
```

### Database File Location
| Environment | Location |
|-------------|----------|
| Local/Development | `./red_dot_pharmacy.db` (SQLite file in project root) |
| Replit Production | PostgreSQL via `DATABASE_URL` environment variable |

### Database Tables (Models)
Defined in `models.py`:

| Table | Purpose | Key Fields |
|-------|---------|------------|
| `User` | Patient/Doctor accounts | id, username, email, password_hash, role, phone |
| `Admin` | Admin accounts | id, name, email, password_hash, role |
| `Medicine` | Product catalog | id, name, chemical, description, price, stock_quantity, category, image, status |
| `Order` | Customer orders | id, user_id, total_amount, status, shipping_address, payment_method |
| `OrderItem` | Order line items | id, order_id, medicine_id, quantity, price |
| `Appointment` | Doctor appointments | id, patient_id, doctor_id, starts_at, ends_at, status, google_meet_link |
| `TimeSlot` | Doctor availability | id, doctor_id, day_of_week, start_time, end_time, is_available |
| `ChatLog` | Chatbot conversations | id, user_id, session_id, message, response, language |
| `PaymentMethod` | Payment options | id, name, slug, account_title, account_number, is_active |

---

## 2. RAG System Architecture

### Important: NO Vector Database

**The RAG system does NOT use a vector database (no FAISS, Chroma, Pinecone, etc.).**

Instead, it uses a **hybrid retrieval approach**:

### RAG Components

```
┌─────────────────────────────────────────────────────────────┐
│                    User Query                                │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              Dual Keyword Extraction                         │
│  ┌─────────────────────┐  ┌─────────────────────────────┐   │
│  │ Pattern-Based Agent │  │ Gemini LLM Agent            │   │
│  │ (KeywordExtractor)  │  │ (GeminiClient)              │   │
│  │ - Fast, 90% conf    │  │ - Context-aware             │   │
│  │ - Regex patterns    │  │ - Urdu/English support      │   │
│  └─────────────────────┘  └─────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  Query Classification                        │
│  - medication_query (medicine name/brand)                    │
│  - disease_query (symptoms/conditions)                       │
│  - general_query (greetings, etc.)                          │
└─────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│ SQL Database    │  │ Wikipedia API   │  │ Gemini LLM      │
│ Search          │  │ (Text-based)    │  │ Response Gen    │
│                 │  │                 │  │                 │
│ - Medicine      │  │ - Medical query │  │ - Combine       │
│   catalog       │  │   transformation│  │   contexts      │
│ - Fuzzy match   │  │ - Summary fetch │  │ - Safety checks │
│ - Condition     │  │ - Quality score │  │ - Bilingual     │
│   mapping       │  │                 │  │                 │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

### Data Sources for RAG

| Source | Type | Storage | Purpose |
|--------|------|---------|---------|
| Medicine Database | SQL Query | `red_dot_pharmacy.db` / PostgreSQL | Drug names, chemicals, prices, uses |
| Wikipedia API | HTTP API | External (no local storage) | Medical/disease information |
| Gemini 2.0 Flash | LLM API | External (no local storage) | Response generation, keyword extraction |

### Key RAG Files

| File | Purpose |
|------|---------|
| `agent/rag_engine.py` | Main RAG orchestrator - MedicalRAGEngine class |
| `agent/gemini_client.py` | Gemini LLM integration for keyword extraction |
| `agent/query_classifier.py` | Classifies queries (medication/disease/general) |
| `agent/wikipedia_crawler.py` | Wikipedia content fetcher |
| `services/smart_rag_orchestrator.py` | Smart orchestrator with fallback logic |
| `services/wikipedia_medical_agent.py` | Medical-specific Wikipedia agent |
| `services/wikipedia_utils_safe.py` | Safe Wikipedia API utilities |
| `services/medicine_rag.py` | Medicine database search functions |
| `services/keyword_extractor.py` | Pattern-based keyword extraction |

---

## 3. Medicine Catalog Data

### Initial Data Population

The medicine catalog is populated via `bootstrap.py`:

```bash
python bootstrap.py
```

### Sample Medicines (Seeded Data)

| Medicine | Chemical | Category | Price (PKR) |
|----------|----------|----------|-------------|
| Panadol 500mg | Paracetamol | Pain Relief | 60 |
| Augmentin 625mg | Amoxicillin + Clavulanic Acid | Antibiotics | 950 |
| Brufen 400mg | Ibuprofen | Pain Relief | 80 |
| Disprin | Aspirin | Pain Relief | 40 |
| Flagyl 400mg | Metronidazole | Antibiotics | 150 |

### Adding New Medicines

**Option 1: Admin Dashboard**
- Navigate to `/admin` → Medicines → Add Medicine
- Upload product images to `static/uploads/medicines/`

**Option 2: Direct Database**
```python
from models import Medicine
from app import db

medicine = Medicine(
    name="New Medicine",
    chemical="Active Ingredient",
    description="Description",
    price=100,
    stock_quantity=50,
    category="Category",
    status="in_stock"
)
db.session.add(medicine)
db.session.commit()
```

### Medicine Images Storage

| Type | Location |
|------|----------|
| Uploaded images | `static/uploads/medicines/` |
| Default placeholder | `static/images/default-medicine.png` |

---

## 4. File Storage Locations

### Static Assets

| Directory | Contents |
|-----------|----------|
| `static/css/` | Stylesheets |
| `static/js/` | JavaScript files |
| `static/images/` | Default images, icons |
| `static/uploads/medicines/` | Uploaded medicine product images |
| `static/uploads/receipts/` | Payment receipt uploads |

### Configuration Files

| File | Purpose |
|------|---------|
| `app.py` | Flask app configuration, database setup |
| `models.py` | SQLAlchemy database models |
| `bootstrap.py` | Database seeding script |
| `service_account_key.json` | Google Calendar API credentials |

---

## 5. Environment Variables

| Variable | Purpose | Storage |
|----------|---------|---------|
| `DATABASE_URL` | PostgreSQL connection string | Replit Secrets |
| `SESSION_SECRET` | Flask session encryption | Replit Secrets |
| `GOOGLE_API_KEY` | Gemini AI API key | Replit Secrets |
| `GOOGLE_SERVICE_ACCOUNT_KEY` | Google Calendar credentials | Replit Secrets |
| `OPENAI_API_KEY` | OpenAI API (optional) | Replit Secrets |

---

## 6. Session & Cache Storage

### User Sessions
- Stored in: Flask session (server-side, encrypted)
- Duration: 12 hours (JWT token expiry)

### Chat Sessions
- Stored in: `ChatLog` database table
- Fields: session_id, user_id, message, response, timestamp

### Shopping Cart
- Stored in: Browser localStorage (client-side)
- Key: `cart_items`

---

## 7. Data Flow Summary

```
┌──────────────────────────────────────────────────────────────────┐
│                        DATA SOURCES                               │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │ SQLite/Postgres │  │ Wikipedia API   │  │ Gemini 2.0      │  │
│  │                 │  │ (External)      │  │ Flash (External)│  │
│  │ - Users         │  │                 │  │                 │  │
│  │ - Medicines     │  │ - Disease info  │  │ - Keyword       │  │
│  │ - Orders        │  │ - Medical terms │  │   extraction    │  │
│  │ - Appointments  │  │ - Summaries     │  │ - Response gen  │  │
│  │ - Chat logs     │  │                 │  │ - Translation   │  │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘  │
│           │                    │                    │            │
│           └────────────────────┼────────────────────┘            │
│                                ▼                                 │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                    RAG Engine                                │ │
│  │        (No Vector DB - SQL + API Retrieval)                 │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                │                                 │
│                                ▼                                 │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                 Medical Chatbot UI                           │ │
│  │              (templates/assistant.html)                      │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## 8. Backup & Migration

### Database Backup
```bash
# SQLite backup
cp red_dot_pharmacy.db red_dot_pharmacy_backup.db

# PostgreSQL backup (Replit)
# Use Replit's database panel for backups
```

### Data Export
The admin dashboard provides data export functionality for:
- Orders (CSV)
- Appointments (CSV)
- Medicine inventory (CSV)

---

## Summary

| Data Type | Storage Location | Technology |
|-----------|------------------|------------|
| All application data | `red_dot_pharmacy.db` or PostgreSQL | SQLAlchemy ORM |
| Medicine images | `static/uploads/medicines/` | File system |
| Vector embeddings | **NONE** | Not used |
| External knowledge | Wikipedia API | Live HTTP calls |
| AI responses | Gemini 2.0 Flash API | Live HTTP calls |
| User sessions | Flask session + JWT | In-memory + tokens |
| Shopping cart | Browser localStorage | Client-side |
