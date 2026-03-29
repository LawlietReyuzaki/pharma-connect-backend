# SQLite Migration Guide for Red Dot Pharmacy

## Overview

This guide explains the migration from PostgreSQL to SQLite for local development of the Red Dot Pharmacy application. The application is now fully optimized to work with SQLite while maintaining full compatibility with PostgreSQL on Replit production.

## Architecture

### Data Flow

```
User Query (Chatbot)
        ↓
Query Classifier (agent/query_classifier.py)
        ↓
Smart RAG Orchestrator (services/smart_rag_orchestrator.py)
        ↓
Medicine Search Service (services/sqlite_medicine_search.py) ← NEW
        ↓
SQLite Database (red_dot_pharmacy.db) ← LOCAL
        ↓
Format Response + Images
        ↓
Chatbot Response
```

## Key Components

### 1. SQLite Database (`red_dot_pharmacy.db`)

**Location**: Project root directory
**Type**: File-based SQLite database (single file)
**Tables**: 
- `medicines` - Product catalog with image paths
- `users` - Patient/doctor accounts
- `orders` - Customer orders
- `appointments` - Doctor appointments
- `chat_logs` - Chatbot conversation history

### 2. Medicine CSV Data (`medicines_export.csv`)

**Format**:
```
id,name,chemical,description,price,stock_quantity,category,status,image_path
35,2blink Eye Drop 15ml,...,479,100,Sante,in_stock,/static/uploads/medicines/1.jpeg
```

**Key Field**: `image_path`
- Links each medicine to its image
- Format: `/static/uploads/medicines/{filename}`
- Images stored in: `static/uploads/medicines/`

### 3. Images Directory

**Location**: `static/uploads/medicines/`
**Contents**: Individual medicine product images
**Formats**: .png, .jpg, .jpeg
**Usage**: Referenced in CSV via `image_path` column

### 4. SQLite-Optimized Search Service

**File**: `services/sqlite_medicine_search.py`
**Class**: `MedicineSearchService`
**Methods**:
- `search_by_name()` - Search by medicine name
- `search_by_chemical()` - Search by active ingredient
- `search_by_description()` - Search by description
- `multi_field_search()` - Search across all fields
- `search_in_stock()` - Search only available items
- `autocomplete()` - Get name suggestions
- And more...

## Setup Instructions

### Step 1: Run the Setup Script

```bash
# From project root
python setup_local_db.py
```

This script will:
1. ✅ Check all required files
2. ✅ Create `static/uploads/medicines/` directory if needed
3. ✅ Initialize SQLite database and tables
4. ✅ Load all medicines from CSV
5. ✅ Test RAG search functionality
6. ✅ Create `.env` file template

### Step 2: Configure Environment (Optional)

Edit `.env` file if needed:
```
# Database (SQLite used by default)
# DATABASE_URL=sqlite:///red_dot_pharmacy.db

# Flask
SESSION_SECRET=your-secret-key

# APIs (if using external services)
GOOGLE_API_KEY=your-gemini-api-key
```

### Step 3: Verify Installation

```bash
# Test database
python
>>> from app import create_app
>>> app = create_app()
>>> from models import Medicine
>>> with app.app_context():
...     count = Medicine.query.count()
...     print(f"Medicines loaded: {count}")
```

### Step 4: Start the Application

```bash
python main.py
```

Navigate to `http://localhost:5000`

## How the RAG System Works with SQLite

### Query Flow

1. **User Query** → "Where can I find Panadol?"

2. **Query Classifier** → Identifies as medication query

3. **Medicine Search** (SQLite):
   ```python
   from services.sqlite_medicine_search import MedicineSearchService
   
   results = MedicineSearchService.multi_field_search("Panadol", limit=5)
   # Returns: [{'id': 35, 'name': 'Panadol 500mg', 'image_url': '/static/uploads/medicines/1.jpeg', ...}]
   ```

4. **Image Retrieval**:
   - `image_path` from database: `/static/uploads/medicines/1.jpeg`
   - Served from: `static/uploads/medicines/1.jpeg`
   - URL to user: `http://localhost:5000/static/uploads/medicines/1.jpeg`

5. **Formatted Response**:
   ```json
   {
     "medicines": [
       {
         "id": 35,
         "name": "Panadol 500mg",
         "price": 60,
         "image_url": "/static/uploads/medicines/1.jpeg",
         "description": "...",
         "status": "in_stock"
       }
     ]
   }
   ```

### SQLite Query Examples

**Search by Name**:
```python
from services.sqlite_medicine_search import MedicineSearchService
results = MedicineSearchService.search_by_name("Panadol")
```

**Search by Ingredient**:
```python
results = MedicineSearchService.search_by_chemical("Paracetamol")
```

**Search In Stock Only**:
```python
results = MedicineSearchService.search_in_stock("Aspirin")
```

**Price Range**:
```python
results = MedicineSearchService.get_medicines_by_price_range(100, 500)
```

**Autocomplete**:
```python
suggestions = MedicineSearchService.autocomplete("Pan")
# Returns: ['Panadol 500mg', 'Panadol Extra', ...]
```

## Database Schema

### medicines table

```sql
CREATE TABLE medicines (
    id INTEGER PRIMARY KEY,
    name VARCHAR(160) NOT NULL,
    chemical VARCHAR(160),
    description TEXT,
    price INTEGER NOT NULL,
    stock_quantity INTEGER DEFAULT 0,
    category VARCHAR(100),
    status VARCHAR(30) DEFAULT 'in_stock',
    image_path VARCHAR(255),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
```

## Key Features

### 1. Backward Compatibility

All existing code continues to work:
```python
# Old code (still works)
from services.medicine_rag import search_medicines
results = search_medicines("Panadol")

# New code (recommended)
from services.sqlite_medicine_search import MedicineSearchService
results = MedicineSearchService.multi_field_search("Panadol")
```

### 2. Dual Database Support

- **Development**: SQLite (local file)
- **Production (Replit)**: PostgreSQL (via `DATABASE_URL`)
- No code changes needed - SQLAlchemy handles both

### 3. Image Linking

- CSV contains `image_path` column
- Each medicine directly linked to one image
- Path format: `/static/uploads/medicines/{id}.{ext}`

### 4. Full-Text Search

SQLite supports LIKE patterns:
```python
# Fuzzy search
results = MedicineSearchService.multi_field_search("pan%")

# Case-insensitive
results = MedicineSearchService.search_by_name("PANADOL")
```

## Troubleshooting

### Issue: "medicines_export.csv not found"

**Solution**:
```bash
# Check file location
ls medicines_export.csv

# Run setup from correct directory
python setup_local_db.py
```

### Issue: Images not displaying

**Check**:
1. Image files exist: `static/uploads/medicines/1.jpeg`
2. CSV contains correct path: `/static/uploads/medicines/1.jpeg`
3. Flask serving static files correctly

```bash
# Test static file
# Navigate to: http://localhost:5000/static/uploads/medicines/1.jpeg
```

### Issue: Database locked (SQLite)

**Solution**:
```python
# Close all connections
# Restart the application
# SQLite will auto-recover

# Or delete and recreate
rm red_dot_pharmacy.db
python setup_local_db.py
```

### Issue: Search returns no results

**Check**:
1. Medicines are loaded: `python setup_local_db.py` verify step
2. Search term matches data: Try exact medicine name
3. Medicine status is "in_stock"

```python
from app import create_app
from models import Medicine

app = create_app()
with app.app_context():
    med = Medicine.query.first()
    print(med.name, med.chemical, med.image_path)
```

## Performance Tips

### 1. Index Creation (Optional)

For large datasets, SQLite automatically creates indexes. To manually optimize:

```python
from app import db

# Run in app context
db.session.execute('''
    CREATE INDEX IF NOT EXISTS idx_medicine_name 
    ON medicines(name)
''')
```

### 2. Query Optimization

Use specific search methods instead of loading all data:

```python
# ❌ Slow (loads all)
all_meds = Medicine.query.all()
result = [m for m in all_meds if 'Panadol' in m.name]

# ✅ Fast (filtered at DB level)
result = MedicineSearchService.search_by_name("Panadol")
```

### 3. Caching

For frequently used data:

```python
from flask_caching import Cache

cache = Cache(app, config={'CACHE_TYPE': 'simple'})

@cache.cached(timeout=300)
def get_all_categories():
    return MedicineSearchService.get_all_medicines()
```

## Integration with RAG System

### Smart RAG Orchestrator

The RAG system automatically uses SQLite:

```python
from services.smart_rag_orchestrator import SmartRAGOrchestrator

orchestrator = SmartRAGOrchestrator()
result = orchestrator.retrieve("Where can I get panadol?")

# result contains:
# - medications: [list from SQLite search]
# - wiki_context: [from Wikipedia if needed]
# - images: [validated image paths]
```

### RAG Engine

```python
from agent.rag_engine import MedicalRAGEngine

engine = MedicalRAGEngine()
response = engine.process_query_sync("Tell me about Panadol")

# response.medications: [from SQLite]
# response.image_paths: [validated local paths]
```

## Migration from PostgreSQL (If Needed)

If you have an existing PostgreSQL database and want to migrate:

```python
# Export from PostgreSQL
# python export_medicines_to_csv.py

# Then import to SQLite
# python setup_local_db.py
```

## Development Workflow

### Local Development

```bash
# 1. Setup
python setup_local_db.py

# 2. Run app
python main.py

# 3. Test RAG
# Navigate to chatbot and search for medicines

# 4. Add new medicine (via admin or code)
from models import Medicine
from app import db, create_app

app = create_app()
with app.app_context():
    med = Medicine(name="New Med", chemical="Ingredient", price=100)
    db.session.add(med)
    db.session.commit()
```

### Testing

```python
# Test search
from services.sqlite_medicine_search import MedicineSearchService

results = MedicineSearchService.search_by_name("Panadol")
assert len(results) > 0
assert results[0]['price'] > 0
assert 'image_url' in results[0]
```

## Production Deployment

On Replit:
1. Set `DATABASE_URL` in Secrets (PostgreSQL)
2. No code changes needed
3. App automatically uses PostgreSQL

```bash
# Set in Replit Secrets
DATABASE_URL=postgresql://user:pass@host/dbname

# Run normally
python main.py
# App detects DATABASE_URL and uses PostgreSQL
```

## Files Changed/Created

### New Files
- `services/sqlite_medicine_search.py` - SQLite-optimized search
- `database_loader.py` - CSV to SQLite loader
- `setup_local_db.py` - Automated setup script
- `config.py` - Configuration management
- `SQLITE_MIGRATION.md` - This file

### Modified Files
- `services/medicine_rag.py` - Added SQLite imports
- `app.py` - Uses SQLite by default
- `models.py` - No changes (already compatible)

## Support & Questions

If you encounter issues:

1. Check this guide
2. Run: `python setup_local_db.py` (it has troubleshooting)
3. Check database: `python -c "from models import Medicine; from app import create_app; app = create_app(); print(Medicine.query.count())"`
4. Verify images: `ls static/uploads/medicines/`

