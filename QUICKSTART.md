# 🚀 Quick Start - SQLite Local Setup

## One-Step Setup

```bash
# From project root directory
python setup_local_db.py
```

That's it! This will:
- ✅ Create SQLite database
- ✅ Load all medicines from CSV
- ✅ Validate images
- ✅ Test medicine search
- ✅ Create .env file

## Start the App

```bash
python main.py
```

Then open: **http://localhost:5000**

## Test the Chatbot

Try asking the chatbot:
- "Where can I find Panadol?"
- "What medicines treat fever?"
- "Show me medicines under 500 rupees"

You should see:
- ✅ Medicine name and price
- ✅ Product image (from `static/uploads/medicines/`)
- ✅ Chemical ingredients
- ✅ Description

## What Was Changed

### The Problem
- App was using PostgreSQL (cloud database)
- Not working locally without internet
- Images linked via CSV weren't properly integrated

### The Solution
1. **SQLite Database** - Local file-based DB (`red_dot_pharmacy.db`)
2. **CSV Loader** - Imports 1000+ medicines with image links
3. **SQLite Search Service** - Optimized medicine search
4. **Setup Script** - Automated initialization

### How It Works

```
CSV File (medicines_export.csv)
    ↓
CSV Loader (database_loader.py)
    ↓
SQLite Database (red_dot_pharmacy.db) ← Local
    ↓
Search Service (sqlite_medicine_search.py)
    ↓
RAG System (agent/rag_engine.py)
    ↓
Images (static/uploads/medicines/)
    ↓
Chatbot Response with Images
```

## File Structure

```
UrduBotBooker/
├── red_dot_pharmacy.db              ← SQLite database (created)
├── medicines_export.csv             ← Medicine data source
├── setup_local_db.py               ← Setup script (NEW)
├── database_loader.py              ← CSV loader (NEW)
├── config.py                       ← Configuration (NEW)
├── services/
│   └── sqlite_medicine_search.py   ← Search engine (NEW)
├── static/uploads/medicines/       ← Product images
└── ... (other files unchanged)
```

## Key Components

### 1. Database Loader
```python
python database_loader.py medicines_export.csv
```
- Reads CSV
- Validates data
- Saves to SQLite
- Links images automatically

### 2. Search Service
```python
from services.sqlite_medicine_search import MedicineSearchService

# Search by name
results = MedicineSearchService.search_by_name("Panadol")

# Search by ingredient
results = MedicineSearchService.search_by_chemical("Paracetamol")

# Search in stock
results = MedicineSearchService.search_in_stock("Aspirin")
```

### 3. Image Linking
Each medicine has:
- `image_path` - From CSV: `/static/uploads/medicines/1.jpeg`
- `image_url` - Formatted for browser: `http://localhost:5000/static/uploads/medicines/1.jpeg`

## Verify Installation

```bash
# Check database
python -c "
from app import create_app
from models import Medicine

app = create_app()
with app.app_context():
    count = Medicine.query.count()
    print(f'✅ Medicines loaded: {count}')
    
    sample = Medicine.query.first()
    print(f'Sample: {sample.name} - Rs.{sample.price}')
    print(f'Image: {sample.image_path}')
"

# Output should show:
# ✅ Medicines loaded: 1000+
# Sample: 2blink Eye Drop 15ml - Rs.479
# Image: /static/uploads/medicines/1.jpeg
```

## Database Schema

### medicines table
```sql
id          INTEGER PRIMARY KEY
name        VARCHAR(160) - Medicine name
chemical    VARCHAR(160) - Active ingredient
description TEXT - Full description
price       INTEGER - Price in PKR
stock_quantity INTEGER - Stock level
category    VARCHAR(100) - Medicine category
status      VARCHAR(30) - in_stock/out_of_stock
image_path  VARCHAR(255) - Path to product image
created_at  DATETIME
updated_at  DATETIME
```

## Search Examples

### Find all Paracetamol medicines
```python
from services.sqlite_medicine_search import MedicineSearchService
results = MedicineSearchService.search_by_chemical("Paracetamol")
```

### Autocomplete search
```python
suggestions = MedicineSearchService.autocomplete("Pan")
# Returns: ['Panadol 500mg', 'Panadol Extra', ...]
```

### Price range search
```python
affordable = MedicineSearchService.get_medicines_by_price_range(50, 200)
```

## Troubleshooting

### Problem: "medicines_export.csv not found"
```bash
# Verify file exists
ls medicines_export.csv

# If missing, check its actual location
find . -name "medicines_export.csv"

# Run from correct directory
cd /path/to/UrduBotBooker
python setup_local_db.py
```

### Problem: Images not showing
```bash
# Check images folder exists
ls static/uploads/medicines/

# Should show: 1.jpeg, 2.png, 3.png, etc.

# Check first few files
ls static/uploads/medicines/ | head -10
```

### Problem: No medicines found in search
```bash
# Verify medicines are loaded
python -c "
from app import create_app
from models import Medicine

app = create_app()
with app.app_context():
    count = Medicine.query.count()
    if count == 0:
        print('❌ No medicines loaded!')
        print('Run: python setup_local_db.py')
    else:
        print(f'✅ {count} medicines in database')
"
```

### Problem: Database locked
```bash
# SQLite auto-recovers, just restart
python main.py

# If persistent, reset database
rm red_dot_pharmacy.db
python setup_local_db.py
```

## Production Deployment

On Replit:
1. Database URL is auto-set to PostgreSQL
2. All code works unchanged
3. No manual setup needed

```bash
# On Replit, just run:
python main.py

# It automatically detects DATABASE_URL in Secrets
# and uses PostgreSQL instead of SQLite
```

## Environment Files

### .env (optional, for local development)
```
FLASK_ENV=development
FLASK_DEBUG=1
SESSION_SECRET=your-secret-key
```

### production (Replit Secrets)
```
DATABASE_URL=postgresql://...
SESSION_SECRET=...
GOOGLE_API_KEY=...
```

## Next Steps

1. ✅ Run `python setup_local_db.py`
2. ✅ Start app with `python main.py`
3. ✅ Test chatbot
4. ✅ Add/edit medicines via admin panel
5. ✅ Upload new medicine images

## Architecture Overview

### Before
```
❌ PostgreSQL (Replit cloud)
   ↓ 
   Requires internet
   Hard to develop locally
   Images managed separately
```

### After
```
✅ SQLite (local file)
   ↓
   Work offline
   Fast local development
   Images linked in CSV
   
✅ PostgreSQL (Replit production)
   ↓
   No code changes
   Auto-detected from DATABASE_URL
```

## Key Files to Know

| File | Purpose |
|------|---------|
| `red_dot_pharmacy.db` | SQLite database (auto-created) |
| `setup_local_db.py` | One-command setup |
| `database_loader.py` | Loads CSV to SQLite |
| `sqlite_medicine_search.py` | Search engine |
| `medicines_export.csv` | Data source |
| `static/uploads/medicines/` | Product images |

## Common Commands

```bash
# Setup everything
python setup_local_db.py

# Start app
python main.py

# Reload medicines from CSV
python database_loader.py medicines_export.csv

# Check database
python -c "from models import Medicine; from app import create_app; app = create_app(); print(Medicine.query.count())"

# Test search
python -c "from services.sqlite_medicine_search import MedicineSearchService; print(MedicineSearchService.search_by_name('panadol'))"

# List images
ls static/uploads/medicines/ | wc -l
```

## Support

For detailed information, see [SQLITE_MIGRATION.md](SQLITE_MIGRATION.md)

For detailed RAG documentation, see [DATA_STORAGE_ARCHITECTURE.md](DATA_STORAGE_ARCHITECTURE.md)

---

**All set!** 🎉 Your local SQLite database is ready to use.
