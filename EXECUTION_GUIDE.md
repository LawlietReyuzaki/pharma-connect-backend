# 🚀 SQLite Migration - Execution Guide

## Step-by-Step Instructions

### Step 1: Navigate to Project Directory
```bash
cd "c:\Users\Hassan\Desktop\red  dot\UrduBotBooker"
```

### Step 2: Run Setup (One Command)
```bash
python setup_local_db.py
```

**This will:**
- ✅ Check all required files
- ✅ Create `static/uploads/medicines/` if needed  
- ✅ Create SQLite database (`red_dot_pharmacy.db`)
- ✅ Create all database tables
- ✅ Load 1000+ medicines from CSV
- ✅ Validate medicine data
- ✅ Test search functionality
- ✅ Create `.env` file
- ✅ Display statistics

**Expected Output:**
```
==================================================================
  Red Dot Pharmacy - SQLite Local Setup
==================================================================

📋 Checking required files...
  ✅ Found: medicines_export.csv
  ✅ Found: app.py
  ... etc ...

📷 Checking images directory...
  ✅ Directory exists: static/uploads/medicines
  📊 Contains 1000+ image files

📦 Initializing SQLite database...
  ✅ Database tables created successfully
  📍 Database: sqlite:///red_dot_pharmacy.db

📚 Loading medicines from CSV...
  ✅ Successfully loaded 1000+ medicines

🧪 Testing medicine search...
  ✅ Search found results

==================================================================
Setup Summary
==================================================================
  ✅ Requirements
  ✅ Images Directory
  ✅ Database
  ✅ Medicines Loaded
  ✅ RAG Search
  ✅ Environment File
==================================================================

✅ Setup completed successfully!
```

### Step 3: Verify Installation (Optional)
```bash
python verify_implementation.py
```

**This will verify:**
- ✅ All required files exist
- ✅ Images directory and files
- ✅ Database creation
- ✅ Medicine loading
- ✅ Search functionality
- ✅ Image linking
- ✅ RAG integration
- ✅ Database statistics

### Step 4: Run Tests (Optional)
```bash
python test_sqlite_integration.py
```

**This will test:**
- ✅ Required files
- ✅ Images directory
- ✅ Database initialization
- ✅ Medicine loading
- ✅ Search functionality
- ✅ Image linking
- ✅ RAG integration
- ✅ Database statistics

### Step 5: Start the Application
```bash
python main.py
```

**Expected Output:**
```
 * Serving Flask app 'app'
 * Debug mode: on
 * Running on http://127.0.0.1:5000
 * Press CTRL+C to quit
```

### Step 6: Access the Application

Open your browser and go to:
**http://localhost:5000**

You should see:
- ✅ Chatbot interface
- ✅ Medicine search functionality
- ✅ Product images loading

### Step 7: Test the Chatbot

Try asking questions like:
- "Where can I find Panadol?"
- "What medicines treat fever?"
- "Show me medicines under 500 rupees"
- "Tell me about Aspirin"

You should see:
- ✅ Medicine names
- ✅ Prices (in PKR)
- ✅ Product descriptions
- ✅ Active ingredients
- ✅ Product images

---

## Troubleshooting Commands

### Check if medicines are loaded
```bash
python -c "
from app import create_app
from models import Medicine

app = create_app()
with app.app_context():
    count = Medicine.query.count()
    if count > 0:
        print(f'✅ Medicines loaded: {count}')
        med = Medicine.query.first()
        print(f'   Sample: {med.name} - Rs.{med.price}')
        print(f'   Image: {med.image_path}')
    else:
        print('❌ No medicines in database')
        print('   Run: python setup_local_db.py')
"
```

### Test medicine search
```bash
python -c "
from services.sqlite_medicine_search import MedicineSearchService

results = MedicineSearchService.search_by_name('panadol')
print(f'Search results: {len(results)}')
for r in results[:2]:
    print(f'  - {r[\"name\"]}: Rs.{r[\"price\"]}')
"
```

### Count image files
```bash
# Windows PowerShell
(Get-ChildItem "static\uploads\medicines" -File).Count

# Or bash
ls static/uploads/medicines | wc -l
```

### Reset database
```bash
# Delete the database file
rm red_dot_pharmacy.db

# Reload from CSV
python setup_local_db.py
```

---

## Quick Reference

| Task | Command |
|------|---------|
| **Full Setup** | `python setup_local_db.py` |
| **Start App** | `python main.py` |
| **Verify Setup** | `python verify_implementation.py` |
| **Run Tests** | `python test_sqlite_integration.py` |
| **Reload Data** | `python database_loader.py medicines_export.csv` |
| **Check Status** | `python verify_implementation.py` |
| **Browser** | Open `http://localhost:5000` |

---

## Expected File Structure After Setup

```
UrduBotBooker/
├── red_dot_pharmacy.db              ← Created by setup
├── medicines_export.csv             ← Already exists
├── .env                             ← Created by setup
├── app.py
├── models.py
├── main.py
├── database_loader.py
├── setup_local_db.py
├── config.py
├── verify_implementation.py
├── test_sqlite_integration.py
│
├── services/
│   ├── sqlite_medicine_search.py
│   ├── medicine_rag.py
│   └── ...
│
├── static/
│   └── uploads/
│       └── medicines/               ← Already exists (1000+ images)
│
└── ... (other files)
```

---

## Environment Variables

### Default (.env created by setup)
```
FLASK_ENV=development
FLASK_DEBUG=1
SESSION_SECRET=red-dot-pharmacy-dev-secret-key
# DATABASE_URL defaults to SQLite
```

### Optional Customization
Edit `.env` after setup if needed:
```
FLASK_ENV=development
FLASK_DEBUG=1
SESSION_SECRET=your-custom-secret
DATABASE_URL=sqlite:///red_dot_pharmacy.db
```

---

## Database Files

### Primary Database
- **File**: `red_dot_pharmacy.db`
- **Type**: SQLite
- **Size**: ~50MB
- **Location**: Project root
- **Created by**: `setup_local_db.py`

### CSV Data Source
- **File**: `medicines_export.csv`
- **Type**: CSV
- **Records**: 1000+
- **Columns**: id, name, chemical, description, price, stock_quantity, category, status, image_path
- **Already exists**: Yes

### Image Files
- **Location**: `static/uploads/medicines/`
- **Count**: 1000+
- **Formats**: .jpg, .png, .jpeg
- **Already exists**: Yes

---

## Common Issues & Quick Fixes

### Issue: "medicines_export.csv not found"
**Fix**: Check file exists in project root
```bash
ls medicines_export.csv  # or dir medicines_export.csv on Windows
```

### Issue: No medicines after setup
**Fix**: Re-run setup with verbose output
```bash
python database_loader.py medicines_export.csv
```

### Issue: Images not showing
**Fix**: Check images directory
```bash
ls static/uploads/medicines | head  # Should show image files
```

### Issue: "Database is locked"
**Fix**: Restart the application
```bash
# Ctrl+C to stop
python main.py  # Start again
```

### Issue: Port 5000 already in use
**Fix**: Kill process using port 5000 or use different port
```bash
# Windows PowerShell
Get-Process -Id (Get-NetTCPConnection -LocalPort 5000).OwningProcess | Stop-Process -Force

# Or run on different port
python main.py --port 5001
```

---

## Next Steps After Setup

1. ✅ Run `python setup_local_db.py`
2. ✅ Run `python main.py`
3. ✅ Open `http://localhost:5000`
4. ✅ Test the chatbot
5. ✅ Add/edit medicines via admin panel (`http://localhost:5000/admin`)
6. ✅ Upload new medicine images

---

## Deployment Options

### Local Development
```bash
# One-time setup
python setup_local_db.py

# Run app
python main.py

# Database: SQLite (local file)
# Type: sqlite:///red_dot_pharmacy.db
```

### Replit Production
```bash
# Set DATABASE_URL in Secrets (PostgreSQL)
# No setup needed, just run:
python main.py

# App auto-detects PostgreSQL and uses it
```

---

## Support

**If you encounter any issues:**

1. Read: `QUICKSTART.md`
2. Check: `SQLITE_MIGRATION.md`
3. Run: `python verify_implementation.py`
4. Test: `python test_sqlite_integration.py`

---

## You're Ready! 🎉

Everything is set up and ready to go.

```bash
python setup_local_db.py
python main.py
```

Then visit: **http://localhost:5000**

**Enjoy using Red Dot Pharmacy locally!** 🚀
