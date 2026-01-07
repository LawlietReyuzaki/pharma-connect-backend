from flask import Blueprint, request, jsonify
from services.auth import require_auth, get_current_user, require_role
from models import Medicine
from app import db
import logging

bp = Blueprint("store", __name__)

@bp.route("/medicines", methods=["GET"])
def list_medicines():
    """Get list of medicines with optional filtering"""
    try:
        # Get query parameters
        category = request.args.get('category')
        search = request.args.get('search')
        status = request.args.get('status', 'in_stock')
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
        
        # Sort by name ascending and apply pagination
        medicines = query.order_by(Medicine.name.asc()).offset(offset).limit(limit).all()
        
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
                "category": med.category
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

@bp.route("/medicines/<int:medicine_id>", methods=["GET"])
def get_medicine(medicine_id):
    """Get specific medicine details"""
    try:
        medicine = Medicine.query.get_or_404(medicine_id)
        
        return jsonify({
            "success": True,
            "medicine": {
                "id": medicine.id,
                "name": medicine.name,
                "chemical": medicine.chemical,
                "description": medicine.description,
                "price": medicine.price,
                "image_path": medicine.image_path or "/static/images/default-medicine.png",
                "status": medicine.status,
                "stock_quantity": medicine.stock_quantity,
                "category": medicine.category,
                "created_at": medicine.created_at.isoformat(),
                "updated_at": medicine.updated_at.isoformat()
            }
        })
        
    except Exception as e:
        logging.error(f"Get medicine error: {e}")
        return jsonify({"error": f"Failed to retrieve medicine: {str(e)}"}), 500

@bp.route("/medicines", methods=["POST"])
def add_medicine():
    """Add new medicine (admin only)"""
    try:
        current_user = get_current_user()
        if not current_user or current_user.role != "admin":
            return jsonify({"error": "Admin access required"}), 403
        
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Validate required fields
        required_fields = ["name", "price"]
        for field in required_fields:
            if not data.get(field):
                return jsonify({"error": f"{field} is required"}), 400
        
        # Create new medicine
        medicine = Medicine()
        medicine.name = data["name"]
        medicine.chemical = data.get("chemical", "")
        medicine.description = data.get("description", "")
        medicine.price = int(data["price"])
        medicine.image_path = data.get("image_path", "")
        medicine.status = data.get("status", "in_stock")
        medicine.stock_quantity = int(data.get("stock_quantity", 0))
        medicine.category = data.get("category", "General")
        
        db.session.add(medicine)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Medicine added successfully",
            "medicine": {
                "id": medicine.id,
                "name": medicine.name,
                "price": medicine.price,
                "category": medicine.category
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Add medicine error: {e}")
        return jsonify({"error": f"Failed to add medicine: {str(e)}"}), 500

@bp.route("/medicines/<int:medicine_id>", methods=["PUT"])
def update_medicine(medicine_id):
    """Update medicine (admin only)"""
    try:
        current_user = get_current_user()
        if not current_user or current_user.role != "admin":
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
        if "image_path" in data:
            medicine.image_path = data["image_path"]
        if "status" in data:
            medicine.status = data["status"]
        if "stock_quantity" in data:
            medicine.stock_quantity = int(data["stock_quantity"])
        if "category" in data:
            medicine.category = data["category"]
        
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

@bp.route("/medicines/<int:medicine_id>", methods=["DELETE"])
def delete_medicine(medicine_id):
    """Delete medicine (admin only)"""
    try:
        current_user = get_current_user()
        if not current_user or current_user.role != "admin":
            return jsonify({"error": "Admin access required"}), 403
        
        medicine = Medicine.query.get_or_404(medicine_id)
        
        # Check if medicine is in any orders
        from models import OrderItem
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

@bp.route("/categories", methods=["GET"])
def get_categories():
    """Get list of medicine categories - only returns categories with products"""
    try:
        # Get categories with product counts (only categories that have products)
        from sqlalchemy import func
        categories_with_counts = db.session.query(
            Medicine.category,
            func.count(Medicine.id).label('count')
        ).filter(
            Medicine.category.isnot(None),
            Medicine.category != "",
            Medicine.status == 'in_stock'
        ).group_by(Medicine.category).all()
        
        # Only include categories that have at least 1 product
        category_list = [cat[0] for cat in categories_with_counts if cat[0] and cat[1] > 0]
        
        # Remove duplicates (case-insensitive) - keep the first occurrence
        seen = set()
        unique_categories = []
        for cat in category_list:
            cat_lower = cat.lower().strip()
            if cat_lower not in seen:
                seen.add(cat_lower)
                unique_categories.append(cat)
        
        return jsonify({
            "success": True,
            "categories": sorted(unique_categories)
        })
        
    except Exception as e:
        logging.error(f"Get categories error: {e}")
        return jsonify({"error": f"Failed to retrieve categories: {str(e)}"}), 500

@bp.route("/search", methods=["GET"])
def search_medicines():
    """Search medicines with advanced filters"""
    try:
        query_text = request.args.get('q', '').strip()
        min_price = request.args.get('min_price', type=int)
        max_price = request.args.get('max_price', type=int)
        category = request.args.get('category')
        
        if not query_text:
            return jsonify({"error": "Search query is required"}), 400
        
        # Build search query
        query = Medicine.query.filter(Medicine.status == 'in_stock')
        
        # Text search
        search_term = f"%{query_text}%"
        query = query.filter(
            db.or_(
                Medicine.name.ilike(search_term),
                Medicine.chemical.ilike(search_term),
                Medicine.description.ilike(search_term)
            )
        )
        
        # Price range filter
        if min_price is not None:
            query = query.filter(Medicine.price >= min_price)
        if max_price is not None:
            query = query.filter(Medicine.price <= max_price)
        
        # Category filter
        if category:
            query = query.filter(Medicine.category == category)
        
        medicines = query.order_by(Medicine.name.asc()).limit(20).all()
        
        # Format results
        results = []
        for med in medicines:
            results.append({
                "id": med.id,
                "name": med.name,
                "chemical": med.chemical,
                "price": med.price,
                "category": med.category,
                "image_path": med.image_path or "/static/images/default-medicine.png"
            })
        
        return jsonify({
            "success": True,
            "query": query_text,
            "results": results,
            "count": len(results)
        })
        
    except Exception as e:
        logging.error(f"Search medicines error: {e}")
        return jsonify({"error": f"Search failed: {str(e)}"}), 500
