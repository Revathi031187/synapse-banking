# Banking API Endpoints - Complete Reference

## ✅ **All Banking Endpoints Now Working (Matching Academy Sports)**

---

## 📋 **Dataset Management**

### 1. List Available Datasets
```http
GET /api/banking/datasets
```
**Returns**: List of available datasets with table metadata

### 2. View Dataset Table
```http
GET /api/banking/datasets/view/{dataset_name}/{table_name}
```
**Example**: `/api/banking/datasets/view/banking/customers`
**Returns**: First 100 rows, columns, total count

### 3. Load Dataset
```http
POST /api/banking/datasets/load
Body: { "dataset_name": "banking" }
```
**Returns**: Load status and table counts

### 4. System Status
```http
GET /api/banking/status
```
**Returns**: ChromaDB status, loaded datasets, Agent A/B results

---

## 🎯 **Agent A - Customer Segmentation**

### 5. Execute Agent A
```http
POST /api/banking/agent_a/execute
Body: {
  "n_clusters": 5,
  "gamma": 0.5
}
```
**Returns**: Segmentation results with personas

### 6. Get Agent A Results
```http
GET /api/banking/agent_a/results
```
**Returns**: Latest segmentation results

### 7. Get Macro Segments
```http
GET /api/banking/macro-segments
```
**Returns**: List of macro personas with characteristics

### 8. List Customers
```http
GET /api/banking/agent_a/customers
```
**Returns**: All customers with cluster assignments

### 9. Get Customer Details
```http
GET /api/banking/agent_a/customer/{customer_id}
```
**Example**: `/api/banking/agent_a/customer/CUST001`
**Returns**: Detailed customer information

---

## 🎁 **Agent B - Product Recommendations**

### 10. Get Customers (Agent B Compatible)
```http
GET /api/banking/customers
```
**Returns**: List of customers for selection in Agent B
**Note**: Alias for `/api/banking/agent_a/customers` for Agent B compatibility

### 11. Execute Agent B ⚡ NEW!
```http
POST /api/banking/agent_b/execute
Body: {
  "customer_id": "CUST001",
  "top_n": 3
}
```
**Returns**: Personalized product recommendations
- Tailored recommendations
- Similar products
- Segment-based recommendations
- Customer info

### 12. Get All Recommendations
```http
GET /api/banking/recommendations/{customer_id}/all?search_term=credit
```
**Example**: `/api/banking/recommendations/CUST001/all`
**Returns**: All recommendation types for customer

### 13. List Products
```http
GET /api/banking/products
```
**Returns**: All banking products with categories

---

## 🔍 **Endpoint Comparison: Banking vs Academy**

| Feature | Academy Endpoint | Banking Endpoint | Status |
|---------|------------------|------------------|--------|
| Execute Agent A | `/api/academy/agent_a/execute` | `/api/banking/agent_a/execute` | ✅ |
| Agent A Results | `/api/academy/agent_a/results` | `/api/banking/agent_a/results` | ✅ |
| List Customers | `/api/academy/customers` | `/api/banking/customers` | ✅ NEW! |
| Execute Agent B | `/api/academy/agent_b/execute` | `/api/banking/agent_b/execute` | ✅ NEW! |
| Macro Segments | `/api/academy/macro-segments` | `/api/banking/macro-segments` | ✅ |
| Product List | `/api/academy/products` | `/api/banking/products` | ✅ |

---

## 🚀 **Testing Instructions**

### Step 1: Start Backend
```bash
START_BANKING.bat
```

### Step 2: Start Frontend
```bash
cd frontend
npm run dev
```

### Step 3: Test Agent A
1. Go to: `http://localhost:5173/banking/agent-a`
2. Set parameters (e.g., 5 clusters)
3. Click "Execute Segmentation"
4. ✅ Should see persona cards with unique names

### Step 4: Test Macro Dashboard
1. Go to: `http://localhost:5173/banking/macro-dashboard`
2. ✅ Should see beautiful persona cards with images
3. Click any persona to see micro-segments

### Step 5: Test Agent B
1. Go to: `http://localhost:5173/banking/agent-b`
2. Select a customer from dropdown
3. Click "Get Product Recommendations"
4. ✅ Should see 3 recommendation categories

### Step 6: Test Data Loader
1. Go to: `http://localhost:5173/banking/data-loader`
2. Click eye icon on any table
3. ✅ Should see data preview modal

---

## 🐛 **Common Issues & Fixes**

### Issue 1: "base URL /nba-platform/v3/" Error
**Fix**: ✅ FIXED - Vite now uses `/` for dev, `/nba-platform/v3/` for production

### Issue 2: Agent B endpoint not found
**Fix**: ✅ FIXED - Added `/api/banking/agent_b/execute`

### Issue 3: Customers not loading in Agent B
**Fix**: ✅ FIXED - Added `/api/banking/customers` alias endpoint

### Issue 4: ChromaDB DLL errors
**Fix**: ✅ FIXED - Fallback to default embedding (no torch required)

---

## ✅ **All Features Working**

- ✅ **Dataset Loader** - View and load 5,000 customers
- ✅ **Agent A** - Customer segmentation with unique names
- ✅ **Macro Dashboard** - Beautiful persona cards with images
- ✅ **Micro Segments** - Detailed sub-segments per persona
- ✅ **Agent B** - Product recommendations
- ✅ **ChromaDB** - Working with fallback embedding
- ✅ **API Parity** - Banking matches Academy Sports pattern

---

## 📊 **Quick Test Commands**

Test backend is running:
```bash
curl http://localhost:8002/api/banking/status
```

Test Agent A results:
```bash
curl http://localhost:8002/api/banking/agent_a/results
```

Test customers list:
```bash
curl http://localhost:8002/api/banking/customers
```

---

## 🎯 **Summary**

**Status**: 🟢 **ALL SYSTEMS OPERATIONAL**

- ✅ 13 Banking API endpoints
- ✅ Perfect parity with Academy Sports
- ✅ Agent A & B fully functional
- ✅ Macro/Micro dashboards working
- ✅ ChromaDB with fallback
- ✅ No admin rights required

**You're ready to go!** 🚀
