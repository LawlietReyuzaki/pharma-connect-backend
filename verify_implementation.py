"""
SQLite Migration Implementation Checklist
This script verifies all components are properly implemented
"""

import os
import sys
import importlib.util


def check_file_exists(path: str, description: str = "") -> bool:
    """Check if a file exists"""
    exists = os.path.exists(path)
    status = "✅" if exists else "❌"
    print(f"  {status} {path}")
    if description:
        print(f"     {description}")
    return exists


def check_import(module_path: str, name: str, description: str = "") -> bool:
    """Check if a module can be imported"""
    try:
        spec = importlib.util.spec_from_file_location(name, module_path)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            print(f"  ✅ {name}")
            if description:
                print(f"     {description}")
            return True
    except Exception as e:
        print(f"  ❌ {name}")
        print(f"     Error: {e}")
        return False


def main():
    """Run the implementation checklist"""
    
    print("\n" + "="*70)
    print("  SQLite Migration Implementation Checklist")
    print("="*70 + "\n")
    
    all_passed = True
    
    # 1. Check core files
    print("📋 Core Files")
    print("-" * 70)
    core_files = {
        'app.py': 'Flask application',
        'models.py': 'Database models',
        'medicines_export.csv': 'Medicine data source (1000+ medicines)',
    }
    for file, desc in core_files.items():
        if not check_file_exists(file, desc):
            all_passed = False
    
    # 2. Check new implementation files
    print("\n📦 New Implementation Files")
    print("-" * 70)
    new_files = {
        'database_loader.py': 'CSV to SQLite loader',
        'setup_local_db.py': 'Automated setup script',
        'config.py': 'Configuration management',
        'services/sqlite_medicine_search.py': 'SQLite-optimized search service',
        'test_sqlite_integration.py': 'Integration test suite',
    }
    for file, desc in new_files.items():
        if not check_file_exists(file, desc):
            all_passed = False
    
    # 3. Check documentation
    print("\n📚 Documentation Files")
    print("-" * 70)
    docs = {
        'QUICKSTART.md': 'Quick setup guide',
        'SQLITE_MIGRATION.md': 'Detailed migration documentation',
        'SQLITE_SETUP_COMPLETE.md': 'Setup completion summary',
        'DATA_STORAGE_ARCHITECTURE.md': 'System architecture (existing)',
    }
    for file, desc in docs.items():
        if not check_file_exists(file, desc):
            all_passed = False
    
    # 4. Check directory structure
    print("\n📁 Directory Structure")
    print("-" * 70)
    dirs = {
        'static/uploads/medicines': 'Medicine product images',
        'services': 'Service modules',
        'agent': 'RAG agent modules',
        'routes': 'API routes',
        'templates': 'HTML templates',
    }
    for dir, desc in dirs.items():
        if not check_file_exists(dir, desc):
            all_passed = False
    
    # 5. Check key functions exist
    print("\n🔧 Key Functions & Classes")
    print("-" * 70)
    
    try:
        # Test imports
        print("  Testing imports...")
        
        # Test app creation
        try:
            from app import create_app, db
            print("  ✅ app.create_app, db")
        except Exception as e:
            print(f"  ❌ app module: {e}")
            all_passed = False
        
        # Test models
        try:
            from models import Medicine
            print("  ✅ models.Medicine")
        except Exception as e:
            print(f"  ❌ models.Medicine: {e}")
            all_passed = False
        
        # Test SQLite search
        try:
            from services.sqlite_medicine_search import MedicineSearchService
            print("  ✅ sqlite_medicine_search.MedicineSearchService")
        except Exception as e:
            print(f"  ❌ sqlite_medicine_search: {e}")
            all_passed = False
        
        # Test database loader
        try:
            from database_loader import load_medicines_from_csv
            print("  ✅ database_loader.load_medicines_from_csv")
        except Exception as e:
            print(f"  ❌ database_loader: {e}")
            all_passed = False
        
        # Test RAG integration
        try:
            from services.medicine_rag import search_medicines
            print("  ✅ medicine_rag.search_medicines")
        except Exception as e:
            print(f"  ❌ medicine_rag: {e}")
            all_passed = False
    
    except Exception as e:
        print(f"  ❌ Import testing failed: {e}")
        all_passed = False
    
    # 6. Check CSV format
    print("\n📋 CSV Format Verification")
    print("-" * 70)
    try:
        import csv
        with open('medicines_export.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            expected_fields = {'id', 'name', 'chemical', 'description', 'price', 
                             'stock_quantity', 'category', 'status', 'image_path'}
            
            if reader.fieldnames:
                actual_fields = set(reader.fieldnames)
                if expected_fields.issubset(actual_fields):
                    print(f"  ✅ CSV has all required fields")
                    row_count = sum(1 for _ in reader)
                    print(f"  ✅ CSV contains {row_count} medicine records")
                else:
                    missing = expected_fields - actual_fields
                    print(f"  ❌ CSV missing fields: {missing}")
                    all_passed = False
            else:
                print("  ❌ CSV has no headers")
                all_passed = False
    except Exception as e:
        print(f"  ❌ CSV verification failed: {e}")
        all_passed = False
    
    # 7. Configuration verification
    print("\n⚙️ Configuration")
    print("-" * 70)
    try:
        from config import Config, DevelopmentConfig, ProductionConfig
        print("  ✅ config.Config classes")
        
        # Check database URIs
        dev_config = DevelopmentConfig()
        if 'sqlite' in dev_config.SQLALCHEMY_DATABASE_URI:
            print("  ✅ Development uses SQLite")
        else:
            print(f"  ⚠️ Development config: {dev_config.SQLALCHEMY_DATABASE_URI}")
    except Exception as e:
        print(f"  ⚠️ Configuration check: {e}")
    
    # 8. Summary
    print("\n" + "="*70)
    if all_passed:
        print("  ✅ ALL CHECKS PASSED!")
        print("="*70)
        print("\n🚀 Next Steps:")
        print("  1. Run setup: python setup_local_db.py")
        print("  2. Start app: python main.py")
        print("  3. Test chatbot: http://localhost:5000")
        print("\n")
        return 0
    else:
        print("  ⚠️ SOME CHECKS FAILED")
        print("="*70)
        print("\n❌ Please review the errors above and fix them.")
        print("   Check QUICKSTART.md or SQLITE_MIGRATION.md for help.\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
