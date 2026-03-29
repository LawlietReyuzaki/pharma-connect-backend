# Running Backend and Frontend Separately

## Prerequisites
Make sure all dependencies are installed:
```bash
pip install -r requirements.txt
```

## 1️⃣ Start Flask Backend Server

Open a terminal and run:
```bash
python run_backend.py
```

**Expected output:**
```
============================================================
🚀 Starting Flask Backend Server
============================================================
📍 Backend running on http://0.0.0.0:5000
🔧 Debug mode: True
============================================================
```

✅ Backend will be available at: **http://localhost:5000**

---

## 2️⃣ Start Frontend Server

Open a **second terminal** (keep the first one running) and run:

### Option A: Using Python's built-in server
```bash
cd static
python -m http.server 3000
```

### Option B: Using Node.js (if you have it installed)
```bash
cd pharmaflow-react
npm install
npm start
```

✅ Frontend will be available at: **http://localhost:3000**

---

## 📝 Terminal Setup

You should have **2 terminals open**:

| Terminal 1 | Terminal 2 |
|-----------|-----------|
| Backend (Port 5000) | Frontend (Port 3000) |
| `python run_backend.py` | `python -m http.server 3000` |
| ✅ Running | ✅ Running |

---

## 🔗 API Communication

- Frontend runs on: `http://localhost:3000`
- Backend API runs on: `http://localhost:5000`
- API calls will use: `http://localhost:5000/api/*`

---

## ⚠️ Troubleshooting

### Backend won't start?
- Check if port 5000 is available: `netstat -ano | findstr :5000`
- Check if dependencies are installed: `pip install -r requirements.txt`

### Frontend won't start?
- Check if port 3000 is available: `netstat -ano | findstr :3000`
- Ensure you're in the correct directory

### Port already in use?
Change the port when starting:
```bash
# Backend on different port
set PORT=5001
python run_backend.py

# Frontend on different port
python -m http.server 3001
```

