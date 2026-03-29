#!/usr/bin/env python3
"""
Direct Database Setup - Simplified version that creates and populates SQLite database
"""

import os
import sys
import csv
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def setup_database():
    """Setup database directly"""
    try:
        logger.info("=" * 70)
        logger.info("Red Dot Pharmacy - Direct Database Setup")
        logger.info("=" * 70)
        
        # Step 1: Import app
        logger.info("\n📦 Step 1: Importing Flask app...")
        try:
            from app import create_app, db
            logger.info("✅ App imported successfully")
        except Exception as e:
            logger.error(f"❌ Failed to import app: {e}")
            return False
        
        # Step 2: Create app context
        logger.info("\n📦 Step 2: Creating app context...")
        try:
            app = create_app()
            logger.info("✅ App context created")
        except Exception as e:
            logger.error(f"❌ Failed to create app: {e}")
            return False
        
        # Step 3: Initialize database tables
        logger.info("\n📦 Step 3: Initializing database tables...")
        try:
            with app.app_context():
                db.create_all()
                logger.info(f"✅ Database initialized: {app.config['SQLALCHEMY_DATABASE_URI']}")
        except Exception as e:
            logger.error(f"❌ Failed to initialize database: {e}")
            return False
        
        # Step 4: Load medicines from CSV
        logger.info("\n📦 Step 4: Loading medicines from CSV...")
        try:
            from models import Medicine
            
            with app.app_context():
                # Check if already loaded
                existing = Medicine.query.count()
                if existing > 0:
                    logger.warning(f"⚠️ Database already has {existing} medicines")
                    logger.info("Clearing existing medicines...")
                    Medicine.query.delete()
                    db.session.commit()
                
                # Load from CSV
                csv_path = "medicines_export.csv"
                if not os.path.exists(csv_path):
                    logger.error(f"❌ CSV file not found: {csv_path}")
                    return False
                
                loaded = 0
                failed = 0
                
                with open(csv_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    batch = []
                    
                    for row in reader:
                        try:
                            medicine = Medicine(
                                name=row.get('name', '').strip(),
                                chemical=row.get('chemical', '').strip(),
                                description=row.get('description', '').strip(),
                                price=float(row.get('price', 0)),
                                image_path=row.get('image_path', '').strip(),
                                stock_quantity=int(row.get('stock_quantity', 0)),
                                category=row.get('category', '').strip(),
                                status=row.get('status', 'active').strip()
                            )
                            batch.append(medicine)
                            
                            # Commit in batches
                            if len(batch) >= 100:
                                db.session.add_all(batch)
                                db.session.commit()
                                loaded += len(batch)
                                batch = []
                        except Exception as row_error:
                            failed += 1
                            logger.warning(f"⚠️ Failed to load row: {row_error}")
                    
                    # Commit remaining
                    if batch:
                        db.session.add_all(batch)
                        db.session.commit()
                        loaded += len(batch)
                
                logger.info(f"✅ Loaded {loaded} medicines")
                if failed > 0:
                    logger.warning(f"⚠️ Failed to load {failed} medicines")
                
        except Exception as e:
            logger.error(f"❌ Failed to load medicines: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
        
        # Step 5: Verify
        logger.info("\n📦 Step 5: Verifying setup...")
        try:
            with app.app_context():
                count = Medicine.query.count()
                logger.info(f"✅ Total medicines in database: {count}")
                
                # Get sample
                sample = Medicine.query.first()
                if sample:
                    logger.info(f"✅ Sample medicine: {sample.name} - Rs. {sample.price}")
        except Exception as e:
            logger.error(f"❌ Verification failed: {e}")
            return False
        
        # Step 6: Check images
        logger.info("\n📦 Step 6: Checking images...")
        try:
            images_path = Path("static/uploads/medicines")
            if images_path.exists():
                image_count = len(list(images_path.glob("*")))
                logger.info(f"✅ Found {image_count} image files")
            else:
                logger.warning(f"⚠️ Images directory not found: {images_path}")
        except Exception as e:
            logger.warning(f"⚠️ Could not check images: {e}")
        
        logger.info("\n" + "=" * 70)
        logger.info("✅ DATABASE SETUP COMPLETED SUCCESSFULLY!")
        logger.info("=" * 70)
        logger.info("\n🚀 Next steps:")
        logger.info("   1. Run: python main.py")
        logger.info("   2. Open: http://localhost:5000")
        logger.info("   3. Test the chatbot!")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = setup_database()
    sys.exit(0 if success else 1)
