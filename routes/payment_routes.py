from flask import Blueprint, request, jsonify
from datetime import datetime
from services.auth import require_auth, get_current_user
from models import PaymentMethod, Order
from app import db
import logging
import os
from werkzeug.utils import secure_filename

bp = Blueprint("payments", __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
UPLOAD_FOLDER = 'static/uploads/receipts'

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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
            return jsonify({"error": "Invalid file type. Only PNG, JPG, JPEG allowed"}), 400
        
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
                "account_details": None
            },
            {
                "name": "EasyPaisa",
                "slug": "easypaisa",
                "logo_path": "/static/images/payment-logos/easypaisa.png",
                "is_active": True,
                "requires_receipt": True,
                "display_order": 2,
                "account_details": "Account: 0300-XXXXXXX"
            },
            {
                "name": "JazzCash",
                "slug": "jazzcash",
                "logo_path": "/static/images/payment-logos/jazzcash.jpg",
                "is_active": True,
                "requires_receipt": True,
                "display_order": 3,
                "account_details": "Account: 0300-XXXXXXX"
            },
            {
                "name": "Meezan Bank",
                "slug": "meezan_bank",
                "logo_path": "/static/images/payment-logos/meezan-bank.png",
                "is_active": True,
                "requires_receipt": True,
                "display_order": 4,
                "account_details": "Account: XXXXXXXXXX"
            },
            {
                "name": "NayaPay",
                "slug": "nayapay",
                "logo_path": "/static/images/payment-logos/nayapay.jpg",
                "is_active": True,
                "requires_receipt": True,
                "display_order": 5,
                "account_details": "Account: XXXXXXXXXX"
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
