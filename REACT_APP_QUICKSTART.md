# 🚀 React Application Quick Start Guide

## ✅ **You're Back to the Full React Implementation!**

All Streamlit code has been removed. The React frontend with FastAPI backend is ready to use.

---

## 📋 **Prerequisites**

- **Node.js** (v16 or higher) - [Download here](https://nodejs.org/)
- **Python 3.10+** - [Download here](https://www.python.org/)
- **Git** (optional, for updates)

---

## 🎯 **Quick Start (Easiest)**

### **Option 1: Use the Startup Script**

Simply double-click:
```
START_REACT_APP.bat
```

This will:
1. Install all dependencies
2. Start the FastAPI backend (port 8000)
3. Start the React frontend (port 5173)
4. Open your browser automatically

---

## 🔧 **Manual Start (If Script Fails)**

### **Step 1: Start Backend**

Open a terminal and run:
```bash
py -3.10 -m uvicorn api.main_unified_chromadb:app --reload --host 0.0.0.0 --port 8000
```

### **Step 2: Start Frontend**

Open another terminal and run:
```bash
cd frontend
npm install  # First time only
npm run dev
```

### **Step 3: Open Browser**

Go to: **http://localhost:5173**

---

## 🎨 **React Features (All Working!)**

### ✅ **Complete Feature List:**

1. **Professional White Theme**
   - Clean, modern UI
   - Inter font family
   - Smooth animations
   - Responsive design

2. **Agent A: Persona Discovery**
   - K-Prototypes clustering
   - Interactive visualizations
   - Revenue analysis
   - Confidence scores
   - Temporal/seasonal metrics
   - Customer characteristics
   - **Customer Insights Tab** with individual analysis
   - **AI Explanations** for all visualizations

3. **Agent B: Product Recommendations**
   - Logistic regression scoring
   - **Persona-based recommendations**
   - **Customer-specific recommendations**
   - Compatibility scores
   - Real-time filtering
   - Product details

4. **Customer Insights**
   - Searchable customer grid
   - Individual customer profiles
   - **AI-powered explanations** (Together AI)
   - Shopping behavior analysis

5. **Data Management**
   - V1 and V2 dataset support
   - ChromaDB integration for speed
   - Data preview and statistics

---

## 📊 **Architecture**

```
Frontend (React + TypeScript + Vite)
   ↓
Backend (FastAPI + Python 3.10)
   ↓
ML Agents (K-Prototypes + Logistic Regression)
   ↓
Data Storage (ChromaDB + CSV)
```

---

## 🔑 **Environment Setup**

### **Configure Together AI API Key:**

Create a `.env` file in the project root:
```env
TOGETHER_API_KEY=your_api_key_here
DATA_DIR=data/preloaded/academy_sports
```

Get your API key from: https://api.together.xyz/

---

## 🛠️ **Common Issues & Solutions**

### **Issue 1: Port Already in Use**

**Error:** `Port 8000 is already in use`

**Solution:**
```bash
# Find and kill the process
netstat -ano | findstr :8000
taskkill /PID <PID_NUMBER> /F
```

### **Issue 2: Module Not Found**

**Error:** `ModuleNotFoundError: No module named 'X'`

**Solution:**
```bash
pip install -r requirements.txt
```

### **Issue 3: Frontend Won't Start**

**Error:** `npm ERR!`

**Solution:**
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run dev
```

### **Issue 4: ChromaDB Not Initialized**

**Solution:**
```bash
python scripts/initialize_chromadb_academy.py
```

---

## 📁 **Project Structure**

```
personalization-agent/
├── frontend/                 # React application
│   ├── src/
│   │   ├── pages/
│   │   │   └── academy/     # All Academy Sports pages
│   │   ├── components/      # Reusable UI components
│   │   └── utils/           # Helper functions
│   └── package.json
│
├── api/                      # FastAPI backend
│   └── main_unified_chromadb.py
│
├── agents/                   # ML agents
│   ├── agent_a_academy_chromadb.py
│   └── agent_b_academy_chromadb.py
│
├── data/                     # Datasets
│   └── preloaded/
│       └── academy_sports/
│
├── utils/                    # Utility functions
│
└── START_REACT_APP.bat      # Easy startup script
```

---

## 🎯 **Usage Workflow**

1. **Load Data** → Select V1 or V2 dataset
2. **Agent A** → Discover customer personas (3-5 groups)
3. **Customer Insights** → Analyze individual customers
4. **Agent B** → Get product recommendations
5. **Export** → Download results

---

## 📞 **Need Help?**

- **API Documentation:** http://localhost:8000/docs
- **Backend Logs:** Check terminal where backend is running
- **Frontend Console:** Press F12 in browser

---

## ✨ **What's New vs Streamlit?**

| Feature | React ✅ | Streamlit ❌ |
|---------|---------|--------------|
| Speed | Fast | Slow |
| UI Quality | Professional | Basic |
| Animations | Smooth | None |
| Customization | Full | Limited |
| Interactivity | Excellent | Good |
| Production-Ready | Yes | No |
| All Features Working | Yes | No |

---

## 🎉 **Enjoy Your React Application!**

The professional, production-ready interface with all features working correctly!

