#!/usr/bin/env python3
"""
Red Dot Pharmacy - SQLite Local Setup Script
This script initializes the local SQLite database and loads medicine data from CSV
"""

import os
import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def print_header(title: str):
    """Print a formatted header"""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")


def check_requirements():
    """Check if required files exist"""
    required_files = [
        'app.py',
        'models.py',
        'medicines_export.csv',
        'database_loader.py',
        'config.py'
    ]
    
    logger.info("🔍 Checking required files...")
    
    missing = []
    for file in required_files:
        if not os.path.exists(file):
            missing.append(file)
            logger.error(f"  ❌ Missing: {file}")
        else:
            logger.info(f"  ✅ Found: {file}")
    
    if missing:
        logger.error(f"\n❌ Missing {len(missing)} required files")
        return False
    
    logger.info("✅ All required files found\n")
    return True


def check_images_directory():
    """Check if medicine images directory exists"""
    images_dir = Path("static/uploads/medicines")
    
    logger.info("🔍 Checking images directory...")
    
    if images_dir.exists():
        image_files = list(images_dir.glob("*"))
        logger.info(f"  ✅ Directory exists: {images_dir}")
        logger.info(f"  📊 Contains {len(image_files)} image files")
        return True
    else:
        logger.warning(f"  ⚠️ Images directory not found: {images_dir}")
        logger.info("     Creating directory...")
        images_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"  ✅ Created: {images_dir}")
        return False


def initialize_database():
    """Create SQLite database and tables"""
    logger.info("📦 Initializing SQLite database...")
    
    try:
        from app import create_app, db
        
        app = create_app()
        with app.app_context():
            # Create all tables
            db.create_all()
            logger.info("  ✅ Database tables created successfully")
            
            # Show database info
            db_uri = app.config['SQLALCHEMY_DATABASE_URI']
            logger.info(f"  📍 Database: {db_uri}")
            
            return True
            
    except Exception as e:
        logger.error(f"  ❌ Failed to initialize database: {e}")
        return False


def load_medicines():
    """Load medicines from CSV into database"""
    logger.info("📚 Loading medicines from CSV...")
    
    try:
        from database_loader import load_medicines_from_csv, verify_medicines_loaded, get_medicine_statistics
        
        # Load medicines
        loaded_count = load_medicines_from_csv("medicines_export.csv")
        
        if loaded_count > 0:
            logger.info(f"\n  ✅ Successfully loaded {loaded_count} medicines")
            
            # Verify
            if verify_medicines_loaded():
                # Get statistics
                stats = get_medicine_statistics()
                logger.info("\n  📈 Medicine Statistics:")
                logger.info(f"     Total medicines: {stats['total_medicines']}")
                logger.info(f"     Average price: Rs. {stats['average_price']}")
                logger.info(f"     With images: {stats['medicines_with_images']}")
                logger.info(f"     Categories: {len(stats['categories'])}")
                
                return True
        else:
            logger.warning("  ⚠️ No medicines were loaded")
            return False
            
    except Exception as e:
        logger.error(f"  ❌ Failed to load medicines: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_rag_search():
    """Test basic RAG medicine search"""
    logger.info("🧪 Testing medicine search...")
    
    try:
        from app import create_app
        from services.medicine_rag import search_medicines, get_medicine_by_name
        
        app = create_app()
        with app.app_context():
            # Test search
            results = search_medicines("panadol", limit=3)
            
            if results:
                logger.info(f"  ✅ Search found {len(results)} results")
                for med in results[:1]:
                    logger.info(f"     Medicine: {med['name']}")
                    logger.info(f"     Price: Rs. {med['price']}")
                    logger.info(f"     Image: {med.get('image_url', 'No image')}")
                return True
            else:
                logger.warning("  ⚠️ Search found no results")
                return False
                
    except Exception as e:
        logger.error(f"  ❌ Search test failed: {e}")
        return False


def create_env_file():
    """Create a .env file template"""
    env_file = Path(".env")
    
    if env_file.exists():
        logger.info("📝 .env file already exists")
        return True
    
    logger.info("📝 Creating .env file...")
    
    env_content = """# Red Dot Pharmacy - Environment Configuration

# Database
# For local development, SQLite is used by default
# DATABASE_URL=sqlite:///red_dot_pharmacy.db

# For production on Replit, PostgreSQL is used via DATABASE_URL from Secrets

# Flask
SESSION_SECRET=red-dot-pharmacy-dev-secret-key

# Google Gemini API (for RAG system)
# GOOGLE_API_KEY=your-gemini-api-key-here

# Google Calendar OAuth
# GOOGLE_SERVICE_ACCOUNT_KEY=path-to-service-account-json

# Flask Environment
FLASK_ENV=development
FLASK_DEBUG=1
"""
    
    try:
        env_file.write_text(env_content)
        logger.info("  ✅ Created .env file")
        logger.info("     Please add your API keys to .env file")
        return True
    except Exception as e:
        logger.error(f"  ❌ Failed to create .env: {e}")
        return False


def print_summary(results: dict):
    """Print setup summary"""
    print_header("Setup Summary")
    
    status = {
        'Requirements': '✅' if results.get('requirements') else '❌',
        'Images Directory': '✅' if results.get('images') else '⚠️',
        'Database': '✅' if results.get('database') else '❌',
        'Medicines Loaded': '✅' if results.get('medicines') else '❌',
        'RAG Search': '✅' if results.get('search') else '⚠️',
        'Environment File': '✅' if results.get('env') else '⚠️',
    }
    
    for component, status_icon in status.items():
        print(f"  {status_icon} {component}")
    
    print()
    
    if all(results.values()):
        print("✅ Setup completed successfully!")
        print("\n📋 Next steps:")
        print("  1. Review the .env file and add your API keys")
        print("  2. Start the app: python main.py")
        print("  3. Navigate to http://localhost:5000")
        print("  4. Test the chatbot with medicine searches")
    else:
        print("⚠️ Some steps completed with warnings")
        print("   Please review the errors above")
    
    print()


def main():
    """Main setup function"""
    print_header("Red Dot Pharmacy - SQLite Local Setup")
    
    results = {
        'requirements': False,
        'images': False,
        'database': False,
        'medicines': False,
        'search': False,
        'env': False,
    }
    
    # Step 1: Check requirements
    results['requirements'] = check_requirements()
    if not results['requirements']:
        print_summary(results)
        return False
    
    # Step 2: Check/create images directory
    results['images'] = check_images_directory()
    
    # Step 3: Initialize database
    results['database'] = initialize_database()
    if not results['database']:
        print_summary(results)
        return False
    
    # Step 4: Load medicines
    results['medicines'] = load_medicines()
    
    # Step 5: Test RAG search
    if results['medicines']:
        results['search'] = test_rag_search()
    
    # Step 6: Create .env file
    results['env'] = create_env_file()
    
    # Print summary
    print_summary(results)
    
    return all(results.values())


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("\n\n❌ Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n\n❌ Setup failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
