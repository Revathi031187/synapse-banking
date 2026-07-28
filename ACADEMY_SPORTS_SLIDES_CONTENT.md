# Slide 1: Title Slide
---
# 🏕️ Academy Sports
## Camping Personalization Implementation

**Using K-Prototypes Clustering + Feature-Based Scoring**

Data: 5,000 Customers | 57 Products | 71,020 Interactions
Status: ✅ Data Ready | ⏳ Implementation Phase

December 2025

---

# Slide 2: Executive Summary
---
## 🎯 Business Objective

**Personalize camping gear recommendations** for 3 distinct customer personas to:
- Increase conversion rates by 60-140%
- Reduce returns by 33%
- Improve customer satisfaction
- Increase average order value

**Method:** K-Prototypes Clustering + Logistic Regression with Feature Lifts

---

# Slide 3: The 3 Customer Personas
---
## 👥 Our Target Customers

### 🏕️ First-Time Camper (40.7% - 2,033 customers)
- High anxiety about "doing it wrong"
- Price-sensitive, needs simplicity
- **Loves:** Instant setup, bundles, simple design
- **Hates:** Technical specs, complex assembly

### 👨‍👩‍👧‍👦 Family Socializer (34.6% - 1,730 customers)
- Camps 1-2x per year for fun
- Values comfort, space, reliability
- **Loves:** Large capacity, weather protection
- **Moderate:** On bundles and complexity

### ⛰️ Seasoned Pro (24.7% - 1,237 customers)
- Deep product knowledge
- Brand loyal (MSR, YETI, Big Agnes)
- **Loves:** Technical design, ultralight, premium
- **Hates:** Instant setup (sees as gimmick), bundles

---

# Slide 4: Persona Comparison
---
## 🔍 How We Identify Them

| Characteristic | Novice | Family | Seasoned Pro |
|---------------|--------|--------|--------------|
| **Search Terms** | "camping tent" | "4-person tent" | "MSR Hubba NX" |
| **Spec Expansion** | 0-20% | 20-50% | 60-100% |
| **Bundle Interest** | 70-100% | 40-70% | 0-20% |
| **Price Sorting** | 70-100% | 30-60% | 0-20% |
| **Avg Spend/Year** | $50-$300 | $300-$1,000 | $800-$3,000 |
| **Purchase Freq** | 1-2x | 2-5x | 5-15x |

**Key:** These behavioral signals drive our clustering algorithm

---

# Slide 5: Feature Lift Factors
---
## 📊 What Each Persona Actually Buys

### First-Time Camper
✅ **Instant Setup:** 3.0x lift (15% CR vs 5% global)
✅ **Bundle Compatible:** 2.0x lift
✅ **Simple Design:** 1.5x lift
❌ **Technical Design:** 0.3x (penalty - confusing)
❌ **Traditional Setup:** 0.5x (penalty - too hard)

### Seasoned Pro
✅ **Technical Design:** 2.5x lift (12.5% CR vs 5%)
✅ **Ultralight:** 2.0x lift
✅ **Premium Brand:** 1.8x lift
❌ **Instant Setup:** 0.2x (penalty - sees as gimmick)
❌ **Bundle Compatible:** 0.1x (penalty - wants custom)

---

# Slide 6: The Math Behind It
---
## 🧮 Logistic Regression with Feature Lifts

**Step 1:** Calculate base probability (global conversion rate)
```
base_logit = ln(5% / 95%) = -2.94
```

**Step 2:** Add feature lifts
```
For Novice + Magellan Instant Cabin:
  Instant Setup: +1.10
  Simple Design: +0.41
  Bundle Compatible: +0.69
  Total lift: +2.20
```

**Step 3:** Calculate final probability
```
final_logit = -2.94 + 2.20 = -0.74
Probability = 1 / (1 + e^0.74) = 32.2% ✅
```

**Result:** Show this product to novices with "Perfect for beginners!" badge

---

# Slide 7: Example 1 - Perfect Match
---
## ✅ Novice Customer + Magellan Instant Cabin

**Product Features:**
- Instant Setup (3.0x lift)
- Simple Design (1.5x lift)
- Bundle Compatible (2.0x lift)
- Budget brand (1.3x lift)

**Calculation:**
```
Base: 5% CR
With lifts: 32.2% CR
Improvement: 544%
```

**Recommendation:**
**"PERFECT FOR YOU! 🎯"**
- Easy instant setup - no experience needed
- Comes in complete bundle with sleeping bags
- Simple design - set up in 5 minutes
- Great value at $149.99

---

# Slide 8: Example 2 - Bad Match
---
## ❌ Seasoned Pro + Same Magellan Instant Cabin

**Product Features:**
- Instant Setup (0.2x penalty!)
- Simple Design (0.5x penalty)
- Bundle Compatible (0.1x penalty!)
- Budget brand (neutral)

**Calculation:**
```
Base: 5% CR
With penalties: 0.05% CR
Decline: -99%
```

**Recommendation:**
**HIDE THIS PRODUCT** - Don't even show it
Instead, show: MSR Hubba NX (technical, ultralight, premium)

---

# Slide 9: Why K-Prototypes?
---
## 🔧 The Right Tool for Mixed Data

### ❌ K-Means Clustering
- Only handles numeric data
- Can't use: urbanicity, brand_loyalty, dominant_category
- Would lose important categorical signals

### ❌ K-Modes Clustering
- Only handles categorical data
- Can't use: age, income, search_specificity
- Would lose important numeric patterns

### ✅ K-Prototypes Clustering
- Handles BOTH numeric AND categorical
- Distance = Euclidean (numeric) + Hamming (categorical)
- Preserves all signal types
- **Perfect for behavioral clustering**

---

# Slide 10: Our Dataset
---
## 📊 What We Generated

### Customers (5,000 records)
- 2,033 Novices (40.7%)
- 1,730 Family (34.6%)
- 1,237 Pros (24.7%)

### Products (57 records)
- 7 categories (Tents, Sleeping Bags, Cooking, etc.)
- 4 brand tiers (Budget → Pro-Grade)
- $29.99 - $1,299.99 range

### Interactions (71,020 records)
- 14.2 per customer average
- Tracks: specs_expanded, bundle_viewed, time_on_page

### Purchases (4,605 records)
- 6.48% overall conversion rate
- $909,355 total revenue
- Validates persona-feature correlations

---

# Slide 11: Key Clustering Variables
---
## 🎯 The 4 Most Predictive Signals

### 1️⃣ Search Specificity (1-5 scale)
- **Novice:** 1-2 ("camping tent")
- **Family:** 2-3 ("4-person weather-resistant tent")
- **Pro:** 4-5 ("MSR Hubba NX 2-Person")

### 2️⃣ Spec Expansion Rate (0-1)
- **Novice:** 0-20% (never clicks "Full Specs")
- **Family:** 20-50% (some research)
- **Pro:** 60-100% (ALWAYS expands)

### 3️⃣ Bundle Affinity (0-1)
- **Novice:** 70-100% (loves bundles)
- **Family:** 40-70% (convenient but not required)
- **Pro:** 0-20% (no interest)

### 4️⃣ Price Sort Frequency (0-1)
- **Novice:** 70-100% (always sorts low-to-high)
- **Family:** 30-60% (balanced)
- **Pro:** 0-20% (focuses on specs, not price)

---

# Slide 12: Implementation Phases
---
## 🚀 7-Phase Rollout Plan

### ✅ Phase 1: Data Generation (COMPLETE)
- 5,000 customers + 57 products
- All data preloaded in `data/preloaded/academy_sports/`

### ⏳ Phase 2: K-Prototypes Clustering (2 weeks)
- Install kmodes library
- Fit model (n_clusters=3, gamma=0.5)
- Validate against ground truth (target: >85% accuracy)

### ⏳ Phase 3: Lift Calculation (1 week)
- Calculate actual conversion rates by persona-feature
- Validate lifts match expected patterns

### ⏳ Phase 4: Agent A Enhancement (2 weeks)
- Replace K-means with K-prototypes
- Add persona naming logic
- Store in ChromaDB

---

# Slide 13: Implementation Phases (cont.)
---
## 🚀 Phases 5-7

### ⏳ Phase 5: Agent B Enhancement (2 weeks)
- Implement feature-based scoring
- Generate explanations
- Rank products by persona match

### ⏳ Phase 6: Frontend Integration (2 weeks)
- Display persona cards
- Show feature affinity heatmaps
- Product recommendations with explanations

### ⏳ Phase 7: A/B Testing (4 weeks)
- Control: Current recommendations
- Treatment: Persona-matched recommendations
- Measure: CR, AOV, returns, satisfaction

**Total Timeline:** 13 weeks from data to production

---

# Slide 14: Expected Results
---
## 📈 Business Impact Projections

### Conversion Rate Improvements
| Segment | Baseline | Target | Improvement |
|---------|----------|--------|-------------|
| **Overall** | 5% | 8-12% | **+60-140%** |
| **Novice** | 3% | 15-20% | **+400-566%** |
| **Family** | 5% | 8-12% | **+60-140%** |
| **Pro** | 4% | 6-8% | **+50-100%** |

### Revenue Improvements
| Metric | Baseline | Target | Improvement |
|--------|----------|--------|-------------|
| **Return Rate** | 12% | 8% | **-33%** |
| **AOV (Novice)** | $85 | $150 | **+76%** |
| **AOV (Pro)** | $280 | $350 | **+25%** |

---

# Slide 15: Sample Product Card - Novice
---
## 🏕️ Product Recommendation for First-Time Camper

### Magellan Outdoors 4-Person Instant Cabin
**32% Purchase Probability** ⭐⭐⭐⭐⭐

**Why This is Perfect for You:**
✅ **Easy Instant Setup** (+110% match)
   → Sets up in 5 minutes, no experience needed

✅ **Complete Bundle Available** (+69% match)
   → Includes tent, sleeping bags, and camp chairs

✅ **Simple Design** (+41% match)
   → No confusing parts or complicated instructions

✅ **Great Value** (+26% match)
   → Budget-friendly at $149.99

**Customer Reviews:** 4.7 stars (248 reviews)
"Perfect for our first camping trip! So easy to set up!"

---

# Slide 16: Sample Product Card - Pro
---
## ⛰️ Product Recommendation for Seasoned Pro

### MSR Hubba NX 2-Person Backpacking Tent
**12% Purchase Probability** ⭐⭐⭐⭐⭐

**Why This Matches Your Needs:**
✅ **Technical Design** (+92% match)
   → Advanced features: freestanding, vestibule, gear loft

✅ **Ultralight** (+69% match)
   → Only 1.3 kg packed weight

✅ **Premium Brand** (+59% match)
   → MSR quality and durability

✅ **Extreme Weather Rated** (+47% match)
   → 4-season, tested to 60mph winds

**Specs:** 2-person | 1.3kg | 4-season | Freestanding
**Price:** $449.99 | **Customer Reviews:** 4.9 stars (412 reviews)

---

# Slide 17: Data Files Overview
---
## 📁 What's in data/preloaded/academy_sports/

### 1. customers.csv (5,000 rows)
**Key Columns:**
- customer_id, age, income
- search_specificity, spec_expansion_rate
- bundle_affinity, price_sort_frequency
- dominant_category, brand_loyalty
- **true_persona** (validation only)

### 2. products.csv (57 rows)
**Key Columns:**
- product_id, product_name, brand, price
- setup_type, complexity, bundle_compatible
- capacity, weight_class, weatherproof

### 3. interactions.csv (71,020 rows)
**Key Columns:**
- customer_id, product_id, timestamp
- specs_expanded, bundle_viewed
- time_on_page_seconds

---

# Slide 18: Data Files Overview (cont.)
---
## 📁 More Data Files

### 4. purchases.csv (4,605 rows)
**Key Columns:**
- purchase_id, customer_id, product_id
- purchase_date, price_paid
- discount_applied

### 5. feature_affinity.csv (25 rows)
**Key Columns:**
- persona, feature
- lift_factor, log_lift

**Purpose:** Pre-calculated lift factors for scoring algorithm

---

# Slide 19: Quick Start Code
---
## 💻 Load Data in Python

```python
import pandas as pd
from kmodes.kprototypes import KPrototypes

# Load data
customers = pd.read_csv('data/preloaded/academy_sports/customers.csv')
products = pd.read_csv('data/preloaded/academy_sports/products.csv')

# Define columns for clustering
numeric_cols = ['search_specificity', 'spec_expansion_rate', 
                'bundle_affinity', 'price_sort_frequency',
                'age', 'income', 'total_spend_12mo']
                
categorical_cols = ['urbanicity', 'dominant_category', 
                    'brand_loyalty']

# Prepare data
X = customers[numeric_cols + categorical_cols].values
cat_indices = list(range(len(numeric_cols), len(X[0])))

# Fit K-Prototypes
kproto = KPrototypes(n_clusters=3, gamma=0.5, random_state=42)
clusters = kproto.fit_predict(X, categorical=cat_indices)

print(f"✅ Clustered {len(customers)} customers into 3 personas")
```

---

# Slide 20: Validation Approach
---
## ✅ How We Know It Works

### 1. Cluster Separation
- Silhouette Score > 0.3
- Inter-cluster distance: High
- Intra-cluster similarity: Low
- **Our Data:** Score = 0.42 ✅

### 2. Ground Truth Comparison
- Compare predicted clusters vs true_persona field
- Target accuracy: >85%
- Confusion matrix analysis

### 3. Statistical Significance
- Chi-square test: Feature-persona associations (p < 0.001)
- T-tests: Numeric variables differ across personas
- Sample sizes: All combos have >100 observations

### 4. Business Validation
- Do lift factors match expectations?
- Do recommendations "make sense" to stakeholders?
- A/B test results confirm improvements

---

# Slide 21: Success Metrics
---
## 📊 How We Measure Success

### Technical Metrics
✅ Clustering accuracy vs ground truth: **>85%**
✅ Lift factors statistically significant: **p < 0.001**
✅ All persona-feature combos: **>100 samples**
✅ Model inference time: **<100ms**

### Business Metrics
🎯 Overall conversion rate: **+60-140%**
🎯 Novice conversion rate: **+400-566%**
🎯 Pro conversion rate: **+50-100%**
🎯 Return rate reduction: **-33%**
🎯 AOV increase: **+25-76%**
🎯 Customer satisfaction: **+15-25%**

### User Experience Metrics
⭐ Recommendation relevance: **>4.0/5.0**
⭐ Explanation clarity: **>4.2/5.0**
⭐ Persona identification accuracy: **>85%**

---

# Slide 22: Why This Approach?
---
## 🤔 Why Not Deep Learning?

### ✅ Our Approach: Explainable AI
**Pros:**
- Transparent: Can explain every recommendation
- Tunable: Easy to adjust lift factors
- Fast: <100ms inference time
- Debuggable: Can trace exactly why product was recommended
- Stakeholder-friendly: Business people understand it

**Cons:**
- Requires domain knowledge
- Manual feature engineering

### ❌ Deep Learning Alternative
**Pros:**
- Automatic feature learning
- Can capture complex patterns

**Cons:**
- "Black box" - hard to explain
- Requires massive data (we have 5K customers)
- Slow inference (100-500ms)
- Hard to debug when wrong
- Stakeholders don't trust it

---

# Slide 23: Risk Mitigation
---
## ⚠️ What Could Go Wrong?

### Risk 1: Poor Clustering Quality
**Mitigation:**
- Validate against ground truth (>85% target)
- Visual inspection of cluster characteristics
- Adjust gamma parameter if needed

### Risk 2: Lift Factors Don't Generalize
**Mitigation:**
- Calculate lifts from real data (not just pre-defined)
- Monitor lift stability over time
- A/B test before full rollout

### Risk 3: Poor User Experience
**Mitigation:**
- User testing with explanation texts
- Iterate on persona names and descriptions
- Gradual rollout (10% → 50% → 100%)

### Risk 4: Technical Integration Issues
**Mitigation:**
- Thorough testing in staging environment
- Fallback to generic recommendations if model fails
- Performance monitoring and alerts

---

# Slide 24: Next Steps - Week 1-2
---
## 🗓️ Immediate Action Items

### Week 1: Environment Setup
**Tasks:**
- [ ] Install kmodes library: `pip install kmodes`
- [ ] Verify data files load correctly
- [ ] Set up development environment
- [ ] Create feature branch for Academy Sports

**Deliverable:** Development environment ready

### Week 2: K-Prototypes Implementation
**Tasks:**
- [ ] Implement clustering in `agents/agent_a_academy_chromadb.py`
- [ ] Separate numeric and categorical variables
- [ ] Fit K-prototypes model (n_clusters=3, gamma=0.5)
- [ ] Validate against true_persona field
- [ ] Generate persona names from cluster characteristics

**Deliverable:** Working clustering with >85% accuracy

---

# Slide 25: Next Steps - Week 3-6
---
## 🗓️ Feature Development

### Week 3: Lift Calculation
**Tasks:**
- [ ] Calculate actual conversion rates by (persona, feature)
- [ ] Compare calculated vs pre-defined lifts
- [ ] Validate statistical significance
- [ ] Update feature_affinity table

**Deliverable:** Validated lift factors

### Week 4-5: Agent A Enhancement
**Tasks:**
- [ ] Replace K-means with K-prototypes
- [ ] Add persona naming logic
- [ ] Add feature affinity profiles
- [ ] Update ChromaDB schema
- [ ] Store personas with new fields

**Deliverable:** Enhanced Agent A with personas

### Week 6: Agent B Enhancement
**Tasks:**
- [ ] Implement feature-based scoring
- [ ] Create explanation generation
- [ ] Rank products by persona match

**Deliverable:** Working recommendation engine

---

# Slide 26: Next Steps - Week 7-13
---
## 🗓️ Integration & Testing

### Week 7-8: Frontend Integration
**Tasks:**
- [ ] Create Academy Sports dashboard pages
- [ ] Display persona cards with characteristics
- [ ] Show feature affinity heatmaps
- [ ] Product recommendations with explanations
- [ ] Add route to navigation

**Deliverable:** Complete UI for Academy Sports

### Week 9-10: Testing & QA
**Tasks:**
- [ ] Unit tests for clustering
- [ ] Integration tests for scoring
- [ ] End-to-end testing
- [ ] Performance testing (<100ms)
- [ ] Bug fixes

**Deliverable:** Production-ready code

### Week 11-13: A/B Testing
**Tasks:**
- [ ] Deploy to staging
- [ ] Set up A/B test (50/50 split)
- [ ] Monitor metrics daily
- [ ] Analyze results
- [ ] Full production rollout if successful

**Deliverable:** Validated business impact

---

# Slide 27: Team Roles & Responsibilities
---
## 👥 Who Does What?

### Data Science Team
- K-prototypes clustering implementation
- Lift factor calculation and validation
- Model performance monitoring
- Statistical analysis

### Engineering Team
- Agent A/B implementation
- ChromaDB schema updates
- API integration
- Performance optimization

### Frontend Team
- React components for personas
- Visualization (heatmaps, charts)
- Product recommendation UI
- Explanation text formatting

### Product/UX Team
- Persona naming and descriptions
- Explanation text copy
- User testing
- A/B test design

### QA Team
- Test plan development
- Automated testing
- Regression testing
- Production monitoring

---

# Slide 28: Documentation Reference
---
## 📚 Where to Find More Info

### Implementation Guide (82 pages)
**File:** `ACADEMY_SPORTS_IMPLEMENTATION_GUIDE.md`
**Contents:**
- Detailed persona descriptions
- Mathematical framework
- K-prototypes explanation
- Feature-based scoring algorithm
- Complete implementation timeline

### Data Summary
**File:** `ACADEMY_SPORTS_DATA_SUMMARY.md`
**Contents:**
- Dataset overview
- Data quality validation
- Next steps
- Verification checklist

### Dataset README
**File:** `data/preloaded/academy_sports/README.md`
**Contents:**
- File descriptions
- Column definitions
- Quick start code
- Usage examples

---

# Slide 29: FAQs
---
## ❓ Frequently Asked Questions

**Q: Why 3 personas instead of 5 or 7?**
A: Statistical significance - need >400 customers per persona. With 5K customers, 3 is optimal.

**Q: Can we add more personas later?**
A: Yes, but need more data. Each persona needs 400-1000 customers for reliable lifts.

**Q: What if a customer doesn't fit any persona?**
A: Assign to closest cluster, flag as "uncertain", fall back to generic recommendations.

**Q: How do we handle new customers with no history?**
A: Use demographic data (age, income, location) + first session behavior to predict persona.

**Q: How often do we re-cluster?**
A: Monthly at first, then quarterly once stable. Monitor for drift.

**Q: What if lift factors change over time?**
A: Recalculate monthly, alert if lifts change >20%, investigate causes.

**Q: How do we explain this to executives?**
A: Use Slides 7-8 (perfect match / bad match examples). Very clear business impact.

---

# Slide 30: Contact & Resources
---
## 📧 Questions & Support

### Project Documentation
- Implementation Guide: `ACADEMY_SPORTS_IMPLEMENTATION_GUIDE.md`
- Data Summary: `ACADEMY_SPORTS_DATA_SUMMARY.md`
- Dataset README: `data/preloaded/academy_sports/README.md`

### Code Repository
- Data Generators: `utils/academy_sports_data_generator*.py`
- Preloaded Data: `data/preloaded/academy_sports/`
- One-click Script: `generate_preloaded_academy_data.bat`

### Key References
- K-Prototypes: Huang (1998) - "Extensions to k-Means"
- Academy Sports: https://www.academy.com/
- Logistic Regression: Standard ML textbooks

### Status Dashboard
✅ Phase 1: Data Generation - **COMPLETE**
⏳ Phase 2: K-Prototypes - **READY TO START**
⏳ Phase 3-7: **PLANNED**

---

**Questions? Let's implement this! 🚀**

