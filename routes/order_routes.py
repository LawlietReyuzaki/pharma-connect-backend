from flask import Blueprint, request, jsonify
from datetime import datetime
from services.auth import require_auth, get_current_user
from models import Order, OrderItem, Medicine, User
from app import db
import logging

bp = Blueprint("orders", __name__)

@bp.route("/", methods=["POST"])
def create_order():
    """Create a new order"""
    try:
        current_user = get_current_user()
        if not current_user:
            return jsonify({"error": "Authentication required"}), 401
        
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Validate required fields
        required_fields = ["address", "phone", "items"]
        for field in required_fields:
            if not data.get(field):
                return jsonify({"error": f"{field} is required"}), 400
        
        if not isinstance(data["items"], list) or len(data["items"]) == 0:
            return jsonify({"error": "At least one item is required"}), 400
        
        # Validate and calculate total
        total_amount = 0
        validated_items = []
        
        for item in data["items"]:
            if not all(k in item for k in ["medicine_id", "quantity"]):
                return jsonify({"error": "Each item must have medicine_id and quantity"}), 400
            
            medicine = Medicine.query.get(item["medicine_id"])
            if not medicine:
                return jsonify({"error": f"Medicine with ID {item['medicine_id']} not found"}), 404
            
            if medicine.status != "in_stock":
                return jsonify({"error": f"{medicine.name} is currently out of stock"}), 400
            
            quantity = int(item["quantity"])
            if quantity <= 0:
                return jsonify({"error": "Quantity must be positive"}), 400
            
            if medicine.stock_quantity < quantity:
                return jsonify({"error": f"Insufficient stock for {medicine.name}. Available: {medicine.stock_quantity}"}), 400
            
            item_total = medicine.price * quantity
            total_amount += item_total
            
            validated_items.append({
                "medicine_id": medicine.id,
                "medicine_name": medicine.name,
                "quantity": quantity,
                "price_each": medicine.price,
                "total": item_total
            })
        
        # Add delivery fee
        delivery_fee = int(data.get("delivery_fee", 100))  # Default 100 PKR
        final_total = total_amount + delivery_fee
        
        # Create order
        order = Order()
        order.user_id = current_user.id
        order.address = data["address"]
        order.phone = data["phone"]
        order.total_amount = final_total
        order.delivery_fee = delivery_fee
        order.payment_method = data.get("payment_method", "cash_on_delivery")
        order.notes = data.get("notes", "")
        
        # Handle payment receipt for online payments
        payment_receipt = data.get("payment_receipt_path")
        if order.payment_method == "cash_on_delivery":
            # COD orders are confirmed immediately
            order.status = "confirmed"
            order.payment_status = "accepted"  # No payment needed upfront
        elif payment_receipt:
            # Online payment with receipt - pending admin approval
            order.payment_receipt_path = payment_receipt
            order.receipt_uploaded_at = datetime.utcnow()
            order.status = "pending"  # Pending until payment approved
            order.payment_status = "pending"  # Waiting for admin review
        else:
            # Online payment without receipt (shouldn't happen normally)
            order.status = "pending"
            order.payment_status = "pending"
        
        db.session.add(order)
        db.session.flush()  # Get order ID
        
        # Create order items and update stock
        for item_data in validated_items:
            order_item = OrderItem()
            order_item.order_id = order.id
            order_item.medicine_id = item_data["medicine_id"]
            order_item.qty = item_data["quantity"]
            order_item.price_each = item_data["price_each"]
            db.session.add(order_item)
            
            # Update medicine stock
            medicine = Medicine.query.get(item_data["medicine_id"])
            if medicine:
                medicine.stock_quantity -= item_data["quantity"]
                
                # Mark as out of stock if needed
                if medicine.stock_quantity <= 0:
                    medicine.status = "out_of_stock"
        
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Order created successfully",
            "order": {
                "id": order.id,
                "total_amount": order.total_amount,
                "delivery_fee": order.delivery_fee,
                "status": order.status,
                "items": validated_items,
                "estimated_delivery": "2-3 business days"
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Create order error: {e}")
        return jsonify({"error": f"Failed to create order: {str(e)}"}), 500

@bp.route("/", methods=["GET"])
def list_orders():
    """List orders for current user or all orders for admin"""
    try:
        current_user = get_current_user()
        if not current_user:
            return jsonify({"error": "Authentication required"}), 401
        
        # Get query parameters
        status = request.args.get('status')
        limit = int(request.args.get('limit', 20))
        offset = int(request.args.get('offset', 0))
        
        # Build query based on user role
        if current_user.role == "admin":
            query = Order.query
        else:
            query = Order.query.filter_by(user_id=current_user.id)
        
        # Apply status filter
        if status:
            query = query.filter_by(status=status)
        
        # Get total count
        total_count = query.count()
        
        # Apply pagination and ordering
        orders = query.order_by(Order.created_at.desc()).offset(offset).limit(limit).all()
        
        # Format response
        order_list = []
        for order in orders:
            # Get customer info (for admin view)
            customer = User.query.get(order.user_id) if current_user.role == "admin" else current_user
            
            # Get order items
            items = []
            for item in order.items:
                items.append({
                    "medicine_name": item.medicine.name,
                    "quantity": item.qty,
                    "price_each": item.price_each,
                    "total": item.qty * item.price_each
                })
            
            order_list.append({
                "id": order.id,
                "customer_name": customer.name if customer else "Unknown",
                "customer_phone": order.phone,
                "address": order.address,
                "total_amount": order.total_amount,
                "delivery_fee": order.delivery_fee,
                "status": order.status,
                "payment_method": order.payment_method,
                "payment_status": order.payment_status,
                "payment_receipt_path": order.payment_receipt_path,
                "payment_rejection_reason": order.payment_rejection_reason,
                "receipt_uploaded_at": order.receipt_uploaded_at.isoformat() if order.receipt_uploaded_at else None,
                "items": items,
                "item_count": len(items),
                "created_at": order.created_at.isoformat(),
                "notes": order.notes
            })
        
        return jsonify({
            "success": True,
            "orders": order_list,
            "total_count": total_count,
            "offset": offset,
            "limit": limit
        })
        
    except Exception as e:
        logging.error(f"List orders error: {e}")
        return jsonify({"error": f"Failed to retrieve orders: {str(e)}"}), 500

@bp.route("/<int:order_id>", methods=["GET"])
def get_order(order_id):
    """Get specific order details"""
    try:
        current_user = get_current_user()
        if not current_user:
            return jsonify({"error": "Authentication required"}), 401
        
        order = Order.query.get_or_404(order_id)
        
        # Check permissions
        if current_user.role != "admin" and order.user_id != current_user.id:
            return jsonify({"error": "Access denied"}), 403
        
        # Get customer info
        customer = User.query.get(order.user_id)
        
        # Get order items with medicine details
        items = []
        for item in order.items:
            items.append({
                "id": item.id,
                "medicine": {
                    "id": item.medicine.id,
                    "name": item.medicine.name,
                    "chemical": item.medicine.chemical,
                    "image_path": item.medicine.image_path or '/static/images/default-medicine.png'
                },
                "quantity": item.qty,
                "price_each": item.price_each,
                "total": item.qty * item.price_each
            })
        
        return jsonify({
            "success": True,
            "order": {
                "id": order.id,
                "customer": {
                    "name": customer.name if customer else "Unknown",
                    "email": customer.email if customer else "",
                    "phone": order.phone
                },
                "address": order.address,
                "total_amount": order.total_amount,
                "delivery_fee": order.delivery_fee,
                "status": order.status,
                "payment_method": order.payment_method,
                "payment_status": order.payment_status,
                "payment_receipt_path": order.payment_receipt_path,
                "payment_rejection_reason": order.payment_rejection_reason,
                "receipt_uploaded_at": order.receipt_uploaded_at.isoformat() if order.receipt_uploaded_at else None,
                "notes": order.notes,
                "items": items,
                "created_at": order.created_at.isoformat(),
                "updated_at": order.updated_at.isoformat()
            }
        })
        
    except Exception as e:
        logging.error(f"Get order error: {e}")
        return jsonify({"error": f"Failed to retrieve order: {str(e)}"}), 500

@bp.route("/<int:order_id>/status", methods=["PUT"])
def update_order_status(order_id):
    """Update order status (admin only)"""
    try:
        current_user = get_current_user()
        if not current_user or current_user.role != "admin":
            return jsonify({"error": "Admin access required"}), 403
        
        data = request.get_json()
        if not data or "status" not in data:
            return jsonify({"error": "Status is required"}), 400
        
        order = Order.query.get_or_404(order_id)
        
        # Validate status
        valid_statuses = ["pending", "processing", "out_for_delivery", "delivered", "cancelled"]
        if data["status"] not in valid_statuses:
            return jsonify({"error": "Invalid status"}), 400
        
        old_status = order.status
        order.status = data["status"]
        
        # Add notes if provided
        if "notes" in data:
            if order.notes:
                order.notes += f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M')}] {data['notes']}"
            else:
                order.notes = f"[{datetime.now().strftime('%Y-%m-%d %H:%M')}] {data['notes']}"
        
        # Handle cancellation - restore stock
        if data["status"] == "cancelled" and old_status != "cancelled":
            for item in order.items:
                medicine = Medicine.query.get(item.medicine_id)
                if medicine:
                    medicine.stock_quantity += item.qty
                    if medicine.status == "out_of_stock" and medicine.stock_quantity > 0:
                        medicine.status = "in_stock"
        
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": f"Order status updated to {data['status']}",
            "order": {
                "id": order.id,
                "status": order.status,
                "notes": order.notes
            }
        })
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Update order status error: {e}")
        return jsonify({"error": f"Failed to update order status: {str(e)}"}), 500

@bp.route("/stats", methods=["GET"])
def get_order_stats():
    """Get order statistics (admin only)"""
    try:
        current_user = get_current_user()
        if not current_user or current_user.role != "admin":
            return jsonify({"error": "Admin access required"}), 403
        
        # Get various statistics
        total_orders = Order.query.count()
        pending_orders = Order.query.filter_by(status="pending").count()
        processing_orders = Order.query.filter_by(status="processing").count()
        delivered_orders = Order.query.filter_by(status="delivered").count()
        
        # Calculate total revenue (delivered orders only)
        total_revenue = db.session.query(db.func.sum(Order.total_amount))\
                                 .filter_by(status="delivered").scalar() or 0
        
        # Get recent orders
        recent_orders = Order.query.order_by(Order.created_at.desc()).limit(5).all()
        
        recent_order_list = []
        for order in recent_orders:
            customer = User.query.get(order.user_id)
            recent_order_list.append({
                "id": order.id,
                "customer_name": customer.name if customer else "Unknown",
                "total_amount": order.total_amount,
                "status": order.status,
                "created_at": order.created_at.isoformat()
            })
        
        return jsonify({
            "success": True,
            "stats": {
                "total_orders": total_orders,
                "pending_orders": pending_orders,
                "processing_orders": processing_orders,
                "delivered_orders": delivered_orders,
                "total_revenue": total_revenue,
                "recent_orders": recent_order_list
            }
        })
        
    except Exception as e:
        logging.error(f"Get order stats error: {e}")
        return jsonify({"error": f"Failed to retrieve order statistics: {str(e)}"}), 500

@bp.route("/cart/calculate", methods=["POST"])
def calculate_cart():
    """Calculate cart total without creating order"""
    try:
        data = request.get_json()
        if not data or "items" not in data:
            return jsonify({"error": "Items are required"}), 400
        
        if not isinstance(data["items"], list):
            return jsonify({"error": "Items must be an array"}), 400
        
        total_amount = 0
        calculated_items = []
        
        for item in data["items"]:
            if not all(k in item for k in ["medicine_id", "quantity"]):
                return jsonify({"error": "Each item must have medicine_id and quantity"}), 400
            
            medicine = Medicine.query.get(item["medicine_id"])
            if not medicine:
                continue  # Skip invalid medicines
            
            quantity = int(item["quantity"])
            if quantity <= 0:
                continue  # Skip invalid quantities
            
            item_total = medicine.price * quantity
            total_amount += item_total
            
            calculated_items.append({
                "medicine_id": medicine.id,
                "medicine_name": medicine.name,
                "price_each": medicine.price,
                "quantity": quantity,
                "total": item_total,
                "available": medicine.status == "in_stock",
                "stock_available": medicine.stock_quantity >= quantity
            })
        
        delivery_fee = int(data.get("delivery_fee", 100))
        final_total = total_amount + delivery_fee
        
        return jsonify({
            "success": True,
            "calculation": {
                "items": calculated_items,
                "subtotal": total_amount,
                "delivery_fee": delivery_fee,
                "total": final_total,
                "item_count": len(calculated_items)
            }
        })
        
    except Exception as e:
        logging.error(f"Calculate cart error: {e}")
        return jsonify({"error": f"Failed to calculate cart: {str(e)}"}), 500
