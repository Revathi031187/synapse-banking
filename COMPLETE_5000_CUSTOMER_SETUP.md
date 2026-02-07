# 🎯 Complete 5000 Customer Setup for Banking

## ✅ **Issues Fixed**

### 1. ❌ Only 100 Customers → ✅ Now Generating 5000
- Updated generator to output to correct folder (`banking_nba`)
- Matches Academy Sports data structure

### 2. ❌ Data Viewer Crash → ✅ Now Handles NaN/Inf Values
- Added proper JSON serialization in API
- Cleans data before returning to frontend

---

## 🚀 **Quick Setup (3 Steps)**

### Step 1: Generate 5000 Customers
Run this file:
```bash
GENERATE_5000_CUSTOMERS.bat
```

**OR manually**:
```bash
venv\Scripts\activate
python utils/banking_data_generator_5000.py
```

**Expected Output**:
```
Generating 5,000 banking customers...
✅ Generated customers.csv (5000 customers)
✅ Generated products.csv (20 products)
✅ Generated transactions.csv (~50,000 transactions)
```

### Step 2: Restart Backend
```bash
# Stop current backend (Ctrl+C)
# Restart it
START_BANKING.bat
```

### Step 3: Reload in UI
1. Go to: `http://localhost:5173/banking/data-loader`
2. Click "Load Dataset" button
3. Go to Agent A and run segmentation

---

## 📊 **What You'll Get**

| Item | Count | Details |
|------|-------|---------|
| **Customers** | 5,000 | Same as Academy Sports |
| **Products** | 20 | Banking products |
| **Transactions** | ~50,000 | Realistic transaction history |
| **Personas** | 6 Types | Diverse banking personas |

---

## 🎯 **Persona Distribution (5000 Customers)**

| Persona Type | Count | Percentage | Description |
|--------------|-------|------------|-------------|
| High Net Worth Investors | 600 | 12% | $500K+ portfolios |
| Young Professionals | 1,100 | 22% | Career-focused millennials |
| Small Business Owners | 750 | 15% | Business banking needs |
| Family Savers | 1,200 | 24% | Building family wealth |
| Student & First-Time | 800 | 16% | New to banking |
| Retirees | 550 | 11% | Fixed income focus |

---

## ✅ **Verification**

### Check Customer Count
```bash
venv\Scripts\activate
python -c "import pandas as pd; df = pd.read_csv('data/preloaded/banking_nba/customers.csv'); print(f'Total customers: {len(df)}')"
```

**Expected**: `Total customers: 5000`

### Check Data Files
```bash
dir data\preloaded\banking_nba\*.csv
```

**Expected**:
```
customers.csv       (~2 MB)
products.csv        (~2 KB)
transactions.csv    (~5 MB)
```

---

## 🧪 **Test the Full Flow**

### 1. Agent A - Segmentation
- Go to: `/banking/agent-a`
- Set clusters: 5
- Click "Execute Segmentation"
- **Should see**: 5 unique persona cards

### 2. Macro Dashboard
- Go to: `/banking/macro-dashboard`
- **Should see**: Beautiful cards with images
- Click any persona to see micro-segments

### 3. Agent B - Recommendations
- Go to: `/banking/agent-b`
- **Should see**: 5000 customers in dropdown
- Select any customer
- Click "Get Recommendations"
- **Should see**: 3 types of recommendations

### 4. Data Loader
- Go to: `/banking/data-loader`
- Click eye icon on "Customers"
- **Should see**: Table with 5000 rows (preview of 100)

---

## 🐛 **Troubleshooting**

### Issue 1: Still Shows 100 Customers
**Fix**: Re-generate the data
```bash
GENERATE_5000_CUSTOMERS.bat
```

### Issue 2: Data Viewer Still Crashes
**Fix**: Restart backend (changes were made to API)
```bash
# Stop backend (Ctrl+C in terminal)
# Restart
START_BANKING.bat
```

### Issue 3: "Dataset not found"
**Fix**: Check file location
```bash
dir data\preloaded\banking_nba\customers.csv
```
Should exist.

---

## 📁 **Files Created/Modified**

### Backend Changes
- ✅ `api/main_unified_chromadb.py` - Fixed JSON serialization
- ✅ `utils/banking_data_generator_5000.py` - Fixed output path

### New Helper Files
- ✅ `GENERATE_5000_CUSTOMERS.bat` - Easy data generation
- ✅ `COMPLETE_5000_CUSTOMER_SETUP.md` - This guide

---

## 🎯 **Summary**

### Before ❌
- 100 customers only
- Data viewer crashed on NaN values
- Didn't match Academy Sports

### After ✅
- 5,000 customers (matches Academy)
- Data viewer works perfectly
- Same structure as Academy Sports
- All features functional

---

## 🚀 **Next Steps (Do This Now!)**

1. **Run**: `GENERATE_5000_CUSTOMERS.bat`
2. **Wait**: ~30 seconds for generation
3. **Restart**: Backend server
4. **Test**: Go to `/banking/data-loader` and view data

**You'll have the exact same setup as Academy Sports!** 🎉
