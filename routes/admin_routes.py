from flask import Blueprint, request, jsonify, render_template
from datetime import datetime, timedelta, date, time as dt_time
from services.auth import require_auth, get_current_user, require_role
from routes.admin_auth_routes import get_current_admin, require_admin
from models import User, Medicine, Appointment, Order, OrderItem, ChatLog, TimeSlot, DoctorAvailability
from app import db
import logging
import hashlib
import os
from werkzeug.utils import secure_filename

bp = Blueprint("admin", __name__)

def phash(pw):
    """Hash password using SHA256"""
    return hashlib.sha256(pw.encode()).hexdigest()

@bp.route("/")
def admin_main():
    """Main admin route - render admin dashboard"""
    return render_template("admin.html")

@bp.route("/dashboard")  
def admin_dashboard():
    """Alternative route for admin dashboard"""
    return render_template("admin.html")

@bp.route("/api/stats", methods=["GET"])
def get_dashboard_stats():
    """Get comprehensive dashboard statistics"""
    try:
        current_admin = get_current_admin()
        if not current_admin:
            return jsonify({"error": "Admin access required"}), 403
        
        # User statistics
        total_users = User.query.count()
        total_patients = User.query.filter_by(role="patient").count()
        total_doctors = User.query.filter_by(role="doctor").count()
        new_users_today = User.query.filter(
            User.created_at >= datetime.now().date()
        ).count()
        
        # Appointment statistics
        total_appointments = Appointment.query.count()
        today_appointments = Appointment.query.filter(
            db.func.date(Appointment.starts_at) == datetime.now().date()
        ).count()
        pending_appointments = Appointment.query.filter_by(status="scheduled").count()
        completed_appointments = Appointment.query.filter_by(status="completed").count()
        
        # Order statistics
        total_orders = Order.query.count()
        pending_orders = Order.query.filter_by(status="pending").count()
        processing_orders = Order.query.filter_by(status="processing").count()
        delivered_orders = Order.query.filter_by(status="delivered").count()
        
        # Revenue calculation (delivered orders)
        total_revenue = db.session.query(db.func.sum(Order.total_amount))\
                                 .filter_by(status="delivered").scalar() or 0
        
        today_revenue = db.session.query(db.func.sum(Order.total_amount))\
                                 .filter(
                                     Order.status == "delivered",
                                     db.func.date(Order.created_at) == datetime.now().date()
                                 ).scalar() or 0
        
        # Medicine statistics
        total_medicines = Medicine.query.count()
        in_stock_medicines = Medicine.query.filter_by(status="in_stock").count()
        out_of_stock_medicines = Medicine.query.filter_by(status="out_of_stock").count()
        low_stock_medicines = Medicine.query.filter(
            Medicine.stock_quantity <= 10,
            Medicine.status == "in_stock"
        ).count()
        
        # Chat statistics
        total_chats = ChatLog.query.count()
        flagged_chats = ChatLog.query.filter_by(flagged=True).count()
        today_chats = ChatLog.query.filter(
            db.func.date(ChatLog.created_at) == datetime.now().date()
        ).count()
        
        return jsonify({
            "success": True,
            "stats": {
                "users": {
                    "total": total_users,
                    "patients": total_patients,
                    "doctors": total_doctors,
                    "new_today": new_users_today
                },
                "appointments": {
                    "total": total_appointments,
                    "today": today_appointments,
                    "pending": pending_appointments,
                    "completed": completed_appointments
                },
                "orders": {
                    "total": total_orders,
                    "pending": pending_orders,
                    "processing": processing_orders,
                    "delivered": delivered_orders
                },
                "revenue": {
                    "total": total_revenue,
                    "today": today_revenue
                },
                "medicines": {
                    "total": total_medicines,
                    "in_stock": in_stock_medicines,
                    "out_of_stock": out_of_stock_medicines,
                    "low_stock": low_stock_medicines
                },
                "chat": {
                    "total": total_chats,
                    "flagged": flagged_chats,
                    "today": today_chats
                }
            }
        })
        
    except Exception as e:
        logging.error(f"Dashboard stats error: {e}")
        return jsonify({"error": f"Failed to retrieve statistics: {str(e)}"}), 500

@bp.route("/api/users", methods=["GET"])
def list_users():
    """List all users with pagination"""
    try:
        current_admin = get_current_admin()
        if not current_admin:
            return jsonify({"error": "Admin access required"}), 403
        
        # Get query parameters
        role = request.args.get('role')
        search = request.args.get('search')
        limit = int(request.args.get('limit', 20))
        offset = int(request.args.get('offset', 0))
        
        # Build query
        query = User.query
        
        if role:
            query = query.filter_by(role=role)
        
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                db.or_(
                    User.name.ilike(search_term),
                    User.email.ilike(search_term),
                    User.phone.ilike(search_term)
                )
            )
        
        total_count = query.count()
        users = query.order_by(User.created_at.desc()).offset(offset).limit(limit).all()
        
        user_list = []
        for user in users:
            # Get user statistics
            if user.role == "patient":
                appointments_count = Appointment.query.filter_by(user_id=user.id).count()
                orders_count = Order.query.filter_by(user_id=user.id).count()
            elif user.role == "doctor":
                appointments_count = Appointment.query.filter_by(doctor_id=user.id).count()
                orders_count = 0
            else:
                appointments_count = 0
                orders_count = 0
            
            user_list.append({
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "phone": user.phone,
                "role": user.role,
                "created_at": user.created_at.isoformat(),
                "appointments_count": appointments_count,
                "orders_count": orders_count
            })
        
        return jsonify({
            "success": True,
            "users": user_list,
            "total_count": total_count,
            "offset": offset,
            "limit": limit
        })
        
    except Exception as e:
        logging.error(f"List users error: {e}")
        return jsonify({"error": f"Failed to retrieve users: {str(e)}"}), 500

@bp.route("/api/users", methods=["POST"])
def create_user():
    """Create new user (doctor/admin)"""
    try:
        current_admin = get_current_admin()
        if not current_admin:
            return jsonify({"error": "Admin access required"}), 403
        
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Validate required fields
        required_fields = ["name", "email", "password", "role"]
        for field in required_fields:
            if not data.get(field):
                return jsonify({"error": f"{field} is required"}), 400
        
        # Validate role
        if data["role"] not in ["doctor", "admin", "patient"]:
            return jsonify({"error": "Invalid role"}), 400
        
        # Check if email exists
        existing_user = User.query.filter_by(email=data["email"]).first()
        if existing_user:
            return jsonify({"error": "Email already exists"}), 400
        
        # Create user
        new_user = User()
        new_user.name = data["name"]
        new_user.email = data["email"]
        new_user.phone = data.get("phone", "")
        new_user.role = data["role"]
        new_user.password_hash = phash(data["password"])
        
        db.session.add(new_user)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": f"{data['role'].title()} created successfully",
            "user": {
                "id": new_user.id,
                "name": new_user.name,
                "email": new_user.email,
                "role": new_user.role
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Create user error: {e}")
        return jsonify({"error": f"Failed to create user: {str(e)}"}), 500

@bp.route("/api/users/<int:user_id>", methods=["PUT"])
def update_user(user_id):
    """Update user details"""
    try:
        current_admin = get_current_admin()
        if not current_admin:
            return jsonify({"error": "Admin access required"}), 403
        
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        user = User.query.get_or_404(user_id)
        
        # Update allowed fields
        if "name" in data:
            user.name = data["name"]
        if "phone" in data:
            user.phone = data["phone"]
        if "role" in data and data["role"] in ["doctor", "admin", "patient"]:
            user.role = data["role"]
        
        # Update password if provided
        if "password" in data and data["password"]:
            user.password_hash = phash(data["password"])
        
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "User updated successfully",
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "phone": user.phone,
                "role": user.role
            }
        })
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Update user error: {e}")
        return jsonify({"error": f"Failed to update user: {str(e)}"}), 500

@bp.route("/api/chat-logs", methods=["GET"])
def get_chat_logs():
    """Get chat logs with filtering"""
    try:
        current_admin = get_current_admin()
        if not current_admin:
            return jsonify({"error": "Admin access required"}), 403
        
        # Get query parameters
        flagged_only = request.args.get('flagged') == 'true'
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        
        # Build query
        query = ChatLog.query
        
        if flagged_only:
            query = query.filter_by(flagged=True)
        
        total_count = query.count()
        logs = query.order_by(ChatLog.created_at.desc()).offset(offset).limit(limit).all()
        
        log_list = []
        for log in logs:
            user = User.query.get(log.user_id) if log.user_id else None
            
            log_list.append({
                "id": log.id,
                "user_name": user.name if user else "Anonymous",
                "session_id": log.session_id,
                "message": log.message,
                "response": log.response,
                "language": log.language,
                "flagged": log.flagged,
                "created_at": log.created_at.isoformat()
            })
        
        return jsonify({
            "success": True,
            "logs": log_list,
            "total_count": total_count,
            "offset": offset,
            "limit": limit
        })
        
    except Exception as e:
        logging.error(f"Get chat logs error: {e}")
        return jsonify({"error": f"Failed to retrieve chat logs: {str(e)}"}), 500

@bp.route("/api/recent-activity", methods=["GET"])
def get_recent_activity():
    """Get recent system activity"""
    try:
        current_admin = get_current_admin()
        if not current_admin:
            return jsonify({"error": "Admin access required"}), 403
        
        activities = []
        
        # Recent registrations
        recent_users = User.query.filter(
            User.created_at >= datetime.now() - timedelta(days=7)
        ).order_by(User.created_at.desc()).limit(5).all()
        
        for user in recent_users:
            activities.append({
                "type": "registration",
                "message": f"New {user.role} registered: {user.name}",
                "timestamp": user.created_at.isoformat(),
                "icon": "user-plus"
            })
        
        # Recent orders
        recent_orders = Order.query.filter(
            Order.created_at >= datetime.now() - timedelta(days=7)
        ).order_by(Order.created_at.desc()).limit(5).all()
        
        for order in recent_orders:
            customer = User.query.get(order.user_id)
            activities.append({
                "type": "order",
                "message": f"New order #{order.id} by {customer.name if customer else 'Unknown'} - PKR {order.total_amount}",
                "timestamp": order.created_at.isoformat(),
                "icon": "shopping-cart"
            })
        
        # Recent appointments
        recent_appointments = Appointment.query.filter(
            Appointment.created_at >= datetime.now() - timedelta(days=7)
        ).order_by(Appointment.created_at.desc()).limit(5).all()
        
        for appt in recent_appointments:
            patient = User.query.get(appt.user_id)
            doctor = User.query.get(appt.doctor_id)
            activities.append({
                "type": "appointment",
                "message": f"Appointment booked: {patient.name if patient else 'Unknown'} with {doctor.name if doctor else 'Unknown'}",
                "timestamp": appt.created_at.isoformat(),
                "icon": "calendar"
            })
        
        # Sort all activities by timestamp
        activities.sort(key=lambda x: x["timestamp"], reverse=True)
        
        return jsonify({
            "success": True,
            "activities": activities[:15]  # Return top 15 activities
        })
        
    except Exception as e:
        logging.error(f"Get recent activity error: {e}")
        return jsonify({"error": f"Failed to retrieve recent activity: {str(e)}"}), 500

@bp.route("/api/export/data", methods=["GET"])
def export_data():
    """Export system data for backup/analysis"""
    try:
        current_admin = get_current_admin()
        if not current_admin:
            return jsonify({"error": "Admin access required"}), 403
        
        export_type = request.args.get('type', 'summary')
        
        if export_type == 'summary':
            # Export summary statistics
            data = {
                "export_date": datetime.now().isoformat(),
                "total_users": User.query.count(),
                "total_appointments": Appointment.query.count(),
                "total_orders": Order.query.count(),
                "total_medicines": Medicine.query.count(),
                "total_revenue": db.session.query(db.func.sum(Order.total_amount)).filter_by(status="delivered").scalar() or 0
            }
        
        elif export_type == 'orders':
            # Export order data
            orders = Order.query.all()
            data = []
            for order in orders:
                customer = User.query.get(order.user_id)
                data.append({
                    "order_id": order.id,
                    "customer_name": customer.name if customer else "Unknown",
                    "total_amount": order.total_amount,
                    "status": order.status,
                    "created_at": order.created_at.isoformat()
                })
        
        else:
            return jsonify({"error": "Invalid export type"}), 400
        
        return jsonify({
            "success": True,
            "export_type": export_type,
            "data": data
        })
        
    except Exception as e:
        logging.error(f"Export data error: {e}")
        return jsonify({"error": f"Failed to export data: {str(e)}"}), 500

# ============ MEDICINE MANAGEMENT ============

@bp.route("/api/medicines", methods=["GET"])
def list_medicines():
    """List all medicines with pagination"""
    try:
        current_admin = get_current_admin()
        if not current_admin:
            return jsonify({"error": "Admin access required"}), 403
        
        # Get query parameters
        category = request.args.get('category')
        search = request.args.get('search')
        status = request.args.get('status')
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        
        # Build query
        query = Medicine.query
        
        # Apply filters
        if status:
            query = query.filter_by(status=status)
        
        if category:
            query = query.filter_by(category=category)
        
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                db.or_(
                    Medicine.name.ilike(search_term),
                    Medicine.chemical.ilike(search_term),
                    Medicine.description.ilike(search_term)
                )
            )
        
        # Get total count for pagination
        total_count = query.count()
        
        # Apply pagination
        medicines = query.order_by(Medicine.created_at.desc()).offset(offset).limit(limit).all()
        
        # Format response
        medicine_list = []
        for med in medicines:
            medicine_list.append({
                "id": med.id,
                "name": med.name,
                "chemical": med.chemical,
                "description": med.description,
                "price": med.price,
                "image_path": med.image_path or "/static/images/default-medicine.png",
                "status": med.status,
                "stock_quantity": med.stock_quantity,
                "category": med.category,
                "created_at": med.created_at.isoformat() if med.created_at else "",
                "updated_at": med.updated_at.isoformat() if hasattr(med, 'updated_at') and med.updated_at else ""
            })
        
        return jsonify({
            "success": True,
            "medicines": medicine_list,
            "total_count": total_count,
            "offset": offset,
            "limit": limit
        })
        
    except Exception as e:
        logging.error(f"List medicines error: {e}")
        return jsonify({"error": f"Failed to retrieve medicines: {str(e)}"}), 500

@bp.route("/api/medicines", methods=["POST"])
def add_medicine():
    """Add new medicine with file upload"""
    try:
        current_admin = get_current_admin()
        if not current_admin:
            return jsonify({"error": "Admin access required"}), 403
        
        # Handle file upload
        image_path = None
        if 'image_file' in request.files:
            file = request.files['image_file']
            if file and file.filename:
                # Secure the filename
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{timestamp}_{filename}"
                
                # Ensure uploads directory exists
                upload_dir = os.path.join("static", "uploads", "medicines")
                os.makedirs(upload_dir, exist_ok=True)
                
                # Save the file
                file_path = os.path.join(upload_dir, filename)
                file.save(file_path)
                image_path = f"/static/uploads/medicines/{filename}"
        
        # Get form data
        data = request.form
        
        # Validate required fields
        if not data.get('name') or not data.get('price'):
            return jsonify({"error": "Name and price are required"}), 400
        
        # Create new medicine
        medicine = Medicine()
        medicine.name = data['name']
        medicine.chemical = data.get('chemical', '')
        medicine.description = data.get('description', '')
        medicine.price = int(data['price'])
        medicine.image_path = image_path
        medicine.status = data.get('status', 'in_stock')
        medicine.stock_quantity = int(data.get('stock_quantity', 0))
        medicine.category = data.get('category', 'General')
        
        db.session.add(medicine)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Medicine added successfully",
            "medicine": {
                "id": medicine.id,
                "name": medicine.name,
                "price": medicine.price,
                "category": medicine.category,
                "status": medicine.status,
                "stock_quantity": medicine.stock_quantity,
                "image_path": medicine.image_path
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Add medicine error: {e}")
        return jsonify({"error": f"Failed to add medicine: {str(e)}"}), 500

@bp.route("/api/medicines/<int:medicine_id>", methods=["PUT"])
def update_medicine(medicine_id):
    """Update medicine"""
    try:
        current_admin = get_current_admin()
        if not current_admin:
            return jsonify({"error": "Admin access required"}), 403
        
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        medicine = Medicine.query.get_or_404(medicine_id)
        
        # Update fields
        if "name" in data:
            medicine.name = data["name"]
        if "chemical" in data:
            medicine.chemical = data["chemical"]
        if "description" in data:
            medicine.description = data["description"]
        if "price" in data:
            medicine.price = int(data["price"])
        if "status" in data:
            medicine.status = data["status"]
        if "stock_quantity" in data:
            medicine.stock_quantity = int(data["stock_quantity"])
        if "category" in data:
            medicine.category = data["category"]
        
        # Only set updated_at if the column exists
        if hasattr(medicine, 'updated_at'):
            medicine.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Medicine updated successfully",
            "medicine": {
                "id": medicine.id,
                "name": medicine.name,
                "price": medicine.price,
                "status": medicine.status,
                "stock_quantity": medicine.stock_quantity
            }
        })
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Update medicine error: {e}")
        return jsonify({"error": f"Failed to update medicine: {str(e)}"}), 500

@bp.route("/api/medicines/<int:medicine_id>", methods=["DELETE"])
def delete_medicine(medicine_id):
    """Delete medicine"""
    try:
        current_admin = get_current_admin()
        if not current_admin:
            return jsonify({"error": "Admin access required"}), 403
        
        medicine = Medicine.query.get_or_404(medicine_id)
        
        # Check if medicine is in any orders
        order_items = OrderItem.query.filter_by(medicine_id=medicine_id).first()
        
        if order_items:
            # Instead of deleting, mark as discontinued
            medicine.status = "discontinued"
            db.session.commit()
            
            return jsonify({
                "success": True,
                "message": "Medicine marked as discontinued (has order history)"
            })
        else:
            # Safe to delete
            # Remove image file if exists
            if medicine.image_path and medicine.image_path.startswith("/static/uploads/"):
                image_file_path = medicine.image_path[1:]  # Remove leading slash
                if os.path.exists(image_file_path):
                    os.remove(image_file_path)
            
            db.session.delete(medicine)
            db.session.commit()
            
            return jsonify({
                "success": True,
                "message": "Medicine deleted successfully"
            })
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Delete medicine error: {e}")
        return jsonify({"error": f"Failed to delete medicine: {str(e)}"}), 500

# ============ TIME SLOT MANAGEMENT ============

@bp.route("/api/timeslots", methods=["GET"])
def list_time_slots():
    """List all time slots"""
    try:
        current_admin = get_current_admin()
        if not current_admin:
            return jsonify({"error": "Admin access required"}), 403
        
        time_slots = TimeSlot.query.join(User).order_by(TimeSlot.appointment_date, TimeSlot.starts_at).all()
        
        slots_list = []
        for slot in time_slots:
            slots_list.append({
                "id": slot.id,
                "doctor_id": slot.doctor_id,
                "doctor_name": slot.doctor.name,
                "appointment_date": slot.appointment_date.isoformat() if slot.appointment_date else None,
                "starts_at": slot.starts_at.isoformat() if slot.starts_at else None,
                "ends_at": slot.ends_at.isoformat() if slot.ends_at else None,
                "start_time": slot.starts_at.strftime("%H:%M") if slot.starts_at else "",
                "end_time": slot.ends_at.strftime("%H:%M") if slot.ends_at else "",
                "is_booked": slot.is_booked,
                "google_event_id": slot.google_event_id,
                "created_at": slot.created_at.isoformat() if slot.created_at else None
            })
        
        return jsonify({"success": True, "time_slots": slots_list})
        
    except Exception as e:
        logging.error(f"List time slots error: {e}")
        return jsonify({"error": f"Failed to retrieve time slots: {str(e)}"}), 500

# ============ DOCTOR AVAILABILITY MANAGEMENT ============

@bp.route("/api/availability", methods=["GET"])
def list_availabilities():
    """List all doctor availabilities"""
    try:
        current_admin = get_current_admin()
        if not current_admin:
            return jsonify({"error": "Admin access required"}), 403
        
        doctor_id = request.args.get('doctor_id')
        
        query = DoctorAvailability.query.join(User)
        if doctor_id:
            query = query.filter(DoctorAvailability.doctor_id == doctor_id)
        
        availabilities = query.order_by(DoctorAvailability.day_of_week, DoctorAvailability.start_time).all()
        
        avail_list = []
        for avail in availabilities:
            avail_list.append({
                "id": avail.id,
                "doctor_id": avail.doctor_id,
                "doctor_name": avail.doctor.name,
                "day_of_week": avail.day_of_week,
                "day_name": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][avail.day_of_week],
                "start_time": avail.start_time.strftime("%H:%M"),
                "end_time": avail.end_time.strftime("%H:%M"),
                "slot_duration": avail.slot_duration,
                "is_active": avail.is_active,
                "created_at": avail.created_at.isoformat() if avail.created_at else None
            })
        
        return jsonify({"success": True, "availabilities": avail_list})
        
    except Exception as e:
        logging.error(f"List availabilities error: {e}")
        return jsonify({"error": f"Failed to retrieve availabilities: {str(e)}"}), 500

@bp.route("/api/availability", methods=["POST"])
def create_availability():
    """Create doctor availability"""
    try:
        current_admin = get_current_admin()
        if not current_admin:
            return jsonify({"error": "Admin access required"}), 403
        
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Validate required fields
        required_fields = ["doctor_id", "day_of_week", "start_time", "end_time"]
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"{field} is required"}), 400
        
        # Validate doctor exists
        doctor = User.query.filter_by(id=data["doctor_id"], role="doctor").first()
        if not doctor:
            return jsonify({"error": "Invalid doctor selected"}), 400
        
        # Validate day_of_week
        day_of_week = int(data["day_of_week"])
        if day_of_week < 0 or day_of_week > 6:
            return jsonify({"error": "day_of_week must be 0-6 (Monday-Sunday)"}), 400
        
        # Parse time strings
        try:
            start_time = dt_time.fromisoformat(data["start_time"])
            end_time = dt_time.fromisoformat(data["end_time"])
        except ValueError:
            return jsonify({"error": "Invalid time format. Use HH:MM"}), 400
        
        if start_time >= end_time:
            return jsonify({"error": "Start time must be before end time"}), 400
        
        # Check for overlapping availability
        existing = DoctorAvailability.query.filter(
            DoctorAvailability.doctor_id == data["doctor_id"],
            DoctorAvailability.day_of_week == day_of_week,
            DoctorAvailability.is_active == True
        ).all()
        
        for avail in existing:
            if (start_time < avail.end_time and end_time > avail.start_time):
                return jsonify({"error": f"Overlaps with existing availability on {['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][day_of_week]}"}), 400
        
        # Create availability
        new_avail = DoctorAvailability(
            doctor_id=data["doctor_id"],
            day_of_week=day_of_week,
            start_time=start_time,
            end_time=end_time,
            slot_duration=data.get("slot_duration", 30),
            is_active=True
        )
        
        db.session.add(new_avail)
        db.session.commit()
        
        # Auto-generate time slots for next 30 days
        generate_slots_from_availability(new_avail.id, days_ahead=30)
        
        return jsonify({
            "success": True,
            "message": "Doctor availability created successfully",
            "availability": {
                "id": new_avail.id,
                "doctor_name": doctor.name,
                "day_name": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][day_of_week],
                "start_time": start_time.strftime("%H:%M"),
                "end_time": end_time.strftime("%H:%M")
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Create availability error: {e}")
        return jsonify({"error": f"Failed to create availability: {str(e)}"}), 500

@bp.route("/api/availability/<int:avail_id>", methods=["PUT"])
def update_availability(avail_id):
    """Update doctor availability"""
    try:
        current_admin = get_current_admin()
        if not current_admin:
            return jsonify({"error": "Admin access required"}), 403
        
        avail = DoctorAvailability.query.get_or_404(avail_id)
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Update fields
        if "start_time" in data:
            avail.start_time = dt_time.fromisoformat(data["start_time"])
        if "end_time" in data:
            avail.end_time = dt_time.fromisoformat(data["end_time"])
        if "slot_duration" in data:
            avail.slot_duration = int(data["slot_duration"])
        if "is_active" in data:
            avail.is_active = data["is_active"]
        
        avail.updated_at = datetime.utcnow()
        db.session.commit()
        
        # Regenerate future time slots
        if avail.is_active:
            generate_slots_from_availability(avail.id, days_ahead=30)
        
        return jsonify({"success": True, "message": "Availability updated successfully"})
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Update availability error: {e}")
        return jsonify({"error": f"Failed to update availability: {str(e)}"}), 500

@bp.route("/api/availability/<int:avail_id>", methods=["DELETE"])
def delete_availability(avail_id):
    """Delete doctor availability"""
    try:
        current_admin = get_current_admin()
        if not current_admin:
            return jsonify({"error": "Admin access required"}), 403
        
        avail = DoctorAvailability.query.get_or_404(avail_id)
        
        # Just mark as inactive instead of deleting
        avail.is_active = False
        avail.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({"success": True, "message": "Availability deleted successfully"})
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Delete availability error: {e}")
        return jsonify({"error": f"Failed to delete availability: {str(e)}"}), 500

def generate_slots_from_availability(availability_id, days_ahead=30):
    """Auto-generate TimeSlots from DoctorAvailability for future dates"""
    try:
        avail = DoctorAvailability.query.get(availability_id)
        if not avail or not avail.is_active:
            return
        
        today = date.today()
        end_date = today + timedelta(days=days_ahead)
        
        current_date = today
        while current_date <= end_date:
            # Check if this date matches the availability day_of_week
            if current_date.weekday() == avail.day_of_week:
                # Generate slots for this day
                current_time = datetime.combine(current_date, avail.start_time)
                end_time = datetime.combine(current_date, avail.end_time)
                
                while current_time < end_time:
                    slot_end = current_time + timedelta(minutes=avail.slot_duration)
                    if slot_end > end_time:
                        break
                    
                    # Check if slot already exists
                    existing = TimeSlot.query.filter_by(
                        doctor_id=avail.doctor_id,
                        appointment_date=current_date,
                        starts_at=current_time,
                        ends_at=slot_end
                    ).first()
                    
                    if not existing:
                        new_slot = TimeSlot(
                            doctor_id=avail.doctor_id,
                            appointment_date=current_date,
                            starts_at=current_time,
                            ends_at=slot_end,
                            is_booked=False
                        )
                        db.session.add(new_slot)
                    
                    current_time = slot_end
            
            current_date += timedelta(days=1)
        
        db.session.commit()
        logging.info(f"Generated slots for availability {availability_id}")
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Generate slots error: {e}")

@bp.route("/api/availability/generate-slots", methods=["POST"])
def trigger_slot_generation():
    """Manually trigger slot generation for all active availabilities"""
    try:
        current_admin = get_current_admin()
        if not current_admin:
            return jsonify({"error": "Admin access required"}), 403
        
        availabilities = DoctorAvailability.query.filter_by(is_active=True).all()
        
        for avail in availabilities:
            generate_slots_from_availability(avail.id, days_ahead=30)
        
        return jsonify({
            "success": True,
            "message": f"Generated slots for {len(availabilities)} doctor availabilities"
        })
        
    except Exception as e:
        logging.error(f"Trigger slot generation error: {e}")
        return jsonify({"error": f"Failed to generate slots: {str(e)}"}), 500

@bp.route("/api/timeslots/<int:slot_id>", methods=["PUT"])
def update_time_slot(slot_id):
    """Update a time slot"""
    try:
        current_admin = get_current_admin()
        if not current_admin:
            return jsonify({"error": "Admin access required"}), 403
        
        slot = TimeSlot.query.get_or_404(slot_id)
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Update fields
        if "is_available" in data:
            slot.is_available = data["is_available"]
        if "max_appointments" in data:
            slot.max_appointments = data["max_appointments"]
        
        slot.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({"success": True, "message": "Time slot updated successfully"})
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Update time slot error: {e}")
        return jsonify({"error": f"Failed to update time slot: {str(e)}"}), 500

@bp.route("/api/timeslots/<int:slot_id>", methods=["DELETE"])
def delete_time_slot(slot_id):
    """Delete a time slot"""
    try:
        current_admin = get_current_admin()
        if not current_admin:
            return jsonify({"error": "Admin access required"}), 403
        
        slot = TimeSlot.query.get_or_404(slot_id)
        
        # Check if there are pending appointments for this slot
        pending_appointments = Appointment.query.filter_by(
            time_slot_id=slot_id,
            approval_status="pending"
        ).count()
        
        if pending_appointments > 0:
            return jsonify({"error": "Cannot delete time slot with pending appointments"}), 400
        
        db.session.delete(slot)
        db.session.commit()
        
        return jsonify({"success": True, "message": "Time slot deleted successfully"})
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Delete time slot error: {e}")
        return jsonify({"error": f"Failed to delete time slot: {str(e)}"}), 500

# ============ DOCTOR MANAGEMENT ============

@bp.route("/api/doctors", methods=["GET"])
def list_doctors():
    """List all doctors"""
    try:
        current_admin = get_current_admin()
        if not current_admin:
            return jsonify({"error": "Admin access required"}), 403
        
        doctors = User.query.filter_by(role="doctor").all()
        
        doctors_list = []
        for doctor in doctors:
            doctors_list.append({
                "id": doctor.id,
                "name": doctor.name,
                "email": doctor.email,
                "phone": doctor.phone,
                "specialization": doctor.specialization,
                "qualification": doctor.qualification,
                "experience_years": doctor.experience_years,
                "current_hospital": doctor.current_hospital,
                "created_at": doctor.created_at.isoformat() if doctor.created_at else None,
                "appointment_count": doctor.doctor_appointments.count()
            })
        
        return jsonify({
            "success": True,
            "doctors": doctors_list,
            "total_count": len(doctors_list)
        })
        
    except Exception as e:
        logging.error(f"List doctors error: {e}")
        return jsonify({"error": f"Failed to load doctors: {str(e)}"}), 500

@bp.route("/api/doctors", methods=["POST"])
def create_doctor():
    """Create a new doctor"""
    try:
        current_admin = get_current_admin()
        if not current_admin:
            return jsonify({"error": "Admin access required"}), 403
        
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Validate required fields
        required_fields = ["name", "email", "phone", "specialization", "qualification", "experience_years", "current_hospital"]
        for field in required_fields:
            if not data.get(field):
                return jsonify({"error": f"{field} is required"}), 400
        
        # Check if email already exists
        existing_user = User.query.filter_by(email=data["email"]).first()
        if existing_user:
            return jsonify({"error": "Email already exists"}), 400
        
        # Create new doctor
        from services.auth import phash
        new_doctor = User()
        new_doctor.name = data["name"]
        new_doctor.email = data["email"]
        new_doctor.phone = data["phone"]
        new_doctor.specialization = data["specialization"]
        new_doctor.qualification = data["qualification"]
        new_doctor.experience_years = data["experience_years"]
        new_doctor.current_hospital = data["current_hospital"]
        new_doctor.role = "doctor"
        new_doctor.password_hash = phash("doctor123")  # Default password
        new_doctor.doctor_password_set = False
        
        db.session.add(new_doctor)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Doctor created successfully",
            "doctor": {
                "id": new_doctor.id,
                "name": new_doctor.name,
                "email": new_doctor.email,
                "phone": new_doctor.phone,
                "default_password": "doctor123"
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Create doctor error: {e}")
        return jsonify({"error": f"Failed to create doctor: {str(e)}"}), 500

@bp.route("/api/doctors/<int:doctor_id>", methods=["PUT"])
def update_doctor(doctor_id):
    """Update a doctor"""
    try:
        current_admin = get_current_admin()
        if not current_admin:
            return jsonify({"error": "Admin access required"}), 403
        
        doctor = User.query.filter_by(id=doctor_id, role="doctor").first()
        if not doctor:
            return jsonify({"error": "Doctor not found"}), 404
        
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Update fields
        if data.get("name"):
            doctor.name = data["name"]
        if data.get("email"):
            # Check if new email already exists (excluding current doctor)
            existing = User.query.filter(User.email == data["email"], User.id != doctor_id).first()
            if existing:
                return jsonify({"error": "Email already exists"}), 400
            doctor.email = data["email"]
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
        
        doctor.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Doctor updated successfully",
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
        logging.error(f"Update doctor error: {e}")
        return jsonify({"error": f"Failed to update doctor: {str(e)}"}), 500

@bp.route("/api/doctors/<int:doctor_id>", methods=["DELETE"])
def delete_doctor(doctor_id):
    """Delete a doctor"""
    try:
        current_admin = get_current_admin()
        if not current_admin:
            return jsonify({"error": "Admin access required"}), 403
        
        doctor = User.query.filter_by(id=doctor_id, role="doctor").first()
        if not doctor:
            return jsonify({"error": "Doctor not found"}), 404
        
        # Check if doctor has pending appointments
        pending_appointments = Appointment.query.filter_by(
            doctor_id=doctor_id,
            approval_status="pending"
        ).count()
        
        if pending_appointments > 0:
            return jsonify({"error": "Cannot delete doctor with pending appointments"}), 400
        
        # Delete associated time slots first
        TimeSlot.query.filter_by(doctor_id=doctor_id).delete()
        
        db.session.delete(doctor)
        db.session.commit()
        
        return jsonify({"success": True, "message": "Doctor deleted successfully"})
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Delete doctor error: {e}")
        return jsonify({"error": f"Failed to delete doctor: {str(e)}"}), 500

@bp.route("/api/doctors/<int:doctor_id>", methods=["GET"])
def get_doctor(doctor_id):
    """Get a specific doctor's details"""
    try:
        current_admin = get_current_admin()
        if not current_admin:
            return jsonify({"error": "Admin access required"}), 403
        
        doctor = User.query.filter_by(id=doctor_id, role="doctor").first()
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
                "current_hospital": doctor.current_hospital,
                "created_at": doctor.created_at.isoformat() if doctor.created_at else None
            }
        })
        
    except Exception as e:
        logging.error(f"Get doctor error: {e}")
        return jsonify({"error": f"Failed to retrieve doctor: {str(e)}"}), 500

# ============ APPOINTMENT APPROVAL MANAGEMENT ============

@bp.route("/api/appointments", methods=["GET"])
def list_appointments():
    """List appointments with filtering"""
    try:
        current_admin = get_current_admin()
        if not current_admin:
            return jsonify({"error": "Admin access required"}), 403
        
        # Get query parameters
        approval_status = request.args.get('approval_status')  # pending, approved, declined
        status = request.args.get('status')  # scheduled, completed, etc.
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        
        # Build query - join with patient and doctor users using aliases
        from sqlalchemy.orm import aliased
        
        PatientUser = aliased(User)
        DoctorUser = aliased(User) 
        
        query = Appointment.query.join(PatientUser, Appointment.user_id == PatientUser.id).join(
            DoctorUser, Appointment.doctor_id == DoctorUser.id
        )
        
        if approval_status:
            query = query.filter(Appointment.approval_status == approval_status)
        
        if status:
            query = query.filter(Appointment.status == status)
        
        total_count = query.count()
        appointments = query.order_by(Appointment.created_at.desc()).offset(offset).limit(limit).all()
        
        appointments_list = []
        for appointment in appointments:
            # Get patient and doctor info directly from the appointment relationships
            patient_name = appointment.patient.name if appointment.patient else "Unknown Patient"
            patient_email = appointment.patient.email if appointment.patient else ""
            doctor_name = appointment.doctor.name if appointment.doctor else "Unknown Doctor"
            
            appointments_list.append({
                "id": appointment.id,
                "patient_id": appointment.user_id,
                "patient_name": patient_name,
                "patient_email": patient_email,
                "doctor_id": appointment.doctor_id,
                "doctor_name": doctor_name,
                "appointment_date": appointment.appointment_date.isoformat() if appointment.appointment_date else None,
                "starts_at": appointment.starts_at.isoformat() if appointment.starts_at else None,
                "ends_at": appointment.ends_at.isoformat() if appointment.ends_at else None,
                "status": appointment.status,
                "approval_status": appointment.approval_status,
                "symptoms": appointment.symptoms,
                "note": appointment.note,
                "time_slot_id": appointment.time_slot_id,
                "approved_by": appointment.approved_by,
                "approved_at": appointment.approved_at.isoformat() if appointment.approved_at else None,
                "created_at": appointment.created_at.isoformat() if appointment.created_at else None
            })
        
        return jsonify({
            "success": True,
            "appointments": appointments_list,
            "total_count": total_count,
            "pending_count": Appointment.query.filter_by(approval_status="pending").count(),
            "approved_count": Appointment.query.filter_by(approval_status="approved").count()
        })
        
    except Exception as e:
        logging.error(f"List appointments error: {e}")
        return jsonify({"error": f"Failed to retrieve appointments: {str(e)}"}), 500

@bp.route("/api/appointments/<int:appointment_id>/approve", methods=["POST"])
def approve_appointment(appointment_id):
    """Approve a pending appointment"""
    try:
        current_admin = get_current_admin()
        if not current_admin:
            return jsonify({"error": "Admin access required"}), 403
        
        appointment = Appointment.query.get_or_404(appointment_id)
        
        if appointment.approval_status != "pending":
            return jsonify({"error": "Appointment is not pending approval"}), 400
        
        # Update appointment
        appointment.approval_status = "approved"
        appointment.status = "scheduled"
        appointment.approved_by = current_admin['admin_id']
        appointment.approved_at = datetime.utcnow()
        appointment.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        # Send fake email notifications
        patient = User.query.get(appointment.user_id)
        doctor = User.query.get(appointment.doctor_id)
        if patient and doctor:
            logging.info(f"Email sent to {patient.email}: Your appointment with {doctor.name} on {appointment.appointment_date} has been approved by admin!")
        
        return jsonify({
            "success": True,
            "message": "Appointment approved successfully",
            "appointment": {
                "id": appointment.id,
                "patient_name": appointment.patient.name if appointment.patient else "Unknown",
                "doctor_name": appointment.doctor.name if appointment.doctor else "Unknown",
                "appointment_date": appointment.appointment_date.isoformat() if appointment.appointment_date else None,
                "approval_status": appointment.approval_status
            }
        })
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Approve appointment error: {e}")
        return jsonify({"error": f"Failed to approve appointment: {str(e)}"}), 500

@bp.route("/api/appointments/<int:appointment_id>/decline", methods=["POST"])
def decline_appointment(appointment_id):
    """Decline a pending appointment"""
    try:
        current_admin = get_current_admin()
        if not current_admin:
            return jsonify({"error": "Admin access required"}), 403
        
        appointment = Appointment.query.get_or_404(appointment_id)
        
        if appointment.approval_status != "pending":
            return jsonify({"error": "Appointment is not pending approval"}), 400
        
        data = request.get_json()
        decline_reason = data.get("reason", "No reason provided") if data else "No reason provided"
        
        # Update appointment
        appointment.approval_status = "declined"
        appointment.status = "cancelled"
        appointment.approved_by = current_admin['admin_id']
        appointment.approved_at = datetime.utcnow()
        appointment.note = f"Declined by admin: {decline_reason}"
        appointment.updated_at = datetime.utcnow()
        
        # Free up the time slot if appointment was linked to one
        if appointment.time_slot_id:
            from models import TimeSlot
            slot = TimeSlot.query.get(appointment.time_slot_id)
            if slot:
                slot.is_booked = False
                slot.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        # Send fake email notifications
        patient = User.query.get(appointment.user_id)
        doctor = User.query.get(appointment.doctor_id)
        if patient and doctor:
            logging.info(f"Email sent to {patient.email}: Your appointment with {doctor.name} on {appointment.appointment_date} has been declined by admin. Reason: {decline_reason}")
        
        return jsonify({
            "success": True,
            "message": "Appointment declined successfully",
            "appointment": {
                "id": appointment.id,
                "patient_name": appointment.patient.name,
                "doctor_name": appointment.doctor.name,
                "appointment_date": appointment.appointment_date.isoformat(),
                "approval_status": appointment.approval_status
            }
        })
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Decline appointment error: {e}")
        return jsonify({"error": f"Failed to decline appointment: {str(e)}"}), 500

@bp.route("/api/appointments/<int:appointment_id>", methods=["GET"])
def get_appointment_details(appointment_id):
    """Get detailed information about a specific appointment"""
    try:
        current_admin = get_current_admin()
        if not current_admin:
            return jsonify({"error": "Admin access required"}), 403
        
        appointment = Appointment.query.get(appointment_id)
        if not appointment:
            return jsonify({"error": "Appointment not found"}), 404
        
        # Get patient and doctor details
        patient = User.query.get(appointment.user_id)
        doctor = User.query.get(appointment.doctor_id)
        time_slot = TimeSlot.query.get(appointment.time_slot_id) if appointment.time_slot_id else None
        
        appointment_details = {
            "id": appointment.id,
            "patient": {
                "id": patient.id if patient else None,
                "name": patient.name if patient else "Unknown",
                "email": patient.email if patient else "N/A",
                "phone": patient.phone if patient else "N/A"
            },
            "doctor": {
                "id": doctor.id if doctor else None,
                "name": doctor.name if doctor else "Unknown",
                "email": doctor.email if doctor else "N/A",
                "phone": doctor.phone if doctor else "N/A",
                "specialization": doctor.specialization if doctor else "N/A",
                "qualification": doctor.qualification if doctor else "N/A"
            },
            "appointment_date": appointment.appointment_date.isoformat() if appointment.appointment_date else None,
            "starts_at": appointment.starts_at.isoformat() if appointment.starts_at else None,
            "ends_at": appointment.ends_at.isoformat() if appointment.ends_at else None,
            "symptoms": appointment.symptoms,
            "note": appointment.note,
            "status": appointment.status,
            "approval_status": appointment.approval_status,
            "meet_link": appointment.google_meet_link,
            "created_at": appointment.created_at.isoformat() if appointment.created_at else None,
            "updated_at": appointment.updated_at.isoformat() if appointment.updated_at else None,
            "time_slot": {
                "starts_at": time_slot.starts_at.isoformat() if time_slot and time_slot.starts_at else None,
                "ends_at": time_slot.ends_at.isoformat() if time_slot and time_slot.ends_at else None
            } if time_slot else None
        }
        
        return jsonify({
            "success": True,
            "appointment": appointment_details
        })
        
    except Exception as e:
        logging.error(f"Get appointment details error: {e}")
        return jsonify({"error": f"Failed to retrieve appointment details: {str(e)}"}), 500

@bp.route("/api/appointments/<int:appointment_id>", methods=["DELETE"])
def cancel_appointment(appointment_id):
    """Cancel an approved appointment"""
    try:
        current_admin = get_current_admin()
        if not current_admin:
            return jsonify({"error": "Admin access required"}), 403
        
        appointment = Appointment.query.get_or_404(appointment_id)
        
        if appointment.status in ["completed", "cancelled"]:
            return jsonify({"error": "Cannot cancel a completed or already cancelled appointment"}), 400
        
        # Update appointment
        appointment.status = "cancelled"
        appointment.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Appointment cancelled successfully"
        })
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Cancel appointment error: {e}")
        return jsonify({"error": f"Failed to cancel appointment: {str(e)}"}), 500
