"""
Test Suite for SQLite Integration
Verifies that the database, RAG system, and image linking all work correctly
"""

import os
import sys
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SQLiteIntegrationTest:
    """Comprehensive test suite for SQLite migration"""
    
    def __init__(self):
        self.tests_passed = 0
        self.tests_failed = 0
        self.test_results = []
    
    def log_test(self, name: str, passed: bool, message: str = ""):
        """Log a test result"""
        status = "✅ PASS" if passed else "❌ FAIL"
        self.test_results.append({
            'name': name,
            'passed': passed,
            'message': message
        })
        
        if passed:
            self.tests_passed += 1
            logger.info(f"{status}: {name}")
        else:
            self.tests_failed += 1
            logger.error(f"{status}: {name} - {message}")
    
    # Test 1: Check files exist
    def test_required_files(self):
        """Check if all required files exist"""
        required = {
            'medicines_export.csv': 'Medicine data source',
            'app.py': 'Flask app',
            'models.py': 'Database models',
            'database_loader.py': 'CSV loader',
            'setup_local_db.py': 'Setup script',
            'config.py': 'Configuration',
            'services/sqlite_medicine_search.py': 'Search service',
        }
        
        logger.info("\n📋 Test 1: Checking Required Files")
        logger.info("="*60)
        
        all_exist = True
        for file_path, description in required.items():
            exists = os.path.exists(file_path)
            logger.info(f"  {'✅' if exists else '❌'} {file_path} - {description}")
            if not exists:
                all_exist = False
        
        self.log_test("Required files exist", all_exist)
        return all_exist
    
    # Test 2: Check images directory
    def test_images_directory(self):
        """Check if images directory and files exist"""
        logger.info("\n📷 Test 2: Checking Images Directory")
        logger.info("="*60)
        
        images_dir = Path("static/uploads/medicines")
        
        if images_dir.exists():
            image_files = list(images_dir.glob("*"))
            logger.info(f"  ✅ Directory exists: {images_dir}")
            logger.info(f"  📊 Contains {len(image_files)} image files")
            self.log_test("Images directory exists", True)
            
            if len(image_files) > 0:
                logger.info(f"  Sample images: {[f.name for f in image_files[:3]]}")
                self.log_test("Images found in directory", len(image_files) > 0)
            else:
                logger.warning("  ⚠️ Directory is empty")
                self.log_test("Images found in directory", False, "Directory is empty")
        else:
            logger.error(f"  ❌ Directory not found: {images_dir}")
            self.log_test("Images directory exists", False, "Directory not found")
    
    # Test 3: Database initialization
    def test_database_init(self):
        """Test database creation and tables"""
        logger.info("\n📦 Test 3: Database Initialization")
        logger.info("="*60)
        
        try:
            from app import create_app, db
            
            app = create_app()
            with app.app_context():
                # Create tables
                db.create_all()
                logger.info("  ✅ Database tables created")
                
                # Check database URI
                db_uri = app.config['SQLALCHEMY_DATABASE_URI']
                logger.info(f"  📍 Database: {db_uri}")
                
                self.log_test("Database initialization", True)
                return True
        
        except Exception as e:
            self.log_test("Database initialization", False, str(e))
            return False
    
    # Test 4: Load medicines
    def test_medicine_loading(self):
        """Test loading medicines from CSV"""
        logger.info("\n📚 Test 4: Medicine Loading")
        logger.info("="*60)
        
        try:
            from app import create_app, db
            from models import Medicine
            
            app = create_app()
            with app.app_context():
                # Check CSV file
                if not os.path.exists('medicines_export.csv'):
                    self.log_test("CSV file found", False, "medicines_export.csv not found")
                    return False
                
                logger.info("  ✅ CSV file found")
                
                # Check if medicines already loaded
                count = Medicine.query.count()
                
                if count == 0:
                    logger.warning("  ⚠️ No medicines in database yet")
                    logger.info("  Run: python setup_local_db.py")
                    self.log_test("Medicines loaded in database", False, "Database is empty")
                    return False
                else:
                    logger.info(f"  ✅ Database contains {count} medicines")
                    self.log_test("Medicines loaded in database", count > 0)
                    
                    # Get sample medicine
                    sample = Medicine.query.first()
                    logger.info(f"\n  Sample Medicine:")
                    logger.info(f"    Name: {sample.name}")
                    logger.info(f"    Price: Rs. {sample.price}")
                    logger.info(f"    Chemical: {sample.chemical}")
                    logger.info(f"    Image: {sample.image_path}")
                    
                    return True
        
        except Exception as e:
            self.log_test("Medicines loaded in database", False, str(e))
            return False
    
    # Test 5: Search functionality
    def test_medicine_search(self):
        """Test medicine search"""
        logger.info("\n🔍 Test 5: Medicine Search")
        logger.info("="*60)
        
        try:
            from services.sqlite_medicine_search import MedicineSearchService
            
            # Test name search
            results = MedicineSearchService.search_by_name("panadol", limit=3)
            
            if results:
                logger.info(f"  ✅ Found {len(results)} results for 'panadol'")
                
                for i, med in enumerate(results[:1], 1):
                    logger.info(f"\n  Result {i}:")
                    logger.info(f"    Name: {med['name']}")
                    logger.info(f"    Price: Rs. {med['price']}")
                    logger.info(f"    Image URL: {med['image_url']}")
                    logger.info(f"    Status: {med['status']}")
                
                self.log_test("Medicine search works", True)
                
                # Verify image URL structure
                if results[0]['image_url']:
                    self.log_test("Image URL in results", True)
                else:
                    self.log_test("Image URL in results", False, "No image URL")
                
                return True
            else:
                logger.warning("  ⚠️ No results found")
                self.log_test("Medicine search works", False, "No results found")
                return False
        
        except Exception as e:
            self.log_test("Medicine search works", False, str(e))
            return False
    
    # Test 6: Image linking
    def test_image_linking(self):
        """Test that images are properly linked"""
        logger.info("\n🖼️ Test 6: Image Linking")
        logger.info("="*60)
        
        try:
            from app import create_app
            from models import Medicine
            
            app = create_app()
            with app.app_context():
                # Get medicines with images
                meds_with_images = Medicine.query.filter(
                    Medicine.image_path != None,
                    Medicine.image_path != ''
                ).limit(5).all()
                
                if not meds_with_images:
                    logger.warning("  ⚠️ No medicines with images found")
                    self.log_test("Image linking", False, "No images in database")
                    return False
                
                logger.info(f"  ✅ Found {len(meds_with_images)} medicines with images")
                
                for med in meds_with_images[:3]:
                    logger.info(f"\n  Medicine: {med.name}")
                    logger.info(f"    Raw path: {med.image_path}")
                    
                    # Check if image file exists
                    image_file = Path(f"static/uploads/medicines/{Path(med.image_path).name}")
                    if image_file.exists():
                        logger.info(f"    ✅ File exists: {image_file}")
                    else:
                        logger.warning(f"    ⚠️ File not found: {image_file}")
                
                self.log_test("Image linking", True)
                return True
        
        except Exception as e:
            self.log_test("Image linking", False, str(e))
            return False
    
    # Test 7: RAG integration
    def test_rag_integration(self):
        """Test RAG system integration"""
        logger.info("\n🧠 Test 7: RAG System Integration")
        logger.info("="*60)
        
        try:
            from services.smart_rag_orchestrator import SmartRAGOrchestrator
            
            orchestrator = SmartRAGOrchestrator()
            logger.info("  ✅ RAG Orchestrator initialized")
            
            # Test retrieval
            result = orchestrator.retrieve("pain relief", language="en")
            
            logger.info(f"  Retrieval result keys: {list(result.keys())}")
            
            if result.get('medications'):
                logger.info(f"  ✅ Found {len(result['medications'])} medicines")
                self.log_test("RAG retrieval works", True)
            else:
                logger.warning("  ⚠️ No medicines in RAG result")
                self.log_test("RAG retrieval works", False, "No medicines found")
            
            # Check images
            if result.get('images'):
                logger.info(f"  ✅ Found {len(result['images'])} images")
                self.log_test("RAG image retrieval works", True)
            else:
                logger.info("  ℹ️ No images in result (expected for some queries)")
                self.log_test("RAG image retrieval works", False, "No images retrieved")
            
            return True
        
        except Exception as e:
            self.log_test("RAG system integration", False, str(e))
            return False
    
    # Test 8: Database statistics
    def test_database_stats(self):
        """Get and display database statistics"""
        logger.info("\n📊 Test 8: Database Statistics")
        logger.info("="*60)
        
        try:
            from app import create_app, db
            from models import Medicine
            
            app = create_app()
            with app.app_context():
                total = Medicine.query.count()
                
                if total == 0:
                    logger.warning("  ⚠️ Database is empty")
                    return False
                
                logger.info(f"  Total medicines: {total}")
                
                # By category
                by_category = db.session.query(
                    Medicine.category,
                    db.func.count(Medicine.id).label('count')
                ).group_by(Medicine.category).all()
                
                if by_category:
                    logger.info(f"  Categories ({len(by_category)}):")
                    for cat, count in by_category[:5]:
                        logger.info(f"    - {cat or 'Uncategorized'}: {count}")
                
                # Average price
                avg_price = db.session.query(
                    db.func.avg(Medicine.price)
                ).scalar() or 0
                
                logger.info(f"  Average price: Rs. {round(avg_price, 2)}")
                
                # With images
                with_images = Medicine.query.filter(Medicine.image_path != None).count()
                logger.info(f"  With images: {with_images}/{total} ({round(100*with_images/total)}%)")
                
                self.log_test("Database statistics", True)
                return True
        
        except Exception as e:
            self.log_test("Database statistics", False, str(e))
            return False
    
    def run_all_tests(self):
        """Run all tests"""
        print("\n" + "="*70)
        print("  SQLite Integration Test Suite")
        print("="*70)
        
        # Run tests in order
        self.test_required_files()
        self.test_images_directory()
        self.test_database_init()
        self.test_medicine_loading()
        self.test_medicine_search()
        self.test_image_linking()
        self.test_rag_integration()
        self.test_database_stats()
        
        # Summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        total = self.tests_passed + self.tests_failed
        
        print("\n" + "="*70)
        print("  Test Summary")
        print("="*70)
        print(f"  ✅ Passed: {self.tests_passed}")
        print(f"  ❌ Failed: {self.tests_failed}")
        print(f"  📊 Total: {total}")
        print("="*70)
        
        if self.tests_failed == 0:
            print("\n✅ All tests passed! Your SQLite setup is ready to use.\n")
            return True
        else:
            print(f"\n⚠️ {self.tests_failed} test(s) failed. See above for details.\n")
            return False


def main():
    """Main test function"""
    test_suite = SQLiteIntegrationTest()
    success = test_suite.run_all_tests()
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
