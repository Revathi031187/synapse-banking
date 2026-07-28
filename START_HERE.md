# 🏦 Banking Platform - START HERE

## ✅ TRANSFORMATION COMPLETE!

Your Academy Sports demo has been successfully transformed into a Banking & Financial Services platform for the Databricks Banking GTM meeting.

---

## 🚀 Quick Start (2 Minutes)

### 1. Start the Backend

Open a terminal and run:

```bash
uvicorn api.main_unified_chromadb:app --port 8002 --reload
```

**Verify:** Visit http://localhost:8002/docs and check for `/api/banking/*` endpoints

### 2. Start the Frontend

Open another terminal and run:

```bash
cd frontend
npm run dev
```

**Verify:** Visit http://localhost:3000 (should redirect to `/banking`)

### 3. Run the Demo

1. **Dashboard:** http://localhost:3000/banking
   - Should show "100 customers loaded"

2. **Run Agent A:** Click "Run Agent A - Segmentation"
   - Wait ~5 seconds for clustering
   - View 4-5 banking personas (High Net Worth, Young Professionals, etc.)

3. **View Recommendations:** Click on a customer
   - See personalized product recommendations
   - Products: Credit Cards, Loans, Accounts, Investments

---

## 📊 What's Available

### Data
- **100 banking customers** with life-event tracking (first_home, marriage, career_growth)
- **5 core products** (credit card, mortgage, savings, investment, business loan)
- **Transaction history** with channel tracking (mobile/branch/hybrid)

### Features
- ✅ Customer segmentation (Agent A)
- ✅ Product recommendations (Agent B)
- ✅ Banking personas (Databricks-aligned)
- ✅ Banking theme (blue & gold colors)
- ✅ API endpoints (`/api/banking/*`)
- ✅ Isolated from Academy Sports (both work)

---

## 💡 Key Files

| File | Purpose |
|------|---------|
| `BANKING_TRANSFORMATION_COMPLETE.md` | **Read this next** - Full implementation summary |
| `BANKING_QUICK_START.md` | Detailed setup instructions |
| `BANKING_IMPLEMENTATION_GUIDE.md` | Technical architecture & customization |
| `generate_banking_data_simple.py` | Scale to 5,000 customers (optional) |

---

## 🎯 For Databricks Meeting

### Demo Flow (10 minutes)
1. Show banking dashboard (2 min)
2. Run Agent A segmentation (3 min)
3. Show customer recommendations (3 min)
4. Discuss Databricks alignment (2 min)

### Key Talking Points
- **Use Cases:** Prospecting, personalization, cross-sell, churn prediction
- **Impact:** $40-65M sales uplift, $50M+ cross-sell revenue
- **Tech Stack:** Unity Catalog, MLFlow, Lakeflow integration
- **Personas:** Head of Consumer Banking, Marketing, Customer Experience

### Reference
- Databricks outcome map (your presentation image)
- Impact metrics: 10-20% acquisition improvement, 20-30% cross-sell improvement

---

## ⚡ Optional Enhancements

### Scale Up (5 minutes)
```bash
# Generate 5,000 customers instead of 100
python generate_banking_data_simple.py

# Creates richer demo with more data
# Clustering takes ~60 seconds (vs. 5 seconds)
```

### Complete Agent UI (30 minutes each)
- Copy `AcademyAgentA.tsx` → `BankingAgentA.tsx` (update API calls)
- Copy `AcademyAgentB.tsx` → `BankingAgentB.tsx` (update product cards)

---

## 🔍 Verification

### Check Backend
```bash
# Visit API docs
http://localhost:8002/docs

# Search for "banking" endpoints
# Should see: /api/banking/datasets, /api/banking/agent_a/execute, etc.
```

### Check Frontend
```bash
# Visit banking dashboard
http://localhost:3000/banking

# Should see:
# - "Banking & Financial Services" header
# - Status cards with customer count
# - "Run Agent A" button enabled
```

### Check Academy (Still Works)
```bash
# Original demo unchanged
http://localhost:3000/academy

# Both demos run on same backend
# No conflicts between industries
```

---

## 🆘 Troubleshooting

### Backend won't start
```bash
# Install dependencies
pip install -r requirements.txt

# Check port availability
netstat -ano | findstr :8002
```

### Frontend won't start
```bash
# Install dependencies
cd frontend
npm install
npm run dev
```

### No data loaded
```bash
# Check data exists
dir data\preloaded\banking_nba\

# Should see: customers.csv, products.csv, transactions.csv
```

### Agent A fails
```bash
# Check kmodes installed
pip install kmodes

# Check data structure
python -c "import pandas as pd; df = pd.read_csv('data/preloaded/banking_nba/customers.csv'); print(f'Customers: {len(df)}')"
```

---

## ✨ Success!

Your banking platform is ready for the Databricks meeting!

**Next step:** Read `BANKING_TRANSFORMATION_COMPLETE.md` for full details.

**Questions?** Check the Implementation Guide or Quick Start guide.

---

**Demo URLs:**
- 🏦 Banking: http://localhost:3000/banking
- 🏕️ Academy: http://localhost:3000/academy
- 📚 API Docs: http://localhost:8002/docs

**Good luck with the Databricks Banking GTM meeting!** 🚀
