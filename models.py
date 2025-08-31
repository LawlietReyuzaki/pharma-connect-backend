from datetime import datetime
from app import db
from flask_login import UserMixin

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.String(20), default="patient")  # patient | doctor | admin
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(50))
    password_hash = db.Column(db.String(256), nullable=False)
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
    image_url = db.Column(db.String(255))
    status = db.Column(db.String(30), default="in_stock")  # in_stock | out_of_stock
    stock_quantity = db.Column(db.Integer, default=0)
    category = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class TimeSlot(db.Model):
    __tablename__ = 'time_slots'
    
    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    day_of_week = db.Column(db.Integer, nullable=False)  # 0=Monday, 6=Sunday
    start_time = db.Column(db.Time, nullable=False)  # Start time (e.g., 09:00)
    end_time = db.Column(db.Time, nullable=False)    # End time (e.g., 10:00)
    is_available = db.Column(db.Boolean, default=True)
    max_appointments = db.Column(db.Integer, default=1)  # Number of appointments allowed in this slot
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
    address = db.Column(db.Text, nullable=False)
    phone = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(30), default="pending")   # pending|processing|out_for_delivery|delivered|cancelled
    total_amount = db.Column(db.Integer, default=0)  # PKR
    delivery_fee = db.Column(db.Integer, default=100)  # PKR
    payment_method = db.Column(db.String(50), default="cash_on_delivery")
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    items = db.relationship('OrderItem', backref='order', lazy='dynamic', cascade='all, delete-orphan')

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
    session_id = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    response = db.Column(db.Text, nullable=False)
    language = db.Column(db.String(10), default="ur")  # ur for Urdu, en for English
    flagged = db.Column(db.Boolean, default=False)  # For medical escalation
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
