"""
Flask Backend Server Startup Script
Runs the Flask API server on port 5000
"""
import os
from app import create_app

if __name__ == "__main__":
    app = create_app()
    port = int(os.environ.get("PORT", 5000))
    host = os.environ.get("HOST", "0.0.0.0")
    debug = os.environ.get("FLASK_ENV") == "development"
    
    print("\n" + "="*60)
    print("🚀 Starting Flask Backend Server")
    print("="*60)
    print(f"📍 Backend running on http://{host}:{port}")
    print(f"🔧 Debug mode: {debug}")
    print("="*60 + "\n")
    
    app.run(host=host, port=port, debug=debug)
