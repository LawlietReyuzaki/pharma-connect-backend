"""
SQLite Database Loader for Red Dot Pharmacy
Loads medicines from medicines_export.csv into SQLite database
"""

import os
import csv
import logging
from pathlib import Path
from datetime import datetime
from app import create_app, db
from models import Medicine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_medicines_from_csv(csv_file_path: str = "medicines_export.csv") -> int:
    """
    Load medicines from CSV into SQLite database.
    
    Args:
        csv_file_path: Path to the medicines_export.csv file
        
    Returns:
        Number of medicines loaded
    """
    app = create_app()
    
    with app.app_context():
        # Create all tables first
        db.create_all()
        logger.info("✅ Database tables created")
        
        # Check if CSV exists
        if not os.path.exists(csv_file_path):
            logger.error(f"❌ CSV file not found: {csv_file_path}")
            return 0
        
        # Check if medicines already exist
        existing_count = Medicine.query.count()
        if existing_count > 0:
            logger.warning(f"⚠️ Database already contains {existing_count} medicines")
            response = input("Overwrite existing medicines? (yes/no): ")
            if response.lower() != 'yes':
                logger.info("Operation cancelled")
                return 0
            else:
                # Clear existing medicines
                Medicine.query.delete()
                db.session.commit()
                logger.info("✅ Existing medicines cleared")
        
        loaded_count = 0
        failed_count = 0
        
        try:
            with open(csv_file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                if not reader.fieldnames:
                    logger.error("❌ CSV file is empty or has no headers")
                    return 0
                
                logger.info(f"📋 CSV Headers: {reader.fieldnames}")
                
                medicines_batch = []
                batch_size = 100
                
                for row_num, row in enumerate(reader, start=2):  # start=2 to skip header row
                    try:
                        # Parse required fields
                        med_id = int(row.get('id', 0)) if row.get('id') else None
                        name = row.get('name', '').strip()
                        chemical = row.get('chemical', '').strip()
                        description = row.get('description', '').strip()
                        price = int(row.get('price', 0)) if row.get('price') else 0
                        stock_quantity = int(row.get('stock_quantity', 0)) if row.get('stock_quantity') else 0
                        category = row.get('category', '').strip()
                        status = row.get('status', 'in_stock').strip()
                        image_path = row.get('image_path', '').strip()
                        
                        # Validate required fields
                        if not name:
                            logger.warning(f"⚠️ Row {row_num}: Skipping - no medicine name")
                            failed_count += 1
                            continue
                        
                        # Create medicine object
                        medicine = Medicine(
                            name=name,
                            chemical=chemical or None,
                            description=description or None,
                            price=price,
                            stock_quantity=stock_quantity,
                            category=category or None,
                            status=status or 'in_stock',
                            image_path=image_path or None,
                            created_at=datetime.utcnow(),
                            updated_at=datetime.utcnow()
                        )
                        
                        medicines_batch.append(medicine)
                        
                        # Batch insert
                        if len(medicines_batch) >= batch_size:
                            db.session.add_all(medicines_batch)
                            db.session.commit()
                            loaded_count += len(medicines_batch)
                            logger.info(f"✅ Loaded {loaded_count} medicines...")
                            medicines_batch = []
                        
                    except ValueError as e:
                        logger.warning(f"⚠️ Row {row_num}: Invalid data - {e}")
                        failed_count += 1
                        continue
                    except Exception as e:
                        logger.error(f"❌ Row {row_num}: Error - {e}")
                        failed_count += 1
                        continue
                
                # Insert remaining batch
                if medicines_batch:
                    db.session.add_all(medicines_batch)
                    db.session.commit()
                    loaded_count += len(medicines_batch)
                
                logger.info(f"\n{'='*60}")
                logger.info(f"✅ LOAD COMPLETE")
                logger.info(f"{'='*60}")
                logger.info(f"✅ Successfully loaded: {loaded_count} medicines")
                logger.info(f"❌ Failed: {failed_count} records")
                logger.info(f"📊 Total: {loaded_count + failed_count}")
                logger.info(f"{'='*60}\n")
                
                return loaded_count
        
        except Exception as e:
            logger.error(f"❌ Fatal error reading CSV: {e}")
            db.session.rollback()
            return 0


def verify_medicines_loaded() -> bool:
    """Verify that medicines are loaded in database"""
    app = create_app()
    
    with app.app_context():
        count = Medicine.query.count()
        if count > 0:
            logger.info(f"✅ Database contains {count} medicines")
            
            # Sample some medicines
            sample = Medicine.query.limit(3).all()
            logger.info("\n📋 Sample medicines:")
            for med in sample:
                logger.info(f"  - {med.name} (Rs. {med.price}) - Image: {med.image_path}")
            
            return True
        else:
            logger.warning("⚠️ No medicines found in database")
            return False


def get_medicine_statistics() -> dict:
    """Get statistics about loaded medicines"""
    app = create_app()
    
    with app.app_context():
        total = Medicine.query.count()
        
        by_category = db.session.query(
            Medicine.category,
            db.func.count(Medicine.id).label('count')
        ).group_by(Medicine.category).all()
        
        avg_price = db.session.query(
            db.func.avg(Medicine.price)
        ).scalar() or 0
        
        with_images = Medicine.query.filter(Medicine.image_path != None).filter(Medicine.image_path != '').count()
        
        return {
            'total_medicines': total,
            'categories': {cat: count for cat, count in by_category},
            'average_price': round(avg_price, 2),
            'medicines_with_images': with_images,
            'medicines_without_images': total - with_images
        }


if __name__ == "__main__":
    import sys
    
    csv_path = sys.argv[1] if len(sys.argv) > 1 else "medicines_export.csv"
    
    logger.info(f"Loading medicines from: {csv_path}\n")
    
    # Load medicines
    loaded = load_medicines_from_csv(csv_path)
    
    if loaded > 0:
        # Verify
        logger.info("\n📊 Verifying data...")
        verify_medicines_loaded()
        
        # Statistics
        logger.info("\n📈 Medicine Statistics:")
        stats = get_medicine_statistics()
        for key, value in stats.items():
            if isinstance(value, dict):
                logger.info(f"{key}:")
                for k, v in value.items():
                    logger.info(f"  - {k}: {v}")
            else:
                logger.info(f"{key}: {value}")
