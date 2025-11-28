from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
from services.auth import require_auth, get_current_user, require_role
from services.google_services import calendar_service, meet_service
from models import Appointment, User, TimeSlot
from app import db
import logging

bp = Blueprint("appointments", __name__)


@bp.route("/check-calendar-setup", methods=["GET"])
def check_calendar_setup():
    """Diagnostic endpoint to check Google Calendar Service Account setup"""
    try:
        from services.google_calendar_service_account import calendar_service_account
        
        status = calendar_service_account.check_service_account_setup()
        
        test_result = None
        if status['has_credentials']:
            try:
                service = calendar_service_account._get_service()
                if service:
                    calendar_list = service.calendarList().list().execute()
                    test_result = {
                        'calendar_access': True,
                        'calendars_count': len(calendar_list.get('items', []))
                    }
                else:
                    test_result = {'calendar_access': False, 'error': 'Could not build service'}
            except Exception as e:
                test_result = {'calendar_access': False, 'error': str(e)}
        
        return jsonify({
            "success": True,
            "service_account_status": status,
            "calendar_test": test_result,
            "recommendation": _get_setup_recommendation(status, test_result)
        })
        
    except Exception as e:
        logging.error(f"Calendar setup check error: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


def _get_setup_recommendation(status, test_result):
    """Get setup recommendations based on current status"""
    if not status.get('has_credentials'):
        return ("GOOGLE_SERVICE_ACCOUNT_KEY secret is not properly configured. "
                "Make sure the JSON key is stored correctly.")
    
    if test_result and not test_result.get('calendar_access'):
        error = test_result.get('error', '')
        if 'forbidden' in error.lower():
            return ("Service account needs domain-wide delegation enabled in Google Workspace Admin Console. "
                    f"Go to Admin Console > Security > API Controls > Domain-wide delegation and add: "
                    f"{status.get('service_account_email')} with scopes: "
                    "https://www.googleapis.com/auth/calendar, https://www.googleapis.com/auth/calendar.events")
        return f"Calendar API error: {error}"
    
    if test_result and test_result.get('calendar_access'):
        return "Service account is properly configured and can access calendars!"
    
    return "Unknown status - please check the logs"


@bp.route("/", methods=["POST"])
def create_appointment():
    """Create a new appointment with Google Calendar + Meet integration"""
    try:
        from services.auth import get_current_user
        from services.google_calendar_service_account import calendar_service_account
        
        current_user = get_current_user()
        if not current_user:
            return jsonify({"error": "Authentication required"}), 401
        
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        required_fields = ["doctor_id", "slot_id", "symptoms"]
        for field in required_fields:
            if not data.get(field):
                return jsonify({"error": f"{field} is required"}), 400
        
        slot = TimeSlot.query.get(data["slot_id"])
        if not slot:
            return jsonify({"error": "Invalid time slot selected"}), 404
        
        if slot.doctor_id != data["doctor_id"]:
            return jsonify({"error": "Time slot does not belong to selected doctor"}), 400
        
        if slot.is_booked:
            return jsonify({"error": "This time slot is already booked"}), 400
        
        doctor = User.query.filter_by(id=data["doctor_id"], role="doctor").first()
        if not doctor:
            return jsonify({"error": "Doctor not found"}), 404
        
        start_time = slot.starts_at
        end_time = slot.ends_at
        appointment_date = slot.appointment_date
        
        appointment = Appointment()
        appointment.user_id = current_user.id
        appointment.doctor_id = data["doctor_id"]
        appointment.time_slot_id = slot.id
        appointment.appointment_date = appointment_date
        appointment.starts_at = start_time
        appointment.ends_at = end_time
        appointment.symptoms = data["symptoms"]
        appointment.note = data.get("note", "")
        appointment.status = "pending"
        appointment.approval_status = "pending"
        
        db.session.add(appointment)
        slot.is_booked = True
        slot.updated_at = datetime.utcnow()
        db.session.commit()
        
        calendar_result = None
        meet_link = None
        
        if calendar_service_account.has_credentials:
            appointment_data = {
                'doctor_email': doctor.email,
                'patient_email': current_user.email,
                'doctor_name': doctor.name,
                'patient_name': current_user.name,
                'start_time': start_time,
                'end_time': end_time,
                'symptoms': data["symptoms"],
                'appointment_id': appointment.id
            }
            
            calendar_result = calendar_service_account.create_event_for_both_calendars(appointment_data)
            
            if calendar_result and calendar_result.get('success'):
                meet_link = calendar_result.get('meet_link')
                
                if calendar_result.get('doctor_event'):
                    appointment.google_calendar_event_id = calendar_result['doctor_event'].get('event_id')
                
                logging.info(f"✅ Created Google Calendar events for Dr. {doctor.name} and {current_user.name}")
                logging.info(f"✅ Google Meet link: {meet_link}")
        
        if not meet_link:
            from services.doctor_oauth_service import doctor_oauth_service
            
            if doctor.google_access_token:
                calendar_data = {
                    'summary': f'Online Consultation - Red Dot Pharmacy',
                    'description': f'Patient: {current_user.name}\nSymptoms: {data["symptoms"]}',
                    'start_time': start_time,
                    'end_time': end_time,
                    'attendee_emails': [current_user.email, doctor.email],
                    'appointment_id': appointment.id
                }
                
                oauth_result = doctor_oauth_service.create_calendar_event_for_doctor(
                    doctor_id=doctor.id,
                    appointment_data=calendar_data
                )
                
                if oauth_result and oauth_result.get('meet_link'):
                    meet_link = oauth_result['meet_link']
                    appointment.google_calendar_event_id = oauth_result.get('event_id')
                    logging.info(f"✅ Created event via Doctor OAuth: {meet_link}")
        
        if not meet_link:
            db.session.rollback()
            return jsonify({
                "error": "Could not create Google Meet link. Please ensure Google Calendar is properly configured with domain-wide delegation.",
                "details": "The appointment requires Google Calendar integration to generate Google Meet links."
            }), 503
        
        appointment.google_meet_link = meet_link
        db.session.commit()
        
        logging.info(f"📧 Notification to {current_user.email}: Appointment booked with {doctor.name} at {start_time.strftime('%Y-%m-%d %H:%M')}. Meet link: {meet_link}")
        logging.info(f"📧 Notification to {doctor.email}: New appointment from {current_user.name} for {start_time.strftime('%Y-%m-%d %H:%M')}. Meet link: {meet_link}")
        
        return jsonify({
            "success": True,
            "appointment": {
                "id": appointment.id,
                "doctor_name": doctor.name,
                "start_time": appointment.starts_at.isoformat(),
                "end_time": appointment.ends_at.isoformat(),
                "status": appointment.status,
                "google_meet_link": appointment.google_meet_link,
                "calendar_integrated": calendar_result.get('success') if calendar_result else False
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
                "doctor_specialization": getattr(doctor, 'specialization', 'General Practice') if doctor else "General Practice",
                "starts_at": appt.starts_at.isoformat(),
                "start_time": appt.starts_at.isoformat(),
                "end_time": appt.ends_at.isoformat(),
                "status": appt.status,
                "approval_status": appt.approval_status,
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
                "specialization": doctor.specialization,
                "qualification": doctor.qualification,
                "experience_years": doctor.experience_years,
                "current_hospital": doctor.current_hospital,
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
    """Get available appointment slots for a doctor from their created time slots"""
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
        
        # Get doctor's available time slots for the target date
        # Only show future slots (not past slots if today is selected)
        now = datetime.now()
        available_slots = TimeSlot.query.filter(
            TimeSlot.doctor_id == doctor_id,
            TimeSlot.appointment_date == target_date,
            TimeSlot.is_booked == False,
            TimeSlot.starts_at > now  # Only future slots
        ).order_by(TimeSlot.starts_at).all()
        
        slots = []
        for slot in available_slots:
            slots.append({
                "slot_id": slot.id,
                "start_time": slot.starts_at.isoformat(),
                "end_time": slot.ends_at.isoformat(),
                "display_time": slot.starts_at.strftime("%I:%M %p") + " - " + slot.ends_at.strftime("%I:%M %p"),
                "available": True
            })
        
        return jsonify({
            "success": True,
            "doctor_name": doctor.name,
            "date": date_str,
            "slots": slots,
            "total_slots": len(slots)
        })
        
    except Exception as e:
        logging.error(f"Get available slots error: {e}")
        return jsonify({"error": f"Failed to retrieve available slots: {str(e)}"}), 500


@bp.route("/schedule-appointment", methods=["POST"])
def schedule_appointment():
    """
    Alternative endpoint for scheduling appointments as specified in requirements.
    Accepts: doctorEmail, patientEmail, start, end, reason
    Returns: meetLink, appointment details
    
    This endpoint creates calendar events in both doctor's and patient's Google Calendars
    with automatic Google Meet link generation.
    """
    try:
        from services.google_calendar_service_account import calendar_service_account
        
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided", "success": False}), 400
        
        doctor_email = data.get("doctorEmail")
        patient_email = data.get("patientEmail")
        start_time_str = data.get("start")
        end_time_str = data.get("end")
        reason = data.get("reason", "General medical consultation")
        
        if not all([doctor_email, patient_email, start_time_str]):
            return jsonify({
                "error": "Missing required fields: doctorEmail, patientEmail, start",
                "success": False
            }), 400
        
        try:
            start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
            if end_time_str:
                end_time = datetime.fromisoformat(end_time_str.replace('Z', '+00:00'))
            else:
                end_time = start_time + timedelta(minutes=30)
        except ValueError as e:
            return jsonify({
                "error": f"Invalid date format: {str(e)}",
                "success": False
            }), 400
        
        doctor = User.query.filter_by(email=doctor_email, role="doctor").first()
        if not doctor:
            return jsonify({"error": "Doctor not found with provided email", "success": False}), 404
        
        patient = User.query.filter_by(email=patient_email).first()
        if not patient:
            return jsonify({"error": "Patient not found with provided email", "success": False}), 404
        
        appointment = Appointment()
        appointment.user_id = patient.id
        appointment.doctor_id = doctor.id
        appointment.appointment_date = start_time.date()
        appointment.starts_at = start_time
        appointment.ends_at = end_time
        appointment.symptoms = reason
        appointment.status = "pending"
        appointment.approval_status = "pending"
        
        db.session.add(appointment)
        db.session.commit()
        
        meet_link = None
        calendar_result = None
        
        if calendar_service_account.has_credentials:
            appointment_data = {
                'doctor_email': doctor.email,
                'patient_email': patient.email,
                'doctor_name': doctor.name,
                'patient_name': patient.name,
                'start_time': start_time,
                'end_time': end_time,
                'symptoms': reason,
                'appointment_id': appointment.id
            }
            
            calendar_result = calendar_service_account.create_event_for_both_calendars(appointment_data)
            
            if calendar_result and calendar_result.get('success'):
                meet_link = calendar_result.get('meet_link')
                if calendar_result.get('doctor_event'):
                    appointment.google_calendar_event_id = calendar_result['doctor_event'].get('event_id')
                logging.info(f"✅ Created Google Calendar events with Meet link: {meet_link}")
        
        if not meet_link:
            db.session.rollback()
            return jsonify({
                "success": False,
                "error": "Could not create Google Meet link. Google Calendar integration is required.",
                "details": "Please ensure the service account has domain-wide delegation enabled and can access user calendars."
            }), 503
        
        appointment.google_meet_link = meet_link
        db.session.commit()
        
        return jsonify({
            "success": True,
            "meetLink": meet_link,
            "appointment": {
                "id": appointment.id,
                "doctorName": doctor.name,
                "doctorEmail": doctor.email,
                "patientName": patient.name,
                "patientEmail": patient.email,
                "start": start_time.isoformat(),
                "end": end_time.isoformat(),
                "reason": reason,
                "status": appointment.status,
                "calendarIntegrated": True
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Schedule appointment error: {e}")
        return jsonify({
            "error": f"Failed to schedule appointment: {str(e)}",
            "success": False
        }), 500
