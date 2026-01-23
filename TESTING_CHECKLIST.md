# 🧪 Recommendation System - Testing Checklist

Use this checklist to verify all recommendation functionality is working correctly.

---

## ⚙️ **SETUP (Before Testing)**

- [ ] Backend is running: `py -3.10 api/main_unified_chromadb.py`
- [ ] Frontend is running: `npm run dev`
- [ ] Browser console is open (F12) for debugging
- [ ] Clear browser cache (Ctrl+Shift+Delete)

---

## 🎯 **AGENT A: MACRO SEGMENTATION**

### **Step 1: Run Clustering**
- [ ] Navigate to `/academy/agent-a`
- [ ] Click "Load Dataset"
- [ ] Wait for success message
- [ ] Click "Run Clustering"
- [ ] Wait 10-20 seconds for completion

### **Expected Results**
- [ ] ✅ Success message appears
- [ ] ✅ 4-6 macro personas displayed
- [ ] ✅ Each persona has:
  - [ ] Lifestyle image (not broken)
  - [ ] Persona name (e.g., "Expert Premium Campers")
  - [ ] Customer count
  - [ ] Average revenue
  - [ ] Dominant category
- [ ] ✅ "Visual Macro Dashboard (NEW!)" button appears

### **Console Logs to Check**
```
✓ Loaded X customers
✓ Executing clustering with Y clusters
✓ Generated Z personas
```

---

## 🔍 **VISUAL MACRO DASHBOARD**

### **Step 2: Navigate to Dashboard**
- [ ] Click "Visual Macro Dashboard (NEW!)" button
- [ ] Dashboard loads without errors

### **Expected Results**
- [ ] ✅ All macro persona cards visible
- [ ] ✅ Lifestyle images load correctly
- [ ] ✅ Color themes applied
- [ ] ✅ Customer counts and revenue displayed

### **Step 3: Test Hover Effect**
- [ ] Hover over each macro card
- [ ] Card should smoothly scale up and lift

### **Expected Results**
- [ ] ✅ Smooth scale (1.0 → 1.1)
- [ ] ✅ Smooth translate upward
- [ ] ✅ Z-index increases (card goes above others)
- [ ] ✅ Returns to normal when hover ends

---

## 📊 **MICRO SEGMENTATION**

### **Step 4: Expand Micro Segments**
- [ ] Click on a macro persona card
- [ ] Wait for micro segments to load

### **Expected Results**
- [ ] ✅ Card expands to show 4 micro segments
- [ ] ✅ Each micro segment has:
  - [ ] Descriptive name (e.g., "Brand Loyalist Sleep Gear - Platinum")
  - [ ] Customer count and percentage
  - [ ] Average spend
  - [ ] LTV tier badge (Bronze/Silver/Gold/Platinum)
  - [ ] Icons (brand, expertise, etc.)
  - [ ] Trait badges
  - [ ] **Segment explanation** (with loyalty level)
  - [ ] Example customer

### **Step 5: Verify Segment Explanations**
- [ ] Check each micro segment
- [ ] Expand "Why This Segment?" section

### **Expected Results**
- [ ] ✅ Loyalty level badge (HIGH/MODERATE/LOW)
- [ ] ✅ Explanation text describes:
  - [ ] Why customers are in this segment
  - [ ] Loyalty drivers
  - [ ] Key behaviors (2-3 bullet points)
- [ ] ✅ No placeholder text or "undefined"

### **Console Logs to Check**
```
📊 Micro Segment Data: {...}
📝 Segment Explanation: {loyalty_level: "HIGH", ...}
✓ Parsed X micro segments
```

---

## 🛍️ **PRODUCT RECOMMENDATIONS**

### **Step 6: Select Example Customer**
- [ ] Click "Example Customer" button in a micro segment
- [ ] Wait for recommendations to load

### **Expected Results**
- [ ] ✅ Right panel displays customer info:
  - [ ] Customer name
  - [ ] "Tailored For You" badge
- [ ] ✅ "Top Picks" section shows 3-6 products
- [ ] ✅ Products displayed with:
  - [ ] Product image (placeholder pink tent icon)
  - [ ] Product name
  - [ ] Brand
  - [ ] Price
  - [ ] In-stock indicator

---

## ✅ **RECOMMENDATION ACCURACY**

### **Test 7: Category Matching**

#### **Test 7A: Sleep Gear Customer**
- [ ] Find "Sleep Gear" micro segment (any tier)
- [ ] Click example customer
- [ ] Check recommended products

**Expected Results:**
- [ ] ✅ ALL products should be **Sleeping Bags** or **Airbeds**
- [ ] ❌ NO Coolers, Lanterns, Tents, Backpacks, etc.
- [ ] ✅ Brands: Coleman, Kelty, The North Face, MSR, Big Agnes

**If you see wrong categories, CHECK CONSOLE:**
```
🔍 Finding category preference...
✅ Using customer's dominant_category: 'Sleeping Bags + Airbeds'
🎯 Final category for recommendations: 'Sleeping Bags + Airbeds'
📦 Found X candidate products for category 'Sleeping Bags + Airbeds'
```

#### **Test 7B: Backpack Customer**
- [ ] Find "Backpack" micro segment
- [ ] Click example customer
- [ ] Check recommended products

**Expected Results:**
- [ ] ✅ ALL products should be **Hiking Backpacks**
- [ ] ❌ NO other categories

#### **Test 7C: Tent Customer**
- [ ] Find "Tent" micro segment
- [ ] Click example customer
- [ ] Check recommended products

**Expected Results:**
- [ ] ✅ ALL products should be **Tents + Screen Houses**
- [ ] ❌ NO other categories

---

### **Test 8: Price Tier Matching**

#### **Test 8A: Bronze Tier Customer**
- [ ] Find a "Bronze" tier micro segment
- [ ] Click example customer
- [ ] Check product prices

**Expected Results:**
- [ ] ✅ Prices mostly in **$30-$100 range** (budget-friendly)
- [ ] ❌ NO high-end products ($500+)
- [ ] ✅ Brands: Coleman, Ozark Trail, basic Magellan Outdoors

#### **Test 8B: Platinum Tier Customer**
- [ ] Find a "Platinum" tier micro segment
- [ ] Click example customer
- [ ] Check product prices

**Expected Results:**
- [ ] ✅ Prices can include **$500-$1,200 range** (premium)
- [ ] ✅ Brands: The North Face, YETI, MSR, Big Agnes
- [ ] ❌ Not ONLY budget products

---

### **Test 9: In-Stock vs Out-of-Stock**

#### **Test 9A: Main Recommendations**
- [ ] Select any customer
- [ ] Check "Top Picks" section

**Expected Results:**
- [ ] ✅ All products in main section are **IN STOCK**
- [ ] ✅ No "Out of Stock" labels in main section

#### **Test 9B: Out-of-Stock Section**
- [ ] Scroll down below "Top Picks"
- [ ] Look for "Currently Unavailable" section

**Expected Results:**
- [ ] ✅ Section exists (may be collapsed)
- [ ] ✅ Toggle button to show/hide
- [ ] ✅ When expanded, shows out-of-stock products
- [ ] ✅ Out-of-stock products clearly labeled
- [ ] ✅ Separate from main recommendations

---

## 🎨 **AGENT B PAGE**

### **Test 10: Dynamic Personas**
- [ ] Navigate to `/academy/agent-b`
- [ ] Check persona dropdown

**Expected Results:**
- [ ] ✅ Shows **dynamic personas** from Agent A
- [ ] ❌ NOT hardcoded "Budget Campers", "Premium Campers", "Expert Campers"
- [ ] ✅ Matches personas from Visual Dashboard
- [ ] ✅ Each persona has:
  - [ ] Name
  - [ ] Image
  - [ ] Customer count

### **Test 11: Agent B Recommendations**
- [ ] Select a persona
- [ ] Wait for recommendations to load

**Expected Results:**
- [ ] ✅ Recommendations displayed
- [ ] ✅ Segment explanation visible
- [ ] ✅ In-stock products in main section
- [ ] ✅ Out-of-stock toggle available

---

## 🐛 **ERROR SCENARIOS**

### **Test 12: Empty State Handling**
- [ ] Try accessing Visual Dashboard BEFORE running Agent A

**Expected Results:**
- [ ] ✅ "No Data Available" message
- [ ] ✅ Prompt to run Agent A first
- [ ] ❌ NO crash or blank white page

### **Test 13: Browser Console Errors**
- [ ] Open browser console (F12)
- [ ] Navigate through all pages
- [ ] Click all buttons

**Expected Results:**
- [ ] ✅ NO red error messages
- [ ] ✅ Only blue/green info logs
- [ ] ✅ Warnings (yellow) are acceptable

---

## 📱 **NAVIGATION & PERSISTENCE**

### **Test 14: Data Persistence**
- [ ] Run Agent A clustering
- [ ] Go to Visual Dashboard
- [ ] Navigate back to Agent A page

**Expected Results:**
- [ ] ✅ Agent A results still visible
- [ ] ✅ Personas still displayed
- [ ] ❌ Does NOT show "No data" or require re-running

### **Test 15: Dashboard Persistence**
- [ ] Go to Visual Dashboard
- [ ] Select customer and view recommendations
- [ ] Navigate to Agent B page
- [ ] Navigate back to Visual Dashboard

**Expected Results:**
- [ ] ✅ Previous customer selection remembered (optional)
- [ ] ✅ Macro/micro segments still visible
- [ ] ❌ Does NOT require re-loading

---

## 🔄 **BACKEND LOGS**

### **Test 16: Backend Console Check**
While testing, check backend terminal for:

**Good Logs (✅):**
```
✅ Using clustered customer data with X customers
👤 Customer CUST_00123 info:
   Dominant Category: Sleeping Bags + Airbeds
   Cluster: 2
🔍 Finding category preference...
✅ Using customer's dominant_category: 'Sleeping Bags + Airbeds'
📦 Found 6 candidate products for category 'Sleeping Bags + Airbeds'
📊 Raw recommendations received:
   Tailored: 3 products
```

**Bad Logs (❌):**
```
❌ ERROR: ...
⚠️ Cannot determine product preferences
⚠️ Customer's dominant_category is invalid: 'nan'
```

---

## ✅ **FINAL CHECKLIST**

Before signing off, verify:

- [ ] ✅ Agent A runs without errors
- [ ] ✅ Macro personas display with images
- [ ] ✅ Micro segments load and expand
- [ ] ✅ Segment explanations visible and detailed
- [ ] ✅ Product recommendations match customer category
- [ ] ✅ Bronze customers get budget products
- [ ] ✅ Platinum customers get premium products
- [ ] ✅ In-stock products in main section
- [ ] ✅ Out-of-stock products separate
- [ ] ✅ No category mismatches (Sleep → Coolers ❌)
- [ ] ✅ No browser console errors
- [ ] ✅ Backend logs show correct category selection
- [ ] ✅ Data persists across navigation
- [ ] ✅ Agent B uses dynamic personas

---

## 🎉 **SUCCESS CRITERIA**

**All tests pass:** ✅ System ready for demo/production  
**1-2 tests fail:** ⚠️ Minor issues, review failed tests  
**3+ tests fail:** ❌ Major issues, restart backend and re-run Agent A

---

## 📞 **TROUBLESHOOTING**

### **Issue: Wrong products showing**
1. Check browser console for category logs
2. Verify backend shows correct dominant_category
3. Restart backend: `py -3.10 api/main_unified_chromadb.py`
4. Re-run Agent A clustering
5. Clear browser cache

### **Issue: No explanations showing**
1. Check if `segment_explanation` is in API response (browser Network tab)
2. Restart backend
3. Re-run Agent A clustering (old data doesn't have explanations)

### **Issue: Out-of-stock products in main section**
1. Check backend logs for `in_stock` conversion
2. Verify `products.csv` has correct `in_stock` values
3. Restart backend

### **Issue: Blank white page**
1. Check browser console for errors
2. Check if Agent A has been run
3. Hard refresh (Ctrl+Shift+R)
4. Restart frontend: `npm run dev`

---

**Last Updated:** January 9, 2026  
**Version:** 1.0

