import os
import logging
from functools import wraps
from flask import Flask, render_template, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.exc import SQLAlchemyError, OperationalError
from werkzeug.middleware.proxy_fix import ProxyFix

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

# Initialize extensions
db = SQLAlchemy(model_class=Base)

def create_app():
    # Create Flask app
    app = Flask(__name__, static_folder="static", template_folder="templates")
    
    # Configuration
    app.secret_key = os.environ.get("SESSION_SECRET", "red-dot-pharmacy-secret-key")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///red_dot_pharmacy.db")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }
    
    # WSGI proxy fix for proper URL generation
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
    
    # Initialize extensions
    db.init_app(app)
    CORS(app)
    
    # Register blueprints
    from routes.auth_routes import bp as auth_bp
    from routes.chatbot_routes import bp as chatbot_bp
    from routes.appointment_routes import bp as appt_bp
    from routes.store_routes import bp as store_bp
    from routes.order_routes import bp as order_bp
    from routes.admin_routes import bp as admin_bp
    from routes.admin_auth_routes import bp as admin_auth_bp
    from routes.doctor_routes import bp as doctor_bp
    from routes.google_auth_routes import bp as google_auth_bp
    from routes.doctor_oauth_routes import bp as doctor_oauth_bp
    from routes.payment_routes import bp as payment_bp
    
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(chatbot_bp, url_prefix="/api/chat")
    app.register_blueprint(appt_bp, url_prefix="/api/appointments")
    app.register_blueprint(store_bp, url_prefix="/api/store")
    app.register_blueprint(order_bp, url_prefix="/api/orders")
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(admin_auth_bp, url_prefix="/admin/auth")
    app.register_blueprint(doctor_bp, url_prefix="/doctor")
    app.register_blueprint(google_auth_bp)
    app.register_blueprint(doctor_oauth_bp)
    app.register_blueprint(payment_bp, url_prefix="/api/payments")
    
    @app.route("/")
    def index():
        return render_template("index.html")
    
    @app.route("/admin")
    def admin_dashboard():
        return render_template("admin.html")
    
    @app.route("/video")
    def video_room():
        return render_template("video.html")
    
    @app.route("/shop")
    def shop():
        return render_template("shop.html")
    
    @app.route("/consultation")
    def consultation():
        return render_template("consultation.html")
    
    @app.route("/appointments")
    def appointments():
        return render_template("appointments.html")
    
    @app.route("/assistant")
    def assistant():
        return render_template("assistant.html")
    
    @app.errorhandler(403)
    def forbidden(error):
        return render_template("403.html"), 403
    
    @app.errorhandler(404)
    def not_found(error):
        return render_template("403.html"), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return render_template("403.html"), 500
    
    return app

# Create app instance
app = create_app()

# Lazy database initialization with retry logic
db_initialized = False

def initialize_database():
    """Initialize database tables with error handling and retry logic"""
    global db_initialized
    if db_initialized:
        return True
    
    try:
        with app.app_context():
            import models  # noqa: F401
            db.create_all()
            db_initialized = True
            logging.info("✅ Database tables created successfully for Red Dot Pharmacy")
            return True
    except Exception as e:
        logging.warning(f"⚠️ Database initialization failed (will retry on next request): {e}")
        return False

# Try to initialize database at startup, but don't fail if it doesn't work
initialize_database()

@app.before_request
def ensure_database():
    """Ensure database is initialized before handling requests"""
    if not db_initialized:
        initialize_database()

# Global database error handler
@app.errorhandler(OperationalError)
@app.errorhandler(SQLAlchemyError)
def handle_database_error(error):
    """Handle all database-related errors gracefully"""
    logging.error(f"Database error occurred: {error}")
    return jsonify({
        "error": "Database temporarily unavailable",
        "message": "Our database is currently offline. Please try again in a few moments.",
        "status": 503
    }), 503

# Decorator for database-dependent routes
def handle_db_errors(f):
    """Decorator to catch database errors and return graceful responses"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except (OperationalError, SQLAlchemyError) as e:
            logging.error(f"Database error in {f.__name__}: {e}")
            return jsonify({
                "error": "Database temporarily unavailable",
                "message": "The database is currently unavailable. Please try again shortly.",
                "status": 503
            }), 503
    return decorated_function
