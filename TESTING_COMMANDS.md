# Testing Commands - Agent A Enhanced

## Quick Start

### 1. Clear Python Cache (if needed)
```bash
py -3.10 restart_backend.py
```

### 2. Start Backend
```bash
py -3.10 api/main_unified_chromadb.py
```

Backend will start on `http://localhost:8002`

---

## Test Commands

### Option 1: Direct Agent Test (No API)
**Tests the agent directly without going through the API**

```bash
py -3.10 test_agent_a_direct.py
```

**What it tests:**
- ✅ Agent initialization
- ✅ Clustering execution (5 clusters)
- ✅ Persona generation (AI-generated names)
- ✅ Uniqueness check (no duplicates)
- ✅ Decimal precision (proper rounding)
- ✅ Temporal variation (different patterns)
- ✅ Customer methods (get_all_customers, get_customer_details, etc.)
- ✅ Visualization data (7 types)

**Expected output:**
```
================================================================================
DIRECT TEST: Agent A Enhanced - Academy Sports
================================================================================

1. Initializing Agent A Enhanced...
2. Executing clustering with 5 clusters...
3. ✅ Clustering completed successfully!
   Total customers: 5,000
   Total revenue: $X,XXX,XXX.XX
   Number of clusters: 5

4. Generated Personas (5):
   Cluster 0: 🏕️ Beginner Budget-Conscious
   ...

✅ DIRECT TEST COMPLETED SUCCESSFULLY!
```

---

### Option 2: Test All API Endpoints
**Tests all 27 Academy Sports API endpoints**

**IMPORTANT: Backend must be running first!**

```bash
py -3.10 test_all_academy_endpoints.py
```

**What it tests:**
- 📁 Dataset Management (4 endpoints)
- 🎯 Agent A - Macro Segmentation (6 endpoints)
- 👥 Customer Insights (6 endpoints)
- 📊 Visualization Explanations (7 types)
- 🎁 Agent B - Recommendations (2 endpoints)
- 🔬 Micro Segmentation (2 endpoints)
- 🛍️ Product Recommendations (5 endpoints)
- 🗄️ ChromaDB Management (1 endpoint)

**Expected output:**
```
================================================================================
TESTING ALL ACADEMY SPORTS API ENDPOINTS
================================================================================
Backend URL: http://localhost:8002
================================================================================

📁 DATASET MANAGEMENT
✅ GET  /api/academy/datasets                      [200] List datasets
✅ POST /api/academy/datasets/load                 [200] Load V1 dataset
...

✅ TEST SUMMARY: All endpoints working!
```

---

### Option 3: Manual API Testing with curl

#### Test Agent A Execution
```bash
curl -X POST http://localhost:8002/api/academy/agent_a/execute ^
  -H "Content-Type: application/json" ^
  -d "{\"n_clusters\": 5, \"gamma\": 0.5}"
```

#### Get Agent A Results
```bash
curl http://localhost:8002/api/academy/agent_a/results
```

#### Get All Personas
```bash
curl http://localhost:8002/api/academy/personas
```

#### Get Customers (Paginated)
```bash
curl "http://localhost:8002/api/academy/agent_a/customers?skip=0&limit=10"
```

#### Get Customer Details
```bash
curl http://localhost:8002/api/academy/agent_a/customer/CUST_0001
```

#### Get AI Explanation for Visualization
```bash
curl -X POST http://localhost:8002/api/academy/agent_a/explain-visualization ^
  -H "Content-Type: application/json" ^
  -d "{\"visualization_type\": \"revenue\", \"data\": {}, \"personas\": {}}"
```

---

## Verification Checklist

After running tests, verify:

### ✅ Persona Names
- [ ] AI-generated names (e.g., "🏕️ Beginner Budget-Conscious")
- [ ] No hardcoded names ("Family Socializer", "First-Time Camper")
- [ ] All names are unique (no duplicates)
- [ ] Names reflect actual data characteristics

### ✅ Metrics Precision
- [ ] Confidence: 75.5% (not 75.350979631668%)
- [ ] Percentages: 1 decimal place
- [ ] Revenue: 2 decimal places
- [ ] All metrics properly rounded

### ✅ Temporal Metrics
- [ ] Different seasonal patterns per persona
- [ ] Different peak seasons (not all "Summer")
- [ ] Growth rates vary (-2% to +10%, not "0.0%")
- [ ] Each persona has unique temporal profile

### ✅ Visualization Data
- [ ] cluster_distribution (sizes & revenue)
- [ ] persona_characteristics (6 dimensions, scaled 0-100)
- [ ] behavior_comparison (6 metrics with units)
- [ ] confidence_distribution (high/med/low breakdown)
- [ ] seasonal_acquisition (seasonal patterns + growth)
- [ ] revenue_breakdown (detailed revenue metrics)
- [ ] persona_distribution (for pie chart)

### ✅ AI Explanations
- [ ] Proper HTML formatting (`<div>` tags)
- [ ] Section headers visible
- [ ] Bullet points with • symbol
- [ ] Structured format (SECTION: headers)
- [ ] No markdown symbols (**,  ###)

### ✅ Customer Methods
- [ ] get_all_customers() works
- [ ] get_customer_details() works
- [ ] get_customer_recommendations() works
- [ ] export_persona_assignments() works
- [ ] generate_persona_explanation() works

---

## Troubleshooting

### Issue: "Backend not running"
**Solution:**
```bash
py -3.10 api/main_unified_chromadb.py
```

### Issue: "Module not found"
**Solution:**
```bash
pip install -r requirements.txt
```

### Issue: "Old persona names showing"
**Solution:**
```bash
# Clear cache
py -3.10 restart_backend.py

# Restart backend
py -3.10 api/main_unified_chromadb.py
```

### Issue: "NaN error during clustering"
**Solution:** Already fixed! The enhanced agent now handles NaN values properly.

### Issue: "Identical temporal metrics"
**Solution:** Already fixed! Temporal metrics are now persona-specific.

---

## API Endpoints Summary

### Dataset Management
- `GET  /api/academy/datasets` - List available datasets
- `POST /api/academy/datasets/load` - Load a dataset
- `GET  /api/academy/dataset-version` - Get current version
- `GET  /api/academy/status` - Get system status

### Agent A (Macro Segmentation)
- `POST /api/academy/agent_a/execute` - Run clustering
- `GET  /api/academy/agent_a/results` - Get results
- `GET  /api/academy/personas` - List personas
- `GET  /api/academy/macro-segments` - Get macro segments
- `GET  /api/academy/agent_a/export` - Export CSV
- `GET  /api/academy/agent_a/customers` - Get customers (paginated)
- `GET  /api/academy/agent_a/customer/{id}` - Customer details
- `POST /api/academy/agent_a/customer/{id}/explain` - AI explanation
- `GET  /api/academy/agent_a/customer/{id}/recommendations` - Recommendations
- `POST /api/academy/agent_a/explain-visualization` - Explain chart

### Agent B (Recommendations)
- `POST /api/academy/agent_b/execute` - Generate recommendations
- `GET  /api/academy/agent_b/results` - Get results
- `GET  /api/academy/products` - List products

### Micro Segmentation
- `POST /api/academy/micro-segments/{macro_id}` - Create micro segments
- `GET  /api/academy/micro-segments/{macro_id}` - Get micro segments

### Product Recommendations
- `GET  /api/academy/recommendations/{id}/similar` - Similar products
- `GET  /api/academy/recommendations/{id}/you-might-like` - Personalized
- `POST /api/academy/recommendations/{id}/search` - Search-based
- `GET  /api/academy/recommendations/{id}/all` - All combined
- `GET  /api/academy/recommendations/new-visitor` - New visitor

### ChromaDB
- `POST /api/academy/chromadb/initialize` - Initialize collection
- `GET  /api/academy/chromadb/status` - Check status

---

## Quick Test Flow

1. **Start Backend:**
   ```bash
   py -3.10 api/main_unified_chromadb.py
   ```

2. **Run Direct Test:**
   ```bash
   py -3.10 test_agent_a_direct.py
   ```

3. **Run API Tests:**
   ```bash
   py -3.10 test_all_academy_endpoints.py
   ```

4. **Check Frontend:**
   - Open `http://localhost:3000`
   - Load V1 dataset
   - Run Agent A with 5 clusters
   - Verify all visualizations and metrics

---

## Expected Results

### Direct Test Output:
```
✅ DIRECT TEST COMPLETED SUCCESSFULLY!

Summary:
  • 5 unique AI-generated personas
  • All metrics properly rounded
  • Varied temporal patterns
  • All customer methods working
  • Visualization data complete

✨ Agent A Enhanced is ready for production!
```

### API Test Output:
```
TEST SUMMARY
All endpoints tested. Check for ❌ marks above for any failures.
```

### Frontend:
- 5 unique personas with AI-generated names
- Clean metrics (no excessive decimals)
- Different seasonal patterns per persona
- Professional AI explanations with formatting
- All visualizations populated with data

---

**All tests passing = Production ready!** ✅

