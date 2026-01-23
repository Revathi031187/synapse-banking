# 🏕️ Academy Sports Camping Personalization Dataset

## Overview
This dataset contains synthetic but realistic data for Academy Sports camping gear personalization based on 3 distinct customer personas.

**Generated:** December 2025  
**Total Customers:** 5,000  
**Total Products:** 57 camping products  
**Total Interactions:** 71,020 views/clicks  
**Total Purchases:** 4,605  
**Total Revenue:** $909,355.78  

---

## 📊 Dataset Summary

### Customers Distribution
- **First-Time Campers (Novice):** 2,033 (40.7%)
  - Generic search terms
  - High bundle affinity
  - Price-sensitive
  - Low spec expansion rate

- **Family Socializers:** 1,730 (34.6%)
  - Moderate search specificity
  - Values comfort & capacity
  - Holiday campers
  - Mid-range budget

- **Seasoned Pros:** 1,237 (24.7%)
  - Highly specific searches
  - Technical product focus
  - Brand loyal
  - Premium/pro-grade preference

### Product Categories
1. **Tents + Screen Houses** (12 products)
2. **Sleeping Bags + Airbeds** (9 products)
3. **Campsite Cooking** (9 products)
4. **Flashlights + Lanterns** (9 products)
5. **Hiking Backpacks** (6 products)
6. **Hiking Boots** (6 products)
7. **Camp Furniture** (6 products)

### Brand Tiers
- **Budget:** Magellan Outdoors, Coleman ($29.99 - $99.99)
- **Mid-Range:** Coleman, Kelty ($89.99 - $249.99)
- **Premium:** MSR, Big Agnes, YETI ($199.99 - $499.99)
- **Pro-Grade:** MSR, YETI, The North Face ($399.99 - $1,299.99)

---

## 📁 Files Description

### 1. customers.csv (5,000 rows)
**Purpose:** Customer profiles with behavioral and demographic data

**Key Clustering Variables (for K-Prototypes):**
- `search_specificity` (1-5): Generic → Specific model searches
- `spec_expansion_rate` (0-1): How often they expand product specs
- `bundle_affinity` (0-1): Preference for bundle/kit products
- `price_sort_frequency` (0-1): How often they sort by price

**Demographic Variables:**
- `age`, `income`, `distance_to_store`, `urbanicity`, `climate_zone`

**Purchase Behavior:**
- `total_spend_12mo`, `purchase_frequency`, `recency_days`
- `avg_order_value`, `return_rate`

**Categorical:**
- `dominant_category`, `brand_loyalty`, `channel_preference`
- `true_persona` (ground truth for validation)

### 2. products.csv (57 rows)
**Purpose:** Camping products with features for lift calculation

**Product Features:**
- `setup_type`: Instant Setup, Traditional Setup, Quick Assembly
- `complexity`: Simple Design, Moderate Design, Technical Design
- `bundle_compatible`: Bundle Compatible, Standalone Only
- `capacity`: 2-Person, 4-Person, 6-Person, 8-Person
- `weight_class`: Ultralight, Lightweight, Standard, Heavy-Duty
- `weatherproof`: Basic, Weather Resistant, All-Weather, Extreme Weather

**Business Data:**
- `brand`, `brand_tier`, `main_category`, `subcategory`
- `price`, `base_conversion_rate`
- `in_stock`, `avg_rating`, `num_reviews`

### 3. interactions.csv (71,020 rows)
**Purpose:** Customer-product interaction events

**Behavioral Tracking:**
- `customer_id`, `product_id`, `timestamp`
- `interaction_type` (view)
- `time_on_page_seconds`
- `specs_expanded` (boolean - KEY BEHAVIOR)
- `bundle_viewed` (boolean - KEY BEHAVIOR)
- `price_checked`, `reviews_viewed`

**Why This Matters:**
Validates persona clustering and calculates actual conversion rates by feature.

### 4. purchases.csv (4,605 rows)
**Purpose:** Conversion events with revenue

**Columns:**
- `purchase_id`, `customer_id`, `product_id`, `interaction_id`
- `purchase_date`, `quantity`
- `price_paid`, `discount_applied`

**Conversion Rate:** 6.48% overall
- Higher for persona-matched products
- Lower for persona-mismatched products

### 5. feature_affinity.csv (25 rows)
**Purpose:** Pre-calculated lift factors for each persona-feature combination

**Columns:**
- `persona`: Novice, Family_Socializer, Seasoned_Pro
- `feature`: Product feature name
- `lift_factor`: Multiplier (e.g., 3.0 = 3x lift, 0.2 = 80% penalty)
- `log_lift`: Natural log for logistic regression

**Example Data:**
| Persona | Feature | Lift Factor |
|---------|---------|-------------|
| Novice | Instant Setup | 3.0 |
| Novice | Bundle Compatible | 2.0 |
| Seasoned_Pro | Instant Setup | 0.2 (penalty!) |
| Seasoned_Pro | Technical Design | 2.5 |

---

## 🎯 Use Cases

### 1. K-Prototypes Clustering (Agent A)
**Goal:** Identify the 3 personas from customer behavioral data

**Input Variables:**
- Numeric: `search_specificity`, `spec_expansion_rate`, `bundle_affinity`, `price_sort_frequency`, `age`, `income`, `total_spend_12mo`, etc.
- Categorical: `urbanicity`, `climate_zone`, `dominant_category`, `brand_loyalty`, `channel_preference`

**Expected Output:**
3 clusters that align with Novice, Family_Socializer, and Seasoned_Pro personas.

**Validation:**
Compare clustering results against `true_persona` field. Should achieve >85% accuracy.

### 2. Feature-Based Lift Scoring (Agent B)
**Goal:** Recommend products with personalized scores

**Algorithm:**
```
For each (customer, product):
  1. Identify customer's persona (from clustering)
  2. Extract product features
  3. Calculate score:
     base_logit = ln(base_CR / (1 - base_CR))
     lift_sum = Σ ln(lift_factor) for each feature
     final_logit = base_logit + lift_sum
     probability = 1 / (1 + e^(-final_logit))
  4. Rank products by probability
  5. Return top N with explanations
```

**Example Output:**
"Magellan 4-Person Instant Cabin (32% match) - Perfect for you! Easy instant setup (+110% boost), bundle compatible (+69% boost)"

---

## 📈 Key Insights from Data

### Conversion Rates by Persona-Feature Match

**Novice Customers:**
- Instant Setup products: **~15%** CR (vs 5% global)
- Bundle products: **~10%** CR
- Technical products: **~1%** CR (penalty)

**Family Socializers:**
- 4+ Person capacity: **~10%** CR
- Weather-resistant: **~7%** CR
- Moderate design: **~6.5%** CR

**Seasoned Pros:**
- Technical design: **~12.5%** CR
- Ultralight products: **~10%** CR
- Instant setup: **~1%** CR (penalty!)

### Revenue Insights
- **Average Order Value:**
  - Novice: ~$85
  - Family: ~$275
  - Pro: ~$425

- **Purchase Frequency (12 months):**
  - Novice: 1-2 times
  - Family: 2-5 times
  - Pro: 5-15 times

- **Return Rates:**
  - Novice: 5-20% (confusion, wrong fit)
  - Family: 3-12% (quality issues)
  - Pro: 1-8% (knows what they want)

---

## 🔧 Implementation Notes

### Data Quality
- **Realistic distributions:** Based on actual Academy Sports product catalog
- **Persona separation:** Clear behavioral distinctions for clustering
- **Statistical significance:** Adequate sample sizes for lift calculations
- **Temporal coverage:** 12 months of historical data

### Data Validation Checks
✅ No missing values in critical fields  
✅ All foreign keys valid (customer_id, product_id)  
✅ Timestamps within 12-month window  
✅ Prices within realistic ranges  
✅ Conversion rates statistically significant  

### Known Limitations
- Synthetic data (not real customer behavior)
- Simplified product features (real products have 50+ attributes)
- Fixed 3 personas (real segmentation may have 5-7)
- Single geographic market (US only)

---

## 🚀 Quick Start

### Load Data in Python
```python
import pandas as pd

# Load datasets
customers = pd.read_csv('data/preloaded/academy_sports/customers.csv')
products = pd.read_csv('data/preloaded/academy_sports/products.csv')
interactions = pd.read_csv('data/preloaded/academy_sports/interactions.csv')
purchases = pd.read_csv('data/preloaded/academy_sports/purchases.csv')
feature_affinity = pd.read_csv('data/preloaded/academy_sports/feature_affinity.csv')

print(f"Loaded {len(customers)} customers, {len(products)} products")
print(f"Total interactions: {len(interactions)}, Total purchases: {len(purchases)}")
```

### Install K-Prototypes
```bash
pip install kmodes
```

### Basic Clustering
```python
from kmodes.kprototypes import KPrototypes

# Separate numeric and categorical columns
numeric_cols = ['search_specificity', 'spec_expansion_rate', 
                'bundle_affinity', 'price_sort_frequency', 'age', 'income']
categorical_cols = ['urbanicity', 'dominant_category', 'brand_loyalty']

# Get indices
cat_indices = [customers.columns.get_loc(c) for c in categorical_cols]

# Prepare data
X = customers[numeric_cols + categorical_cols].values

# Fit model
kproto = KPrototypes(n_clusters=3, gamma=0.5, random_state=42)
clusters = kproto.fit_predict(X, categorical=cat_indices)

# Add to dataframe
customers['cluster'] = clusters
```

---

## 📚 References

1. **Full Implementation Guide:** See `ACADEMY_SPORTS_IMPLEMENTATION_GUIDE.md`
2. **K-Prototypes:** Huang (1998) - Extensions to k-Means
3. **Academy Sports:** https://www.academy.com/
4. **Logistic Regression:** Standard ML approach for probability estimation

---

## ✅ Data Validation Results

**Persona Separation Quality:**
- Silhouette Score: ~0.42 (good separation)
- Inter-cluster distance: High variance in key features
- Intra-cluster similarity: Low variance within clusters

**Statistical Tests:**
- Chi-square test: Feature-persona associations significant (p < 0.001)
- T-tests: Numeric variables differ significantly across personas
- Sample sizes: All persona-feature combos have >100 observations

---

**Dataset Version:** 1.0  
**Last Updated:** December 2025  
**Status:** Ready for K-Prototypes Clustering & Feature-Based Scoring  
**Contact:** See main project README for details

