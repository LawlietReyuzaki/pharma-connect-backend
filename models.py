from datetime import datetime
from app import db
from flask_login import UserMixin


# ─── Multi-Pharmacy Network Models ──────────────────────────────────────────

class Pharmacy(db.Model):
    __tablename__ = 'pharmacies'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    owner_name = db.Column(db.String(120), nullable=False)
    owner_photo_path = db.Column(db.String(255))
    pharmacy_photo_path = db.Column(db.String(255))
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(50))
    address = db.Column(db.Text)
    city = db.Column(db.String(100))
    province = db.Column(db.String(100))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    license_number = db.Column(db.String(100))
    operating_hours = db.Column(db.Text)  # JSON string
    theme_key = db.Column(db.String(50), default='theme-default')
    status = db.Column(db.String(30), default='pending')  # pending|approved|suspended
    approved_by = db.Column(db.Integer, db.ForeignKey('admins.admin_id'), nullable=True)
    approved_at = db.Column(db.DateTime, nullable=True)
    rejection_reason = db.Column(db.Text, nullable=True)
    avg_rating = db.Column(db.Float, default=0.0)
    review_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    users = db.relationship('User', backref='pharmacy', lazy='dynamic')
    orders = db.relationship('Order', backref='pharmacy', lazy='dynamic',
                             foreign_keys='Order.pharmacy_id')
    reviews = db.relationship('PharmacyReview', backref='pharmacy', lazy='dynamic')
    pharmacy_admins = db.relationship('PharmacyAdmin', backref='pharmacy', lazy='dynamic')


class PharmacyAdmin(db.Model):
    __tablename__ = 'pharmacy_admins'

    id = db.Column(db.Integer, primary_key=True)
    pharmacy_id = db.Column(db.Integer, db.ForeignKey('pharmacies.id'), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class PharmacyReview(db.Model):
    __tablename__ = 'pharmacy_reviews'

    id = db.Column(db.Integer, primary_key=True)
    pharmacy_id = db.Column(db.Integer, db.ForeignKey('pharmacies.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1-5
    comment = db.Column(db.String(500))
    owner_reply = db.Column(db.Text)
    source_type = db.Column(db.String(20))  # 'order' | 'appointment'
    source_id = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='reviews')


# ─── Existing Models ────────────────────────────────────────────────────────

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.String(20), default="patient")  # patient | doctor | admin
    pharmacy_id = db.Column(db.Integer, db.ForeignKey('pharmacies.id'), nullable=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(50))
    password_hash = db.Column(db.String(256), nullable=False)
    
    # Doctor-specific fields
    specialization = db.Column(db.String(100))  # Medical specialization/field
    qualification = db.Column(db.String(200))   # Medical qualifications
    experience_years = db.Column(db.Integer)    # Years of experience
    current_hospital = db.Column(db.String(200))  # Current workplace
    doctor_password_set = db.Column(db.Boolean, default=False)  # Track if doctor has set their password
    photo_path = db.Column(db.String(255), nullable=True)  # Doctor profile photo
    
    # Google Calendar OAuth integration fields (for doctors)
    google_access_token = db.Column(db.Text, nullable=True)  # Encrypted access token
    google_refresh_token = db.Column(db.Text, nullable=True)  # Encrypted refresh token
    google_token_expiry = db.Column(db.DateTime, nullable=True)  # Token expiration time
    google_email = db.Column(db.String(120), nullable=True)  # Connected Google account email
    google_connected_at = db.Column(db.DateTime, nullable=True)  # When OAuth was completed
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    patient_appointments = db.relationship('Appointment', foreign_keys='Appointment.user_id', backref='patient', lazy='dynamic')
    doctor_appointments = db.relationship('Appointment', foreign_keys='Appointment.doctor_id', backref='doctor', lazy='dynamic')
    orders = db.relationship('Order', backref='customer', lazy='dynamic')

class Medicine(db.Model):
    __tablename__ = 'medicines'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(160), nullable=False)
    chemical = db.Column(db.String(160))
    description = db.Column(db.Text)
    price = db.Column(db.Integer, nullable=False)  # PKR (integer)
    image_path = db.Column(db.String(255))
    status = db.Column(db.String(30), default="in_stock")  # in_stock | out_of_stock
    stock_quantity = db.Column(db.Integer, default=0)
    category = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class DoctorAvailability(db.Model):
    """Recurring weekly availability schedule for doctors"""
    __tablename__ = 'doctor_availability'
    
    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    day_of_week = db.Column(db.Integer, nullable=False)  # 0=Monday, 1=Tuesday, ... 6=Sunday
    start_time = db.Column(db.Time, nullable=False)  # e.g., 09:00
    end_time = db.Column(db.Time, nullable=False)    # e.g., 17:00
    slot_duration = db.Column(db.Integer, default=30)  # Minutes per slot (default 30)
    is_active = db.Column(db.Boolean, default=True)  # Can be disabled without deleting
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    doctor = db.relationship('User', foreign_keys=[doctor_id], backref='availabilities')

class TimeSlot(db.Model):
    __tablename__ = 'time_slots'
    
    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    appointment_date = db.Column(db.Date, nullable=False)  # Specific date for this slot
    starts_at = db.Column(db.DateTime, nullable=False)     # Full datetime when slot starts
    ends_at = db.Column(db.DateTime, nullable=False)       # Full datetime when slot ends
    is_booked = db.Column(db.Boolean, default=False)       # Whether this slot is booked
    google_event_id = db.Column(db.String(255), nullable=True)  # Google Calendar Event ID
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    doctor = db.relationship('User', foreign_keys=[doctor_id], backref='time_slots')

class Appointment(db.Model):
    __tablename__ = 'appointments'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    time_slot_id = db.Column(db.Integer, db.ForeignKey('time_slots.id'), nullable=True)
    appointment_date = db.Column(db.Date, nullable=False)  # Specific date for the appointment
    starts_at = db.Column(db.DateTime, nullable=False)
    ends_at = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(30), default="pending") # pending|approved|scheduled|ongoing|completed|cancelled|declined
    google_meet_link = db.Column(db.String(500))  # Google Meet URL
    google_calendar_event_id = db.Column(db.String(255))  # Google Calendar Event ID
    note = db.Column(db.Text)
    symptoms = db.Column(db.Text)
    approval_status = db.Column(db.String(30), default="pending")  # pending|approved|declined
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # Admin who approved
    approved_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    time_slot = db.relationship('TimeSlot', backref='appointments')
    approver = db.relationship('User', foreign_keys=[approved_by])

class Order(db.Model):
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    pharmacy_id = db.Column(db.Integer, db.ForeignKey('pharmacies.id'), nullable=True)
    address = db.Column(db.Text, nullable=False)
    phone = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(30), default="pending")   # pending|processing|out_for_delivery|delivered|cancelled
    total_amount = db.Column(db.Integer, default=0)  # PKR
    delivery_fee = db.Column(db.Integer, default=100)  # PKR
    payment_method = db.Column(db.String(50), default="cash_on_delivery")
    notes = db.Column(db.Text)
    
    # Payment receipt fields for online payments
    payment_receipt_path = db.Column(db.String(500), nullable=True)  # Path to uploaded receipt image
    payment_status = db.Column(db.String(30), default="pending")  # pending|accepted|declined
    payment_verified_at = db.Column(db.DateTime, nullable=True)
    payment_verified_by = db.Column(db.Integer, db.ForeignKey('admins.admin_id'), nullable=True)
    receipt_uploaded_at = db.Column(db.DateTime, nullable=True)
    payment_rejection_reason = db.Column(db.Text, nullable=True)  # Reason for payment rejection
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    items = db.relationship('OrderItem', backref='order', lazy='dynamic', cascade='all, delete-orphan')
    payment_verifier = db.relationship('Admin', foreign_keys=[payment_verified_by], backref='verified_payments')

class OrderItem(db.Model):
    __tablename__ = 'order_items'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    medicine_id = db.Column(db.Integer, db.ForeignKey('medicines.id'), nullable=False)
    qty = db.Column(db.Integer, default=1)
    price_each = db.Column(db.Integer, nullable=False)
    
    # Relationships
    medicine = db.relationship('Medicine', backref='order_items')

class ChatLog(db.Model):
    __tablename__ = 'chat_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    pharmacy_id = db.Column(db.Integer, db.ForeignKey('pharmacies.id'), nullable=True)
    session_id = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    response = db.Column(db.Text, nullable=False)
    language = db.Column(db.String(10), default="ur")  # ur for Urdu, en for English
    flagged = db.Column(db.Boolean, default=False)  # For medical escalation
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Admin(db.Model):
    __tablename__ = 'admins'
    
    admin_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class PaymentMethod(db.Model):
    __tablename__ = 'payment_methods'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)  # Display name: "EasyPaisa", "JazzCash", etc.
    slug = db.Column(db.String(50), unique=True, nullable=False)  # Internal key: "easypaisa", "jazzcash", etc.
    logo_path = db.Column(db.String(255))  # Path to logo image
    is_active = db.Column(db.Boolean, default=True)  # Admin can toggle on/off
    requires_receipt = db.Column(db.Boolean, default=False)  # True for online payments
    display_order = db.Column(db.Integer, default=0)  # Order in which to display
    account_title = db.Column(db.String(200), nullable=True)  # Account holder name
    account_number = db.Column(db.String(100), nullable=True)  # Account number/IBAN
    account_details = db.Column(db.Text, nullable=True)  # Additional instructions for customer
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class BankingDetails(db.Model):
    __tablename__ = 'banking_details'
    
    id = db.Column(db.Integer, primary_key=True)
    bank_name = db.Column(db.String(200), nullable=True)
    account_title = db.Column(db.String(200), nullable=True)
    account_number = db.Column(db.String(100), nullable=True)
    iban = db.Column(db.String(50), nullable=True)
    easypaisa_number = db.Column(db.String(20), nullable=True)
    jazzcash_number = db.Column(db.String(20), nullable=True)
    additional_instructions = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
