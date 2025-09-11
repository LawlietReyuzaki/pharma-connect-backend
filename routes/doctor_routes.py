from flask import Blueprint, request, jsonify, render_template
from datetime import datetime, date, time
from services.auth import create_token, phash, verify_token, get_current_user
from models import User, Appointment, TimeSlot
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
        
        # Free up the time slot if appointment was linked to one
        if appointment.time_slot_id:
            slot = TimeSlot.query.get(appointment.time_slot_id)
            if slot:
                slot.is_booked = False
                slot.updated_at = datetime.utcnow()
        
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

@bp.route("/api/time-slots", methods=["GET"])
def get_doctor_time_slots():
    """Get all time slots for current doctor"""
    try:
        current_user = get_current_user()
        if not current_user or current_user.role != "doctor":
            return jsonify({"error": "Doctor access required"}), 403
        
        # Get query parameters
        date_filter = request.args.get('date')
        
        # Build query
        query = TimeSlot.query.filter_by(doctor_id=current_user.id)
        
        if date_filter:
            try:
                filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
                query = query.filter_by(appointment_date=filter_date)
            except ValueError:
                return jsonify({"error": "Invalid date format (use YYYY-MM-DD)"}), 400
        
        # Only show future slots
        query = query.filter(TimeSlot.appointment_date >= date.today())
        
        slots = query.order_by(TimeSlot.appointment_date, TimeSlot.starts_at).all()
        
        # Format slots for response
        slots_list = []
        for slot in slots:
            slots_list.append({
                "id": slot.id,
                "appointment_date": slot.appointment_date.isoformat(),
                "starts_at": slot.starts_at.isoformat(),
                "ends_at": slot.ends_at.isoformat(),
                "start_time": slot.starts_at.strftime("%H:%M"),
                "end_time": slot.ends_at.strftime("%H:%M"),
                "is_booked": slot.is_booked,
                "can_delete": not slot.is_booked,
                "created_at": slot.created_at.isoformat()
            })
        
        # Calculate stats
        total_slots = len(slots)
        available_slots = len([s for s in slots if not s.is_booked])
        booked_slots = len([s for s in slots if s.is_booked])
        
        return jsonify({
            "success": True,
            "slots": slots_list,
            "stats": {
                "total": total_slots,
                "available": available_slots,
                "booked": booked_slots
            }
        })
        
    except Exception as e:
        logging.error(f"Get doctor time slots error: {e}")
        return jsonify({"error": f"Failed to get time slots: {str(e)}"}), 500

@bp.route("/api/time-slots", methods=["POST"])
def create_doctor_time_slot():
    """Create a new time slot for current doctor"""
    try:
        current_user = get_current_user()
        if not current_user or current_user.role != "doctor":
            return jsonify({"error": "Doctor access required"}), 403
        
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Validate required fields
        required_fields = ["appointment_date", "start_time", "end_time"]
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"{field} is required"}), 400
        
        # Parse date and times
        try:
            appointment_date = datetime.strptime(data["appointment_date"], '%Y-%m-%d').date()
            start_time_obj = datetime.strptime(data["start_time"], '%H:%M').time()
            end_time_obj = datetime.strptime(data["end_time"], '%H:%M').time()
        except ValueError:
            return jsonify({"error": "Invalid date/time format"}), 400
        
        # Validate date is not in the past
        if appointment_date < date.today():
            return jsonify({"error": "Cannot create slots for past dates"}), 400
        
        # Validate end time is after start time
        if end_time_obj <= start_time_obj:
            return jsonify({"error": "End time must be after start time"}), 400
        
        # Create full datetime objects
        starts_at = datetime.combine(appointment_date, start_time_obj)
        ends_at = datetime.combine(appointment_date, end_time_obj)
        
        # Check for overlapping slots
        overlapping = TimeSlot.query.filter(
            TimeSlot.doctor_id == current_user.id,
            TimeSlot.appointment_date == appointment_date,
            TimeSlot.starts_at < ends_at,
            TimeSlot.ends_at > starts_at
        ).first()
        
        if overlapping:
            return jsonify({"error": "This time slot overlaps with an existing slot"}), 400
        
        # Create new time slot
        new_slot = TimeSlot(
            doctor_id=current_user.id,
            appointment_date=appointment_date,
            starts_at=starts_at,
            ends_at=ends_at,
            is_booked=False
        )
        
        db.session.add(new_slot)
        db.session.commit()
        
        # Try to create Google Calendar event for the time slot
        google_event_details = None
        try:
            from services.doctor_oauth_service import doctor_oauth_service
            
            # Build appointment_data dictionary for Google Calendar event
            appointment_data = {
                'summary': 'Available Consultation Slot',
                'description': f'Doctor {current_user.name} available for consultation',
                'start_time': starts_at,
                'end_time': ends_at,
                'attendee_emails': [],  # Empty since this is just availability
                'appointment_id': new_slot.id
            }
            
            # Create Google Calendar event
            google_result = doctor_oauth_service.create_calendar_event_for_doctor(
                current_user.id, 
                appointment_data
            )
            
            if google_result:
                # Save the Google event ID to the slot
                new_slot.google_event_id = google_result.get('event_id')
                db.session.commit()
                
                google_event_details = {
                    'event_id': google_result.get('event_id'),
                    'calendar_link': google_result.get('calendar_link'),
                    'doctor_calendar': google_result.get('doctor_calendar'),
                    'status': 'created'
                }
                logging.info(f"✅ Created Google Calendar event for slot {new_slot.id}: {google_result.get('event_id')}")
            else:
                google_event_details = {
                    'status': 'failed',
                    'reason': 'Google Calendar not connected or API error'
                }
                logging.warning(f"⚠️ Failed to create Google Calendar event for slot {new_slot.id}")
                
        except Exception as e:
            google_event_details = {
                'status': 'error',
                'reason': str(e)
            }
            logging.error(f"❌ Error creating Google Calendar event for slot {new_slot.id}: {e}")
        
        return jsonify({
            "success": True,
            "message": "Time slot created successfully",
            "slot": {
                "id": new_slot.id,
                "appointment_date": new_slot.appointment_date.isoformat(),
                "starts_at": new_slot.starts_at.isoformat(),
                "ends_at": new_slot.ends_at.isoformat(),
                "start_time": new_slot.starts_at.strftime("%H:%M"),
                "end_time": new_slot.ends_at.strftime("%H:%M"),
                "is_booked": new_slot.is_booked,
                "google_event_id": new_slot.google_event_id
            },
            "google_calendar": google_event_details
        })
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Create doctor time slot error: {e}")
        return jsonify({"error": f"Failed to create time slot: {str(e)}"}), 500

@bp.route("/api/time-slots/<int:slot_id>", methods=["DELETE"])
def delete_doctor_time_slot(slot_id):
    """Delete a time slot (only if not booked)"""
    try:
        current_user = get_current_user()
        if not current_user or current_user.role != "doctor":
            return jsonify({"error": "Doctor access required"}), 403
        
        slot = TimeSlot.query.get_or_404(slot_id)
        
        # Verify this slot belongs to the current doctor
        if slot.doctor_id != current_user.id:
            return jsonify({"error": "You can only delete your own time slots"}), 403
        
        # Check if slot is booked
        if slot.is_booked:
            return jsonify({"error": "Cannot delete a booked time slot"}), 400
        
        db.session.delete(slot)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Time slot deleted successfully"
        })
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Delete doctor time slot error: {e}")
        return jsonify({"error": f"Failed to delete time slot: {str(e)}"}), 500