# 🖥️ Manual Terminal Commands Guide

Complete guide for running the NBA Personalization Platform using terminal commands.

---

## 📥 FIRST TIME SETUP (Run Once)

### Step 1: Clone the Repository
```bash
git clone https://github.com/Revathi031187/NBA.git
cd NBA
```

### Step 2: Install Python Dependencies

**Windows (Command Prompt or PowerShell):**
```cmd
py -3.10 -m pip install -r requirements.txt
```

**Linux/Mac (Terminal):**
```bash
python3.10 -m pip install -r requirements.txt
```

**Alternative (if Python 3.10 is your default):**
```bash
pip install -r requirements.txt
```

---

### Step 3: Install Frontend Dependencies
```bash
cd frontend
npm install
cd ..
```

---

### Step 4: Initialize ChromaDB Database

**Windows:**
```cmd
py -3.10 scripts\initialize_chromadb.py
```

**Linux/Mac:**
```bash
python3.10 scripts/initialize_chromadb.py
```

**Expected Output:**
```
Loading banking data...
✅ Loaded X banking customers
✅ Loaded X banking products
✅ Loaded X banking transactions
Loading retail data...
✅ Loaded X retail customers
✅ Loaded X retail products
✅ Loaded X retail transactions
ChromaDB initialized successfully!
```

⏱️ **Time Required:** ~2-3 minutes

---

## 🚀 RUNNING THE APPLICATION (Every Time)

You need **TWO separate terminal windows/tabs** running simultaneously.

### Terminal 1: Backend Server

**Open first terminal in project root:**

**Windows:**
```cmd
py -3.10 api\main_unified_chromadb.py
```

**Linux/Mac:**
```bash
python3.10 api/main_unified_chromadb.py
```

**Expected Output:**
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8002
```

✅ **Keep this terminal running!** Backend is at `http://localhost:8002`

---

### Terminal 2: Frontend Server

**Open second terminal in project root:**

```bash
cd frontend
npm run dev
```

**Expected Output:**
```
  VITE v5.0.11  ready in 500 ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
  ➜  press h to show help
```

✅ **Keep this terminal running!** Frontend is at `http://localhost:5173`

---

## 🌐 ACCESS THE APPLICATION

Open your browser and navigate to:
```
http://localhost:5173
```

You should see:
- 🏦 Banking Dashboard
- 🛒 Retail Dashboard
- 📊 Analytics & Visualizations

---

## 🧪 VERIFICATION COMMANDS

### Check if Backend is Running:
```bash
curl http://localhost:8002/api/chromadb/stats
```

Or open in browser: `http://localhost:8002/docs` (FastAPI Swagger UI)

### Check if Frontend is Running:
```bash
curl http://localhost:5173
```

Or open in browser: `http://localhost:5173`

### Test API Endpoints:
```bash
# Get ChromaDB collections
curl http://localhost:8002/api/chromadb/collections

# Get banking customers
curl http://localhost:8002/api/banking/customers

# Get retail customers
curl http://localhost:8002/api/retail/customers
```

---

## 🛑 STOPPING THE APPLICATION

### Standard Method:
Press `Ctrl + C` in each terminal window

### Force Kill Processes:

**Windows:**
```cmd
# Kill backend (Python)
taskkill /F /IM python.exe

# Kill frontend (Node)
taskkill /F /IM node.exe
```

**Linux/Mac:**
```bash
# Find and kill by port
lsof -ti:8002 | xargs kill -9  # Backend
lsof -ti:5173 | xargs kill -9  # Frontend

# Or by process name
pkill -f "python.*main_unified_chromadb"
pkill -f "vite"
```

---

## 🔄 RESTARTING THE APPLICATION

1. Stop both servers (`Ctrl + C` in each terminal)
2. Start backend in Terminal 1
3. Start frontend in Terminal 2
4. Refresh browser at `http://localhost:5173`

---

## 📝 USEFUL DEVELOPMENT COMMANDS

### Backend - With Auto-Reload (Development Mode)
```bash
# Windows
py -3.10 -m uvicorn api.main_unified_chromadb:app --reload --port 8002

# Linux/Mac
python3.10 -m uvicorn api.main_unified_chromadb:app --reload --port 8002
```

### Frontend - Build for Production
```bash
cd frontend
npm run build          # Build production bundle
npm run preview        # Preview production build locally
```

### Check API Documentation
- **Swagger UI:** `http://localhost:8002/docs`
- **ReDoc:** `http://localhost:8002/redoc`

### View Backend Logs
```bash
# Backend logs to console output
# To redirect to file:
py -3.10 api\main_unified_chromadb.py > backend.log 2>&1
```

---

## 🔧 DATABASE MANAGEMENT

### Clear ChromaDB and Reinitialize

**Windows:**
```cmd
rmdir /s /q chroma_db
py -3.10 scripts\initialize_chromadb.py
```

**Linux/Mac:**
```bash
rm -rf chroma_db
python3.10 scripts/initialize_chromadb.py
```

### Check ChromaDB Collections

Open Python interactive shell:
```bash
# Windows
py -3.10

# Linux/Mac
python3.10
```

Then run:
```python
from utils.chromadb_client import ChromaDBClient

client = ChromaDBClient()
collections = client.client.list_collections()
print("Collections:", [c.name for c in collections])

# Get collection details
for collection in collections:
    print(f"\n{collection.name}: {collection.count()} documents")
```

Exit with: `exit()`

### Regenerate Data

**Banking Data:**
```bash
py -3.10 utils\banking_data_generator_enhanced.py
```

**Retail Data:**
```bash
py -3.10 utils\retail_data_generator_enhanced.py
```

**Then reinitialize:**
```bash
py -3.10 scripts\initialize_chromadb.py
```

---

## 🐛 TROUBLESHOOTING COMMANDS

### Check Python Version
```bash
py -3.10 --version          # Windows
python3.10 --version        # Linux/Mac
python --version            # Check default
```

Expected: `Python 3.10.x`

### Check Node.js Version
```bash
node --version              # Should be v18.x or higher
npm --version               # Should be 9.x or higher
```

### Check if Ports are Already in Use

**Windows:**
```cmd
# Check port 8002 (Backend)
netstat -ano | findstr :8002

# Check port 5173 (Frontend)
netstat -ano | findstr :5173
```

**Linux/Mac:**
```bash
# Check and show what's using the ports
lsof -i :8002
lsof -i :5173

# Check if ports are listening
netstat -tuln | grep 8002
netstat -tuln | grep 5173
```

### Kill Process Using Specific Port

**Windows:**
```cmd
# Find PID
netstat -ano | findstr :8002
# Kill process (replace PID)
taskkill /F /PID <PID>
```

**Linux/Mac:**
```bash
# Kill directly
lsof -ti:8002 | xargs kill -9
lsof -ti:5173 | xargs kill -9
```

### Check Installed Python Packages
```bash
py -3.10 -m pip list
py -3.10 -m pip show chromadb
py -3.10 -m pip show fastapi
```

### Check Frontend Dependencies
```bash
cd frontend
npm list
npm outdated
```

### Test ChromaDB Connection
```bash
py -3.10 -c "from utils.chromadb_client import ChromaDBClient; client = ChromaDBClient(); print('ChromaDB connected:', client.client.heartbeat())"
```

### Clear npm Cache (if frontend issues)
```bash
cd frontend
rm -rf node_modules package-lock.json
npm cache clean --force
npm install
```

### Reinstall Python Dependencies
```bash
py -3.10 -m pip uninstall -r requirements.txt -y
py -3.10 -m pip install -r requirements.txt
```

---

## 📦 COMPLETE WORKFLOW EXAMPLES

### First Time Setup - Full Workflow

**Windows:**
```cmd
:: Clone repository
git clone https://github.com/Revathi031187/NBA.git
cd NBA

:: Install backend dependencies
py -3.10 -m pip install -r requirements.txt

:: Install frontend dependencies
cd frontend
npm install
cd ..

:: Initialize ChromaDB
py -3.10 scripts\initialize_chromadb.py

:: You're ready to run!
```

**Linux/Mac:**
```bash
# Clone repository
git clone https://github.com/Revathi031187/NBA.git
cd NBA

# Install backend dependencies
python3.10 -m pip install -r requirements.txt

# Install frontend dependencies
cd frontend
npm install
cd ..

# Initialize ChromaDB
python3.10 scripts/initialize_chromadb.py

# You're ready to run!
```

---

### Daily Development Workflow

**Terminal 1 (Backend):**
```bash
cd path/to/NBA
py -3.10 api\main_unified_chromadb.py
```

**Terminal 2 (Frontend):**
```bash
cd path/to/NBA/frontend
npm run dev
```

**Browser:**
```
http://localhost:5173
```

---

## 🎯 QUICK REFERENCE

### URLs
| Service | URL | Description |
|---------|-----|-------------|
| Frontend | `http://localhost:5173` | Main application UI |
| Backend API | `http://localhost:8002` | REST API |
| API Docs (Swagger) | `http://localhost:8002/docs` | Interactive API documentation |
| API Docs (ReDoc) | `http://localhost:8002/redoc` | Alternative API docs |

### Key Commands
| Task | Windows | Linux/Mac |
|------|---------|-----------|
| Run Backend | `py -3.10 api\main_unified_chromadb.py` | `python3.10 api/main_unified_chromadb.py` |
| Run Frontend | `cd frontend && npm run dev` | `cd frontend && npm run dev` |
| Initialize DB | `py -3.10 scripts\initialize_chromadb.py` | `python3.10 scripts/initialize_chromadb.py` |
| Stop Server | `Ctrl + C` | `Ctrl + C` |

### Project Structure
```
NBA/
├── api/                          # Backend FastAPI application
│   └── main_unified_chromadb.py  # Main server file
├── agents/                       # AI agents (A & B)
├── frontend/                     # React TypeScript UI
│   ├── src/                      # Source code
│   └── package.json              # Frontend dependencies
├── scripts/                      # Setup scripts
│   └── initialize_chromadb.py    # Database initialization
├── utils/                        # Helper utilities
├── data/preloaded/              # Pre-generated datasets
├── chroma_db/                    # ChromaDB storage (auto-generated)
└── requirements.txt              # Python dependencies
```

---

## 💡 PRO TIPS

1. **Always start backend before frontend** - Frontend needs backend API
2. **Keep terminals open** - Both must run simultaneously
3. **Check console output** - Errors appear in terminal windows
4. **Use Swagger docs** - Test APIs at `http://localhost:8002/docs`
5. **Browser DevTools** - Check Network tab for API calls (F12)
6. **ChromaDB persistence** - Data persists in `chroma_db/` folder
7. **Hot reload** - Frontend auto-reloads on code changes
8. **Backend restart** - Backend needs manual restart after code changes

---

## 🆘 COMMON ISSUES & SOLUTIONS

### Issue: `ModuleNotFoundError: No module named 'chromadb'`
**Solution:**
```bash
py -3.10 -m pip install -r requirements.txt
```

### Issue: `Port 8002 already in use`
**Solution:**
```bash
# Kill existing process
lsof -ti:8002 | xargs kill -9  # Mac/Linux
netstat -ano | findstr :8002    # Windows (then taskkill)
```

### Issue: `Frontend not loading`
**Solution:**
1. Check if backend is running (`http://localhost:8002/docs`)
2. Check browser console for errors (F12)
3. Clear browser cache and reload

### Issue: `ChromaDB initialization failed`
**Solution:**
```bash
# Delete and reinitialize
rm -rf chroma_db
py -3.10 scripts\initialize_chromadb.py
```

### Issue: `npm install fails`
**Solution:**
```bash
cd frontend
rm -rf node_modules package-lock.json
npm cache clean --force
npm install
```

### Issue: `Python version not found`
**Solution:**
```bash
# Install Python 3.10 from python.org
# Or use your existing Python:
python -m pip install -r requirements.txt
python api/main_unified_chromadb.py
```

---

## 📚 ADDITIONAL RESOURCES

- **Main README:** `README.md`
- **Quick Start:** `QUICKSTART.md`
- **Production Deployment:** `PRODUCTION_DEPLOYMENT.md`
- **Deployment Guide:** `DEPLOYMENT_GUIDE.md`

---

## 🎓 LEARNING THE SYSTEM

### Test Agent A (Customer Segmentation)
```bash
# Start application, then in browser:
# 1. Go to Banking Dashboard
# 2. Click "Agent A: Persona Builder"
# 3. Click "Execute"
# 4. View clustering results and personas
```

### Test Agent B (Product Recommendations)
```bash
# Start application, then in browser:
# 1. Go to Banking Dashboard
# 2. Click "Agent B: Product Matcher"
# 3. Select a customer
# 4. View personalized product recommendations
```

### Explore API Directly
```bash
# List all collections
curl http://localhost:8002/api/chromadb/collections

# Get banking customers
curl http://localhost:8002/api/banking/customers

# Execute Agent A
curl -X POST http://localhost:8002/api/banking/agent_a/execute

# Get Agent A results
curl http://localhost:8002/api/banking/agent_a/results
```

---

**Happy Coding! 🚀**

For issues or questions, please open a GitHub issue at: https://github.com/Revathi031187/NBA/issues

