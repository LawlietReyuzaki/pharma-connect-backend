import os
import logging
from flask import Flask, render_template
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
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
    
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(chatbot_bp, url_prefix="/api/chat")
    app.register_blueprint(appt_bp, url_prefix="/api/appointments")
    app.register_blueprint(store_bp, url_prefix="/api/store")
    app.register_blueprint(order_bp, url_prefix="/api/orders")
    app.register_blueprint(admin_bp, url_prefix="/admin")
    
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

# Create tables
with app.app_context():
    import models  # noqa: F401
    db.create_all()
    logging.info("Database tables created for Red Dot Pharmacy")
