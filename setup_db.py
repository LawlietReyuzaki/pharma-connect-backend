#!/usr/bin/env python3
"""
Minimal Database Setup - Avoids circular imports
"""

import os
import sys
import csv
import logging
import sqlite3
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def setup_db_minimal():
    """Setup database using minimal approach"""
    try:
        logger.info("=" * 70)
        logger.info("Red Dot Pharmacy - Database Setup")
        logger.info("=" * 70)
        
        # Step 1: Create database file and tables
        logger.info("\n📦 Step 1: Creating SQLite database...")
        db_path = "red_dot_pharmacy.db"
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create medicines table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS medicines (
                id INTEGER PRIMARY KEY,
                name VARCHAR(160) NOT NULL,
                chemical VARCHAR(160),
                description TEXT,
                price INTEGER NOT NULL,
                image_path VARCHAR(255),
                status VARCHAR(30) DEFAULT 'in_stock',
                stock_quantity INTEGER DEFAULT 0,
                category VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        logger.info(f"✅ Database created: {db_path}")
        
        # Step 2: Load CSV data
        logger.info("\n📦 Step 2: Loading medicines from CSV...")
        csv_path = "medicines_export.csv"
        
        if not os.path.exists(csv_path):
            logger.error(f"❌ CSV file not found: {csv_path}")
            return False
        
        # Clear existing medicines
        cursor.execute('DELETE FROM medicines')
        conn.commit()
        logger.info("✅ Cleared existing medicines")
        
        # Load from CSV
        loaded = 0
        failed = 0
        
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                try:
                    name = row.get('name', '').strip()
                    chemical = row.get('chemical', '').strip()
                    description = row.get('description', '').strip()
                    price = float(row.get('price', 0))
                    image_path = row.get('image_path', '').strip()
                    stock_quantity = int(row.get('stock_quantity', 0))
                    category = row.get('category', '').strip()
                    status = row.get('status', 'in_stock').strip()
                    
                    cursor.execute('''
                        INSERT INTO medicines 
                        (name, chemical, description, price, image_path, status, stock_quantity, category)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (name, chemical, description, price, image_path, status, stock_quantity, category))
                    loaded += 1
                    
                except Exception as e:
                    failed += 1
                    if failed <= 5:  # Log first 5 errors
                        logger.warning(f"⚠️ Row error: {e}")
            
            conn.commit()
        
        logger.info(f"✅ Loaded {loaded} medicines")
        if failed > 0:
            logger.warning(f"⚠️ Failed to load {failed} rows")
        
        # Step 3: Verify
        logger.info("\n📦 Step 3: Verifying data...")
        cursor.execute('SELECT COUNT(*) FROM medicines')
        count = cursor.fetchone()[0]
        logger.info(f"✅ Total medicines in database: {count}")
        
        # Show sample
        cursor.execute('SELECT name, price FROM medicines LIMIT 1')
        sample = cursor.fetchone()
        if sample:
            logger.info(f"✅ Sample: {sample[0]} - Rs. {sample[1]}")
        
        # Step 4: Check images
        logger.info("\n📦 Step 4: Checking images...")
        images_path = Path("static/uploads/medicines")
        if images_path.exists():
            image_count = len(list(images_path.glob("*")))
            logger.info(f"✅ Found {image_count} image files")
        else:
            logger.warning(f"⚠️ Images directory not found: {images_path}")
        
        # Step 5: Show statistics
        logger.info("\n📦 Step 5: Database statistics...")
        cursor.execute('SELECT category, COUNT(*) FROM medicines GROUP BY category')
        categories = cursor.fetchall()
        logger.info(f"✅ Categories found: {len(categories)}")
        for cat, cnt in categories[:5]:
            logger.info(f"   - {cat}: {cnt} medicines")
        
        cursor.execute('SELECT MIN(price), MAX(price), AVG(price) FROM medicines')
        min_p, max_p, avg_p = cursor.fetchone()
        logger.info(f"✅ Price range: Rs. {min_p} - Rs. {max_p} (avg: Rs. {int(avg_p)})")
        
        cursor.execute('SELECT COUNT(*) FROM medicines WHERE image_path IS NOT NULL AND image_path != ""')
        with_images = cursor.fetchone()[0]
        logger.info(f"✅ Medicines with images: {with_images}/{count}")
        
        conn.close()
        
        logger.info("\n" + "=" * 70)
        logger.info("✅ DATABASE SETUP COMPLETED SUCCESSFULLY!")
        logger.info("=" * 70)
        logger.info("\n🚀 Next steps:")
        logger.info("   1. Run: python main.py")
        logger.info("   2. Open: http://localhost:5000")
        logger.info("   3. Test the chatbot!")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = setup_db_minimal()
    sys.exit(0 if success else 1)
