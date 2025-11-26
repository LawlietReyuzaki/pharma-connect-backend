from flask import Blueprint, request, jsonify
from datetime import datetime
from services.auth import require_auth, get_current_user
from models import PaymentMethod, Order
from app import db
import logging
import os
from werkzeug.utils import secure_filename

bp = Blueprint("payments", __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}
UPLOAD_FOLDER = 'static/uploads/receipts'
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def check_file_size(file):
    """Check if file size is within limit"""
    file.seek(0, 2)  # Seek to end
    size = file.tell()
    file.seek(0)  # Reset to beginning
    return size <= MAX_FILE_SIZE

def ensure_upload_folder():
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

@bp.route("/methods", methods=["GET"])
def get_payment_methods():
    """Get all active payment methods for customers"""
    try:
        methods = PaymentMethod.query.filter_by(is_active=True).order_by(PaymentMethod.display_order).all()
        
        return jsonify({
            "success": True,
            "payment_methods": [{
                "id": m.id,
                "name": m.name,
                "slug": m.slug,
                "logo_path": m.logo_path,
                "requires_receipt": m.requires_receipt,
                "account_title": m.account_title,
                "account_number": m.account_number,
                "account_details": m.account_details
            } for m in methods]
        })
    except Exception as e:
        logging.error(f"Get payment methods error: {e}")
        return jsonify({"error": "Failed to get payment methods"}), 500

@bp.route("/upload-receipt", methods=["POST"])
def upload_receipt():
    """Upload payment receipt image"""
    try:
        current_user = get_current_user()
        if not current_user:
            return jsonify({"error": "Authentication required"}), 401
        
        if 'receipt' not in request.files:
            return jsonify({"error": "No receipt file provided"}), 400
        
        file = request.files['receipt']
        
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        if not allowed_file(file.filename):
            return jsonify({"error": "Invalid file type. Only PNG, JPG, JPEG, PDF allowed"}), 400
        
        if not check_file_size(file):
            return jsonify({"error": "File too large. Maximum size is 5MB"}), 400
        
        ensure_upload_folder()
        
        original_filename = file.filename if file.filename else "receipt"
        filename = secure_filename(original_filename)
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        unique_filename = f"receipt_{current_user.id}_{timestamp}_{filename}"
        filepath = os.path.join(UPLOAD_FOLDER, unique_filename)
        
        file.save(filepath)
        
        relative_path = f"/{filepath}"
        
        return jsonify({
            "success": True,
            "message": "Receipt uploaded successfully",
            "receipt_path": relative_path
        })
        
    except Exception as e:
        logging.error(f"Upload receipt error: {e}")
        return jsonify({"error": f"Failed to upload receipt: {str(e)}"}), 500

@bp.route("/reupload-receipt/<int:order_id>", methods=["POST"])
def reupload_receipt(order_id):
    """Re-upload receipt for a rejected payment"""
    try:
        current_user = get_current_user()
        if not current_user:
            return jsonify({"error": "Authentication required"}), 401
        
        order = Order.query.get_or_404(order_id)
        
        # Check if order belongs to current user
        if order.user_id != current_user.id:
            return jsonify({"error": "Unauthorized"}), 403
        
        # Check if order payment was declined
        if order.payment_status not in ['declined', 'pending']:
            return jsonify({"error": "Receipt can only be re-uploaded for declined or pending payments"}), 400
        
        if 'receipt' not in request.files:
            return jsonify({"error": "No receipt file provided"}), 400
        
        file = request.files['receipt']
        
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        if not allowed_file(file.filename):
            return jsonify({"error": "Invalid file type. Only PNG, JPG, JPEG, PDF allowed"}), 400
        
        if not check_file_size(file):
            return jsonify({"error": "File too large. Maximum size is 5MB"}), 400
        
        ensure_upload_folder()
        
        original_filename = file.filename if file.filename else "receipt"
        filename = secure_filename(original_filename)
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        unique_filename = f"receipt_{current_user.id}_{order_id}_{timestamp}_{filename}"
        filepath = os.path.join(UPLOAD_FOLDER, unique_filename)
        
        file.save(filepath)
        
        # Update order with new receipt
        order.payment_receipt_path = f"/{filepath}"
        order.receipt_uploaded_at = datetime.utcnow()
        order.payment_status = "pending"  # Reset to pending for re-review
        order.payment_rejection_reason = None  # Clear rejection reason
        
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Receipt re-uploaded successfully. Your payment will be reviewed.",
            "receipt_path": f"/{filepath}"
        })
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Re-upload receipt error: {e}")
        return jsonify({"error": f"Failed to re-upload receipt: {str(e)}"}), 500

@bp.route("/init-methods", methods=["POST"])
def init_payment_methods():
    """Initialize default payment methods (one-time setup)"""
    try:
        existing = PaymentMethod.query.first()
        if existing:
            return jsonify({"message": "Payment methods already initialized"}), 200
        
        default_methods = [
            {
                "name": "Cash on Delivery",
                "slug": "cash_on_delivery",
                "logo_path": "/static/images/payment-logos/cash-on-delivery.svg",
                "is_active": True,
                "requires_receipt": False,
                "display_order": 1,
                "account_title": None,
                "account_number": None,
                "account_details": "Pay in cash when your order is delivered"
            },
            {
                "name": "EasyPaisa",
                "slug": "easypaisa",
                "logo_path": "/static/images/payment-logos/easypaisa.png",
                "is_active": True,
                "requires_receipt": True,
                "display_order": 2,
                "account_title": "Red Dot Pharmacy",
                "account_number": "0300-XXXXXXX",
                "account_details": "Send payment via EasyPaisa app and upload receipt"
            },
            {
                "name": "JazzCash",
                "slug": "jazzcash",
                "logo_path": "/static/images/payment-logos/jazzcash.jpg",
                "is_active": True,
                "requires_receipt": True,
                "display_order": 3,
                "account_title": "Red Dot Pharmacy",
                "account_number": "0300-XXXXXXX",
                "account_details": "Send payment via JazzCash app and upload receipt"
            },
            {
                "name": "Meezan Bank",
                "slug": "meezan_bank",
                "logo_path": "/static/images/payment-logos/meezan-bank.png",
                "is_active": True,
                "requires_receipt": True,
                "display_order": 4,
                "account_title": "Red Dot Pharmacy",
                "account_number": "PK00MEZN0000000000000000",
                "account_details": "Transfer via bank app and upload receipt"
            },
            {
                "name": "NayaPay",
                "slug": "nayapay",
                "logo_path": "/static/images/payment-logos/nayapay.jpg",
                "is_active": True,
                "requires_receipt": True,
                "display_order": 5,
                "account_title": "Red Dot Pharmacy",
                "account_number": "0300-XXXXXXX",
                "account_details": "Send payment via NayaPay and upload receipt"
            }
        ]
        
        for method_data in default_methods:
            method = PaymentMethod()
            method.name = method_data["name"]
            method.slug = method_data["slug"]
            method.logo_path = method_data["logo_path"]
            method.is_active = method_data["is_active"]
            method.requires_receipt = method_data["requires_receipt"]
            method.display_order = method_data["display_order"]
            method.account_title = method_data["account_title"]
            method.account_number = method_data["account_number"]
            method.account_details = method_data["account_details"]
            db.session.add(method)
        
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Payment methods initialized successfully"
        })
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Init payment methods error: {e}")
        return jsonify({"error": f"Failed to initialize payment methods: {str(e)}"}), 500
