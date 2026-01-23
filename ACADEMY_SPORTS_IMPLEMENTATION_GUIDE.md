# 🏕️ Academy Sports Camping Personalization - Implementation Guide

## 📋 Document Purpose
This guide documents our implementation plan for Academy Sports camping gear personalization using K-prototypes clustering and feature-based lift scoring.

---

## 🎯 Business Objective

**Goal**: Personalize camping gear recommendations for 3 distinct customer personas to increase conversion rates and customer satisfaction.

**Success Metrics:**
- Increase conversion rate by persona-product match
- Reduce returns due to product mismatch
- Improve customer satisfaction scores
- Increase average order value for targeted personas

---

## 👥 Customer Personas (From Document Analysis)

### 1. 🏕️ First-Time Camper ("The Novice")
**Characteristics:**
- High anxiety about "doing it wrong"
- Price-sensitive but willing to buy simple solutions
- Confused by technical jargon
- Needs hand-holding and reassurance

**Behavioral Signals:**
- Search Specificity: 1-2 (Generic terms like "camping tent")
- Spec Expansion Rate: 0-20% (doesn't expand technical specs)
- Bundle Affinity: 70-100% (LOVES bundles/kits)
- Price Sort Frequency: 70-100% (always sorts by price low-to-high)

**Product Preferences:**
- ✅ Instant Setup
- ✅ Simple Design
- ✅ Bundle Compatible
- ✅ Budget-friendly brands
- ❌ Technical specifications
- ❌ Complex assembly

**Example Lift Factors:**
- Instant Setup: 3.0x (300% lift)
- Simple Design: 1.5x
- Bundle Compatible: 2.0x
- Budget Brand: 1.3x

---

### 2. 👨‍👩‍👧‍👦 Occasional Holiday Camper ("The Family Socializer")
**Characteristics:**
- Camps 1-2x per year for fun/social reasons
- Prioritizes comfort, space, food/drink storage
- Shopping for specific upcoming trip
- Moderate budget, values quality

**Behavioral Signals:**
- Search Specificity: 2-3 (Attributes like "4-person tent")
- Spec Expansion Rate: 20-50%
- Bundle Affinity: 40-70%
- Price Sort Frequency: 30-60%

**Product Preferences:**
- ✅ Large capacity (4+ person)
- ✅ Weather-resistant
- ✅ Comfortable features
- ✅ Mid-range brands
- ❌ Ultralight/minimalist
- ❌ Technical complexity

**Example Lift Factors:**
- 4+ Person Capacity: 2.0x
- Weather Resistant: 1.4x
- Moderate Design: 1.3x
- Bundle Compatible: 1.2x

---

### 3. ⛰️ Seasoned Pro ("The Technical Expert")
**Characteristics:**
- Deep knowledge of gear
- Optimizes for weight, durability, technical specs
- Brand loyal to performance names (MSR, YETI, Big Agnes)
- Indifferent to "instant setup" gimmicks

**Behavioral Signals:**
- Search Specificity: 4-5 (Model names like "MSR Hubba NX")
- Spec Expansion Rate: 60-100% (ALWAYS expands specs)
- Bundle Affinity: 0-20% (no interest in bundles)
- Price Sort Frequency: 0-20% (doesn't sort by price)

**Product Preferences:**
- ✅ Technical Design
- ✅ Ultralight/Lightweight
- ✅ Premium/Pro-Grade brands
- ✅ Extreme weather rating
- ❌ Instant Setup (sees as gimmick)
- ❌ Bundle kits (wants to choose each piece)

**Example Lift Factors (many are penalties):**
- Technical Design: 2.5x
- Ultralight: 2.0x
- Premium Brand: 1.8x
- Instant Setup: 0.2x (80% penalty!)
- Bundle Compatible: 0.1x (90% penalty!)

---

## 🔢 Mathematical Framework

### Logistic Regression with Feature Lifts

**Formula:**
```
Step 1: Base Score (logit scale)
base_logit = ln(global_conversion_rate / (1 - global_conversion_rate))

Step 2: Feature Lifts
For each feature:
  lift_logit = ln(persona_conversion / global_conversion)

Step 3: Total Score
z = base_logit + Σ(lift_logits for all features)

Step 4: Convert to Probability
P(purchase) = 1 / (1 + e^(-z))
```

**Example from Document:**

**Magellan Instant Cabin for Novice:**
- Global CR: 5% → base_logit = ln(0.05/0.95) = -2.94
- Instant Setup: 15% CR for novices → lift = ln(15%/5%) = ln(3.0) = +1.10
- Simple Design: lift = +0.41
- Bundle Compatible: lift = +0.69
- **Total z = -2.94 + 1.10 + 0.41 + 0.69 = -0.74**
- **Final P = 1/(1 + e^0.74) = 32.2%** ✅ SHOW THIS PRODUCT

**Same Product for Seasoned Pro:**
- Base: -2.94
- Instant Setup: 0.2% CR for pros → lift = ln(0.2%/5%) = ln(0.04) = -1.61
- Simple Design: -0.69
- Bundle: -2.30
- **Total z = -7.54**
- **Final P = 0.05%** ❌ HIDE THIS PRODUCT

---

## 🗄️ Data Architecture

### Table 1: Customers (5,000 records)

**Numeric Variables:**
| Column | Type | Description | Why It Matters |
|--------|------|-------------|----------------|
| age | int | Customer age (22-60) | Correlates with experience level |
| income | int | Annual income ($35k-$150k) | Price sensitivity indicator |
| distance_to_store | float | Miles to nearest Academy | Urban vs rural shopping patterns |
| search_specificity | int | 1-5 scale of search detail | **KEY CLUSTERING VARIABLE** |
| spec_expansion_rate | float | % of times they expand specs | **KEY CLUSTERING VARIABLE** |
| bundle_affinity | float | Preference for bundles 0-1 | **KEY CLUSTERING VARIABLE** |
| price_sort_frequency | float | How often sorts by price | **KEY CLUSTERING VARIABLE** |
| total_spend_12mo | float | Last 12 months spend | Value tier |
| purchase_frequency | int | # purchases in 12 months | Engagement level |
| recency_days | int | Days since last purchase | Churn risk |
| avg_order_value | float | Average $ per order | Spending power |
| return_rate | float | % of orders returned | Satisfaction indicator |

**Categorical Variables:**
| Column | Type | Levels | Why It Matters |
|--------|------|--------|----------------|
| urbanicity | string | Urban/Suburban/Rural | Shopping behavior |
| climate_zone | string | Temperate/Hot/Cold | Gear needs |
| dominant_category | string | 7 camping categories | Product affinity |
| brand_loyalty | string | Brand name or "None" | Brand targeting |
| primary_return_reason | string | Size/Quality/Price/etc | Pain points |
| channel_preference | string | Web/Mobile/In-Store | Marketing channel |
| true_persona | string | Novice/Family/Pro | **GROUND TRUTH for validation** |

---

### Table 2: Products (150-200 products)

**Columns:**
| Column | Description | Example Values |
|--------|-------------|----------------|
| product_id | Unique identifier | PROD_00001 |
| product_name | Full product name | "Magellan 4-Person Instant Tent" |
| brand | Manufacturer | Coleman, MSR, YETI |
| brand_tier | Price category | budget/mid_range/premium/pro_grade |
| main_category | Academy category | "Tents + Screen Houses" |
| subcategory | Specific type | "Instant Tents" |
| price | Retail price | $29.99 - $1,299.99 |
| base_conversion_rate | Global CR | 0.01 - 0.08 |
| **setup_type** | **LIFT FEATURE** | Instant/Traditional/Quick |
| **complexity** | **LIFT FEATURE** | Simple/Moderate/Technical |
| **bundle_compatible** | **LIFT FEATURE** | Yes/No |
| capacity | Size | 1/2/4/6/8-Person |
| weight_class | Weight category | Ultralight/Lightweight/Standard |
| weatherproof | Weather rating | Basic/Resistant/All-Weather/Extreme |

---

### Table 3: Interactions (50,000-150,000 records)

**Purpose**: Track every customer-product interaction

**Columns:**
- interaction_id, customer_id, product_id
- timestamp
- interaction_type (view/click/add_to_cart)
- search_query (original search term)
- time_on_page_seconds
- specs_expanded (boolean) - **KEY BEHAVIOR**
- price_checked (boolean)
- reviews_viewed (boolean)
- bundle_viewed (boolean) - **KEY BEHAVIOR**

**Why This Matters:**
- Validates clustering (do people in same cluster behave similarly?)
- Calculates actual lift factors from real behavior
- Trains recommendation model

---

### Table 4: Purchases (5,000-15,000 records)

**Purpose**: Conversion events with feature attribution

**Columns:**
- purchase_id, customer_id, product_id, interaction_id
- purchase_date
- quantity, price_paid
- discount_applied
- purchased_as_bundle (boolean)

**Conversion Calculation:**
```
For each (persona, feature) pair:
  total_views_with_feature = COUNT(interactions WHERE product has feature)
  purchases_with_feature = COUNT(purchases WHERE product has feature)
  
  persona_CR = purchases / views for this persona
  global_CR = all purchases / all views
  
  lift_factor = persona_CR / global_CR
```

---

### Table 5: Feature Affinity Matrix

**Purpose**: Pre-calculated lift factors for each persona-feature combination

**Columns:**
- persona (Novice/Family_Socializer/Seasoned_Pro)
- feature (e.g., "Instant Setup", "Bundle Compatible")
- lift_factor (e.g., 3.0, 0.2)
- log_lift (for logistic regression: ln(lift_factor))

**Example Data:**
| Persona | Feature | Lift Factor | Log Lift |
|---------|---------|-------------|----------|
| Novice | Instant Setup | 3.0 | 1.10 |
| Novice | Bundle Compatible | 2.0 | 0.69 |
| Seasoned_Pro | Instant Setup | 0.2 | -1.61 |
| Seasoned_Pro | Technical Design | 2.5 | 0.92 |

---

## 🔧 Implementation Phases

### Phase 1: K-Prototypes Clustering ✅ (Current)

**Why K-Prototypes Instead of K-Means?**

| Aspect | K-Means | K-Prototypes | Why We Choose K-Prototypes |
|--------|---------|--------------|----------------------------|
| Data Types | Numeric only | Numeric + Categorical | We have mixed data types |
| Distance Metric | Euclidean | Euclidean + Hamming | Handles categories properly |
| Example | Can't handle "Brand_Loyalty" | Can handle all our variables | Preserves categorical meaning |

**Algorithm:**
```
distance(customer1, customer2) = 
  Σ(numeric differences)² + 
  γ × Σ(categorical mismatches)

where γ is tuned to balance numeric vs categorical importance
```

**Implementation:**
```python
from kmodes.kprototypes import KPrototypes

# Separate numeric and categorical indices
numeric_cols = ['age', 'income', 'search_specificity', 
                'spec_expansion_rate', 'bundle_affinity', ...]
categorical_cols = ['urbanicity', 'climate_zone', 
                    'dominant_category', 'brand_loyalty', ...]

# Fit model
kproto = KPrototypes(n_clusters=3, gamma=0.5, random_state=42)
clusters = kproto.fit_predict(customer_data, categorical=[cat_indices])
```

**Success Validation:**
- Do novices cluster together? (High bundle_affinity, low specificity)
- Do pros cluster together? (High specificity, low bundle_affinity)
- Silhouette score > 0.3

---

### Phase 2: Feature Lift Calculation

**Process:**
1. For each product feature (e.g., "Instant Setup")
2. Calculate views and purchases by cluster
3. Compute lift = (cluster_CR / global_CR)
4. Store in feature_affinity table

**Code Pattern:**
```python
def calculate_lift(cluster_id, feature_name):
    # Global stats
    global_views = interactions[products.has_feature(feature)].count()
    global_purchases = purchases[products.has_feature(feature)].count()
    global_CR = global_purchases / global_views
    
    # Cluster-specific
    cluster_customers = customers[customers.cluster == cluster_id]
    cluster_views = interactions[
        interactions.customer.isin(cluster_customers) &
        products.has_feature(feature)
    ].count()
    cluster_purchases = purchases[
        purchases.customer.isin(cluster_customers) &
        products.has_feature(feature)
    ].count()
    cluster_CR = cluster_purchases / cluster_views
    
    lift = cluster_CR / global_CR
    return lift
```

---

### Phase 3: Agent A Enhancement

**Current Agent A (Banking/Retail):**
- K-means clustering
- Generic persona names
- Basic RFM scoring

**New Agent A (Academy Sports Camping):**
- **K-prototypes clustering** (handles mixed data)
- **Behavioral persona identification**:
  - "🏕️ First-Time Camper" (not "Cluster 0")
  - "👨‍👩‍👧‍👦 Family Socializer" (not "Cluster 1")  
  - "⛰️ Seasoned Pro" (not "Cluster 2")
- **Feature affinity profiles**:
  - Shows which features each persona loves/hates
  - Displays lift factors visually
- **Search behavior analysis**:
  - Tracks specificity patterns
  - Monitors spec expansion behavior

**New Outputs:**
```json
{
  "persona": "First-Time Camper",
  "size": 2000,
  "characteristics": {
    "avg_search_specificity": 1.4,
    "avg_spec_expansion_rate": 0.12,
    "avg_bundle_affinity": 0.85,
    "avg_price_sort_freq": 0.78
  },
  "feature_preferences": {
    "loves": ["Instant Setup (3.0x)", "Bundles (2.0x)", "Simple Design (1.5x)"],
    "hates": ["Technical Design (0.3x)", "Complex Assembly (0.4x)"]
  }
}
```

---

### Phase 4: Agent B Enhancement

**Current Agent B:**
- Basic product similarity
- Generic recommendations

**New Agent B (Feature-Based Scoring):**

**For Each (Customer, Product) Pair:**
1. Identify customer's cluster/persona
2. Extract product features
3. Calculate score:
```python
def score_product(customer, product):
    base_logit = log(product.base_CR / (1 - product.base_CR))
    
    lift_sum = 0
    for feature in product.features:
        persona = customer.cluster
        lift = feature_affinity[persona, feature]
        lift_sum += log(lift)
    
    final_logit = base_logit + lift_sum
    probability = 1 / (1 + exp(-final_logit))
    return probability
```

4. Rank all products by probability
5. Return top N with explanations

**Output Example:**
```json
{
  "customer": "CUST_00123",
  "persona": "First-Time Camper",
  "recommendations": [
    {
      "product": "Magellan 4-Person Instant Cabin",
      "score": 0.322,
      "price": "$149.99",
      "explanation": "Perfect for you! Easy instant setup (3x match), comes in convenient bundles (2x match), and simple design (1.5x match)",
      "why_features_match": {
        "Instant Setup": "+110% boost",
        "Bundle Compatible": "+69% boost",
        "Simple Design": "+41% boost"
      }
    }
  ]
}
```

---

## 📊 Why Each Data Element Matters

### Customer Variables

**search_specificity (1-5):**
- **Why**: Most predictive of expertise level
- **How measured**: Parse search queries
  - 1: "camping tent" (generic)
  - 3: "4-person weather-resistant tent" (specific attribute)
  - 5: "MSR Hubba NX 2-Person" (exact model)
- **Clustering impact**: PRIMARY separator between novice and pro

**spec_expansion_rate (0-1):**
- **Why**: Indicates research depth
- **How measured**: % of product views where they clicked "Full Specifications"
- **Clustering impact**: Pros ALWAYS expand (>60%), novices NEVER (<20%)

**bundle_affinity (0-1):**
- **Why**: Separates convenience-seekers from specialists
- **How measured**: % of bundle-product views vs total views
- **Clustering impact**: Novices love bundles (>70%), pros ignore them (<20%)

**price_sort_frequency (0-1):**
- **Why**: Price sensitivity indicator
- **How measured**: % of searches where they sorted by "Price: Low to High"
- **Clustering impact**: Novices always sort by price (>70%), pros don't (<20%)

---

## 🎯 Expected Outcomes

### Metric Improvements

| Metric | Baseline | Target | Method |
|--------|----------|--------|--------|
| Overall Conversion | 5% | 8-12% | Persona-matched recommendations |
| Novice Conversion | 3% | 15-20% | Show instant/bundle products |
| Pro Conversion | 4% | 6-8% | Hide instant, show technical |
| Return Rate | 12% | 8% | Better product-persona fit |
| AOV (Novice) | $85 | $150 | Bundle upsells |
| AOV (Pro) | $280 | $350 | Premium product targeting |

### Personalization Examples

**Scenario 1: Novice searches "camping tent"**
- **Before**: Shows all tents, sorted by popularity
- **After**: 
  - Top result: "Coleman 4-Person Instant Setup Kit" with "PERFECT FOR BEGINNERS" badge
  - Hides: MSR technical tents
  - Upsell: "Complete camping bundle - save $50"

**Scenario 2: Pro searches "ultralight 2-person"**
- **Before**: Shows instant tents (irrelevant)
- **After**:
  - Top result: "MSR Hubba NX 2 - 1.3kg"
  - Shows: Technical specs expanded by default
  - Hides: Budget/instant options

---

## 🧪 Validation & Testing

### Clustering Validation
1. **Check separation**: Are cluster centroids distinct?
2. **Check coherence**: Do cluster members share behaviors?
3. **Check ground truth**: Does clustering match our "true_persona" labels?

**Metrics:**
- Silhouette Score > 0.3 (good separation)
- Davies-Bouldin Score < 1.5 (compact clusters)
- Accuracy vs true_persona > 85%

### Lift Factor Validation
1. **Statistical significance**: Is lift > 1.2x statistically significant?
2. **Sample size**: Enough data per persona-feature combo?
3. **Consistency**: Do lifts stay stable over time?

**Tests:**
- Chi-square test for independence
- Minimum 100 views per combo
- Track lift factors weekly

### A/B Test Design
- **Control**: Current recommendation algorithm
- **Treatment**: Feature-based lift scoring
- **Primary metric**: Conversion rate
- **Secondary**: AOV, return rate, satisfaction
- **Duration**: 4 weeks
- **Sample size**: 10,000 customers per group

---

## 📅 Implementation Timeline

| Phase | Duration | Deliverables |
|-------|----------|--------------|
| **Phase 1**: Data Generation | 1 week | 5 CSV files with 5,000 customers |
| **Phase 2**: K-Prototypes Clustering | 1 week | Persona identification working |
| **Phase 3**: Lift Calculation | 1 week | Feature affinity matrix |
| **Phase 4**: Agent A Enhancement | 2 weeks | New clustering + personas |
| **Phase 5**: Agent B Enhancement | 2 weeks | Feature-based scoring |
| **Phase 6**: Integration & Testing | 2 weeks | End-to-end validation |
| **Phase 7**: A/B Test | 4 weeks | Production rollout |

**Total: 13 weeks from data to production**

---

## 🔄 Next Steps

### Immediate (This Week):
1. ✅ Generate synthetic data (5,000 customers)
2. ✅ Create implementation documentation
3. ⏳ Install kmodes library: `pip install kmodes`
4. ⏳ Test K-prototypes clustering on sample data

### Short Term (Next 2 Weeks):
1. Implement K-prototypes clustering in Agent A
2. Validate persona separation
3. Calculate feature lift factors
4. Update ChromaDB schema

### Medium Term (Next Month):
1. Build feature-based scoring in Agent B
2. Create explanation layer
3. Update frontend with persona insights
4. Integration testing

---

## 📚 References

1. **Original Document**: Academy Sports Use Case - Camping Personalization
2. **Academy Sports Website**: https://www.academy.com/
3. **K-Prototypes Algorithm**: Huang (1998) - "Extensions to the k-Means Algorithm for Clustering Large Data Sets with Categorical Values"
4. **Logistic Regression**: Standard ML textbook approach
5. **Feature Engineering**: Derived from actual Academy product catalog

---

## ✅ Success Criteria

**Technical:**
- [ ] K-prototypes successfully identifies 3 distinct clusters
- [ ] Cluster characteristics match persona definitions
- [ ] Feature lift calculations show expected patterns (novice loves instant, pro hates it)
- [ ] Recommendation scores align with purchase probability

**Business:**
- [ ] Conversion rate improves by >30%
- [ ] Return rate decreases by >25%
- [ ] Customer satisfaction scores improve
- [ ] Revenue per customer increases

**User Experience:**
- [ ] Novices see simplified recommendations
- [ ] Pros see technical products they want
- [ ] Search results feel "personalized"
- [ ] Explanations are clear and helpful

---

**Document Version**: 1.0  
**Last Updated**: December 16, 2025  
**Status**: Phase 1 - Data Generation Complete ✅  
**Next Phase**: K-Prototypes Implementation  


