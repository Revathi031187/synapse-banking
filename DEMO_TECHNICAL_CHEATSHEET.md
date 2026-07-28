# 🎯 Technical Demo - Quick Reference Cheat Sheet

**Print this for quick reference during demo presentations**

---

## 📊 **DATA SOURCES**

| Dataset | Records | Key Fields | Purpose |
|---------|---------|------------|---------|
| `customers.csv` | 5,000 | customer_id, total_spend_12mo, search_specificity, bundle_affinity, dominant_category, brand_loyalty | Clustering features |
| `products.csv` | 41 | product_id, brand, price, main_category, in_stock | Recommendation candidates |
| `purchases.csv` | ~50,000 | customer_id, product_id, price_paid, purchase_date | Transaction history |

---

## 🔬 **MACRO SEGMENTATION (K-PROTOTYPES)**

### **Algorithm: K-Prototypes (Hybrid)**
```
Distance = Σ(numeric_distances) + γ × Σ(categorical_mismatches)
γ = 0.5 (balance parameter)
```

### **Clustering Features**

| Feature Type | Feature Name | Scale | Meaning |
|--------------|--------------|-------|---------|
| **Numeric** | `total_spend_12mo` | $0 - $3,000 | Annual LTV |
| **Numeric** | `search_specificity` | 1-5 | Expertise level |
| **Numeric** | `bundle_affinity` | 0-1 | Bundle preference |
| **Numeric** | `price_sort_frequency` | 0-1 | Price sensitivity |
| **Numeric** | `purchase_frequency` | 1-15 | Transactions/year |
| **Numeric** | `recency_days` | 0-365 | Days since purchase |
| **Categorical** | `dominant_category` | 7 categories | Product interest |
| **Categorical** | `brand_loyalty` | 8 values | Brand preference |
| **Categorical** | `urbanicity` | 3 values | Location type |
| **Categorical** | `climate_zone` | 3 values | Geographic |

### **Process**
1. Test K = {4, 5, 6} clusters
2. Run 3 initializations per K
3. Validate business constraints
4. Select best solution
5. Generate persona names & explanations

### **Business Constraints**
- ✅ Min segment size: 50 customers
- ✅ Min avg revenue per segment
- ✅ No overly similar segments

---

## 🔍 **MICRO SEGMENTATION (K-MEANS)**

### **Algorithm: K-Means (Standard)**
```
Distance = Euclidean distance in 6D feature space
K = 4 (fixed)
Initialization: k-means++
```

### **Micro Features (All Numeric, Standardized)**

| Feature | Formula | Range | Purpose |
|---------|---------|-------|---------|
| `brand_loyalty_score` | Map categorical → numeric | 0-1 | Brand affinity |
| `expertise_level` | (specificity/5)×0.6 + expansion×0.4 | 0-1 | Knowledge level |
| `ltv_tier` | Binned total_spend | 0-3 | Value tier |
| `category_focus` | (1/(recency+1))×0.5 + freq×0.5 | 0-1 | Specialization |
| `bundle_affinity` | Direct from data | 0-1 | Bundle pref |
| `price_sensitivity` | Direct from data | 0-1 | Price focus |

### **LTV Tiers**
```
Bronze:   $0 - $300    → Tier 0
Silver:   $300 - $600  → Tier 1
Gold:     $600 - $1000 → Tier 2
Platinum: $1000+       → Tier 3
```

### **Micro Segment Name Format**
```
[Shopping Style] + [Category] + [LTV Tier]

Examples:
- "Brand Loyalist Sleep Gear - Platinum"
- "Frequent Buyer Backpack - Gold"
- "Value Hunter Tent - Bronze"
```

### **Shopping Styles**
- `bundle_affinity > 0.15` → "Bundle-Focused"
- `spec_expansion > 0.8` → "Category Explorer"
- `purchase_freq > 10` → "Frequent Buyer"
- `brand_loyalty > 0.7` → "Brand Loyalist"
- `price_sensitivity > 0.15` → "Value Hunter"
- Default → "Selective Shopper"

---

## 🛍️ **AGENT B: RECOMMENDATIONS**

### **Strategy 1: Similar Products (Content-Based)**

#### **Step 1: Price Range by LTV Tier**
```python
if ltv < $300:      # Bronze
    min = avg × 0.4, max = avg × 1.2
elif ltv < $600:    # Silver
    min = avg × 0.5, max = avg × 1.3
elif ltv < $1000:   # Gold
    min = avg × 0.6, max = avg × 1.5
else:               # Platinum
    min = avg × 0.8, max = avg × 2.0
```

#### **Step 2: Filter Candidates**
```sql
WHERE main_category = customer.dominant_category  -- MUST MATCH
  AND price BETWEEN min_price AND max_price
  AND in_stock = True
  AND product_id NOT IN purchased
```

#### **Step 3: Score Products**
```
score = (category_match × 0.50) +      # Highest!
        (subcategory_match × 0.15) +
        (brand_match × 0.20) +
        (rating/5 × 0.30)
```

### **Strategy 2: Segment Recommendations (Collaborative)**

#### **Process**
1. Get customers in same segment
2. Count product popularity in segment
3. Get customer's dominant_category
4. Filter: segment_products + category_match + price_range + in_stock
5. Score: `popularity×0.7 + rating×0.3`

### **Strategy 3: Search Recommendations (Semantic)**

#### **Process**
1. Embed search term (Together AI)
2. Query ChromaDB (cosine similarity)
3. Filter by customer price range + in_stock
4. Return top 3

---

## 🎯 **KEY METRICS TO MENTION**

### **Segmentation Quality**
- **K-Prototypes Cost**: Minimize (show value)
- **Segment Sizes**: All ≥50 customers
- **Revenue Distribution**: Show % per segment

### **Recommendation Accuracy**
- **Category Match**: 95%+ (verify during demo)
- **Price Appropriateness**: Show Bronze vs Platinum examples
- **In-Stock Rate**: 100% for main recommendations

### **Performance**
- **Clustering Time**: 10-20 seconds for 5,000 customers
- **Recommendation Time**: <100ms per customer
- **API Response**: <500ms end-to-end

---

## 🎨 **VISUAL ELEMENTS**

### **Macro Personas**
- **Images**: 11 categories, 3-4 images each, hash-based selection
- **Colors**: Consistent theme per persona
- **Emojis**: Quick visual identifier
- **Hover**: Scale 1.1, translate up 8px, 500ms transition

### **Micro Segments**
- **Icons**: 💎 Premium, 🎯 Expert, 💰 Value, ⚡ Frequent
- **Badges**: Dynamic color-coded traits
- **Explanations**: Loyalty level + behaviors + recommendations

---

## 📈 **DEMO FLOW**

```
1. DATA LOADING (3 min)
   ├─ Show 3 CSV files
   ├─ Explain preprocessing
   └─ Click "Load Dataset"

2. MACRO CLUSTERING (5 min)
   ├─ Explain K-Prototypes
   ├─ Show features (10 total)
   ├─ Click "Run Clustering"
   ├─ Show personas
   └─ Explain metrics & explanations

3. MICRO SEGMENTATION (4 min)
   ├─ Navigate to Visual Dashboard
   ├─ Click macro persona
   ├─ Explain K-Means
   ├─ Show 6 micro features
   ├─ Show micro segments
   └─ Explain naming logic

4. RECOMMENDATIONS (5 min)
   ├─ Click example customer
   ├─ Explain 3 strategies
   ├─ Show price tier logic
   ├─ Show category filtering
   ├─ Verify accuracy
   └─ Show out-of-stock section

5. TECHNICAL ARCH (2 min)
   ├─ Stack: FastAPI + React
   ├─ Data flow diagram
   ├─ Caching strategy
   └─ Error handling

6. METRICS & VALIDATION (2 min)
   ├─ Clustering quality
   ├─ Recommendation accuracy
   └─ Business metrics

7. Q&A (3-5 min)
```

---

## 🎤 **QUICK ANSWERS**

**Q: Why K-Prototypes?**  
A: Handles mixed numeric + categorical data. Can't use K-Means on `dominant_category` or `brand_loyalty`.

**Q: Why 4-6 clusters?**  
A: Business constraint - need actionable segments. Too few = not granular, too many = hard to operationalize.

**Q: How often re-cluster?**  
A: Monthly for stable, weekly for dynamic. Our system: 10-20 sec for 5K customers, so could do nightly.

**Q: Recommendation cold start?**  
A: Use segment-based (Strategy 2) until purchase history builds. New visitors get best-sellers.

**Q: Scale to 1M customers?**  
A: Incremental clustering, distributed compute (Spark), approximate NN (FAISS), precomputed recommendations.

**Q: Why rule-based explanations?**  
A: Fast (no API), deterministic, explainable, no hallucination risk. Can add LLM later for richer text.

---

## 💡 **TECHNICAL HIGHLIGHTS**

### **Sophisticated ML**
✅ Hybrid K-Prototypes algorithm  
✅ Hierarchical segmentation (macro + micro)  
✅ Multi-strategy recommendations  

### **Business-Aware**
✅ LTV tier-based price filtering  
✅ Constraint validation  
✅ Explainable segments  

### **Production-Ready**
✅ Fast performance (<1 min clustering)  
✅ Robust error handling  
✅ Comprehensive logging  

### **User Experience**
✅ Visual dashboard with lifestyle images  
✅ Smooth animations (500ms transitions)  
✅ In-stock/out-of-stock separation  

---

## 🐛 **DEMO TROUBLESHOOTING**

| Issue | Quick Fix |
|-------|-----------|
| No macro personas | Re-run Agent A clustering |
| No micro segments | Click macro card again |
| Wrong product categories | Check browser console for category logs |
| No explanations | Restart backend, re-run clustering |
| Out-of-stock in main | Verify `products.csv` in_stock field |
| Blank white page | Hard refresh (Ctrl+Shift+R) |

---

## 📐 **FORMULAS QUICK REFERENCE**

### **K-Prototypes Distance**
```
d(x, y) = Σ|x_num - y_num| + γ × Σ(x_cat ≠ y_cat)
```

### **Price Range**
```
Bronze:   [avg×0.4, avg×1.2]
Silver:   [avg×0.5, avg×1.3]
Gold:     [avg×0.6, avg×1.5]
Platinum: [avg×0.8, avg×2.0]
```

### **Recommendation Score**
```
Similar Products:
  0.50×category + 0.15×subcat + 0.20×brand + 0.30×rating

Segment Recommendations:
  0.70×popularity + 0.30×rating
```

### **Expertise Level**
```
expertise = (search_specificity / 5) × 0.6
          + spec_expansion_rate × 0.4
```

### **Category Focus**
```
focus = (1 / (recency_days + 1)) × 0.5
      + (frequency / max_frequency) × 0.5
```

---

## 🎯 **DEMO SUCCESS CHECKLIST**

**Before Demo:**
- [ ] Backend running on `http://localhost:8000`
- [ ] Frontend running on `http://localhost:5173`
- [ ] Agent A clustering completed
- [ ] Test customer prepared with good recommendations
- [ ] Browser console open (F12) for transparency

**During Demo:**
- [ ] Speak slowly and clearly
- [ ] Show specific numbers (don't say "several", say "5 personas")
- [ ] Verify recommendations match expectations
- [ ] Use cursor/laser pointer to highlight UI elements
- [ ] Acknowledge good questions, answer thoroughly

**Key Things to Show:**
- [ ] CSV files and preprocessing
- [ ] Clustering running (10-20 sec)
- [ ] Macro personas with images
- [ ] Micro segments with explanations
- [ ] Category-matched recommendations
- [ ] Bronze vs Platinum price differences
- [ ] In-stock vs out-of-stock separation
- [ ] Browser console logs (transparency)

---

**Print this sheet and keep it next to your laptop during demos!**

**Total Sections:** 9 | **Total Demo Time:** 18-22 minutes

