from flask import Blueprint, request, jsonify, render_template
from datetime import datetime
from services.auth import create_token, phash, verify_token, get_current_user
from models import User, Appointment
from app import db
import logging

bp = Blueprint("doctor", __name__)

@bp.route("/dashboard")
def dashboard():
    """Doctor dashboard page"""
    return render_template("doctor_dashboard.html")

@bp.route("/api/login", methods=["POST"])
def doctor_login():
    """Doctor login endpoint"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        email = data.get("email", "").strip()
        password = data.get("password", "")
        
        if not email or not password:
            return jsonify({"error": "Email and password are required"}), 400
        
        # Find doctor by email
        doctor = User.query.filter_by(email=email, role="doctor").first()
        if not doctor:
            return jsonify({"error": "Doctor not found"}), 401
        
        # Verify password
        if doctor.password_hash != phash(password):
            return jsonify({"error": "Invalid credentials"}), 401
        
        # Create JWT token
        token = create_token(doctor)
        
        return jsonify({
            "success": True,
            "token": token,
            "doctor": {
                "id": doctor.id,
                "name": doctor.name,
                "email": doctor.email,
                "role": doctor.role,
                "phone": doctor.phone,
                "specialization": doctor.specialization,
                "qualification": doctor.qualification,
                "experience_years": doctor.experience_years,
                "current_hospital": doctor.current_hospital,
                "password_set": doctor.doctor_password_set
            }
        })
        
    except Exception as e:
        logging.error(f"Doctor login error: {e}")
        return jsonify({"error": f"Login failed: {str(e)}"}), 500

@bp.route("/api/setup-password", methods=["POST"])
def setup_password():
    """Set up password for doctor first time login"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        email = data.get("email", "").strip()
        password = data.get("password", "")
        confirm_password = data.get("confirm_password", "")
        
        if not email or not password or not confirm_password:
            return jsonify({"error": "All fields are required"}), 400
            
        if password != confirm_password:
            return jsonify({"error": "Passwords do not match"}), 400
            
        if len(password) < 6:
            return jsonify({"error": "Password must be at least 6 characters"}), 400
        
        # Find doctor by email
        doctor = User.query.filter_by(email=email, role="doctor").first()
        if not doctor:
            return jsonify({"error": "Doctor not found"}), 404
        
        # Update password
        doctor.password_hash = phash(password)
        doctor.doctor_password_set = True
        doctor.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        # Create JWT token for immediate login
        token = create_token(doctor)
        
        return jsonify({
            "success": True,
            "message": "Password set successfully",
            "token": token,
            "doctor": {
                "id": doctor.id,
                "name": doctor.name,
                "email": doctor.email,
                "role": doctor.role,
                "phone": doctor.phone,
                "specialization": doctor.specialization,
                "qualification": doctor.qualification,
                "experience_years": doctor.experience_years,
                "current_hospital": doctor.current_hospital,
                "password_set": doctor.doctor_password_set
            }
        })
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Password setup error: {e}")
        return jsonify({"error": f"Password setup failed: {str(e)}"}), 500

@bp.route("/api/profile", methods=["GET"])
def get_profile():
    """Get doctor profile"""
    try:
        # Get authenticated doctor
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({"error": "Authentication required"}), 401
        
        token = auth_header.split(' ')[1]
        user_data = verify_token(token)
        
        if not user_data:
            return jsonify({"error": "Invalid or expired token"}), 401
        
        doctor = User.query.filter_by(id=user_data['sub'], role="doctor").first()
        if not doctor:
            return jsonify({"error": "Doctor not found"}), 404
        
        return jsonify({
            "success": True,
            "doctor": {
                "id": doctor.id,
                "name": doctor.name,
                "email": doctor.email,
                "phone": doctor.phone,
                "specialization": doctor.specialization,
                "qualification": doctor.qualification,
                "experience_years": doctor.experience_years,
                "current_hospital": doctor.current_hospital
            }
        })
        
    except Exception as e:
        logging.error(f"Get profile error: {e}")
        return jsonify({"error": f"Failed to retrieve profile: {str(e)}"}), 500

@bp.route("/api/profile", methods=["PUT"])
def update_profile():
    """Update doctor profile"""
    try:
        # Get authenticated doctor
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({"error": "Authentication required"}), 401
        
        token = auth_header.split(' ')[1]
        user_data = verify_token(token)
        
        if not user_data:
            return jsonify({"error": "Invalid or expired token"}), 401
        
        doctor = User.query.filter_by(id=user_data['sub'], role="doctor").first()
        if not doctor:
            return jsonify({"error": "Doctor not found"}), 404
        
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Update allowed fields (email cannot be changed)
        if data.get("name"):
            doctor.name = data["name"]
        if data.get("phone"):
            doctor.phone = data["phone"]
        if data.get("specialization"):
            doctor.specialization = data["specialization"]
        if data.get("qualification"):
            doctor.qualification = data["qualification"]
        if data.get("experience_years"):
            doctor.experience_years = data["experience_years"]
        if data.get("current_hospital"):
            doctor.current_hospital = data["current_hospital"]
        
        # Update password if provided
        if data.get("password"):
            doctor.password_hash = phash(data["password"])
        
        doctor.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Profile updated successfully",
            "doctor": {
                "id": doctor.id,
                "name": doctor.name,
                "email": doctor.email,
                "phone": doctor.phone,
                "specialization": doctor.specialization,
                "qualification": doctor.qualification,
                "experience_years": doctor.experience_years,
                "current_hospital": doctor.current_hospital
            }
        })
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Update profile error: {e}")
        return jsonify({"error": f"Profile update failed: {str(e)}"}), 500

@bp.route("/api/appointments", methods=["GET"])
def get_appointments():
    """Get doctor's appointments"""
    try:
        # Get authenticated doctor
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({"error": "Authentication required"}), 401
        
        token = auth_header.split(' ')[1]
        user_data = verify_token(token)
        
        if not user_data:
            return jsonify({"error": "Invalid or expired token"}), 401
        
        doctor = User.query.filter_by(id=user_data['sub'], role="doctor").first()
        if not doctor:
            return jsonify({"error": "Doctor not found"}), 404
        
        # Get filter parameter
        status_filter = request.args.get('status', 'all')
        
        # Base query
        query = Appointment.query.filter_by(doctor_id=doctor.id)
        
        # Apply status filter
        if status_filter == 'pending':
            query = query.filter_by(approval_status='pending')
        elif status_filter == 'scheduled':
            query = query.filter_by(approval_status='approved', status='scheduled')
        elif status_filter == 'completed':
            query = query.filter_by(status='completed')
        
        appointments = query.order_by(Appointment.appointment_date.desc(), Appointment.starts_at.desc()).all()
        
        appointments_list = []
        for appointment in appointments:
            patient_name = appointment.patient.name if appointment.patient else "Unknown Patient"
            
            appointments_list.append({
                "id": appointment.id,
                "patient_name": patient_name,
                "patient_phone": appointment.patient.phone if appointment.patient else "",
                "appointment_date": appointment.appointment_date.isoformat() if appointment.appointment_date else None,
                "starts_at": appointment.starts_at.isoformat() if appointment.starts_at else None,
                "ends_at": appointment.ends_at.isoformat() if appointment.ends_at else None,
                "symptoms": appointment.symptoms,
                "note": appointment.note,
                "status": appointment.status,
                "approval_status": appointment.approval_status,
                "google_meet_link": appointment.google_meet_link,
                "created_at": appointment.created_at.isoformat() if appointment.created_at else None
            })
        
        # Get statistics
        stats = {
            "total": doctor.doctor_appointments.count(),
            "pending": doctor.doctor_appointments.filter_by(approval_status='pending').count(),
            "scheduled": doctor.doctor_appointments.filter(
                Appointment.approval_status == 'approved',
                Appointment.status == 'scheduled'
            ).count(),
            "completed": doctor.doctor_appointments.filter_by(status='completed').count()
        }
        
        return jsonify({
            "success": True,
            "appointments": appointments_list,
            "stats": stats
        })
        
    except Exception as e:
        logging.error(f"Get appointments error: {e}")
        return jsonify({"error": f"Failed to retrieve appointments: {str(e)}"}), 500

@bp.route("/api/appointments/<int:appointment_id>/complete", methods=["POST"])
def complete_appointment(appointment_id):
    """Mark appointment as completed"""
    try:
        # Get authenticated doctor
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({"error": "Authentication required"}), 401
        
        token = auth_header.split(' ')[1]
        user_data = verify_token(token)
        
        if not user_data:
            return jsonify({"error": "Invalid or expired token"}), 401
        
        doctor = User.query.filter_by(id=user_data['sub'], role="doctor").first()
        if not doctor:
            return jsonify({"error": "Doctor not found"}), 404
        
        # Find appointment
        appointment = Appointment.query.filter_by(id=appointment_id, doctor_id=doctor.id).first()
        if not appointment:
            return jsonify({"error": "Appointment not found"}), 404
        
        if appointment.status == 'completed':
            return jsonify({"error": "Appointment already completed"}), 400
        
        # Update appointment status
        appointment.status = 'completed'
        appointment.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Appointment marked as completed"
        })
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Complete appointment error: {e}")
        return jsonify({"error": f"Failed to complete appointment: {str(e)}"}), 500

@bp.route("/api/appointments", methods=["GET"])
def get_doctor_appointments():
    """Get appointments for current doctor"""
    try:
        current_user = get_current_user()
        if not current_user or current_user.role != "doctor":
            return jsonify({"error": "Doctor access required"}), 403
        
        # Get query parameters
        status = request.args.get('status', 'all')
        
        # Build query
        query = Appointment.query.filter_by(doctor_id=current_user.id)
        
        if status != 'all':
            if status == 'pending':
                query = query.filter_by(approval_status='pending')
            else:
                query = query.filter_by(status=status)
        
        appointments = query.order_by(Appointment.starts_at.desc()).all()
        
        # Format appointments for response
        appointment_list = []
        for appointment in appointments:
            patient = User.query.get(appointment.user_id)
            appointment_list.append({
                "id": appointment.id,
                "patient_id": appointment.user_id,
                "patient_name": patient.name if patient else "Unknown",
                "patient_email": patient.email if patient else "Unknown",
                "appointment_date": appointment.appointment_date.isoformat() if appointment.appointment_date else None,
                "starts_at": appointment.starts_at.isoformat() if appointment.starts_at else None,
                "ends_at": appointment.ends_at.isoformat() if appointment.ends_at else None,
                "status": appointment.status,
                "approval_status": appointment.approval_status,
                "symptoms": appointment.symptoms,
                "note": appointment.note,
                "google_meet_link": appointment.google_meet_link,
                "created_at": appointment.created_at.isoformat() if appointment.created_at else None
            })
        
        # Calculate stats
        total_appointments = len(appointments)
        pending_appointments = len([a for a in appointments if a.approval_status == "pending"])
        approved_appointments = len([a for a in appointments if a.approval_status == "approved"])
        
        return jsonify({
            "success": True,
            "appointments": appointment_list,
            "stats": {
                "total": total_appointments,
                "pending": pending_appointments,
                "approved": approved_appointments
            }
        })
        
    except Exception as e:
        logging.error(f"Get doctor appointments error: {e}")
        return jsonify({"error": f"Failed to get appointments: {str(e)}"}), 500

@bp.route("/api/appointments/<int:appointment_id>/approve", methods=["POST"])
def approve_doctor_appointment(appointment_id):
    """Doctor approves their own appointment"""
    try:
        current_user = get_current_user()
        if not current_user or current_user.role != "doctor":
            return jsonify({"error": "Doctor access required"}), 403
        
        appointment = Appointment.query.get_or_404(appointment_id)
        
        # Verify this appointment belongs to the current doctor
        if appointment.doctor_id != current_user.id:
            return jsonify({"error": "You can only manage your own appointments"}), 403
        
        if appointment.approval_status != "pending":
            return jsonify({"error": "Appointment is not pending approval"}), 400
        
        # Update appointment
        appointment.approval_status = "approved"
        appointment.status = "scheduled"
        appointment.approved_by = current_user.id
        appointment.approved_at = datetime.utcnow()
        appointment.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        # Send fake email notifications
        patient = User.query.get(appointment.user_id)
        if patient:
            logging.info(f"Email sent to {patient.email}: Your appointment with {current_user.name} on {appointment.appointment_date} at {appointment.starts_at.strftime('%H:%M')} has been approved!")
        
        return jsonify({
            "success": True,
            "message": "Appointment approved successfully"
        })
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Doctor approve appointment error: {e}")
        return jsonify({"error": f"Failed to approve appointment: {str(e)}"}), 500

@bp.route("/api/appointments/<int:appointment_id>/decline", methods=["POST"])
def decline_doctor_appointment(appointment_id):
    """Doctor declines their own appointment"""
    try:
        current_user = get_current_user()
        if not current_user or current_user.role != "doctor":
            return jsonify({"error": "Doctor access required"}), 403
        
        data = request.get_json()
        reason = data.get("reason", "No reason provided") if data else "No reason provided"
        
        appointment = Appointment.query.get_or_404(appointment_id)
        
        # Verify this appointment belongs to the current doctor
        if appointment.doctor_id != current_user.id:
            return jsonify({"error": "You can only manage your own appointments"}), 403
        
        if appointment.approval_status != "pending":
            return jsonify({"error": "Appointment is not pending approval"}), 400
        
        # Update appointment
        appointment.approval_status = "declined"
        appointment.status = "cancelled"
        appointment.approved_by = current_user.id
        appointment.approved_at = datetime.utcnow()
        appointment.note = f"Declined by doctor: {reason}"
        appointment.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        # Send fake email notifications
        patient = User.query.get(appointment.user_id)
        if patient:
            logging.info(f"Email sent to {patient.email}: Your appointment with {current_user.name} on {appointment.appointment_date} has been declined. Reason: {reason}")
        
        return jsonify({
            "success": True,
            "message": "Appointment declined successfully"
        })
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Doctor decline appointment error: {e}")
        return jsonify({"error": f"Failed to decline appointment: {str(e)}"}), 500