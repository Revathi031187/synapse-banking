# 🚀 Quick Start Guide - Phase 1 & 2

## ⚡ 5-Minute Setup

### 1. Start Backend (if not running)
```bash
cd c:\Users\jaisonsamuel.d.lv\Desktop\personalization-agent
py -3.10 api/main_unified_chromadb.py
```
**Expected**: Server running on http://0.0.0.0:8002

### 2. Start Frontend (if not running)
```bash
cd frontend
npm run dev
```
**Expected**: Frontend running on http://localhost:5173

### 3. Initialize ChromaDB (ONE-TIME)
```bash
py -3.10 -c "from utils.chromadb_academy_init import initialize_academy_chromadb; result = initialize_academy_chromadb(); print(f'Status: {result[\"product_initialization\"][\"status\"]}, Products: {result[\"product_initialization\"].get(\"product_count\", 0)}')"
```
**Expected**: `Status: success, Products: 57` (takes ~30-60 seconds)

### 4. Run Test Suite
```bash
py -3.10 test_phase1_phase2.py
```
**Expected**: `5/5 tests passed` ✅

### 5. Open Frontend
Navigate to: http://localhost:5173/academy

## 🎯 Complete Workflow Test

1. **Load Data** → http://localhost:5173/academy/data-loader
   - Select "Academy Sports V1"
   - Click "Confirm Dataset" ✅

2. **Macro Segmentation** → http://localhost:5173/academy/agent-a
   - Click "Discover Personas" button
   - Wait 10-15 seconds ⏳
   - See 4-5 macro segments ✅

3. **Micro Segmentation** → Click any macro segment card
   - Automatically navigates to `/academy/macro-segment/{id}/micro`
   - Click "Create Micro Segments" button
   - Wait 3-5 seconds ⏳
   - See 3-4 micro segments ✅

4. **Product Recommendations** → Click any customer ID in micro segments
   - Navigates to `/academy/customer/{customerId}/recommendations`
   - View 3 tabs:
     - Similar Products ✅
     - You Might Like ✅
     - Search & Discover ✅

## 📋 What Was Built

### Phase 1: Pure Clustering ✅
- ✅ Macro Segmentation (K-Prototypes) with business constraints
- ✅ Micro Segmentation (K-Means) with LTV tiers
- ✅ Professional agent: `agents/agent_a_academy_micro.py`

### Phase 2: ChromaDB Recommendations ✅
- ✅ Product embeddings with Together AI
- ✅ Semantic search with ChromaDB
- ✅ 3 recommendation types (Similar, You Might Like, Search)
- ✅ Professional agent: `agents/agent_b_academy_recommendations.py`

## 📁 Key Files Created

```
personalization-agent/
├── agents/
│   ├── agent_a_academy_micro.py           # Micro segmentation
│   └── agent_b_academy_recommendations.py  # Recommendations
├── utils/
│   └── chromadb_academy_init.py           # ChromaDB setup
├── test_phase1_phase2.py                  # Automated tests
├── PHASE1_PHASE2_COMPLETE_GUIDE.md        # Full documentation
├── SEGMENTATION_WITH_CHROMADB_PROPOSAL.md # Architecture
└── QUICK_START.md                         # This file
```

## 🔧 API Endpoints (Quick Reference)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/academy/chromadb/initialize` | POST | Initialize ChromaDB (one-time) |
| `/api/academy/chromadb/status` | GET | Check ChromaDB status |
| `/api/academy/agent_a/execute` | POST | Run macro segmentation |
| `/api/academy/macro-segments` | GET | Get macro segments summary |
| `/api/academy/micro-segments/{id}` | POST | Create micro segments |
| `/api/academy/micro-segments/{id}` | GET | Get micro segments |
| `/api/academy/recommendations/{id}/similar` | GET | Get similar products |
| `/api/academy/recommendations/{id}/you-might-like` | GET | Get segment recommendations |
| `/api/academy/recommendations/{id}/search` | POST | Search-based recommendations |
| `/api/academy/recommendations/new-visitor` | GET | Generic recommendations |

## 🐛 Troubleshooting

### Frontend not loading data?
**Check**: Backend running on correct port (8002)
```bash
curl http://localhost:8002/api/academy/datasets
```

### ChromaDB initialization fails?
**Check**: Together AI API key is set
```bash
# Windows
echo %TOGETHER_API_KEY%

# Or check in Python
py -3.10 -c "import os; print(os.getenv('TOGETHER_API_KEY'))"
```

### Recommendations return empty?
**Possible**: Customer has no purchase history
**Solution**: Use "New Visitor" recommendations endpoint

### Micro segmentation fails?
**Possible**: Macro segment too small
**Solution**: Reduce `n_micro_segments` parameter

## ✅ Success Checklist

- [ ] Backend running on port 8002
- [ ] Frontend running on port 5173
- [ ] ChromaDB initialized (57 products)
- [ ] Data loaded (5,000 customers)
- [ ] Macro segmentation works (4-5 segments)
- [ ] Micro segmentation works (3-4 per macro)
- [ ] Recommendations work (all 3 types)
- [ ] Test suite passes (5/5 tests)

## 📚 Full Documentation

For detailed information, see:
- **PHASE1_PHASE2_COMPLETE_GUIDE.md** - Complete guide with examples
- **SEGMENTATION_WITH_CHROMADB_PROPOSAL.md** - Architecture & benefits

## 🎉 You're Ready!

Once all checklist items are ✅, your system is fully operational!

**Next**: Navigate to http://localhost:5173/academy and test the complete workflow! 🚀

