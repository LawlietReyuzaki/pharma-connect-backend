from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
from services.auth import require_auth, get_current_user, require_role
from services.google_services import calendar_service, meet_service
from models import Appointment, User
from app import db
import logging

bp = Blueprint("appointments", __name__)

@bp.route("/", methods=["POST"])
def create_appointment():
    """Create a new appointment"""
    try:
        from services.auth import get_current_user
        
        # Get authenticated user
        current_user = get_current_user()
        if not current_user:
            return jsonify({"error": "Authentication required"}), 401
        
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Validate required fields
        required_fields = ["doctor_id", "start_time", "symptoms"]
        for field in required_fields:
            if not data.get(field):
                return jsonify({"error": f"{field} is required"}), 400
        
        # Parse datetime
        try:
            start_time = datetime.fromisoformat(data["start_time"].replace('Z', '+00:00'))
            end_time = start_time + timedelta(minutes=30)  # Default 30-minute appointments
        except ValueError:
            return jsonify({"error": "Invalid datetime format"}), 400
        
        # Verify doctor exists
        doctor = User.query.filter_by(id=data["doctor_id"], role="doctor").first()
        if not doctor:
            return jsonify({"error": "Doctor not found"}), 404
        
        # Check for scheduling conflicts
        existing = Appointment.query.filter(
            Appointment.doctor_id == data["doctor_id"],
            Appointment.starts_at <= end_time,
            Appointment.ends_at >= start_time,
            Appointment.status.in_(["scheduled", "ongoing"])
        ).first()
        
        if existing:
            return jsonify({"error": "Time slot not available"}), 409
        
        # Create Google Meet link
        meet_link = meet_service.create_meet_room(
            appointment_id=f"temp_{int(start_time.timestamp())}",
            doctor_name=doctor.name,
            patient_name=current_user.name
        )
        
        # Create calendar event
        calendar_data = {
            'summary': f'Red Dot Pharmacy - Consultation with {doctor.name}',
            'description': f'Patient: {current_user.name}\nSymptoms: {data["symptoms"]}',
            'start_time': start_time,
            'end_time': end_time,
            'attendee_emails': [current_user.email, doctor.email]
        }
        
        calendar_result = calendar_service.create_appointment_event(calendar_data)
        
        # Create appointment record
        appointment = Appointment()
        appointment.user_id = current_user.id
        appointment.doctor_id = data["doctor_id"]
        appointment.starts_at = start_time
        appointment.ends_at = end_time
        appointment.symptoms = data["symptoms"]
        appointment.note = data.get("note", "")
        appointment.google_meet_link = meet_link
        appointment.google_calendar_event_id = calendar_result["event_id"] if calendar_result else None
        appointment.status = "scheduled"
        
        db.session.add(appointment)
        db.session.commit()
        
        # Update meet link with actual appointment ID
        appointment.google_meet_link = meet_service.create_meet_room(
            appointment_id=appointment.id,
            doctor_name=doctor.name,
            patient_name=current_user.name
        )
        db.session.commit()
        
        return jsonify({
            "success": True,
            "appointment": {
                "id": appointment.id,
                "doctor_name": doctor.name,
                "start_time": appointment.starts_at.isoformat(),
                "end_time": appointment.ends_at.isoformat(),
                "status": appointment.status,
                "google_meet_link": appointment.google_meet_link,
                "calendar_link": calendar_result["calendar_link"] if calendar_result else None
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Create appointment error: {e}")
        return jsonify({"error": f"Failed to create appointment: {str(e)}"}), 500

@bp.route("/", methods=["GET"])
def list_appointments():
    """List appointments for current user"""
    try:
        current_user = get_current_user()
        if not current_user:
            return jsonify({"error": "Authentication required"}), 401
        
        # Get query parameters
        status = request.args.get('status')
        limit = int(request.args.get('limit', 10))
        
        # Build query based on user role
        if current_user.role == "patient":
            query = Appointment.query.filter_by(user_id=current_user.id)
        elif current_user.role == "doctor":
            query = Appointment.query.filter_by(doctor_id=current_user.id)
        else:  # admin
            query = Appointment.query
        
        # Apply status filter
        if status:
            query = query.filter_by(status=status)
        
        # Order by start time and limit
        appointments = query.order_by(Appointment.starts_at.desc()).limit(limit).all()
        
        # Format response
        appointment_list = []
        for appt in appointments:
            # Get related user info
            patient = User.query.get(appt.user_id)
            doctor = User.query.get(appt.doctor_id)
            
            appointment_list.append({
                "id": appt.id,
                "patient_name": patient.name if patient else "Unknown",
                "doctor_name": doctor.name if doctor else "Unknown",
                "start_time": appt.starts_at.isoformat(),
                "end_time": appt.ends_at.isoformat(),
                "status": appt.status,
                "symptoms": appt.symptoms,
                "note": appt.note,
                "google_meet_link": appt.google_meet_link
            })
        
        return jsonify({
            "success": True,
            "appointments": appointment_list
        })
        
    except Exception as e:
        logging.error(f"List appointments error: {e}")
        return jsonify({"error": f"Failed to retrieve appointments: {str(e)}"}), 500

@bp.route("/<int:appointment_id>", methods=["GET"])
def get_appointment(appointment_id):
    """Get specific appointment details"""
    try:
        current_user = get_current_user()
        if not current_user:
            return jsonify({"error": "Authentication required"}), 401
        
        appointment = Appointment.query.get_or_404(appointment_id)
        
        # Check permissions
        if (current_user.role == "patient" and appointment.user_id != current_user.id) or \
           (current_user.role == "doctor" and appointment.doctor_id != current_user.id):
            return jsonify({"error": "Access denied"}), 403
        
        # Get related users
        patient = User.query.get(appointment.user_id)
        doctor = User.query.get(appointment.doctor_id)
        
        return jsonify({
            "success": True,
            "appointment": {
                "id": appointment.id,
                "patient": {
                    "id": patient.id if patient else None,
                    "name": patient.name if patient else "Unknown",
                    "email": patient.email if patient else "Unknown",
                    "phone": patient.phone if patient else "Unknown"
                },
                "doctor": {
                    "id": doctor.id if doctor else None,
                    "name": doctor.name if doctor else "Unknown",
                    "email": doctor.email if doctor else "Unknown"
                },
                "start_time": appointment.starts_at.isoformat(),
                "end_time": appointment.ends_at.isoformat(),
                "status": appointment.status,
                "symptoms": appointment.symptoms,
                "note": appointment.note,
                "google_meet_link": appointment.google_meet_link,
                "google_calendar_event_id": appointment.google_calendar_event_id
            }
        })
        
    except Exception as e:
        logging.error(f"Get appointment error: {e}")
        return jsonify({"error": f"Failed to retrieve appointment: {str(e)}"}), 500

@bp.route("/<int:appointment_id>/status", methods=["PUT"])
def update_appointment_status(appointment_id):
    """Update appointment status"""
    try:
        current_user = get_current_user()
        if not current_user:
            return jsonify({"error": "Authentication required"}), 401
        
        data = request.get_json()
        if not data or "status" not in data:
            return jsonify({"error": "Status is required"}), 400
        
        appointment = Appointment.query.get_or_404(appointment_id)
        
        # Check permissions (doctors and admins can update status)
        if current_user.role == "patient":
            return jsonify({"error": "Only doctors can update appointment status"}), 403
        
        if current_user.role == "doctor" and appointment.doctor_id != current_user.id:
            return jsonify({"error": "Access denied"}), 403
        
        # Validate status
        valid_statuses = ["scheduled", "ongoing", "completed", "cancelled"]
        if data["status"] not in valid_statuses:
            return jsonify({"error": "Invalid status"}), 400
        
        # Update appointment
        appointment.status = data["status"]
        
        # Add note if provided
        if "note" in data:
            appointment.note = data["note"]
        
        db.session.commit()
        
        # Update calendar event if needed
        if appointment.google_calendar_event_id:
            calendar_service.update_appointment_event(
                appointment.google_calendar_event_id,
                {"status": data["status"]}
            )
        
        return jsonify({
            "success": True,
            "message": "Appointment status updated",
            "appointment": {
                "id": appointment.id,
                "status": appointment.status,
                "note": appointment.note
            }
        })
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Update appointment status error: {e}")
        return jsonify({"error": f"Failed to update appointment: {str(e)}"}), 500

@bp.route("/doctors", methods=["GET"])
def list_doctors():
    """Get list of available doctors"""
    try:
        doctors = User.query.filter_by(role="doctor").all()
        
        doctor_list = []
        for doctor in doctors:
            # Get upcoming appointments count
            upcoming_count = Appointment.query.filter(
                Appointment.doctor_id == doctor.id,
                Appointment.status.in_(["scheduled", "ongoing"]),
                Appointment.starts_at >= datetime.now()
            ).count()
            
            doctor_list.append({
                "id": doctor.id,
                "name": doctor.name,
                "email": doctor.email,
                "phone": doctor.phone,
                "upcoming_appointments": upcoming_count
            })
        
        return jsonify({
            "success": True,
            "doctors": doctor_list
        })
        
    except Exception as e:
        logging.error(f"List doctors error: {e}")
        return jsonify({"error": f"Failed to retrieve doctors: {str(e)}"}), 500

@bp.route("/available-slots/<int:doctor_id>", methods=["GET"])
def get_available_slots(doctor_id):
    """Get available appointment slots for a doctor"""
    try:
        # Get query parameters
        date_str = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
        
        try:
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({"error": "Invalid date format (use YYYY-MM-DD)"}), 400
        
        # Verify doctor exists
        doctor = User.query.filter_by(id=doctor_id, role="doctor").first()
        if not doctor:
            return jsonify({"error": "Doctor not found"}), 404
        
        # Generate time slots (9 AM to 5 PM, 30-minute intervals)
        start_hour = 9
        end_hour = 17
        slot_duration = 30  # minutes
        
        slots = []
        current_time = datetime.combine(target_date, datetime.min.time().replace(hour=start_hour))
        end_time = datetime.combine(target_date, datetime.min.time().replace(hour=end_hour))
        
        while current_time < end_time:
            slot_end = current_time + timedelta(minutes=slot_duration)
            
            # Check if slot is available
            existing = Appointment.query.filter(
                Appointment.doctor_id == doctor_id,
                Appointment.starts_at <= slot_end,
                Appointment.ends_at >= current_time,
                Appointment.status.in_(["scheduled", "ongoing"])
            ).first()
            
            slots.append({
                "start_time": current_time.isoformat(),
                "end_time": slot_end.isoformat(),
                "available": existing is None,
                "display_time": current_time.strftime("%I:%M %p")
            })
            
            current_time = slot_end
        
        return jsonify({
            "success": True,
            "doctor_name": doctor.name,
            "date": date_str,
            "slots": slots
        })
        
    except Exception as e:
        logging.error(f"Get available slots error: {e}")
        return jsonify({"error": f"Failed to retrieve available slots: {str(e)}"}), 500
