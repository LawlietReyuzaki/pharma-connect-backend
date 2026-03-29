"""
Frontend Server Startup Script
Runs the frontend HTTP server on port 3000
Backend should be started separately using: python run_backend.py
"""
import os
import sys
import http.server
import socketserver
from pathlib import Path

FRONTEND_PORT = 3000
BACKEND_PORT = 5000
HOST = "0.0.0.0"

class FrontendHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory="static", **kwargs)
    
    def log_message(self, format, *args):
        print(f"[Frontend] {format % args}")

def print_banner():
    """Print startup banner with instructions"""
    print("\n" + "="*70)
    print("🎨 FRONTEND SERVER STARTING")
    print("="*70)
    print(f"📍 Frontend running on http://localhost:{FRONTEND_PORT}")
    print(f"   Public access: http://0.0.0.0:{FRONTEND_PORT}")
    print("="*70)
    print("\n⚠️  IMPORTANT: The Backend must be started separately!")
    print("\n📝 In a NEW TERMINAL, run:")
    print("   python run_backend.py")
    print(f"\n🔗 Backend will run on http://localhost:{BACKEND_PORT}")
    print("\n✅ Once both servers are running:")
    print(f"   - Frontend: http://localhost:{FRONTEND_PORT}")
    print(f"   - Backend API: http://localhost:{BACKEND_PORT}/api")
    print("="*70 + "\n")

if __name__ == "__main__":
    # Verify static folder exists
    static_path = Path("static")
    if not static_path.exists():
        print("❌ Error: 'static' folder not found!")
        print(f"Current directory: {os.getcwd()}")
        sys.exit(1)
    
    print_banner()
    
    try:
        with socketserver.TCPServer((HOST, FRONTEND_PORT), FrontendHandler) as httpd:
            print(f"✅ Frontend server is running...")
            print(f"🎯 Press CTRL+C to stop the server\n")
            httpd.serve_forever()
    except OSError as e:
        if e.errno == 48 or e.errno == 98:  # Port already in use
            print(f"❌ Port {FRONTEND_PORT} is already in use!")
            print(f"   Try: netstat -ano | findstr :{FRONTEND_PORT}")
        else:
            print(f"❌ Error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n👋 Frontend server stopped.")
        sys.exit(0)
