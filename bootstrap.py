import os
import hashlib
import logging
from datetime import datetime, timedelta
from app import create_app, db
from models import User, Medicine

# Configure logging
logging.basicConfig(level=logging.DEBUG)

def phash(pw):
    """Hash password using SHA256"""
    return hashlib.sha256(pw.encode()).hexdigest()

def bootstrap_database():
    """Initialize database with seed data for Red Dot Pharmacy"""
    app = create_app()
    
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Check if data already exists
        if User.query.first():
            print("✅ Database already initialized")
            return
        
        # Create default users
        admin = User()
        admin.name = "Red Dot Admin"
        admin.email = "admin@reddotpharmacy.com"
        admin.role = "admin"
        admin.phone = "03001234567"
        admin.password_hash = phash("admin123")
        
        doctor1 = User()
        doctor1.name = "Dr. Ayesha Khan"
        doctor1.email = "dr.ayesha@reddotpharmacy.com"
        doctor1.role = "doctor"
        doctor1.phone = "03001234568"
        doctor1.password_hash = phash("doc123")
        
        doctor2 = User()
        doctor2.name = "Dr. Ahmed Ali"
        doctor2.email = "dr.ahmed@reddotpharmacy.com"
        doctor2.role = "doctor"
        doctor2.phone = "03001234569"
        doctor2.password_hash = phash("doc123")
        
        patient = User()
        patient.name = "Hassan Ali"
        patient.email = "patient@example.com"
        patient.role = "patient"
        patient.phone = "03000000000"
        patient.password_hash = phash("patient123")
        
        db.session.add_all([admin, doctor1, doctor2, patient])
        
        # Create sample medicines
        # Create medicines
        med1 = Medicine()
        med1.name = "Panadol 500mg"
        med1.chemical = "Paracetamol"
        med1.description = "Pain relief and fever reducer"
        med1.price = 60
        med1.stock_quantity = 100
        med1.category = "Pain Relief"
        med1.status = "in_stock"
        
        med2 = Medicine()
        med2.name = "Augmentin 625mg"
        med2.chemical = "Amoxicillin + Clavulanic Acid"
        med2.description = "Antibiotic for bacterial infections"
        med2.price = 950
        med2.stock_quantity = 50
        med2.category = "Antibiotics"
        med2.status = "in_stock"
        
        med3 = Medicine()
        med3.name = "Brufen 400mg"
        med3.chemical = "Ibuprofen"
        med3.description = "Anti-inflammatory pain reliever"
        med3.price = 120
        med3.stock_quantity = 75
        med3.category = "Pain Relief"
        med3.status = "in_stock"
        
        med4 = Medicine()
        med4.name = "Flagyl 500mg"
        med4.chemical = "Metronidazole"
        med4.description = "Antibiotic and antiprotozoal medication"
        med4.price = 180
        med4.stock_quantity = 30
        med4.category = "Antibiotics"
        med4.status = "in_stock"
        
        med5 = Medicine()
        med5.name = "Risek 20mg"
        med5.chemical = "Omeprazole"
        med5.description = "Proton pump inhibitor for acid reflux"
        med5.price = 320
        med5.stock_quantity = 60
        med5.category = "Gastric"
        med5.status = "in_stock"
        
        med6 = Medicine()
        med6.name = "Arinac Tablet"
        med6.chemical = "Paracetamol + Pseudoephedrine + Triprolidine"
        med6.description = "Cold and flu relief"
        med6.price = 240
        med6.stock_quantity = 40
        med6.category = "Cold & Flu"
        med6.status = "in_stock"
        
        medicines = [med1, med2, med3, med4, med5, med6]
        
        db.session.add_all(medicines)
        
        # Commit all changes
        db.session.commit()
        
        print("✅ Red Dot Pharmacy database initialized successfully!")
        print("📊 Created:")
        print(f"   - {len([admin, doctor1, doctor2, patient])} users (1 admin, 2 doctors, 1 patient)")
        print(f"   - {len(medicines)} medicines")
        print("\n🔑 Default credentials:")
        print("   Admin: admin@reddotpharmacy.com / admin123")
        print("   Doctor: dr.ayesha@reddotpharmacy.com / doc123")
        print("   Patient: patient@example.com / patient123")

if __name__ == "__main__":
    bootstrap_database()
    print("✅ Bootstrap complete for Red Dot Pharmacy")
