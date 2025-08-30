from flask import Blueprint, request, jsonify, render_template
from datetime import datetime, timedelta
from services.auth import require_auth, get_current_user, require_role
from models import User, Medicine, Appointment, Order, OrderItem, ChatLog
from app import db
import logging
import hashlib

bp = Blueprint("admin", __name__)

def phash(pw):
    """Hash password using SHA256"""
    return hashlib.sha256(pw.encode()).hexdigest()

@bp.route("/dashboard")
def admin_dashboard():
    """Render admin dashboard page"""
    return render_template("admin.html")

@bp.route("/api/stats", methods=["GET"])
def get_dashboard_stats():
    """Get comprehensive dashboard statistics"""
    try:
        current_user = get_current_user()
        if not current_user or current_user.role != "admin":
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
        current_user = get_current_user()
        if not current_user or current_user.role != "admin":
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
        current_user = get_current_user()
        if not current_user or current_user.role != "admin":
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
        current_user = get_current_user()
        if not current_user or current_user.role != "admin":
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
        current_user = get_current_user()
        if not current_user or current_user.role != "admin":
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
        current_user = get_current_user()
        if not current_user or current_user.role != "admin":
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
        current_user = get_current_user()
        if not current_user or current_user.role != "admin":
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
